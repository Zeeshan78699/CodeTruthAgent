"""
TC_V2_040
REVIEW Severity Workflow

Objective:

REVIEW
↓
PENDING_REVIEW
↓
Human Approval
↓
Governed Execution
↓
Backup
↓
Modification
↓
Syntax Validation

Uses controlled repository only.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from core.code_modifier import apply_safe_merge

from validation.approval_engine import (
    request_approval,
    approve_finding
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
    / "review_workflow_reports"
)

REPORT_FILE = (
    OUTPUT_DIR
    / "tc_v2_040_report.json"
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

def run_tc_v2_040():

    print("\n" + "=" * 70)
    print(
        "TC_V2_040 REVIEW Severity Workflow"
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
        "REVIEW",

        "category":
        "SAFE_LOGICAL_DUPLICATE"
    }

    # ---------------------------------------------
    # Phase 1
    # REVIEW should create pending review
    # ---------------------------------------------

    approval_result = (
        request_approval(
            finding
        )
    )

    initial_status = (
        approval_result["status"]
    )

    print(
        f"\nInitial Status: "
        f"{initial_status}"
    )

    if initial_status != "PENDING_REVIEW":

        raise RuntimeError(
            "Expected PENDING_REVIEW."
        )

    # ---------------------------------------------
    # Phase 2
    # Human Approval
    # ---------------------------------------------

    human_approval = (
        approve_finding(
            finding,
            reviewer="TC_V2_040"
        )
    )

    print(
        "\nHuman Approval Recorded"
    )

    # ---------------------------------------------
    # Phase 3
    # Execute modification after approval
    # ---------------------------------------------

    original_cwd = os.getcwd()

    try:

        os.chdir(
            str(CONTROLLED_REPO)
        )

        execution_finding = {

            "file_path":
            "duplicate_module.py",

            "function_name":
            "compute_total",

            "severity":
            "SAFE",

            "category":
            "SAFE_LOGICAL_DUPLICATE"
        }

        def merge_action():

            apply_safe_merge(
                file_path="duplicate_module.py",
                remove_func="compute_total",
                keep_func="calculate_total"
            )

        execution_result = (
            execute_governed_action(
                finding=execution_finding,
                target_file="duplicate_module.py",
                proposed_action=merge_action,
                confidence_score=1.0
            )
        )

    finally:

        os.chdir(
            original_cwd
        )

    modified_module = (
        duplicate_file.read_text(
            encoding="utf-8"
        )
    )

    modified_consumer = (
        consumer_file.read_text(
            encoding="utf-8"
        )
    )

    merge_executed = (
        "def compute_total("
        not in modified_module
    )

    consumer_updated = (
        "calculate_total("
        in modified_consumer
    )

    execution_success = (
        execution_result.get(
            "execution_status"
        )
        ==
        "EXECUTED_SUCCESSFULLY"
    )

    report = {

        "test_case":
        "TC_V2_040",

        "severity":
        "REVIEW",

        "initial_status":
        initial_status,

        "human_approval":
        human_approval["decision"],

        "execution_status":
        execution_result.get(
            "execution_status"
        ),

        "merge_executed":
        merge_executed,

        "consumer_updated":
        consumer_updated,

        "status":
        (
            "PASSED"
            if (
                initial_status
                ==
                "PENDING_REVIEW"
                and human_approval["decision"]
                ==
                "APPROVED"
                and execution_success
                and merge_executed
                and consumer_updated
            )
            else
            "FAILED"
        )
    }

    save_report(report)

    print("\nRESULT")
    print("-" * 70)

    print(
        f"Initial Status: "
        f"{initial_status}"
    )

    print(
        f"Human Approval: "
        f"{human_approval['decision']}"
    )

    print(
        f"Execution Status: "
        f"{execution_result.get('execution_status')}"
    )

    print(
        f"Merge Executed: "
        f"{merge_executed}"
    )

    print(
        f"Consumer Updated: "
        f"{consumer_updated}"
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

    run_tc_v2_040()