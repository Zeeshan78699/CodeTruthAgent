"""
TC_V2_045 - Real Engine Integration Validation

Objective:
Chain the three V2.1 engines on REAL Python code:
    SemanticDecisionEngine -> BehavioralSignatureEngine -> FusionEngine

Unlike TC_V2_042 (semantic only), TC_V2_043 (behavioral only), and
TC_V2_044 (fusion with synthetic inputs), this test validates that
the three engines work together when chained on actual code, not
synthetic signals.

Pipeline per test case:
    1. Build a real Python fixture file
    2. SemanticDecisionEngine.analyze_change(func_a, func_b, code_a, code_b)
       -> semantic_score, semantic_decision
    3. BehavioralSignatureEngine.analyze_file(fixture_file)
       -> behavioral signatures for func_a and func_b
    4. FusionEngine.fuse(semantic + behavioral)
       -> fusion_decision, fusion_risk_level

Honest caveats:
    - Test fixtures are still hand-crafted (not real open-source code)
    - This validates the CHAINING, not real-world precision
    - Real open-source repo integration is a separate test (V2.1 final step)

Pass criterion:
    fusion_decision matches expected category

Category:
V2.1 Real Engine Integration Validation
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# =========================================================
# PATH SETUP
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# ENGINE IMPORTS
# =========================================================

from ai.semantic_decision_engine import SemanticDecisionEngine
from ai.behavioral_signature_engine import BehavioralSignatureEngine
from ai.fusion_engine import FusionEngine


# =========================================================
# OUTPUT PATHS
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "integration_validation_reports"
)

FIXTURE_DIR = OUTPUT_DIR / "fixtures"

REPORT_FILE = OUTPUT_DIR / "TC_V2_045_report.json"


# =========================================================
# FIXTURE FILE - REAL CODE FOR ALL TEST CASES
# =========================================================
# A single fixture file containing all functions used across
# the 6 test cases. This is real Python with real behaviors.

FIXTURE_FILE_NAME = "tc_v2_045_integration_fixture.py"

FIXTURE_CONTENT = '''"""
TC_V2_045 integration fixture.
Contains real Python functions exercising different behavior categories.
"""

import os
import shutil


# -----------------------------------------------------
# Backup / Recovery pair (OPPOSING)
# -----------------------------------------------------

def create_backup(source_path, backup_path):
    """Copy a file to backup location."""
    shutil.copy2(source_path, backup_path)
    return True


def restore_backup(backup_path, target_path):
    """Restore a file from backup."""
    shutil.copy2(backup_path, target_path)
    os.remove(backup_path)
    return True


# -----------------------------------------------------
# Save / Store pair (SIMILAR)
# -----------------------------------------------------

def save_user_data(user_id, data):
    """Write user data to disk."""
    with open(f"users/{user_id}.json", "w") as f:
        f.write(data)
    return True


def store_user_data(user_id, data):
    """Persist user data to disk."""
    with open(f"users/{user_id}.json", "w") as f:
        f.write(data)
    return True


# -----------------------------------------------------
# Delete / Cleanup pair (SHARED HIGH IMPACT)
# -----------------------------------------------------

def delete_temp_file(path):
    """Remove a temporary file."""
    os.remove(path)
    return True


def cleanup_temp_file(path):
    """Clean up temporary file."""
    os.remove(path)
    return True


# -----------------------------------------------------
# Pure functions (BOTH CLEAN)
# -----------------------------------------------------

def calculate_sum(values):
    """Sum a list of numbers."""
    total = 0
    for value in values:
        total = total + value
    return total


def add_numbers(numbers):
    """Add up a list of numbers."""
    result = 0
    for number in numbers:
        result = result + number
    return result


# -----------------------------------------------------
# Unrelated functions (BLOCK case)
# -----------------------------------------------------

def send_email_notification(recipient, subject, body):
    """Send a notification email."""
    import requests
    requests.request(
        "POST",
        "https://api.email.example.com/send",
        json={"to": recipient, "subject": subject, "body": body},
    )
    return True


def calculate_invoice_total(items, tax_rate):
    """Compute invoice total with tax."""
    subtotal = 0
    for item in items:
        subtotal = subtotal + item["price"]
    total = subtotal * (1 + tax_rate)
    return total


# -----------------------------------------------------
# Auth domain pair (SAME DOMAIN, DIFFERENT NAMES)
# -----------------------------------------------------

def authenticate_user(username, password):
    """Verify user credentials and return auth token."""
    token = authenticate(username, password)
    return token


def validate_login(username, password):
    """Validate login credentials."""
    token = authenticate(username, password)
    return token


def authenticate(user, pwd):
    """Internal auth helper."""
    return "fake_token_xyz"
'''


# =========================================================
# TEST CASES
# =========================================================
# Each case names two functions in the fixture file plus the
# expected fusion decision.

TEST_CASES = [

    {
        "category": "OPPOSING",
        "description": "create_backup vs restore_backup (opposing)",
        "func_a": "create_backup",
        "func_b": "restore_backup",
        "expected_decision": "BLOCK",
        "rationale": "BACKUP_OPERATION vs RECOVERY_OPERATION = opposing",
    },

    {
        "category": "SIMILAR_HIGH_IMPACT",
        "description": "save_user_data vs store_user_data (similar)",
        "func_a": "save_user_data",
        "func_b": "store_user_data",
        "expected_decision": "REVIEW",
        "rationale": (
            "Both FILE_WRITE - shared high-impact behavior, "
            "high semantic similarity"
        ),
    },

    {
        "category": "SHARED_HIGH_IMPACT",
        "description": "delete_temp_file vs cleanup_temp_file",
        "func_a": "delete_temp_file",
        "func_b": "cleanup_temp_file",
        "expected_decision": "REVIEW",
        "rationale": (
            "Both DELETE_OPERATION - shared HIGH-impact behavior, "
            "minimum REVIEW required"
        ),
    },

    {
        "category": "BOTH_CLEAN",
        "description": "calculate_sum vs add_numbers (pure functions)",
        "func_a": "calculate_sum",
        "func_b": "add_numbers",
        "expected_decision": "SAFE",
        "rationale": (
            "No tracked behaviors, semantically similar pure functions"
        ),
    },

    {
        "category": "UNRELATED",
        "description": "send_email_notification vs calculate_invoice_total",
        "func_a": "send_email_notification",
        "func_b": "calculate_invoice_total",
        "expected_decision": "BLOCK",
        "rationale": (
            "Semantically unrelated, no shared behaviors"
        ),
    },

    {
        "category": "AUTH_DOMAIN",
        "description": "authenticate_user vs validate_login (auth pair)",
        "func_a": "authenticate_user",
        "func_b": "validate_login",
        "expected_decision": "REVIEW",
        "rationale": (
            "Both AUTH_OPERATION - shared HIGH-impact behavior, "
            "minimum REVIEW required"
        ),
    },
]


# =========================================================
# AST HELPER: EXTRACT FUNCTION CODE BODY
# =========================================================

def extract_function_code(file_path: Path, function_name: str) -> str:
    """
    Extract the source code of a named function from a Python file.
    Returns the function's source text (def + body).
    """

    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                return ast.get_source_segment(source, node) or ""

    return ""


# =========================================================
# HELPER: FIND BEHAVIORAL SIGNATURE BY NAME
# =========================================================

def find_signature(signatures, function_name):
    for sig in signatures:
        if sig.function_name == function_name:
            return sig
    return None


# =========================================================
# PIPELINE EXECUTION FOR ONE TEST CASE
# =========================================================

def run_pipeline(
    case: Dict,
    fixture_path: Path,
    semantic_engine: SemanticDecisionEngine,
    behavioral_engine: BehavioralSignatureEngine,
    fusion_engine: FusionEngine,
    behavioral_signatures,
) -> Dict:
    """
    Run the full V2.1 pipeline on one test case:
        Semantic -> Behavioral -> Fusion
    Return the result dict.
    """

    func_a = case["func_a"]
    func_b = case["func_b"]

    # -----------------------------------------------------
    # Step 1: Extract code bodies from the fixture file
    # -----------------------------------------------------

    code_a = extract_function_code(fixture_path, func_a)
    code_b = extract_function_code(fixture_path, func_b)

    if not code_a or not code_b:
        return {
            "category": case["category"],
            "description": case["description"],
            "func_a": func_a,
            "func_b": func_b,
            "expected_decision": case["expected_decision"],
            "actual_decision": None,
            "error": (
                f"Could not extract code for "
                f"{func_a if not code_a else func_b}"
            ),
            "status": "ERROR",
        }

    # -----------------------------------------------------
    # Step 2: Semantic engine
    # -----------------------------------------------------

    semantic_result = semantic_engine.analyze_change(
        function_a=func_a,
        function_b=func_b,
        code_a=code_a,
        code_b=code_b,
    )

    semantic_score = semantic_result["embedding_score"]
    semantic_decision = semantic_result["decision"]

    # -----------------------------------------------------
    # Step 3: Behavioral engine - get signatures for both
    # -----------------------------------------------------

    sig_a = find_signature(behavioral_signatures, func_a)
    sig_b = find_signature(behavioral_signatures, func_b)

    if sig_a is None or sig_b is None:
        return {
            "category": case["category"],
            "description": case["description"],
            "func_a": func_a,
            "func_b": func_b,
            "expected_decision": case["expected_decision"],
            "actual_decision": None,
            "error": (
                f"Behavioral signature missing for "
                f"{func_a if sig_a is None else func_b}"
            ),
            "status": "ERROR",
        }

    # -----------------------------------------------------
    # Step 4: Fusion engine
    # -----------------------------------------------------

    fusion_result = fusion_engine.fuse(
        semantic_score=semantic_score,
        semantic_decision=semantic_decision,
        behavior_a_tags=sig_a.behavioral_tags,
        behavior_b_tags=sig_b.behavioral_tags,
        behavior_a_risk=sig_a.risk_level,
        behavior_b_risk=sig_b.risk_level,
    )

    # -----------------------------------------------------
    # Step 5: Evaluate
    # -----------------------------------------------------

    decision_match = (
        fusion_result.fusion_decision == case["expected_decision"]
    )

    status = "PASS" if decision_match else "FAIL"

    return {
        "category": case["category"],
        "description": case["description"],
        "func_a": func_a,
        "func_b": func_b,

        # Semantic engine output
        "semantic_score": semantic_score,
        "semantic_decision": semantic_decision,
        "semantic_lexical_score": semantic_result["lexical_score"],
        "semantic_confidence": semantic_result["confidence"],
        "semantic_reasoning": semantic_result["reasoning"],

        # Behavioral engine output
        "behavior_a_tags": sig_a.behavioral_tags,
        "behavior_b_tags": sig_b.behavioral_tags,
        "behavior_a_risk": sig_a.risk_level,
        "behavior_b_risk": sig_b.risk_level,

        # Fusion engine output
        "fusion_decision": fusion_result.fusion_decision,
        "fusion_risk_score": fusion_result.fusion_risk_score,
        "fusion_risk_level": fusion_result.fusion_risk_level,
        "opposing_detected": fusion_result.opposing_behavior_detected,
        "shared_behavior_tags": fusion_result.shared_behavior_tags,
        "fusion_reasoning": fusion_result.reasoning,

        # Verdict
        "expected_decision": case["expected_decision"],
        "actual_decision": fusion_result.fusion_decision,
        "decision_match": decision_match,
        "rationale": case["rationale"],
        "status": status,
    }


# =========================================================
# MAIN TEST RUNNER
# =========================================================

def run_test():

    print("=" * 90)
    print("TC_V2_045 - REAL ENGINE INTEGRATION VALIDATION")
    print("=" * 90)

    # -----------------------------------------------------
    # Build fixture file
    # -----------------------------------------------------

    print("\nBuilding fixture file...")

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    fixture_path = FIXTURE_DIR / FIXTURE_FILE_NAME
    fixture_path.write_text(FIXTURE_CONTENT, encoding="utf-8")

    print(f"Fixture created: {fixture_path}")

    # -----------------------------------------------------
    # Load engines
    # -----------------------------------------------------

    print("\nLoading engines...")

    print("  Loading SemanticDecisionEngine (this may take a moment)...")
    semantic_engine = SemanticDecisionEngine()

    print("  Loading BehavioralSignatureEngine...")
    behavioral_engine = BehavioralSignatureEngine()

    print("  Loading FusionEngine...")
    fusion_engine = FusionEngine()

    print("All engines loaded.")

    # -----------------------------------------------------
    # Pre-compute behavioral signatures for the fixture file
    # (called once, then we look up per-function)
    # -----------------------------------------------------

    print("\nExtracting behavioral signatures from fixture file...")
    behavioral_signatures = behavioral_engine.analyze_file(
        str(fixture_path)
    )
    print(
        f"Extracted {len(behavioral_signatures)} "
        f"function signatures."
    )

    # -----------------------------------------------------
    # Execute test cases
    # -----------------------------------------------------

    results = []
    pass_count = 0
    error_count = 0

    for index, case in enumerate(TEST_CASES, start=1):

        print("\n" + "-" * 90)
        print(
            f"[{index}/{len(TEST_CASES)}] {case['category']} - "
            f"{case['description']}"
        )

        result = run_pipeline(
            case=case,
            fixture_path=fixture_path,
            semantic_engine=semantic_engine,
            behavioral_engine=behavioral_engine,
            fusion_engine=fusion_engine,
            behavioral_signatures=behavioral_signatures,
        )

        results.append(result)

        if result["status"] == "PASS":
            pass_count += 1
        elif result["status"] == "ERROR":
            error_count += 1

        # Print summary
        if result["status"] == "ERROR":
            print(f"  ERROR: {result.get('error', 'Unknown error')}")
            continue

        print(f"  Semantic score    : {result['semantic_score']}")
        print(f"  Semantic decision : {result['semantic_decision']}")
        print(f"  Behavior A tags   : {result['behavior_a_tags']}")
        print(f"  Behavior B tags   : {result['behavior_b_tags']}")
        print(f"  Behavior A risk   : {result['behavior_a_risk']}")
        print(f"  Behavior B risk   : {result['behavior_b_risk']}")
        print(f"  Fusion decision   : {result['fusion_decision']}")
        print(f"  Fusion risk level : {result['fusion_risk_level']}")
        print(f"  Fusion risk score : {result['fusion_risk_score']}")
        print(f"  Opposing detected : {result['opposing_detected']}")
        print(f"  Expected          : {result['expected_decision']}")
        print(f"  Status            : {result['status']}")

    # -----------------------------------------------------
    # Compute summary
    # -----------------------------------------------------

    total = len(TEST_CASES)
    accuracy = round(100 * pass_count / total, 2) if total else 0
    overall_status = (
        "PASS" if pass_count == total and error_count == 0 else "FAIL"
    )

    report = {
        "test_case": "TC_V2_045",
        "category": "Real Engine Integration Validation",
        "pipeline": (
            "SemanticDecisionEngine -> "
            "BehavioralSignatureEngine -> "
            "FusionEngine"
        ),
        "tests_executed": total,
        "tests_passed": pass_count,
        "tests_failed": total - pass_count - error_count,
        "tests_errored": error_count,
        "decision_accuracy_percent": accuracy,
        "overall_status": overall_status,
        "fixture_file": str(fixture_path),
        "results": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print("\n" + "=" * 90)
    print(f"Tests Executed         : {total}")
    print(f"Tests Passed           : {pass_count}")
    print(f"Tests Failed           : {total - pass_count - error_count}")
    print(f"Tests Errored          : {error_count}")
    print(f"Decision Accuracy      : {accuracy}%")
    print(f"Overall Status         : {overall_status}")
    print(f"Report Saved           : {REPORT_FILE}")
    print("=" * 90)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    run_test()
