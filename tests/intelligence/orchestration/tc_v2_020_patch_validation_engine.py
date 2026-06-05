"""
TC_V2_020
PATCH VALIDATION ENGINE

Objective:
Validate PatchValidationEngine decisions.

Validation Areas:
- APPROVE
- REVIEW
- REJECT
- Governance Failure
- Syntax Failure
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
    / "patch_validation_reports"
    / "tc_v2_020_report.json"
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
# TEST 001
# APPROVE
# =========================================================

def test_approve():

    generator = PatchGenerationEngine()
    validator = PatchValidationEngine()

    source = """

def run_user_code(user_input):

    result = eval(user_input)

    return result

"""

    patch = generator.generate_patch(
        issue_type="unsafe_eval",
        source_code=source,
        target_file="approve.py"
    )

    result = validator.validate_patch(
        patch
    )

    passed = (
        result.decision == "APPROVE"
    )

    return {
        "passed": passed,
        "decision": result.decision,
        "risk": result.risk_level
    }


# =========================================================
# TEST 002
# REVIEW
# =========================================================

def test_review():

    generator = PatchGenerationEngine()
    validator = PatchValidationEngine()

    source = """

print("hello")

"""

    patch = generator.generate_patch(
        issue_type="missing_try_except",
        source_code=source,
        target_file="review.py"
    )

    result = validator.validate_patch(
        patch
    )

    passed = (
        result.decision == "REVIEW"
    )

    return {
        "passed": passed,
        "decision": result.decision,
        "risk": result.risk_level
    }


# =========================================================
# TEST 003
# REJECT LOW CONFIDENCE
# =========================================================

def test_reject_low_confidence():

    class FakePatch:

        modified_code = "print('x')"

        confidence_score = 0.20

    validator = PatchValidationEngine()

    result = validator.validate_patch(
        FakePatch()
    )

    passed = (
        result.decision == "REJECT"
    )

    return {
        "passed": passed,
        "decision": result.decision
    }


# =========================================================
# TEST 004
# REJECT GOVERNANCE
# =========================================================

def test_reject_governance():

    class FakePatch:

        modified_code = """

exec(user_input)

"""

        confidence_score = 0.95

    validator = PatchValidationEngine()

    result = validator.validate_patch(
        FakePatch()
    )

    passed = (
        result.decision == "REJECT"
    )

    return {
        "passed": passed,
        "decision": result.decision,
        "reasons": result.reasons
    }


# =========================================================
# TEST 005
# REJECT SYNTAX
# =========================================================

def test_reject_syntax():

    class FakePatch:

        modified_code = """

def broken(

"""

        confidence_score = 0.95

    validator = PatchValidationEngine()

    result = validator.validate_patch(
        FakePatch()
    )

    passed = (
        result.decision == "REJECT"
    )

    return {
        "passed": passed,
        "decision": result.decision,
        "syntax_valid": result.syntax_valid
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_020():

    print("\n" + "=" * 70)
    print("TC_V2_020 PATCH VALIDATION ENGINE")
    print("=" * 70)

    report = {

        "test_case": "TC_V2_020",

        "tests": {

            "approve":
            test_approve(),

            "review":
            test_review(),

            "reject_low_confidence":
            test_reject_low_confidence(),

            "reject_governance":
            test_reject_governance(),

            "reject_syntax":
            test_reject_syntax(),
        }
    }

    total = len(
        report["tests"]
    )

    passed = sum(
        1
        for test in report["tests"].values()
        if test["passed"]
    )

    report["summary"] = {

        "total_tests": total,

        "passed_tests": passed,

        "failed_tests": total - passed,

        "status":
        "PASSED"
        if passed == total
        else "FAILED"
    }

    print("\nSUMMARY")
    print("-" * 70)

    for name, result in report["tests"].items():

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

    run_tc_v2_020()