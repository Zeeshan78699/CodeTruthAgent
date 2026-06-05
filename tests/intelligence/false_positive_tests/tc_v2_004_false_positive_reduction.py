"""
TC_V2_004 — False Positive Reduction Validation

Objective:
Validate that V2 avoids incorrect:

- BLOCK decisions
- REVIEW decisions

for unrelated repository behaviors.

Expected Result:
SAFE

Category:
False Positive Reduction Validation
"""

import json
from pathlib import Path


# =========================================================
# SAMPLE FUNCTIONS UNDER TEST
# =========================================================

def read_config():
    """
    Reads application configuration
    """

    return {
        "operation": "FILE_READ",
        "resource": "config.json"
    }


def send_email():
    """
    Sends notification email
    """

    return {
        "operation": "EMAIL_SEND",
        "recipient": "admin@example.com"
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

        # -------------------------------------------------
        # Semantic similarity patterns
        # -------------------------------------------------

        semantic_groups = [
            ("refund", "refund"),
            ("backup", "restore"),
            ("delete", "remove"),
        ]

        for a, b in semantic_groups:

            if a in name_a and b in name_b:

                return {
                    "relation": "RELATED",
                    "confidence": 0.88
                }

        # -------------------------------------------------
        # No relationship detected
        # -------------------------------------------------

        return {
            "relation": "UNRELATED",
            "confidence": 0.11
        }


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(
        self,
        behavior_a,
        behavior_b,
        semantic_relation
    ):

        # -------------------------------------------------
        # Opposing behaviors
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
        # Similar behavior
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
        # Default SAFE
        # -------------------------------------------------

        return {
            "decision": "SAFE",
            "reason":
                "No relationship or conflict detected"
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_004 — False Positive Reduction Validation")
    print("=" * 60)

    # -----------------------------------------------------
    # Step 1 — Execute Functions
    # -----------------------------------------------------

    result_a = read_config()
    result_b = send_email()

    # -----------------------------------------------------
    # Step 2 — Behavioral Analysis
    # -----------------------------------------------------

    behavioral_engine = BehavioralAnalyzer()

    behavior_a = behavioral_engine.analyze(
        result_a
    )

    behavior_b = behavioral_engine.analyze(
        result_b
    )

    # -----------------------------------------------------
    # Step 3 — Semantic Analysis
    # -----------------------------------------------------

    semantic_engine = SemanticEngine()

    semantic_result = semantic_engine.compare(
        "read_config",
        "send_email"
    )

    # -----------------------------------------------------
    # Step 4 — Governance Decision
    # -----------------------------------------------------

    governance_engine = GovernanceDecisionEngine()

    final_result = governance_engine.decide(
        behavior_a["behavior"],
        behavior_b["behavior"],
        semantic_result["relation"]
    )

    # -----------------------------------------------------
    # Step 5 — Display Results
    # -----------------------------------------------------

    print("\n[Behavior Analysis]")
    print("Function A:", behavior_a)

    print("Function B:", behavior_b)

    print("\n[Semantic Analysis]")
    print(semantic_result)

    print("\n[Governance Decision]")
    print(final_result)

    # -----------------------------------------------------
    # Step 6 — PASS / FAIL
    # -----------------------------------------------------

    expected_decision = "SAFE"

    if (
        final_result["decision"]
        == expected_decision
    ):

        status = "PASS"

    else:
        status = "FAIL"

    print("\n[Test Status]")
    print(status)

    # -----------------------------------------------------
    # Step 7 — Save Report
    # -----------------------------------------------------

    report = {
        "test_case": "TC_V2_004",
        "category":
            "False Positive Reduction",
        "function_a":
            "read_config",
        "function_b":
            "send_email",
        "behavior_a":
            behavior_a["behavior"],
        "behavior_b":
            behavior_b["behavior"],
        "semantic_relation":
            semantic_result["relation"],
        "confidence":
            semantic_result["confidence"],
        "decision":
            final_result["decision"],
        "reason":
            final_result["reason"],
        "status":
            status
    }

    output_dir = Path(
        "tests/output/v2/false_positive_reports"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        output_dir /
        "TC_V2_004_report.json"
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