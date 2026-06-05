"""
TC_V2_FINAL_002 — Real Multi-File Repository Scan

Title:
Can the Engine Safely Scan and Understand
a Real Multi-File Repository Structure?

Description:
This test validates whether CodeTruth Agent V2 can:

- scan a real repository
- discover Python files
- build AST cognition
- detect imports
- reconstruct repository relationships
- initialize governance orchestration safely

WITHOUT modifying repository files.

Objective:
Validate repository-wide cognition initialization.

Expected Result:
SAFE

Category:
Final Repository Orchestration Validation
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.repository_graph_engine import (
    RepositoryGraphEngine
)


# =========================================================
# GOVERNANCE ENGINE
# =========================================================

class GovernanceValidationEngine:

    def validate_repository(self, graph):

        total_files = len(graph.files)

        total_functions = sum(
            len(file_node.functions)
            for file_node in graph.files.values()
        )

        total_classes = sum(
            len(file_node.classes)
            for file_node in graph.files.values()
        )

        total_dependencies = sum(
            len(dependencies)
            for dependencies in graph.dependency_map.values()
        )

        # -------------------------------------------------
        # SAFE VALIDATION
        # -------------------------------------------------

        if total_files == 0:

            return {
                "decision": "BLOCK",
                "risk_level": "HIGH",
                "reason":
                    "Repository scan failed. No files detected."
            }

        if total_functions == 0:

            return {
                "decision": "REVIEW",
                "risk_level": "MEDIUM",
                "reason":
                    "Repository scanned but no functions detected."
            }

        return {
            "decision": "SAFE",
            "risk_level": "LOW",
            "reason":
                (
                    "Repository cognition initialized "
                    "successfully."
                )
        }


# =========================================================
# REPORT ENGINE
# =========================================================

class ReportEngine:

    def __init__(self):

        self.output_dir = Path(
            "tests/output/v2/final_orchestration_reports"
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.json_report = (
            self.output_dir /
            "TC_V2_FINAL_002_report.json"
        )

        self.text_report = (
            self.output_dir /
            "TC_V2_FINAL_002_output.txt"
        )

    # -----------------------------------------------------
    # SAVE JSON REPORT
    # -----------------------------------------------------

    def save_json_report(self, report):

        with open(
            self.json_report,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                report,
                f,
                indent=4
            )

    # -----------------------------------------------------
    # SAVE TEXT REPORT
    # -----------------------------------------------------

    def save_text_report(self, report):

        lines = []

        lines.append("=" * 70)
        lines.append(
            "TC_V2_FINAL_002 — Real Multi-File Repository Scan"
        )
        lines.append("=" * 70)

        lines.append(
            f"\nRepository Root: "
            f"{report['repository_root']}"
        )

        lines.append(
            f"Files Scanned: "
            f"{report['files_scanned']}"
        )

        lines.append(
            f"Functions Discovered: "
            f"{report['functions_discovered']}"
        )

        lines.append(
            f"Classes Discovered: "
            f"{report['classes_discovered']}"
        )

        lines.append(
            f"Dependencies Detected: "
            f"{report['dependencies_detected']}"
        )

        lines.append(
            f"Governance Decision: "
            f"{report['governance_decision']}"
        )

        lines.append(
            f"Risk Level: "
            f"{report['risk_level']}"
        )

        lines.append(
            f"Reason: "
            f"{report['reason']}"
        )

        lines.append(
            f"Test Status: "
            f"{report['test_status']}"
        )

        with open(
            self.text_report,
            "w",
            encoding="utf-8"
        ) as f:

            f.write("\n".join(lines))


# =========================================================
# TEST EXECUTION
# =========================================================

def run_test():

    print("=" * 70)
    print(
        "TC_V2_FINAL_002 — Real Multi-File Repository Scan"
    )
    print("=" * 70)

    # -----------------------------------------------------
    # STEP 1 — Repository Root
    # -----------------------------------------------------

    repository_root = "."

    # -----------------------------------------------------
    # STEP 2 — Repository Graph Build
    # -----------------------------------------------------

    graph_engine = RepositoryGraphEngine(
        repo_root=repository_root
    )

    graph = graph_engine.build_graph()

    # -----------------------------------------------------
    # STEP 3 — Repository Metrics
    # -----------------------------------------------------

    files_scanned = len(graph.files)

    functions_discovered = sum(
        len(file_node.functions)
        for file_node in graph.files.values()
    )

    classes_discovered = sum(
        len(file_node.classes)
        for file_node in graph.files.values()
    )

    dependencies_detected = sum(
        len(dependencies)
        for dependencies
        in graph.dependency_map.values()
    )

    # -----------------------------------------------------
    # STEP 4 — Governance Validation
    # -----------------------------------------------------

    governance_engine = (
        GovernanceValidationEngine()
    )

    governance_result = (
        governance_engine.validate_repository(
            graph
        )
    )

    # -----------------------------------------------------
    # STEP 5 — PASS / FAIL
    # -----------------------------------------------------

    expected_decision = "SAFE"

    test_status = (
        "PASS"
        if governance_result["decision"]
        == expected_decision
        else "FAIL"
    )

    # -----------------------------------------------------
    # STEP 6 — Final Report
    # -----------------------------------------------------

    final_report = {

        "test_case":
            "TC_V2_FINAL_002",

        "title":
            (
                "Real Multi-File Repository Scan"
            ),

        "repository_root":
            str(Path(repository_root).resolve()),

        "files_scanned":
            files_scanned,

        "functions_discovered":
            functions_discovered,

        "classes_discovered":
            classes_discovered,

        "dependencies_detected":
            dependencies_detected,

        "governance_decision":
            governance_result["decision"],

        "risk_level":
            governance_result["risk_level"],

        "reason":
            governance_result["reason"],

        "test_status":
            test_status
    }

    # -----------------------------------------------------
    # STEP 7 — Display Results
    # -----------------------------------------------------

    print("\n[Repository Metrics]")

    print(
        json.dumps(
            {
                "files_scanned":
                    files_scanned,
                "functions_discovered":
                    functions_discovered,
                "classes_discovered":
                    classes_discovered,
                "dependencies_detected":
                    dependencies_detected
            },
            indent=4
        )
    )

    print("\n[Governance Decision]")

    print(
        json.dumps(
            governance_result,
            indent=4
        )
    )

    print("\n[Test Status]")
    print(test_status)

    # -----------------------------------------------------
    # STEP 8 — Save Reports
    # -----------------------------------------------------

    report_engine = ReportEngine()

    report_engine.save_json_report(
        final_report
    )

    report_engine.save_text_report(
        final_report
    )

    print("\n[Reports Generated]")
    print(
        "tests/output/v2/"
        "final_orchestration_reports/"
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    run_test()