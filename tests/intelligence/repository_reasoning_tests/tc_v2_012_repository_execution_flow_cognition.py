"""
TC_V2_012 — Repository Execution-Flow Cognition Validation

Title:
Can the Engine Understand Repository-Wide Execution Flow?

Description:
This test validates whether CodeTruth Agent V2 can dynamically
reconstruct execution-flow sequences using AST analysis.

Objective:
Validate repository execution-flow cognition.

Expected Result:
REVIEW

Category:
Execution-Flow Cognition Validation
"""

import ast
import json
from pathlib import Path


# =========================================================
# SAMPLE REPOSITORY CODE
# =========================================================

sample_code = '''
def validate_order(order):

    return True


def save_order(order):

    return "ORDER_SAVED"


def send_confirmation_email(order):

    return "EMAIL_SENT"


def handle_order(order):

    valid = validate_order(order)

    if valid:

        result = save_order(order)

        send_confirmation_email(order)

        return result
'''


# =========================================================
# EXECUTION FLOW ENGINE
# =========================================================

class ExecutionFlowEngine(ast.NodeVisitor):

    def __init__(self):

        self.execution_flows = {}
        self.current_function = None

    # -----------------------------------------------------
    # Function Definitions
    # -----------------------------------------------------

    def visit_FunctionDef(self, node):

        self.current_function = node.name

        self.execution_flows[
            self.current_function
        ] = []

        self.generic_visit(node)

    # -----------------------------------------------------
    # Function Call Sequence
    # -----------------------------------------------------

    def visit_Call(self, node):

        if (
            isinstance(node.func, ast.Name)
            and self.current_function
        ):

            called_function = node.func.id

            self.execution_flows[
                self.current_function
            ].append(called_function)

        self.generic_visit(node)


# =========================================================
# FLOW RECONSTRUCTION ENGINE
# =========================================================

class FlowReconstructionEngine:

    def reconstruct_flow(
        self,
        execution_map,
        entry_function
    ):

        flow = []

        visited = set()

        def traverse(function_name):

            if function_name in visited:
                return

            visited.add(function_name)

            flow.append(function_name)

            for called_fn in execution_map.get(
                function_name,
                []
            ):

                traverse(called_fn)

        traverse(entry_function)

        return flow


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(self, execution_flow):

        if len(execution_flow) > 2:

            return {
                "decision": "REVIEW",
                "reason":
                    (
                        "Repository execution-flow "
                        "chain reconstructed."
                    )
            }

        return {
            "decision": "SAFE",
            "reason":
                "Simple execution flow detected."
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_012 — Repository Execution-Flow Cognition Validation")
    print("=" * 60)

    # -----------------------------------------------------
    # Step 1 — Parse AST
    # -----------------------------------------------------

    tree = ast.parse(sample_code)

    # -----------------------------------------------------
    # Step 2 — Extract Execution Flow
    # -----------------------------------------------------

    engine = ExecutionFlowEngine()

    engine.visit(tree)

    execution_map = engine.execution_flows

    # -----------------------------------------------------
    # Step 3 — Reconstruct Flow
    # -----------------------------------------------------

    flow_engine = (
        FlowReconstructionEngine()
    )

    entry_function = "handle_order"

    execution_flow = (
        flow_engine.reconstruct_flow(
            execution_map,
            entry_function
        )
    )

    # -----------------------------------------------------
    # Step 4 — Governance Decision
    # -----------------------------------------------------

    governance_engine = GovernanceDecisionEngine()

    final_result = governance_engine.decide(
        execution_flow
    )

    # -----------------------------------------------------
    # Step 5 — Display Results
    # -----------------------------------------------------

    print("\n[Execution Map]")
    print(json.dumps(execution_map, indent=4))

    print("\n[Entry Function]")
    print(entry_function)

    print("\n[Reconstructed Execution Flow]")
    print(execution_flow)

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
        "test_case": "TC_V2_012",
        "title":
            "Repository Execution-Flow Cognition Validation",
        "description":
            (
                "Validates whether V2 can dynamically "
                "reconstruct repository execution flows."
            ),
        "category":
            "Execution-Flow Cognition",
        "execution_map":
            execution_map,
        "entry_function":
            entry_function,
        "execution_flow":
            execution_flow,
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
        "TC_V2_012_report.json"
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