mod auth;
mod db;
mod elo;
mod fragments;
mod game;
mod notify;
mod sse;
mod templates;

use askama::Template;
use axum::{
    extract::{Path, Query, State},
    http::{HeaderMap, StatusCode},
    response::{Html, IntoResponse, Redirect, Response},
    routing::{get, post},
    Form, Router,
};
use datastar::prelude::ExecuteScript;
use serde::Deserialize;
use sqlx::SqlitePool;
use std::sync::Arc;
use tower_http::services::ServeDir;
use tower_sessions::{Session, SessionManagerLayer};
use tower_sessions_sqlx_store::SqliteStore;

use auth::{authenticate, create_user, get_user_by_id, list_leaderboard, User};
use game::{
    apply_game_move, assign_random_colors, build_replay_payload, cancel_waiting_game,
    can_access_replay, create_waiting_random_game, find_joinable_waiting_random_game,
    find_own_waiting_random_game, load_board_or_standard, resign_game, try_join_waiting_random_game,
    count_finished_games, create_game, filtered_view, get_game_by_uuid, list_finished_games,
    elo_summary_for_player, format_game_datetime, game_played_at, game_result_label,
    legal_moves_json, load_board,
    load_replay_snaps,
    parse_replay_initial_step, player_color, replay_player_headers, username_for,
    ARCHIVE_PAGE_SIZE, GameRow,
};
use notify::NotifyHub;
use templates::{
    ArchiveListItem, ArchiveTemplate, GameListItem, GameTemplate, InviteView, LeaderboardRow,
    LeaderboardTemplate, LobbyTemplate, SentInviteView, LoginTemplate, RegisterTemplate,
    ReplayTemplate,
};

#[derive(Clone)]
pub struct AppState {
    pool: SqlitePool,
    notify: NotifyHub,
}

#[derive(Deserialize)]
struct LoginForm {
    username: String,
    password: String,
}

#[derive(Deserialize)]
struct RegisterForm {
    username: String,
    password: String,
}

#[derive(Deserialize)]
struct InviteForm {
    username: String,
    message: Option<String>,
}

#[derive(Deserialize)]
struct MoveForm {
    r#move: String,
}

#[derive(Deserialize)]
struct PromoteForm {
    piece: String,
    pending_move: String,
}

#[derive(Deserialize)]
struct ArchiveQuery {
    page: Option<i64>,
}

#[derive(Deserialize)]
struct LobbyQuery {
    invite_error: Option<String>,
}

fn invite_error_message(code: &str) -> Option<&'static str> {
    match code {
        "self" => Some("You cannot invite yourself."),
        "unknown_user" => Some("User not found."),
        "ongoing_game" => Some("You already have an active game with this player."),
        "pending_invite" => Some("There is already a pending invite with this player."),
        "declined_invite" => {
            Some("Delete your rejected invite to this player before sending another.")
        }
        "limit" => Some("You already have 5 pending invites outstanding."),
        _ => None,
    }
}

async fn has_active_game_with(pool: &SqlitePool, user_id: i64, other_id: i64) -> bool {
    sqlx::query_scalar::<_, i64>(
        "SELECT 1 FROM games WHERE status != 'over'
         AND ((white_user_id = ? AND black_user_id = ?) OR (white_user_id = ? AND black_user_id = ?))
         LIMIT 1",
    )
    .bind(user_id)
    .bind(other_id)
    .bind(other_id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .ok()
    .flatten()
    .is_some()
}

async fn has_declined_sent_invite_with(pool: &SqlitePool, user_id: i64, other_id: i64) -> bool {
    sqlx::query_scalar::<_, i64>(
        "SELECT 1 FROM invitations WHERE status = 'declined' AND from_user_id = ? AND to_user_id = ? LIMIT 1",
    )
    .bind(user_id)
    .bind(other_id)
    .fetch_optional(pool)
    .await
    .ok()
    .flatten()
    .is_some()
}

async fn has_pending_invite_with(pool: &SqlitePool, user_id: i64, other_id: i64) -> bool {
    sqlx::query_scalar::<_, i64>(
        "SELECT 1 FROM invitations WHERE status = 'pending'
         AND ((from_user_id = ? AND to_user_id = ?) OR (from_user_id = ? AND to_user_id = ?))
         LIMIT 1",
    )
    .bind(user_id)
    .bind(other_id)
    .bind(other_id)
    .bind(user_id)
    .fetch_optional(pool)
    .await
    .ok()
    .flatten()
    .is_some()
}

#[derive(Deserialize)]
struct ReplayQuery {
    step: Option<String>,
}

const USER_KEY: &str = "user_id";

pub async fn current_user(pool: &SqlitePool, session: &Session) -> Option<User> {
    let id: i64 = session.get(USER_KEY).await.ok()??;
    get_user_by_id(pool, id).await.ok()
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();
    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "sqlite:./battlechess.db?mode=rwc".into());
    let port: u16 = std::env::var("PORT")
        .ok()
        .and_then(|p| p.parse().ok())
        .unwrap_or(3100);

    let pool = db::connect(&database_url).await.expect("db connect");
    let session_store = SqliteStore::new(pool.clone());
    session_store.migrate().await.expect("session migrate");
    let session_layer = SessionManagerLayer::new(session_store).with_secure(false);

    let state = Arc::new(AppState {
        pool,
        notify: NotifyHub::default(),
    });

    let app = Router::new()
        .route("/", get(index))
        .route("/login", get(login_page).post(login_post))
        .route("/register", get(register_page).post(register_post))
        .route("/logout", post(logout))
        .route("/lobby", get(lobby))
        .route("/lobby/events", get(sse::lobby_events))
        .route("/queue", post(join_queue))
        .route("/invites", post(send_invite))
        .route("/invites/{id}/accept", post(accept_invite))
        .route("/invites/{id}/decline", post(decline_invite))
        .route("/invites/{id}/delete", post(delete_invite))
        .route("/games/{uuid}", get(game_page))
        .route("/games/{uuid}/events", get(sse::game_events))
        .route("/games/{uuid}/move", post(game_move))
        .route("/games/{uuid}/promote", post(game_promote))
        .route("/games/{uuid}/resign", post(game_resign))
        .route("/games/{uuid}/cancel", post(game_cancel_waiting))
        .route("/games/{uuid}/replay", get(replay_page))
        .route("/archive", get(archive_page))
        .route("/leaderboard", get(leaderboard_page))
        .nest_service("/static", ServeDir::new("static"))
        .layer(session_layer)
        .with_state(state);

    let addr = format!("0.0.0.0:{port}");
    let listener = tokio::net::TcpListener::bind(&addr).await.expect("bind");
    tracing::info!("BattleChess listening on http://{addr}");
    axum::serve(listener, app).await.expect("serve");
}

fn html<T: Template>(t: T) -> Html<String> {
    Html(t.render().unwrap())
}

async fn index(session: Session, State(st): State<Arc<AppState>>) -> impl IntoResponse {
    if current_user(&st.pool, &session).await.is_some() {
        Redirect::to("/lobby")
    } else {
        Redirect::to("/login")
    }
}

async fn login_page() -> Html<String> {
    html(LoginTemplate {
        user: None,
        error: None,
    })
}

async fn login_post(
    State(st): State<Arc<AppState>>,
    session: Session,
    Form(f): Form<LoginForm>,
) -> Response {
    match authenticate(&st.pool, &f.username, &f.password).await {
        Ok(Some(u)) => {
            session.insert(USER_KEY, u.id).await.ok();
            Redirect::to("/lobby").into_response()
        }
        _ => html(LoginTemplate {
            user: None,
            error: Some("Invalid credentials".into()),
        })
        .into_response(),
    }
}

async fn register_page() -> Html<String> {
    html(RegisterTemplate {
        user: None,
        error: None,
    })
}

async fn register_post(
    State(st): State<Arc<AppState>>,
    session: Session,
    Form(f): Form<RegisterForm>,
) -> Response {
    match create_user(&st.pool, &f.username, None, &f.password, 0)
    .await
    {
        Ok(u) => {
            session.insert(USER_KEY, u.id).await.ok();
            Redirect::to("/lobby").into_response()
        }
        Err(e) => html(RegisterTemplate {
            user: None,
            error: Some(e),
        })
        .into_response(),
    }
}

async fn logout(session: Session) -> Redirect {
    session.delete().await.ok();
    Redirect::to("/login")
}

fn format_invite_sent_on(created_at: &str) -> String {
    format_game_datetime(created_at)
}

pub async fn fetch_invites(pool: &SqlitePool, user_id: i64) -> Vec<InviteView> {
    sqlx::query_as::<_, (i64, String, String, String)>(
        "SELECT i.id, u.username, i.message, i.created_at FROM invitations i JOIN users u ON u.id = i.from_user_id WHERE i.to_user_id = ? AND i.status = 'pending' ORDER BY i.created_at DESC",
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .unwrap_or_default()
    .into_iter()
    .map(|(id, from_name, message, created_at)| InviteView {
        id,
        from_name,
        message,
        sent_on: format_invite_sent_on(&created_at),
    })
    .collect()
}

fn invite_status_label(status: &str) -> &'static str {
    match status {
        "accepted" => "Accepted",
        "declined" => "Rejected",
        _ => "Pending",
    }
}

pub async fn fetch_sent_invites(pool: &SqlitePool, user_id: i64) -> Vec<SentInviteView> {
    sqlx::query_as::<_, (i64, String, String, String, String, Option<String>)>(
        r#"SELECT i.id, u.username, i.message, i.status, i.created_at,
            COALESCE(
                (SELECT g.uuid FROM games g WHERE g.id = i.game_id AND g.status != 'over'),
                (SELECT g.uuid FROM games g
                 WHERE g.source = 'invite' AND g.status != 'over'
                 AND ((g.white_user_id = i.from_user_id AND g.black_user_id = i.to_user_id)
                      OR (g.white_user_id = i.to_user_id AND g.black_user_id = i.from_user_id))
                 ORDER BY g.id DESC LIMIT 1)
            ) AS game_uuid
        FROM invitations i
        JOIN users u ON u.id = i.to_user_id
        WHERE i.from_user_id = ?
        AND (
            i.status != 'accepted'
            OR COALESCE(
                (SELECT g.uuid FROM games g WHERE g.id = i.game_id AND g.status != 'over'),
                (SELECT g.uuid FROM games g
                 WHERE g.source = 'invite' AND g.status != 'over'
                 AND ((g.white_user_id = i.from_user_id AND g.black_user_id = i.to_user_id)
                      OR (g.white_user_id = i.to_user_id AND g.black_user_id = i.from_user_id))
                 ORDER BY g.id DESC LIMIT 1)
            ) IS NOT NULL
        )
        ORDER BY i.created_at DESC
        LIMIT 50"#,
    )
    .bind(user_id)
    .fetch_all(pool)
    .await
    .unwrap_or_default()
    .into_iter()
    .map(|(id, to_name, message, status, created_at, game_uuid)| SentInviteView {
        id,
        to_name,
        message,
        status_label: invite_status_label(&status).to_string(),
        status,
        sent_on: format_invite_sent_on(&created_at),
        game_uuid,
    })
    .collect()
}

async fn lobby(
    State(st): State<Arc<AppState>>,
    session: Session,
    Query(q): Query<LobbyQuery>,
) -> Result<Html<String>, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };

    let received = fetch_invites(&st.pool, user.id).await;
    let sent = fetch_sent_invites(&st.pool, user.id).await;
    let games = list_user_games(&st.pool, user.id).await;

    Ok(html(LobbyTemplate {
        user: Some(user.clone()),
        username: user.username,
        elo: user.elo,
        invite_msg: q
            .invite_error
            .as_deref()
            .and_then(invite_error_message)
            .map(str::to_string),
        received,
        sent,
        games,
    }))
}

pub async fn list_user_games(pool: &SqlitePool, user_id: i64) -> Vec<GameListItem> {
    let rows: Vec<GameRow> = sqlx::query_as(
        "SELECT id, uuid, white_user_id, black_user_id, status, turn, winner, resigned_by, \
         elo_applied, white_elo_delta, black_elo_delta FROM games \
         WHERE (white_user_id = ? OR black_user_id = ?) AND status != 'over' ORDER BY id DESC",
    )
    .bind(user_id)
    .bind(user_id)
    .fetch_all(pool)
    .await
    .unwrap_or_default();

    let mut out = Vec::new();
    for g in rows {
        let opp_id = if g.white_user_id == Some(user_id) {
            g.black_user_id
        } else {
            g.white_user_id
        };
        let opponent = if let Some(oid) = opp_id {
            sqlx::query_scalar::<_, String>("SELECT username FROM users WHERE id = ?")
                .bind(oid)
                .fetch_optional(pool)
                .await
                .ok()
                .flatten()
                .unwrap_or_else(|| "?".into())
        } else {
            "waiting".into()
        };
        let your_turn = g.status != "over"
            && player_color(&g, user_id)
                .map(|c| {
                    (c == btch_core::Color::White && g.turn == "white")
                        || (c == btch_core::Color::Black && g.turn == "black")
                })
                .unwrap_or(false);
        out.push(GameListItem {
            uuid: g.uuid,
            opponent,
            status: g.status,
            your_turn,
        });
    }
    out
}

fn redirect_to_game(uuid: &str, headers: &HeaderMap) -> Response {
    if sse::is_datastar(headers) {
        let script = ExecuteScript::new(format!("window.location.href='/games/{uuid}'"));
        sse::sse_from_events(vec![script.write_as_axum_sse_event()]).into_response()
    } else {
        Redirect::to(&format!("/games/{uuid}")).into_response()
    }
}

async fn join_queue(
    State(st): State<Arc<AppState>>,
    session: Session,
    headers: HeaderMap,
) -> Result<Response, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };

    sqlx::query("DELETE FROM match_queue WHERE user_id = ?")
        .bind(user.id)
        .execute(&st.pool)
        .await
        .ok();

    if let Ok(Some(g)) = find_own_waiting_random_game(&st.pool, user.id).await {
        return Ok(redirect_to_game(&g.uuid, &headers));
    }

    if let Ok(Some(waiting)) = find_joinable_waiting_random_game(&st.pool, user.id).await {
        if let Ok(Some(g)) = try_join_waiting_random_game(&st.pool, waiting.id, user.id).await {
            if let Some(host_id) = waiting.white_user_id.or(waiting.black_user_id) {
                st.notify.notify_lobby_user(host_id);
            }
            st.notify.notify_game(&g.uuid);
            st.notify.notify_lobby_user(user.id);
            return Ok(redirect_to_game(&g.uuid, &headers));
        }
    }

    if let Ok(g) = create_waiting_random_game(&st.pool, user.id).await {
        st.notify.notify_lobby_user(user.id);
        return Ok(redirect_to_game(&g.uuid, &headers));
    }

    Ok(Redirect::to("/lobby").into_response())
}

async fn send_invite(
    State(st): State<Arc<AppState>>,
    session: Session,
    Form(f): Form<InviteForm>,
) -> Result<Redirect, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };
    let Some(target) = auth::get_user_by_username(&st.pool, &f.username)
        .await
        .ok()
        .flatten()
    else {
        return Ok(Redirect::to("/lobby?invite_error=unknown_user"));
    };
    if target.id == user.id {
        return Ok(Redirect::to("/lobby?invite_error=self"));
    }
    if has_active_game_with(&st.pool, user.id, target.id).await {
        return Ok(Redirect::to("/lobby?invite_error=ongoing_game"));
    }
    if has_pending_invite_with(&st.pool, user.id, target.id).await {
        return Ok(Redirect::to("/lobby?invite_error=pending_invite"));
    }
    if has_declined_sent_invite_with(&st.pool, user.id, target.id).await {
        return Ok(Redirect::to("/lobby?invite_error=declined_invite"));
    }
    let pending: i64 = sqlx::query_scalar(
        "SELECT COUNT(*) FROM invitations WHERE from_user_id = ? AND status = 'pending'",
    )
    .bind(user.id)
    .fetch_one(&st.pool)
    .await
    .unwrap_or(0);
    if pending >= 5 {
        return Ok(Redirect::to("/lobby?invite_error=limit"));
    }
    sqlx::query(
        "INSERT INTO invitations (from_user_id, to_user_id, message) VALUES (?, ?, ?)",
    )
    .bind(user.id)
    .bind(target.id)
    .bind(f.message.unwrap_or_default())
    .execute(&st.pool)
    .await
    .ok();
    st.notify.notify_lobby_user(target.id);
    st.notify.notify_lobby_user(user.id);
    Ok(Redirect::to("/lobby"))
}

async fn accept_invite(
    State(st): State<Arc<AppState>>,
    session: Session,
    Path(id): Path<i64>,
    headers: HeaderMap,
) -> Result<Response, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };
    let inv: Option<(i64,)> = sqlx::query_as(
        "SELECT from_user_id FROM invitations WHERE id = ? AND to_user_id = ? AND status = 'pending'",
    )
    .bind(id)
    .bind(user.id)
    .fetch_optional(&st.pool)
    .await
    .ok()
    .flatten();
    if let Some((from_id,)) = inv {
        let (white, black) = assign_random_colors(from_id, user.id);
        if let Ok(g) = create_game(&st.pool, white, black, "invite").await {
            sqlx::query("UPDATE invitations SET status = 'accepted', game_id = ? WHERE id = ?")
                .bind(g.id)
                .bind(id)
                .execute(&st.pool)
                .await
                .ok();
            st.notify.notify_lobby_user(from_id);
            st.notify.notify_lobby_user(user.id);
            if sse::is_datastar(&headers) {
                let script = ExecuteScript::new(format!(
                    "window.location.href='/games/{}'",
                    g.uuid
                ));
                return Ok(sse::sse_from_events(vec![script.write_as_axum_sse_event()]).into_response());
            }
            return Ok(Redirect::to(&format!("/games/{}", g.uuid)).into_response());
        }
    }
    Ok(Redirect::to("/lobby").into_response())
}

async fn delete_invite(
    State(st): State<Arc<AppState>>,
    session: Session,
    Path(id): Path<i64>,
    headers: HeaderMap,
) -> Result<Response, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };

    let to_id: Option<i64> = sqlx::query_scalar(
        "DELETE FROM invitations WHERE id = ? AND from_user_id = ? AND status IN ('pending', 'declined') RETURNING to_user_id",
    )
    .bind(id)
    .bind(user.id)
    .fetch_optional(&st.pool)
    .await
    .ok()
    .flatten();

    if let Some(to_id) = to_id {
        st.notify.notify_lobby_user(to_id);
    }
    st.notify.notify_lobby_user(user.id);

    if sse::is_datastar(&headers) {
        let sent = fetch_sent_invites(&st.pool, user.id).await;
        let patch = sse::patch_inner("#sent-invites", fragments::sent_invites_html(&sent));
        return Ok(sse::sse_from_events(vec![patch]).into_response());
    }
    Ok(Redirect::to("/lobby").into_response())
}

async fn decline_invite(
    State(st): State<Arc<AppState>>,
    session: Session,
    Path(id): Path<i64>,
    headers: HeaderMap,
) -> Result<Response, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };
    let from_id: Option<i64> = sqlx::query_scalar(
        "SELECT from_user_id FROM invitations WHERE id = ? AND to_user_id = ?",
    )
    .bind(id)
    .bind(user.id)
    .fetch_optional(&st.pool)
    .await
    .ok()
    .flatten();

    sqlx::query("UPDATE invitations SET status = 'declined' WHERE id = ? AND to_user_id = ?")
        .bind(id)
        .bind(user.id)
        .execute(&st.pool)
        .await
        .ok();

    if let Some(fid) = from_id {
        st.notify.notify_lobby_user(fid);
    }
    st.notify.notify_lobby_user(user.id);

    if sse::is_datastar(&headers) {
        let received = fetch_invites(&st.pool, user.id).await;
        let sent = fetch_sent_invites(&st.pool, user.id).await;
        return Ok(
            sse::sse_from_events(vec![
                sse::patch_inner("#invites", fragments::invites_html(&received)),
                sse::patch_inner("#sent-invites", fragments::sent_invites_html(&sent)),
            ])
            .into_response(),
        );
    }
    Ok(Redirect::to("/lobby").into_response())
}

const LEADERBOARD_LIMIT: i64 = 100;

async fn leaderboard_page(
    State(st): State<Arc<AppState>>,
    session: Session,
) -> Result<Html<String>, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };
    let entries = list_leaderboard(&st.pool, LEADERBOARD_LIMIT)
        .await
        .unwrap_or_default();
    let players: Vec<LeaderboardRow> = entries
        .into_iter()
        .enumerate()
        .map(|(i, e)| LeaderboardRow {
            rank: i + 1,
            username: e.username,
            elo: e.elo,
            is_you: e.id == user.id,
        })
        .collect();
    Ok(html(LeaderboardTemplate {
        user: Some(user),
        players,
    }))
}

async fn archive_page(
    State(st): State<Arc<AppState>>,
    session: Session,
    Query(q): Query<ArchiveQuery>,
) -> Result<Html<String>, Redirect> {
    let user = current_user(&st.pool, &session).await;
    let page = q.page.unwrap_or(1).max(1);
    let total_count = count_finished_games(&st.pool).await.unwrap_or(0);
    let total_pages = if total_count == 0 {
        1
    } else {
        (total_count + ARCHIVE_PAGE_SIZE - 1) / ARCHIVE_PAGE_SIZE
    };
    let page = page.min(total_pages);
    let rows = list_finished_games(&st.pool, page).await.unwrap_or_default();
    let games: Vec<ArchiveListItem> = rows
        .into_iter()
        .map(|g| {
            let white = g.white_name.as_deref().unwrap_or("?");
            let black = g.black_name.as_deref().unwrap_or("?");
            ArchiveListItem {
                uuid: g.uuid,
                white_name: white.into(),
                black_name: black.into(),
                winner_label: game_result_label(
                    g.winner.as_deref(),
                    g.resigned_by.as_deref(),
                    white,
                    black,
                ),
                played_at: g.played_at,
            }
        })
        .collect();
    Ok(html(ArchiveTemplate {
        user,
        games,
        page,
        total_pages,
        total_count,
        has_prev: page > 1,
        has_next: page < total_pages,
    }))
}

async fn replay_page(
    State(st): State<Arc<AppState>>,
    session: Session,
    Path(uuid): Path<String>,
    Query(q): Query<ReplayQuery>,
) -> Result<Html<String>, Redirect> {
    let user = current_user(&st.pool, &session).await;
    let user_id = user.as_ref().map(|u| u.id);
    let game = get_game_by_uuid(&st.pool, &uuid)
        .await
        .ok()
        .flatten()
        .ok_or(Redirect::to("/archive"))?;
    let Some(role) = can_access_replay(&game, user_id) else {
        return Err(Redirect::to("/archive"));
    };
    let snaps = load_replay_snaps(&st.pool, game.id)
        .await
        .map_err(|_| Redirect::to("/archive"))?;
    let white_name = username_for(&st.pool, game.white_user_id).await;
    let black_name = username_for(&st.pool, game.black_user_id).await;
    let color = user_id.and_then(|id| player_color(&game, id));
    let color_s = color.map(|c| {
        if c == btch_core::Color::White {
            "white"
        } else {
            "black"
        }
    });
    let payload = build_replay_payload(
        &game,
        &white_name,
        &black_name,
        &snaps,
        role,
        color_s,
    );
    let replay_json = serde_json::to_string(&payload).unwrap_or_else(|_| "{}".into());
    let max_move = snaps.last().map(|s| s.move_number).unwrap_or(0);
    let initial_step = parse_replay_initial_step(q.step.as_deref(), max_move);
    let show_live_link = role == "player" && game.status == "started";
    let played_at_raw = game_played_at(&st.pool, game.id).await;
    let played_at = format_game_datetime(&played_at_raw);
    let (white_player, black_player) = replay_player_headers(
        &white_name,
        &black_name,
        game.winner.as_deref(),
        game.resigned_by.as_deref(),
    );
    Ok(html(ReplayTemplate {
        user,
        white_player,
        black_player,
        played_at,
        show_live_link,
        live_uuid: game.uuid.clone(),
        replay_json,
        initial_step,
    }))
}

async fn game_page(
    State(st): State<Arc<AppState>>,
    session: Session,
    Path(uuid): Path<String>,
) -> Result<Html<String>, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };
    let game = get_game_by_uuid(&st.pool, &uuid)
        .await
        .ok()
        .flatten()
        .ok_or(Redirect::to("/lobby"))?;
    render_game_page(&st.pool, &game, &user, false, "").await
}

async fn render_game_page(
    pool: &SqlitePool,
    game: &GameRow,
    user: &User,
    needs_promotion: bool,
    pending_move: &str,
) -> Result<Html<String>, Redirect> {
    let color = player_color(game, user.id).ok_or(Redirect::to("/lobby"))?;
    let board = load_board_or_standard(pool, game).await;
    let view = filtered_view(&board, color);
    let visible = btch_core::visibility::visible_squares(&board, color);
    let board_html = fragments::board_inner_html(&view, &visible);
    let (captured_white_html, captured_black_html) = fragments::captured_bars_from_board(&board);
    let waiting = game.status == "waiting";
    let game_over = game.status == "over";
    let your_turn = !waiting
        && !game_over
        && ((color == btch_core::Color::White && game.turn == "white")
            || (color == btch_core::Color::Black && game.turn == "black"));
    let color_s = if color == btch_core::Color::White {
        "white"
    } else {
        "black"
    };
    let winner = game.winner.as_deref().unwrap_or("");
    let legal_json = if your_turn && !game_over && !needs_promotion {
        legal_moves_json(&board, color)
    } else {
        "{}".into()
    };
    let controls = fragments::promotion_or_move_html(
        &game.uuid,
        needs_promotion,
        pending_move,
        your_turn,
        game_over,
        waiting,
        &legal_json,
    );
    let elo_summary = if game_over {
        elo_summary_for_player(pool, game, user.id).await
    } else {
        None
    };
    let overlay_html = if waiting {
        fragments::waiting_overlay_html()
    } else {
        fragments::game_over_overlay_html(game_over, winner, color_s, &game.uuid, elo_summary)
    };
    Ok(html(GameTemplate {
        user: Some(user.clone()),
        uuid: game.uuid.clone(),
        player_color: color_s.to_string(),
        status_html: fragments::game_status_html(
            color_s,
            &game.turn,
            btch_core::check_aware(&board, color),
            game_over,
            waiting,
        ),
        overlay_html,
        captured_white_html,
        board_html,
        captured_black_html,
        controls_html: controls,
    }))
}

async fn game_move(
    State(st): State<Arc<AppState>>,
    session: Session,
    Path(uuid): Path<String>,
    headers: HeaderMap,
    Form(f): Form<MoveForm>,
) -> Result<Response, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };
    let game = get_game_by_uuid(&st.pool, &uuid)
        .await
        .ok()
        .flatten()
        .ok_or(Redirect::to("/lobby"))?;

    match apply_game_move(&st.pool, &game, user.id, &f.r#move, None).await {
        Ok(out) if out.needs_promotion => {
            st.notify.notify_game(&uuid);
            if sse::is_datastar(&headers) {
                return sse::respond_game_view(
                    &st.pool,
                    &st.notify,
                    &uuid,
                    &user,
                    true,
                    &f.r#move,
                    &headers,
                )
                .await
                .map_err(|_| Redirect::to("/lobby"));
            }
            return render_game_page(&st.pool, &game, &user, true, &f.r#move)
                .await
                .map(|h| h.into_response())
                .map_err(|r: Redirect| r);
        }
        Ok(_) => {
            st.notify.notify_game(&uuid);
            if sse::is_datastar(&headers) {
                return sse::respond_game_view(
                    &st.pool,
                    &st.notify,
                    &uuid,
                    &user,
                    false,
                    "",
                    &headers,
                )
                .await
                .map_err(|_| Redirect::to("/lobby"));
            }
            Ok(Redirect::to(&format!("/games/{uuid}")).into_response())
        }
        Err(e) => {
            if sse::is_datastar(&headers) {
                if let Ok(view) =
                    fragments::build_game_view(&st.pool, &game, &user, false, "").await
                {
                    let status = format!(
                        "{}{}",
                        view.status_html,
                        fragments::move_error_html(&e)
                    );
                    return Ok(
                        sse::sse_from_events(vec![
                            sse::patch_inner("#game-status", status),
                            sse::patch_inner("#game-modal", view.overlay_html),
                            sse::patch_inner("#captured-white", view.captured_white_html),
                            sse::patch_inner("#board", view.board_html),
                            sse::patch_inner("#captured-black", view.captured_black_html),
                            sse::patch_inner("#move-area", view.controls_html),
                        ])
                        .into_response(),
                    );
                }
            }
            Ok((StatusCode::BAD_REQUEST, e).into_response())
        }
    }
}

async fn game_cancel_waiting(
    State(st): State<Arc<AppState>>,
    session: Session,
    Path(uuid): Path<String>,
) -> Result<Response, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };
    let game = get_game_by_uuid(&st.pool, &uuid)
        .await
        .ok()
        .flatten()
        .ok_or(Redirect::to("/lobby"))?;

    match cancel_waiting_game(&st.pool, &game, user.id).await {
        Ok(()) => {
            st.notify.notify_lobby_user(user.id);
            Ok(Redirect::to("/lobby").into_response())
        }
        Err(_) => Ok(Redirect::to(&format!("/games/{}", game.uuid)).into_response()),
    }
}

fn notify_game_players_lobby(hub: &NotifyHub, game: &GameRow) {
    if let Some(id) = game.white_user_id {
        hub.notify_lobby_user(id);
    }
    if let Some(id) = game.black_user_id {
        hub.notify_lobby_user(id);
    }
}

async fn game_resign(
    State(st): State<Arc<AppState>>,
    session: Session,
    Path(uuid): Path<String>,
    headers: HeaderMap,
) -> Result<Response, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };
    let game = get_game_by_uuid(&st.pool, &uuid)
        .await
        .ok()
        .flatten()
        .ok_or(Redirect::to("/lobby"))?;

    match resign_game(&st.pool, &game, user.id).await {
        Ok(updated) => {
            st.notify.notify_game(&uuid);
            notify_game_players_lobby(&st.notify, &updated);
            if sse::is_datastar(&headers) {
                return sse::respond_game_view(
                    &st.pool,
                    &st.notify,
                    &uuid,
                    &user,
                    false,
                    "",
                    &headers,
                )
                .await
                .map_err(|_| Redirect::to("/lobby"));
            }
            Ok(Redirect::to(&format!("/games/{uuid}")).into_response())
        }
        Err(e) => {
            if sse::is_datastar(&headers) {
                if let Ok(view) =
                    fragments::build_game_view(&st.pool, &game, &user, false, "").await
                {
                    let status = format!(
                        "{}{}",
                        view.status_html,
                        fragments::move_error_html(&e)
                    );
                    return Ok(
                        sse::sse_from_events(vec![
                            sse::patch_inner("#game-status", status),
                            sse::patch_inner("#move-area", view.controls_html),
                        ])
                        .into_response(),
                    );
                }
            }
            Ok((StatusCode::BAD_REQUEST, e).into_response())
        }
    }
}

async fn game_promote(
    State(st): State<Arc<AppState>>,
    session: Session,
    Path(uuid): Path<String>,
    headers: HeaderMap,
    Form(f): Form<PromoteForm>,
) -> Result<Response, Redirect> {
    let user = match current_user(&st.pool, &session).await {
        Some(u) => u,
        None => return Err(Redirect::to("/login")),
    };
    let game = get_game_by_uuid(&st.pool, &uuid)
        .await
        .ok()
        .flatten()
        .ok_or(Redirect::to("/lobby"))?;
    let ch = f.piece.chars().next().unwrap_or('q');
    match apply_game_move(&st.pool, &game, user.id, &f.pending_move, Some(ch)).await {
        Ok(_) => {
            st.notify.notify_game(&uuid);
            if sse::is_datastar(&headers) {
                return sse::respond_game_view(
                    &st.pool,
                    &st.notify,
                    &uuid,
                    &user,
                    false,
                    "",
                    &headers,
                )
                .await
                .map_err(|_| Redirect::to("/lobby"));
            }
            Ok(Redirect::to(&format!("/games/{uuid}")).into_response())
        }
        Err(e) => Ok((StatusCode::BAD_REQUEST, e).into_response()),
    }
}
