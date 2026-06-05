"""
CodeTruth Agent V2
Archive Retention Tests
"""

import os
import time

from memory.memory_store_v2 import MemoryStoreV2


TEST_MEMORY_FILE = "test_archive_memory.json"


def cleanup_test_environment():

    if os.path.exists(TEST_MEMORY_FILE):
        os.remove(TEST_MEMORY_FILE)


def test_archive_retention_limit():

    cleanup_test_environment()

    memory_store = MemoryStoreV2(
        memory_file=TEST_MEMORY_FILE
    )

    # ===================================================
    # CREATE MANY ARCHIVES
    # ===================================================

    for index in range(35):

        archive_path = os.path.join(
            memory_store.archive_directory,
            (
                f"memory_archive_test_"
                f"{index}.json"
            )
        )

        with open(archive_path, "w") as file:
            file.write("test")

        # Ensure unique timestamps
        time.sleep(0.01)

    data = memory_store.get_memory()

    memory_store._prune_old_archives(data)

    archive_files = []

    for file_name in os.listdir(
        memory_store.archive_directory
    ):

        if (
            file_name.startswith(
                "memory_archive_"
            )
            and
            file_name.endswith(".json")
        ):

            archive_files.append(file_name)

    # ===================================================
    # VERIFY RETENTION LIMIT
    # ===================================================

    assert (
        len(archive_files)
        <= memory_store.max_archive_files
    )

    cleanup_test_environment()


def test_archive_cleanup_event_logging():

    cleanup_test_environment()

    memory_store = MemoryStoreV2(
        memory_file=TEST_MEMORY_FILE
    )

    for index in range(30):

        archive_path = os.path.join(
            memory_store.archive_directory,
            (
                f"memory_archive_cleanup_"
                f"{index}.json"
            )
        )

        with open(archive_path, "w") as file:
            file.write("cleanup")

        time.sleep(0.01)

    data = memory_store.get_memory()

    memory_store._prune_old_archives(data)

    assert (
        len(data["archive_cleanup_events"])
        >= 1
    )

    cleanup_test_environment()