from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    telegram_token: str
    openai_api_key: str
    openai_base_url: str | None
    qbittorrent_host: str
    qbittorrent_username: str
    qbittorrent_password: str
    download_dir: str
    movies_dir: str
    series_dir: str
    database_path: str
    openai_model: str


def load_config() -> Config:
    load_dotenv()
    return Config(
        telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
        openai_api_key=os.environ.get("OPENAI_API_KEY", "local"),
        openai_base_url=os.environ.get("OPENAI_BASE_URL"),
        qbittorrent_host=os.environ.get("QBITTORRENT_HOST", "http://localhost:8080"),
        qbittorrent_username=os.environ.get("QBITTORRENT_USERNAME", "admin"),
        qbittorrent_password=os.environ.get("QBITTORRENT_PASSWORD", "adminadmin"),
        download_dir=os.environ.get("DOWNLOAD_DIR", "/downloads"),
        movies_dir=os.environ.get("MOVIES_DIR", "/media/movies"),
        series_dir=os.environ.get("SERIES_DIR", "/media/series"),
        database_path=os.environ.get("DATABASE_PATH", "media_bot.sqlite3"),
        openai_model=os.environ.get("OPENAI_MODEL", ""),
    )
