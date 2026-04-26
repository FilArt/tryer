# Media Bot

Minimal Telegram bot that accepts magnet links or torrent files, sends them to qBittorrent, asks an LLM for a Jellyfin organization plan, and moves video files.

## Configuration

Create `.env`:

```env
TELEGRAM_BOT_TOKEN=...
OPENAI_API_KEY=...
OPENAI_BASE_URL=
QBITTORRENT_HOST=http://localhost:8080
QBITTORRENT_USERNAME=admin
QBITTORRENT_PASSWORD=adminadmin
DOWNLOAD_DIR=/downloads
MOVIES_DIR=/media/movies
SERIES_DIR=/media/series
DATABASE_PATH=media_bot.sqlite3
OPENAI_MODEL=
```

For `llama.cpp`, either leave `OPENAI_MODEL` empty and the app will use the first model from `/v1/models`, or set an alias explicitly:

```sh
llama-server -m /path/to/model.gguf --host 127.0.0.1 --port 8081 --alias local
```

```env
OPENAI_API_KEY=local
OPENAI_BASE_URL=http://127.0.0.1:8081/v1
OPENAI_MODEL=local
```

## Run

```sh
python -m media_bot.main
```

Ask the model from Telegram:

```text
/ask explain this filename
```
