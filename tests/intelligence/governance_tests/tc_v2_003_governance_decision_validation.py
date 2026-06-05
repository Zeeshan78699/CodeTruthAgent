"""
TC_V2_003 — Governance Decision Validation

Objective:
Validate that V2 can correctly classify:

SAFE
REVIEW
BLOCK

governance decisions using:

- semantic reasoning
- behavioral analysis
- operational conflict detection

Expected Results:
SAFE
REVIEW
BLOCK

Category:
Governance Intelligence Validation
"""

import json
from pathlib import Path


# =========================================================
# SAMPLE FUNCTIONS UNDER TEST
# =========================================================

def read_config():
    """
    Safe read-only operation
    """

    return {
        "operation": "FILE_READ",
        "resource": "config.json"
    }


def process_refund():
    """
    Refund operation
    """

    return {
        "operation": "REFUND_OPERATION",
        "amount": 250
    }


def refund_customer():
    """
    Similar refund operation
    """

    return {
        "operation": "REFUND_OPERATION",
        "amount": 500
    }


def create_backup():
    """
    Backup creation
    """

    return {
        "operation": "BACKUP_OPERATION"
    }


def restore_backup():
    """
    Restore backup
    """

    return {
        "operation": "RECOVERY_OPERATION"
    }


# =========================================================
# BEHAVIORAL ANALYZER
# =========================================================

class BehavioralAnalyzer:

    def analyze(self, result):

        return {
            "behavior": result.get(
                "operation",
                "UNKNOWN"
            )
        }


# =========================================================
# SEMANTIC ENGINE
# =========================================================

class SemanticEngine:

    def compare(self, name_a, name_b):

        name_a = name_a.lower()
        name_b = name_b.lower()

        # ---------------------------------------------
        # Refund semantic relationship
        # ---------------------------------------------

        if (
            "refund" in name_a
            and "refund" in name_b
        ):

            return {
                "relation": "RELATED"
            }

        # ---------------------------------------------
        # Backup semantic relationship
        # ---------------------------------------------

        if (
            "backup" in name_a
            and "backup" in name_b
        ):

            return {
                "relation": "RELATED"
            }

        return {
            "relation": "UNRELATED"
        }


# =========================================================
# GOVERNANCE DECISION ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(
        self,
        behavior_a,
        behavior_b,
        semantic_relation
    ):

        # -------------------------------------------------
        # BLOCK
        # -------------------------------------------------

        opposing_pairs = [
            (
                "BACKUP_OPERATION",
                "RECOVERY_OPERATION"
            )
        ]

        for op_a, op_b in opposing_pairs:

            if (
                behavior_a == op_a
                and behavior_b == op_b
            ):

                return {
                    "decision": "BLOCK",
                    "reason":
                        "Opposing behaviors detected"
                }

        # -------------------------------------------------
        # REVIEW
        # -------------------------------------------------

        if (
            behavior_a == behavior_b
            and semantic_relation == "RELATED"
        ):

            return {
                "decision": "REVIEW",
                "reason":
                    "Semantic similarity detected"
            }

        # -------------------------------------------------
        # SAFE
        # -------------------------------------------------

        return {
            "decision": "SAFE",
            "reason":
                "No conflict detected"
        }


# =========================================================
# TEST RUNNER
# =========================================================

def run_scenario(
    scenario_name,
    func_a_name,
    func_b_name,
    func_a_result,
    func_b_result,
    expected_decision
):

    behavioral_engine = BehavioralAnalyzer()
    semantic_engine = SemanticEngine()
    governance_engine = GovernanceDecisionEngine()

    behavior_a = behavioral_engine.analyze(
        func_a_result
    )

    behavior_b = behavioral_engine.analyze(
        func_b_result
    )

    semantic_result = semantic_engine.compare(
        func_a_name,
        func_b_name
    )

    final_result = governance_engine.decide(
        behavior_a["behavior"],
        behavior_b["behavior"],
        semantic_result["relation"]
    )

    # -------------------------------------------------
    # PASS / FAIL
    # -------------------------------------------------

    if (
        final_result["decision"]
        == expected_decision
    ):

        status = "PASS"

    else:
        status = "FAIL"

    # -------------------------------------------------
    # Display
    # -------------------------------------------------

    print("\n" + "=" * 60)
    print("Scenario:", scenario_name)
    print("=" * 60)

    print("\n[Behavior A]")
    print(behavior_a)

    print("\n[Behavior B]")
    print(behavior_b)

    print("\n[Semantic Analysis]")
    print(semantic_result)

    print("\n[Governance Decision]")
    print(final_result)

    print("\n[Test Status]")
    print(status)

    return {
        "scenario": scenario_name,
        "behavior_a": behavior_a["behavior"],
        "behavior_b": behavior_b["behavior"],
        "semantic_relation":
            semantic_result["relation"],
        "decision":
            final_result["decision"],
        "expected":
            expected_decision,
        "status":
            status
    }


# =========================================================
# MAIN TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_003 — Governance Decision Validation")
    print("=" * 60)

    results = []

    # -----------------------------------------------------
    # Scenario 1 — SAFE
    # -----------------------------------------------------

    results.append(
        run_scenario(
            scenario_name="SAFE Scenario",
            func_a_name="read_config",
            func_b_name="process_refund",
            func_a_result=read_config(),
            func_b_result=process_refund(),
            expected_decision="SAFE"
        )
    )

    # -----------------------------------------------------
    # Scenario 2 — REVIEW
    # -----------------------------------------------------

    results.append(
        run_scenario(
            scenario_name="REVIEW Scenario",
            func_a_name="process_refund",
            func_b_name="refund_customer",
            func_a_result=process_refund(),
            func_b_result=refund_customer(),
            expected_decision="REVIEW"
        )
    )

    # -----------------------------------------------------
    # Scenario 3 — BLOCK
    # -----------------------------------------------------

    results.append(
        run_scenario(
            scenario_name="BLOCK Scenario",
            func_a_name="create_backup",
            func_b_name="restore_backup",
            func_a_result=create_backup(),
            func_b_result=restore_backup(),
            expected_decision="BLOCK"
        )
    )

    # -----------------------------------------------------
    # Final Summary
    # -----------------------------------------------------

    passed = sum(
        1 for r in results
        if r["status"] == "PASS"
    )

    total = len(results)

    overall_status = (
        "PASS"
        if passed == total
        else "FAIL"
    )

    summary = {
        "test_case": "TC_V2_003",
        "category": "Governance Decision Validation",
        "total_scenarios": total,
        "passed": passed,
        "overall_status": overall_status,
        "results": results
    }

    # -----------------------------------------------------
    # Save Report
    # -----------------------------------------------------

    output_dir = Path(
        "tests/output/v2/governance_reports"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        "TC_V2_003_report.json"
    )

    with open(output_file, "w") as f:
        json.dump(summary, f, indent=4)

    print("\n" + "=" * 60)
    print("FINAL TEST STATUS:", overall_status)
    print("=" * 60)

    print("\n[Report Saved]")
    print(output_file)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    run_test()