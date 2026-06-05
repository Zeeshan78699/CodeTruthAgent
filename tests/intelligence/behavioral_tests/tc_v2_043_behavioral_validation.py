"""
TC_V2_043 - Behavioral Intelligence Validation

Objective:
Validate the BehavioralSignatureEngine on real Python code fixtures.

Each fixture file contains hand-crafted functions that exhibit a
specific behavior category. The engine scans the file, and we verify
that the expected behavioral tags appear in the detected tags.

Unlike TC_V2_042 (function names only), this test uses actual code
bodies - the way the engine will be used in production governance.

Categories validated:
- FILE_WRITE
- FILE_READ
- DELETE_OPERATION
- NETWORK_OPERATION
- DATABASE_OPERATION
- AUTH_OPERATION
- BACKUP_OPERATION
- RECOVERY_OPERATION
- MEMORY_OPERATION
- STATE_MUTATION
- OBJECT_CREATION
- CLEAN (control case - no behaviors expected)

Pass criterion (per function):
The expected tag MUST be present in the detected tags. The engine
may detect ADDITIONAL tags (that's fine - functions often have
multiple behaviors). Failures are only when the expected behavior
is MISSING.

Category:
V2.1 Behavioral Intelligence Validation
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path


# =========================================================
# PATH SETUP
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# ENGINE IMPORT
# =========================================================

from ai.behavioral_signature_engine import (
    BehavioralSignatureEngine,
)


# =========================================================
# OUTPUT PATHS
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "behavioral_validation_reports"
)

FIXTURE_DIR = OUTPUT_DIR / "fixtures"

REPORT_FILE = OUTPUT_DIR / "TC_V2_043_report.json"


# =========================================================
# FIXTURE BUILDER
# =========================================================

def build_fixtures():
    """
    Build 12 hand-crafted Python fixture files, one per behavior
    category. Each file contains a function whose behavior the
    engine should detect.
    """

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = {

        # -----------------------------------------------------
        # 1. FILE_WRITE
        # -----------------------------------------------------
        "file_write_fixture.py": (
            "def save_user_data(data):\n"
            "    with open('out.txt', 'w') as f:\n"
            "        f.write(data)\n"
            "    return True\n"
        ),

        # -----------------------------------------------------
        # 2. FILE_READ
        # -----------------------------------------------------
        "file_read_fixture.py": (
            "def load_config_file(path):\n"
            "    with open(path, 'r') as f:\n"
            "        contents = f.read()\n"
            "    return contents\n"
        ),

        # -----------------------------------------------------
        # 3. DELETE_OPERATION
        # -----------------------------------------------------
        "delete_fixture.py": (
            "import os\n"
            "\n"
            "def cleanup_temp_file(path):\n"
            "    os.remove(path)\n"
            "    return True\n"
        ),

        # -----------------------------------------------------
        # 4. NETWORK_OPERATION
        # -----------------------------------------------------
        "network_fixture.py": (
            "import requests\n"
            "\n"
            "def fetch_user_profile(user_id):\n"
            "    response = requests.request(\n"
            "        'GET',\n"
            "        f'https://api.example.com/users/{user_id}'\n"
            "    )\n"
            "    return response.json()\n"
        ),

        # -----------------------------------------------------
        # 5. DATABASE_OPERATION
        # -----------------------------------------------------
        "database_fixture.py": (
            "def insert_user_record(conn, user):\n"
            "    cursor = conn.cursor()\n"
            "    cursor.execute('INSERT INTO users VALUES (?)', (user,))\n"
            "    conn.commit()\n"
            "    return cursor\n"
        ),

        # -----------------------------------------------------
        # 6. AUTH_OPERATION
        # -----------------------------------------------------
        "auth_fixture.py": (
            "def login_user(username, password):\n"
            "    token = authenticate(username, password)\n"
            "    return token\n"
            "\n"
            "def authenticate(user, pwd):\n"
            "    return 'fake_token'\n"
        ),

        # -----------------------------------------------------
        # 7. BACKUP_OPERATION
        # -----------------------------------------------------
        "backup_fixture.py": (
            "def archive_user_data(user_id):\n"
            "    create_backup(user_id)\n"
            "    return True\n"
            "\n"
            "def create_backup(target):\n"
            "    return True\n"
        ),

        # -----------------------------------------------------
        # 8. RECOVERY_OPERATION
        # -----------------------------------------------------
        "recovery_fixture.py": (
            "def restore_user_data(user_id):\n"
            "    restore_backup(user_id)\n"
            "    return True\n"
            "\n"
            "def restore_backup(target):\n"
            "    return True\n"
        ),

        # -----------------------------------------------------
        # 9. MEMORY_OPERATION
        # -----------------------------------------------------
        "memory_fixture.py": (
            "def persist_decision(decision):\n"
            "    store_memory(decision)\n"
            "    return True\n"
            "\n"
            "def store_memory(payload):\n"
            "    return True\n"
        ),

        # -----------------------------------------------------
        # 10. STATE_MUTATION
        # -----------------------------------------------------
        "state_mutation_fixture.py": (
            "def add_event_to_log(log_list, event):\n"
            "    log_list.append(event)\n"
            "    return log_list\n"
        ),

        # -----------------------------------------------------
        # 11. OBJECT_CREATION
        # -----------------------------------------------------
        "object_creation_fixture.py": (
            "class UserRecord:\n"
            "    def __init__(self, name):\n"
            "        self.name = name\n"
            "\n"
            "def create_user(name):\n"
            "    user = UserRecord(name)\n"
            "    return user\n"
        ),

        # -----------------------------------------------------
        # 12. CLEAN (control case - no behaviors expected)
        # -----------------------------------------------------
        "clean_fixture.py": (
            "def add_numbers(a, b):\n"
            "    return a + b\n"
            "\n"
            "def multiply(x, y):\n"
            "    return x * y\n"
        ),
    }

    for filename, source in fixtures.items():
        (FIXTURE_DIR / filename).write_text(source, encoding="utf-8")

    return list(fixtures.keys())


# =========================================================
# TEST CASES
# =========================================================
#
# Each case: (fixture_filename, function_to_check, expected_tag,
#             expected_risk_level)
#
# Notes:
# - expected_tag is the behavior we REQUIRE to be present
# - expected_risk_level is what the engine should classify
# - clean_fixture is the control case - no tags expected

TEST_CASES = [

    # FILE_WRITE
    {
        "fixture": "file_write_fixture.py",
        "function": "save_user_data",
        "expected_tag": "FILE_WRITE",
        "expected_risk": "MEDIUM",
        "category": "FILE_WRITE",
    },

    # FILE_READ
    {
        "fixture": "file_read_fixture.py",
        "function": "load_config_file",
        "expected_tag": "FILE_READ",
        "expected_risk": "MEDIUM",
        "category": "FILE_READ",
    },

    # DELETE_OPERATION (HIGH impact)
    {
        "fixture": "delete_fixture.py",
        "function": "cleanup_temp_file",
        "expected_tag": "DELETE_OPERATION",
        "expected_risk": "HIGH",
        "category": "DELETE_OPERATION",
    },

    # NETWORK_OPERATION
    {
        "fixture": "network_fixture.py",
        "function": "fetch_user_profile",
        "expected_tag": "NETWORK_OPERATION",
        "expected_risk": "MEDIUM",
        "category": "NETWORK_OPERATION",
    },

    # DATABASE_OPERATION (HIGH impact)
    {
        "fixture": "database_fixture.py",
        "function": "insert_user_record",
        "expected_tag": "DATABASE_OPERATION",
        "expected_risk": "HIGH",
        "category": "DATABASE_OPERATION",
    },

    # AUTH_OPERATION (HIGH impact)
    {
        "fixture": "auth_fixture.py",
        "function": "login_user",
        "expected_tag": "AUTH_OPERATION",
        "expected_risk": "HIGH",
        "category": "AUTH_OPERATION",
    },

    # BACKUP_OPERATION
    {
        "fixture": "backup_fixture.py",
        "function": "archive_user_data",
        "expected_tag": "BACKUP_OPERATION",
        "expected_risk": "MEDIUM",
        "category": "BACKUP_OPERATION",
    },

    # RECOVERY_OPERATION (HIGH impact)
    {
        "fixture": "recovery_fixture.py",
        "function": "restore_user_data",
        "expected_tag": "RECOVERY_OPERATION",
        "expected_risk": "HIGH",
        "category": "RECOVERY_OPERATION",
    },

    # MEMORY_OPERATION
    {
        "fixture": "memory_fixture.py",
        "function": "persist_decision",
        "expected_tag": "MEMORY_OPERATION",
        "expected_risk": "MEDIUM",
        "category": "MEMORY_OPERATION",
    },

    # STATE_MUTATION
    {
        "fixture": "state_mutation_fixture.py",
        "function": "add_event_to_log",
        "expected_tag": "STATE_MUTATION",
        "expected_risk": "MEDIUM",
        "category": "STATE_MUTATION",
    },

    # OBJECT_CREATION
    {
        "fixture": "object_creation_fixture.py",
        "function": "create_user",
        "expected_tag": "OBJECT_CREATION",
        "expected_risk": "MEDIUM",
        "category": "OBJECT_CREATION",
    },

    # CLEAN (control - no tags expected)
    {
        "fixture": "clean_fixture.py",
        "function": "add_numbers",
        "expected_tag": None,
        "expected_risk": "LOW",
        "category": "CLEAN",
    },
]


# =========================================================
# TEST EXECUTION
# =========================================================

def find_signature(signatures, function_name):
    """
    Find a behavioral signature by function name.
    """
    for sig in signatures:
        if sig.function_name == function_name:
            return sig
    return None


def evaluate_test_case(case, engine):
    """
    Run one test case. Returns a result dict.
    """

    fixture_path = FIXTURE_DIR / case["fixture"]

    signatures = engine.analyze_file(str(fixture_path))

    sig = find_signature(signatures, case["function"])

    if sig is None:
        return {
            "category": case["category"],
            "function": case["function"],
            "expected_tag": case["expected_tag"],
            "expected_risk": case["expected_risk"],
            "detected_tags": [],
            "detected_risk": None,
            "tag_match": False,
            "risk_match": False,
            "status": "FAIL",
            "reason": "Function not found in signature output",
        }

    detected_tags = sig.behavioral_tags
    detected_risk = sig.risk_level

    # Tag presence check
    if case["expected_tag"] is None:
        # Clean fixture: no behavioral tags should be present
        tag_match = len(detected_tags) == 0
    else:
        tag_match = case["expected_tag"] in detected_tags

    # Risk level check
    risk_match = detected_risk == case["expected_risk"]

    # Overall pass: tag match required; risk match nice-to-have
    # (but we report both)
    status = "PASS" if tag_match else "FAIL"

    return {
        "category": case["category"],
        "function": case["function"],
        "expected_tag": case["expected_tag"],
        "expected_risk": case["expected_risk"],
        "detected_tags": detected_tags,
        "detected_risk": detected_risk,
        "side_effects": sig.side_effects,
        "function_calls": sig.function_calls,
        "method_calls": sig.method_calls,
        "tag_match": tag_match,
        "risk_match": risk_match,
        "status": status,
    }


def run_test():
    """
    Build fixtures, run engine on each, evaluate.
    """

    print("=" * 90)
    print("TC_V2_043 - BEHAVIORAL INTELLIGENCE VALIDATION")
    print("=" * 90)

    # Build fixture files
    print("\nBuilding fixture files...")
    fixtures = build_fixtures()
    print(f"Created {len(fixtures)} fixture files in: {FIXTURE_DIR}")

    # Load engine
    print("\nLoading BehavioralSignatureEngine...")
    engine = BehavioralSignatureEngine()
    print("BehavioralSignatureEngine loaded.")

    # Run cases
    results = []
    pass_count = 0
    tag_match_count = 0
    risk_match_count = 0

    for index, case in enumerate(TEST_CASES, start=1):

        print("\n" + "-" * 90)
        print(
            f"[{index}/{len(TEST_CASES)}] {case['category']} -> "
            f"{case['function']}"
        )

        result = evaluate_test_case(case, engine)
        results.append(result)

        if result["status"] == "PASS":
            pass_count += 1

        if result["tag_match"]:
            tag_match_count += 1

        if result["risk_match"]:
            risk_match_count += 1

        print(f"  Expected tag    : {result['expected_tag']}")
        print(f"  Detected tags   : {result['detected_tags']}")
        print(f"  Expected risk   : {result['expected_risk']}")
        print(f"  Detected risk   : {result['detected_risk']}")
        print(f"  Tag match       : {result['tag_match']}")
        print(f"  Risk match      : {result['risk_match']}")
        print(f"  Status          : {result['status']}")

    # Compute summary
    total = len(TEST_CASES)
    tag_accuracy = round(100 * tag_match_count / total, 2)
    risk_accuracy = round(100 * risk_match_count / total, 2)
    overall_accuracy = round(100 * pass_count / total, 2)

    overall_status = "PASS" if pass_count == total else "FAIL"

    report = {
        "test_case": "TC_V2_043",
        "category": "Behavioral Intelligence Validation",
        "tests_executed": total,
        "tests_passed": pass_count,
        "tag_match_count": tag_match_count,
        "risk_match_count": risk_match_count,
        "tag_accuracy_percent": tag_accuracy,
        "risk_accuracy_percent": risk_accuracy,
        "overall_accuracy_percent": overall_accuracy,
        "overall_status": overall_status,
        "results": results,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    # Summary
    print("\n" + "=" * 90)
    print(f"Tests Executed        : {total}")
    print(f"Tests Passed          : {pass_count}")
    print(f"Tag Match Count       : {tag_match_count}/{total}")
    print(f"Risk Match Count      : {risk_match_count}/{total}")
    print(f"Tag Accuracy          : {tag_accuracy}%")
    print(f"Risk Accuracy         : {risk_accuracy}%")
    print(f"Overall Status        : {overall_status}")
    print(f"Report Saved          : {REPORT_FILE}")
    print("=" * 90)


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    run_test()
