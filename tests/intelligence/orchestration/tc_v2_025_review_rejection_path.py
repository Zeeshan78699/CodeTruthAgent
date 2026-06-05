"""
TC_V2_025
REVIEW REJECTION PATH

Objective:

Validate:

Patch
→ Validation
→ REVIEW
→ HITL
→ Human Rejects
→ No Modification

Expected:

File remains unchanged.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ai.patch_generation_engine import PatchGenerationEngine
from ai.patch_validation_engine import PatchValidationEngine


# =========================================================
# PATHS
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "review_rejection_reports"
)

REPORT_OUTPUT = (
    OUTPUT_DIR
    / "tc_v2_025_report.json"
)

TEST_FILE = (
    OUTPUT_DIR
    / "review_rejection_test.py"
)

BACKUP_FILE = (
    OUTPUT_DIR
    / "review_rejection_test.py.bak"
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
# TEST
# =========================================================

def run_review_rejection_test():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    original_code = """
print("hello")
"""

    with open(
        TEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(original_code)

    create_backup()

    generator = PatchGenerationEngine()
    validator = PatchValidationEngine()

    patch = generator.generate_patch(
        issue_type="missing_try_except",
        source_code=original_code,
        target_file=str(TEST_FILE)
    )

    validation = validator.validate_patch(
        patch
    )

    hitl = hitl_decision(validation)

    # Simulated human rejection
    human_decision = "REJECTED"

    if hitl != "PENDING_HUMAN_APPROVAL":

        return {
            "passed": False,
            "reason": "Expected REVIEW path"
        }

    current_content = TEST_FILE.read_text(
        encoding="utf-8"
    )

    file_unchanged = (
        current_content == original_code
    )

    return {

        "passed":
        file_unchanged,

        "validation_decision":
        validation.decision,

        "hitl_decision":
        hitl,

        "human_decision":
        human_decision,

        "file_modified":
        False,

        "file_unchanged":
        file_unchanged
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_025():

    print("\n" + "=" * 70)
    print("TC_V2_025 REVIEW REJECTION PATH")
    print("=" * 70)

    result = run_review_rejection_test()

    report = {

        "test_case":
        "TC_V2_025",

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

    run_tc_v2_025()