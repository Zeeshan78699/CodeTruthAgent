"""
final_resolution_benchmark.py

Purpose:
Final deterministic-resolution benchmark.

FIX: ASSIGNMENT_RESOLVED renamed to ASSIGNMENT_GROUNDWORK and passed
as assignment_groundwork - matches resolution_scorecard.py's fix, so
it's reported for context but no longer summed into "resolved".
"""

import json

from v3.repository_graph.tests.unresolved_pipeline.resolution_scorecard import (
    build_resolution_scorecard
)


BASELINE_UNRESOLVED = 2732

RETURN_FLOW_RESOLVED = 21
CONSTRUCTOR_RESOLVED = 25
FACTORY_RESOLVED = 12
ASSIGNMENT_GROUNDWORK = 479


def build_final_report():
    scorecard = build_resolution_scorecard(
        baseline_unresolved=BASELINE_UNRESOLVED,
        return_flow_resolved=RETURN_FLOW_RESOLVED,
        constructor_resolved=CONSTRUCTOR_RESOLVED,
        factory_resolved=FACTORY_RESOLVED,
        assignment_groundwork=ASSIGNMENT_GROUNDWORK,
    )

    reduction = scorecard["reduction_pct"]

    if reduction >= 50:
        maturity = "high"
    elif reduction >= 25:
        maturity = "medium"
    else:
        maturity = "early"

    report = {
        "baseline_unresolved": scorecard["baseline_unresolved"],
        "resolved": scorecard["resolved"],
        "remaining": scorecard["remaining"],
        "reduction_pct": reduction,
        "maturity": maturity,
        "components": {
            "return_flow": RETURN_FLOW_RESOLVED,
            "constructor": CONSTRUCTOR_RESOLVED,
            "factory": FACTORY_RESOLVED,
            # Context only - not counted as resolved, see resolution_scorecard.py.
            "assignment_groundwork_available": ASSIGNMENT_GROUNDWORK,
        },
    }
    return report


def main():
    report = build_final_report()

    print("=" * 80)
    print("FINAL RESOLUTION BENCHMARK")
    print("=" * 80)
    print(json.dumps(report, indent=2))
    print("=" * 80)

    print()
    print("SUMMARY")
    print("=" * 80)
    print(f"Baseline: {report['baseline_unresolved']:,}")
    print(f"Resolved: {report['resolved']:,}")
    print(f"Remaining: {report['remaining']:,}")
    print(f"Reduction: {report['reduction_pct']}%")
    print(f"Maturity: {report['maturity']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
