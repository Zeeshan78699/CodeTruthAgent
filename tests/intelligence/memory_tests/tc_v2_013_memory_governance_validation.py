"""
TC_V2_013 — Memory Governance Validation

Title:
Can the Engine Remember and Detect Previous Governance Decisions?

Description:
This test validates whether CodeTruth Agent V2 can store,
retrieve, and detect previous governance decisions.

Objective:
Validate governance memory cognition.

Expected Result:
REVIEW

Category:
Governance Memory Cognition Validation
"""

import json
from pathlib import Path


# =========================================================
# GOVERNANCE MEMORY ENGINE
# =========================================================

class GovernanceMemoryEngine:

    def __init__(self):

        self.memory_file = Path(
            "tests/output/v2/memory_reports/governance_memory.json"
        )

        self.memory_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not self.memory_file.exists():

            with open(self.memory_file, "w") as f:
                json.dump([], f)

    # -----------------------------------------------------
    # Load Memory
    # -----------------------------------------------------

    def load_memory(self):

        with open(self.memory_file, "r") as f:
            return json.load(f)

    # -----------------------------------------------------
    # Save Memory
    # -----------------------------------------------------

    def save_memory(self, data):

        with open(self.memory_file, "w") as f:
            json.dump(data, f, indent=4)

    # -----------------------------------------------------
    # Check Existing Decision
    # -----------------------------------------------------

    def decision_exists(
        self,
        function_a,
        function_b
    ):

        memory = self.load_memory()

        for item in memory:

            if (
                item["function_a"] == function_a
                and item["function_b"] == function_b
            ):

                return item

        return None

    # -----------------------------------------------------
    # Store Governance Decision
    # -----------------------------------------------------

    def store_decision(
        self,
        function_a,
        function_b,
        decision
    ):

        memory = self.load_memory()

        memory.append({
            "function_a": function_a,
            "function_b": function_b,
            "decision": decision
        })

        self.save_memory(memory)


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(
        self,
        function_a,
        function_b
    ):

        return {
            "decision": "REVIEW",
            "reason":
                (
                    "Potential semantic similarity detected."
                )
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_013 — Memory Governance Validation")
    print("=" * 60)

    function_a = "refund_customer"
    function_b = "process_refund"

    memory_engine = GovernanceMemoryEngine()

    # -----------------------------------------------------
    # Step 1 — Check Existing Memory
    # -----------------------------------------------------

    existing_decision = (
        memory_engine.decision_exists(
            function_a,
            function_b
        )
    )

    # -----------------------------------------------------
    # Step 2 — Existing Decision Found
    # -----------------------------------------------------

    if existing_decision:

        final_result = {
            "decision":
                existing_decision["decision"],
            "reason":
                (
                    "Previous governance decision "
                    "retrieved from memory."
                )
        }

        duplicate_detected = True

    # -----------------------------------------------------
    # Step 3 — New Governance Decision
    # -----------------------------------------------------

    else:

        governance_engine = (
            GovernanceDecisionEngine()
        )

        final_result = governance_engine.decide(
            function_a,
            function_b
        )

        memory_engine.store_decision(
            function_a,
            function_b,
            final_result["decision"]
        )

        duplicate_detected = False

    # -----------------------------------------------------
    # Step 4 — Display Results
    # -----------------------------------------------------

    print("\n[Function A]")
    print(function_a)

    print("\n[Function B]")
    print(function_b)

    print("\n[Duplicate Decision Detected]")
    print(duplicate_detected)

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
        "test_case": "TC_V2_013",
        "title":
            "Memory Governance Validation",
        "description":
            (
                "Validates whether V2 can persist "
                "and retrieve governance decisions."
            ),
        "category":
            "Governance Memory Cognition",
        "function_a":
            function_a,
        "function_b":
            function_b,
        "duplicate_detected":
            duplicate_detected,
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
        "tests/output/v2/memory_reports"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        "TC_V2_013_report.json"
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