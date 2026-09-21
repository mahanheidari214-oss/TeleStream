# Tasks: TeleStream Instant (Kavimo Edition)

- [/] Phase 1: Project Scaffolding & Configuration Engine
  - [x] Create directory structure `d:\mahan\antigravity\TeleStream`
  - [ ] Write `requirements.txt`
  - [ ] Write `Procfile`, `railway.json`, `nixpacks.toml`
  - [ ] Write `config.py` (Railway env vars + local config.json fallback)
  - [ ] Write `crypto_patch.py` & `net_patch.py`
  - [ ] Write `network_utils.py`

- [ ] Phase 2: Core Data & Streaming Engine
  - [ ] Write `database.py` (async SQLite media mapping)
  - [ ] Write `streamer.py` (zero-disk chunked MTProto streamer with HTTP 206 support & auto-recovery)

- [ ] Phase 3: Kavimo / Biomaz HTML5 Player UI
  - [ ] Design and implement `templates/player.html`
    - [ ] Floating acrylic glass control dock
    - [ ] Biomaz speed selector (`0.5x`, `0.75x`, `1x`, `1.25x`, `1.5x`, `1.75x`, `2x`, `2.5x`)
    - [ ] ±10s circular jump buttons
    - [ ] Mobile double-tap gestures (left/right ripple)
    - [ ] Center play/pause beacon animation
    - [ ] Vazirmatn Persian typography & time format
    - [ ] Mobile responsive layout & full-screen / PiP controls

- [ ] Phase 4: Server Routes & Telegram Bot Controller
  - [ ] Write `server.py` (`/`, `/play/{link_id}`, `/stream/{link_id}/{filename}`, `/dl/{link_id}/{filename}`)
  - [ ] Write `bot.py` (Hydrogram client, media detection, Markdown cards, inline keyboard for Kavimo/VLC/ADM)

- [ ] Phase 5: Verification & Packaging
  - [ ] Write unit test suite `tests/test_server.py`
  - [ ] Run test suite with Python 3.12 venv
  - [ ] Provide `setup.bat` and `start.bat` for local Windows testing
  - [ ] Provide Railway deployment guide `RAILWAY_DEPLOY.md`
