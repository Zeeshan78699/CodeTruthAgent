"""
TC_V2_030
TEST EXECUTION ENGINE

Objective:

Validate:

TestExecutionEngine
→ Execute Test Command
→ Capture Results
→ PASS / FAIL

This test does NOT modify repository files.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.test_execution_engine import (
    TestExecutionEngine
)


# =========================================================
# REPORT PATH
# =========================================================

REPORT_OUTPUT = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "test_execution_reports"
    / "tc_v2_030_report.json"
)


# =========================================================
# TEST SUCCESS
# =========================================================

def test_success_execution():

    engine = TestExecutionEngine()

    result = engine.execute_tests(
        command="python -c \"print('PASS')\""
    )

    return {

        "passed":
        result.success,

        "success":
        result.success,

        "execution_time":
        result.execution_time_seconds,

        "errors":
        result.errors
    }


# =========================================================
# TEST FAILURE
# =========================================================

def test_failure_execution():

    engine = TestExecutionEngine()

    result = engine.execute_tests(
        command="python -c \"import sys; sys.exit(1)\""
    )

    return {

        "passed":
        not result.success,

        "success":
        result.success,

        "execution_time":
        result.execution_time_seconds,

        "errors":
        result.errors
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_030():

    print("\n" + "=" * 70)
    print("TC_V2_030 TEST EXECUTION ENGINE")
    print("=" * 70)

    report = {

        "test_case":
        "TC_V2_030",

        "tests": {

            "success_execution":
            test_success_execution(),

            "failure_execution":
            test_failure_execution(),
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

    run_tc_v2_030()