"""
TC_V2_021
PATCH + GOVERNANCE INTEGRATION

Objective:
Validate end-to-end integration between:

Patch Generation
→ Patch Validation
→ Governance Decision

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
    / "patch_governance_reports"
    / "tc_v2_021_report.json"
)


# =========================================================
# HELPERS
# =========================================================

def save_report(report):

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


# =========================================================
# APPROVE FLOW
# =========================================================

def test_approve_flow():

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

    passed = (
        validation.decision == "APPROVE"
    )

    return {
        "passed": passed,
        "decision": validation.decision,
        "risk_level": validation.risk_level,
        "confidence_score": validation.confidence_score
    }


# =========================================================
# REVIEW FLOW
# =========================================================

def test_review_flow():

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

    passed = (
        validation.decision == "REVIEW"
    )

    return {
        "passed": passed,
        "decision": validation.decision,
        "risk_level": validation.risk_level,
        "confidence_score": validation.confidence_score
    }


# =========================================================
# REJECT FLOW
# =========================================================

def test_reject_flow():

    class FakePatch:

        modified_code = """

exec(user_input)

"""

        confidence_score = 0.95

    validator = PatchValidationEngine()

    validation = validator.validate_patch(
        FakePatch()
    )

    passed = (
        validation.decision == "REJECT"
    )

    return {
        "passed": passed,
        "decision": validation.decision,
        "risk_level": validation.risk_level,
        "reasons": validation.reasons
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_021():

    print("\n" + "=" * 70)
    print("TC_V2_021 PATCH + GOVERNANCE INTEGRATION")
    print("=" * 70)

    report = {

        "test_case": "TC_V2_021",

        "flows": {

            "approve_flow":
            test_approve_flow(),

            "review_flow":
            test_review_flow(),

            "reject_flow":
            test_reject_flow(),
        }
    }

    total_flows = len(
        report["flows"]
    )

    passed_flows = sum(
        1
        for flow in report["flows"].values()
        if flow["passed"]
    )

    report["summary"] = {

        "total_flows": total_flows,

        "passed_flows": passed_flows,

        "failed_flows":
        total_flows - passed_flows,

        "status":
        "PASSED"
        if passed_flows == total_flows
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
    print(
        report["summary"]["status"]
    )

    save_report(report)

    print(
        f"\n[Report Saved] "
        f"{REPORT_OUTPUT}"
    )

    return report


if __name__ == "__main__":

    run_tc_v2_021()