import sys

from .project import (
    get_project_directory,
    get_project_name
)

from .watcher import start_watching
from .database import BackupDatabase
from .commands import restore_command


def main():

    # =========================================================
    # COMMAND MODE
    # =========================================================

    if len(sys.argv) > 1:

        command = sys.argv[1].lower()

        # -----------------------------------------------------
        # RESTORE COMMAND
        # -----------------------------------------------------

        if command == "restore":

            if len(sys.argv) < 4:

                print()
                print("Usage:")
                print(
                    "python -m autobackup.main "
                    "restore <snapshot-id> "
                    "<destination>"
                )

                return

            snapshot_id = sys.argv[2]
            destination = sys.argv[3]

            restore_command(
                snapshot_id,
                destination
            )

            return

    # =========================================================
    # NORMAL WATCH MODE
    # =========================================================

    project_path = (
        get_project_directory()
    )

    project_name = (
        get_project_name(
            project_path
        )
    )

    database_path = (
        project_path /
        ".autobackup-storage" /
        "database.db"
    )

    database = BackupDatabase(
        database_path
    )

    project_id = (
        database.register_project(
            project_name,
            str(project_path)
        )
    )

    print()
    print("===================================")
    print("          AUTOBACKUP V1.4")
    print("===================================")
    print()
    print(
        f"Project: {project_name}"
    )
    print(
        f"Location: {project_path}"
    )
    print(
        f"Project ID: {project_id}"
    )
    print()
    print("Database: READY")
    print()

    try:

        start_watching(
            project_path,
            database,
            project_id
        )

    finally:

        database.close()


if __name__ == "__main__":
    main()
    
    