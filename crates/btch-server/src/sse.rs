use crate::auth::User;
use crate::fragments::{self, build_game_view, game_version};
use crate::game::get_game_by_uuid;
use crate::notify::NotifyHub;
use crate::{fetch_invites, fetch_sent_invites, list_user_games, AppState};
use async_stream::stream;
use axum::{
    extract::State,
    http::HeaderMap,
    response::{
        sse::{Event, KeepAlive, Sse},
        IntoResponse, Redirect, Response,
    },
};
use core::convert::Infallible;
use datastar::prelude::{ElementPatchMode, PatchElements};
use sqlx::SqlitePool;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::broadcast;
use tower_sessions::Session;

pub fn is_datastar(headers: &HeaderMap) -> bool {
    headers
        .get("datastar-request")
        .is_some()
}

pub fn patch(selector: &str, html: String) -> Event {
    PatchElements::new(html)
        .selector(selector)
        .mode(ElementPatchMode::Outer)
        .write_as_axum_sse_event()
}

pub fn patch_inner(selector: &str, html: String) -> Event {
    PatchElements::new(html)
        .selector(selector)
        .mode(ElementPatchMode::Inner)
        .write_as_axum_sse_event()
}

pub fn game_patches(view: &fragments::GameViewState) -> Vec<Event> {
    vec![
        patch_inner("#game-status", view.status_html.clone()),
        patch_inner("#game-modal", view.overlay_html.clone()),
        patch_inner("#captured-white", view.captured_white_html.clone()),
        patch_inner("#board", view.board_html.clone()),
        patch_inner("#captured-black", view.captured_black_html.clone()),
        patch_inner("#move-area", view.controls_html.clone()),
    ]
}

pub fn sse_from_events(events: Vec<Event>) -> Sse<impl futures_util::Stream<Item = Result<Event, Infallible>>> {
    Sse::new(futures_util::stream::iter(events.into_iter().map(Ok)))
        .keep_alive(KeepAlive::default())
}

pub async fn game_events(
    State(st): State<Arc<AppState>>,
    session: Session,
    axum::extract::Path(uuid): axum::extract::Path<String>,
) -> Result<Sse<impl futures_util::Stream<Item = Result<Event, Infallible>>>, Redirect> {
    let user = crate::current_user(&st.pool, &session)
        .await
        .ok_or(Redirect::to("/login"))?;

    let game = get_game_by_uuid(&st.pool, &uuid)
        .await
        .ok()
        .flatten()
        .ok_or(Redirect::to("/lobby"))?;

    let pool = st.pool.clone();
    let hub = st.notify.clone();
    let game_id = game.id;
    let uuid_clone = uuid.clone();
    let mut rx = hub.subscribe_game(&uuid);

    let stream = stream! {
        let mut last = None::<(i32, String, String)>;
        loop {
            let Ok(Some(game)) = get_game_by_uuid(&pool, &uuid_clone).await else {
                break;
            };
            let Ok(version) = game_version(&pool, game_id).await else {
                tokio::select! {
                    r = rx.recv() => {
                        if matches!(r, Err(broadcast::error::RecvError::Closed)) {
                            break;
                        }
                    }
                    _ = tokio::time::sleep(Duration::from_millis(800)) => {}
                }
                continue;
            };
            if last.as_ref() != Some(&version) {
                last = Some(version.clone());
                if let Ok(view) = build_game_view(&pool, &game, &user, false, "").await {
                    for ev in game_patches(&view) {
                        yield Ok(ev);
                    }
                }
            }
            tokio::select! {
                r = rx.recv() => {
                    if matches!(r, Err(broadcast::error::RecvError::Closed)) {
                        break;
                    }
                }
                _ = tokio::time::sleep(Duration::from_millis(800)) => {}
            }
        }
    };

    Ok(Sse::new(stream).keep_alive(KeepAlive::default()))
}

pub async fn lobby_events(
    State(st): State<Arc<AppState>>,
    session: Session,
) -> Result<Sse<impl futures_util::Stream<Item = Result<Event, Infallible>>>, Redirect> {
    let user = crate::current_user(&st.pool, &session)
        .await
        .ok_or(Redirect::to("/login"))?;

    let pool = st.pool.clone();
    let hub = st.notify.clone();
    let user_id = user.id;
    let mut rx = hub.subscribe_lobby(user_id);

    let stream = stream! {
        let mut last_key = String::new();
        loop {
            let _ = tokio::select! {
                r = rx.recv() => r,
                _ = tokio::time::sleep(Duration::from_millis(2000)) => Ok(()),
            };
            let received = fetch_invites(&pool, user_id).await;
            let sent = fetch_sent_invites(&pool, user_id).await;
            let games = list_user_games(&pool, user_id).await;
            let sent_key: String = sent
                .iter()
                .map(|i| {
                    format!(
                        "{}:{}:{}",
                        i.id,
                        i.status,
                        i.game_uuid.as_deref().unwrap_or("")
                    )
                })
                .collect::<Vec<_>>()
                .join(",");
            let key = format!("{}|{}|{}", received.len(), sent_key, games.len());
            if key == last_key {
                continue;
            }
            last_key = key;

            yield Ok(patch_inner("#invites", fragments::invites_html(&received)));
            yield Ok(patch_inner("#sent-invites", fragments::sent_invites_html(&sent)));
            yield Ok(patch_inner("#games-list", fragments::games_list_html(&games)));
        }
    };

    Ok(Sse::new(stream).keep_alive(KeepAlive::default()))
}

pub async fn respond_game_view(
    pool: &SqlitePool,
    hub: &NotifyHub,
    uuid: &str,
    user: &User,
    needs_promotion: bool,
    pending_move: &str,
    headers: &HeaderMap,
) -> Result<Response, String> {
    let game = get_game_by_uuid(pool, uuid)
        .await
        .map_err(|e| e.to_string())?
        .ok_or("Game not found")?;
    let view = build_game_view(pool, &game, user, needs_promotion, pending_move).await?;
    hub.notify_game(uuid);

    if is_datastar(headers) {
        Ok(sse_from_events(game_patches(&view)).into_response())
    } else {
        Err("use datastar".into())
    }
}
