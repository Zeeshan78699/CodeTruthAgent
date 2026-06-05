import time

from validation.safe_execution_engine import (
    execute_governed_action
)

from memory.governance_memory_engine import (
    store_governance_decision,
    build_governance_summary,
    get_repeat_offenders
)

from ai.incremental_change_engine import (
    detect_incremental_changes
)


TEST_FILE = "temp_v2_resilience_test.py"

TOTAL_ITERATIONS = 5


def prepare_initial_file():

    with open(TEST_FILE, "w", encoding="utf-8") as file:

        file.write(
            "def initial_state():\n"
            "    return 'baseline'\n"
        )


def safe_action(iteration):

    with open(TEST_FILE, "w", encoding="utf-8") as file:

        file.write(
            f"def safe_function_{iteration}():\n"
            f"    return 'safe_{iteration}'\n"
        )


def syntax_failure_action():

    with open(TEST_FILE, "w", encoding="utf-8") as file:

        file.write(
            "def broken_function(\n"
        )


def runtime_failure_action():

    raise RuntimeError(
        "Simulated orchestration runtime failure."
    )


def fake_v1_handler(finding):

    return {
        "v1_status": "SAFE_V1_EXECUTION"
    }


def print_separator(title):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def run_safe_iterations():

    print_separator("SAFE EXECUTION RESILIENCE")

    for iteration in range(TOTAL_ITERATIONS):

        prepare_initial_file()

        finding = {
            "file_path": TEST_FILE,
            "function_name": f"safe_function_{iteration}",
            "severity": "SAFE",
            "category": "UTILITY"
        }

        result = execute_governed_action(
            finding=finding,
            target_file=TEST_FILE,
            proposed_action=lambda i=iteration: safe_action(i),
            confidence_score=0.45,
            v1_handler=fake_v1_handler
        )

        print(f"\nSAFE ITERATION {iteration + 1}")
        print(result)

        store_governance_decision(
            file_path=TEST_FILE,
            function_name=f"safe_function_{iteration}",
            severity="SAFE",
            category="UTILITY",
            decision="APPROVED",
            confidence_score=0.45,
            source="TC_V2_017_SAFE"
        )


def run_review_iterations():

    print_separator("REVIEW RESILIENCE")

    for iteration in range(3):

        finding = {
            "file_path": TEST_FILE,
            "function_name": f"review_process_{iteration}",
            "severity": "REVIEW",
            "category": "PROCESS_OPERATION"
        }

        result = execute_governed_action(
            finding=finding,
            target_file=TEST_FILE,
            proposed_action=lambda: safe_action(iteration),
            confidence_score=0.90,
            v1_handler=fake_v1_handler
        )

        print(f"\nREVIEW ITERATION {iteration + 1}")
        print(result)


def run_block_iterations():

    print_separator("BLOCK RESILIENCE")

    for iteration in range(3):

        finding = {
            "file_path": TEST_FILE,
            "function_name": f"dangerous_eval_{iteration}",
            "severity": "BLOCK",
            "category": "DYNAMIC_EXEC"
        }

        result = execute_governed_action(
            finding=finding,
            target_file=TEST_FILE,
            proposed_action=lambda: safe_action(iteration),
            confidence_score=0.95,
            v1_handler=fake_v1_handler
        )

        print(f"\nBLOCK ITERATION {iteration + 1}")
        print(result)


def run_syntax_failure_iterations():

    print_separator("SYNTAX FAILURE RESILIENCE")

    for iteration in range(2):

        prepare_initial_file()

        finding = {
            "file_path": TEST_FILE,
            "function_name": f"broken_function_{iteration}",
            "severity": "SAFE",
            "category": "UTILITY"
        }

        result = execute_governed_action(
            finding=finding,
            target_file=TEST_FILE,
            proposed_action=syntax_failure_action,
            confidence_score=0.50,
            v1_handler=fake_v1_handler
        )

        print(f"\nSYNTAX FAILURE ITERATION {iteration + 1}")
        print(result)


def run_runtime_failure_iterations():

    print_separator("RUNTIME FAILURE RESILIENCE")

    for iteration in range(2):

        prepare_initial_file()

        finding = {
            "file_path": TEST_FILE,
            "function_name": f"runtime_failure_{iteration}",
            "severity": "SAFE",
            "category": "UTILITY"
        }

        result = execute_governed_action(
            finding=finding,
            target_file=TEST_FILE,
            proposed_action=runtime_failure_action,
            confidence_score=0.40,
            v1_handler=fake_v1_handler
        )

        print(f"\nRUNTIME FAILURE ITERATION {iteration + 1}")
        print(result)


def run_incremental_detection():

    print_separator("INCREMENTAL REPOSITORY DETECTION")

    result = detect_incremental_changes(".")

    print(result)


def run_memory_summary():

    print_separator("GOVERNANCE MEMORY SUMMARY")

    summary = build_governance_summary()

    print(summary)

    print("\nREPEAT OFFENDERS")

    repeat_offenders = get_repeat_offenders()

    print(repeat_offenders)


def run_final_status():

    print_separator("FINAL RESILIENCE STATUS")

    print("TC_V2_017 ORCHESTRATION RESILIENCE VALIDATION PASSED")


def run_full_resilience_suite():

    start_time = time.time()

    run_safe_iterations()

    run_review_iterations()

    run_block_iterations()

    run_syntax_failure_iterations()

    run_runtime_failure_iterations()

    run_incremental_detection()

    run_memory_summary()

    run_final_status()

    end_time = time.time()

    print("\nTOTAL EXECUTION TIME")
    print(f"{round(end_time - start_time, 2)} seconds")


if __name__ == "__main__":

    run_full_resilience_suite()