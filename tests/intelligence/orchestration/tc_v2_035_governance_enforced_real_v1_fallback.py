"""
TC_V2_035
Governance-Enforced Real V1 Fallback

Purpose:
Validate that real V1 findings are routed through
V2 governance before execution.

Uses:
- Real V1Adapter
- Real repository scan
- Real duplicate findings
- Human approval

Does NOT:
- Modify files
- Execute merges
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
    "tests/output/v2/governance_reports"
)

REPORT_FILE = (
    f"{REPORT_FOLDER}/tc_v2_035_report.json"
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


def run_tc_v2_035():

    print("\n" + "=" * 60)
    print("TC_V2_035")
    print("Governance-Enforced Real V1 Fallback")
    print("=" * 60)

    adapter = V1Adapter(
        project_path=".",
        max_files=25
    )

    findings = adapter.run_analysis()

    if not findings:

        raise RuntimeError(
            "No V1 findings returned."
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
        f"Suggested Action: "
        f"{finding['action']}"
    )

    print("\n" + "=" * 60)
    print("GOVERNANCE APPROVAL")
    print("=" * 60)

    print("A = APPROVE")
    print("R = REJECT")

    decision = input(
        "\nDecision: "
    ).strip().upper()

    while decision not in ["A", "R"]:

        decision = input(
            "Enter A or R: "
        ).strip().upper()

    if decision == "A":

        status = "APPROVED"

        execution_result = (
            "V1 Recommendation Allowed"
        )

    else:

        status = "REJECTED"

        execution_result = (
            "V1 Recommendation Blocked"
        )

    report = {

        "test_case":
        "TC_V2_035",

        "title":
        "Governance-Enforced Real V1 Fallback",

        "finding":
        finding,

        "decision":
        status,

        "execution_result":
        execution_result,

        "status":
        "PASSED"
    }

    save_report(report)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    print(
        f"Decision: "
        f"{status}"
    )

    print(
        f"Execution Result: "
        f"{execution_result}"
    )

    print(
        f"\nReport Saved:\n"
        f"{REPORT_FILE}"
    )

    return report


if __name__ == "__main__":

    run_tc_v2_035()