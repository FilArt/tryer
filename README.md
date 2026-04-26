# Media Bot

Minimal Telegram bot that accepts magnet links or torrent files, sends them to qBittorrent, asks an LLM for a Jellyfin organization plan, and moves video files.

## Environment

```sh
export TELEGRAM_BOT_TOKEN="..."
export OPENAI_API_KEY="..."
export QBITTORRENT_HOST="http://localhost:8080"
export QBITTORRENT_USERNAME="admin"
export QBITTORRENT_PASSWORD="adminadmin"
export DOWNLOAD_DIR="/downloads"
export MOVIES_DIR="/media/movies"
export SERIES_DIR="/media/series"
export DATABASE_PATH="media_bot.sqlite3"
export OPENAI_MODEL="gpt-4.1-mini"
```

## Run

```sh
python -m media_bot.main
```
