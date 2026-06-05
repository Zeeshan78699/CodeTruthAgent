"""
TC_V2_029
PATCH VALIDATION + RISK INTEGRATION

Objective:

Validate:

Patch Validation
→ Risk Classification
→ Governance Action

Enterprise Flow:

Validation
↓
Risk Classification
↓
LOW / MEDIUM / HIGH / CRITICAL
↓
Approval Action
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.patch_generation_engine import (
    PatchGenerationEngine
)

from ai.patch_validation_engine import (
    PatchValidationEngine
)

from ai.risk_classification_engine import (
    RiskClassificationEngine
)


# =========================================================
# REPORT PATH
# =========================================================

REPORT_OUTPUT = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "validation_risk_reports"
    / "tc_v2_029_report.json"
)


# =========================================================
# HELPERS
# =========================================================

def build_result(
    validation,
    risk_decision
):

    return {

        "validation_decision":
        validation.decision,

        "risk_level":
        risk_decision.risk_level,

        "action":
        risk_decision.action
    }


# =========================================================
# TEST LOW
# =========================================================

def test_low_flow():

    generator = PatchGenerationEngine()

    validator = PatchValidationEngine()

    risk_engine = RiskClassificationEngine()

    source_code = """

print("hello")

"""

    patch = generator.generate_patch(
        issue_type="print_to_logger",
        source_code=source_code,
        target_file="low.py"
    )

    validation = validator.validate_patch(
        patch
    )

    risk_decision = (
        risk_engine.classify_patch(
            "print_to_logger"
        )
    )

    passed = (

        risk_decision.risk_level
        == "LOW"

        and

        risk_decision.action
        == "AUTO_APPLY"
    )

    result = build_result(
        validation,
        risk_decision
    )

    result["passed"] = passed

    return result


# =========================================================
# TEST MEDIUM
# =========================================================

def test_medium_flow():

    generator = PatchGenerationEngine()

    validator = PatchValidationEngine()

    risk_engine = RiskClassificationEngine()

    source_code = """

print("hello")

"""

    patch = generator.generate_patch(
        issue_type="missing_try_except",
        source_code=source_code,
        target_file="medium.py"
    )

    validation = validator.validate_patch(
        patch
    )

    risk_decision = (
        risk_engine.classify_patch(
            "missing_try_except"
        )
    )

    passed = (

        risk_decision.risk_level
        == "MEDIUM"

        and

        risk_decision.action
        == "BATCH_APPROVAL"
    )

    result = build_result(
        validation,
        risk_decision
    )

    result["passed"] = passed

    return result


# =========================================================
# TEST HIGH
# =========================================================

def test_high_flow():

    risk_engine = RiskClassificationEngine()

    risk_decision = (
        risk_engine.classify_patch(
            "authentication_change"
        )
    )

    passed = (

        risk_decision.risk_level
        == "HIGH"

        and

        risk_decision.action
        == "INDIVIDUAL_APPROVAL"
    )

    return {

        "passed": passed,

        "risk_level":
        risk_decision.risk_level,

        "action":
        risk_decision.action
    }


# =========================================================
# TEST CRITICAL
# =========================================================

def test_critical_flow():

    risk_engine = RiskClassificationEngine()

    risk_decision = (
        risk_engine.classify_patch(
            "database_change"
        )
    )

    passed = (

        risk_decision.risk_level
        == "CRITICAL"

        and

        risk_decision.action
        == "FREEZE_PATCH"
    )

    return {

        "passed": passed,

        "risk_level":
        risk_decision.risk_level,

        "action":
        risk_decision.action
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_029():

    print("\n" + "=" * 70)
    print("TC_V2_029 PATCH VALIDATION + RISK INTEGRATION")
    print("=" * 70)

    report = {

        "test_case":
        "TC_V2_029",

        "tests": {

            "low_flow":
            test_low_flow(),

            "medium_flow":
            test_medium_flow(),

            "high_flow":
            test_high_flow(),

            "critical_flow":
            test_critical_flow(),
        }
    }

    total_tests = len(
        report["tests"]
    )

    passed_tests = sum(
        1
        for test in report["tests"].values()
        if test["passed"]
    )

    report["summary"] = {

        "total_tests":
        total_tests,

        "passed_tests":
        passed_tests,

        "failed_tests":
        total_tests - passed_tests,

        "status":
        "PASSED"
        if passed_tests == total_tests
        else "FAILED"
    }

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

    print("\nRESULTS")
    print("-" * 70)

    for name, result in report["tests"].items():

        print(
            f"{name}: "
            f"{'PASS' if result['passed'] else 'FAIL'}"
        )

    print(
        f"\nOVERALL STATUS: "
        f"{report['summary']['status']}"
    )

    print(
        f"\n[Report Saved] "
        f"{REPORT_OUTPUT}"
    )

    return report


if __name__ == "__main__":

    run_tc_v2_029()