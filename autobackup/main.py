from .project import (
    get_project_directory,
    get_project_name
)

from .watcher import start_watching
from .database import BackupDatabase


def main():

    project_path = get_project_directory()

    project_name = get_project_name(
        project_path
    )

    database_path = (
        project_path.parent /
        ".autobackup-storage" /
        "database.db"
    )

    database = BackupDatabase(
        database_path
    )

    project_id = database.register_project(
        project_name,
        str(project_path)
    )

    print()
    print("===================================")
    print("          AUTOBACKUP V1.3")
    print("===================================")
    print()
    print(f"Project: {project_name}")
    print(f"Location: {project_path}")
    print(f"Project ID: {project_id}")
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