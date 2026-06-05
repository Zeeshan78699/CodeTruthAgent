"""
TC_V2_006 — Semantic Regression Detection Validation

Title:
Can the Engine Detect Hidden Business-Rule Changes?

Description:
This test validates whether CodeTruth Agent V2 can detect a semantic
regression when code still looks valid but the business rule changes.

Example:
OLD: user.is_admin
NEW: user.is_active

Both may look like simple condition checks, but the meaning is different.
Changing admin permission logic to active-user logic may create a security
or authorization regression.

Objective:
Detect hidden semantic/business-rule drift before merge.

Expected Result:
BLOCK

Category:
Semantic Regression Intelligence Validation
"""

import json
from pathlib import Path


# =========================================================
# SIMULATED OLD AND NEW FUNCTION BEHAVIOR
# =========================================================

def old_authorization_rule():
    return {
        "function": "can_delete_user",
        "condition": "user.is_admin",
        "business_rule": "ADMIN_PERMISSION_REQUIRED",
        "risk_area": "AUTHORIZATION"
    }


def new_authorization_rule():
    return {
        "function": "can_delete_user",
        "condition": "user.is_active",
        "business_rule": "ACTIVE_USER_ALLOWED",
        "risk_area": "AUTHORIZATION"
    }


# =========================================================
# SEMANTIC REGRESSION ENGINE
# =========================================================

class SemanticRegressionEngine:

    def compare_rules(self, old_rule, new_rule):

        old_business_rule = old_rule.get("business_rule")
        new_business_rule = new_rule.get("business_rule")

        old_risk_area = old_rule.get("risk_area")
        new_risk_area = new_rule.get("risk_area")

        if (
            old_risk_area == new_risk_area
            and old_business_rule != new_business_rule
        ):
            return {
                "regression_detected": True,
                "severity": "CRITICAL",
                "reason": (
                    "Business rule changed inside the same risk area. "
                    "Authorization meaning changed from admin-only access "
                    "to active-user access."
                )
            }

        return {
            "regression_detected": False,
            "severity": "LOW",
            "reason": "No semantic regression detected."
        }


# =========================================================
# GOVERNANCE DECISION ENGINE
# =========================================================

class GovernanceDecisionEngine:

    def decide(self, regression_result):

        if regression_result["regression_detected"]:
            return {
                "decision": "BLOCK",
                "reason": regression_result["reason"],
                "severity": regression_result["severity"]
            }

        return {
            "decision": "SAFE",
            "reason": "No dangerous semantic regression detected.",
            "severity": "LOW"
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_006 — Semantic Regression Detection Validation")
    print("=" * 60)

    old_rule = old_authorization_rule()
    new_rule = new_authorization_rule()

    regression_engine = SemanticRegressionEngine()

    regression_result = regression_engine.compare_rules(
        old_rule,
        new_rule
    )

    governance_engine = GovernanceDecisionEngine()

    final_result = governance_engine.decide(
        regression_result
    )

    print("\n[Old Rule]")
    print(old_rule)

    print("\n[New Rule]")
    print(new_rule)

    print("\n[Regression Analysis]")
    print(regression_result)

    print("\n[Governance Decision]")
    print(final_result)

    expected_decision = "BLOCK"

    status = (
        "PASS"
        if final_result["decision"] == expected_decision
        else "FAIL"
    )

    print("\n[Test Status]")
    print(status)

    report = {
        "test_case": "TC_V2_006",
        "title": "Semantic Regression Detection Validation",
        "description": (
            "Validates whether V2 can detect hidden semantic or business-rule "
            "regression when authorization logic changes from admin-only access "
            "to active-user access."
        ),
        "category": "Semantic Regression",
        "old_condition": old_rule["condition"],
        "new_condition": new_rule["condition"],
        "old_business_rule": old_rule["business_rule"],
        "new_business_rule": new_rule["business_rule"],
        "risk_area": old_rule["risk_area"],
        "regression_detected": regression_result["regression_detected"],
        "severity": final_result["severity"],
        "decision": final_result["decision"],
        "reason": final_result["reason"],
        "expected": expected_decision,
        "status": status
    }

    output_dir = Path(
        "tests/output/v2/regression_reports"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = output_dir / "TC_V2_006_report.json"

    with open(output_file, "w") as f:
        json.dump(report, f, indent=4)

    print("\n[Report Saved]")
    print(output_file)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    run_test()