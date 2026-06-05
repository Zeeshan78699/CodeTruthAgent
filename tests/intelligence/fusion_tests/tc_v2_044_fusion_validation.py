"""
TC_V2_044 - Fusion Engine Validation

Objective:
Validate the FusionEngine combines semantic + behavioral signals
into correct unified decisions.

Approach:
Hand-crafted test cases that probe each fusion rule:
    1. Opposing behaviors -> BLOCK
    2. Both clean, semantically similar -> SAFE
    3. Shared high-impact behavior -> REVIEW minimum
    4. Semantically unrelated, no shared behaviors -> BLOCK
    5. Similar functions, low-risk behaviors -> SAFE
    6. Mixed signals (high semantic, high behavior risk) -> REVIEW
    7. CRITICAL combinations -> BLOCK

Each test feeds the engine raw signals (semantic_score, semantic_decision,
behavior tags, behavior risks) - NOT real functions. This isolates the
fusion logic from upstream engine variations.

Pass criterion:
    fusion_decision matches expected
    fusion_risk_level matches expected

Category:
V2.1 Fusion Engine Validation
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


# =========================================================
# PATH SETUP
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from ai.fusion_engine import FusionEngine


# =========================================================
# OUTPUT PATHS
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "fusion_validation_reports"
)

REPORT_FILE = OUTPUT_DIR / "TC_V2_044_report.json"


# =========================================================
# TEST CASES
# =========================================================

TEST_CASES = [

    # -----------------------------------------------------
    # Category 1: OPPOSING BEHAVIORS (must BLOCK)
    # -----------------------------------------------------
    {
        "category": "OPPOSING",
        "description": "BACKUP vs RECOVERY",
        "semantic_score": 0.55,
        "semantic_decision": "REVIEW",
        "behavior_a_tags": ["BACKUP_OPERATION"],
        "behavior_b_tags": ["RECOVERY_OPERATION"],
        "behavior_a_risk": "MEDIUM",
        "behavior_b_risk": "HIGH",
        "expected_decision": "BLOCK",
        "expected_risk_level": "CRITICAL",
    },
    {
        "category": "OPPOSING",
        "description": "FILE_WRITE vs DELETE",
        "semantic_score": 0.40,
        "semantic_decision": "REVIEW",
        "behavior_a_tags": ["FILE_WRITE"],
        "behavior_b_tags": ["DELETE_OPERATION"],
        "behavior_a_risk": "MEDIUM",
        "behavior_b_risk": "HIGH",
        "expected_decision": "BLOCK",
        "expected_risk_level": "CRITICAL",
    },

    # -----------------------------------------------------
    # Category 2: BOTH CLEAN (no behaviors)
    # -----------------------------------------------------
    {
        "category": "BOTH_CLEAN",
        "description": "Two pure functions, semantically similar",
        "semantic_score": 0.85,
        "semantic_decision": "SAFE",
        "behavior_a_tags": [],
        "behavior_b_tags": [],
        "behavior_a_risk": "LOW",
        "behavior_b_risk": "LOW",
        "expected_decision": "SAFE",
        "expected_risk_level": "LOW",
    },

    # -----------------------------------------------------
    # Category 3: SHARED HIGH-IMPACT (minimum REVIEW)
    # -----------------------------------------------------
    {
        "category": "SHARED_HIGH_IMPACT",
        "description": "Both DELETE_OPERATION",
        "semantic_score": 0.85,
        "semantic_decision": "REVIEW",
        "behavior_a_tags": ["DELETE_OPERATION"],
        "behavior_b_tags": ["DELETE_OPERATION"],
        "behavior_a_risk": "HIGH",
        "behavior_b_risk": "HIGH",
        "expected_decision": "REVIEW",
        "expected_risk_level": "MEDIUM",
    },
    {
        "category": "SHARED_HIGH_IMPACT",
        "description": "Both DATABASE_OPERATION",
        "semantic_score": 0.78,
        "semantic_decision": "REVIEW",
        "behavior_a_tags": ["DATABASE_OPERATION"],
        "behavior_b_tags": ["DATABASE_OPERATION"],
        "behavior_a_risk": "HIGH",
        "behavior_b_risk": "HIGH",
        "expected_decision": "REVIEW",
        "expected_risk_level": "MEDIUM",
    },
    {
        "category": "SHARED_HIGH_IMPACT",
        "description": "Both AUTH_OPERATION",
        "semantic_score": 0.70,
        "semantic_decision": "REVIEW",
        "behavior_a_tags": ["AUTH_OPERATION"],
        "behavior_b_tags": ["AUTH_OPERATION"],
        "behavior_a_risk": "HIGH",
        "behavior_b_risk": "HIGH",
        "expected_decision": "REVIEW",
        "expected_risk_level": "MEDIUM",
    },

    # -----------------------------------------------------
    # Category 4: SEMANTICALLY UNRELATED + NO SHARED TAGS
    # -----------------------------------------------------
    {
        "category": "UNRELATED",
        "description": "Send email vs calculate invoice (unrelated)",
        "semantic_score": 0.13,
        "semantic_decision": "BLOCK",
        "behavior_a_tags": ["NETWORK_OPERATION"],
        "behavior_b_tags": ["STATE_MUTATION"],
        "behavior_a_risk": "MEDIUM",
        "behavior_b_risk": "MEDIUM",
        "expected_decision": "BLOCK",
        "expected_risk_level": "CRITICAL",
    },
    {
        "category": "UNRELATED",
        "description": "Backup vs authenticate (totally different)",
        "semantic_score": 0.10,
        "semantic_decision": "BLOCK",
        "behavior_a_tags": ["BACKUP_OPERATION"],
        "behavior_b_tags": ["AUTH_OPERATION"],
        "behavior_a_risk": "MEDIUM",
        "behavior_b_risk": "HIGH",
        "expected_decision": "BLOCK",
        "expected_risk_level": "CRITICAL",
    },

    # -----------------------------------------------------
    # Category 5: SIMILAR LOW-RISK (SAFE candidate)
    # -----------------------------------------------------
    {
        "category": "SIMILAR_LOW_RISK",
        "description": "Both FILE_READ, semantically similar",
        "semantic_score": 0.88,
        "semantic_decision": "SAFE",
        "behavior_a_tags": ["FILE_READ"],
        "behavior_b_tags": ["FILE_READ"],
        "behavior_a_risk": "MEDIUM",
        "behavior_b_risk": "MEDIUM",
        "expected_decision": "REVIEW",
        "expected_risk_level": "MEDIUM",
    },

    # -----------------------------------------------------
    # Category 6: MIXED SIGNALS
    # -----------------------------------------------------
    {
        "category": "MIXED",
        "description": "High semantic + DATABASE -> REVIEW",
        "semantic_score": 0.90,
        "semantic_decision": "REVIEW",
        "behavior_a_tags": ["DATABASE_OPERATION", "STATE_MUTATION"],
        "behavior_b_tags": ["DATABASE_OPERATION"],
        "behavior_a_risk": "HIGH",
        "behavior_b_risk": "HIGH",
        "expected_decision": "REVIEW",
        "expected_risk_level": "MEDIUM",
    },

    # -----------------------------------------------------
    # Category 7: CRITICAL (multiple high-impact, low sem)
    # -----------------------------------------------------
    {
        "category": "CRITICAL",
        "description": "Low semantic + DELETE + AUTH = critical",
        "semantic_score": 0.25,
        "semantic_decision": "REVIEW",
        "behavior_a_tags": ["DELETE_OPERATION", "DATABASE_OPERATION"],
        "behavior_b_tags": ["AUTH_OPERATION"],
        "behavior_a_risk": "HIGH",
        "behavior_b_risk": "HIGH",
        "expected_decision": "BLOCK",
        "expected_risk_level": "CRITICAL",
    },

    # -----------------------------------------------------
    # Category 8: SHARED LOW-IMPACT
    # -----------------------------------------------------
    {
        "category": "SHARED_LOW_IMPACT",
        "description": "Both STATE_MUTATION only",
        "semantic_score": 0.80,
        "semantic_decision": "REVIEW",
        "behavior_a_tags": ["STATE_MUTATION"],
        "behavior_b_tags": ["STATE_MUTATION"],
        "behavior_a_risk": "MEDIUM",
        "behavior_b_risk": "MEDIUM",
        "expected_decision": "REVIEW",
        "expected_risk_level": "MEDIUM",
    },
]


# =========================================================
# EVALUATION
# =========================================================

def evaluate(case, engine):

    result = engine.fuse(
        semantic_score=case["semantic_score"],
        semantic_decision=case["semantic_decision"],
        behavior_a_tags=case["behavior_a_tags"],
        behavior_b_tags=case["behavior_b_tags"],
        behavior_a_risk=case["behavior_a_risk"],
        behavior_b_risk=case["behavior_b_risk"],
    )

    decision_match = (
        result.fusion_decision == case["expected_decision"]
    )

    risk_match = (
        result.fusion_risk_level == case["expected_risk_level"]
    )

    status = "PASS" if decision_match and risk_match else "FAIL"

    return {
        "category": case["category"],
        "description": case["description"],
        "input": {
            "semantic_score": case["semantic_score"],
            "semantic_decision": case["semantic_decision"],
            "behavior_a_tags": case["behavior_a_tags"],
            "behavior_b_tags": case["behavior_b_tags"],
            "behavior_a_risk": case["behavior_a_risk"],
            "behavior_b_risk": case["behavior_b_risk"],
        },
        "expected_decision": case["expected_decision"],
        "expected_risk_level": case["expected_risk_level"],
        "actual_decision": result.fusion_decision,
        "actual_risk_level": result.fusion_risk_level,
        "fusion_risk_score": result.fusion_risk_score,
        "shared_behavior_tags": result.shared_behavior_tags,
        "opposing_behavior_detected": result.opposing_behavior_detected,
        "reasoning": result.reasoning,
        "decision_match": decision_match,
        "risk_match": risk_match,
        "status": status,
    }


def run_test():

    print("=" * 90)
    print("TC_V2_044 - FUSION ENGINE VALIDATION")
    print("=" * 90)

    print("\nLoading FusionEngine...")
    engine = FusionEngine()
    print("FusionEngine loaded.")

    results = []
    pass_count = 0
    decision_pass = 0
    risk_pass = 0

    for index, case in enumerate(TEST_CASES, start=1):
        print("\n" + "-" * 90)
        print(
            f"[{index}/{len(TEST_CASES)}] {case['category']} - "
            f"{case['description']}"
        )

        result = evaluate(case, engine)
        results.append(result)

        if result["status"] == "PASS":
            pass_count += 1
        if result["decision_match"]:
            decision_pass += 1
        if result["risk_match"]:
            risk_pass += 1

        print(f"  Expected decision : {result['expected_decision']}")
        print(f"  Actual decision   : {result['actual_decision']}")
        print(f"  Expected risk     : {result['expected_risk_level']}")
        print(f"  Actual risk       : {result['actual_risk_level']}")
        print(f"  Fusion score      : {result['fusion_risk_score']}")
        print(f"  Decision match    : {result['decision_match']}")
        print(f"  Risk match        : {result['risk_match']}")
        print(f"  Status            : {result['status']}")

    total = len(TEST_CASES)
    overall_status = "PASS" if pass_count == total else "FAIL"

    report = {
        "test_case": "TC_V2_044",
        "category": "Fusion Engine Validation",
        "tests_executed": total,
        "tests_passed": pass_count,
        "decision_pass_count": decision_pass,
        "risk_pass_count": risk_pass,
        "decision_accuracy_percent": round(
            100 * decision_pass / total, 2
        ),
        "risk_accuracy_percent": round(
            100 * risk_pass / total, 2
        ),
        "overall_accuracy_percent": round(
            100 * pass_count / total, 2
        ),
        "overall_status": overall_status,
        "results": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    # Summary
    print("\n" + "=" * 90)
    print(f"Tests Executed     : {total}")
    print(f"Tests Passed       : {pass_count}")
    print(f"Decision Accuracy  : {round(100 * decision_pass / total, 2)}%")
    print(f"Risk Accuracy      : {round(100 * risk_pass / total, 2)}%")
    print(f"Overall Status     : {overall_status}")
    print(f"Report Saved       : {REPORT_FILE}")
    print("=" * 90)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    run_test()
