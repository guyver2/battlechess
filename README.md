# BattleChess (Rust)

Fog-of-war chess with accounts, invites, random matchmaking, and a Datastar-powered web UI.

## Requirements

- Rust 1.85+
- SQLite

## Run

```bash
cd /home/pi/battlechess
cargo run -p btch-server
```

Server listens on **http://0.0.0.0:3100** by default.

Environment variables:

- `PORT` — default `3100`
- `DATABASE_URL` — default `sqlite:./battlechess.db?mode=rwc`

## Development

```bash
cargo test -p btch-core
cargo build -p btch-server
```

## Architecture

- `crates/btch-core` — chess engine with fog visibility, awareness-gated check/en passant, dual-aware checkmate, player-chosen promotion
- `crates/btch-server` — Axum HTTP server, SQLite persistence, session auth, SSR templates, **Datastar SSE** live updates

### Live updates (Datastar SSE)

- **Lobby** — `data-on:load="@get('/lobby/events')"` patches `#invites`, `#games-list`, `#queue-msg` when invites, games, or queue status change
- **Game** — `data-on:load="@get('/games/{uuid}/events')"` patches `#game-status`, `#board`, `#move-area` when the opponent moves or game ends
- **Moves** — forms use `data-on:submit="@post(..., {contentType: 'form'})"` so move fields are sent as form data; SSE patches update the board without a full reload
- **Live game view** — `static/game-sse.js` opens `/games/{uuid}/events` (SSE) and applies board patches; moves submit via fetch and patch the DOM for both players

### ELO ratings

- New accounts start at **1500** ELO
- After each finished game with two human players, ratings update using standard Elo (K=32): win = 1, loss = 0
- The game-over overlay shows your change (e.g. `+16 ELO · rating now 1516`); the lobby shows your current rating
- **Leaderboard** — `/leaderboard` lists players by ELO (top 100)

### Archive and replay

- **Archive** — `/archive` lists all finished games (newest first, 20 per page). Any logged-in user can open a replay.
- **Replay** — `/games/{uuid}/replay` steps through stored positions with First/Prev/Next/Last and arrow keys.
- **Fog modes** — no fog, white POV, black POV, or active player at the current ply (overlay only; all pieces are shown).
- **Access** — players can replay in-progress games; spectators can replay finished games only.
- Entry: archive list, game-over **Watch replay**, or `/games/{uuid}/replay` (starts at move 0; use transport controls or `?step=last` for the final position).

## Repository layout

```
├── crates/btch-core/     # Chess engine
├── crates/btch-server/   # HTTP server + templates
├── migrations/           # SQLite schema
├── static/               # CSS and client scripts
└── legacy/               # Original Python, Vue, and Cocos2d-x code (not used)
```

Older stacks live under **`legacy/`** only; do not run them for the current game.

## Rules (summary)

- Each player sees their pieces and adjacent squares (Moore neighborhood).
- Check restrictions apply only when the player is **aware** of the threat.
- En passant requires visibility of the capturing pawn, target square, and passed pawn.
- Checkmate ends the game when **both** players are aware; king capture always ends the game.
- Pawn promotion: choose queen, rook, bishop, or knight.
