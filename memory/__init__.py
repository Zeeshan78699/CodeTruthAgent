"""
Memory Layer
"""
import os

def __init__(self, memory_file="memory_v2.json"):

    self.memory_file = memory_file

    self.backup_directory = "backups"

    self.archive_directory = (
        "backups/memory_archives"
    )

    # ===================================================
    # MEMORY LIMIT CONFIGURATION
    # ===================================================

    self.max_approved_decisions = 100

    self.max_recovery_events = 50

    self.max_cleanup_events = 50

    self.max_archive_cleanup_events = 50

    # ===================================================
    # ARCHIVE RETENTION CONFIGURATION
    # ===================================================

    self.max_archive_files = 25

    # ===================================================
    # ENSURE DIRECTORIES EXIST
    # ===================================================

    os.makedirs(
        self.backup_directory,
        exist_ok=True
    )

    os.makedirs(
        self.archive_directory,
        exist_ok=True
    )

    # ===================================================
    # INITIALIZE MEMORY
    # ===================================================

    if not os.path.exists(
        self.memory_file
    ):

        self._initialize_memory()