"""
CodeTruth Agent V2
Formal Rollback Tests
"""

import os
import sys

# ===================================================
# PROJECT ROOT SETUP
# ===================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

# ===================================================
# IMPORTS
# ===================================================

from validation.rollback_manager import RollbackManager

# ===================================================
# TEST CONFIGURATION
# ===================================================

TEST_FILE = "sample_test_file.txt"

# ===================================================
# BACKUP CREATION TEST
# ===================================================

def test_backup_creation():

    result = RollbackManager.create_backup(
        TEST_FILE
    )

    assert result["success"] is True

    assert os.path.exists(
        result["backup_path"]
    )

# ===================================================
# ROLLBACK RESTORE TEST
# ===================================================

def test_backup_restore():

    # CREATE BACKUP
    backup_result = RollbackManager.create_backup(
        TEST_FILE
    )

    backup_path = backup_result["backup_path"]

    # MODIFY FILE
    with open(TEST_FILE, "w") as file:
        file.write("Unsafe Modified Content")

    # RESTORE BACKUP
    restore_result = RollbackManager.restore_backup(
        backup_path,
        TEST_FILE
    )

    assert restore_result["success"] is True

    # VERIFY CONTENT
    with open(TEST_FILE, "r") as file:
        content = file.read()

    assert content == "Original Safe Content"

# ===================================================
# MISSING BACKUP TEST
# ===================================================

def test_missing_backup_restore():

    invalid_backup = "missing_backup.txt"

    try:

        RollbackManager.restore_backup(
            invalid_backup,
            TEST_FILE
        )

        assert False, "Expected FileNotFoundError"

    except FileNotFoundError:

        assert True

# ===================================================
# MISSING TARGET FILE TEST
# ===================================================

def test_missing_target_backup():

    invalid_target = "missing_target.txt"

    try:

        RollbackManager.create_backup(
            invalid_target
        )

        assert False, "Expected FileNotFoundError"

    except FileNotFoundError:

        assert True