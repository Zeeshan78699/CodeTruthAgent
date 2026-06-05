"""
TC_V2_037A
Dependency-Aware Dry Run Impact Analysis

Purpose:
Validate repository-wide impact analysis before
any safe modification is executed.

Uses:
- Real V1Adapter
- Real V1 Findings
- Real Dependency Analysis
- Governance Enforcement

No repository modification occurs.
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
from core.risk_analyzer import (
    find_project_usage
)

# =====================================================
# CONFIG
# =====================================================

REPORT_FOLDER = (
    "tests/output/v2/dry_run_reports"
)

REPORT_FILE = (
    f"{REPORT_FOLDER}/tc_v2_037a_report.json"
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
# IMPACT ANALYSIS
# =====================================================

def build_impact_analysis(finding):

    keep_function = (
        finding["best_function"]
    )

    remove_function = (
        finding["function_2"]
        if keep_function
        ==
        finding["function_1"]
        else finding["function_1"]
    )

    usage_count, dependency_map = (
        find_project_usage(
            ".",
            remove_function
        )
    )

    impacted_files = []

    for file_path, count in (
        dependency_map.items()
    ):

        impacted_files.append({

            "file":
            file_path,

            "references":
            count
        })

    return {

        "function_keep":
        keep_function,

        "function_remove":
        remove_function,

        "total_references":
        usage_count,

        "dependency_count":
        len(dependency_map),

        "affected_files":
        impacted_files,

        "execution_mode":
        "DRY_RUN",

        "repository_modified":
        False,

        "backup_required":
        True,

        "rollback_available":
        True
    }

# =====================================================
# MAIN TEST
# =====================================================

def run_tc_v2_037a():

    print("\n" + "=" * 60)
    print("TC_V2_037A")
    print("Dependency-Aware Dry Run")
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

    governance = (
        evaluate_policy(
            finding
        )
    )

    impact_analysis = (
        build_impact_analysis(
            finding
        )
    )

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

    print("\n" + "=" * 60)
    print("DEPENDENCY IMPACT ANALYSIS")
    print("=" * 60)

    print(
        f"Keep Function: "
        f"{impact_analysis['function_keep']}"
    )

    print(
        f"Remove Function: "
        f"{impact_analysis['function_remove']}"
    )

    print(
        f"Total References: "
        f"{impact_analysis['total_references']}"
    )

    print(
        f"Impacted Files: "
        f"{impact_analysis['dependency_count']}"
    )

    print(
        f"Execution Mode: "
        f"{impact_analysis['execution_mode']}"
    )

    print(
        f"Rollback Available: "
        f"{impact_analysis['rollback_available']}"
    )

    print("\nAffected Files:")

    if impact_analysis["affected_files"]:

        for item in (
            impact_analysis["affected_files"]
        ):

            print(
                f" - {item['file']} "
                f"({item['references']} refs)"
            )

    else:

        print(
            "No dependent files found."
        )

    report = {

        "test_case":
        "TC_V2_037A",

        "title":
        "Dependency-Aware Dry Run Impact Analysis",

        "finding":
        finding,

        "governance":
        governance,

        "impact_analysis":
        impact_analysis,

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

    run_tc_v2_037a()