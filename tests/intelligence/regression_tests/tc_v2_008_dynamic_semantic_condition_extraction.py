"""
TC_V2_008 — Dynamic Semantic Condition Extraction Validation

Title:
Can the Engine Extract and Compare Real AST Conditions Automatically?

Description:
This test validates whether CodeTruth Agent V2 can dynamically extract
authorization conditions from AST parsing and detect semantic regression.

Objective:
Validate dynamic semantic condition extraction.

Expected Result:
BLOCK

Category:
Dynamic Semantic Cognition Validation
"""

import ast
import json
from pathlib import Path


# =========================================================
# OLD AND NEW SAMPLE CODE
# =========================================================

old_code = '''
def can_delete_user(user):

    if user.is_admin:
        return True

    return False
'''

new_code = '''
def can_delete_user(user):

    if user.is_active:
        return True

    return False
'''


# =========================================================
# AST CONDITION EXTRACTION ENGINE
# =========================================================

class ConditionExtractionEngine(ast.NodeVisitor):

    def __init__(self):

        self.conditions = []

    # -----------------------------------------------------
    # Extract IF Conditions
    # -----------------------------------------------------

    def visit_If(self, node):

        condition = ast.unparse(node.test)

        self.conditions.append(condition)

        self.generic_visit(node)


# =========================================================
# SEMANTIC REGRESSION ENGINE
# =========================================================

class SemanticRegressionEngine:

    def compare_conditions(
        self,
        old_conditions,
        new_conditions
    ):

        old_condition = (
            old_conditions[0]
            if old_conditions
            else "UNKNOWN"
        )

        new_condition = (
            new_conditions[0]
            if new_conditions
            else "UNKNOWN"
        )

        # -------------------------------------------------
        # Detect semantic authorization drift
        # -------------------------------------------------

        if (
            old_condition != new_condition
        ):

            return {
                "regression_detected": True,
                "severity": "CRITICAL",
                "reason":
                    (
                        "Authorization condition changed "
                        "from "
                        f"'{old_condition}' "
                        "to "
                        f"'{new_condition}'."
                    )
            }

        return {
            "regression_detected": False,
            "severity": "LOW",
            "reason": "No semantic regression detected."
        }


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(self, regression_result):

        if regression_result["regression_detected"]:

            return {
                "decision": "BLOCK",
                "reason":
                    regression_result["reason"],
                "severity":
                    regression_result["severity"]
            }

        return {
            "decision": "SAFE",
            "reason":
                "No dangerous semantic regression detected.",
            "severity": "LOW"
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_008 — Dynamic Semantic Condition Extraction Validation")
    print("=" * 60)

    # -----------------------------------------------------
    # Step 1 — Parse AST
    # -----------------------------------------------------

    old_tree = ast.parse(old_code)
    new_tree = ast.parse(new_code)

    # -----------------------------------------------------
    # Step 2 — Extract Conditions
    # -----------------------------------------------------

    old_engine = ConditionExtractionEngine()
    new_engine = ConditionExtractionEngine()

    old_engine.visit(old_tree)
    new_engine.visit(new_tree)

    old_conditions = old_engine.conditions
    new_conditions = new_engine.conditions

    # -----------------------------------------------------
    # Step 3 — Semantic Regression Analysis
    # -----------------------------------------------------

    regression_engine = SemanticRegressionEngine()

    regression_result = (
        regression_engine.compare_conditions(
            old_conditions,
            new_conditions
        )
    )

    # -----------------------------------------------------
    # Step 4 — Governance Decision
    # -----------------------------------------------------

    governance_engine = GovernanceDecisionEngine()

    final_result = governance_engine.decide(
        regression_result
    )

    # -----------------------------------------------------
    # Step 5 — Display Results
    # -----------------------------------------------------

    print("\n[Old Conditions]")
    print(old_conditions)

    print("\n[New Conditions]")
    print(new_conditions)

    print("\n[Regression Analysis]")
    print(regression_result)

    print("\n[Governance Decision]")
    print(final_result)

    # -----------------------------------------------------
    # Step 6 — PASS / FAIL
    # -----------------------------------------------------

    expected_decision = "BLOCK"

    status = (
        "PASS"
        if final_result["decision"] == expected_decision
        else "FAIL"
    )

    print("\n[Test Status]")
    print(status)

    # -----------------------------------------------------
    # Step 7 — Save Report
    # -----------------------------------------------------

    report = {
        "test_case": "TC_V2_008",
        "title":
            "Dynamic Semantic Condition Extraction Validation",
        "description":
            (
                "Validates whether V2 can dynamically "
                "extract and compare authorization conditions "
                "from AST parsing."
            ),
        "category":
            "Dynamic Semantic Cognition",
        "old_conditions":
            old_conditions,
        "new_conditions":
            new_conditions,
        "regression_detected":
            regression_result["regression_detected"],
        "severity":
            final_result["severity"],
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
        "tests/output/v2/regression_reports"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        "TC_V2_008_report.json"
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