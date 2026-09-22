from pathlib import Path
import shutil

from .integrity import IntegrityChecker


class RestoreManager:

    def __init__(self, database):

        self.database = database
        self.integrity_checker = IntegrityChecker()

    # =========================================================
    # RESTORE SNAPSHOT
    # =========================================================

    def restore_snapshot(
        self,
        snapshot_id: str,
        destination: Path
    ) -> bool:

        snapshot = self._find_snapshot(
            snapshot_id
        )

        if snapshot is None:

            print()
            print("✗ Snapshot not found")
            print(
                f"Snapshot ID: {snapshot_id}"
            )

            return False

        snapshot_location = Path(
            snapshot["location"]
        )

        print()
        print("===================================")
        print("          RESTORE SNAPSHOT")
        print("===================================")
        print(
            f"Snapshot: {snapshot_id}"
        )
        print(
            f"Source:   {snapshot_location}"
        )
        print(
            f"Target:   {destination}"
        )

        # -----------------------------------------------------
        # Check snapshot exists
        # -----------------------------------------------------

        if not snapshot_location.exists():

            print()
            print(
                "✗ Snapshot location does not exist"
            )

            return False

        # -----------------------------------------------------
        # Verify snapshot before restoring
        # -----------------------------------------------------

        print()
        print(
            "Verifying snapshot before restore..."
        )

        valid = (
            self.integrity_checker
            .verify_snapshot(
                snapshot_location
            )
        )

        if not valid:

            print()
            print(
                "✗ Restore cancelled."
            )

            print(
                "The snapshot failed integrity "
                "verification."
            )

            return False

        # -----------------------------------------------------
        # Prevent accidental overwrite
        # -----------------------------------------------------

        if destination.exists():

            print()
            print(
                "⚠ Destination already exists:"
            )

            print(destination)

            print()

            print(
                "Restore cancelled to prevent "
                "overwriting existing files."
            )

            return False

        # -----------------------------------------------------
        # Create destination
        # -----------------------------------------------------

        destination.mkdir(
            parents=True,
            exist_ok=True
        )

        source_files = (
            snapshot_location /
            "files"
        )

        # -----------------------------------------------------
        # Restore files
        # -----------------------------------------------------

        restored_count = 0

        for source in source_files.rglob("*"):

            if not source.is_file():
                continue

            relative_path = (
                source.relative_to(
                    source_files
                )
            )

            target = (
                destination /
                relative_path
            )

            target.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            shutil.copy2(
                source,
                target
            )

            restored_count += 1

        # -----------------------------------------------------
        # Restore complete
        # -----------------------------------------------------

        print()
        print("===================================")
        print("        RESTORE COMPLETE")
        print("===================================")

        print(
            f"✓ Files restored: {restored_count}"
        )

        print(
            f"✓ Destination: {destination}"
        )

        return True

    # =========================================================
    # FIND SNAPSHOT
    # =========================================================

    def _find_snapshot(
        self,
        snapshot_id: str
    ):

        return self.database.get_snapshot(
            snapshot_id
        )