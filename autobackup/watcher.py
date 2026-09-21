from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class BackupEventHandler(FileSystemEventHandler):

    def on_created(self, event):
        if not event.is_directory:
            print(f"[CREATED] {Path(event.src_path)}")

    def on_modified(self, event):
        if not event.is_directory:
            print(f"[MODIFIED] {Path(event.src_path)}")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"[DELETED] {Path(event.src_path)}")

    def on_moved(self, event):
        if not event.is_directory:
            print(
                f"[MOVED] {Path(event.src_path)} "
                f"→ {Path(event.dest_path)}"
            )


def start_watching(project_path: Path):

    event_handler = BackupEventHandler()

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
    print("Modify a file to test detection.")
    print("Press Ctrl+C to stop.")
    print()

    try:
        while True:
            pass

    except KeyboardInterrupt:
        print("\nStopping AutoBackup...")

        observer.stop()

    observer.join()