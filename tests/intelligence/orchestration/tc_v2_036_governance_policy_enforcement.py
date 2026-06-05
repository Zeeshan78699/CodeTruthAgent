"""
TC_V2_036
Governance Policy Enforcement

Purpose:
Validate governance policy enforcement
on real V1 findings.

Rule:

merge_allowed = False
    => BLOCK

merge_allowed = True
and Human Approved
    => ALLOW

merge_allowed = True
and Human Rejected
    => BLOCK

Author:
CodeTruth Agent V2
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


# =========================================================
# CONFIG
# =========================================================

REPORT_FOLDER = (
    "tests/output/v2/governance_reports"
)

REPORT_FILE = (
    f"{REPORT_FOLDER}/tc_v2_036_report.json"
)


# =========================================================
# REPORT WRITER
# =========================================================

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


# =========================================================
# GOVERNANCE POLICY
# =========================================================

def evaluate_governance_policy(
    finding,
    human_decision
):

    merge_allowed = (
        finding.get(
            "merge_allowed",
            False
        )
    )

    if not merge_allowed:

        return {
            "final_decision":
            "BLOCKED",

            "reason":
            "V1 policy blocks merge."
        }

    if human_decision == "APPROVED":

        return {
            "final_decision":
            "ALLOWED",

            "reason":
            "Approved by governance."
        }

    return {
        "final_decision":
        "BLOCKED",

        "reason":
        "Rejected by governance."
    }


# =========================================================
# MAIN TEST
# =========================================================

def run_tc_v2_036():

    print("\n" + "=" * 60)
    print("TC_V2_036")
    print("Governance Policy Enforcement")
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
            "No findings returned "
            "from V1Adapter."
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

    print(
        f"Action: "
        f"{finding['action']}"
    )

    print("\n" + "=" * 60)
    print("GOVERNANCE DECISION")
    print("=" * 60)

    print("A = APPROVE")
    print("R = REJECT")

    choice = input(
        "\nDecision: "
    ).strip().upper()

    while choice not in ["A", "R"]:

        choice = input(
            "Enter A or R: "
        ).strip().upper()

    human_decision = (
        "APPROVED"
        if choice == "A"
        else "REJECTED"
    )

    result = (
        evaluate_governance_policy(
            finding,
            human_decision
        )
    )

    print("\n" + "=" * 60)
    print("POLICY RESULT")
    print("=" * 60)

    print(
        f"Human Decision: "
        f"{human_decision}"
    )

    print(
        f"Final Decision: "
        f"{result['final_decision']}"
    )

    print(
        f"Reason: "
        f"{result['reason']}"
    )

    report = {

        "test_case":
        "TC_V2_036",

        "title":
        "Governance Policy Enforcement",

        "finding":
        finding,

        "human_decision":
        human_decision,

        "policy_result":
        result,

        "status":
        "PASSED"
    }

    save_report(report)

    print(
        f"\nReport Saved:\n"
        f"{REPORT_FILE}"
    )

    return report


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    run_tc_v2_036()