"""
TC_V2_027
RISK CLASSIFICATION ENGINE

Objective:

Validate enterprise risk routing:

LOW
→ AUTO_APPLY

MEDIUM
→ BATCH_APPROVAL

HIGH
→ INDIVIDUAL_APPROVAL

CRITICAL
→ FREEZE_PATCH
"""

from __future__ import annotations

import json
from pathlib import Path


# =========================================================
# REPORT PATH
# =========================================================

REPORT_OUTPUT = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "risk_classification_reports"
    / "tc_v2_027_report.json"
)


# =========================================================
# RISK ENGINE
# =========================================================

class RiskClassificationEngine:

    def classify_risk(
        self,
        score: int
    ):

        if score <= 29:

            return {
                "risk": "LOW",
                "action": "AUTO_APPLY"
            }

        if score <= 59:

            return {
                "risk": "MEDIUM",
                "action": "BATCH_APPROVAL"
            }

        if score <= 79:

            return {
                "risk": "HIGH",
                "action": "INDIVIDUAL_APPROVAL"
            }

        return {
            "risk": "CRITICAL",
            "action": "FREEZE_PATCH"
        }


# =========================================================
# TESTS
# =========================================================

def test_low_risk():

    engine = RiskClassificationEngine()

    result = engine.classify_risk(10)

    return {

        "passed":
        result["risk"] == "LOW"
        and result["action"] == "AUTO_APPLY",

        "risk":
        result["risk"],

        "action":
        result["action"]
    }


def test_medium_risk():

    engine = RiskClassificationEngine()

    result = engine.classify_risk(45)

    return {

        "passed":
        result["risk"] == "MEDIUM"
        and result["action"] == "BATCH_APPROVAL",

        "risk":
        result["risk"],

        "action":
        result["action"]
    }


def test_high_risk():

    engine = RiskClassificationEngine()

    result = engine.classify_risk(70)

    return {

        "passed":
        result["risk"] == "HIGH"
        and result["action"] == "INDIVIDUAL_APPROVAL",

        "risk":
        result["risk"],

        "action":
        result["action"]
    }


def test_critical_risk():

    engine = RiskClassificationEngine()

    result = engine.classify_risk(95)

    return {

        "passed":
        result["risk"] == "CRITICAL"
        and result["action"] == "FREEZE_PATCH",

        "risk":
        result["risk"],

        "action":
        result["action"]
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_027():

    print("\n" + "=" * 70)
    print("TC_V2_027 RISK CLASSIFICATION ENGINE")
    print("=" * 70)

    report = {

        "test_case":
        "TC_V2_027",

        "tests": {

            "low_risk":
            test_low_risk(),

            "medium_risk":
            test_medium_risk(),

            "high_risk":
            test_high_risk(),

            "critical_risk":
            test_critical_risk(),
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

    run_tc_v2_027()