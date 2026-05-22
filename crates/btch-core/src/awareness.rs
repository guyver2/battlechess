use crate::board::Board;
use crate::rules::{self, generate_legal_moves, in_check, is_checkmate};
use crate::square::{Color, PieceKind, Square};
use crate::visibility::is_visible;

/// En passant legal only if mover sees own pawn, ep square, and passed opponent pawn.
pub fn ep_aware(board: &Board, color: Color, from: Square, ep_target: Square) -> bool {
    let Some(passed) = rules::ep_passed_pawn_square(board, ep_target) else {
        return false;
    };
    is_visible(board, color, from)
        && is_visible(board, color, ep_target)
        && is_visible(board, color, passed)
}

pub fn ep_move_allowed(board: &Board, color: Color, from: Square, to: Square) -> bool {
    if board.en_passant != Some(to) {
        return true;
    }
    ep_aware(board, color, from, to)
}

/// Player is aware of check: in check, sees king, and sees each attacker (or sliding ray).
pub fn check_aware(board: &Board, color: Color) -> bool {
    if !in_check(board, color) {
        return false;
    }
    let Some(king_sq) = board.king_square(color) else {
        return false;
    };
    if !is_visible(board, color, king_sq) {
        return false;
    }
    attackers_visible(board, color, king_sq)
}

fn attackers_visible(board: &Board, color: Color, king_sq: Square) -> bool {
    let opponent = color.opposite();
    let mut found_attacker = false;
    for i in 0..64 {
        let from = Square::from_index(i).unwrap();
        let Some(p) = board.get(from) else {
            continue;
        };
        if p.color != opponent {
            continue;
        }
        if !rules::attacks_square(board, from, king_sq, p) {
            continue;
        }
        found_attacker = true;
        if !attacker_visible(board, color, from, king_sq, p.kind) {
            return false;
        }
    }
    found_attacker
}

fn attacker_visible(
    board: &Board,
    defender: Color,
    attacker_sq: Square,
    king_sq: Square,
    kind: PieceKind,
) -> bool {
    if is_visible(board, defender, attacker_sq) {
        return true;
    }
    match kind {
        PieceKind::Knight | PieceKind::Pawn | PieceKind::King => false,
        _ => sliding_ray_visible(board, defender, attacker_sq, king_sq),
    }
}

fn sliding_ray_visible(board: &Board, color: Color, from: Square, king_sq: Square) -> bool {
    if is_visible(board, color, from) {
        return true;
    }
    let df = (king_sq.file as i8 - from.file as i8).signum();
    let dr = (king_sq.rank as i8 - from.rank as i8).signum();
    let mut f = from.file as i8 + df;
    let mut r = from.rank as i8 + dr;
    while f != king_sq.file as i8 || r != king_sq.rank as i8 {
        let sq = Square::new(f as u8, r as u8).unwrap();
        if is_visible(board, color, sq) {
            return true;
        }
        f += df;
        r += dr;
    }
    false
}

pub fn mate_aware_mated(board: &Board, color: Color) -> bool {
    let aware = check_aware(board, color);
    is_checkmate(board, color, |f, t| ep_move_allowed(board, color, f, t), aware) && aware
}

pub fn opponent_sees_mate(board: &Board, mated: Color) -> bool {
    let opponent = mated.opposite();
    let Some(king_sq) = board.king_square(mated) else {
        return false;
    };
    if !is_visible(board, opponent, king_sq) {
        return false;
    }
    if !in_check(board, mated) {
        return false;
    }
    attackers_visible(board, opponent, king_sq)
}

pub fn dual_aware_checkmate(board: &Board, mated: Color) -> bool {
    let aware = check_aware(board, mated);
    if !is_checkmate(board, mated, |f, t| ep_move_allowed(board, mated, f, t), aware) {
        return false;
    }
    mate_aware_mated(board, mated) && opponent_sees_mate(board, mated)
}

pub fn game_end_checkmate(board: &Board) -> Option<Color> {
    for color in [Color::White, Color::Black] {
        if board.turn == color && dual_aware_checkmate(board, color) {
            return Some(color.opposite());
        }
    }
    None
}

/// After a move, check if either side to move is in dual-aware mate.
pub fn winner_if_checkmate(board: &Board) -> Option<Color> {
    game_end_checkmate(board)
}

pub fn legal_moves_for(board: &Board, color: Color) -> Vec<rules::Move> {
    let aware = check_aware(board, color);
    generate_legal_moves(
        board,
        color,
        |f, t| ep_move_allowed(board, color, f, t),
        aware,
    )
}

pub use crate::visibility::filter_board_for_player;
