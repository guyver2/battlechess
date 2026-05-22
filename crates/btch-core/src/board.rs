use crate::square::{Color, Piece, PieceKind, Square};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub struct CastlingRights {
    pub kingside: bool,
    pub queenside: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Board {
    pub squares: [Option<Piece>; 64],
    pub turn: Color,
    pub white_castle: CastlingRights,
    pub black_castle: CastlingRights,
    pub en_passant: Option<Square>,
}

impl Board {
    pub fn standard() -> Self {
        let mut b = Self {
            squares: [None; 64],
            turn: Color::White,
            white_castle: CastlingRights {
                kingside: true,
                queenside: true,
            },
            black_castle: CastlingRights {
                kingside: true,
                queenside: true,
            },
            en_passant: None,
        };
        let back = |rank: u8, color: Color| {
            [
                PieceKind::Rook,
                PieceKind::Knight,
                PieceKind::Bishop,
                PieceKind::Queen,
                PieceKind::King,
                PieceKind::Bishop,
                PieceKind::Knight,
                PieceKind::Rook,
            ]
            .into_iter()
            .enumerate()
            .map(move |(f, k)| {
                (
                    Square::new(f as u8, rank).unwrap(),
                    Some(Piece { kind: k, color }),
                )
            })
        };
        for (sq, p) in back(0, Color::White).chain(back(7, Color::Black)) {
            b.set(sq, p);
        }
        for f in 0..8 {
            b.set(
                Square::new(f, 1).unwrap(),
                Some(Piece {
                    kind: PieceKind::Pawn,
                    color: Color::White,
                }),
            );
            b.set(
                Square::new(f, 6).unwrap(),
                Some(Piece {
                    kind: PieceKind::Pawn,
                    color: Color::Black,
                }),
            );
        }
        b
    }

    pub fn get(&self, sq: Square) -> Option<Piece> {
        self.squares[sq.index()]
    }

    pub fn set(&mut self, sq: Square, piece: Option<Piece>) {
        self.squares[sq.index()] = piece;
    }

    pub fn king_square(&self, color: Color) -> Option<Square> {
        for i in 0..64 {
            let sq = Square::from_index(i).unwrap();
            if let Some(p) = self.get(sq) {
                if p.kind == PieceKind::King && p.color == color {
                    return Some(sq);
                }
            }
        }
        None
    }
}
