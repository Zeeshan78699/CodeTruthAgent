"""
TC_V2_042C — Semantic Tuning Validation

Objective:
Validate semantic intelligence performance
on previously identified weak semantic areas.

Focus Areas:

1. Authentication Semantics
2. Recovery Semantics
3. Control BLOCK Protection

Purpose:

Measure whether semantic tuning
improves REVIEW classification
without reducing BLOCK accuracy.

Category:
V2.1 Semantic Tuning Validation
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.semantic_decision_engine import (
    SemanticDecisionEngine
)


# =========================================================
# TUNING TEST SET
# =========================================================

TEST_CASES = [

    # -----------------------------------------------------
    # AUTHENTICATION SEMANTICS
    # -----------------------------------------------------

    {
        "category": "AUTH_TUNING",
        "function_a": "validate_user_token",
        "function_b": "authenticate_session",
        "expected": "REVIEW"
    },

    {
        "category": "AUTH_TUNING",
        "function_a": "validate_login",
        "function_b": "authenticate_user",
        "expected": "REVIEW"
    },

    {
        "category": "AUTH_TUNING",
        "function_a": "verify_credentials",
        "function_b": "authenticate_account",
        "expected": "REVIEW"
    },

    # -----------------------------------------------------
    # RECOVERY SEMANTICS
    # -----------------------------------------------------

    {
        "category": "RECOVERY_TUNING",
        "function_a": "rollback_transaction",
        "function_b": "restore_backup",
        "expected": "REVIEW"
    },

    {
        "category": "RECOVERY_TUNING",
        "function_a": "rollback_database",
        "function_b": "restore_database",
        "expected": "REVIEW"
    },

    {
        "category": "RECOVERY_TUNING",
        "function_a": "recover_state",
        "function_b": "rollback_state",
        "expected": "REVIEW"
    },

    # -----------------------------------------------------
    # CONTROL BLOCK CASES
    # -----------------------------------------------------

    {
        "category": "CONTROL_BLOCK",
        "function_a": "send_email",
        "function_b": "calculate_invoice",
        "expected": "BLOCK"
    },

    {
        "category": "CONTROL_BLOCK",
        "function_a": "load_memory",
        "function_b": "delete_database",
        "expected": "BLOCK"
    },

    {
        "category": "CONTROL_BLOCK",
        "function_a": "generate_report",
        "function_b": "rollback_transaction",
        "expected": "BLOCK"
    }
]


# =========================================================
# MAIN TEST
# =========================================================

def run_test():

    print("=" * 90)
    print("TC_V2_042C — SEMANTIC TUNING VALIDATION")
    print("=" * 90)

    print("\nLoading SemanticDecisionEngine...")

    semantic_engine = SemanticDecisionEngine()

    print("SemanticDecisionEngine loaded successfully.")

    results = []

    passed = 0

    auth_total = 0
    auth_correct = 0

    recovery_total = 0
    recovery_correct = 0

    block_total = 0
    block_correct = 0

    semantic_gaps = []

    # =====================================================
    # EXECUTE TESTS
    # =====================================================

    for index, test in enumerate(TEST_CASES, start=1):

        function_a = test["function_a"]
        function_b = test["function_b"]

        expected = test["expected"]
        category = test["category"]

        print("\n" + "-" * 90)

        print(
            f"[{index}/{len(TEST_CASES)}] "
            f"{function_a} <-> {function_b}"
        )

        try:

            result = semantic_engine.analyze_change(
                function_a=function_a,
                function_b=function_b
            )

            actual = result["decision"]

            status = (
                "PASS"
                if actual == expected
                else "FAIL"
            )

            if status == "PASS":
                passed += 1
            else:
                semantic_gaps.append(
                    {
                        "function_a": function_a,
                        "function_b": function_b,
                        "expected": expected,
                        "actual": actual
                    }
                )

            # =============================================
            # CATEGORY METRICS
            # =============================================

            if category == "AUTH_TUNING":

                auth_total += 1

                if actual == expected:
                    auth_correct += 1

            elif category == "RECOVERY_TUNING":

                recovery_total += 1

                if actual == expected:
                    recovery_correct += 1

            elif category == "CONTROL_BLOCK":

                block_total += 1

                if actual == expected:
                    block_correct += 1

            results.append({

                "category":
                category,

                "function_a":
                function_a,

                "function_b":
                function_b,

                "expected":
                expected,

                "actual":
                actual,

                "status":
                status,

                "lexical_score":
                result["lexical_score"],

                "embedding_score":
                result["embedding_score"],

                "confidence":
                result["confidence"],

                "risk_level":
                result["risk_level"],

                "reasoning":
                result["reasoning"]
            })

            print(
                f"Expected : {expected}"
            )

            print(
                f"Actual   : {actual}"
            )

            print(
                f"Status   : {status}"
            )

        except Exception as ex:

            print(
                f"ERROR: {str(ex)}"
            )

            results.append({

                "category":
                category,

                "function_a":
                function_a,

                "function_b":
                function_b,

                "status":
                "ERROR",

                "error":
                str(ex)
            })

    # =====================================================
    # METRICS
    # =====================================================

    total_tests = len(TEST_CASES)

    accuracy = round(
        (passed / total_tests) * 100,
        2
    )

    auth_accuracy = round(
        (auth_correct / auth_total) * 100,
        2
    ) if auth_total else 0

    recovery_accuracy = round(
        (recovery_correct / recovery_total) * 100,
        2
    ) if recovery_total else 0

    block_accuracy = round(
        (block_correct / block_total) * 100,
        2
    ) if block_total else 0

    # =====================================================
    # REPORT
    # =====================================================

    report = {

        "test_case":
        "TC_V2_042C",

        "category":
        "Semantic Tuning Validation",

        "total_tests":
        total_tests,

        "passed":
        passed,

        "failed":
        total_tests - passed,

        "accuracy":
        accuracy,

        "authentication_accuracy":
        auth_accuracy,

        "recovery_accuracy":
        recovery_accuracy,

        "block_accuracy":
        block_accuracy,

        "semantic_gaps":
        semantic_gaps,

        "results":
        results
    }

    # =====================================================
    # SAVE REPORT
    # =====================================================

    output_dir = Path(
        "tests/output/v2/semantic_validation_reports"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        "TC_V2_042C_report.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )

    # =====================================================
    # SUMMARY
    # =====================================================

    print("\n" + "=" * 90)

    print(f"Total Tests             : {total_tests}")
    print(f"Passed                  : {passed}")
    print(f"Failed                  : {total_tests - passed}")

    print(f"Overall Accuracy        : {accuracy}%")

    print(
        f"Authentication Accuracy : "
        f"{auth_accuracy}%"
    )

    print(
        f"Recovery Accuracy       : "
        f"{recovery_accuracy}%"
    )

    print(
        f"BLOCK Accuracy          : "
        f"{block_accuracy}%"
    )

    print(
        f"\nReport Saved: "
        f"{output_file}"
    )

    print("=" * 90)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    run_test()