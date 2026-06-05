"""
CodeTruth Agent V2
Test Execution Engine

Objective:
Safely execute repository test suites and
capture results for governance decisions.

Used By:
- main_v2.py
- Rollback Layer
- Safe Execution Layer
- Future CodeGenerationEngine

V2 Philosophy:
- deterministic
- governance-first
- safety-first
- rollback-aware
"""

from __future__ import annotations

import subprocess
import time

from dataclasses import dataclass
from typing import List


# =========================================================
# TEST RESULT
# =========================================================

@dataclass
class TestExecutionResult:
    
    __test__ = False

    success: bool

    total_tests: int

    passed_tests: int

    failed_tests: int

    execution_time_seconds: float

    command: str

    output: str

    errors: List[str]


# =========================================================
# TEST EXECUTION ENGINE
# =========================================================

class TestExecutionEngine:
    
    __test__ = False

    def __init__(self):

        self.default_timeout = 300

    # =====================================================
    # MAIN EXECUTION
    # =====================================================

    def execute_tests(

        self,

        command: str = "pytest -q",

        working_directory: str | None = None

    ) -> TestExecutionResult:

        start_time = time.time()

        errors = []

        try:

            result = subprocess.run(

                command,

                shell=True,

                cwd=working_directory,

                capture_output=True,

                text=True,

                timeout=self.default_timeout
            )

            duration = round(
                time.time() - start_time,
                2
            )

            output = (
                result.stdout
                + "\n"
                + result.stderr
            )

            passed_tests = self._extract_pass_count(
                output
            )

            failed_tests = self._extract_fail_count(
                output
            )

            total_tests = (
                passed_tests + failed_tests
            )

            success = (
                result.returncode == 0
            )

            return TestExecutionResult(

                success=success,

                total_tests=total_tests,

                passed_tests=passed_tests,

                failed_tests=failed_tests,

                execution_time_seconds=duration,

                command=command,

                output=output,

                errors=errors
            )

        except subprocess.TimeoutExpired:

            errors.append(
                "Test execution timed out."
            )

        except Exception as ex:

            errors.append(
                str(ex)
            )

        duration = round(
            time.time() - start_time,
            2
        )

        return TestExecutionResult(

            success=False,

            total_tests=0,

            passed_tests=0,

            failed_tests=0,

            execution_time_seconds=duration,

            command=command,

            output="",

            errors=errors
        )

    # =====================================================
    # PASS COUNT
    # =====================================================

    def _extract_pass_count(

        self,

        output: str

    ) -> int:

        import re

        patterns = [

            r"(\d+)\s+passed",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                output,
                re.IGNORECASE
            )

            if match:

                return int(
                    match.group(1)
                )

        return 0

    # =====================================================
    # FAIL COUNT
    # =====================================================

    def _extract_fail_count(

        self,

        output: str

    ) -> int:

        import re

        patterns = [

            r"(\d+)\s+failed",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                output,
                re.IGNORECASE
            )

            if match:

                return int(
                    match.group(1)
                )

        return 0

    # =====================================================
    # QUICK VALIDATION
    # =====================================================

    def tests_passed(

        self,

        result: TestExecutionResult

    ) -> bool:

        return result.success


# =========================================================
# MANUAL TEST
# =========================================================

if __name__ == "__main__":

    engine = TestExecutionEngine()

    result = engine.execute_tests()

    print("=" * 60)
    print("TEST EXECUTION RESULT")
    print("=" * 60)

    print(
        f"Success: {result.success}"
    )

    print(
        f"Passed: {result.passed_tests}"
    )

    print(
        f"Failed: {result.failed_tests}"
    )

    print(
        f"Duration: "
        f"{result.execution_time_seconds}s"
    )