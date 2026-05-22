use crate::board::{Board, CastlingRights};
use crate::square::{Color, Piece, PieceKind, PromotionChoice, Square};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Move {
    pub from: Square,
    pub to: Square,
    pub promotion: Option<PromotionChoice>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MoveError {
    NotYourTurn,
    NoPiece,
    IllegalMove,
    PromotionRequired,
    PromotionNotAllowed,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ApplyResult {
    pub board: Board,
    pub king_captured: bool,
    pub needs_promotion: bool,
}

pub fn in_check(board: &Board, color: Color) -> bool {
    let Some(king_sq) = board.king_square(color) else {
        return false;
    };
    is_square_attacked(board, king_sq, color.opposite())
}

pub fn is_square_attacked(board: &Board, sq: Square, by: Color) -> bool {
    for i in 0..64 {
        let from = Square::from_index(i).unwrap();
        if let Some(p) = board.get(from) {
            if p.color == by && attacks_square(board, from, sq, p) {
                return true;
            }
        }
    }
    false
}

pub(crate) fn attacks_square(board: &Board, from: Square, target: Square, piece: Piece) -> bool {
    let df = target.file as i8 - from.file as i8;
    let dr = target.rank as i8 - from.rank as i8;
    let pattern = match piece.kind {
        PieceKind::Pawn => {
            let dir: i8 = if piece.color == Color::White { 1 } else { -1 };
            dr == dir && df.abs() == 1
        }
        PieceKind::Knight => (df.abs(), dr.abs()) == (1, 2) || (df.abs(), dr.abs()) == (2, 1),
        PieceKind::King => df.abs() <= 1 && dr.abs() <= 1 && (df != 0 || dr != 0),
        PieceKind::Rook => (df == 0 || dr == 0) && (df != 0 || dr != 0),
        PieceKind::Bishop => df.abs() == dr.abs() && df != 0,
        PieceKind::Queen => {
            (df == 0 || dr == 0 || df.abs() == dr.abs()) && (df != 0 || dr != 0)
        }
    };
    pattern && ray_clear_for_attack(board, from, target, piece.kind)
}

fn ray_clear_for_attack(board: &Board, from: Square, target: Square, kind: PieceKind) -> bool {
    let df = target.file as i8 - from.file as i8;
    let dr = target.rank as i8 - from.rank as i8;
    match kind {
        PieceKind::Knight | PieceKind::King | PieceKind::Pawn => true,
        _ => {
            if df == 0 && dr == 0 {
                return false;
            }
            let step_f = df.signum();
            let step_r = dr.signum();
            let mut f = from.file as i8 + step_f;
            let mut r = from.rank as i8 + step_r;
            while f != target.file as i8 || r != target.rank as i8 {
                if board.get(Square::new(f as u8, r as u8).unwrap()).is_some() {
                    return false;
                }
                f += step_f;
                r += step_r;
            }
            true
        }
    }
}

fn pawn_dir(color: Color) -> i8 {
    if color == Color::White { 1 } else { -1 }
}

fn pawn_start_rank(color: Color) -> u8 {
    if color == Color::White { 1 } else { 6 }
}

fn pawn_promo_rank(color: Color) -> u8 {
    if color == Color::White { 7 } else { 0 }
}

/// Reachable squares for a piece (respects blockers).
pub fn reachable_from(board: &Board, from: Square) -> Vec<Square> {
    let Some(piece) = board.get(from) else {
        return vec![];
    };
    let mut out = Vec::new();
    let color = piece.color;

    match piece.kind {
        PieceKind::Pawn => {
            let dir = pawn_dir(color);
            let one = Square::new(from.file, (from.rank as i8 + dir) as u8);
            if let Some(s) = one {
                if board.get(s).is_none() {
                    out.push(s);
                    if from.rank == pawn_start_rank(color) {
                        let two = Square::new(from.file, (from.rank as i8 + 2 * dir) as u8);
                        if let Some(t2) = two {
                            if board.get(t2).is_none() {
                                out.push(t2);
                            }
                        }
                    }
                }
            }
            for df in [-1i8, 1] {
                let cap = Square::new((from.file as i8 + df) as u8, (from.rank as i8 + dir) as u8);
                if let Some(s) = cap {
                    if board.get(s).map(|t| t.color != color).unwrap_or(false) {
                        out.push(s);
                    }
                }
            }
            if let Some(ep) = board.en_passant {
                let forward = (from.rank as i8 + pawn_dir(color)) as u8;
                if ep.rank == forward
                    && (from.file as i8 - ep.file as i8).abs() == 1
                {
                    out.push(ep);
                }
            }
        }
        PieceKind::Knight => {
            for (df, dr) in [
                (1, 2),
                (2, 1),
                (2, -1),
                (1, -2),
                (-1, -2),
                (-2, -1),
                (-2, 1),
                (-1, 2),
            ] {
                if let Some(s) = Square::new((from.file as i8 + df) as u8, (from.rank as i8 + dr) as u8)
                {
                    if square_free_or_enemy(board, s, color) {
                        out.push(s);
                    }
                }
            }
        }
        PieceKind::King => {
            for df in -1..=1 {
                for dr in -1..=1 {
                    if df == 0 && dr == 0 {
                        continue;
                    }
                    if let Some(s) =
                        Square::new((from.file as i8 + df) as u8, (from.rank as i8 + dr) as u8)
                    {
                        if square_free_or_enemy(board, s, color) {
                            out.push(s);
                        }
                    }
                }
            }
        }
        PieceKind::Rook | PieceKind::Bishop | PieceKind::Queen => {
            let dirs: &[(i8, i8)] = match piece.kind {
                PieceKind::Rook => &[(0, 1), (0, -1), (1, 0), (-1, 0)],
                PieceKind::Bishop => &[(1, 1), (1, -1), (-1, 1), (-1, -1)],
                PieceKind::Queen => &[
                    (0, 1),
                    (0, -1),
                    (1, 0),
                    (-1, 0),
                    (1, 1),
                    (1, -1),
                    (-1, 1),
                    (-1, -1),
                ],
                _ => unreachable!(),
            };
            for (df, dr) in dirs {
                let mut f = from.file as i8 + df;
                let mut r = from.rank as i8 + dr;
                while let Some(s) = Square::new(f as u8, r as u8) {
                    match board.get(s) {
                        None => {
                            out.push(s);
                        }
                        Some(t) if t.color != color => {
                            out.push(s);
                            break;
                        }
                        _ => break,
                    }
                    f += df;
                    r += dr;
                }
            }
        }
    }
    out
}

fn square_free_or_enemy(board: &Board, sq: Square, color: Color) -> bool {
    board.get(sq).map(|p| p.color != color).unwrap_or(true)
}

/// Intent squares for sliding pieces (ignore blockers) — used for fog truncation.
pub fn intent_squares_on_ray(board: &Board, from: Square, to: Square) -> bool {
    let Some(piece) = board.get(from) else {
        return false;
    };
    if !matches!(
        piece.kind,
        PieceKind::Rook | PieceKind::Bishop | PieceKind::Queen
    ) {
        return from == to;
    }
    let df = to.file as i8 - from.file as i8;
    let dr = to.rank as i8 - from.rank as i8;
    match piece.kind {
        PieceKind::Rook => df == 0 || dr == 0,
        PieceKind::Bishop => df.abs() == dr.abs() && df != 0,
        PieceKind::Queen => (df == 0 || dr == 0 || df.abs() == dr.abs()) && (df != 0 || dr != 0),
        _ => false,
    }
}

/// Closest reachable square toward `intent` along the ray (fog sliding).
pub fn closest_reachable(board: &Board, from: Square, intent: Square) -> Option<Square> {
    let reach = reachable_from(board, from);
    if reach.contains(&intent) {
        return Some(intent);
    }
    if !intent_squares_on_ray(board, from, intent) {
        return None;
    }
    let df = (intent.file as i8 - from.file as i8).signum();
    let dr = (intent.rank as i8 - from.rank as i8).signum();
    let mut best: Option<Square> = None;
    let mut best_dist = -1i32;
    for s in reach {
        let sdf = s.file as i8 - from.file as i8;
        let sdr = s.rank as i8 - from.rank as i8;
        if sdf.signum() == df && sdr.signum() == dr && (sdf != 0 || sdr != 0) {
            let dist = (sdf.abs() + sdr.abs()) as i32;
            if dist > best_dist {
                best_dist = dist;
                best = Some(s);
            }
        }
    }
    best
}

pub fn resolve_to_square(board: &Board, from: Square, to: Square) -> Option<Square> {
    let reach = reachable_from(board, from);
    if reach.contains(&to) {
        Some(to)
    } else {
        closest_reachable(board, from, to)
    }
}

pub fn ep_passed_pawn_square(board: &Board, ep_target: Square) -> Option<Square> {
    let dir: i8 = if board.turn == Color::White { -1 } else { 1 };
    Square::new(ep_target.file, (ep_target.rank as i8 + dir) as u8)
}

pub fn generate_pseudo_legal(
    board: &Board,
    color: Color,
    ep_allowed: impl Fn(Square, Square) -> bool,
) -> Vec<Move> {
    let mut moves = Vec::new();
    for i in 0..64 {
        let from = Square::from_index(i).unwrap();
        let Some(piece) = board.get(from) else {
            continue;
        };
        if piece.color != color {
            continue;
        }
        let mut targets = reachable_from(board, from);
        if matches!(
            piece.kind,
            PieceKind::Rook | PieceKind::Bishop | PieceKind::Queen
        ) {
            for df in -7..=7 {
                for dr in -7..=7 {
                    if let Some(t) =
                        Square::new((from.file as i8 + df) as u8, (from.rank as i8 + dr) as u8)
                    {
                        if intent_squares_on_ray(board, from, t) && !targets.contains(&t) {
                            if closest_reachable(board, from, t).is_some() {
                                targets.push(t);
                            }
                        }
                    }
                }
            }
        }
        for to in targets {
            if piece.kind == PieceKind::Pawn
                && board.en_passant == Some(to)
                && !ep_allowed(from, to)
            {
                continue;
            }
            let promo = if piece.kind == PieceKind::Pawn && to.rank == pawn_promo_rank(color) {
                None
            } else {
                None
            };
            moves.push(Move {
                from,
                to,
                promotion: promo,
            });
        }
    }
    moves
}

pub fn generate_legal_moves(
    board: &Board,
    color: Color,
    ep_allowed: impl Fn(Square, Square) -> bool,
    check_aware: bool,
) -> Vec<Move> {
    let pseudo = generate_pseudo_legal(board, color, ep_allowed);
    if !check_aware {
        return pseudo;
    }
    pseudo
        .into_iter()
        .filter(|m| {
            let mut b = board.clone();
            if apply_move_unchecked(&mut b, m).is_ok() {
                !in_check(&b, color)
            } else {
                false
            }
        })
        .collect()
}

pub fn is_checkmate(
    board: &Board,
    color: Color,
    ep_allowed: impl Fn(Square, Square) -> bool + Copy,
    check_aware: bool,
) -> bool {
    in_check(board, color)
        && generate_legal_moves(board, color, ep_allowed, check_aware).is_empty()
}

pub fn apply_move(board: &mut Board, mv: &Move) -> Result<ApplyResult, MoveError> {
    let color = board.turn;
    let Some(piece) = board.get(mv.from) else {
        return Err(MoveError::NoPiece);
    };
    if piece.color != color {
        return Err(MoveError::NotYourTurn);
    }

    let actual_to = resolve_to_square(board, mv.from, mv.to).ok_or(MoveError::IllegalMove)?;

    let mut resolved = mv.clone();
    resolved.to = actual_to;

    if piece.kind == PieceKind::Pawn && actual_to.rank == pawn_promo_rank(color) {
        if mv.promotion.is_none() {
            return Ok(ApplyResult {
                board: board.clone(),
                king_captured: false,
                needs_promotion: true,
            });
        }
    } else if mv.promotion.is_some() {
        return Err(MoveError::PromotionNotAllowed);
    }

    let king_captured = apply_move_unchecked(board, &resolved)?;
    let needs_promotion = false;
    Ok(ApplyResult {
        board: board.clone(),
        king_captured,
        needs_promotion,
    })
}

fn apply_move_unchecked(board: &mut Board, mv: &Move) -> Result<bool, MoveError> {
    let color = board.turn;
    let Some(piece) = board.get(mv.from) else {
        return Err(MoveError::NoPiece);
    };

    let mut king_captured = false;
    let actual_to = resolve_to_square(board, mv.from, mv.to).ok_or(MoveError::IllegalMove)?;

    // En passant capture
    if piece.kind == PieceKind::Pawn && board.en_passant == Some(actual_to) {
        let captured_sq = ep_passed_pawn_square(board, actual_to).unwrap();
        if let Some(cap) = board.get(captured_sq) {
            if cap.kind == PieceKind::King {
                king_captured = true;
            }
        }
        board.set(captured_sq, None);
    }

    if let Some(target) = board.get(actual_to) {
        if target.kind == PieceKind::King {
            king_captured = true;
        }
    }

    board.set(mv.from, None);

    let promo_kind = mv
        .promotion
        .map(|p| p.to_piece_kind())
        .unwrap_or(piece.kind);
    board.set(
        actual_to,
        Some(Piece {
            kind: if piece.kind == PieceKind::Pawn && actual_to.rank == pawn_promo_rank(color) {
                promo_kind
            } else {
                piece.kind
            },
            color,
        }),
    );

    // En passant target for double push
    board.en_passant = None;
    if piece.kind == PieceKind::Pawn && (actual_to.rank as i8 - mv.from.rank as i8).abs() == 2 {
        let ep_rank = (mv.from.rank as i8 + pawn_dir(color)) as u8;
        board.en_passant = Square::new(mv.from.file, ep_rank);
    }

    // Castling rights (simplified: clear on king/rook move)
    if piece.kind == PieceKind::King {
        match color {
            Color::White => board.white_castle = CastlingRights::default(),
            Color::Black => board.black_castle = CastlingRights::default(),
        }
    }

    board.turn = color.opposite();
    Ok(king_captured)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::square::{Color, Piece, PieceKind};

    #[test]
    fn sliding_truncates_to_blocker() {
        let mut b = Board::standard();
        b.squares = [None; 64];
        b.turn = Color::White;
        b.set(
            Square::from_uci("a1").unwrap(),
            Some(Piece {
                kind: PieceKind::Rook,
                color: Color::White,
            }),
        );
        b.set(
            Square::from_uci("a8").unwrap(),
            Some(Piece {
                kind: PieceKind::King,
                color: Color::Black,
            }),
        );
        b.set(
            Square::from_uci("a4").unwrap(),
            Some(Piece {
                kind: PieceKind::Pawn,
                color: Color::Black,
            }),
        );
        let mv = parse_move("a1a8").unwrap();
        let to = resolve_to_square(&b, mv.from, mv.to).unwrap();
        assert_eq!(to.to_uci(), "a4");
        apply_move(&mut b, &mv).unwrap();
        assert_eq!(
            b.get(Square::from_uci("a4").unwrap()).unwrap().kind,
            PieceKind::Rook
        );
    }
}

pub fn parse_move(s: &str) -> Option<Move> {
    let s = s.trim();
    if s.len() < 4 {
        return None;
    }
    let from = Square::from_uci(&s[0..2])?;
    let to = Square::from_uci(&s[2..4])?;
    let promotion = if s.len() >= 5 {
        PromotionChoice::from_char(s.chars().nth(4)?)
    } else {
        None
    };
    Some(Move {
        from,
        to,
        promotion,
    })
}
