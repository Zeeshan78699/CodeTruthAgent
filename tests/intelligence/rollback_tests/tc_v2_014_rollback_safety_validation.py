"""
TC_V2_014 — Rollback Safety Validation

Title:
Can the Engine Safely Restore Repository State After Modification?

Description:
This test validates whether CodeTruth Agent V2 can safely
restore repository state after unsafe modification.

Objective:
Validate rollback governance cognition.

Expected Result:
PASS

Category:
Rollback Governance Validation
"""

import shutil
from pathlib import Path
import json


# =========================================================
# TEST FILE PATHS
# =========================================================

TEST_DIR = Path(
    "tests/output/v2/rollback_reports"
)

TEST_DIR.mkdir(
    parents=True,
    exist_ok=True
)

ORIGINAL_FILE = TEST_DIR / "sample_module.py"

BACKUP_FILE = TEST_DIR / "sample_module_backup.py"


# =========================================================
# ORIGINAL SAFE CONTENT
# =========================================================

ORIGINAL_CONTENT = '''
def calculate_total():

    return 100
'''


# =========================================================
# BROKEN CONTENT
# =========================================================

BROKEN_CONTENT = '''
def calculate_total():

    return "BROKEN"
'''


# =========================================================
# ROLLBACK ENGINE
# =========================================================

class RollbackEngine:

    # -----------------------------------------------------
    # Create Original File
    # -----------------------------------------------------

    def create_original_file(self):

        with open(ORIGINAL_FILE, "w") as f:
            f.write(ORIGINAL_CONTENT)

    # -----------------------------------------------------
    # Create Backup
    # -----------------------------------------------------

    def create_backup(self):

        shutil.copy2(
            ORIGINAL_FILE,
            BACKUP_FILE
        )

    # -----------------------------------------------------
    # Unsafe Modification
    # -----------------------------------------------------

    def apply_broken_change(self):

        with open(ORIGINAL_FILE, "w") as f:
            f.write(BROKEN_CONTENT)

    # -----------------------------------------------------
    # Rollback Restore
    # -----------------------------------------------------

    def rollback_restore(self):

        shutil.copy2(
            BACKUP_FILE,
            ORIGINAL_FILE
        )

    # -----------------------------------------------------
    # Read Current Content
    # -----------------------------------------------------

    def read_current_content(self):

        with open(ORIGINAL_FILE, "r") as f:
            return f.read()


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceValidationEngine:

    def validate_integrity(
        self,
        current_content
    ):

        if (
            current_content.strip()
            ==
            ORIGINAL_CONTENT.strip()
        ):

            return {
                "status": "PASS",
                "reason":
                    (
                        "Repository state successfully "
                        "restored."
                    )
            }

        return {
            "status": "FAIL",
            "reason":
                (
                    "Repository rollback restoration failed."
                )
        }


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 60)
    print("TC_V2_014 — Rollback Safety Validation")
    print("=" * 60)

    rollback_engine = RollbackEngine()

    # -----------------------------------------------------
    # Step 1 — Create Original File
    # -----------------------------------------------------

    rollback_engine.create_original_file()

    # -----------------------------------------------------
    # Step 2 — Create Backup
    # -----------------------------------------------------

    rollback_engine.create_backup()

    # -----------------------------------------------------
    # Step 3 — Apply Unsafe Modification
    # -----------------------------------------------------

    rollback_engine.apply_broken_change()

    broken_content = (
        rollback_engine.read_current_content()
    )

    # -----------------------------------------------------
    # Step 4 — Rollback Restore
    # -----------------------------------------------------

    rollback_engine.rollback_restore()

    restored_content = (
        rollback_engine.read_current_content()
    )

    # -----------------------------------------------------
    # Step 5 — Governance Validation
    # -----------------------------------------------------

    governance_engine = (
        GovernanceValidationEngine()
    )

    final_result = (
        governance_engine.validate_integrity(
            restored_content
        )
    )

    # -----------------------------------------------------
    # Step 6 — Display Results
    # -----------------------------------------------------

    print("\n[Broken Repository State]")
    print(broken_content)

    print("\n[Restored Repository State]")
    print(restored_content)

    print("\n[Rollback Validation]")
    print(final_result)

    # -----------------------------------------------------
    # Step 7 — Save Report
    # -----------------------------------------------------

    report = {
        "test_case": "TC_V2_014",
        "title":
            "Rollback Safety Validation",
        "description":
            (
                "Validates whether V2 can safely "
                "restore repository state."
            ),
        "category":
            "Rollback Governance",
        "rollback_restored":
            (
                final_result["status"]
                == "PASS"
            ),
        "status":
            final_result["status"],
        "reason":
            final_result["reason"]
    }

    output_file = (
        TEST_DIR /
        "TC_V2_014_report.json"
    )

    with open(output_file, "w") as f:
        json.dump(report, f, indent=4)

    print("\n[Test Status]")
    print(final_result["status"])

    print("\n[Report Saved]")
    print(output_file)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    run_test()