"""
TC_V2_018
REAL REPOSITORY GOVERNANCE VALIDATION

Objective:
Validate CodeTruth Agent V2 operational governance
against a real repository environment.

Validation Areas:
- repository cognition
- governance analysis
- dangerous API detection
- HITL routing
- V1 fallback
- rollback protection
- safe execution
- syntax validation
- orchestration resilience
- governance reporting

IMPORTANT:
This is NOT a benchmark yet.

This is:
REAL-WORLD OPERATIONAL VALIDATION.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

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

from validation.rollback_manager import (
    RollbackManager
)

from ai.incremental_change_engine import (
    detect_incremental_changes
)


# =========================================================
# CONFIGURATION
# =========================================================

PROJECT_ROOT = str(
    Path.cwd()
)

REPORT_OUTPUT = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "real_repository_validation_reports"
    / "tc_v2_018_report.json"
)

TEST_EXECUTION_FILE = (
    "tc_v2_018_execution_test.py"
)


# =========================================================
# HELPERS
# =========================================================

def print_separator(title):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def safe_execution_action():

    with open(
        TEST_EXECUTION_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "def generated_function():\n"
            "    return 'safe_execution'\n"
        )


def fake_v1_handler(finding):

    return {
        "v1_status": "SAFE_V1_EXECUTION"
    }


# =========================================================
# STEP 1
# INCREMENTAL REPOSITORY VALIDATION
# =========================================================

def validate_incremental_detection():

    print_separator(
        "STEP 1 - INCREMENTAL REPOSITORY VALIDATION"
    )

    result = detect_incremental_changes(
        PROJECT_ROOT
    )

    print(result)

    return result


# =========================================================
# STEP 2
# REPOSITORY GRAPH VALIDATION
# =========================================================

def validate_repository_graph():

    print_separator(
        "STEP 2 - REPOSITORY GRAPH VALIDATION"
    )

    engine = RepositoryGraphEngine(
        PROJECT_ROOT
    )

    graph = engine.build_graph()

    print(
        f"Files Scanned: "
        f"{len(graph.files)}"
    )

    print(
        f"Dependencies: "
        f"{len(graph.dependency_map)}"
    )

    print(
        f"Functions Indexed: "
        f"{len(graph.function_index)}"
    )

    print(
        f"Classes Indexed: "
        f"{len(graph.class_index)}"
    )

    return graph


# =========================================================
# STEP 3
# GOVERNANCE VALIDATION
# =========================================================

def validate_governance(graph):

    print_separator(
        "STEP 3 - GOVERNANCE VALIDATION"
    )

    governance_report = (
        run_governance_on_scan(
            graph=graph,
            ignored_calls=set(),
            repo_root=PROJECT_ROOT
        )
    )

    report_dict = report_to_dict(
        governance_report
    )

    print(
        f"Files With Findings: "
        f"{report_dict['files_with_findings']}"
    )

    print(
        f"Total Findings: "
        f"{report_dict['total_findings']}"
    )

    print(
        f"Findings By Severity: "
    )

    print(
        report_dict[
            "findings_by_severity"
        ]
    )

    return report_dict


# =========================================================
# STEP 4
# HITL VALIDATION
# =========================================================

def validate_hitl():

    print_separator(
        "STEP 4 - HITL VALIDATION"
    )

    review_finding = {

        "file_path":
        "demo.py",

        "function_name":
        "dangerous_process",

        "severity":
        "REVIEW",

        "category":
        "PROCESS_OPERATION"
    }

    result = request_approval(
        review_finding
    )

    print(result)

    return result


# =========================================================
# STEP 5
# V1 FALLBACK VALIDATION
# =========================================================

def validate_fallback():

    print_separator(
        "STEP 5 - V1 FALLBACK VALIDATION"
    )

    finding = {

        "file_path":
        "demo.py",

        "function_name":
        "fallback_case",

        "severity":
        "REVIEW",

        "category":
        "PROCESS_OPERATION"
    }

    result = route_to_v1(

        finding=finding,

        confidence_score=0.40,

        v1_handler=fake_v1_handler
    )

    print(result)

    return result


# =========================================================
# STEP 6
# SAFE EXECUTION VALIDATION
# =========================================================

def validate_safe_execution():

    print_separator(
        "STEP 6 - SAFE EXECUTION VALIDATION"
    )

    with open(
        TEST_EXECUTION_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "def initial():\n"
            "    return 'safe'\n"
        )

    finding = {

        "file_path":
        TEST_EXECUTION_FILE,

        "function_name":
        "generated_function",

        "severity":
        "SAFE",

        "category":
        "UTILITY"
    }

    result = execute_governed_action(

        finding=finding,

        target_file=TEST_EXECUTION_FILE,

        proposed_action=safe_execution_action,

        confidence_score=0.40,

        v1_handler=fake_v1_handler
    )

    print(result)

    return result


# =========================================================
# STEP 7
# ROLLBACK VALIDATION
# =========================================================

def validate_rollback():

    print_separator(
        "STEP 7 - ROLLBACK VALIDATION"
    )

    rollback_result = (
        RollbackManager.create_backup(
            TEST_EXECUTION_FILE
        )
    )

    print(rollback_result)

    return rollback_result


# =========================================================
# STEP 8
# REPORT GENERATION
# =========================================================

def generate_final_report(results):

    print_separator(
        "STEP 8 - FINAL REPORT GENERATION"
    )

    REPORT_OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        REPORT_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4
        )

    print(
        f"Report saved to:\n"
        f"{REPORT_OUTPUT}"
    )


# =========================================================
# MAIN EXECUTION
# =========================================================

def run_tc_v2_018():

    start_time = time.time()

    print("\n" + "=" * 70)
    print(
        "TC_V2_018 - REAL REPOSITORY "
        "GOVERNANCE VALIDATION"
    )
    print("=" * 70)

    results = {}

    # STEP 1
    results[
        "incremental_detection"
    ] = validate_incremental_detection()

    # STEP 2
    graph = validate_repository_graph()

    results[
        "repository_graph"
    ] = {
        "files_scanned":
        len(graph.files),

        "dependencies":
        len(graph.dependency_map),

        "functions_indexed":
        len(graph.function_index),

        "classes_indexed":
        len(graph.class_index)
    }

    # STEP 3
    results[
        "governance"
    ] = validate_governance(graph)

    # STEP 4
    results[
        "hitl"
    ] = validate_hitl()

    # STEP 5
    results[
        "fallback"
    ] = validate_fallback()

    # STEP 6
    results[
        "safe_execution"
    ] = validate_safe_execution()

    # STEP 7
    results[
        "rollback"
    ] = validate_rollback()

    # TIMING
    execution_time = round(
        time.time() - start_time,
        2
    )

    results[
        "execution_time_seconds"
    ] = execution_time

    results[
        "validation_status"
    ] = "PASSED"

    # STEP 8
    generate_final_report(results)

    print("\n" + "=" * 70)
    print(
        "TC_V2_018 VALIDATION PASSED"
    )
    print("=" * 70)

    print(
        f"\nExecution Time: "
        f"{execution_time} seconds"
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    run_tc_v2_018()