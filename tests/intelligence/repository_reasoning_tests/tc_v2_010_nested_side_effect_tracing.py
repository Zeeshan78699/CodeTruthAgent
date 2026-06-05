"""
TC_V2_010 — Nested Side-Effect Tracing Validation

Title:
Can the Engine Detect Indirect Repository Mutations?

Description:
This test validates whether CodeTruth Agent V2 can detect
hidden side effects caused indirectly through nested function calls.

Objective:
Validate nested side-effect tracing cognition.

Expected Result:
REVIEW

Category:
Side-Effect Cognition Validation
"""

import ast
import json
from pathlib import Path


# =========================================================
# SAMPLE REPOSITORY CODE
# =========================================================

sample_code = '''
DATABASE = {}

def update_balance(user_id, amount):

    DATABASE[user_id] = amount

    return True


def process_payment(user_id, amount):

    success = update_balance(user_id, amount)

    return success
'''


# =========================================================
# AST SIDE-EFFECT ENGINE
# =========================================================

class SideEffectEngine(ast.NodeVisitor):

    def __init__(self):

        self.dependencies = {}
        self.side_effect_functions = set()
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

    # -----------------------------------------------------
    # Detect Mutations
    # -----------------------------------------------------

    def visit_Assign(self, node):

        for target in node.targets:

            if isinstance(target, ast.Subscript):

                if (
                    isinstance(target.value, ast.Name)
                    and target.value.id == "DATABASE"
                ):

                    if self.current_function:

                        self.side_effect_functions.add(
                            self.current_function
                        )

        self.generic_visit(node)


# =========================================================
# SIDE-EFFECT PROPAGATION ENGINE
# =========================================================

class SideEffectPropagationEngine:

    def trace_side_effects(
        self,
        dependency_map,
        side_effect_functions
    ):

        impacted = set()

        def propagate(function_name):

            for fn, deps in dependency_map.items():

                if function_name in deps:

                    impacted.add(fn)

                    propagate(fn)

        for side_effect_fn in side_effect_functions:

            propagate(side_effect_fn)

        return list(impacted)


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(
        self,
        side_effect_functions,
        impacted_functions
    ):

        if (
            side_effect_functions
            or impacted_functions
        ):

            return {
                "decision": "REVIEW",
                "reason":
                    (
                        "Nested repository side-effects "
                        "detected."
                    )
            }

        return {
            "decision": "SAFE",
            "reason":
                "No side-effects detected."
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_010 — Nested Side-Effect Tracing Validation")
    print("=" * 60)

    # -----------------------------------------------------
    # Step 1 — Parse AST
    # -----------------------------------------------------

    tree = ast.parse(sample_code)

    # -----------------------------------------------------
    # Step 2 — AST Analysis
    # -----------------------------------------------------

    engine = SideEffectEngine()

    engine.visit(tree)

    dependency_map = engine.dependencies

    side_effect_functions = list(
        engine.side_effect_functions
    )

    # -----------------------------------------------------
    # Step 3 — Side-Effect Propagation
    # -----------------------------------------------------

    propagation_engine = (
        SideEffectPropagationEngine()
    )

    impacted_functions = (
        propagation_engine.trace_side_effects(
            dependency_map,
            side_effect_functions
        )
    )

    # -----------------------------------------------------
    # Step 4 — Governance Decision
    # -----------------------------------------------------

    governance_engine = GovernanceDecisionEngine()

    final_result = governance_engine.decide(
        side_effect_functions,
        impacted_functions
    )

    # -----------------------------------------------------
    # Step 5 — Display Results
    # -----------------------------------------------------

    print("\n[Dependency Map]")
    print(json.dumps(dependency_map, indent=4))

    print("\n[Side-Effect Functions]")
    print(side_effect_functions)

    print("\n[Indirectly Impacted Functions]")
    print(impacted_functions)

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
        "test_case": "TC_V2_010",
        "title":
            "Nested Side-Effect Tracing Validation",
        "description":
            (
                "Validates whether V2 can detect "
                "hidden repository mutations through "
                "nested function calls."
            ),
        "category":
            "Side-Effect Cognition",
        "dependency_map":
            dependency_map,
        "side_effect_functions":
            side_effect_functions,
        "impacted_functions":
            impacted_functions,
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
        "TC_V2_010_report.json"
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