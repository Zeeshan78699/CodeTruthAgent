"""
========================================================================
gate_validator.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITY:
    V3-003 Repository Understanding Gate

Fixes TC_M1_001 gap: cognition_status = COMPLETE confirms gate
passed, but no dedicated gate detail field existed.

V3-003 RULE:
    Build repository-wide understanding BEFORE any modification
    is attempted. This gate enforces that rule by checking that
    all required pre-conditions are met.

GATE DECISIONS:
    APPROVED          — all checks passed, safe to proceed to Module 2
    REVIEW_REQUIRED   — understanding is partial, human review needed
    BLOCKED           — critical checks failed, must not proceed
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GateCheckResult:
    check_name:  str
    passed:      bool
    detail:      str


@dataclass
class GateValidationResult:
    gate_passed:     bool
    gate_decision:   str                  # "APPROVED" | "REVIEW_REQUIRED" | "BLOCKED"
    checks:          list[GateCheckResult]
    approved_for:    str                  # "MODULE_2" | "NONE"
    blocking_reason: Optional[str]        # populated if BLOCKED


class GateValidator:
    """
    Validates that Module 1 has built sufficient repository understanding
    before any downstream module proceeds.
    Checks the CognitionReport, RepositoryIdentity, and BoundaryDetectionResult.
    """

    def validate(
        self,
        report: object,
        identity: object,
        boundary: object,
    ) -> GateValidationResult:

        checks: list[GateCheckResult] = []

        # Early exit: if cognition FAILED, gate is BLOCKED immediately
        status = str(getattr(report, "cognition_status", "") or "")
        if status.upper() == "FAILED":
            return GateValidationResult(
                gate_passed=False,
                gate_decision="BLOCKED",
                checks=[GateCheckResult(
                    check_name="Cognition Status",
                    passed=False,
                    detail="cognition_status = FAILED — repository could not be classified",
                )],
                approved_for="NONE",
                blocking_reason="Cognition FAILED — classification required before gate can pass",
            )

        # Check 1 — cognition completed
        c1 = GateCheckResult(
            check_name="Cognition Status",
            passed=status.upper() == "COMPLETE",
            detail=f"cognition_status = {status}",
        )
        checks.append(c1)

        # Check 2 — domain is known
        is_known = getattr(identity, "is_known", False)
        domain   = getattr(identity, "domain", "UNKNOWN")
        c2 = GateCheckResult(
            check_name="Domain Classification",
            passed=is_known,
            detail=f"domain = {domain}, is_known = {is_known}",
        )
        checks.append(c2)

        # Check 3 — repository boundary confirmed
        b_detected = getattr(boundary, "boundary_detected", False)
        c3 = GateCheckResult(
            check_name="Repository Boundary",
            passed=b_detected,
            detail=f"boundary_detected = {b_detected}",
        )
        checks.append(c3)

        # Check 4 — at least some files were found
        total_files = getattr(boundary, "total_files", 0)
        c4 = GateCheckResult(
            check_name="Repository Not Empty",
            passed=total_files > 0,
            detail=f"total_files = {total_files}",
        )
        checks.append(c4)

        # Check 5 — confidence score present
        confidence = getattr(report, "confidence_score", None)
        c5 = GateCheckResult(
            check_name="Confidence Score Present",
            passed=confidence is not None,
            detail=f"confidence_score = {confidence}",
        )
        checks.append(c5)

        # Determine gate decision
        blocking_checks  = [c1, c3, c4]   # must all pass for APPROVED
        review_checks    = [c2, c5]        # failure here → REVIEW_REQUIRED

        all_blocking_passed = all(c.passed for c in blocking_checks)
        all_review_passed   = all(c.passed for c in review_checks)

        if not all_blocking_passed:
            failed = [c.check_name for c in blocking_checks if not c.passed]
            return GateValidationResult(
                gate_passed=False,
                gate_decision="BLOCKED",
                checks=checks,
                approved_for="NONE",
                blocking_reason=f"Critical checks failed: {', '.join(failed)}",
            )

        if not all_review_passed:
            return GateValidationResult(
                gate_passed=False,
                gate_decision="REVIEW_REQUIRED",
                checks=checks,
                approved_for="NONE",
                blocking_reason="Domain or confidence uncertain — human review required",
            )

        return GateValidationResult(
            gate_passed=True,
            gate_decision="APPROVED",
            checks=checks,
            approved_for="MODULE_2",
            blocking_reason=None,
        )