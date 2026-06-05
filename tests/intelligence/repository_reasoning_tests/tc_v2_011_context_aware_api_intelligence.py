"""
TC_V2_011 — Context-Aware API Intelligence Validation

Title:
Can the Engine Understand Framework/API Meaning Dynamically?

Description:
This test validates whether CodeTruth Agent V2 can dynamically
understand API/framework meaning through AST extraction.

Objective:
Validate context-aware API cognition.

Expected Result:
REVIEW

Category:
Context-Aware Repository Cognition Validation
"""

import ast
import json
from pathlib import Path


# =========================================================
# SAMPLE REPOSITORY CODE
# =========================================================

sample_code = '''
import requests
import os

def fetch_customer_data():

    response = requests.get(
        "https://api.example.com/customers"
    )

    return response.json()


def delete_temp_file():

    os.remove("temp.txt")

    return True
'''


# =========================================================
# API INTELLIGENCE ENGINE
# =========================================================

class APIIntelligenceEngine(ast.NodeVisitor):

    def __init__(self):

        self.api_calls = []
        self.classifications = []

    # -----------------------------------------------------
    # Detect API Calls
    # -----------------------------------------------------

    def visit_Call(self, node):

        if isinstance(node.func, ast.Attribute):

            object_name = None

            if isinstance(node.func.value, ast.Name):

                object_name = node.func.value.id

            api_name = node.func.attr

            full_call = (
                f"{object_name}.{api_name}"
            )

            self.api_calls.append(full_call)

            classification = self.classify_api(
                full_call
            )

            self.classifications.append(
                classification
            )

        self.generic_visit(node)

    # -----------------------------------------------------
    # Context-Aware Classification
    # -----------------------------------------------------

    def classify_api(self, full_call):

        api_map = {
            "requests.get":
                "NETWORK_OPERATION",

            "os.remove":
                "DELETE_OPERATION",

            "Path.write_text":
                "FILE_WRITE_OPERATION",

            "sqlite3.connect":
                "DATABASE_OPERATION"
        }

        operation = api_map.get(
            full_call,
            "UNKNOWN_OPERATION"
        )

        return {
            "api_call": full_call,
            "classification": operation
        }


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(self, classifications):

        risky_operations = [
            "DELETE_OPERATION",
            "DATABASE_OPERATION"
        ]

        for item in classifications:

            if (
                item["classification"]
                in risky_operations
            ):

                return {
                    "decision": "REVIEW",
                    "reason":
                        (
                            "Risky repository API "
                            "operation detected."
                        )
                }

        return {
            "decision": "SAFE",
            "reason":
                "No risky API operations detected."
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_011 — Context-Aware API Intelligence Validation")
    print("=" * 60)

    # -----------------------------------------------------
    # Step 1 — Parse AST
    # -----------------------------------------------------

    tree = ast.parse(sample_code)

    # -----------------------------------------------------
    # Step 2 — API Intelligence Analysis
    # -----------------------------------------------------

    engine = APIIntelligenceEngine()

    engine.visit(tree)

    api_calls = engine.api_calls

    classifications = engine.classifications

    # -----------------------------------------------------
    # Step 3 — Governance Decision
    # -----------------------------------------------------

    governance_engine = GovernanceDecisionEngine()

    final_result = governance_engine.decide(
        classifications
    )

    # -----------------------------------------------------
    # Step 4 — Display Results
    # -----------------------------------------------------

    print("\n[Detected API Calls]")
    print(api_calls)

    print("\n[Context Classifications]")
    print(json.dumps(classifications, indent=4))

    print("\n[Governance Decision]")
    print(final_result)

    # -----------------------------------------------------
    # Step 5 — PASS / FAIL
    # -----------------------------------------------------

    expected_decision = "REVIEW"

    status = (
        "PASS"
        if final_result["decision"] == expected_decision
        else "FAIL"
    )

    print("\n[Test Status]")
    print(status)

    # -----------------------------------------------------
    # Step 6 — Save Report
    # -----------------------------------------------------

    report = {
        "test_case": "TC_V2_011",
        "title":
            "Context-Aware API Intelligence Validation",
        "description":
            (
                "Validates whether V2 can dynamically "
                "understand framework/API behavior meaning."
            ),
        "category":
            "Context-Aware Repository Cognition",
        "api_calls":
            api_calls,
        "classifications":
            classifications,
        "decision":
            final_result["decision"],
        "reason":
            final_result["reason"],
        "expected":
            expected_decision,
        "status":
            status
    }

    output_dir = Path(
        "tests/output/v2/repository_reasoning_reports"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        "TC_V2_011_report.json"
    )

    with open(output_file, "w") as f:
        json.dump(report, f, indent=4)

    print("\n[Report Saved]")
    print(output_file)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    run_test()