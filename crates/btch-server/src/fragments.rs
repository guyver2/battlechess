use btch_core::{Board, PieceKind};

use crate::auth::User;
use crate::game::{
    captured_trays, elo_summary_for_player, filtered_view, kind_char, legal_moves_json,
    player_color, GameRow, PieceDto,
};
use crate::templates::{GameListItem, InviteView, SentInviteView};

pub fn captured_tray_html(label: &str, pieces: &[PieceKind], glyph_color: &str) -> String {
    let mut html = format!(r#"<span class="captured-label">{label}</span>"#);
    if pieces.is_empty() {
        html.push_str(r#"<span class="captured-empty"> —</span>"#);
    } else {
        for kind in pieces {
            html.push_str(&format!(
                r#"<span class="captured-piece {glyph_color}">{}</span>"#,
                kind_char(*kind).to_uppercase()
            ));
        }
    }
    html
}

pub fn captured_bars_from_board(board: &Board) -> (String, String) {
    let (by_white, by_black) = captured_trays(board);
    (
        captured_tray_html("White takes", &by_white, "black"),
        captured_tray_html("Black takes", &by_black, "white"),
    )
}

fn sq_coord_markup(file: u8, rank: u8) -> String {
    let mut html = String::new();
    if file == 0 {
        html.push_str(&format!(
            r#"<span class="sq-coord sq-coord-rank" aria-hidden="true">{}</span>"#,
            rank + 1
        ));
    }
    if rank == 0 {
        html.push_str(&format!(
            r#"<span class="sq-coord sq-coord-file" aria-hidden="true">{}</span>"#,
            (b'a' + file) as char
        ));
    }
    html
}

pub fn board_inner_html(view: &[Option<PieceDto>], visible: &[bool; 64]) -> String {
    let mut html = String::new();
    for rank in (0u8..8).rev() {
        html.push_str("<div class=\"rank\">");
        for file in 0u8..8 {
            let idx = rank as usize * 8 + file as usize;
            let light = (rank + file) % 2 == 1;
            let sq = format!("{}{}", (b'a' + file) as char, rank + 1);
            let fog = if visible[idx] { "" } else { " fog" };
            html.push_str(&format!(
                "<div class=\"sq {}{}\" data-sq=\"{}\">{}",
                if light { "light" } else { "dark" },
                fog,
                sq,
                sq_coord_markup(file, rank)
            ));
            if let Some(p) = &view[idx] {
                html.push_str(&format!(
                    "<span class=\"piece {}\">{}</span>",
                    p.color,
                    p.kind.to_uppercase()
                ));
            }
            if !visible[idx] {
                html.push_str(r#"<span class="fog-overlay" aria-hidden="true"></span>"#);
            }
            html.push_str("</div>");
        }
        html.push_str("</div>");
    }
    html
}

pub fn move_error_html(msg: &str) -> String {
    format!(r#"<p class="move-error" role="alert">{msg}</p>"#)
}

pub fn game_status_html(
    color: &str,
    turn: &str,
    check_aware: bool,
    game_over: bool,
    waiting: bool,
) -> String {
    if waiting {
        return format!(
            "<p>Playing as <strong>{color}</strong> — <em>Waiting for a random opponent…</em></p>"
        );
    }
    let turn_label = if game_over {
        "no one"
    } else {
        turn
    };
    let mut extra = String::new();
    if check_aware && !game_over {
        extra.push_str(" — <em>In check!</em>");
    }
    format!(
        "<p>Playing as <strong>{color}</strong> — Turn: {turn_label}{extra}</p>"
    )
}

fn modal_layer(inner: &str) -> String {
    format!(
        r#"<div class="game-modal-backdrop" aria-hidden="true"></div>
<div class="game-modal-content">{inner}</div>"#
    )
}

pub fn waiting_overlay_html() -> String {
    modal_layer(
        r#"<div class="waiting-panel" role="status">
  <p class="waiting-title">Waiting for opponent</p>
  <p class="waiting-detail">Matchmaking is open. When someone joins, the game will start automatically.</p>
</div>"#,
    )
}

pub fn quit_waiting_html(uuid: &str) -> String {
    format!(
        r#"<form class="quit-waiting-form" method="post" action="/games/{uuid}/cancel">
  <button type="submit" class="btn btn-ghost">Quit waiting</button>
</form>"#
    )
}

fn elo_change_html(delta: i32, new_elo: i32) -> String {
    let sign = if delta >= 0 { "+" } else { "" };
    format!(
        r#"<p class="game-over-elo">{sign}{delta} ELO · rating now {new_elo}</p>"#
    )
}

pub fn game_over_overlay_html(
    game_over: bool,
    winner: &str,
    player_color: &str,
    uuid: &str,
    elo_summary: Option<(i32, i32)>,
) -> String {
    if !game_over {
        return String::new();
    }
    let winner_side = match winner {
        "white" => "White",
        "black" => "Black",
        other if !other.is_empty() => other,
        _ => "Unknown",
    };
    let title = if winner == player_color {
        "You win!".to_string()
    } else if winner.is_empty() {
        "Game over".to_string()
    } else {
        format!("{winner_side} wins")
    };
    let detail = if winner.is_empty() {
        "This game has ended.".to_string()
    } else if winner == player_color {
        format!("Congratulations — you beat your opponent as {player_color}.")
    } else {
        format!("{winner_side} is victorious.")
    };
    let elo_html = elo_summary
        .map(|(d, n)| elo_change_html(d, n))
        .unwrap_or_default();
    modal_layer(&format!(
        r#"<div class="game-over-panel" role="status">
  <p class="game-over-title">{title}</p>
  <p class="game-over-detail">{detail}</p>
  {elo_html}
  <div class="panel-actions">
    <a href="/games/{uuid}/replay" class="btn btn-secondary">Watch replay</a>
    <a href="/lobby" class="btn btn-primary">Back to lobby</a>
  </div>
</div>"#
    ))
}

pub fn promotion_html(uuid: &str, pending_move: &str) -> String {
    let mut html = String::from(r#"<p class="promotion-prompt">Choose promotion</p><div class="promotion-btns">"#);
    for (label, ch) in [("Queen", "q"), ("Rook", "r"), ("Bishop", "b"), ("Knight", "n")] {
        html.push_str(&format!(
            r#"<form data-on:submit="@post('/games/{uuid}/promote', {{contentType: 'form'}})">
  <input type="hidden" name="piece" value="{ch}">
  <input type="hidden" name="pending_move" value="{pending_move}">
  <button type="submit" class="btn btn-secondary btn-sm">{label}</button>
</form>"#
        ));
    }
    html.push_str("</div>");
    html
}

fn escape_html_attr(s: &str) -> String {
    s.replace('&', "&amp;").replace('"', "&quot;")
}

pub fn move_controls_html(uuid: &str, legal_moves_json: &str) -> String {
    format!(
        r#"<div class="move-ui" data-move-url="/games/{uuid}/move" data-legal-moves="{legal_moves_json}">
  <p class="move-hint">Click your piece, then a destination square.</p>
</div>"#,
        legal_moves_json = escape_html_attr(legal_moves_json)
    )
}

pub fn resign_html(uuid: &str) -> String {
    format!(
        r#"<form class="resign-form" data-on:submit="@post('/games/{uuid}/resign', {{contentType: 'form'}})" onsubmit="return confirm('Give up? You will lose this game.');">
  <button type="submit" class="btn btn-ghost btn-sm">Give up</button>
</form>"#
    )
}

pub fn promotion_or_move_html(
    uuid: &str,
    needs_promotion: bool,
    pending_move: &str,
    your_turn: bool,
    game_over: bool,
    waiting: bool,
    legal_moves_json: &str,
) -> String {
    if waiting {
        return quit_waiting_html(uuid);
    }
    let mut html = if needs_promotion {
        promotion_html(uuid, pending_move)
    } else if your_turn && !game_over {
        move_controls_html(uuid, legal_moves_json)
    } else {
        String::new()
    };
    if !game_over {
        html.push_str(&resign_html(uuid));
    }
    html
}

pub fn sent_invites_html(sent: &[SentInviteView]) -> String {
    let mut html = String::from(r#"<h2 class="card-title">Invites sent</h2>"#);
    if sent.is_empty() {
        html.push_str(r#"<p class="empty-state">No invites sent yet.</p>"#);
        return html;
    }
    for inv in sent {
        let game_link = inv.game_uuid.as_ref().map(|uuid| {
            format!(
                r#"<a href="/games/{uuid}" class="btn btn-secondary btn-sm">Go to game</a>"#
            )
        });
        let delete_btn = if inv.status == "declined" || inv.status == "pending" {
            let label = if inv.status == "pending" {
                "Cancel"
            } else {
                "Delete"
            };
            Some(format!(
                r#"<form data-on:submit="@post('/invites/{}/delete', {{contentType: 'form'}})"><button type="submit" class="btn btn-ghost btn-sm">{label}</button></form>"#,
                inv.id
            ))
        } else {
            None
        };
        let msg = if inv.message.is_empty() {
            String::new()
        } else {
            format!(r#"<p class="invite-message">{}</p>"#, inv.message)
        };
        html.push_str(&format!(
            r#"<article class="invite invite-sent">
  <div class="invite-body">
    <p class="invite-main">To <strong>{to_name}</strong></p>
    {msg}
    <p class="invite-sent-on">Sent {sent_on}</p>
  </div>
  <div class="invite-actions">
    {game_link}
    {delete_btn}
    <span class="invite-status invite-status-{status}">{status_label}</span>
  </div>
</article>"#,
            to_name = inv.to_name,
            msg = msg,
            sent_on = inv.sent_on,
            game_link = game_link.unwrap_or_default(),
            delete_btn = delete_btn.unwrap_or_default(),
            status = inv.status,
            status_label = inv.status_label,
        ));
    }
    html
}

pub fn invites_html(received: &[InviteView]) -> String {
    let mut html = String::from(r#"<h2 class="card-title">Pending invites</h2>"#);
    if received.is_empty() {
        html.push_str(r#"<p class="empty-state">No pending invites.</p>"#);
        return html;
    }
    for inv in received {
        let msg = if inv.message.is_empty() {
            String::new()
        } else {
            format!(r#"<p class="invite-message">{}</p>"#, inv.message)
        };
        html.push_str(&format!(
            r#"<article class="invite">
  <div class="invite-body">
    <p class="invite-main">From <strong>{from_name}</strong></p>
    {msg}
    <p class="invite-sent-on">Sent {sent_on}</p>
  </div>
  <div class="invite-actions">
    <form data-on:submit="@post('/invites/{id}/accept', {{contentType: 'form'}})"><button type="submit" class="btn btn-primary btn-sm">Accept</button></form>
    <form data-on:submit="@post('/invites/{id}/decline', {{contentType: 'form'}})"><button type="submit" class="btn btn-ghost btn-sm">Decline</button></form>
  </div>
</article>"#,
            from_name = inv.from_name,
            msg = msg,
            sent_on = inv.sent_on,
            id = inv.id,
        ));
    }
    html
}

pub fn games_list_html(games: &[GameListItem]) -> String {
    let mut html = String::from(r#"<h2 class="card-title">Active games</h2>"#);
    if games.is_empty() {
        html.push_str(
            r#"<p class="empty-state">No active games. <a href="/archive">Browse finished games</a>.</p>"#,
        );
        return html;
    }
    html.push_str(r#"<ul class="game-links">"#);
    for g in games {
        let turn = if g.your_turn { " · your turn" } else { "" };
        html.push_str(&format!(
            r#"<li><a href="/games/{}" class="game-link"><span class="game-link-opponent">vs {}</span><span class="game-link-meta">{}{}</span></a></li>"#,
            g.uuid, g.opponent, g.status, turn
        ));
    }
    html.push_str("</ul>");
    html
}

pub fn queue_status_html(in_queue: bool) -> String {
    if in_queue {
        "<p class=\"queue-msg\">Searching for an opponent…</p>".into()
    } else {
        String::new()
    }
}

pub struct GameViewState {
    pub status_html: String,
    pub overlay_html: String,
    pub captured_white_html: String,
    pub board_html: String,
    pub captured_black_html: String,
    pub controls_html: String,
}

pub async fn build_game_view(
    pool: &sqlx::SqlitePool,
    game: &GameRow,
    user: &User,
    needs_promotion: bool,
    pending_move: &str,
) -> Result<GameViewState, String> {
    let color = player_color(game, user.id).ok_or("Not a player")?;
    let board = crate::game::load_board_or_standard(pool, game).await;
    let view = filtered_view(&board, color);
    let visible = btch_core::visibility::visible_squares(&board, color);
    let waiting = game.status == "waiting";
    let game_over = game.status == "over";
    let your_turn = !waiting
        && !game_over
        && ((color == btch_core::Color::White && game.turn == "white")
            || (color == btch_core::Color::Black && game.turn == "black"));
    let color_s = if color == btch_core::Color::White {
        "white"
    } else {
        "black"
    };
    let winner = game.winner.as_deref().unwrap_or("");
    let (captured_white_html, captured_black_html) = captured_bars_from_board(&board);
    let legal_json = if your_turn && !game_over && !needs_promotion {
        legal_moves_json(&board, color)
    } else {
        "{}".into()
    };
    let elo_summary = if game_over {
        elo_summary_for_player(pool, game, user.id).await
    } else {
        None
    };
    let overlay_html = if waiting {
        waiting_overlay_html()
    } else {
        game_over_overlay_html(game_over, winner, color_s, &game.uuid, elo_summary)
    };
    Ok(GameViewState {
        status_html: game_status_html(
            color_s,
            &game.turn,
            btch_core::check_aware(&board, color),
            game_over,
            waiting,
        ),
        overlay_html,
        captured_white_html,
        board_html: board_inner_html(&view, &visible),
        captured_black_html,
        controls_html: promotion_or_move_html(
            &game.uuid,
            needs_promotion,
            pending_move,
            your_turn,
            game_over,
            waiting,
            &legal_json,
        ),
    })
}

pub async fn game_version(pool: &sqlx::SqlitePool, game_id: i64) -> Result<(i32, String, String), sqlx::Error> {
    let snap: i32 = sqlx::query_scalar(
        "SELECT COALESCE(MAX(move_number), 0) FROM game_snaps WHERE game_id = ?",
    )
    .bind(game_id)
    .fetch_one(pool)
    .await?;
    let row: (String, String) = sqlx::query_as(
        "SELECT turn, status FROM games WHERE id = ?",
    )
    .bind(game_id)
    .fetch_one(pool)
    .await?;
    Ok((snap, row.0, row.1))
}
