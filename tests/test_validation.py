"""
CodeTruth Agent V2
Formal Validation Tests
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

from validation.syntax_validator import SyntaxValidator


# ===================================================
# POSITIVE TEST
# ===================================================

def test_valid_python_code():

    valid_code = """
def hello():
    print("Hello World")
"""

    result = SyntaxValidator.validate_python_code(
        valid_code
    )

    assert result["success"] is True
    assert result["valid"] is True
    assert result["error"] is None


# ===================================================
# NEGATIVE TEST
# ===================================================

def test_invalid_python_code():

    invalid_code = """
def hello(
    print("Broken")
"""

    result = SyntaxValidator.validate_python_code(
        invalid_code
    )

    assert result["success"] is False
    assert result["valid"] is False
    assert result["error"] is not None