use sqlx::SqlitePool;

pub const DEFAULT_ELO: i32 = 1500;
pub const K_FACTOR: i32 = 32;

/// Expected score for `rating` vs `opponent` (standard Elo, 400-point scale).
pub fn expected_score(rating: f64, opponent: f64) -> f64 {
    1.0 / (1.0 + 10f64.powf((opponent - rating) / 400.0))
}

/// Rating change after one game; `score` is 1.0 win, 0.5 draw, 0.0 loss.
pub fn rating_change(rating: i32, opponent: i32, score: f64) -> i32 {
    let expected = expected_score(rating as f64, opponent as f64);
    (K_FACTOR as f64 * (score - expected)).round() as i32
}

/// Apply Elo once per finished rated game (both human players, clear winner).
pub async fn apply_for_game(pool: &SqlitePool, game_id: i64) -> Result<(), sqlx::Error> {
    let mut tx = pool.begin().await?;

    let row: (Option<i64>, Option<i64>, Option<String>, i32) = sqlx::query_as(
        "SELECT white_user_id, black_user_id, winner, elo_applied FROM games WHERE id = ?",
    )
    .bind(game_id)
    .fetch_one(&mut *tx)
    .await?;

    let (white_id, black_id, winner, elo_applied) = row;
    if elo_applied != 0 {
        tx.commit().await?;
        return Ok(());
    }

    let (Some(white_id), Some(black_id)) = (white_id, black_id) else {
        tx.commit().await?;
        return Ok(());
    };

    let winner = winner.as_deref().unwrap_or("");
    let (white_score, black_score) = match winner {
        "white" => (1.0, 0.0),
        "black" => (0.0, 1.0),
        _ => {
            tx.commit().await?;
            return Ok(());
        }
    };

    let white_elo: i32 = sqlx::query_scalar("SELECT elo FROM users WHERE id = ?")
        .bind(white_id)
        .fetch_one(&mut *tx)
        .await?;
    let black_elo: i32 = sqlx::query_scalar("SELECT elo FROM users WHERE id = ?")
        .bind(black_id)
        .fetch_one(&mut *tx)
        .await?;

    let white_delta = rating_change(white_elo, black_elo, white_score);
    let black_delta = rating_change(black_elo, white_elo, black_score);
    let white_new = white_elo + white_delta;
    let black_new = black_elo + black_delta;

    sqlx::query("UPDATE users SET elo = ? WHERE id = ?")
        .bind(white_new)
        .bind(white_id)
        .execute(&mut *tx)
        .await?;
    sqlx::query("UPDATE users SET elo = ? WHERE id = ?")
        .bind(black_new)
        .bind(black_id)
        .execute(&mut *tx)
        .await?;
    sqlx::query(
        "UPDATE games SET elo_applied = 1, white_elo_delta = ?, black_elo_delta = ? WHERE id = ?",
    )
    .bind(white_delta)
    .bind(black_delta)
    .bind(game_id)
    .execute(&mut *tx)
    .await?;

    tx.commit().await
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn equal_ratings_win_is_sixteen() {
        assert_eq!(rating_change(1500, 1500, 1.0), 16);
        assert_eq!(rating_change(1500, 1500, 0.0), -16);
    }

    #[test]
    fn heavy_favorite_gains_little() {
        assert!(rating_change(1900, 1500, 1.0) <= 4);
        assert!(rating_change(1500, 1900, 1.0) >= 28);
    }
}
