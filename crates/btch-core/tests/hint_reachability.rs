use btch_core::{hint_reachable_from, Board, Color, Piece, PieceKind, Square};

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
fn queen_slides_through_fog_forward_not_over_visible_blockers() {
    let e4 = Square::from_uci("e4").unwrap();
    let e8 = Square::from_uci("e8").unwrap();
    let d3 = Square::from_uci("d3").unwrap();
    let d4 = Square::from_uci("d4").unwrap();
    let c4 = Square::from_uci("c4").unwrap();
    let b = board_with(
        &[
            (e4, p(PieceKind::Queen, Color::White)),
            (Square::from_uci("e1").unwrap(), p(PieceKind::King, Color::White)),
            (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
            (d3, p(PieceKind::Pawn, Color::White)),
            (d4, p(PieceKind::Rook, Color::Black)),
        ],
        Color::White,
    );
    let reach = hint_reachable_from(&b, Color::White, e4);
    assert!(
        reach.contains(&e8),
        "queen should be advised to reach rank 8 through fog: {reach:?}"
    );
    assert!(
        !reach.contains(&d3),
        "should not advise moving onto visible friendly pawn"
    );
    assert!(
        reach.contains(&d4),
        "should advise capture on visible blocking rook"
    );
    assert!(
        !reach.contains(&c4),
        "should not advise squares beyond a visible blocker on the same ray"
    );
    assert!(
        !reach.iter().any(|s| s.file < e4.file && s.rank < e4.rank),
        "backward diagonal should be blocked by visible friendly on d3: {reach:?}"
    );
}

#[test]
fn pawn_diagonal_hints_only_when_enemy_present() {
    let e4 = Square::from_uci("e4").unwrap();
    let d5 = Square::from_uci("d5").unwrap();
    let f5 = Square::from_uci("f5").unwrap();
    let e5 = Square::from_uci("e5").unwrap();
    let b = board_with(
        &[
            (e4, p(PieceKind::Pawn, Color::White)),
            (Square::from_uci("e1").unwrap(), p(PieceKind::King, Color::White)),
            (Square::from_uci("h8").unwrap(), p(PieceKind::King, Color::Black)),
            (d5, p(PieceKind::Pawn, Color::Black)),
        ],
        Color::White,
    );
    let reach = hint_reachable_from(&b, Color::White, e4);
    assert!(reach.contains(&e5), "forward");
    assert!(reach.contains(&d5), "capture visible enemy");
    assert!(!reach.contains(&f5), "no hint on empty diagonal");
}
