"""
TC_V2_042D — Real Function Semantic Validation

Objective:
Validate SemanticDecisionEngine using
real function implementations rather
than function names only.

Validates:

1. Lexical Intelligence
2. Embedding Intelligence
3. Purpose Analysis
4. Side Effect Detection
5. Decision Generation

Category:
V2.1 Real Function Semantic Validation
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.semantic_decision_engine import (
    SemanticDecisionEngine
)


# =====================================================
# REAL FUNCTION TEST CASES
# =====================================================

TEST_CASES = [

    {
        "category": "MEMORY",

        "function_a": "save_memory_record",

        "function_b": "store_memory_record",

        "code_a": """
def save_memory_record(record):
    memory_store.write(record)
""",

        "code_b": """
def store_memory_record(record):
    memory_store.write(record)
""",

        "docstring_a":
        "Save memory record to storage",

        "docstring_b":
        "Store memory record to storage",

        "expected":
        "REVIEW"
    },

    {
        "category": "RECOVERY",

        "function_a": "rollback_transaction",

        "function_b": "restore_backup",

        "code_a": """
def rollback_transaction():
    database.rollback()
""",

        "code_b": """
def restore_backup():
    backup.restore()
""",

        "docstring_a":
        "Rollback failed transaction",

        "docstring_b":
        "Restore backup after failure",

        "expected":
        "REVIEW"
    },

    {
        "category": "AUTH",

        "function_a": "validate_login",

        "function_b": "authenticate_user",

        "code_a": """
def validate_login(user):
    token.verify(user)
""",

        "code_b": """
def authenticate_user(user):
    auth.authenticate(user)
""",

        "docstring_a":
        "Validate user login",

        "docstring_b":
        "Authenticate user account",

        "expected":
        "REVIEW"
    },

    {
        "category": "UNRELATED",

        "function_a": "send_email",

        "function_b": "calculate_invoice",

        "code_a": """
def send_email():
    smtp.send()
""",

        "code_b": """
def calculate_invoice(amount, tax):
    return amount * tax
""",

        "docstring_a":
        "Send notification email",

        "docstring_b":
        "Calculate invoice total",

        "expected":
        "BLOCK"
    },

    {
        "category": "RECOVERY",

        "function_a": "restore_database",

        "function_b": "rollback_database",

        "code_a": """
def restore_database():
    db.restore()
""",

        "code_b": """
def rollback_database():
    db.rollback()
""",

        "docstring_a":
        "Restore database state",

        "docstring_b":
        "Rollback database transaction",

        "expected":
        "REVIEW"
    }
]


# =====================================================
# MAIN TEST
# =====================================================

def run_test():

    print("=" * 90)
    print("TC_V2_042D — REAL FUNCTION SEMANTIC VALIDATION")
    print("=" * 90)

    print("\nLoading SemanticDecisionEngine...")

    semantic_engine = SemanticDecisionEngine()

    print("SemanticDecisionEngine loaded successfully.")

    results = []

    passed = 0

    for index, test in enumerate(TEST_CASES, start=1):

        print("\n" + "-" * 90)

        print(
            f"[{index}/{len(TEST_CASES)}] "
            f"{test['function_a']} "
            f"<-> "
            f"{test['function_b']}"
        )

        try:

            result = semantic_engine.analyze_change(

                function_a=
                test["function_a"],

                function_b=
                test["function_b"],

                code_a=
                test["code_a"],

                code_b=
                test["code_b"],

                docstring_a=
                test["docstring_a"],

                docstring_b=
                test["docstring_b"]
            )

            actual = result["decision"]

            status = (
                "PASS"
                if actual == test["expected"]
                else "FAIL"
            )

            if status == "PASS":
                passed += 1

            results.append({

                "category":
                test["category"],

                "function_a":
                test["function_a"],

                "function_b":
                test["function_b"],

                "expected":
                test["expected"],

                "actual":
                actual,

                "status":
                status,

                "lexical_score":
                result["lexical_score"],

                "embedding_score":
                result["embedding_score"],

                "purpose_domain_match":
                result["purpose_domain_match"],

                "side_effects_detected":
                result["side_effects_detected"],

                "confidence":
                result["confidence"],

                "risk_level":
                result["risk_level"],

                "reasoning":
                result["reasoning"]
            })

            print(
                f"Expected : {test['expected']}"
            )

            print(
                f"Actual   : {actual}"
            )

            print(
                f"SideEffects : "
                f"{result['side_effects_detected']}"
            )

            print(
                f"Status   : {status}"
            )

        except Exception as ex:

            print(f"ERROR: {str(ex)}")

            results.append({

                "function_a":
                test["function_a"],

                "function_b":
                test["function_b"],

                "status":
                "ERROR",

                "error":
                str(ex)
            })

    # =================================================
    # SUMMARY
    # =================================================

    total_tests = len(TEST_CASES)

    accuracy = round(
        (passed / total_tests) * 100,
        2
    )

    report = {

        "test_case":
        "TC_V2_042D",

        "category":
        "Real Function Semantic Validation",

        "total_tests":
        total_tests,

        "passed":
        passed,

        "failed":
        total_tests - passed,

        "accuracy":
        accuracy,

        "results":
        results
    }

    output_dir = Path(
        "tests/output/v2/semantic_validation_reports"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        "TC_V2_042D_report.json"
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

    print("\n" + "=" * 90)

    print(
        f"Accuracy : {accuracy}%"
    )

    print(
        f"Passed   : {passed}/{total_tests}"
    )

    print(
        f"Report   : {output_file}"
    )

    print("=" * 90)


if __name__ == "__main__":

    run_test()