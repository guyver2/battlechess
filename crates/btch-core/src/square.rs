use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Color {
    White,
    Black,
}

impl Color {
    pub fn opposite(self) -> Self {
        match self {
            Color::White => Color::Black,
            Color::Black => Color::White,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum PieceKind {
    King,
    Queen,
    Rook,
    Bishop,
    Knight,
    Pawn,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Piece {
    pub kind: PieceKind,
    pub color: Color,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Square {
    pub file: u8,
    pub rank: u8,
}

impl Square {
    pub const fn new(file: u8, rank: u8) -> Option<Self> {
        if file < 8 && rank < 8 {
            Some(Self { file, rank })
        } else {
            None
        }
    }

    pub fn from_uci(s: &str) -> Option<Self> {
        let bytes = s.as_bytes();
        if bytes.len() != 2 {
            return None;
        }
        let file = bytes[0].wrapping_sub(b'a');
        let rank = bytes[1].wrapping_sub(b'1');
        Self::new(file, rank)
    }

    pub fn to_uci(self) -> String {
        format!("{}{}", (b'a' + self.file) as char, self.rank + 1)
    }

    pub fn index(self) -> usize {
        self.rank as usize * 8 + self.file as usize
    }

    pub fn from_index(i: usize) -> Option<Self> {
        if i < 64 {
            Some(Self {
                file: (i % 8) as u8,
                rank: (i / 8) as u8,
            })
        } else {
            None
        }
    }

    pub fn chebyshev_distance(self, other: Self) -> u8 {
        let df = self.file.abs_diff(other.file);
        let dr = self.rank.abs_diff(other.rank);
        df.max(dr)
    }
}

impl fmt::Display for Square {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.to_uci())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PromotionChoice {
    Queen,
    Rook,
    Bishop,
    Knight,
}

impl PromotionChoice {
    pub fn from_char(c: char) -> Option<Self> {
        match c {
            'q' | 'Q' => Some(Self::Queen),
            'r' | 'R' => Some(Self::Rook),
            'b' | 'B' => Some(Self::Bishop),
            'n' | 'N' => Some(Self::Knight),
            _ => None,
        }
    }

    pub fn to_piece_kind(self) -> PieceKind {
        match self {
            Self::Queen => PieceKind::Queen,
            Self::Rook => PieceKind::Rook,
            Self::Bishop => PieceKind::Bishop,
            Self::Knight => PieceKind::Knight,
        }
    }
}
