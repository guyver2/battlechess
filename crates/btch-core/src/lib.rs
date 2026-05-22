pub mod awareness;
pub mod board;
pub mod rules;
pub mod square;
pub mod visibility;

pub use awareness::{
    check_aware, dual_aware_checkmate, ep_aware, filter_board_for_player, game_end_checkmate,
    legal_moves_for, mate_aware_mated, opponent_sees_mate, winner_if_checkmate,
};
pub use board::Board;
pub use rules::{parse_move, resolve_to_square, ApplyResult, Move, MoveError};
pub use square::{Color, Piece, PieceKind, PromotionChoice, Square};
pub use visibility::hint_reachable_from;
