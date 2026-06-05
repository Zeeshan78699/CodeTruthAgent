"""
TC_V2_039
Governed Real Safe Modification

Objective:

Governance
→ Approval Engine
→ Safe Execution Engine
→ Rollback Manager
→ Real Safe Merge
→ Syntax Validation

Uses controlled repository only.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from core.code_modifier import apply_safe_merge

from validation.safe_execution_engine import (
    execute_governed_action
)

from validation.rollback_manager import (
    RollbackManager
)


# =========================================================
# CONFIG
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "governed_modification_reports"
)

REPORT_FILE = (
    OUTPUT_DIR
    / "tc_v2_039_report.json"
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

def run_tc_v2_039():

    print("\n" + "=" * 70)
    print(
        "TC_V2_039 "
        "Governed Real Safe Modification"
    )
    print("=" * 70)

    duplicate_file, consumer_file = (
        build_controlled_repository()
    )

    original_cwd = os.getcwd()

    try:

        os.chdir(
            str(CONTROLLED_REPO)
        )

        finding = {

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

        result = (
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
        result.get(
            "execution_status"
        )
        ==
        "EXECUTED_SUCCESSFULLY"
    )

    rollback_created = (
        "rollback_created"
        in result
    )

    report = {

        "test_case":
        "TC_V2_039",

        "governance_status":
        result.get(
            "execution_status"
        ),

        "execution_result":
        result,

        "merge_executed":
        merge_executed,

        "consumer_updated":
        consumer_updated,

        "rollback_created":
        rollback_created,

        "status":
        (
            "PASSED"
            if (
                execution_success
                and merge_executed
                and consumer_updated
                and rollback_created
            )
            else
            "FAILED"
        )
    }

    save_report(report)

    print("\nRESULT")
    print("-" * 70)

    print(
        f"Execution Status: "
        f"{result.get('execution_status')}"
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
        f"Rollback Created: "
        f"{rollback_created}"
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


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    run_tc_v2_039()