from pathlib import Path

from .database import BackupDatabase
from .restore import RestoreManager


def restore_command(
    snapshot_id: str,
    destination: str
):

    destination_path = Path(
        destination
    ).resolve()

    project_path = Path.cwd().resolve()

    database_path = (
        project_path /
        ".autobackup-storage" /
        "database.db"
    )

    database = BackupDatabase(
        database_path
    )

    try:

        manager = RestoreManager(
            database
        )

        return manager.restore_snapshot(
            snapshot_id,
            destination_path
        )

    finally:

        database.close()
        
        