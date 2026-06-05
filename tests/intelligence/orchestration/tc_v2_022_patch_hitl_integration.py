"""
TC_V2_022
PATCH + HITL INTEGRATION

Objective:
Validate integration between:

Patch Generation
→ Patch Validation
→ HITL Decision

Decision Paths:
APPROVE
REVIEW
REJECT
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.patch_generation_engine import PatchGenerationEngine
from ai.patch_validation_engine import PatchValidationEngine


# =========================================================
# REPORT LOCATION
# =========================================================

REPORT_OUTPUT = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "patch_hitl_reports"
    / "tc_v2_022_report.json"
)


# =========================================================
# SIMPLE HITL SIMULATION
# =========================================================

def hitl_decision(validation_result):

    if validation_result.decision == "APPROVE":

        return "AUTO_APPROVED"

    if validation_result.decision == "REVIEW":

        return "PENDING_HUMAN_APPROVAL"

    return "BLOCKED"


# =========================================================
# APPROVE FLOW
# =========================================================

def test_approve_hitl():

    generator = PatchGenerationEngine()
    validator = PatchValidationEngine()

    source_code = """

def run_user_code(user_input):

    result = eval(user_input)

    return result

"""

    patch = generator.generate_patch(
        issue_type="unsafe_eval",
        source_code=source_code,
        target_file="approve_demo.py"
    )

    validation = validator.validate_patch(
        patch
    )

    hitl = hitl_decision(validation)

    passed = (
        validation.decision == "APPROVE"
        and hitl == "AUTO_APPROVED"
    )

    return {
        "passed": passed,
        "validation_decision": validation.decision,
        "hitl_decision": hitl
    }


# =========================================================
# REVIEW FLOW
# =========================================================

def test_review_hitl():

    generator = PatchGenerationEngine()
    validator = PatchValidationEngine()

    source_code = """

print("hello")

"""

    patch = generator.generate_patch(
        issue_type="missing_try_except",
        source_code=source_code,
        target_file="review_demo.py"
    )

    validation = validator.validate_patch(
        patch
    )

    hitl = hitl_decision(validation)

    passed = (
        validation.decision == "REVIEW"
        and hitl == "PENDING_HUMAN_APPROVAL"
    )

    return {
        "passed": passed,
        "validation_decision": validation.decision,
        "hitl_decision": hitl
    }


# =========================================================
# REJECT FLOW
# =========================================================

def test_reject_hitl():

    class FakePatch:

        modified_code = """

exec(user_input)

"""

        confidence_score = 0.95

    validator = PatchValidationEngine()

    validation = validator.validate_patch(
        FakePatch()
    )

    hitl = hitl_decision(validation)

    passed = (
        validation.decision == "REJECT"
        and hitl == "BLOCKED"
    )

    return {
        "passed": passed,
        "validation_decision": validation.decision,
        "hitl_decision": hitl
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_022():

    print("\n" + "=" * 70)
    print("TC_V2_022 PATCH + HITL INTEGRATION")
    print("=" * 70)

    report = {

        "test_case": "TC_V2_022",

        "flows": {

            "approve_hitl":
            test_approve_hitl(),

            "review_hitl":
            test_review_hitl(),

            "reject_hitl":
            test_reject_hitl(),
        }
    }

    total = len(report["flows"])

    passed = sum(
        1
        for flow in report["flows"].values()
        if flow["passed"]
    )

    report["summary"] = {

        "total_flows": total,

        "passed_flows": passed,

        "failed_flows": total - passed,

        "status":
        "PASSED"
        if passed == total
        else "FAILED"
    }

    print("\nFLOW RESULTS")
    print("-" * 70)

    for name, result in report["flows"].items():

        print(
            f"{name}: "
            f"{'PASS' if result['passed'] else 'FAIL'}"
        )

    print("\nOVERALL STATUS:")
    print(report["summary"]["status"])

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

    print(
        f"\n[Report Saved] {REPORT_OUTPUT}"
    )

    return report


if __name__ == "__main__":

    run_tc_v2_022()