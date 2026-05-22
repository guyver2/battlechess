use crate::board::Board;
use crate::square::{Color, Piece, PieceKind, Square};

/// Moore-neighborhood visibility: own piece squares + all 8 neighbors.
pub fn visible_squares(board: &Board, color: Color) -> [bool; 64] {
    let mut vis = [false; 64];
    for i in 0..64 {
        let sq = Square::from_index(i).unwrap();
        if let Some(p) = board.get(sq) {
            if p.color == color {
                vis[i] = true;
                for df in -1..=1 {
                    for dr in -1..=1 {
                        let f = sq.file as i8 + df;
                        let r = sq.rank as i8 + dr;
                        if let Some(n) = Square::new(f as u8, r as u8) {
                            if f >= 0 && r >= 0 && f < 8 && r < 8 {
                                vis[n.index()] = true;
                            }
                        }
                    }
                }
            }
        }
    }
    vis
}

pub fn is_visible(board: &Board, color: Color, sq: Square) -> bool {
    visible_squares(board, color)[sq.index()]
}

/// Filter board for a player's view: hidden cells empty; enemy on visible squares shown.
pub fn filter_board_for_player(board: &Board, color: Color) -> [Option<Piece>; 64] {
    let vis = visible_squares(board, color);
    let mut out = [None; 64];
    for i in 0..64 {
        let sq = Square::from_index(i).unwrap();
        if let Some(p) = board.get(sq) {
            if p.color == color {
                out[i] = Some(p);
            } else if vis[i] {
                // enemy piece visible (on square or adjacent to friendly)
                out[i] = Some(p);
            }
        }
    }
    out
}

#[derive(Copy, Clone, Eq, PartialEq)]
enum HintRayStep {
    /// Fog or visible empty: can land here and keep scanning (sliding).
    PassThrough,
    /// Visible enemy: can capture here, then stop.
    CaptureStop,
    /// Visible friendly: blocks without landing.
    Block,
}

fn hint_ray_step(board: &Board, color: Color, vis: &[bool; 64], sq: Square) -> HintRayStep {
    if !vis[sq.index()] {
        return HintRayStep::PassThrough;
    }
    match board.get(sq) {
        None => HintRayStep::PassThrough,
        Some(p) if p.color != color => HintRayStep::CaptureStop,
        _ => HintRayStep::Block,
    }
}

fn hint_leap_target(board: &Board, color: Color, vis: &[bool; 64], sq: Square) -> bool {
    if !vis[sq.index()] {
        return true;
    }
    match board.get(sq) {
        None => true,
        Some(p) if p.color != color => true,
        _ => false,
    }
}

/// Pawn capture square: must have an enemy (visible or hidden in fog).
fn hint_pawn_capture_target(board: &Board, color: Color, sq: Square) -> bool {
    match board.get(sq) {
        Some(p) if p.color != color => true,
        _ => false,
    }
}

fn hint_sliding_dirs(kind: PieceKind) -> &'static [(i8, i8)] {
    match kind {
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
        _ => &[],
    }
}

fn hint_ray_targets(
    board: &Board,
    color: Color,
    from: Square,
    vis: &[bool; 64],
    dirs: &[(i8, i8)],
) -> Vec<Square> {
    let mut out = Vec::new();
    for (df, dr) in dirs {
        let mut f = from.file as i8 + df;
        let mut r = from.rank as i8 + dr;
        while let Some(s) = Square::new(f as u8, r as u8) {
            match hint_ray_step(board, color, vis, s) {
                HintRayStep::PassThrough => {
                    out.push(s);
                    f += df;
                    r += dr;
                }
                HintRayStep::CaptureStop => {
                    out.push(s);
                    break;
                }
                HintRayStep::Block => break,
            }
        }
    }
    out
}

fn pawn_dir(color: Color) -> i8 {
    if color == Color::White { 1 } else { -1 }
}

fn pawn_start_rank(color: Color) -> u8 {
    if color == Color::White { 1 } else { 6 }
}

/// Move-hint destinations: fog squares count as empty; visible friendlies and enemies block rays.
pub fn hint_reachable_from(board: &Board, color: Color, from: Square) -> Vec<Square> {
    let Some(piece) = board.get(from) else {
        return vec![];
    };
    if piece.color != color {
        return vec![];
    }
    let vis = visible_squares(board, color);
    let mut out = Vec::new();

    match piece.kind {
        PieceKind::Pawn => {
            let dir = pawn_dir(color);
            let mut r = from.rank as i8 + dir;
            if let Some(s) = Square::new(from.file, r as u8) {
                match hint_ray_step(board, color, &vis, s) {
                    HintRayStep::PassThrough => {
                        out.push(s);
                        if from.rank == pawn_start_rank(color) {
                            r += dir;
                            if let Some(s2) = Square::new(from.file, r as u8) {
                                if hint_ray_step(board, color, &vis, s2) == HintRayStep::PassThrough {
                                    out.push(s2);
                                }
                            }
                        }
                    }
                    HintRayStep::CaptureStop => out.push(s),
                    HintRayStep::Block => {}
                }
            }
            for df in [-1i8, 1] {
                if let Some(s) =
                    Square::new((from.file as i8 + df) as u8, (from.rank as i8 + dir) as u8)
                {
                    if hint_pawn_capture_target(board, color, s) {
                        out.push(s);
                    }
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
                if let Some(s) =
                    Square::new((from.file as i8 + df) as u8, (from.rank as i8 + dr) as u8)
                {
                    if hint_leap_target(board, color, &vis, s) {
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
                        if hint_leap_target(board, color, &vis, s) {
                            out.push(s);
                        }
                    }
                }
            }
        }
        PieceKind::Rook | PieceKind::Bishop | PieceKind::Queen => {
            out.extend(hint_ray_targets(
                board,
                color,
                from,
                &vis,
                hint_sliding_dirs(piece.kind),
            ));
        }
    }
    out
}
