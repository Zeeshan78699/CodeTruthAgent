"""
TC_V2_038
Real Safe Modification

Purpose:
Validate end-to-end safe modification using:

Duplicate Detection
→ Merge Advisor
→ Governance
→ Backup
→ apply_safe_merge()
→ Syntax Validation
→ Rollback

Runs ONLY inside a controlled repository.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from core.code_modifier import apply_safe_merge
from validation.rollback_manager import RollbackManager
from validation.syntax_validator import validate_python_syntax


REPORT_FOLDER = (
    "tests/output/v2/real_modification_reports"
)

REPORT_FILE = (
    f"{REPORT_FOLDER}/tc_v2_038_report.json"
)

CONTROLLED_REPO = (
    Path(REPORT_FOLDER)
    / "controlled_merge_repo"
)


def save_report(report):

    os.makedirs(
        REPORT_FOLDER,
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
        shutil.rmtree(CONTROLLED_REPO)

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

    return duplicate_file, consumer_file


def run_tc_v2_038():

    print("\n" + "=" * 60)
    print("TC_V2_038")
    print("Real Safe Modification")
    print("=" * 60)

    duplicate_file, consumer_file = (
        build_controlled_repository()
    )

    rollback_result = (
        RollbackManager.create_backup(
            str(duplicate_file)
        )
    )

    rollback_path = (
        rollback_result["backup_path"]
    )

    original_cwd = os.getcwd()

    try:

        os.chdir(
            str(CONTROLLED_REPO)
        )

        apply_safe_merge(
            file_path="duplicate_module.py",
            remove_func="compute_total",
            keep_func="calculate_total"
        )

    finally:

        os.chdir(original_cwd)

    modified_code = (
        duplicate_file.read_text(
            encoding="utf-8"
        )
    )

    consumer_code = (
        consumer_file.read_text(
            encoding="utf-8"
        )
    )

    merge_executed = (
        "def compute_total("
        not in modified_code
    )

    consumer_updated = (
        "calculate_total("
        in consumer_code
    )

    syntax_ok = (
        validate_python_syntax(
            str(duplicate_file)
        )
    )

    restore_result = (
        RollbackManager.restore_backup(
            rollback_path,
            str(duplicate_file)
        )
    )

    restored_code = (
        duplicate_file.read_text(
            encoding="utf-8"
        )
    )

    rollback_successful = (
        "def compute_total("
        in restored_code
    )

    report = {

        "test_case":
        "TC_V2_038",

        "backup_created":
        rollback_result["success"],

        "merge_executed":
        merge_executed,

        "consumer_updated":
        consumer_updated,

        "syntax_validation":
        syntax_ok,

        "rollback_successful":
        rollback_successful,

        "repository_restored":
        rollback_successful,

        "status":
        (
            "PASSED"
            if (
                rollback_result["success"]
                and merge_executed
                and consumer_updated
                and syntax_ok
                and rollback_successful
            )
            else
            "FAILED"
        )
    }

    save_report(report)

    print("\nRESULT")
    print("-" * 60)

    for key, value in report.items():

        if key != "test_case":

            print(
                f"{key}: {value}"
            )

    return report


if __name__ == "__main__":

    run_tc_v2_038()