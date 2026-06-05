"""
TC_V2_026
BLOCK PATH VALIDATION

Objective:

Validate:

Patch
→ Validation
→ REJECT
→ BLOCKED
→ No Modification
→ No Execution

Expected:

Original file remains unchanged.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai.patch_validation_engine import (
    PatchValidationEngine
)


# =========================================================
# PATHS
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "block_path_reports"
)

REPORT_OUTPUT = (
    OUTPUT_DIR
    / "tc_v2_026_report.json"
)

TEST_FILE = (
    OUTPUT_DIR
    / "block_path_test.py"
)

BACKUP_FILE = (
    OUTPUT_DIR
    / "block_path_test.py.bak"
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


def create_backup():

    shutil.copy2(
        TEST_FILE,
        BACKUP_FILE
    )


# =========================================================
# HITL
# =========================================================

def hitl_decision(validation):

    if validation.decision == "APPROVE":
        return "AUTO_APPROVED"

    if validation.decision == "REVIEW":
        return "PENDING_HUMAN_APPROVAL"

    return "BLOCKED"


# =========================================================
# FAKE REJECT PATCH
# =========================================================

class DangerousPatch:

    modified_code = """

exec(user_input)

"""

    confidence_score = 0.95


# =========================================================
# TEST
# =========================================================

def run_block_path_test():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    original_code = """

print("safe code")

"""

    with open(
        TEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            original_code
        )

    create_backup()

    validator = PatchValidationEngine()

    validation = validator.validate_patch(
        DangerousPatch()
    )

    hitl = hitl_decision(
        validation
    )

    current_content = TEST_FILE.read_text(
        encoding="utf-8"
    )

    file_unchanged = (
        current_content == original_code
    )

    execution_blocked = (
        validation.decision == "REJECT"
        and hitl == "BLOCKED"
    )

    return {

        "passed":
        execution_blocked and file_unchanged,

        "validation_decision":
        validation.decision,

        "hitl_decision":
        hitl,

        "execution_blocked":
        execution_blocked,

        "file_modified":
        False,

        "file_unchanged":
        file_unchanged
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_026():

    print("\n" + "=" * 70)
    print("TC_V2_026 BLOCK PATH VALIDATION")
    print("=" * 70)

    result = run_block_path_test()

    report = {

        "test_case":
        "TC_V2_026",

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

    run_tc_v2_026()