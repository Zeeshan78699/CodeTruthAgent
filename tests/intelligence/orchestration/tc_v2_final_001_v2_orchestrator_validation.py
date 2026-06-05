"""
TC_V2_FINAL_001
Full V2 Orchestrator Validation

Objective:

Validate the complete V2 orchestration pipeline:

Repository Graph
↓
Governance
↓
V1 Adapter
↓
Fallback Routing
↓
Memory Update
↓
Reporting

This test validates the REAL
ai.v2_orchestrator implementation.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai.v2_orchestrator import V2Orchestrator


OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "final_orchestration_reports"
)

REPORT_FILE = (
    OUTPUT_DIR
    / "tc_v2_final_001_report.json"
)


def save_report(report):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4
        )


def run_tc_v2_final_001():

    print("\n" + "=" * 70)
    print(
        "TC_V2_FINAL_001"
    )
    print(
        "Full V2 Orchestrator Validation"
    )
    print("=" * 70)

    orchestrator = (
        V2Orchestrator(
            repo_root=Path.cwd()
        )
    )

    result = orchestrator.run()

    passed = (

        result.get(
            "repository_files",
            0
        ) > 0

        and

        result.get(
            "governance_findings",
            0
        ) > 0

        and

        result.get(
            "v1_findings",
            0
        ) > 0

        and

        result.get(
            "memory_updated",
            False
        ) is True

        and

        result.get(
            "status"
        ) == "PASSED"
    )

    report = {

        "test_case":
        "TC_V2_FINAL_001",

        "repository_files":
        result.get(
            "repository_files"
        ),

        "governance_findings":
        result.get(
            "governance_findings"
        ),

        "v1_findings":
        result.get(
            "v1_findings"
        ),

        "safe":
        result.get(
            "safe"
        ),

        "review":
        result.get(
            "review"
        ),

        "block":
        result.get(
            "block"
        ),

        "fallback_triggered":
        result.get(
            "fallback_triggered"
        ),

        "memory_updated":
        result.get(
            "memory_updated"
        ),

        "orchestrator_status":
        result.get(
            "status"
        ),

        "status":
        (
            "PASSED"
            if passed
            else
            "FAILED"
        )
    }

    save_report(report)

    print("\nRESULT")
    print("-" * 70)

    print(
        f"Repository Files: "
        f"{report['repository_files']}"
    )

    print(
        f"Governance Findings: "
        f"{report['governance_findings']}"
    )

    print(
        f"V1 Findings: "
        f"{report['v1_findings']}"
    )

    print(
        f"Fallback Triggered: "
        f"{report['fallback_triggered']}"
    )

    print(
        f"Memory Updated: "
        f"{report['memory_updated']}"
    )

    print(
        f"\nOVERALL STATUS: "
        f"{report['status']}"
    )

    print(
        f"\nReport Saved:"
        f"\n{REPORT_FILE}"
    )

    return report


if __name__ == "__main__":

    run_tc_v2_final_001()