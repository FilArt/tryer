import sqlite3
from datetime import datetime


class Database:
    def __init__(self, path: str):
        self.path = path
        self.init()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self):
        with self.connect() as conn:
            conn.execute(
                """
                create table if not exists torrents (
                    id integer primary key autoincrement,
                    telegram_user_id integer not null,
                    torrent_hash text,
                    name text,
                    status text not null,
                    download_path text,
                    created_at text not null,
                    completed_at text
                )
                """
            )
            conn.execute(
                """
                create table if not exists organize_jobs (
                    id integer primary key autoincrement,
                    torrent_id integer not null,
                    status text not null,
                    plan text,
                    error text,
                    created_at text not null,
                    completed_at text,
                    foreign key(torrent_id) references torrents(id)
                )
                """
            )

    def create_torrent(self, user_id: int, torrent_hash: str | None, name: str) -> int:
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            cur = conn.execute(
                """
                insert into torrents (telegram_user_id, torrent_hash, name, status, created_at)
                values (?, ?, ?, ?, ?)
                """,
                (user_id, torrent_hash, name, "downloading", now),
            )
            return int(cur.lastrowid)

    def update_torrent(self, torrent_id: int, status: str, download_path: str | None = None):
        completed_at = datetime.utcnow().isoformat() if status == "completed" else None
        with self.connect() as conn:
            conn.execute(
                """
                update torrents
                set status = ?, download_path = coalesce(?, download_path), completed_at = coalesce(?, completed_at)
                where id = ?
                """,
                (status, download_path, completed_at, torrent_id),
            )

    def create_job(self, torrent_id: int) -> int:
        now = datetime.utcnow().isoformat()
        with self.connect() as conn:
            cur = conn.execute(
                """
                insert into organize_jobs (torrent_id, status, created_at)
                values (?, ?, ?)
                """,
                (torrent_id, "pending", now),
            )
            return int(cur.lastrowid)

    def update_job(self, job_id: int, status: str, plan: str | None = None, error: str | None = None):
        completed_at = datetime.utcnow().isoformat() if status in {"done", "failed", "needs_confirmation"} else None
        with self.connect() as conn:
            conn.execute(
                """
                update organize_jobs
                set status = ?, plan = coalesce(?, plan), error = coalesce(?, error), completed_at = coalesce(?, completed_at)
                where id = ?
                """,
                (status, plan, error, completed_at, job_id),
            )

    def list_recent(self):
        with self.connect() as conn:
            return conn.execute(
                """
                select id, name, status, download_path, created_at, completed_at
                from torrents
                order by id desc
                limit 20
                """
            ).fetchall()

    def find_torrent_by_name(self, name: str):
        with self.connect() as conn:
            return conn.execute(
                """
                select *
                from torrents
                where name = ?
                order by id desc
                limit 1
                """,
                (name,),
            ).fetchone()

    def has_done_job(self, torrent_id: int) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                """
                select id
                from organize_jobs
                where torrent_id = ? and status in ('done', 'needs_confirmation')
                limit 1
                """,
                (torrent_id,),
            ).fetchone()
            return row is not None
