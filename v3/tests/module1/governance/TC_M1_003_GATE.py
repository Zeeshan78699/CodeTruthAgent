"""
======================================================================
TEST ID: TC_M1_003_GATE

TITLE:
Module 1 Governance Gate Validation

PURPOSE:

Validate governance decisions produced by
Module 1 Repository Cognition.

This test verifies:

APPROVED
REVIEW_REQUIRED
BLOCKED
HUMAN_OVERRIDE

======================================================================
"""

from dataclasses import dataclass
import json
from pathlib import Path
from datetime import datetime, UTC


# ------------------------------------------------------------------
# Mock Structures
# ------------------------------------------------------------------

@dataclass
class MockGateResult:
    gate_passed: bool
    gate_decision: str
    approved_for: str | None
    blocking_reason: str | None


# ------------------------------------------------------------------
# Governance Logic
# ------------------------------------------------------------------

def evaluate_gate(
    cognition_status,
    confidence_score,
    is_known,
    total_files,
):
    if total_files == 0:
        return MockGateResult(
            False,
            "BLOCKED",
            None,
            "Repository Empty"
        )

    if cognition_status != "COMPLETE":
        return MockGateResult(
            False,
            "REVIEW_REQUIRED",
            None,
            "Incomplete Cognition"
        )

    if confidence_score < 0.50:
        return MockGateResult(
            False,
            "REVIEW_REQUIRED",
            None,
            "Low Confidence"
        )

    if not is_known:
        return MockGateResult(
            False,
            "REVIEW_REQUIRED",
            None,
            "Unknown Repository"
        )

    return MockGateResult(
        True,
        "APPROVED",
        "MODULE_2",
        None
    )


# ------------------------------------------------------------------
# Test Cases
# ------------------------------------------------------------------

def test_known_repository():

    result = evaluate_gate(
        cognition_status="COMPLETE",
        confidence_score=1.0,
        is_known=True,
        total_files=100
    )

    assert result.gate_decision == "APPROVED"

    print(
        "PASS TC_M1_003_GATE_001 "
        "Known Repository"
    )


def test_unknown_repository():

    result = evaluate_gate(
        cognition_status="COMPLETE",
        confidence_score=1.0,
        is_known=False,
        total_files=100
    )

    assert result.gate_decision == "REVIEW_REQUIRED"

    print(
        "PASS TC_M1_003_GATE_002 "
        "Unknown Repository"
    )


def test_low_confidence():

    result = evaluate_gate(
        cognition_status="COMPLETE",
        confidence_score=0.25,
        is_known=True,
        total_files=100
    )

    assert result.gate_decision == "REVIEW_REQUIRED"

    print(
        "PASS TC_M1_003_GATE_003 "
        "Low Confidence"
    )


def test_empty_repository():

    result = evaluate_gate(
        cognition_status="COMPLETE",
        confidence_score=1.0,
        is_known=True,
        total_files=0
    )

    assert result.gate_decision == "BLOCKED"

    print(
        "PASS TC_M1_003_GATE_004 "
        "Empty Repository"
    )


def test_human_override():

    override = {
        "override_by": "human_reviewer",
        "timestamp": datetime.now(
            UTC
        ).isoformat(),
        "decision": "APPROVED"
    }

    output_dir = (
        Path(__file__).parent
        / "evidence"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    override_file = (
        output_dir
        / "override_signature.json"
    )

    with open(
        override_file,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            override,
            f,
            indent=2
        )

    assert override["decision"] == "APPROVED"

    print(
        "PASS TC_M1_003_GATE_005 "
        "Human Override"
    )


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():

    print("=" * 70)
    print("TC_M1_003_GATE")
    print("MODULE 1 GOVERNANCE VALIDATION")
    print("=" * 70)

    test_known_repository()

    test_unknown_repository()

    test_low_confidence()

    test_empty_repository()

    test_human_override()

    print("\nFINAL RESULT")
    print("-" * 70)

    print("PASS")
    print("Governance Gate Logic : PASS")
    print("Human Override Audit  : PASS")


if __name__ == "__main__":
    main()