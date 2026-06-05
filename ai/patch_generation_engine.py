"""
CodeTruth Agent V2
Controlled Patch Generation Engine

Objective:
Generate SAFE deterministic code patches
before governance execution.

V2 Philosophy:
- controlled generation
- deterministic first
- explainable behavior
- governance before execution
- rollback-safe architecture

IMPORTANT:
This is NOT autonomous unrestricted generation.
This is controlled repository-aware patch synthesis.
"""

from __future__ import annotations

import ast
import difflib
from dataclasses import dataclass
from typing import Dict
from typing import List
from typing import Optional


# =========================================================
# PATCH OBJECT
# =========================================================

@dataclass
class PatchCandidate:

    target_file: str
    original_code: str
    modified_code: str

    patch_reason: str

    confidence_score: float

    generation_type: str

    risk_level: str

    syntax_valid: bool

    diff_preview: List[str]


# =========================================================
# PATCH GENERATION ENGINE
# =========================================================

class PatchGenerationEngine:

    def __init__(self):

        self.supported_patch_types = {

            "missing_try_except",

         #   "missing_return",

            "unsafe_eval",

            "unsafe_exec",

            "print_to_logger",

         #   "missing_encoding",

         #   "missing_exists_check",
        }
        
        self.patch_confidence = {
            "unsafe_eval": 0.95,
            "unsafe_exec": 0.95,
            "print_to_logger": 0.90,
            "missing_try_except": 0.60,
        }

    # =====================================================
    # MAIN PATCH ENTRY
    # =====================================================

    def generate_patch(

        self,

        issue_type: str,

        source_code: str,

        target_file: str,

        metadata: Optional[Dict] = None

    ) -> PatchCandidate:

        metadata = metadata or {}

        if issue_type not in self.supported_patch_types:

            return self._build_failed_patch(
                target_file=target_file,
                source_code=source_code,
                reason=f"Unsupported issue type: {issue_type}"
            )

        generator = getattr(
            self,
            f"_patch_{issue_type}",
            None
        )

        if generator is None:

            return self._build_failed_patch(
                target_file=target_file,
                source_code=source_code,
                reason=f"Generator not implemented: {issue_type}"
            )

        try:

            modified_code = generator(
                source_code,
                metadata
            )

            syntax_valid = self._validate_syntax(
                modified_code
            )

            diff_preview = self._generate_diff(
                source_code,
                modified_code
            )

            return PatchCandidate(

                target_file=target_file,

                original_code=source_code,

                modified_code=modified_code,

                patch_reason=issue_type,

                confidence_score=self.patch_confidence.get(
                    issue_type,
                    0.50
                ),

                generation_type="CONTROLLED_PATCH",

                risk_level="LOW",

                syntax_valid=syntax_valid,

                diff_preview=diff_preview
            )

        except Exception as error:

            return self._build_failed_patch(
                target_file=target_file,
                source_code=source_code,
                reason=str(error)
            )

    # =====================================================
    # PATCH: UNSAFE EVAL
    # =====================================================

    def _patch_unsafe_eval(

        self,

        source_code: str,

        metadata: Dict

    ) -> str:

        return source_code.replace(

            "eval(",

            "safe_eval("
        )

    # =====================================================
    # PATCH: UNSAFE EXEC
    # =====================================================

    def _patch_unsafe_exec(

        self,

        source_code: str,

        metadata: Dict

    ) -> str:

        return source_code.replace(

            "exec(",

            "safe_exec("
        )

    # =====================================================
    # PATCH: PRINT TO LOGGER
    # =====================================================

    def _patch_print_to_logger(

        self,

        source_code: str,

        metadata: Dict

    ) -> str:

        lines = source_code.splitlines()

        updated = []

        logger_import_exists = (
            "import logging"
            in source_code
        )

        if not logger_import_exists:

            updated.append("import logging")
            updated.append("")

        for line in lines:

            stripped = line.strip()

            if stripped.startswith("print("):

                indent = (
                    len(line)
                    - len(line.lstrip())
                )

                spaces = " " * indent

                updated.append(
                    f"{spaces}logging.info"
                    f"{stripped[5:]}"
                )

            else:

                updated.append(line)

        return "\n".join(updated)

    # =====================================================
    # PATCH: MISSING ENCODING
    # =====================================================

    def _patch_missing_encoding(

        self,

        source_code: str,

        metadata: Dict

    ) -> str:

        updated = source_code.replace(

            'open(',

            'open('
        )

        updated = updated.replace(

            '")',

            '", encoding="utf-8")'
        )

        return updated

    # =====================================================
    # PATCH: MISSING EXISTS CHECK
    # =====================================================

    def _patch_missing_exists_check(

        self,

        source_code: str,

        metadata: Dict

    ) -> str:

        lines = source_code.splitlines()

        updated = []

        if "import os" not in source_code:

            updated.append("import os")
            updated.append("")
            inserted_import = True

        for line in lines:

            updated.append(line)

            if "open(" in line:

                updated.append(
                    "if not os.path.exists(file_path):"
                )

                updated.append(
                    "    raise FileNotFoundError(file_path)"
                )

        return "\n".join(updated)

    # =====================================================
    # PATCH: MISSING TRY EXCEPT
    # =====================================================

    def _patch_missing_try_except(

        self,

        source_code: str,

        metadata: Dict

    ) -> str:

        lines = source_code.splitlines()

        wrapped = []

        wrapped.append("try:")

        for line in lines:

            wrapped.append(f"    {line}")

        wrapped.append("")
        wrapped.append("except Exception as error:")
        wrapped.append("    print(error)")

        return "\n".join(wrapped)

    # =====================================================
    # PATCH: MISSING RETURN
    # =====================================================

    def _patch_missing_return(

        self,

        source_code: str,

        metadata: Dict

    ) -> str:

        if "return " in source_code:

            return source_code

        return source_code + "\n\nreturn None\n"

    # =====================================================
    # SYNTAX VALIDATION
    # =====================================================

    def _validate_syntax(

        self,

        source_code: str

    ) -> bool:

        try:

            ast.parse(source_code)

            return True

        except Exception:

            return False

    # =====================================================
    # GENERATE DIFF
    # =====================================================

    def _generate_diff(

        self,

        original: str,

        modified: str

    ) -> List[str]:

        return list(

            difflib.unified_diff(

                original.splitlines(),

                modified.splitlines(),

                lineterm=""
            )
        )

    # =====================================================
    # FAILED PATCH
    # =====================================================

    def _build_failed_patch(

        self,

        target_file: str,

        source_code: str,

        reason: str

    ) -> PatchCandidate:

        return PatchCandidate(

            target_file=target_file,

            original_code=source_code,

            modified_code=source_code,

            patch_reason=reason,

            confidence_score=0.0,

            generation_type="FAILED_PATCH",

            risk_level="HIGH",

            syntax_valid=False,

            diff_preview=[]
        )


# =========================================================
# MANUAL TEST
# =========================================================

if __name__ == "__main__":

    engine = PatchGenerationEngine()

    sample_code = '''

def run_user_code(user_input):

    result = eval(user_input)

    print(result)

'''

    result = engine.generate_patch(

        issue_type="unsafe_eval",

        source_code=sample_code,

        target_file="demo.py"
    )

    print("=" * 60)
    print("PATCH RESULT")
    print("=" * 60)

    print(result)

    print("\nDIFF PREVIEW:")
    print("=" * 60)

    for line in result.diff_preview:

        print(line)