use std::collections::HashMap;

use btch_core::{
    awareness::{check_aware, dual_aware_checkmate, filter_board_for_player, legal_moves_for},
    board::Board,
    rules::{self, parse_move, resolve_to_square, ApplyResult, Move, MoveError},
    square::{Color, Piece, PieceKind, PromotionChoice, Square},
    winner_if_checkmate,
};
use rand::Rng;
use serde::{Deserialize, Serialize};
use sqlx::SqlitePool;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize)]
pub struct BoardState {
    pub squares: Vec<Option<PieceDto>>,
    pub turn: String,
    pub en_passant: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PieceDto {
    pub kind: String,
    pub color: String,
}

#[derive(Debug, sqlx::FromRow)]
pub struct GameRow {
    pub id: i64,
    pub uuid: String,
    pub white_user_id: Option<i64>,
    pub black_user_id: Option<i64>,
    pub status: String,
    pub turn: String,
    pub winner: Option<String>,
    pub resigned_by: Option<String>,
    pub elo_applied: i32,
    pub white_elo_delta: Option<i32>,
    pub black_elo_delta: Option<i32>,
}

const GAME_ROW_SELECT: &str = "SELECT id, uuid, white_user_id, black_user_id, status, turn, winner, resigned_by, \
    elo_applied, white_elo_delta, black_elo_delta FROM games";

pub fn format_game_datetime(dt: &str) -> String {
    const MONTHS: [&str; 12] = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ];
    let date = dt.get(0..10).unwrap_or(dt);
    let time = dt.get(11..16).unwrap_or("");
    let mut parts = date.split('-');
    let year = parts.next().unwrap_or("");
    let month = parts
        .next()
        .and_then(|m| m.parse::<usize>().ok())
        .and_then(|m| MONTHS.get(m.saturating_sub(1)).copied())
        .unwrap_or("");
    let day = parts.next().unwrap_or("");
    if time.is_empty() {
        format!("{day} {month} {year}")
    } else {
        format!("{day} {month} {year}, {time}")
    }
}

/// Replay header player: badge sits outside the name (left for white, right for black).
#[derive(Clone)]
pub struct ReplayPlayerHeader {
    pub name: String,
    pub color: String,
    pub badge: Option<String>,
}

pub fn replay_player_headers(
    white_name: &str,
    black_name: &str,
    winner: Option<&str>,
    resigned_by: Option<&str>,
) -> (ReplayPlayerHeader, ReplayPlayerHeader) {
    let mut white_badge = None;
    let mut black_badge = None;
    match winner.unwrap_or("") {
        "white" => white_badge = Some("👑".into()),
        "black" => black_badge = Some("👑".into()),
        _ => {}
    }
    if let Some(rb) = resigned_by {
        if rb == "white" {
            white_badge = Some("🏳️".into());
        } else if rb == "black" {
            black_badge = Some("🏳️".into());
        }
    }
    (
        ReplayPlayerHeader {
            name: white_name.to_string(),
            color: "White".into(),
            badge: white_badge,
        },
        ReplayPlayerHeader {
            name: black_name.to_string(),
            color: "Black".into(),
            badge: black_badge,
        },
    )
}

pub async fn game_played_at(pool: &SqlitePool, game_id: i64) -> String {
    sqlx::query_scalar::<_, String>(
        "SELECT COALESCE(started_at, created_at) FROM games WHERE id = ?",
    )
    .bind(game_id)
    .fetch_optional(pool)
    .await
    .ok()
    .flatten()
    .unwrap_or_default()
}

pub fn game_result_label(
    winner: Option<&str>,
    resigned_by: Option<&str>,
    white_name: &str,
    black_name: &str,
) -> String {
    let w = winner.unwrap_or("");
    if w.is_empty() {
        return "—".into();
    }
    let winner_name = if w == "white" { white_name } else { black_name };
    if let Some(rb) = resigned_by {
        let resigned_name = if rb == "white" { white_name } else { black_name };
        return format!("{winner_name} wins ({resigned_name} gave up)");
    }
    match w {
        "white" => format!("{white_name} wins"),
        "black" => format!("{black_name} wins"),
        other => other.into(),
    }
}

pub fn board_to_state(board: &Board) -> BoardState {
    BoardState {
        squares: board
            .squares
            .iter()
            .map(|p| {
                p.map(|piece| PieceDto {
                    kind: kind_char(piece.kind).to_string(),
                    color: if piece.color == Color::White {
                        "white".into()
                    } else {
                        "black".into()
                    },
                })
            })
            .collect(),
        turn: if board.turn == Color::White {
            "white".into()
        } else {
            "black".into()
        },
        en_passant: board.en_passant.map(|s| s.to_uci()),
    }
}

pub fn state_to_board(state: &BoardState) -> Board {
    let mut squares = [None; 64];
    for (i, p) in state.squares.iter().enumerate().take(64) {
        squares[i] = p.as_ref().map(|dto| Piece {
            kind: char_kind(&dto.kind),
            color: if dto.color == "white" {
                Color::White
            } else {
                Color::Black
            },
        });
    }
    Board {
        squares,
        turn: if state.turn == "white" {
            Color::White
        } else {
            Color::Black
        },
        white_castle: Default::default(),
        black_castle: Default::default(),
        en_passant: state.en_passant.as_deref().and_then(Square::from_uci),
    }
}

pub fn kind_char(k: PieceKind) -> char {
    match k {
        PieceKind::King => 'k',
        PieceKind::Queen => 'q',
        PieceKind::Rook => 'r',
        PieceKind::Bishop => 'b',
        PieceKind::Knight => 'n',
        PieceKind::Pawn => 'p',
    }
}

const STARTING: [(PieceKind, u8); 5] = [
    (PieceKind::Queen, 1),
    (PieceKind::Rook, 2),
    (PieceKind::Bishop, 2),
    (PieceKind::Knight, 2),
    (PieceKind::Pawn, 8),
];

fn material_index(kind: PieceKind) -> Option<usize> {
    match kind {
        PieceKind::Queen => Some(0),
        PieceKind::Rook => Some(1),
        PieceKind::Bishop => Some(2),
        PieceKind::Knight => Some(3),
        PieceKind::Pawn => Some(4),
        PieceKind::King => None,
    }
}

fn count_material(board: &Board, color: Color) -> [u8; 5] {
    let mut counts = [0u8; 5];
    for i in 0..64 {
        let sq = Square::from_index(i).unwrap();
        if let Some(p) = board.get(sq) {
            if p.color == color {
                if let Some(idx) = material_index(p.kind) {
                    counts[idx] += 1;
                }
            }
        }
    }
    counts
}

fn captured_by(board: &Board, captor: Color) -> Vec<PieceKind> {
    let victim = captor.opposite();
    let on_board = count_material(board, victim);
    let mut taken = Vec::new();
    for (kind, start) in STARTING {
        let idx = material_index(kind).unwrap();
        for _ in 0..start.saturating_sub(on_board[idx]) {
            taken.push(kind);
        }
    }
    taken
}

/// (pieces taken by white, pieces taken by black)
pub fn captured_trays(board: &Board) -> (Vec<PieceKind>, Vec<PieceKind>) {
    (
        captured_by(board, Color::White),
        captured_by(board, Color::Black),
    )
}

fn char_kind(s: &str) -> PieceKind {
    match s.chars().next().unwrap_or('p') {
        'k' | 'K' => PieceKind::King,
        'q' | 'Q' => PieceKind::Queen,
        'r' | 'R' => PieceKind::Rook,
        'b' | 'B' => PieceKind::Bishop,
        'n' | 'N' => PieceKind::Knight,
        _ => PieceKind::Pawn,
    }
}

pub fn player_color(game: &GameRow, user_id: i64) -> Option<Color> {
    if game.white_user_id == Some(user_id) {
        Some(Color::White)
    } else if game.black_user_id == Some(user_id) {
        Some(Color::Black)
    } else {
        None
    }
}

/// Legal destinations keyed by origin square (UCI), for move hints in the UI.
/// Fog squares are treated as empty; visible pieces block as on the real board.
pub fn legal_moves_by_from(board: &Board, color: Color) -> HashMap<String, Vec<String>> {
    let mut by_from: HashMap<String, Vec<String>> = HashMap::new();
    for i in 0..64 {
        let from = Square::from_index(i).expect("square index");
        let Some(piece) = board.get(from) else {
            continue;
        };
        if piece.color != color {
            continue;
        }
        for to in btch_core::hint_reachable_from(board, color, from) {
            by_from
                .entry(from.to_uci())
                .or_default()
                .push(to.to_uci());
        }
    }
    for dests in by_from.values_mut() {
        dests.sort();
        dests.dedup();
    }
    by_from
}

pub fn legal_moves_json(board: &Board, color: Color) -> String {
    serde_json::to_string(&legal_moves_by_from(board, color)).unwrap_or_else(|_| "{}".into())
}

pub fn filtered_view(board: &Board, color: Color) -> Vec<Option<PieceDto>> {
    filter_board_for_player(board, color)
        .iter()
        .map(|p| {
            p.map(|piece| PieceDto {
                kind: kind_char(piece.kind).to_string(),
                color: if piece.color == Color::White {
                    "white".into()
                } else {
                    "black".into()
                },
            })
        })
        .collect()
}

pub async fn load_board(pool: &SqlitePool, game_id: i64) -> Result<Board, sqlx::Error> {
    let json: String = sqlx::query_scalar(
        "SELECT board_json FROM game_snaps WHERE game_id = ? ORDER BY move_number DESC LIMIT 1",
    )
    .bind(game_id)
    .fetch_one(pool)
    .await?;
    let state: BoardState = serde_json::from_str(&json).unwrap();
    Ok(state_to_board(&state))
}

pub async fn save_snap(
    pool: &SqlitePool,
    game_id: i64,
    move_number: i32,
    uci: &str,
    board: &Board,
) -> Result<(), sqlx::Error> {
    let json = serde_json::to_string(&board_to_state(board)).unwrap();
    sqlx::query(
        "INSERT INTO game_snaps (game_id, move_number, move_uci, board_json) VALUES (?, ?, ?, ?)",
    )
    .bind(game_id)
    .bind(move_number)
    .bind(uci)
    .bind(json)
    .execute(pool)
    .await?;
    Ok(())
}

pub async fn find_own_waiting_random_game(
    pool: &SqlitePool,
    user_id: i64,
) -> Result<Option<GameRow>, sqlx::Error> {
    sqlx::query_as(&format!(
        "{GAME_ROW_SELECT} WHERE status = 'waiting' AND source = 'random'
         AND (white_user_id = ? OR black_user_id = ?)
         ORDER BY id DESC LIMIT 1"
    ))
    .bind(user_id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
}

pub async fn find_joinable_waiting_random_game(
    pool: &SqlitePool,
    user_id: i64,
) -> Result<Option<GameRow>, sqlx::Error> {
    sqlx::query_as(&format!(
        "{GAME_ROW_SELECT} WHERE status = 'waiting' AND source = 'random'
         AND (
           (white_user_id IS NOT NULL AND black_user_id IS NULL AND white_user_id != ?)
           OR (black_user_id IS NOT NULL AND white_user_id IS NULL AND black_user_id != ?)
         )
         ORDER BY id ASC LIMIT 1"
    ))
    .bind(user_id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
}

pub async fn create_waiting_random_game(pool: &SqlitePool, creator_id: i64) -> Result<GameRow, sqlx::Error> {
    let uuid = Uuid::new_v4().to_string();
    let id: i64 = sqlx::query_scalar(
        "INSERT INTO games (uuid, white_user_id, black_user_id, status, source, turn)
         VALUES (?, ?, NULL, 'waiting', 'random', '') RETURNING id",
    )
    .bind(&uuid)
    .bind(creator_id)
    .fetch_one(pool)
    .await?;
    get_game_by_id(pool, id).await
}

pub async fn try_join_waiting_random_game(
    pool: &SqlitePool,
    game_id: i64,
    joiner_id: i64,
) -> Result<Option<GameRow>, sqlx::Error> {
    let game = get_game_by_id(pool, game_id).await?;
    if game.status != "waiting" {
        return Ok(None);
    }
    let host_id = game
        .white_user_id
        .or(game.black_user_id)
        .ok_or_else(|| sqlx::Error::RowNotFound)?;
    if host_id == joiner_id {
        return Ok(None);
    }
    let (white_id, black_id) = assign_random_colors(host_id, joiner_id);
    let updated = sqlx::query(
        "UPDATE games SET white_user_id = ?, black_user_id = ?, status = 'started', turn = 'white', started_at = datetime('now')
         WHERE id = ? AND status = 'waiting'",
    )
    .bind(white_id)
    .bind(black_id)
    .bind(game_id)
    .execute(pool)
    .await?;
    if updated.rows_affected() == 0 {
        return Ok(None);
    }
    let board = Board::standard();
    save_snap(pool, game_id, 0, "", &board).await?;
    get_game_by_id(pool, game_id).await.map(Some)
}

pub fn is_solo_waiting_game(game: &GameRow) -> bool {
    game.status == "waiting"
        && ((game.white_user_id.is_some() && game.black_user_id.is_none())
            || (game.white_user_id.is_none() && game.black_user_id.is_some()))
}

pub async fn cancel_waiting_game(
    pool: &SqlitePool,
    game: &GameRow,
    user_id: i64,
) -> Result<(), String> {
    if !is_solo_waiting_game(game) {
        return Err("Game is not waiting for an opponent".into());
    }
    if player_color(game, user_id).is_none() {
        return Err("Not a player".into());
    }
    sqlx::query("DELETE FROM game_snaps WHERE game_id = ?")
        .bind(game.id)
        .execute(pool)
        .await
        .map_err(|e| e.to_string())?;
    let deleted = sqlx::query("DELETE FROM games WHERE id = ? AND status = 'waiting'")
        .bind(game.id)
        .execute(pool)
        .await
        .map_err(|e| e.to_string())?;
    if deleted.rows_affected() == 0 {
        return Err("Game not found".into());
    }
    Ok(())
}

pub async fn load_board_or_standard(pool: &SqlitePool, game: &GameRow) -> Board {
    if game.status == "waiting" {
        return Board::standard();
    }
    load_board(pool, game.id)
        .await
        .unwrap_or_else(|_| Board::standard())
}

pub async fn create_game(
    pool: &SqlitePool,
    white_id: i64,
    black_id: i64,
    source: &str,
) -> Result<GameRow, sqlx::Error> {
    let uuid = Uuid::new_v4().to_string();
    let id: i64 = sqlx::query_scalar(
        "INSERT INTO games (uuid, white_user_id, black_user_id, status, source, started_at) VALUES (?, ?, ?, 'started', ?, datetime('now')) RETURNING id",
    )
    .bind(&uuid)
    .bind(white_id)
    .bind(black_id)
    .bind(source)
    .fetch_one(pool)
    .await?;
    let board = Board::standard();
    save_snap(pool, id, 0, "", &board).await?;
    get_game_by_id(pool, id).await
}

pub async fn get_game_by_uuid(pool: &SqlitePool, uuid: &str) -> Result<Option<GameRow>, sqlx::Error> {
    sqlx::query_as(&format!("{GAME_ROW_SELECT} WHERE uuid = ?"))
    .bind(uuid)
    .fetch_optional(pool)
    .await
}

pub async fn get_game_by_id(pool: &SqlitePool, id: i64) -> Result<GameRow, sqlx::Error> {
    sqlx::query_as(&format!("{GAME_ROW_SELECT} WHERE id = ?"))
    .bind(id)
    .fetch_one(pool)
    .await
}

pub struct ReplaySnap {
    pub move_number: i32,
    pub move_uci: String,
    pub board: Board,
}

pub async fn load_replay_snaps(pool: &SqlitePool, game_id: i64) -> Result<Vec<ReplaySnap>, sqlx::Error> {
    let rows: Vec<(i32, String, String)> = sqlx::query_as(
        "SELECT move_number, move_uci, board_json FROM game_snaps WHERE game_id = ? ORDER BY move_number ASC",
    )
    .bind(game_id)
    .fetch_all(pool)
    .await?;
    let mut out = Vec::with_capacity(rows.len());
    for (move_number, move_uci, json) in rows {
        let state: BoardState = serde_json::from_str(&json).unwrap();
        out.push(ReplaySnap {
            move_number,
            move_uci,
            board: state_to_board(&state),
        });
    }
    Ok(out)
}

#[derive(Serialize)]
pub struct ReplayStepDto {
    pub n: i32,
    pub uci: String,
    /// When fog blocks the path, square where the piece actually stopped (UCI).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub actual_to: Option<String>,
    pub turn: String,
    pub squares: Vec<Option<PieceDto>>,
}

#[derive(Serialize)]
pub struct ReplayPayload {
    pub uuid: String,
    pub white_name: String,
    pub black_name: String,
    pub winner: String,
    pub resigned_by: Option<String>,
    pub result_label: String,
    pub status: String,
    pub role: String,
    pub player_color: Option<String>,
    pub steps: Vec<ReplayStepDto>,
}

fn replay_actual_to(snaps: &[ReplaySnap], step_index: usize, uci: &str) -> Option<String> {
    if uci.is_empty() || step_index == 0 {
        return None;
    }
    let mv = parse_move(uci)?;
    let prev = &snaps[step_index - 1].board;
    let actual = resolve_to_square(prev, mv.from, mv.to)?;
    if actual == mv.to {
        None
    } else {
        Some(actual.to_uci())
    }
}

pub fn build_replay_payload(
    game: &GameRow,
    white_name: &str,
    black_name: &str,
    snaps: &[ReplaySnap],
    viewer_role: &str,
    player_color: Option<&str>,
) -> ReplayPayload {
    ReplayPayload {
        uuid: game.uuid.clone(),
        white_name: white_name.to_string(),
        black_name: black_name.to_string(),
        winner: game.winner.clone().unwrap_or_default(),
        resigned_by: game.resigned_by.clone(),
        result_label: game_result_label(
            game.winner.as_deref(),
            game.resigned_by.as_deref(),
            white_name,
            black_name,
        ),
        status: game.status.clone(),
        role: viewer_role.to_string(),
        player_color: player_color.map(str::to_string),
        steps: snaps
            .iter()
            .enumerate()
            .map(|(i, s)| {
                let actual_to = replay_actual_to(snaps, i, &s.move_uci);
                ReplayStepDto {
                    n: s.move_number,
                    uci: s.move_uci.clone(),
                    actual_to,
                    turn: board_to_state(&s.board).turn,
                    squares: board_to_state(&s.board).squares,
                }
            })
            .collect(),
    }
}

pub fn can_access_replay(game: &GameRow, user_id: Option<i64>) -> Option<&'static str> {
    if let Some(uid) = user_id {
        if player_color(game, uid).is_some() {
            return Some("player");
        }
    }
    if game.status == "over" {
        return Some("spectator");
    }
    None
}

pub fn parse_replay_initial_step(query: Option<&str>, max_move: i32) -> i32 {
    match query.unwrap_or("first").trim() {
        "last" => max_move,
        "first" | "" => 0,
        s => s.parse::<i32>().unwrap_or(0).clamp(0, max_move),
    }
}

pub const ARCHIVE_PAGE_SIZE: i64 = 20;

#[derive(Debug, Clone, sqlx::FromRow)]
pub struct ArchiveGameRow {
    pub uuid: String,
    pub white_name: Option<String>,
    pub black_name: Option<String>,
    pub winner: Option<String>,
    pub resigned_by: Option<String>,
    pub played_at: String,
}

pub async fn count_finished_games(pool: &SqlitePool) -> Result<i64, sqlx::Error> {
    sqlx::query_scalar("SELECT COUNT(*) FROM games WHERE status = 'over'")
        .fetch_one(pool)
        .await
}

pub async fn list_finished_games(
    pool: &SqlitePool,
    page: i64,
) -> Result<Vec<ArchiveGameRow>, sqlx::Error> {
    let offset = (page - 1).max(0) * ARCHIVE_PAGE_SIZE;
    sqlx::query_as(
        r#"SELECT g.uuid,
                  w.username AS white_name,
                  b.username AS black_name,
                  g.winner,
                  g.resigned_by,
                  COALESCE(g.started_at, g.created_at) AS played_at
           FROM games g
           LEFT JOIN users w ON w.id = g.white_user_id
           LEFT JOIN users b ON b.id = g.black_user_id
           WHERE g.status = 'over'
           ORDER BY played_at DESC
           LIMIT ? OFFSET ?"#,
    )
    .bind(ARCHIVE_PAGE_SIZE)
    .bind(offset)
    .fetch_all(pool)
    .await
}

pub async fn username_for(pool: &SqlitePool, user_id: Option<i64>) -> String {
    let Some(id) = user_id else {
        return "?".into();
    };
    sqlx::query_scalar::<_, String>("SELECT username FROM users WHERE id = ?")
        .bind(id)
        .fetch_optional(pool)
        .await
        .ok()
        .flatten()
        .unwrap_or_else(|| "?".into())
}

pub fn assign_random_colors(
    u1: i64,
    u2: i64,
) -> (i64, i64) {
    if rand::thread_rng().gen_bool(0.5) {
        (u1, u2)
    } else {
        (u2, u1)
    }
}

pub struct MoveOutcome {
    pub board: Board,
    pub needs_promotion: bool,
    pub game_over: bool,
    pub winner: Option<String>,
    pub check_aware: bool,
    pub dual_mate: bool,
}

pub async fn apply_game_move(
    pool: &SqlitePool,
    game: &GameRow,
    user_id: i64,
    uci: &str,
    promotion: Option<char>,
) -> Result<MoveOutcome, String> {
    let color = player_color(game, user_id).ok_or("Not a player")?;
    let turn = if game.turn == "white" {
        Color::White
    } else {
        Color::Black
    };
    if color != turn {
        return Err("Not your turn".into());
    }
    if game.status == "over" {
        return Err("Game is over".into());
    }
    if game.status == "waiting" {
        return Err("Waiting for an opponent".into());
    }

    let mut board = load_board(pool, game.id).await.map_err(|e| e.to_string())?;
    let mut mv = parse_move(uci).ok_or("Invalid move")?;
    if let Some(ch) = promotion {
        mv.promotion = PromotionChoice::from_char(ch);
    }

    let result = rules::apply_move(&mut board, &mv).map_err(|e| match e {
        MoveError::PromotionRequired => "Promotion required".to_string(),
        _ => "Illegal move".to_string(),
    })?;

    if result.needs_promotion {
        return Ok(MoveOutcome {
            board: board.clone(),
            needs_promotion: true,
            game_over: false,
            winner: None,
            check_aware: check_aware(&board, color),
            dual_mate: false,
        });
    }

    let move_number: i32 = sqlx::query_scalar(
        "SELECT COALESCE(MAX(move_number), 0) + 1 FROM game_snaps WHERE game_id = ?",
    )
    .bind(game.id)
    .fetch_one(pool)
    .await
    .map_err(|e| e.to_string())?;

    let uci_full = if let Some(p) = mv.promotion {
        format!("{}{}", uci, match p {
            PromotionChoice::Queen => 'q',
            PromotionChoice::Rook => 'r',
            PromotionChoice::Bishop => 'b',
            PromotionChoice::Knight => 'n',
        })
    } else {
        uci.to_string()
    };

    save_snap(pool, game.id, move_number, &uci_full, &board)
        .await
        .map_err(|e| e.to_string())?;

    let mut game_over = false;
    let mut winner = None;

    if result.king_captured {
        game_over = true;
        winner = Some(if color == Color::White {
            "white".into()
        } else {
            "black".into()
        });
    } else if let Some(w) = winner_if_checkmate(&board) {
        game_over = true;
        winner = Some(if w == Color::White {
            "white".into()
        } else {
            "black".into()
        });
    }

    let new_turn = if board.turn == Color::White {
        "white"
    } else {
        "black"
    };

    if game_over {
        sqlx::query("UPDATE games SET status = 'over', winner = ?, turn = '' WHERE id = ?")
            .bind(&winner)
            .bind(game.id)
            .execute(pool)
            .await
            .map_err(|e| e.to_string())?;
        if let Err(e) = crate::elo::apply_for_game(pool, game.id).await {
            tracing::warn!(game_id = game.id, "elo update failed: {e}");
        }
    } else {
        sqlx::query("UPDATE games SET turn = ? WHERE id = ?")
            .bind(new_turn)
            .bind(game.id)
            .execute(pool)
            .await
            .map_err(|e| e.to_string())?;
    }

    let mated = board.turn;
    let opp = color.opposite();
    Ok(MoveOutcome {
        board: board.clone(),
        needs_promotion: false,
        game_over,
        winner,
        check_aware: check_aware(&board, opp),
        dual_mate: dual_aware_checkmate(&board, mated),
    })
}

pub async fn resign_game(
    pool: &SqlitePool,
    game: &GameRow,
    user_id: i64,
) -> Result<GameRow, String> {
    let color = player_color(game, user_id).ok_or("Not a player")?;
    if game.status == "over" {
        return Err("Game is over".into());
    }
    if game.status == "waiting" {
        return Err("Waiting for an opponent".into());
    }
    let winner = if color == Color::White {
        "black"
    } else {
        "white"
    };
    let resigned_by = if color == Color::White {
        "white"
    } else {
        "black"
    };
    sqlx::query(
        "UPDATE games SET status = 'over', winner = ?, turn = '', resigned_by = ? WHERE id = ?",
    )
    .bind(winner)
    .bind(resigned_by)
    .bind(game.id)
    .execute(pool)
    .await
    .map_err(|e| e.to_string())?;
    if let Err(e) = crate::elo::apply_for_game(pool, game.id).await {
        tracing::warn!(game_id = game.id, "elo update failed: {e}");
    }
    get_game_by_id(pool, game.id)
        .await
        .map_err(|e| e.to_string())
}

/// Elo change shown on game-over overlay for the current player.
pub async fn elo_summary_for_player(
    pool: &SqlitePool,
    game: &GameRow,
    user_id: i64,
) -> Option<(i32, i32)> {
    if game.elo_applied == 0 {
        return None;
    }
    let delta = if game.white_user_id == Some(user_id) {
        game.white_elo_delta?
    } else if game.black_user_id == Some(user_id) {
        game.black_elo_delta?
    } else {
        return None;
    };
    let new_elo: i32 = sqlx::query_scalar("SELECT elo FROM users WHERE id = ?")
        .bind(user_id)
        .fetch_one(pool)
        .await
        .ok()?;
    Some((delta, new_elo))
}
