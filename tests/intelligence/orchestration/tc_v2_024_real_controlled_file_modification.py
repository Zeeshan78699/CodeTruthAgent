"""
TC_V2_024
REAL CONTROLLED FILE MODIFICATION

Objective:
Validate successful repository-safe modification.

Flow:

Patch Generation
→ Patch Validation
→ Governance
→ HITL
→ Backup
→ Modify File
→ Verify Change
→ KEEP CHANGE

No rollback unless failure occurs.
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
    / "real_modification_reports"
)

REPORT_OUTPUT = (
    OUTPUT_DIR
    / "tc_v2_024_report.json"
)

TEST_FILE = (
    OUTPUT_DIR
    / "controlled_modification_test.py"
)

BACKUP_FILE = (
    OUTPUT_DIR
    / "controlled_modification_test.py.bak"
)


# =========================================================
# HELPERS
# =========================================================

def create_backup():

    shutil.copy2(
        TEST_FILE,
        BACKUP_FILE
    )


def restore_backup():

    shutil.copy2(
        BACKUP_FILE,
        TEST_FILE
    )


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
# HITL SIMULATION
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

def run_controlled_modification():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    original_code = """

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
            original_code
        )

    create_backup()

    generator = PatchGenerationEngine()

    validator = PatchValidationEngine()

    patch = generator.generate_patch(

        issue_type="unsafe_eval",

        source_code=original_code,

        target_file=str(TEST_FILE)
    )

    validation = validator.validate_patch(
        patch
    )

    hitl = hitl_decision(
        validation
    )

    if validation.decision != "APPROVE":

        restore_backup()

        return {

            "passed": False,

            "failure_reason":
            "Patch not approved",

            "validation_decision":
            validation.decision
        }

    if hitl != "AUTO_APPROVED":

        restore_backup()

        return {

            "passed": False,

            "failure_reason":
            "HITL rejected patch",

            "hitl_decision":
            hitl
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

    modified_code = TEST_FILE.read_text(
        encoding="utf-8"
    )

    patch_applied = (
        modified_code != original_code
    )

    safe_eval_present = (
        "safe_eval(" in modified_code
    )

    return {

        "passed":
        patch_applied and safe_eval_present,

        "patch_applied":
        patch_applied,

        "safe_eval_present":
        safe_eval_present,

        "validation_decision":
        validation.decision,

        "hitl_decision":
        hitl,

        "rollback_triggered":
        False
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_024():

    print("\n" + "=" * 70)
    print("TC_V2_024 REAL CONTROLLED FILE MODIFICATION")
    print("=" * 70)

    result = run_controlled_modification()

    report = {

        "test_case":
        "TC_V2_024",

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

    run_tc_v2_024()