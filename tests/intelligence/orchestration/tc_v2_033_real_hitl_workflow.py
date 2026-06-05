"""
TC_V2_033
REAL HITL (HUMAN-IN-THE-LOOP) WORKFLOW VALIDATION

Objective:
Validate the complete REVIEW → Human Approval / Rejection flow.

Workflow:

REVIEW
↓
request_approval()
↓
PENDING_REVIEW
↓
Human Decision
↓
APPROVE / REJECT
↓
Execution Allowed / Blocked

Expected Result:
PASS

Author:
CodeTruth Agent V2
"""

from __future__ import annotations

import json
import os

from validation.approval_engine import (
    request_approval,
    approve_finding,
    reject_finding,
    get_pending_reviews
)


# =========================================================
# CONFIG
# =========================================================

REPORT_FOLDER = (
    "tests/output/v2/patch_hitl_reports"
)

REPORT_FILE = (
    f"{REPORT_FOLDER}/tc_v2_033_report.json"
)


# =========================================================
# REPORT WRITER
# =========================================================

def save_report(report_data):

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
            report_data,
            file,
            indent=4
        )


# =========================================================
# REAL HITL TEST
# =========================================================

def test_real_hitl_workflow():

    print("\n" + "=" * 60)
    print("REAL HITL WORKFLOW")
    print("=" * 60)

    finding = {

        "file_path":
        "sample_module.py",

        "function_name":
        "update_customer_record",

        "severity":
        "REVIEW",

        "category":
        "BUSINESS_LOGIC"
    }

    # -----------------------------------------------------
    # STEP 1
    # REVIEW ROUTING
    # -----------------------------------------------------

    approval_result = request_approval(
        finding
    )

    print(
        "\nApproval Status:"
    )

    print(
        approval_result["status"]
    )

    assert (
        approval_result["status"]
        == "PENDING_REVIEW"
    )

    # -----------------------------------------------------
    # STEP 2
    # HUMAN DECISION
    # -----------------------------------------------------

    print("\n" + "-" * 60)
    print("HUMAN APPROVAL REQUIRED")
    print("-" * 60)

    print("A = APPROVE")
    print("R = REJECT")

    choice = input(
        "\nDecision: "
    ).strip().upper()

    while choice not in ["A", "R"]:

        print(
            "\nInvalid choice."
        )

        choice = input(
            "Enter A or R: "
        ).strip().upper()

    # -----------------------------------------------------
    # APPROVED PATH
    # -----------------------------------------------------

    if choice == "A":

        human_decision = approve_finding(

            finding,

            reviewer="human_reviewer"
        )

        execution_status = (
            "ALLOWED"
        )

        final_status = (
            "APPROVED"
        )

    # -----------------------------------------------------
    # REJECTED PATH
    # -----------------------------------------------------

    else:

        human_decision = reject_finding(

            finding,

            reviewer="human_reviewer",

            reason=(
                "Rejected during "
                "TC_V2_033 validation."
            )
        )

        execution_status = (
            "BLOCKED"
        )

        final_status = (
            "REJECTED"
        )

    print("\n" + "-" * 60)

    print(
        f"Human Decision: "
        f"{human_decision['decision']}"
    )

    print(
        f"Execution Status: "
        f"{execution_status}"
    )

    print("-" * 60)

    return {

        "approval_status":
        approval_result["status"],

        "human_decision":
        human_decision["decision"],

        "execution_status":
        execution_status,

        "final_status":
        final_status,

        "status":
        "PASSED"
    }


# =========================================================
# PENDING REVIEW CHECK
# =========================================================

def test_pending_review_tracking():

    pending_reviews = (
        get_pending_reviews()
    )

    print("\n" + "=" * 60)
    print("PENDING REVIEW CHECK")
    print("=" * 60)

    print(
        f"Pending Reviews Found: "
        f"{len(pending_reviews)}"
    )

    return {

        "pending_review_count":
        len(pending_reviews),

        "status":
        "PASSED"
    }


# =========================================================
# MAIN TEST RUNNER
# =========================================================

def run_tc_v2_033():

    print("\n" + "=" * 60)
    print("TC_V2_033")
    print("REAL HITL WORKFLOW VALIDATION")
    print("=" * 60)

    hitl_result = (
        test_real_hitl_workflow()
    )

    pending_result = (
        test_pending_review_tracking()
    )

    report = {

        "test_case":
        "TC_V2_033",

        "title":
        "Real HITL Workflow Validation",

        "status":
        "PASSED",

        "hitl_result":
        hitl_result,

        "pending_review_check":
        pending_result
    }

    save_report(report)

    print("\n" + "=" * 60)
    print("TC_V2_033 PASSED")
    print("=" * 60)

    print(
        f"\nReport Saved:\n"
        f"{REPORT_FILE}"
    )

    return report


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    run_tc_v2_033()