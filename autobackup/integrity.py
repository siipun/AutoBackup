from pathlib import Path
import hashlib
import json

class IntegrityChecker:

    def verify_snapshot(
        self,
        snapshot_path: Path
    ) -> bool:

        manifest_path = (
            snapshot_path /
            "manifest.json"
        )

        if not manifest_path.exists():

            print(
                "✗ Manifest missing"
            )

            return False

        with manifest_path.open(
            "r",
            encoding="utf-8"
        ) as file:

            manifest = json.load(file)

        if manifest.get("status") != "complete":

            print(
                "✗ Snapshot is not marked complete"
            )

            return False

        print()
        print("Verifying snapshot...")

        for entry in manifest["files"]:

            relative_path = Path(
                entry["path"]
            )

            file_path = (
                snapshot_path /
                "files" /
                relative_path
            )

            if not file_path.exists():

                print(
                    f"✗ Missing: {relative_path}"
                )

                return False

            actual_hash = (
                self._sha256(file_path)
            )

            expected_hash = entry[
                "sha256"
            ]

            if actual_hash != expected_hash:

                print(
                    f"✗ Corrupted: "
                    f"{relative_path}"
                )

                return False

        print(
            "✓ Snapshot integrity verified"
        )

        return True

    def _sha256(
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