"""
CodeTruth Agent V2
SIT Failure Pipeline Tests
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

from ai.ai_interface import AIInterface
from validation.syntax_validator import SyntaxValidator
from memory.memory_store_v2 import MemoryStoreV2


# ===================================================
# FULL PIPELINE FAILURE SURVIVAL TEST
# ===================================================

def test_pipeline_survives_validation_failure():

    # ---------------------------------------------------
    # AI GATEWAY
    # ---------------------------------------------------

    ai_gateway = AIInterface(
        ai_enabled=False
    )

    ai_result = ai_gateway.analyze_text(
        "Failure Pipeline Test"
    )

    assert ai_result["fallback_used"] is True

    # ---------------------------------------------------
    # INVALID VALIDATION
    # ---------------------------------------------------

    invalid_code = """
def broken(
    print("failure")
"""

    validation_result = (
        SyntaxValidator.validate_python_code(
            invalid_code
        )
    )

    assert validation_result["valid"] is False

    # ---------------------------------------------------
    # MEMORY MUST STILL WORK
    # ---------------------------------------------------

    memory = MemoryStoreV2()

    result = memory.store_approved_decision({
        "decision": "Failure Pipeline Test",
        "risk_level": "LOW"
    })

    assert "success" in result

    # ---------------------------------------------------
    # PIPELINE SURVIVAL CONFIRMATION
    # ---------------------------------------------------

    assert True