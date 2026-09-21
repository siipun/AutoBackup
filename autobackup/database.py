from pathlib import Path
import sqlite3
import threading
from datetime import datetime, timezone


class BackupDatabase:

    def __init__(self, database_path: Path):

        self.database_path = Path(
            database_path
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Lock protects database operations
        # when multiple AutoBackup threads
        # access SQLite at the same time.
        self.lock = threading.RLock()

        self.connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False
        )

        self.connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        self.connection.execute(
            "PRAGMA journal_mode = WAL"
        )

        self._create_tables()

    # =========================================================
    # DATABASE SCHEMA
    # =========================================================

    def _create_tables(self):

        with self.lock:

            self.connection.executescript("""

            CREATE TABLE IF NOT EXISTS projects (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                name TEXT NOT NULL,

                path TEXT NOT NULL UNIQUE,

                created_at TEXT NOT NULL,

                last_backup_at TEXT

            );


            CREATE TABLE IF NOT EXISTS snapshots (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                project_id INTEGER NOT NULL,

                snapshot_id TEXT NOT NULL UNIQUE,

                location TEXT NOT NULL,

                created_at TEXT NOT NULL,

                status TEXT NOT NULL,

                file_count INTEGER DEFAULT 0,

                total_size INTEGER DEFAULT 0,

                FOREIGN KEY(project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE

            );


            CREATE TABLE IF NOT EXISTS files (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                snapshot_id INTEGER NOT NULL,

                path TEXT NOT NULL,

                size INTEGER NOT NULL,

                sha256 TEXT NOT NULL,

                FOREIGN KEY(snapshot_id)
                    REFERENCES snapshots(id)
                    ON DELETE CASCADE

            );


            CREATE INDEX IF NOT EXISTS
            idx_snapshots_project

            ON snapshots(project_id);


            CREATE INDEX IF NOT EXISTS
            idx_files_snapshot

            ON files(snapshot_id);

            """)

            self.connection.commit()

    # =========================================================
    # REGISTER PROJECT
    # =========================================================

    def register_project(
        self,
        name: str,
        path: str
    ) -> int:

        with self.lock:

            existing = self.connection.execute(
                """
                SELECT id
                FROM projects
                WHERE path = ?
                """,
                (path,)
            ).fetchone()

            if existing:

                return existing[0]

            created_at = self._now()

            cursor = self.connection.execute(
                """
                INSERT INTO projects (
                    name,
                    path,
                    created_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    path,
                    created_at
                )
            )

            self.connection.commit()

            return cursor.lastrowid

    # =========================================================
    # REGISTER SNAPSHOT
    # =========================================================

    def register_snapshot(
        self,
        project_id: int,
        snapshot_id: str,
        location: str,
        status: str,
        file_count: int,
        total_size: int
    ) -> int:

        with self.lock:

            cursor = self.connection.execute(
                """
                INSERT INTO snapshots (
                    project_id,
                    snapshot_id,
                    location,
                    created_at,
                    status,
                    file_count,
                    total_size
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project_id,
                    snapshot_id,
                    location,
                    self._now(),
                    status,
                    file_count,
                    total_size
                )
            )

            self.connection.execute(
                """
                UPDATE projects

                SET last_backup_at = ?

                WHERE id = ?
                """,
                (
                    self._now(),
                    project_id
                )
            )

            self.connection.commit()

            return cursor.lastrowid

    # =========================================================
    # REGISTER FILE
    # =========================================================

    def register_file(
        self,
        snapshot_database_id: int,
        path: str,
        size: int,
        sha256: str
    ):

        with self.lock:

            self.connection.execute(
                """
                INSERT INTO files (
                    snapshot_id,
                    path,
                    size,
                    sha256
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    snapshot_database_id,
                    path,
                    size,
                    sha256
                )
            )

            self.connection.commit()

    # =========================================================
    # HISTORY
    # =========================================================

    def get_history(
        self,
        project_path: str
    ):

        with self.lock:

            return self.connection.execute(
                """
                SELECT

                    snapshots.snapshot_id,

                    snapshots.created_at,

                    snapshots.status,

                    snapshots.file_count,

                    snapshots.total_size,

                    snapshots.location

                FROM snapshots

                INNER JOIN projects

                    ON snapshots.project_id =
                       projects.id

                WHERE projects.path = ?

                ORDER BY
                    snapshots.created_at DESC

                """,
                (project_path,)
            ).fetchall()

    # =========================================================
    # TIME
    # =========================================================

    @staticmethod
    def _now():

        return datetime.now(
            timezone.utc
        ).isoformat()

    # =========================================================
    # CLOSE
    # =========================================================

    def close(self):

        with self.lock:

            self.connection.close()