"""
CodeTruth Agent V2
Rollback Manager
"""

import os
import shutil
from datetime import datetime


class RollbackManager:

    BACKUP_FOLDER = "backups"

    @classmethod
    def create_backup(cls, file_path: str):

        if not os.path.exists(cls.BACKUP_FOLDER):
            os.makedirs(cls.BACKUP_FOLDER)

        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        file_name = os.path.basename(file_path)

        backup_name = f"{timestamp}_{file_name}"

        backup_path = os.path.join(
            cls.BACKUP_FOLDER,
            backup_name
        )

        shutil.copy2(file_path, backup_path)

        return {
            "success": True,
            "backup_path": backup_path,
            "message": "Backup created successfully."
        }

    @classmethod
    def restore_backup(
        cls,
        backup_path: str,
        original_path: str
    ):

        if not os.path.exists(backup_path):
            raise FileNotFoundError(
                f"Backup not found: {backup_path}"
            )

        shutil.copy2(backup_path, original_path)

        return {
            "success": True,
            "message": "Backup restored successfully."
        }