use askama::Template;
use crate::auth::User;

#[derive(Template)]
#[template(path = "login.html")]
pub struct LoginTemplate {
    pub user: Option<User>,
    pub error: Option<String>,
}

#[derive(Template)]
#[template(path = "register.html")]
pub struct RegisterTemplate {
    pub user: Option<User>,
    pub error: Option<String>,
}

#[derive(Template)]
#[template(path = "lobby.html")]
pub struct LobbyTemplate {
    pub user: Option<User>,
    pub username: String,
    pub elo: i32,
    pub invite_msg: Option<String>,
    pub received: Vec<InviteView>,
    pub sent: Vec<SentInviteView>,
    pub games: Vec<GameListItem>,
}

#[derive(Clone)]
pub struct InviteView {
    pub id: i64,
    pub from_name: String,
    pub message: String,
    pub sent_on: String,
}

#[derive(Clone)]
pub struct SentInviteView {
    pub id: i64,
    pub to_name: String,
    pub message: String,
    pub status: String,
    pub status_label: String,
    pub sent_on: String,
    pub game_uuid: Option<String>,
}

#[derive(Clone)]
pub struct GameListItem {
    pub uuid: String,
    pub opponent: String,
    pub status: String,
    pub your_turn: bool,
}

#[derive(Clone)]
pub struct ArchiveListItem {
    pub uuid: String,
    pub white_name: String,
    pub black_name: String,
    pub winner_label: String,
    pub played_at: String,
}

#[derive(Clone)]
pub struct LeaderboardRow {
    pub rank: usize,
    pub username: String,
    pub elo: i32,
    pub is_you: bool,
}

#[derive(Template)]
#[template(path = "leaderboard.html")]
pub struct LeaderboardTemplate {
    pub user: Option<User>,
    pub players: Vec<LeaderboardRow>,
}

#[derive(Template)]
#[template(path = "archive.html")]
pub struct ArchiveTemplate {
    pub user: Option<User>,
    pub games: Vec<ArchiveListItem>,
    pub page: i64,
    pub total_pages: i64,
    pub total_count: i64,
    pub has_prev: bool,
    pub has_next: bool,
}

#[derive(Template)]
#[template(path = "replay.html")]
pub struct ReplayTemplate {
    pub user: Option<User>,
    pub white_player: crate::game::ReplayPlayerHeader,
    pub black_player: crate::game::ReplayPlayerHeader,
    pub played_at: String,
    pub show_live_link: bool,
    pub live_uuid: String,
    pub replay_json: String,
    pub initial_step: i32,
}

#[derive(Template)]
#[template(path = "game.html")]
pub struct GameTemplate {
    pub user: Option<User>,
    pub uuid: String,
    pub player_color: String,
    pub status_html: String,
    pub overlay_html: String,
    pub captured_white_html: String,
    pub board_html: String,
    pub captured_black_html: String,
    pub controls_html: String,
}

#[derive(Clone)]
pub struct SquareView {
    pub kind: String,
    pub color: String,
}
