use dashmap::DashMap;
use std::sync::Arc;
use tokio::sync::broadcast;

const CAP: usize = 64;

#[derive(Clone, Default)]
pub struct NotifyHub {
    games: Arc<DashMap<String, broadcast::Sender<()>>>,
    lobby: Arc<DashMap<i64, broadcast::Sender<()>>>,
}

impl NotifyHub {
    pub fn notify_game(&self, uuid: &str) {
        let tx = self
            .games
            .entry(uuid.to_string())
            .or_insert_with(|| broadcast::channel(CAP).0);
        let _ = tx.send(());
    }

    pub fn subscribe_game(&self, uuid: &str) -> broadcast::Receiver<()> {
        self.games
            .entry(uuid.to_string())
            .or_insert_with(|| broadcast::channel(CAP).0)
            .subscribe()
    }

    pub fn notify_lobby_user(&self, user_id: i64) {
        if let Some(tx) = self.lobby.get(&user_id) {
            let _ = tx.send(());
        }
    }

    pub fn notify_lobby_users(&self, user_ids: impl IntoIterator<Item = i64>) {
        for id in user_ids {
            self.notify_lobby_user(id);
        }
    }

    pub fn subscribe_lobby(&self, user_id: i64) -> broadcast::Receiver<()> {
        self.lobby
            .entry(user_id)
            .or_insert_with(|| broadcast::channel(CAP).0)
            .subscribe()
    }
}
