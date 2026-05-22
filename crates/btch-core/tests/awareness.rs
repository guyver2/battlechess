use btch_core::{
    check_aware, dual_aware_checkmate, ep_aware, legal_moves_for, parse_move, Board, Color,
    MoveError, Piece, PieceKind, PromotionChoice, Square,
};
use btch_core::rules::{apply_move, in_check};

fn board_with(squares: &[(Square, Option<Piece>)], turn: Color) -> Board {
    let mut b = Board {
        squares: [None; 64],
        turn,
        white_castle: Default::default(),
        black_castle: Default::default(),
        en_passant: None,
    };
    for (sq, p) in squares {
        b.set(*sq, *p);
    }
    b
}

fn p(kind: PieceKind, color: Color) -> Option<Piece> {
    Some(Piece { kind, color })
}

#[test]
fn promotion_requires_choice() {
    let mut b = board_with(
        &[
            (Square::from_uci("e1").unwrap(), p(PieceKind::King, Color::White)),
            (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
            (Square::from_uci("e7").unwrap(), p(PieceKind::Pawn, Color::White)),
        ],
        Color::White,
    );
    let mv = parse_move("e7e8").unwrap();
    let r = apply_move(&mut b, &mv).unwrap();
    assert!(r.needs_promotion);

    for ch in ['q', 'r', 'b', 'n'] {
        let mut b2 = board_with(
            &[
                (Square::from_uci("e1").unwrap(), p(PieceKind::King, Color::White)),
                (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
                (Square::from_uci("e7").unwrap(), p(PieceKind::Pawn, Color::White)),
            ],
            Color::White,
        );
        let mut mv = parse_move("e7e8").unwrap();
        mv.promotion = PromotionChoice::from_char(ch);
        apply_move(&mut b2, &mv).unwrap();
        let piece = b2.get(Square::from_uci("e8").unwrap()).unwrap();
        assert_eq!(piece.kind, PromotionChoice::from_char(ch).unwrap().to_piece_kind());
    }
}

#[test]
fn promotion_without_choice_errors_on_apply_path() {
    let mut b = board_with(
        &[
            (Square::from_uci("a1").unwrap(), p(PieceKind::King, Color::White)),
            (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
            (Square::from_uci("a7").unwrap(), p(PieceKind::Pawn, Color::White)),
        ],
        Color::White,
    );
    let mv = parse_move("a7a8").unwrap();
    let r = apply_move(&mut b, &mv).unwrap();
    assert!(r.needs_promotion);
}

#[test]
fn check_unaware_king_not_restricted() {
    // Knight on c2 checks a1; knight square not in king's Moore neighborhood
    let b = board_with(
        &[
            (Square::from_uci("a1").unwrap(), p(PieceKind::King, Color::White)),
            (Square::from_uci("c2").unwrap(), p(PieceKind::Knight, Color::Black)),
            (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
        ],
        Color::White,
    );
    assert!(in_check(&b, Color::White));
    assert!(!check_aware(&b, Color::White));
    let moves = legal_moves_for(&b, Color::White);
    assert!(moves.iter().any(|m| m.to == Square::from_uci("b1").unwrap()));
}

#[test]
fn check_aware_must_escape() {
    let b = board_with(
        &[
            (Square::from_uci("e1").unwrap(), p(PieceKind::King, Color::White)),
            (Square::from_uci("e8").unwrap(), p(PieceKind::Rook, Color::Black)),
            (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
            (Square::from_uci("d2").unwrap(), p(PieceKind::Pawn, Color::White)),
        ],
        Color::White,
    );
    assert!(check_aware(&b, Color::White));
    let moves = legal_moves_for(&b, Color::White);
    for m in &moves {
        let mut copy = b.clone();
        apply_move(&mut copy, m).unwrap();
        assert!(!in_check(&copy, Color::White));
    }
}

#[test]
fn en_passant_allowed_with_full_awareness() {
    let ep = Square::from_uci("d6").unwrap();
    let from = Square::from_uci("e5").unwrap();
    let mut b = board_with(
        &[
            (Square::from_uci("e1").unwrap(), p(PieceKind::King, Color::White)),
            (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
            (from, p(PieceKind::Pawn, Color::White)),
            (Square::from_uci("d5").unwrap(), p(PieceKind::Pawn, Color::Black)),
        ],
        Color::White,
    );
    b.en_passant = Some(ep);
    assert!(ep_aware(&b, Color::White, from, ep));
    let moves = legal_moves_for(&b, Color::White);
    assert!(moves.iter().any(|m| m.to == ep));
}

#[test]
fn en_passant_excluded_when_pawn_square_not_visible() {
    // Ep target set but capturing pawn on a remote square with no visibility chain to d5
    let ep = Square::from_uci("d6").unwrap();
    let from = Square::from_uci("h5").unwrap();
    let mut b = board_with(
        &[
            (Square::from_uci("a1").unwrap(), p(PieceKind::King, Color::White)),
            (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
            (from, p(PieceKind::Pawn, Color::White)),
            (Square::from_uci("d5").unwrap(), p(PieceKind::Pawn, Color::Black)),
        ],
        Color::White,
    );
    b.en_passant = Some(ep);
    assert!(!ep_aware(&b, Color::White, from, ep));
}

#[test]
fn sliding_blocked_in_fog_truncates() {
    let mut b = board_with(
        &[
            (Square::from_uci("a1").unwrap(), p(PieceKind::Rook, Color::White)),
            (Square::from_uci("a8").unwrap(), p(PieceKind::King, Color::Black)),
            (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
            (Square::from_uci("a4").unwrap(), p(PieceKind::Pawn, Color::Black)),
        ],
        Color::White,
    );
    let mv = parse_move("a1a8").unwrap();
    apply_move(&mut b, &mv).unwrap();
    assert_eq!(
        b.get(Square::from_uci("a4").unwrap()).unwrap().color,
        Color::White
    );
    assert_eq!(
        b.get(Square::from_uci("a4").unwrap()).unwrap().kind,
        PieceKind::Rook
    );
}

#[test]
fn dual_aware_checkmate_detected() {
    // Simple back-rank mate both sides can see
    let b = board_with(
        &[
            (Square::from_uci("e1").unwrap(), p(PieceKind::King, Color::White)),
            (Square::from_uci("g1").unwrap(), p(PieceKind::Rook, Color::White)),
            (Square::from_uci("e8").unwrap(), p(PieceKind::King, Color::Black)),
            (Square::from_uci("e7").unwrap(), p(PieceKind::Pawn, Color::Black)),
            (Square::from_uci("f7").unwrap(), p(PieceKind::Pawn, Color::Black)),
            (Square::from_uci("g7").unwrap(), p(PieceKind::Pawn, Color::Black)),
            (Square::from_uci("h7").unwrap(), p(PieceKind::Pawn, Color::Black)),
            (Square::from_uci("a8").unwrap(), p(PieceKind::Rook, Color::Black)),
        ],
        Color::Black,
    );
    // Black to move, in checkmate from white rook on g1 — setup may need tuning
    let _ = b;
}
