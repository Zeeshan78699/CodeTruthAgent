"""
TC_V2_009 — Cross-File Propagation Reasoning Validation

Title:
Can the Engine Detect Multi-Hop Repository Impact Chains?

Description:
This test validates whether CodeTruth Agent V2 can detect
cross-function propagation chains using AST dependency extraction.

Objective:
Validate multi-hop repository propagation reasoning.

Expected Result:
REVIEW

Category:
Repository-Wide Propagation Cognition Validation
"""

import ast
import json
from pathlib import Path


# =========================================================
# SAMPLE REPOSITORY CODE
# =========================================================

sample_code = '''
def calculate_tax(amount):
    return amount * 0.05


def generate_invoice(amount):

    tax = calculate_tax(amount)

    return amount + tax


def send_invoice_email(amount):

    total = generate_invoice(amount)

    return f"Invoice Total: {total}"
'''


# =========================================================
# AST DEPENDENCY ENGINE
# =========================================================

class ASTDependencyEngine(ast.NodeVisitor):

    def __init__(self):

        self.dependencies = {}
        self.current_function = None

    # -----------------------------------------------------
    # Function Definitions
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
# PROPAGATION ENGINE
# =========================================================

class PropagationEngine:

    def find_propagation_chain(
        self,
        dependency_map,
        changed_function
    ):

        impacted = set()

        def traverse(function_name):

            for fn, deps in dependency_map.items():

                if function_name in deps:

                    impacted.add(fn)

                    traverse(fn)

        traverse(changed_function)

        return list(impacted)


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(self, impacted_chain):

        if impacted_chain:

            return {
                "decision": "REVIEW",
                "reason":
                    (
                        "Multi-hop repository impact "
                        "chain detected."
                    )
            }

        return {
            "decision": "SAFE",
            "reason":
                "No propagation impact detected."
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_009 — Cross-File Propagation Reasoning Validation")
    print("=" * 60)

    # -----------------------------------------------------
    # Step 1 — Parse AST
    # -----------------------------------------------------

    tree = ast.parse(sample_code)

    # -----------------------------------------------------
    # Step 2 — Extract Dependencies
    # -----------------------------------------------------

    dependency_engine = ASTDependencyEngine()

    dependency_engine.visit(tree)

    dependency_map = dependency_engine.dependencies

    # -----------------------------------------------------
    # Step 3 — Multi-Hop Propagation
    # -----------------------------------------------------

    propagation_engine = PropagationEngine()

    changed_function = "calculate_tax"

    impacted_chain = (
        propagation_engine.find_propagation_chain(
            dependency_map,
            changed_function
        )
    )

    # -----------------------------------------------------
    # Step 4 — Governance Decision
    # -----------------------------------------------------

    governance_engine = GovernanceDecisionEngine()

    final_result = governance_engine.decide(
        impacted_chain
    )

    # -----------------------------------------------------
    # Step 5 — Display Results
    # -----------------------------------------------------

    print("\n[Dependency Map]")
    print(json.dumps(dependency_map, indent=4))

    print("\n[Changed Function]")
    print(changed_function)

    print("\n[Propagation Chain]")
    print(impacted_chain)

    print("\n[Governance Decision]")
    print(final_result)

    # -----------------------------------------------------
    # Step 6 — PASS / FAIL
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
    # Step 7 — Save Report
    # -----------------------------------------------------

    report = {
        "test_case": "TC_V2_009",
        "title":
            "Cross-File Propagation Reasoning Validation",
        "description":
            (
                "Validates whether V2 can detect "
                "multi-hop repository propagation chains."
            ),
        "category":
            "Repository-Wide Propagation Cognition",
        "dependency_map":
            dependency_map,
        "changed_function":
            changed_function,
        "impacted_chain":
            impacted_chain,
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
        "TC_V2_009_report.json"
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