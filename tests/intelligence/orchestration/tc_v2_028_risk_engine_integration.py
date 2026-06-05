"""
TC_V2_028
RISK ENGINE INTEGRATION

Objective:

Validate:

Patch Type
→ Risk Classification
→ Governance Action

LOW
MEDIUM
HIGH
CRITICAL
"""

from __future__ import annotations

import json
from pathlib import Path

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
    / "risk_engine_integration_reports"
    / "tc_v2_028_report.json"
)


# =========================================================
# TESTS
# =========================================================

def test_low_patch():

    engine = RiskClassificationEngine()

    decision = engine.classify_patch(
        "print_to_logger"
    )

    return {

        "passed":
        decision.risk_level == "LOW"
        and decision.action == "AUTO_APPLY",

        "risk":
        decision.risk_level,

        "action":
        decision.action
    }


def test_medium_patch():

    engine = RiskClassificationEngine()

    decision = engine.classify_patch(
        "missing_try_except"
    )

    return {

        "passed":
        decision.risk_level == "MEDIUM"
        and decision.action == "BATCH_APPROVAL",

        "risk":
        decision.risk_level,

        "action":
        decision.action
    }


def test_high_patch():

    engine = RiskClassificationEngine()

    decision = engine.classify_patch(
        "authentication_change"
    )

    return {

        "passed":
        decision.risk_level == "HIGH"
        and decision.action == "INDIVIDUAL_APPROVAL",

        "risk":
        decision.risk_level,

        "action":
        decision.action
    }


def test_critical_patch():

    engine = RiskClassificationEngine()

    decision = engine.classify_patch(
        "database_change"
    )

    return {

        "passed":
        decision.risk_level == "CRITICAL"
        and decision.action == "FREEZE_PATCH",

        "risk":
        decision.risk_level,

        "action":
        decision.action
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_028():

    print("\n" + "=" * 70)
    print("TC_V2_028 RISK ENGINE INTEGRATION")
    print("=" * 70)

    report = {

        "test_case":
        "TC_V2_028",

        "tests": {

            "low_patch":
            test_low_patch(),

            "medium_patch":
            test_medium_patch(),

            "high_patch":
            test_high_patch(),

            "critical_patch":
            test_critical_patch(),
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

    run_tc_v2_028()