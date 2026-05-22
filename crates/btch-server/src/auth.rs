use argon2::{
    password_hash::{rand_core::OsRng, PasswordHash, PasswordHasher, PasswordVerifier, SaltString},
    Argon2,
};
use sqlx::SqlitePool;

#[derive(Debug, Clone, sqlx::FromRow)]
pub struct User {
    pub id: i64,
    pub username: String,
    pub email: Option<String>,
    pub password_hash: String,
    pub avatar_id: i64,
    pub elo: i32,
}

pub fn hash_password(password: &str) -> Result<String, password_hash::Error> {
    let salt = SaltString::generate(&mut OsRng);
    let hash = Argon2::default().hash_password(password.as_bytes(), &salt)?;
    Ok(hash.to_string())
}

pub fn verify_password(password: &str, hash: &str) -> bool {
    PasswordHash::new(hash)
        .ok()
        .and_then(|h| Argon2::default().verify_password(password.as_bytes(), &h).ok())
        .is_some()
}

pub async fn create_user(
    pool: &SqlitePool,
    username: &str,
    email: Option<&str>,
    password: &str,
    avatar_id: i64,
) -> Result<User, String> {
    let hash = hash_password(password).map_err(|e| e.to_string())?;
    let id: i64 = sqlx::query_scalar(
        "INSERT INTO users (username, email, password_hash, avatar_id) VALUES (?, ?, ?, ?) RETURNING id",
    )
    .bind(username)
    .bind(email)
    .bind(&hash)
    .bind(avatar_id)
    .fetch_one(pool)
    .await
    .map_err(|e| {
        if e.to_string().contains("UNIQUE") {
            "Username already taken".to_string()
        } else {
            e.to_string()
        }
    })?;
    get_user_by_id(pool, id).await.map_err(|e| e.to_string())
}

pub async fn get_user_by_id(pool: &SqlitePool, id: i64) -> Result<User, sqlx::Error> {
    sqlx::query_as("SELECT id, username, email, password_hash, avatar_id, elo FROM users WHERE id = ?")
        .bind(id)
        .fetch_one(pool)
        .await
}

pub async fn get_user_by_username(pool: &SqlitePool, username: &str) -> Result<Option<User>, sqlx::Error> {
    sqlx::query_as("SELECT id, username, email, password_hash, avatar_id, elo FROM users WHERE username = ?")
        .bind(username)
        .fetch_one(pool)
        .await
        .map(|u| Some(u))
        .or_else(|e| {
            if matches!(e, sqlx::Error::RowNotFound) {
                Ok(None)
            } else {
                Err(e)
            }
        })
}

#[derive(Debug, Clone, sqlx::FromRow)]
pub struct LeaderboardEntry {
    pub id: i64,
    pub username: String,
    pub elo: i32,
}

pub async fn list_leaderboard(pool: &SqlitePool, limit: i64) -> Result<Vec<LeaderboardEntry>, sqlx::Error> {
    sqlx::query_as(
        "SELECT id, username, elo FROM users ORDER BY elo DESC, username ASC LIMIT ?",
    )
    .bind(limit)
    .fetch_all(pool)
    .await
}

pub async fn authenticate(
    pool: &SqlitePool,
    username: &str,
    password: &str,
) -> Result<Option<User>, sqlx::Error> {
    let Some(user) = get_user_by_username(pool, username).await? else {
        return Ok(None);
    };
    if verify_password(password, &user.password_hash) {
        Ok(Some(user))
    } else {
        Ok(None)
    }
}
