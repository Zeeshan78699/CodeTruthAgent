"""
CodeTruth Agent V2
Real SIT Pipeline Test
"""

import os
import sys

# ===================================================
# PROJECT ROOT SETUP
# ===================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

# ===================================================
# IMPORTS
# ===================================================

from ai.ai_interface import AIInterface
from validation.syntax_validator import SyntaxValidator
from memory.memory_store_v2 import MemoryStoreV2
from reporting.report_generator import ReportGenerator
from validation.rollback_manager import RollbackManager

# ===================================================
# TEST CONFIGURATION
# ===================================================

TEST_FILE = "sample_test_file.txt"

# ===================================================
# REAL SIT PIPELINE TEST
# ===================================================

def test_full_v2_pipeline():

    # ---------------------------------------------------
    # AI GATEWAY
    # ---------------------------------------------------

    ai_gateway = AIInterface(
        ai_enabled=False
    )

    ai_result = ai_gateway.analyze_text(
        "Test Prompt"
    )

    assert ai_result["fallback_used"] is True

    # ---------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------

    valid_code = """
def hello():
    print("Hello World")
"""

    validation_result = (
        SyntaxValidator.validate_python_code(
            valid_code
        )
    )

    assert validation_result["valid"] is True

    # ---------------------------------------------------
    # MEMORY
    # ---------------------------------------------------

    memory = MemoryStoreV2()

    memory.store_approved_decision({
        "decision": "SIT Pipeline Test",
        "risk_level": "LOW"
    })

    memory_data = memory.get_memory()

    assert "approved_decisions" in memory_data

    # ---------------------------------------------------
    # REPORTING
    # ---------------------------------------------------

    report_data = {
        "ai_gateway": ai_result,
        "validation": validation_result,
        "memory": memory_data
    }

    ReportGenerator.generate_console_report(
        report_data
    )

    assert isinstance(report_data, dict)

    # ---------------------------------------------------
    # ROLLBACK
    # ---------------------------------------------------

    backup_result = (
        RollbackManager.create_backup(
            TEST_FILE
        )
    )

    assert backup_result["success"] is True

    # MODIFY FILE
    with open(TEST_FILE, "w") as file:
        file.write("Unsafe SIT Content")

    # RESTORE FILE
    restore_result = (
        RollbackManager.restore_backup(
            backup_result["backup_path"],
            TEST_FILE
        )
    )

    assert restore_result["success"] is True

    # VERIFY CONTENT
    with open(TEST_FILE, "r") as file:
        content = file.read()

    assert content == "Original Safe Content"