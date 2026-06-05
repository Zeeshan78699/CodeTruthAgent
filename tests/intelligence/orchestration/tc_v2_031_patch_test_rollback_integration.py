"""
TC_V2_031
PATCH → TEST → ROLLBACK INTEGRATION

Objective:

Validate:

Patch Applied
→ Test Failure
→ Rollback Triggered
→ Original File Restored

Expected:

Repository returns to original state.
"""

from __future__ import annotations

import json
from pathlib import Path

from validation.rollback_manager import (
    RollbackManager
)


# =========================================================
# PATHS
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "patch_test_rollback_reports"
)

REPORT_OUTPUT = (
    OUTPUT_DIR
    / "tc_v2_031_report.json"
)

TEST_FILE = (
    OUTPUT_DIR
    / "tc_v2_031_test_file.py"
)


# =========================================================
# HELPERS
# =========================================================

def save_report(report):

    REPORT_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        REPORT_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )


# =========================================================
# TEST
# =========================================================

def run_patch_test_rollback():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    original_content = (
        "def status():\n"
        "    return 'safe'\n"
    )

    patched_content = (
        "def status():\n"
        "    return 'modified'\n"
    )

    # -----------------------------------------
    # CREATE ORIGINAL FILE
    # -----------------------------------------

    with open(
        TEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            original_content
        )

    # -----------------------------------------
    # BACKUP
    # -----------------------------------------

    backup_result = (
        RollbackManager.create_backup(
            str(TEST_FILE)
        )
    )

    backup_created = (
        backup_result.get(
            "success",
            False
        )
    )

    # -----------------------------------------
    # APPLY PATCH
    # -----------------------------------------

    with open(
        TEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            patched_content
        )

    patched_state = (
        TEST_FILE.read_text(
            encoding="utf-8"
        )
        == patched_content
    )

    # -----------------------------------------
    # SIMULATED TEST FAILURE
    # -----------------------------------------

    test_result = {
        "success": False
    }

    rollback_triggered = False

    if not test_result["success"]:

        rollback_triggered = True

        restore_result = (
            RollbackManager.restore_backup(
                backup_result["backup_path"],
                str(TEST_FILE)
            )
        )

    else:

        restore_result = {
            "success": False
        }

    # -----------------------------------------
    # VERIFY RESTORE
    # -----------------------------------------

    restored_content = (
        TEST_FILE.read_text(
            encoding="utf-8"
        )
    )

    file_restored = (
        restored_content
        == original_content
    )

    passed = (

        backup_created

        and

        patched_state

        and

        rollback_triggered

        and

        file_restored
    )

    return {

        "passed":
        passed,

        "backup_created":
        backup_created,

        "patch_applied":
        patched_state,

        "test_failed":
        True,

        "rollback_triggered":
        rollback_triggered,

        "restore_success":
        restore_result.get(
            "success",
            False
        ),

        "file_restored":
        file_restored
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_031():

    print("\n" + "=" * 70)
    print(
        "TC_V2_031 PATCH TEST ROLLBACK INTEGRATION"
    )
    print("=" * 70)

    result = run_patch_test_rollback()

    report = {

        "test_case":
        "TC_V2_031",

        "result":
        result,

        "summary": {

            "status":
            "PASSED"
            if result["passed"]
            else "FAILED"
        }
    }

    print("\nSUMMARY")
    print("-" * 70)

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )

    print(
        f"\nOVERALL STATUS: "
        f"{report['summary']['status']}"
    )

    save_report(report)

    print(
        f"\n[Report Saved] "
        f"{REPORT_OUTPUT}"
    )

    return report


if __name__ == "__main__":

    run_tc_v2_031()