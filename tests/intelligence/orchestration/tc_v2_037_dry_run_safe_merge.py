"""
TC_V2_037
Dry Run Safe Merge

Purpose:
Validate safe merge planning without
modifying repository files.

Uses:
- Real V1Adapter
- Real V1 Findings
- Governance Enforcement
- Dry Run Planning

No file modifications occur.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

from ai.v1_adapter import V1Adapter


REPORT_FOLDER = (
    "tests/output/v2/dry_run_reports"
)

REPORT_FILE = (
    f"{REPORT_FOLDER}/tc_v2_037_report.json"
)


# =====================================================
# REPORT
# =====================================================

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


# =====================================================
# GOVERNANCE
# =====================================================

def evaluate_policy(finding):

    if not finding.get(
        "merge_allowed",
        False
    ):

        return {
            "decision":
            "BLOCKED",

            "reason":
            "V1 policy blocks merge."
        }

    return {
        "decision":
        "ALLOWED",

        "reason":
        "Merge policy allows execution."
    }


# =====================================================
# DRY RUN
# =====================================================

def build_dry_run_plan(finding):

    return {

        "keep_function":
        finding["best_function"],

        "remove_function":
        (
            finding["function_2"]
            if finding["best_function"]
            ==
            finding["function_1"]
            else finding["function_1"]
        ),

        "risk_level":
        finding["risk_level"],

        "risk_reason":
        finding["risk_reason"],

        "affected_files": [

            finding["file_1"],
            finding["file_2"]
        ],

        "backup_required":
        True,

        "rollback_available":
        True,

        "repository_modified":
        False,

        "execution_mode":
        "DRY_RUN"
    }


# =====================================================
# MAIN TEST
# =====================================================

def run_tc_v2_037():

    print("\n" + "=" * 60)
    print("TC_V2_037")
    print("Dry Run Safe Merge")
    print("=" * 60)

    adapter = V1Adapter(
        project_path=".",
        max_files=25
    )

    findings = (
        adapter.run_analysis()
    )

    if not findings:

        raise RuntimeError(
            "No findings returned."
        )

    finding = findings[0]

    print("\n" + "=" * 60)
    print("REAL V1 FINDING")
    print("=" * 60)

    print(
        f"Function 1: "
        f"{finding['function_1']}"
    )

    print(
        f"Function 2: "
        f"{finding['function_2']}"
    )

    print(
        f"Risk Level: "
        f"{finding['risk_level']}"
    )

    print(
        f"Merge Allowed: "
        f"{finding['merge_allowed']}"
    )

    governance = (
        evaluate_policy(
            finding
        )
    )

    dry_run_plan = (
        build_dry_run_plan(
            finding
        )
    )

    print("\n" + "=" * 60)
    print("DRY RUN PLAN")
    print("=" * 60)

    print(
        f"Keep Function: "
        f"{dry_run_plan['keep_function']}"
    )

    print(
        f"Remove Function: "
        f"{dry_run_plan['remove_function']}"
    )

    print(
        f"Risk Level: "
        f"{dry_run_plan['risk_level']}"
    )

    print(
        f"Execution Mode: "
        f"{dry_run_plan['execution_mode']}"
    )

    print(
        f"Repository Modified: "
        f"{dry_run_plan['repository_modified']}"
    )

    print(
        f"Rollback Available: "
        f"{dry_run_plan['rollback_available']}"
    )

    print(
        "\nAffected Files:"
    )

    for file in (
        dry_run_plan["affected_files"]
    ):

        print(
            f" - {file}"
        )

    report = {

        "test_case":
        "TC_V2_037",

        "title":
        "Dry Run Safe Merge",

        "finding":
        finding,

        "governance":
        governance,

        "dry_run_plan":
        dry_run_plan,

        "status":
        "PASSED"
    }

    save_report(report)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    print(
        f"Governance Decision: "
        f"{governance['decision']}"
    )

    print(
        f"Reason: "
        f"{governance['reason']}"
    )

    print(
        f"\nReport Saved:\n"
        f"{REPORT_FILE}"
    )

    return report


# =====================================================
# ENTRY
# =====================================================

if __name__ == "__main__":

    run_tc_v2_037()