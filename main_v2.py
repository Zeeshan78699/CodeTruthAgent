""""
CodeTruth Agent V2 Entry Point

This file starts V2 safely.
V1 main.py remains untouched.
"""

import os
from ai.patch_generation_engine import PatchGenerationEngine
from ai.patch_validation_engine import PatchValidationEngine

# ---------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------
# IMPORTS
# ---------------------------------------------------

from ai.ai_interface import AIInterface

from ai.test_execution_engine import (
    TestExecutionEngine
)

from ai.repository_graph_engine import (
    RepositoryGraphEngine
)

from ai.governance_wiring import (
    run_governance_on_scan,
    report_to_dict
)

from validation.approval_engine import (
    request_approval
)

from ai.fallback_orchestrator import (
    route_to_v1
)

from validation.safe_execution_engine import (
    execute_governed_action
)

from ai.incremental_change_engine import (
    detect_incremental_changes
)

from validation.syntax_validator import (
    SyntaxValidator
)

from memory.memory_store_v2 import (
    MemoryStoreV2
)

from reporting.report_generator import (
    ReportGenerator
)

from validation.rollback_manager import (
    RollbackManager
)


# ---------------------------------------------------
# MAIN V2 DEMO PIPELINE
# ---------------------------------------------------

def run_v2_demo():

    print("=" * 60)
    print("CodeTruth Agent V2 - Phase 1 AI Gateway Test")
    print("=" * 60)

    # ===================================================
    # AI GATEWAY TEST
    # ===================================================

    print("\nAI Gateway Result:")
    print("-" * 60)

    # IMPORTANT:
    # Set to False for normal fallback testing
    # Set to True for AI failure injection testing
    ai_gateway = AIInterface(ai_enabled=False)

    prompt = """
    Analyze this function safely:

    def add_numbers(a, b):
        return a + b
    """

    result = ai_gateway.analyze_text(prompt)

    for key, value in result.items():
        print(f"{key}: {value}")

    print("-" * 60)
    print("Phase 1 test completed safely.")

    # ===================================================
    # SYNTAX VALIDATION TEST
    # ===================================================

    print("\nSyntax Validation Test:")
    print("-" * 60)

    # SAFE TEST:
    # sample_code = '''
    # def hello():
    #     print("Hello World")
    # '''

    # FAILURE TEST:
    sample_code = """
def hello(
    print("Broken Code")
"""

    validation_result = SyntaxValidator.validate_python_code(
        sample_code
    )

    for key, value in validation_result.items():
        print(f"{key}: {value}")

    print("-" * 60)
    print("Validation phase completed safely.")

    # ===================================================
    # MEMORY TEST
    # ===================================================

    print("\nMemory System Test:")
    print("-" * 60)

    memory = MemoryStoreV2()

    memory.store_approved_decision({
        "decision": "Safe merge approved",
        "risk_level": "LOW"
    })

    memory_data = memory.get_memory()

    print(memory_data)

    print("-" * 60)
    print("Memory phase completed safely.")

    # ===================================================
    # REPORTING TEST
    # ===================================================

    report_data = {
        "ai_gateway": result,
        "validation": validation_result,
        "memory": memory_data
    }

    print("\nReporting Test:")
    print("-" * 60)

    ReportGenerator.generate_console_report(
        report_data
    )

    print("Reporting phase completed safely.")

    # ===================================================
    # ROLLBACK MANAGER TEST
    # ===================================================

    print("\nRollback Manager Test:")
    print("-" * 60)

    test_file = "sample_test_file.txt"

    try:

        # CREATE BACKUP
        backup_result = RollbackManager.create_backup(
            test_file
        )

        print("Backup Result:")
        print(backup_result)

        # SIMULATE FILE MODIFICATION
        with open(test_file, "w", encoding="utf-8") as file:
            file.write("Modified Unsafe Content")

        print("\nFile modified successfully.")

        # RESTORE BACKUP
        restore_result = RollbackManager.restore_backup(
            backup_result["backup_path"],
            test_file
        )

        print("\nRestore Result:")
        print(restore_result)

        # VERIFY RESTORED CONTENT
        with open(test_file, "r", encoding="utf-8") as file:
            restored_content = file.read()

        print("\nRestored File Content:")
        print(restored_content)

    except Exception as exc:

        print("\nRollback Test Failed:")
        print(str(exc))

    print("-" * 60)
    print("Rollback phase completed safely.")

    # ===================================================
    # INCREMENTAL REPOSITORY DETECTION TEST
    # ===================================================

    print("\nIncremental Repository Detection Test:")
    print("-" * 60)

    try:

        incremental_result = detect_incremental_changes(
            PROJECT_ROOT
        )

        print("Incremental Scan Result:")
        print(incremental_result)

    except Exception as exc:

        print("\nIncremental Detection Failed:")
        print(str(exc))

    print("-" * 60)
    print("Incremental detection phase completed safely.")
    
    # ===================================================
    # GOVERNANCE ORCHESTRATION TEST
    # ===================================================

    print("\nGovernance Orchestration Test:")
    print("-" * 60)

    try:
        
        graph_engine = RepositoryGraphEngine(
            PROJECT_ROOT
        )

        graph = graph_engine.build_graph()

        governance_report = run_governance_on_scan(
            graph=graph,
            ignored_calls=set(),
            repo_root=PROJECT_ROOT
        )

        governance_findings = report_to_dict(
            governance_report
        )

        print(
            f"Governance Findings: "
            f"{len(governance_findings)}"
        )

        if governance_findings:
            
            finding = {
                "file_path": "main_v2.py",
                "function_name": "run_v2_demo",
                "severity": "REVIEW",
                "category": "PROCESS_OPERATION"
            }

            print("\nSample Governance Finding:")
            print(finding)

            # -------------------------------------------
            # APPROVAL ROUTING
            # -------------------------------------------

            approval_result = request_approval(
                finding
            )

            print("\nApproval Result:")
            print(approval_result)

            # -------------------------------------------
            # FALLBACK ROUTING
            # -------------------------------------------

            fallback_result = route_to_v1(
                finding=finding,
                confidence_score=0.40,
                v1_handler=lambda x: {
                    "v1_status": "SAFE_V1_EXECUTION"
                }
            )

            print("\nFallback Result:")
            print(fallback_result)

            # -------------------------------------------
            # SAFE EXECUTION TEST
            # -------------------------------------------

            test_execution_file = "v2_execution_test.py"

            with open(
                test_execution_file,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(
                    "def initial():\n"
                    "    return 'safe'\n"
                )

            def safe_execution_action():

                with open(
                    test_execution_file,
                    "w",
                    encoding="utf-8"
                ) as file:

                    file.write(
                        "def governed_execution():\n"
                        "    return 'executed'\n"
                    )

            execution_result = execute_governed_action(
                finding={
                    "file_path": test_execution_file,
                    "function_name": "governed_execution",
                    "severity": "SAFE",
                    "category": "UTILITY"
                },
                target_file=test_execution_file,
                proposed_action=safe_execution_action,
                confidence_score=0.40,
                v1_handler=lambda x: {
                    "v1_status": "SAFE_V1_EXECUTION"
                }
            )

            print("\nGoverned Execution Result:")
            print(execution_result)
            
            
            # -------------------------------------------
            # TEST EXECUTION ENGINE
            # -------------------------------------------

            test_engine = TestExecutionEngine()

            test_result = test_engine.execute_tests(
                command="pytest -q",
                working_directory=PROJECT_ROOT
            )

            print("\nTest Execution Result:")
            print(test_result)

            if not test_result.success:
                

                print(
                    "\nTests Failed - Rollback Recommended"
                )

        else:

            print(
                "No governance findings detected."
            )

    except Exception as exc:

        print("\nGovernance Orchestration Failed:")
        print(str(exc))

    print("-" * 60)
    print(
        "Governance orchestration phase "
        "completed safely."
    )

    # ===================================================
    # FINAL STATUS
    # ===================================================

    print("\n" + "=" * 60)
    print("CodeTruth Agent V2 Pipeline Completed Safely")
    print("=" * 60)
    
    # ---------------------------------------------------
    # REAL PATCH WORKFLOW
    # ---------------------------------------------------

    def run_real_patch_workflow():

        print("\n" + "=" * 60)
        print("REAL PATCH WORKFLOW")
        print("=" * 60)

        # workflow code here

# ---------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------

if __name__ == "__main__":

    run_v2_demo()
    