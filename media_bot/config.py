from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Config:
    telegram_token: str
    qbittorrent_host: str
    qbittorrent_username: str
    qbittorrent_password: str
    download_dir: str
    movies_dir: str
    series_dir: str
    database_path: str
    openai_model: str


def load_config() -> Config:
    return Config(
        telegram_token=os.environ["TELEGRAM_BOT_TOKEN"],
        qbittorrent_host=os.environ.get("QBITTORRENT_HOST", "http://localhost:8080"),
        qbittorrent_username=os.environ.get("QBITTORRENT_USERNAME", "admin"),
        qbittorrent_password=os.environ.get("QBITTORRENT_PASSWORD", "adminadmin"),
        download_dir=os.environ.get("DOWNLOAD_DIR", "/downloads"),
        movies_dir=os.environ.get("MOVIES_DIR", "/media/movies"),
        series_dir=os.environ.get("SERIES_DIR", "/media/series"),
        database_path=os.environ.get("DATABASE_PATH", "media_bot.sqlite3"),
        openai_model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
    )
