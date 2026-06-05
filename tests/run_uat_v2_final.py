"""
CodeTruth Agent V2

FINAL UAT RUNNER

Objective:

Execute all validated V2 orchestration
and safety test cases in one run.

Expected:

ALL TESTS PASSED
"""

from __future__ import annotations

import importlib
import time


# =========================================================
# TEST SUITE
# =========================================================

TEST_MODULES = [

    # -----------------------------------------
    # PATCH WORKFLOW
    # -----------------------------------------

    (
        "TC_V2_024",
        "tests.intelligence.orchestration.tc_v2_024_real_controlled_file_modification",
        "run_tc_v2_024"
    ),

    (
        "TC_V2_025",
        "tests.intelligence.orchestration.tc_v2_025_review_rejection_path",
        "run_tc_v2_025"
    ),

    (
        "TC_V2_026",
        "tests.intelligence.orchestration.tc_v2_026_block_path",
        "run_tc_v2_026"
    ),

    (
        "TC_V2_027",
        "tests.intelligence.orchestration.tc_v2_027_risk_classification_engine",
        "run_tc_v2_027"
    ),

    (
        "TC_V2_028",
        "tests.intelligence.orchestration.tc_v2_028_risk_engine_integration",
        "run_tc_v2_028"
    ),

    (
        "TC_V2_029",
        "tests.intelligence.orchestration.tc_v2_029_patch_validation_risk_integration",
        "run_tc_v2_029"
    ),

    (
        "TC_V2_030",
        "tests.intelligence.orchestration.tc_v2_030_test_execution_engine",
        "run_tc_v2_030"
    ),

    (
        "TC_V2_031",
        "tests.intelligence.orchestration.tc_v2_031_patch_test_rollback_integration",
        "run_tc_v2_031"
    ),

    (
        "TC_V2_032",
        "tests.intelligence.orchestration.tc_v2_032_real_patch_workflow_orchestrator",
        "run_tc_v2_032"
    ),
]


# =========================================================
# EXECUTION
# =========================================================

def run_uat_v2_final():

    print("=" * 70)
    print("CODETRUTH AGENT V2 FINAL UAT")
    print("=" * 70)

    start_time = time.time()

    passed = 0
    failed = 0

    results = []

    for (

        test_name,
        module_path,
        function_name

    ) in TEST_MODULES:

        print(f"\nRunning {test_name}")
        print("-" * 70)

        try:

            module = importlib.import_module(
                module_path
            )

            test_function = getattr(
                module,
                function_name
            )

            report = test_function()

            status = (
                report
                .get(
                    "summary",
                    {}
                )
                .get(
                    "status",
                    "FAILED"
                )
            )

            if status == "PASSED":

                passed += 1

                print(
                    f"{test_name}: PASSED"
                )

            else:

                failed += 1

                print(
                    f"{test_name}: FAILED"
                )

            results.append({

                "test":
                test_name,

                "status":
                status
            })

        except Exception as exc:

            failed += 1

            print(
                f"{test_name}: FAILED"
            )

            print(
                f"ERROR: {exc}"
            )

            results.append({

                "test":
                test_name,

                "status":
                "FAILED",

                "error":
                str(exc)
            })

    duration = round(
        time.time() - start_time,
        2
    )

    print("\n" + "=" * 70)
    print("FINAL UAT SUMMARY")
    print("=" * 70)

    print(
        f"Total Tests : "
        f"{len(TEST_MODULES)}"
    )

    print(
        f"Passed      : "
        f"{passed}"
    )

    print(
        f"Failed      : "
        f"{failed}"
    )

    print(
        f"Duration    : "
        f"{duration}s"
    )

    if failed == 0:

        print(
            "\nUAT STATUS: PASSED"
        )

    else:

        print(
            "\nUAT STATUS: FAILED"
        )

    return {

        "passed":
        passed,

        "failed":
        failed,

        "results":
        results
    }


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    run_uat_v2_final()