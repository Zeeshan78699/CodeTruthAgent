"""
CodeTruth Agent V2
Central UAT Runner
"""

import pytest
import sys


def run_all_uat_tests():

    print("=" * 60)
    print("RUNNING CODETRUTH V2 UAT")
    print("=" * 60)

    test_files = [
        "tests/test_validation.py",
        "tests/test_rollback.py",
        "tests/test_v1_regression.py",
        "tests/test_memory_recovery.py",
        "tests/test_memory_cleanup.py",
        "tests/test_archive_retention.py"
    ]

    exit_code = pytest.main(test_files)

    print("\n" + "=" * 60)

    if exit_code == 0:

        print("UAT STATUS: PASSED")

    else:

        print("UAT STATUS: FAILED")

    print("=" * 60)

    return exit_code


if __name__ == "__main__":

    result = run_all_uat_tests()

    sys.exit(result)