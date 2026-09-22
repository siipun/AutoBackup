from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil


class SnapshotManager:

    def __init__(
        self,
        project_path: Path,
        database,
        project_id: int
    ):

        self.project_path = Path(
            project_path
        ).resolve()

        self.database = database
        self.project_id = project_id

        self.backup_root = (
            self.project_path /
            ".autobackup-storage"
        )

        self.backup_root.mkdir(
            parents=True,
            exist_ok=True
        )

    # =========================================================
    # CREATE SNAPSHOT
    # =========================================================

    def create_snapshot(self) -> Path:

        snapshot_id = datetime.now().strftime(
            "%Y%m%d-%H%M%S-%f"
        )

        snapshot_path = (
            self.backup_root /
            self.project_path.name /
            snapshot_id
        )

        files_path = snapshot_path / "files"

        files_path.mkdir(
            parents=True,
            exist_ok=True
        )

        print()
        print("===================================")
        print("       CREATING SNAPSHOT")
        print("===================================")
        print(f"Snapshot ID: {snapshot_id}")

        manifest = {
            "snapshot_id": snapshot_id,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "project": self.project_path.name,
            "source": str(self.project_path),
            "status": "creating",
            "files": []
        }

        try:

            # -------------------------------------------------
            # Copy project files
            # -------------------------------------------------

            self._copy_files(
                files_path,
                manifest
            )

            # -------------------------------------------------
            # Mark snapshot complete
            # -------------------------------------------------

            manifest["status"] = "complete"

            # -------------------------------------------------
            # Calculate total size
            # -------------------------------------------------

            total_size = sum(
                file_entry["size"]
                for file_entry in manifest["files"]
            )

            # -------------------------------------------------
            # Register snapshot in SQLite
            # -------------------------------------------------

            database_snapshot_id = (
                self.database.register_snapshot(
                    project_id=self.project_id,
                    snapshot_id=snapshot_id,
                    location=str(snapshot_path),
                    status="complete",
                    file_count=len(
                        manifest["files"]
                    ),
                    total_size=total_size
                )
            )

            # -------------------------------------------------
            # Register individual files
            # -------------------------------------------------

            for file_entry in manifest["files"]:

                self.database.register_file(
                    snapshot_database_id=(
                        database_snapshot_id
                    ),
                    path=file_entry["path"],
                    size=file_entry["size"],
                    sha256=file_entry["sha256"]
                )

            # -------------------------------------------------
            # Save manifest
            # -------------------------------------------------

            self._write_manifest(
                snapshot_path,
                manifest
            )

            # -------------------------------------------------
            # Success message
            # -------------------------------------------------

            print()
            print("✓ Snapshot complete")
            print(
                f"✓ Files: {len(manifest['files'])}"
            )
            print(
                f"✓ Size: {total_size} bytes"
            )
            print(
                f"✓ Location: {snapshot_path}"
            )

            return snapshot_path

        except Exception as error:

            # -------------------------------------------------
            # Mark snapshot as failed
            # -------------------------------------------------

            manifest["status"] = "failed"

            self._write_manifest(
                snapshot_path,
                manifest
            )

            print()
            print("✗ Snapshot failed")
            print(f"Error: {error}")

            raise

    # =========================================================
    # COPY FILES
    # =========================================================

    def _copy_files(
        self,
        destination: Path,
        manifest: dict
    ):

        for source in self.project_path.rglob("*"):

            # Ignore directories
            if not source.is_file():
                continue

            # Ignore system/backup files
            if self._should_ignore(source):
                continue

            # Get path relative to project
            relative_path = source.relative_to(
                self.project_path
            )

            target = (
                destination /
                relative_path
            )

            # Make destination directory
            target.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # Copy file
            shutil.copy2(
                source,
                target
            )

            # Calculate SHA-256
            file_hash = self._calculate_sha256(
                target
            )

            # Get file size
            file_size = target.stat().st_size

            # Add information to manifest
            manifest["files"].append(
                {
                    "path": relative_path.as_posix(),
                    "size": file_size,
                    "sha256": file_hash
                }
            )

    # =========================================================
    # IGNORE FILES / DIRECTORIES
    # =========================================================

    def _should_ignore(
        self,
        path: Path
    ) -> bool:

        ignored_directories = {
            ".autobackup-storage",
            ".git",
            "__pycache__",
            ".venv",
            "venv"
        }

        return any(
            directory in path.parts
            for directory in ignored_directories
        )

    # =========================================================
    # SHA-256
    # =========================================================

    def _calculate_sha256(
        self,
        file_path: Path
    ) -> str:

        sha256 = hashlib.sha256()

        with file_path.open(
            "rb"
        ) as file:

            while True:

                chunk = file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()

    # =========================================================
    # WRITE MANIFEST
    # =========================================================

    def _write_manifest(
        self,
        snapshot_path: Path,
        manifest: dict
    ):

        manifest_path = (
            snapshot_path /
            "manifest.json"
        )

        with manifest_path.open(
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                manifest,
                file,
                indent=4
            )