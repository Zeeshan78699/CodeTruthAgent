"""
CodeTruth Agent V2
V1 Adapter

Safe V1 Wrapper

Purpose:
- Expose V1 findings to V2
- Read-only operation
- No file modifications
- No approvals
- No memory updates
- Progress visibility
"""

from __future__ import annotations

import traceback

from core.project_scanner import get_python_files
from core.parser import extract_functions_from_files
from core.duplicate_detector import find_duplicates
from core.quality_checker import compare_functions
from core.merge_advisor import suggest_merge
from core.risk_analyzer import analyze_risk


class V1Adapter:

    def __init__(
        self,
        project_path=".",
        max_files=None
    ):
        self.project_path = project_path
        self.max_files = max_files

    # =====================================================
    # MAIN ANALYSIS
    # =====================================================

    def run_analysis(self):

        import time

        findings = []

        print("\n[V1Adapter] STEP 1 - Scanning Files")

        start_time = time.time()

        python_files = get_python_files(
            self.project_path
        )

        if self.max_files:
            python_files = python_files[
                :self.max_files
            ]

        print(
            f"[V1Adapter] Files Found: "
            f"{len(python_files)}"
        )

        print(
            "[V1Adapter] STEP 2 - "
            "Extracting Functions"
        )

        functions = (
            extract_functions_from_files(
                python_files
            )
        )

        print(
            f"[V1Adapter] Functions Found: "
            f"{len(functions)}"
        )

        print(
            "[V1Adapter] STEP 3 - "
            "Running Duplicate Detector"
        )

        duplicate_start = time.time()

        duplicates = find_duplicates(
            functions
        )

        duplicate_time = (
            time.time() - duplicate_start
        )

        print(
            f"[V1Adapter] Duplicates Found: "
            f"{len(duplicates)}"
        )

        print(
            f"[V1Adapter] Duplicate Detection Time: "
            f"{duplicate_time:.2f}s"
        )

        print(
            "[V1Adapter] STEP 4 - "
            "Building Findings"
        )

        for index, duplicate in enumerate(
            duplicates,
            start=1
        ):

            try:

                print(
                    f"\n[V1Adapter] Processing "
                    f"Finding "
                    f"{index}/{len(duplicates)}"
                )

                f1 = duplicate["function_1"]
                f2 = duplicate["function_2"]

                print(
                    f"[V1Adapter] "
                    f"{f1} <-> {f2}"
                )

                func1 = next(
                    f for f in functions
                    if f["name"] == f1
                )

                func2 = next(
                    f for f in functions
                    if f["name"] == f2
                )

                print(
                    "[V1Adapter] "
                    "compare_functions"
                )

                best_function, reasons = (
                    compare_functions(
                        func1,
                        func2
                    )
                )

                print(
                    "[V1Adapter] "
                    "suggest_merge"
                )

                merge_plan = suggest_merge(
                    func1,
                    func2,
                    best_function,
                    duplicate
                )

                print(
                    "[V1Adapter] "
                    "analyze_risk"
                )

                risk_start = time.time()

                risk_level, risk_reason = (
                    analyze_risk(
                        func1["file"],
                        merge_plan["remove"],
                        duplicate
                    )
                )

                risk_time = (
                    time.time() - risk_start
                )

                print(
                    f"[V1Adapter] "
                    f"Risk Analysis Time: "
                    f"{risk_time:.2f}s"
                )

                findings.append({

                    "function_1": f1,
                    "function_2": f2,

                    "file_1":
                    func1["file"],

                    "file_2":
                    func2["file"],

                    "similarity":
                    duplicate.get(
                        "similarity"
                    ),

                    "duplicate_type":
                    duplicate.get(
                        "duplicate_type"
                    ),

                    "risk_level":
                    risk_level,

                    "risk_reason":
                    risk_reason,

                    "best_function":
                    best_function,

                    "merge_allowed":
                    merge_plan.get(
                    "merge_allowed"
                    ),

                    "action":
                    merge_plan.get(
                        "action"
                    )
                })

                print(
                    "[V1Adapter] "
                    "completed"
                )

            except Exception as ex:

                print(
                    f"[V1Adapter] "
                    f"Finding Build Error: "
                    f"{ex}"
                )

        total_time = (
            time.time() - start_time
        )

        print(
            "\n[V1Adapter] Analysis Completed"
        )

        print(
            f"[V1Adapter] Total Time: "
            f"{total_time:.2f}s"
        )

        return findings

    # =====================================================
    # SUMMARY
    # =====================================================

    def get_summary(self):

        findings = self.run_analysis()

        return {

            "files_scanned":
            len(
                get_python_files(
                    self.project_path
                )
            ),

            "duplicates_found":
            len(findings),

            "findings":
            findings
        }


# =========================================================
# MANUAL TEST
# =========================================================

if __name__ == "__main__":

    try:

        print(
            "\n=================================================="
        )
        print(
            "V1 ADAPTER VALIDATION"
        )
        print(
            "=================================================="
        )

        adapter = V1Adapter(

            project_path=".",

            # Safety limit
            max_files=25
        )

        result = (
            adapter.get_summary()
        )

        print(
            "\n=================================================="
        )
        print(
            "SUMMARY"
        )
        print(
            "=================================================="
        )

        print(
            f"Files Scanned: "
            f"{result['files_scanned']}"
        )

        print(
            f"Duplicates Found: "
            f"{result['duplicates_found']}"
        )

        print(
            "\nValidation PASSED"
        )

    except Exception as ex:

        print(
            "\n[V1Adapter] FAILED"
        )

        print(str(ex))

        print(
            traceback.format_exc()
        )