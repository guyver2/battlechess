# Legacy BattleChess

Original implementations and assets, kept for reference. The active game is the Rust workspace at the repository root (`crates/btch-core`, `crates/btch-server`).

| Path | Description |
|------|-------------|
| `app/` | Cocos2d-x mobile client |
| `client/` | Vue.js web client |
| `server/` | Python FastAPI server and tests |
| `core/` | Python board logic |
| `ia/` | AI experiments |
| `data/` | Original sprites, sounds, SQLite sample DB |
| `battleChess.py`, `server.py`, `communication.py` | Standalone Python scripts |
| `.github/`, `.travis.yml` | Historical CI for the Python stack |

Do not run these for production; use `cargo run -p btch-server` from the repo root instead.
