"""
========================================================================
classification_reason.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - Classification Evidence  (what signals were found)
    - Classification Reason    (why this domain won)

Builds a human-readable, audit-friendly explanation of why Module 1
classified the repository as it did.

TRUTH BOUNDARY:
    Reason is derived from actual signals — never fabricated.
    If evidence is weak, reason states that explicitly.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .signal_analyzer import SignalResult


@dataclass
class ClassificationEvidence:
    domain:             str
    winning_reason:     str
    signal_summary:     dict[str, int]   # domain -> score
    top_signals:        list[str]        # top contributing signal names
    evidence_strength:  str              # "STRONG" | "MODERATE" | "WEAK" | "NONE"
    notes:              list[str]


class ClassificationReasonBuilder:
    """
    Builds a ClassificationEvidence record from a SignalResult.
    """

    STRONG_THRESHOLD   = 5
    MODERATE_THRESHOLD = 2

    def build(
        self,
        signal_result: SignalResult,
        final_domain: str,
    ) -> ClassificationEvidence:

        top_score = signal_result.domain_scores.get(final_domain, 0)

        # Gather all signals for the winning domain
        top_signals: list[str] = []
        for bucket in [
            signal_result.package_signals,
            signal_result.import_signals,
            signal_result.content_signals,
        ]:
            top_signals.extend(bucket.get(final_domain, []))
        top_signals = list(dict.fromkeys(top_signals))[:10]   # deduplicate, cap

        if top_score >= self.STRONG_THRESHOLD:
            strength = "STRONG"
        elif top_score >= self.MODERATE_THRESHOLD:
            strength = "MODERATE"
        elif top_score >= 1:
            strength = "WEAK"
        else:
            strength = "NONE"

        # Build winning reason
        if final_domain == "UNKNOWN" or strength == "NONE":
            reason = "Insufficient evidence to classify repository domain."
        else:
            signal_names = ", ".join(top_signals[:5]) if top_signals else "none"
            reason = (
                f"{final_domain} signals dominate "
                f"(score={top_score}, evidence=[{signal_names}])."
            )

        notes: list[str] = []
        if strength == "WEAK":
            notes.append(
                "Classification confidence is low — consider gathering more "
                "evidence (documentation, business rules) before proceeding."
            )
        if strength == "NONE":
            notes.append(
                "No domain signals found. Human review required before "
                "Module 2 proceeds."
            )

        return ClassificationEvidence(
            domain=final_domain,
            winning_reason=reason,
            signal_summary=signal_result.domain_scores,
            top_signals=top_signals,
            evidence_strength=strength,
            notes=notes,
        )
