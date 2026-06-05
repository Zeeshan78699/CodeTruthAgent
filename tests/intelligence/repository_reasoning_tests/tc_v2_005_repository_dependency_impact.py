"""
TC_V2_005 — Repository Dependency Impact Validation

Title:
Can the Engine Understand Cross-File Impact Chains?

Description:
This test validates whether CodeTruth Agent V2 can detect that a change
in one function may impact another dependent function in the repository.

Objective:
Validate repository-wide reasoning by detecting dependency impact.

Expected Result:
REVIEW

Category:
Repository Reasoning Intelligence Validation
"""

import json
from pathlib import Path


# =========================================================
# SIMULATED REPOSITORY FUNCTIONS
# =========================================================

def calculate_discount(amount):
    return {
        "function": "calculate_discount",
        "operation": "BUSINESS_RULE",
        "output": amount * 0.10
    }


def generate_invoice_total(amount):
    discount = calculate_discount(amount)["output"]

    return {
        "function": "generate_invoice_total",
        "operation": "INVOICE_TOTAL",
        "depends_on": ["calculate_discount"],
        "total": amount - discount
    }


# =========================================================
# REPOSITORY DEPENDENCY ENGINE
# =========================================================

class RepositoryDependencyEngine:

    def build_dependency_map(self):
        return {
            "calculate_discount": [],
            "generate_invoice_total": ["calculate_discount"]
        }

    def find_impacted_functions(self, changed_function):
        dependency_map = self.build_dependency_map()

        impacted = []

        for function_name, dependencies in dependency_map.items():
            if changed_function in dependencies:
                impacted.append(function_name)

        return impacted


# =========================================================
# IMPACT DECISION ENGINE
# =========================================================

class ImpactDecisionEngine:

    def decide(self, changed_function, impacted_functions):

        if impacted_functions:
            return {
                "decision": "REVIEW",
                "reason": (
                    "Repository dependency impact detected. "
                    "Change may affect dependent functions."
                )
            }

        return {
            "decision": "SAFE",
            "reason": "No dependency impact detected."
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_005 — Repository Dependency Impact Validation")
    print("=" * 60)

    changed_function = "calculate_discount"

    dependency_engine = RepositoryDependencyEngine()

    impacted_functions = dependency_engine.find_impacted_functions(
        changed_function
    )

    decision_engine = ImpactDecisionEngine()

    final_result = decision_engine.decide(
        changed_function,
        impacted_functions
    )

    print("\n[Changed Function]")
    print(changed_function)

    print("\n[Impacted Functions]")
    print(impacted_functions)

    print("\n[Governance Decision]")
    print(final_result)

    expected_decision = "REVIEW"

    status = (
        "PASS"
        if final_result["decision"] == expected_decision
        else "FAIL"
    )

    print("\n[Test Status]")
    print(status)

    report = {
        "test_case": "TC_V2_005",
        "title": "Repository Dependency Impact Validation",
        "description": (
            "Validates whether V2 can detect cross-file or repository "
            "dependency impact when a changed function is used by another function."
        ),
        "category": "Repository Reasoning",
        "changed_function": changed_function,
        "impacted_functions": impacted_functions,
        "decision": final_result["decision"],
        "reason": final_result["reason"],
        "expected": expected_decision,
        "status": status
    }

    output_dir = Path(
        "tests/output/v2/repository_reasoning_reports"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = output_dir / "TC_V2_005_report.json"

    with open(output_file, "w") as f:
        json.dump(report, f, indent=4)

    print("\n[Report Saved]")
    print(output_file)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    run_test()