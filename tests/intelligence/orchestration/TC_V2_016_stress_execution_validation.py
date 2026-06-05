from validation.safe_execution_engine import (
    execute_governed_action
)

from memory.governance_memory_engine import (
    store_governance_decision,
    build_governance_summary,
    get_repeat_offenders
)


TEST_FILE = "temp_v2_stress_test.py"


def prepare_initial_file():
    """
    Create initial file for rollback testing.
    """

    with open(TEST_FILE, "w", encoding="utf-8") as file:

        file.write(
            "def initial_function():\n"
            "    return 'initial'\n"
        )


def safe_action():
    """
    Valid safe execution.
    """

    with open(TEST_FILE, "w", encoding="utf-8") as file:

        file.write(
            "def safe_function():\n"
            "    return 'safe'\n"
        )


def syntax_failure_action():
    """
    Intentionally broken syntax.
    """

    with open(TEST_FILE, "w", encoding="utf-8") as file:

        file.write(
            "def broken_function(\n"
        )


def runtime_failure_action():
    """
    Simulated runtime failure.
    """

    raise RuntimeError(
        "Simulated governed execution failure."
    )


def fake_v1_handler(finding):

    return {
        "v1_status": "SAFE_V1_EXECUTION"
    }


def print_separator(title):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def run_stress_validation():

    # ---------------------------------------------------
    # TEST 1 — SAFE EXECUTION
    # ---------------------------------------------------

    print_separator("TEST 1 — SAFE EXECUTION")

    prepare_initial_file()

    safe_finding = {
        "file_path": TEST_FILE,
        "function_name": "safe_function",
        "severity": "SAFE",
        "category": "UTILITY"
    }

    result_1 = execute_governed_action(
        finding=safe_finding,
        target_file=TEST_FILE,
        proposed_action=safe_action,
        confidence_score=0.40,
        v1_handler=fake_v1_handler
    )

    print(result_1)

    store_governance_decision(
        file_path=TEST_FILE,
        function_name="safe_function",
        severity="SAFE",
        category="UTILITY",
        decision="APPROVED",
        confidence_score=0.40,
        source="TC_V2_016"
    )

    # ---------------------------------------------------
    # TEST 2 — REVIEW FLOW
    # ---------------------------------------------------

    print_separator("TEST 2 — REVIEW FLOW")

    review_finding = {
        "file_path": TEST_FILE,
        "function_name": "subprocess_handler",
        "severity": "REVIEW",
        "category": "PROCESS_OPERATION"
    }

    result_2 = execute_governed_action(
        finding=review_finding,
        target_file=TEST_FILE,
        proposed_action=safe_action,
        confidence_score=0.90,
        v1_handler=fake_v1_handler
    )

    print(result_2)

    # ---------------------------------------------------
    # TEST 3 — BLOCK FLOW
    # ---------------------------------------------------

    print_separator("TEST 3 — BLOCK FLOW")

    block_finding = {
        "file_path": TEST_FILE,
        "function_name": "dangerous_eval",
        "severity": "BLOCK",
        "category": "DYNAMIC_EXEC"
    }

    result_3 = execute_governed_action(
        finding=block_finding,
        target_file=TEST_FILE,
        proposed_action=safe_action,
        confidence_score=0.95,
        v1_handler=fake_v1_handler
    )

    print(result_3)

    # ---------------------------------------------------
    # TEST 4 — SYNTAX FAILURE
    # ---------------------------------------------------

    print_separator("TEST 4 — SYNTAX FAILURE")

    prepare_initial_file()

    syntax_finding = {
        "file_path": TEST_FILE,
        "function_name": "broken_function",
        "severity": "SAFE",
        "category": "UTILITY"
    }

    result_4 = execute_governed_action(
        finding=syntax_finding,
        target_file=TEST_FILE,
        proposed_action=syntax_failure_action,
        confidence_score=0.50,
        v1_handler=fake_v1_handler
    )

    print(result_4)

    # ---------------------------------------------------
    # TEST 5 — RUNTIME FAILURE
    # ---------------------------------------------------

    print_separator("TEST 5 — RUNTIME FAILURE")

    prepare_initial_file()

    runtime_finding = {
        "file_path": TEST_FILE,
        "function_name": "runtime_failure",
        "severity": "SAFE",
        "category": "UTILITY"
    }

    result_5 = execute_governed_action(
        finding=runtime_finding,
        target_file=TEST_FILE,
        proposed_action=runtime_failure_action,
        confidence_score=0.45,
        v1_handler=fake_v1_handler
    )

    print(result_5)

    # ---------------------------------------------------
    # TEST 6 — REPEAT OFFENDER MEMORY
    # ---------------------------------------------------

    print_separator("TEST 6 — REPEAT OFFENDER MEMORY")

    store_governance_decision(
        file_path=TEST_FILE,
        function_name="safe_function",
        severity="SAFE",
        category="UTILITY",
        decision="APPROVED",
        confidence_score=0.50,
        source="TC_V2_016_REPEAT"
    )

    repeat_offenders = get_repeat_offenders()

    print(repeat_offenders)

    # ---------------------------------------------------
    # TEST 7 — FINAL GOVERNANCE SUMMARY
    # ---------------------------------------------------

    print_separator("TEST 7 — FINAL GOVERNANCE SUMMARY")

    summary = build_governance_summary()

    print(summary)

    # ---------------------------------------------------
    # FINAL STATUS
    # ---------------------------------------------------

    print_separator("FINAL STATUS")

    print("TC_V2_016 STRESS VALIDATION COMPLETED")


if __name__ == "__main__":

    run_stress_validation()