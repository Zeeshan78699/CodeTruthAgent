"""
CodeTruth Agent V2
Syntax Validation Engine
"""

import ast
from typing import Dict, Any


class SyntaxValidator:

    @staticmethod
    def validate_python_code(code: str) -> Dict[str, Any]:
        """
        Validates Python syntax safely.
        """

        try:

            ast.parse(code)

            return {
                "success": True,
                "valid": True,
                "error": None,
                "message": "Python syntax is valid."
            }

        except SyntaxError as exc:

            return {
                "success": False,
                "valid": False,
                "error": str(exc),
                "message": "Python syntax validation failed."
            }


def validate_python_syntax(file_path: str) -> bool:
    """
    Compatibility wrapper for V2 orchestration layer.

    Used by:
    - safe_execution_engine.py
    """

    try:

        with open(file_path, "r", encoding="utf-8") as file:
            source = file.read()

        result = SyntaxValidator.validate_python_code(source)

        return result["valid"]

    except Exception:

        return False