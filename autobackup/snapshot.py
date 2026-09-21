from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil


class SnapshotManager:

    def __init__(self, project_path: Path):

        self.project_path = project_path.resolve()

        self.backup_root = (
            self.project_path.parent /
            ".autobackup-storage"
        )

        self.backup_root.mkdir(
            parents=True,
            exist_ok=True
        )

    # Public API
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

            self._copy_files(
                files_path,
                manifest
            )

            manifest["status"] = "complete"

            self._write_manifest(
                snapshot_path,
                manifest
            )

            print()
            print("✓ Snapshot complete")
            print(
                f"✓ Files: {len(manifest['files'])}"
            )
            print(
                f"✓ Location: {snapshot_path}"
            )

            return snapshot_path

        except Exception:

            manifest["status"] = "failed"

            self._write_manifest(
                snapshot_path,
                manifest
            )

            raise

    # Copy files
    def _copy_files(
        self,
        destination: Path,
        manifest: dict
    ):

        for source in self.project_path.rglob("*"):

            if not source.is_file():
                continue

            if self._should_ignore(source):
                continue

            relative_path = source.relative_to(
                self.project_path
            )

            target = destination / relative_path

            target.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            shutil.copy2(
                source,
                target
            )

            file_hash = self._calculate_sha256(
                target
            )

            file_size = target.stat().st_size

            manifest["files"].append(
                {
                    "path": relative_path.as_posix(),
                    "size": file_size,
                    "sha256": file_hash
                }
            )

    # Ignore system files/directories
    def _should_ignore(self, path: Path) -> bool:

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

    # SHA-256
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

    # Manifest
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