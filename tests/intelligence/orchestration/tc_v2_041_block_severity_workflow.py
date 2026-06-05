"""
TC_V2_041
BLOCK Severity Workflow

Objective:

BLOCK
↓
Auto Reject
↓
Execution Blocked
↓
No Backup Created
↓
No Modification Performed

This validates the final governance path.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from core.code_modifier import apply_safe_merge

from validation.approval_engine import (
    request_approval
)

from validation.safe_execution_engine import (
    execute_governed_action
)


# =========================================================
# CONFIG
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "block_workflow_reports"
)

REPORT_FILE = (
    OUTPUT_DIR
    / "tc_v2_041_report.json"
)

CONTROLLED_REPO = (
    OUTPUT_DIR
    / "controlled_repo"
)


# =========================================================
# HELPERS
# =========================================================

def save_report(report):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )


def build_controlled_repository():

    if CONTROLLED_REPO.exists():
        shutil.rmtree(
            CONTROLLED_REPO
        )

    CONTROLLED_REPO.mkdir(
        parents=True,
        exist_ok=True
    )

    duplicate_module = """
def calculate_total(x):
    return x * 2


def compute_total(x):
    return x * 2
"""

    consumer = """
from duplicate_module import compute_total

value = compute_total(10)
"""

    duplicate_file = (
        CONTROLLED_REPO
        / "duplicate_module.py"
    )

    consumer_file = (
        CONTROLLED_REPO
        / "consumer.py"
    )

    duplicate_file.write_text(
        duplicate_module,
        encoding="utf-8"
    )

    consumer_file.write_text(
        consumer,
        encoding="utf-8"
    )

    return (
        duplicate_file,
        consumer_file
    )


# =========================================================
# TEST
# =========================================================

def run_tc_v2_041():

    print("\n" + "=" * 70)
    print(
        "TC_V2_041 BLOCK Severity Workflow"
    )
    print("=" * 70)

    duplicate_file, consumer_file = (
        build_controlled_repository()
    )

    finding = {

        "file_path":
        "duplicate_module.py",

        "function_name":
        "compute_total",

        "severity":
        "BLOCK",

        "category":
        "BUSINESS_LOGIC_CONFLICT"
    }

    # --------------------------------------------------
    # Phase 1
    # Approval Engine
    # --------------------------------------------------

    approval_result = (
        request_approval(
            finding
        )
    )

    approval_status = (
        approval_result["status"]
    )

    print(
        f"\nApproval Status: "
        f"{approval_status}"
    )

    # --------------------------------------------------
    # Phase 2
    # Attempt governed execution
    # --------------------------------------------------

    original_cwd = os.getcwd()

    try:

        os.chdir(
            str(CONTROLLED_REPO)
        )

        def merge_action():

            apply_safe_merge(
                file_path="duplicate_module.py",
                remove_func="compute_total",
                keep_func="calculate_total"
            )

        execution_result = (
            execute_governed_action(
                finding=finding,
                target_file="duplicate_module.py",
                proposed_action=merge_action,
                confidence_score=1.0
            )
        )

    finally:

        os.chdir(
            original_cwd
        )

    execution_status = (
        execution_result.get(
            "execution_status"
        )
    )

    # --------------------------------------------------
    # Phase 3
    # Verify repository unchanged
    # --------------------------------------------------

    module_code = (
        duplicate_file.read_text(
            encoding="utf-8"
        )
    )

    consumer_code = (
        consumer_file.read_text(
            encoding="utf-8"
        )
    )

    module_unchanged = (
        "def compute_total("
        in module_code
    )

    consumer_unchanged = (
        "compute_total("
        in consumer_code
    )

    rollback_created = (
        "rollback_created"
        in execution_result
    )

    report = {

        "test_case":
        "TC_V2_041",

        "severity":
        "BLOCK",

        "approval_status":
        approval_status,

        "execution_status":
        execution_status,

        "backup_created":
        rollback_created,

        "module_unchanged":
        module_unchanged,

        "consumer_unchanged":
        consumer_unchanged,

        "repository_modified":
        not (
            module_unchanged
            and consumer_unchanged
        ),

        "status":
        (
            "PASSED"
            if (
                approval_status
                == "REJECTED"
                and execution_status
                == "BLOCKED"
                and not rollback_created
                and module_unchanged
                and consumer_unchanged
            )
            else
            "FAILED"
        )
    }

    save_report(report)

    print("\nRESULT")
    print("-" * 70)

    print(
        f"Approval Status: "
        f"{approval_status}"
    )

    print(
        f"Execution Status: "
        f"{execution_status}"
    )

    print(
        f"Backup Created: "
        f"{rollback_created}"
    )

    print(
        f"Module Unchanged: "
        f"{module_unchanged}"
    )

    print(
        f"Consumer Unchanged: "
        f"{consumer_unchanged}"
    )

    print(
        f"\nOVERALL STATUS: "
        f"{report['status']}"
    )

    print(
        f"\n[Report Saved] "
        f"{REPORT_FILE}"
    )

    return report


if __name__ == "__main__":

    run_tc_v2_041()