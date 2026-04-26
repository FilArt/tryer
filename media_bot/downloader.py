from pathlib import Path
import qbittorrentapi


class Downloader:
    def __init__(self, host: str, username: str, password: str, download_dir: str):
        self.download_dir = download_dir
        self.client = qbittorrentapi.Client(host=host, username=username, password=password)
        self.client.auth_log_in()

    def add_magnet(self, magnet: str):
        self.client.torrents_add(urls=magnet, save_path=self.download_dir)

    def add_torrent_file(self, path: str):
        with open(path, "rb") as torrent:
            self.client.torrents_add(torrent_files=torrent, save_path=self.download_dir)

    def torrents(self):
        return list(self.client.torrents_info())

    def find_by_name(self, name: str):
        for torrent in self.torrents():
            if torrent.name == name or torrent.hash == name:
                return torrent
        return None

    def completed(self):
        return [torrent for torrent in self.torrents() if float(torrent.progress) >= 1.0]

    def content_path(self, torrent) -> str:
        root = Path(str(torrent.save_path))
        candidate = root / str(torrent.name)
        return str(candidate if candidate.exists() else root)
