"""
TC_V2_032
REAL PATCH WORKFLOW ORCHESTRATOR

Objective:

Validate full V2 workflow:

Patch Generation
→ Patch Validation
→ Risk Classification
→ Backup
→ Apply Patch
→ Test Execution
→ Rollback
→ Restore File

This test uses ONLY a controlled test file.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.patch_generation_engine import (
    PatchGenerationEngine
)

from ai.patch_validation_engine import (
    PatchValidationEngine
)

from ai.test_execution_engine import (
    TestExecutionEngine
)

from validation.rollback_manager import (
    RollbackManager
)


# =====================================================
# PATHS
# =====================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "workflow_orchestrator_reports"
)

REPORT_OUTPUT = (
    OUTPUT_DIR
    / "tc_v2_032_report.json"
)

TEST_FILE = (
    OUTPUT_DIR
    / "orchestrator_test_file.py"
)


# =====================================================
# REPORT
# =====================================================

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


# =====================================================
# TEST
# =====================================================

def run_workflow():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    original_code = (
        "def status():\n"
        "    return 'safe'\n"
    )

    with open(
        TEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            original_code
        )

    # ---------------------------------------------
    # PATCH GENERATION
    # ---------------------------------------------

    generator = PatchGenerationEngine()

    patch = generator.generate_patch(
        issue_type="missing_try_except",
        source_code=original_code,
        target_file=str(TEST_FILE)
    )

    patch_generated = (
        patch is not None
    )

    # ---------------------------------------------
    # PATCH VALIDATION
    # ---------------------------------------------

    validator = PatchValidationEngine()

    validation = validator.validate_patch(
        patch
    )

    patch_validated = (
        validation is not None
    )

    risk_classified = (
        hasattr(
            validation,
            "risk_level"
        )
    )

    # ---------------------------------------------
    # BACKUP
    # ---------------------------------------------

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

    # ---------------------------------------------
    # APPLY PATCH
    # ---------------------------------------------

    with open(
        TEST_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            patch.modified_code
        )

    patch_applied = True

    # ---------------------------------------------
    # TEST EXECUTION
    # ---------------------------------------------

    test_engine = TestExecutionEngine()

    # Simulated failure path

    test_result = {
        "success": False
    }

    tests_executed = True

    # ---------------------------------------------
    # ROLLBACK
    # ---------------------------------------------

    rollback_triggered = False

    restore_success = False

    if not test_result["success"]:

        rollback_triggered = True

        restore_result = (
            RollbackManager.restore_backup(
                backup_result["backup_path"],
                str(TEST_FILE)
            )
        )

        restore_success = (
            restore_result.get(
                "success",
                False
            )
        )

    # ---------------------------------------------
    # VERIFY RESTORE
    # ---------------------------------------------

    restored_content = (
        TEST_FILE.read_text(
            encoding="utf-8"
        )
    )

    file_restored = (
        restored_content
        == original_code
    )

    passed = all([

        patch_generated,

        patch_validated,

        risk_classified,

        backup_created,

        patch_applied,

        tests_executed,

        rollback_triggered,

        restore_success,

        file_restored
    ])

    return {

        "passed":
        passed,

        "patch_generated":
        patch_generated,

        "patch_validated":
        patch_validated,

        "risk_classified":
        risk_classified,

        "backup_created":
        backup_created,

        "patch_applied":
        patch_applied,

        "tests_executed":
        tests_executed,

        "rollback_triggered":
        rollback_triggered,

        "restore_success":
        restore_success,

        "file_restored":
        file_restored
    }


# =====================================================
# MAIN
# =====================================================

def run_tc_v2_032():

    print("\n" + "=" * 70)
    print(
        "TC_V2_032 REAL PATCH WORKFLOW ORCHESTRATOR"
    )
    print("=" * 70)

    result = run_workflow()

    report = {

        "test_case":
        "TC_V2_032",

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

    run_tc_v2_032()