"""
resolution_scorecard.py

Purpose:
Single view of all deterministic resolution progress.

FIX: assignment_resolved was being added directly into the "resolved"
total, even though it's not a count of resolved unresolved-entries at
all - it's the size of the assignment table (every "x = y" statement
found in the codebase), a measure of available groundwork, not an
outcome. Folding it into "resolved" inflated the reported number from
a real 58 to a false 537 (19.66% vs the real ~2%). It's now tracked
separately and reported for context, but never summed into the
resolved/reduction figures.
"""

import json


class ResolutionScorecard:

    def __init__(self):
        self.metrics = {}

    def add_metric(self, name, value):
        self.metrics[name] = value

    def build(self):
        baseline = self.metrics.get("baseline_unresolved", 0)
        resolved = self.metrics.get("resolved", 0)
        remaining = max(0, baseline - resolved)

        reduction_pct = 0.0
        if baseline:
            reduction_pct = round((resolved / baseline) * 100, 2)

        return {
            "baseline_unresolved": baseline,
            "resolved": resolved,
            "remaining": remaining,
            "reduction_pct": reduction_pct,
            "details": self.metrics,
        }


def build_resolution_scorecard(
    baseline_unresolved,
    return_flow_resolved=0,
    constructor_resolved=0,
    factory_resolved=0,
    assignment_groundwork=0,
):
    """
    FIX: parameter renamed from assignment_resolved to
    assignment_groundwork to make clear what it actually measures -
    and it is NOT included in total_resolved below.
    """
    scorecard = ResolutionScorecard()

    scorecard.add_metric("baseline_unresolved", baseline_unresolved)
    scorecard.add_metric("return_flow_resolved", return_flow_resolved)
    scorecard.add_metric("constructor_resolved", constructor_resolved)
    scorecard.add_metric("factory_resolved", factory_resolved)

    # Context only - NOT a resolved count, never summed in.
    scorecard.add_metric("assignment_groundwork", assignment_groundwork)

    total_resolved = (
        return_flow_resolved
        + constructor_resolved
        + factory_resolved
    )

    scorecard.add_metric("resolved", total_resolved)

    return scorecard.build()


if __name__ == "__main__":
    report = build_resolution_scorecard(
        baseline_unresolved=2732,
        return_flow_resolved=21,
        constructor_resolved=25,
        factory_resolved=12,
        assignment_groundwork=479,
    )
    print(json.dumps(report, indent=2))
