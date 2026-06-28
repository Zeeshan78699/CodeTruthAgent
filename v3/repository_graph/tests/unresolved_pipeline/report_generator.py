"""
report_generator.py

Experimental Module 2.5 validation harness.

Purpose:
Generate human-readable and JSON reports from the
resolution pipeline output.

Truth Boundary:
- Reports only facts produced by pipeline
- No interpretation
- No guessing
"""

import json
from pathlib import Path
from typing import Any, Dict


class ReportGenerator:

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def build_report(
        self,
        repo_name: str,
        pipeline_results: Dict[str, Any]
    ) -> Dict[str, Any]:

        return {
            "repo": repo_name,

            "baseline": {
                "unresolved":
                    pipeline_results[
                        "baseline_unresolved"
                    ]
            },

            "cause_breakdown":
                pipeline_results[
                    "classification"
                ],

            "resolver_results":
                pipeline_results[
                    "resolver_results"
                ],

            "final":
                pipeline_results[
                    "final"
                ]
        }

    def save_json_report(
        self,
        repo_name: str,
        report: Dict[str, Any]
    ) -> Path:

        output_file = (
            self.output_dir
            / f"{repo_name}_resolution_report.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                report,
                f,
                indent=2
            )

        return output_file

    def print_console_summary(
        self,
        report: Dict[str, Any]
    ) -> None:

        print("=" * 80)

        print(
            f"Repository: "
            f"{report['repo']}"
        )

        print("-" * 80)

        baseline = (
            report["baseline"]["unresolved"]
        )

        final = (
            report["final"][
                "remaining_unresolved"
            ]
        )

        reduction = (
            report["final"][
                "reduction_pct"
            ]
        )

        print(
            f"Baseline Unresolved: "
            f"{baseline:,}"
        )

        print(
            f"Remaining Unresolved: "
            f"{final:,}"
        )

        print(
            f"Reduction: "
            f"{reduction}%"
        )

        print()

        print("Resolver Results")

        for (
            resolver,
            count
        ) in report[
            "resolver_results"
        ].items():

            print(
                f"  {resolver}: {count:,}"
            )

        print("=" * 80)

    def generate(
        self,
        repo_name: str,
        pipeline_results: Dict[str, Any]
    ) -> Path:

        report = self.build_report(
            repo_name,
            pipeline_results
        )

        self.print_console_summary(
            report
        )

        return self.save_json_report(
            repo_name,
            report
        )


def generate_report(
    repo_name: str,
    pipeline_results: Dict[str, Any],
    output_dir: str
):

    generator = ReportGenerator(
        output_dir
    )

    return generator.generate(
        repo_name,
        pipeline_results
    )