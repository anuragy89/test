# 🐱 NekoMusic — Telegram Voice Chat Music Bot v2.0

> Fast, scalable, production-ready music bot built with **Pyrogram**, **PyTgCalls 4.0**, **music.xbitcode.com API**, and **MongoDB**. Runs smoothly in 10,000+ groups.

---

## ✨ Features

| | Feature |
|---|---|
| 🎵 | `/play` — stream audio in voice chat (search or YouTube URL) |
| 🎬 | `/vplay` — stream video in voice chat |
| ⚡ | `/playforce` — skip queue and play immediately |
| ⏸ | `/pause` `/resume` `/skip` `/end` — full playback control |
| 📋 | `/queue` — view queue (up to 20 songs per group) |
| 🏓 | `/ping` — live latency check |
| 🔀 | Shuffle / 🔁 Loop — inline button controls |
| 🖼 | Auto-generated **Blue Horizon style** thumbnail with album art, neon waveform, dominant-colour neon accents, progress bar |
| 🌐 | 5 languages: English, Hindi, Spanish, Arabic, Russian |
| 📊 | `/stats` `/broadcast` `/restart` — owner commands |
| 💾 | MongoDB — all users & groups stored for broadcast |
| 🎨 | Colored inline buttons (Bot API 9.4 `style` field) |
| ✨ | Premium animated emoji via `<tg-emoji>` tags |
| 📋 | Colorised console + rotating log file + optional Telegram log group |

---

## 🚀 Deploy on Heroku (Standard-2X)

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/YourUsername/NekoMusic)

> `app.json` pre-fills all 50+ config vars with descriptions. Just fill in required fields.

---

## 🛠 Local Setup

```bash
# 1. Clone
git clone https://github.com/YourUsername/NekoMusic
cd NekoMusic

# 2. Install dependencies  (Python 3.11+ required)
pip install -r requirements.txt

# 3. Install FFmpeg
sudo apt install ffmpeg          # Ubuntu/Debian
brew install ffmpeg              # macOS

# 4. Generate assistant string session
python generate_session.py

# 5. Configure
cp .env.example .env
# Edit .env with your values

# 6. Run
python __main__.py
```

---

## ⚙️ Key Environment Variables

| Variable | Required | Description |
|---|---|---|
| `API_ID` | ✅ | [my.telegram.org](https://my.telegram.org) |
| `API_HASH` | ✅ | [my.telegram.org](https://my.telegram.org) |
| `BOT_TOKEN` | ✅ | [@BotFather](https://t.me/BotFather) |
| `STRING_SESSION` | ✅ | Run `generate_session.py` |
| `MONGO_URI` | ✅ | [MongoDB Atlas](https://cloud.mongodb.com) |
| `OWNER_ID` | ✅ | Your Telegram user ID |
| `BOT_USERNAME` | ✅ | Bot username without `@` |
| `MUSIC_API_BASE` | — | `https://music.xbitcode.com` |
| `YT_API_KEY` | — | YouTube Data API v3 key (improves search) |
| `YT_PROXY_URL` | — | Proxy for music API requests |
| `HEROKU_APP_NAME` | — | Enables `/restart` command |
| `HEROKU_API_KEY` | — | Enables `/restart` command |
| `LOG_GROUP_ID` | — | Telegram group for error logs |
| `EMOJI_*_ID` | — | 44 premium emoji document IDs |

---

## 📝 Commands

### 🎵 Music (groups only)
```
/play [name or URL]       Stream audio in voice chat
/vplay [name or URL]      Stream video in voice chat
/playforce [name or URL]  Force play (front of queue)
/pause                    Pause playback
/resume                   Resume playback
/skip                     Skip to next track
/end                      Stop & clear queue
/queue                    View current queue
```

### 🌐 General
```
/start     Welcome message + buttons
/help      Full command list
/ping      Bot latency
/lang      Change language (en/hi/es/ar/ru)
```

### 👑 Owner Only
```
/stats                    Users, groups, songs played, RAM, CPU, uptime
/broadcast -user <text>   Send to all users
/broadcast -group <text>  Send to all groups
/broadcast <text>         Send to everyone (or reply to a message)
/restart                  Restart via Heroku API
/ban <user_id>            Ban a user
/unban <user_id>          Unban a user
```

---

## 🖼 Thumbnail Design

Matches the **Blue Horizon** card style:
- Dark split-panel (art left | info right)
- Blurred song cover as background
- Neon colours extracted from album art (cyan/teal/purple)
- "NOW PLAYING" pill badge
- Animated-style waveform bars
- Progress bar with glow dot
- NekoMusic 🐱 watermark

Drop `NotoSans-Bold.ttf` + `NotoSans-Regular.ttf` into `assets/fonts/` for crisp text.
Free download: [Google Fonts — Noto Sans](https://fonts.google.com/noto/specimen/Noto+Sans)

---

## 💎 Premium Emoji Setup

1. Find an animated emoji sticker pack in Telegram
2. Forward the animated emoji to a userbot and read `media.document.id`
3. Paste the ID into the matching `EMOJI_*_ID` env var
4. The bot owner needs **Telegram Premium** for them to render animated

All 44 emoji slots are defined in `config.py` with `E.NAME` + `E.NAME_ID`.
Use `pe(E.CROWN, E.CROWN_ID)` anywhere to get a premium tag or plain fallback.

---

## 📁 Project Structure

```
NekoMusic/
├── __main__.py                  Entry point
├── config.py                    All config + 44 emoji ID slots
├── logger.py                    Logger system
├── requirements.txt
├── Procfile                     Heroku: worker standard-2x
├── app.json                     Heroku one-click deploy
├── runtime.txt                  Python 3.11.8
├── generate_session.py          Assistant session helper
├── .env.example
├── assets/
│   ├── banner.jpg               Start message banner (add your own 1280x640)
│   └── fonts/                   NotoSans-Bold.ttf + NotoSans-Regular.ttf
└── NekoMusic/
    ├── client.py                Bot + Assistant + PyTgCalls
    ├── database/db.py           Async MongoDB (Motor)
    ├── locales/                 en, hi, es, ar, ru
    ├── utils/
    │   ├── musicapi.py          music.xbitcode.com API wrapper
    │   ├── queue.py             Per-chat queue manager
    │   ├── keyboards.py         Colored inline keyboards
    │   └── thumb.py             Blue Horizon thumbnail generator
    └── plugins/
        ├── user/
        │   ├── music.py         ALL music commands + callbacks (one file)
        │   └── start.py         /start /help /lang
        └── owner/
            └── admin.py         /stats /broadcast /restart /ban
```

---

<p align="center">Made with ❤️ and 🐱</p>
