"""
TC_V2_007 — Dynamic AST Dependency Discovery Validation

Title:
Can the Engine Automatically Discover Real Function Dependencies from Code?

Description:
This test validates whether CodeTruth Agent V2 can dynamically discover
function dependencies using AST parsing instead of hardcoded dependency maps.

Objective:
Validate dynamic repository dependency cognition.

Expected Result:
REVIEW

Category:
Dynamic Repository Cognition Validation
"""

import ast
import json
from pathlib import Path


# =========================================================
# SAMPLE PYTHON CODE
# =========================================================

sample_code = '''
def calculate_discount(amount):
    return amount * 0.10


def generate_invoice_total(amount):
    discount = calculate_discount(amount)
    return amount - discount
'''


# =========================================================
# AST DEPENDENCY ENGINE
# =========================================================

class ASTDependencyEngine(ast.NodeVisitor):

    def __init__(self):

        self.dependencies = {}
        self.current_function = None

    # -----------------------------------------------------
    # Function Definition
    # -----------------------------------------------------

    def visit_FunctionDef(self, node):

        self.current_function = node.name

        self.dependencies[self.current_function] = []

        self.generic_visit(node)

    # -----------------------------------------------------
    # Function Calls
    # -----------------------------------------------------

    def visit_Call(self, node):

        if (
            isinstance(node.func, ast.Name)
            and self.current_function
        ):

            called_function = node.func.id

            self.dependencies[
                self.current_function
            ].append(called_function)

        self.generic_visit(node)


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(self, dependency_map):

        impacted_functions = []

        for function_name, dependencies in dependency_map.items():

            if dependencies:
                impacted_functions.append(function_name)

        if impacted_functions:

            return {
                "decision": "REVIEW",
                "reason":
                    "Dynamic repository dependencies discovered."
            }

        return {
            "decision": "SAFE",
            "reason":
                "No repository dependencies detected."
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_007 — Dynamic AST Dependency Discovery Validation")
    print("=" * 60)

    # -----------------------------------------------------
    # Step 1 — Parse AST
    # -----------------------------------------------------

    tree = ast.parse(sample_code)

    # -----------------------------------------------------
    # Step 2 — Dynamic Dependency Discovery
    # -----------------------------------------------------

    dependency_engine = ASTDependencyEngine()

    dependency_engine.visit(tree)

    dependency_map = dependency_engine.dependencies

    # -----------------------------------------------------
    # Step 3 — Governance Decision
    # -----------------------------------------------------

    governance_engine = GovernanceDecisionEngine()

    final_result = governance_engine.decide(
        dependency_map
    )

    # -----------------------------------------------------
    # Step 4 — Display Results
    # -----------------------------------------------------

    print("\n[Dynamic Dependency Map]")
    print(json.dumps(dependency_map, indent=4))

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
        "test_case": "TC_V2_007",
        "title":
            "Dynamic AST Dependency Discovery Validation",
        "description":
            (
                "Validates whether V2 can dynamically discover "
                "repository dependencies using AST parsing."
            ),
        "category":
            "Dynamic Repository Cognition",
        "dependency_map":
            dependency_map,
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
        "TC_V2_007_report.json"
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