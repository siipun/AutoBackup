from pathlib import Path
import threading

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .snapshot import SnapshotManager


class BackupEventHandler(FileSystemEventHandler):

    def __init__(self, snapshot_manager):
        super().__init__()

        self.snapshot_manager = snapshot_manager

        # Prevent several filesystem events from
        # creating snapshots simultaneously.
        self.lock = threading.Lock()

        self.timer = None

    def schedule_snapshot(self):

        if self.timer:
            self.timer.cancel()

        # Wait briefly because one save operation
        # can generate multiple filesystem events.
        self.timer = threading.Timer(
            2.0,
            self.create_snapshot
        )

        self.timer.start()

    def create_snapshot(self):

        with self.lock:

            try:
                self.snapshot_manager.create_snapshot()

            except Exception as error:

                print()
                print("✗ Backup failed")
                print(f"Error: {error}")

    def on_created(self, event):

        if not event.is_directory:

            print(f"[CREATED] {Path(event.src_path)}")

            self.schedule_snapshot()

    def on_modified(self, event):

        if not event.is_directory:

            print(f"[MODIFIED] {Path(event.src_path)}")

            self.schedule_snapshot()

    def on_deleted(self, event):

        if not event.is_directory:

            print(f"[DELETED] {Path(event.src_path)}")

            self.schedule_snapshot()

    def on_moved(self, event):

        if not event.is_directory:

            print(
                f"[MOVED] {Path(event.src_path)} "
                f"→ {Path(event.dest_path)}"
            )

            self.schedule_snapshot()


def start_watching(project_path: Path):

    snapshot_manager = SnapshotManager(
        project_path
    )

    event_handler = BackupEventHandler(
        snapshot_manager
    )

    observer = Observer()

    observer.schedule(
        event_handler,
        str(project_path),
        recursive=True
    )

    observer.start()

    print()
    print("===================================")
    print("         AUTOBACKUP WATCHER")
    print("===================================")
    print(f"Watching: {project_path}")
    print("Status: ACTIVE")
    print()
    print("Modify a file to trigger a backup.")
    print("Press Ctrl+C to stop.")
    print()

    try:

        # Don't burn CPU with while True/pass.
        observer.join()

    except KeyboardInterrupt:

        print()
        print("Stopping AutoBackup...")

        observer.stop()

        observer.join()