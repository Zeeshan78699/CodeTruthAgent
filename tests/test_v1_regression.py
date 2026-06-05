"""
CodeTruth Agent V2
V1 Regression Protection Tests
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

from validation.syntax_validator import SyntaxValidator
from validation.rollback_manager import RollbackManager

# ===================================================
# TEST CONFIGURATION
# ===================================================

TEST_FILE = "sample_test_file.txt"

# ===================================================
# V1 VALIDATION REGRESSION TEST
# ===================================================

def test_v1_validation_still_works():

    valid_code = """
def hello():
    print("Hello World")
"""

    result = SyntaxValidator.validate_python_code(
        valid_code
    )

    assert result["success"] is True
    assert result["valid"] is True

# ===================================================
# V1 INVALID VALIDATION REGRESSION TEST
# ===================================================

def test_v1_invalid_validation_still_works():

    invalid_code = """
def hello(
    print("Broken")
"""

    result = SyntaxValidator.validate_python_code(
        invalid_code
    )

    assert result["success"] is False
    assert result["valid"] is False

# ===================================================
# V1 ROLLBACK REGRESSION TEST
# ===================================================

def test_v1_rollback_still_works():

    backup_result = RollbackManager.create_backup(
        TEST_FILE
    )

    assert backup_result["success"] is True

    assert os.path.exists(
        backup_result["backup_path"]
    )