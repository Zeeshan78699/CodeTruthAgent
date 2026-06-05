from validation.safe_execution_engine import (
    execute_governed_action
)

from memory.governance_memory_engine import (
    store_governance_decision,
    build_governance_summary
)


TEST_FILE = "temp_v2_execution_test.py"


def prepare_initial_file():
    """
    Create initial repository file.

    Required for rollback snapshot testing.
    """

    with open(TEST_FILE, "w", encoding="utf-8") as file:

        file.write(
            "def initial_function():\n"
            "    return 'initial_state'\n"
        )


def fake_safe_action():
    """
    Simulated governed modification.
    """

    with open(TEST_FILE, "w", encoding="utf-8") as file:

        file.write(
            "def generated_function():\n"
            "    return 'safe_execution'\n"
        )


def fake_v1_handler(finding):
    """
    Simulated frozen V1 routing.
    """

    return {
        "v1_status": "SAFE_V1_EXECUTION"
    }


def run_pipeline_test():

    print("\n=== STEP 0 — PREPARE INITIAL FILE ===")

    prepare_initial_file()

    print("Initial repository file created.")

    finding = {
        "file_path": TEST_FILE,
        "function_name": "generated_function",
        "severity": "SAFE",
        "category": "UTILITY"
    }

    print("\n=== STEP 1 — GOVERNED EXECUTION ===")

    execution_result = execute_governed_action(
        finding=finding,
        target_file=TEST_FILE,
        proposed_action=fake_safe_action,
        confidence_score=0.40,
        v1_handler=fake_v1_handler
    )

    print(execution_result)

    print("\n=== STEP 2 — GOVERNANCE MEMORY UPDATE ===")

    store_governance_decision(
        file_path=TEST_FILE,
        function_name="generated_function",
        severity="SAFE",
        category="UTILITY",
        decision="APPROVED",
        confidence_score=0.40,
        source="TC_V2_015"
    )

    print("Governance memory updated.")

    print("\n=== STEP 3 — GOVERNANCE SUMMARY ===")

    summary = build_governance_summary()

    print(summary)

    print("\n=== STEP 4 — FINAL PIPELINE STATUS ===")

    if execution_result.get("execution_status") == "EXECUTED_SUCCESSFULLY":

        print("FULL GOVERNANCE PIPELINE PASSED")

    else:

        print("FULL GOVERNANCE PIPELINE FAILED")


if __name__ == "__main__":

    run_pipeline_test()