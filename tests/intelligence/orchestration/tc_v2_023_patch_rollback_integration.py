"""
TC_V2_023
PATCH + ROLLBACK INTEGRATION

Objective:
Validate integration between:

Patch Generation
→ Patch Validation
→ Governance
→ HITL
→ Backup Creation
→ Rollback

This test NEVER modifies production files.
Only temporary test files are used.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai.patch_generation_engine import PatchGenerationEngine
from ai.patch_validation_engine import PatchValidationEngine


# =========================================================
# REPORT LOCATION
# =========================================================

REPORT_OUTPUT = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "patch_rollback_reports"
    / "tc_v2_023_report.json"
)

TEST_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "patch_rollback_reports"
)

TEST_FILE = TEST_DIR / "rollback_test.py"

BACKUP_FILE = TEST_DIR / "rollback_test.py.bak"


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


def create_backup():

    shutil.copy2(
        TEST_FILE,
        BACKUP_FILE
    )


def rollback_file():

    shutil.copy2(
        BACKUP_FILE,
        TEST_FILE
    )


# =========================================================
# TEST
# =========================================================

def test_patch_rollback():

    TEST_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    original_content = """

def run_user_code(user_input):

    result = eval(user_input)

    return result

"""

    with open(
        TEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            original_content
        )

    create_backup()

    generator = PatchGenerationEngine()

    validator = PatchValidationEngine()

    patch = generator.generate_patch(
        issue_type="unsafe_eval",
        source_code=original_content,
        target_file=str(TEST_FILE)
    )

    validation = validator.validate_patch(
        patch
    )

    if validation.decision != "APPROVE":

        return {
            "passed": False,
            "reason": "Patch was not approved"
        }

    # =====================================
    # APPLY PATCH
    # =====================================

    with open(
        TEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            patch.modified_code
        )

    modified_content = TEST_FILE.read_text(
        encoding="utf-8"
    )

    patch_applied = (
        modified_content != original_content
    )

    # =====================================
    # SIMULATED FAILURE
    # =====================================

    rollback_file()

    restored_content = TEST_FILE.read_text(
        encoding="utf-8"
    )

    rollback_success = (
        restored_content == original_content
    )

    return {

        "passed":
        patch_applied and rollback_success,

        "patch_applied":
        patch_applied,

        "rollback_success":
        rollback_success,

        "validation_decision":
        validation.decision
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_023():

    print("\n" + "=" * 70)
    print("TC_V2_023 PATCH + ROLLBACK INTEGRATION")
    print("=" * 70)

    result = test_patch_rollback()

    report = {

        "test_case":
        "TC_V2_023",

        "result":
        result,

        "summary": {

            "status":
            "PASSED"
            if result["passed"]
            else "FAILED"
        }
    }

    print("\nRESULT")
    print("-" * 70)

    print(
        "PASS"
        if result["passed"]
        else "FAIL"
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

    run_tc_v2_023()