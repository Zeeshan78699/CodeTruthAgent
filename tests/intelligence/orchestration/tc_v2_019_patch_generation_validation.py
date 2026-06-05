"""
TC_V2_019
PATCH GENERATION VALIDATION

Objective:
Validate PatchGenerationEngine behavior.

Validation Areas:
- unsafe_eval patch
- unsafe_exec patch
- print_to_logger patch
- missing_try_except patch
- unsupported patch handling
- syntax validation
- confidence scoring
- diff generation
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.patch_generation_engine import (
    PatchGenerationEngine
)


# =========================================================
# REPORT LOCATION
# =========================================================

REPORT_OUTPUT = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "patch_generation_reports"
    / "tc_v2_019_report.json"
)


# =========================================================
# HELPERS
# =========================================================

def print_header(title: str):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def save_report(report_data):

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
            report_data,
            file,
            indent=4
        )

    print(
        f"\n[Report Saved] {REPORT_OUTPUT}"
    )


# =========================================================
# TEST 001
# UNSAFE EVAL
# =========================================================

def test_unsafe_eval(engine):

    source_code = """
def run_user_code(user_input):

    result = eval(user_input)

    return result
"""

    patch = engine.generate_patch(
        issue_type="unsafe_eval",
        source_code=source_code,
        target_file="demo_eval.py"
    )

    passed = (
        patch.syntax_valid
        and "safe_eval(" in patch.modified_code
        and patch.confidence_score == 0.95
    )

    return {
        "passed": passed,
        "confidence_score": patch.confidence_score,
        "syntax_valid": patch.syntax_valid,
        "generation_type": patch.generation_type,
        "diff_lines": len(patch.diff_preview)
    }


# =========================================================
# TEST 002
# UNSAFE EXEC
# =========================================================

def test_unsafe_exec(engine):

    source_code = """
def execute_code(user_code):

    exec(user_code)
"""

    patch = engine.generate_patch(
        issue_type="unsafe_exec",
        source_code=source_code,
        target_file="demo_exec.py"
    )

    passed = (
        patch.syntax_valid
        and "safe_exec(" in patch.modified_code
        and patch.confidence_score == 0.95
    )

    return {
        "passed": passed,
        "confidence_score": patch.confidence_score,
        "syntax_valid": patch.syntax_valid,
        "generation_type": patch.generation_type,
        "diff_lines": len(patch.diff_preview)
    }


# =========================================================
# TEST 003
# PRINT TO LOGGER
# =========================================================

def test_print_to_logger(engine):

    source_code = """
def hello():

    print("hello")
"""

    patch = engine.generate_patch(
        issue_type="print_to_logger",
        source_code=source_code,
        target_file="demo_logger.py"
    )

    passed = (
        patch.syntax_valid
        and "logging.info" in patch.modified_code
        and patch.confidence_score == 0.90
    )

    return {
        "passed": passed,
        "confidence_score": patch.confidence_score,
        "syntax_valid": patch.syntax_valid,
        "generation_type": patch.generation_type,
        "diff_lines": len(patch.diff_preview)
    }


# =========================================================
# TEST 004
# TRY EXCEPT
# =========================================================

def test_missing_try_except(engine):

    source_code = """
value = 1 / number
"""

    patch = engine.generate_patch(
        issue_type="missing_try_except",
        source_code=source_code,
        target_file="demo_try.py"
    )

    passed = (
        patch.syntax_valid
        and "try:" in patch.modified_code
        and "except Exception as error:" in patch.modified_code
        and patch.confidence_score == 0.60
    )

    return {
        "passed": passed,
        "confidence_score": patch.confidence_score,
        "syntax_valid": patch.syntax_valid,
        "generation_type": patch.generation_type,
        "diff_lines": len(patch.diff_preview)
    }


# =========================================================
# TEST 005
# UNSUPPORTED PATCH
# =========================================================

def test_unsupported_patch(engine):

    source_code = """
print("unsupported")
"""

    patch = engine.generate_patch(
        issue_type="unknown_patch",
        source_code=source_code,
        target_file="demo_unknown.py"
    )

    passed = (
        patch.generation_type == "FAILED_PATCH"
        and patch.confidence_score == 0.0
    )

    return {
        "passed": passed,
        "confidence_score": patch.confidence_score,
        "generation_type": patch.generation_type,
        "risk_level": patch.risk_level
    }


# =========================================================
# MAIN
# =========================================================

def run_tc_v2_019():

    print_header(
        "TC_V2_019 - PATCH GENERATION VALIDATION"
    )

    engine = PatchGenerationEngine()

    results = {

        "test_case":
        "TC_V2_019",

        "tests": {

            "unsafe_eval":
            test_unsafe_eval(engine),

            "unsafe_exec":
            test_unsafe_exec(engine),

            "print_to_logger":
            test_print_to_logger(engine),

            "missing_try_except":
            test_missing_try_except(engine),

            "unsupported_patch":
            test_unsupported_patch(engine),
        }
    }

    total_tests = len(
        results["tests"]
    )

    passed_tests = sum(
        1
        for test in results["tests"].values()
        if test["passed"]
    )

    results["summary"] = {

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

    print("\nSUMMARY")
    print("-" * 70)

    for name, result in results["tests"].items():

        print(
            f"{name}: "
            f"{'PASS' if result['passed'] else 'FAIL'}"
        )

    print("\nOVERALL STATUS:")
    print(
        results["summary"]["status"]
    )

    save_report(results)

    return results


# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    run_tc_v2_019()