"""
CodeTruth Agent V2
System Integration Testing (SIT) Runner
"""

import pytest
import sys


def run_all_sit_tests():

    print("=" * 60)
    print("RUNNING CODETRUTH V2 SIT")
    print("=" * 60)

    test_files = [
        "tests/test_validation.py",
        "tests/test_rollback.py",
        "tests/test_v1_regression.py",
        "tests/test_memory_recovery.py",
        "tests/test_memory_cleanup.py",
        "tests/test_sit_pipeline.py",
        "tests/test_sit_failure_pipeline.py",
        "tests/test_archive_retention.py"
    ]

    exit_code = pytest.main(test_files)

    print("\n" + "=" * 60)

    if exit_code == 0:

        print("SIT STATUS: PASSED")

    else:

        print("SIT STATUS: FAILED")

    print("=" * 60)

    return exit_code


if __name__ == "__main__":

    result = run_all_sit_tests()

    sys.exit(result)