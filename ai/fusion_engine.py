"""
CodeTruth Agent V2.1
Fusion Engine

Objective:
Combine semantic similarity and behavioral signature signals
into a unified risk decision.

V2.1 Philosophy:
- Deterministic - same inputs always produce same outputs
- Explainable - every decision has a reasoning trail
- Conservative - when in doubt, escalate (REVIEW over SAFE)
- Symmetric - high-impact behavior overrides low semantic similarity

Decision Logic:
    Inputs:
        semantic_score (0.0 - 1.0) - from SemanticDecisionEngine
        semantic_decision (SAFE / REVIEW / BLOCK) - from SemanticDecisionEngine
        behavior_a_tags (list) - from BehavioralSignatureEngine
        behavior_b_tags (list) - from BehavioralSignatureEngine
        behavior_a_risk (LOW / MEDIUM / HIGH)
        behavior_b_risk (LOW / MEDIUM / HIGH)

    Output:
        fusion_decision (SAFE / REVIEW / BLOCK)
        fusion_risk_score (0 - 100)
        fusion_risk_level (LOW / MEDIUM / HIGH / CRITICAL)
        reasoning (list of human-readable rationale strings)

Key Rules:
    1. If either behavior has HIGH risk: minimum REVIEW
    2. If behaviors are OPPOSING (e.g., DELETE vs BACKUP): BLOCK
    3. If behaviors are DISJOINT (no shared tags) AND semantic is unrelated: BLOCK
    4. If semantic is BLOCK: fusion is BLOCK (semantic engine is authoritative on
       unrelated functions)
    5. Otherwise combine semantic score with behavior risk via weighted sum

This is NOT AI. This is rule-based fusion of two deterministic signal sources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


# ---------------------------------------------------------
# OPPOSING BEHAVIOR PAIRS
# ---------------------------------------------------------
# These are behaviors that "undo" each other.
# If function A does one and function B does the other,
# merging them would be a real semantic regression.

OPPOSING_BEHAVIORS = {
    frozenset(["BACKUP_OPERATION", "RECOVERY_OPERATION"]),
    frozenset(["BACKUP_OPERATION", "DELETE_OPERATION"]),
    frozenset(["FILE_WRITE", "DELETE_OPERATION"]),
    frozenset(["DATABASE_OPERATION", "DELETE_OPERATION"]),
}


# ---------------------------------------------------------
# HIGH-IMPACT BEHAVIORS
# ---------------------------------------------------------
# Behaviors that always trigger at least REVIEW, regardless
# of semantic similarity.

HIGH_IMPACT_BEHAVIORS = {
    "DELETE_OPERATION",
    "AUTH_OPERATION",
    "DATABASE_OPERATION",
    "RECOVERY_OPERATION",
}


# ---------------------------------------------------------
# RISK LEVEL CONSTANTS
# ---------------------------------------------------------

RISK_NUMERIC = {
    "LOW": 0,
    "MEDIUM": 50,
    "HIGH": 100,
    None: 0,
}


# ---------------------------------------------------------
# FUSION DECISION DATA MODEL
# ---------------------------------------------------------

@dataclass
class FusionDecision:
    fusion_decision: str
    fusion_risk_score: int
    fusion_risk_level: str

    semantic_score: float
    semantic_decision: str
    behavior_a_tags: List[str]
    behavior_b_tags: List[str]
    behavior_a_risk: str
    behavior_b_risk: str

    opposing_behavior_detected: bool
    shared_behavior_tags: List[str]

    reasoning: List[str] = field(default_factory=list)


# ---------------------------------------------------------
# FUSION ENGINE
# ---------------------------------------------------------

class FusionEngine:

    def __init__(self) -> None:
        pass

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------

    def fuse(
        self,
        semantic_score: float,
        semantic_decision: str,
        behavior_a_tags: List[str],
        behavior_b_tags: List[str],
        behavior_a_risk: str,
        behavior_b_risk: str,
    ) -> FusionDecision:
        """
        Combine semantic + behavioral signals into a unified decision.
        """

        tags_a: Set[str] = set(behavior_a_tags or [])
        tags_b: Set[str] = set(behavior_b_tags or [])

        shared_tags = sorted(tags_a & tags_b)
        all_tags = tags_a | tags_b

        reasoning: List[str] = []

        # -------------------------------------------------
        # Step 1: Check for opposing behaviors (BLOCK rule)
        # -------------------------------------------------

        opposing_detected = self._detect_opposing(tags_a, tags_b)

        if opposing_detected:
            reasoning.append(
                "Opposing behaviors detected between the two functions."
            )

        # -------------------------------------------------
        # Step 2: Compute behavior risk score
        # -------------------------------------------------

        behavior_risk_score = self._compute_behavior_risk(
            tags_a=tags_a,
            tags_b=tags_b,
            risk_a=behavior_a_risk,
            risk_b=behavior_b_risk,
            reasoning=reasoning,
        )

        # -------------------------------------------------
        # Step 3: Compute semantic risk score
        # -------------------------------------------------

        # Inverted: high semantic similarity = low semantic risk
        # (similar functions are SAFER to merge, not riskier)
        # BUT: if semantic engine said BLOCK, score is maxed
        if semantic_decision == "BLOCK":
            semantic_risk_score = 100
            reasoning.append(
                "Semantic engine returned BLOCK (functions unrelated)."
            )
        else:
            semantic_risk_score = int((1.0 - semantic_score) * 100)

        # -------------------------------------------------
        # Step 4: Weighted fusion of semantic + behavior
        # -------------------------------------------------
        # Weights:
        #   - Semantic risk: 40% (whether functions are related)
        #   - Behavior risk: 60% (what the functions actually DO)
        # Behavior weighted higher because behavior is more concrete
        # than semantic similarity of names.

        fusion_score = round(
            (semantic_risk_score * 0.40)
            + (behavior_risk_score * 0.60)
        )

        # -------------------------------------------------
        # Step 5: Apply override rules
        # -------------------------------------------------

        if opposing_detected:
            # Opposing behaviors -> always BLOCK
            fusion_score = max(fusion_score, 90)
            decision = "BLOCK"
            risk_level = "CRITICAL"
            reasoning.append(
                "Override: opposing behaviors force BLOCK decision."
            )

        elif semantic_decision == "BLOCK" and not shared_tags:
            # Semantic says unrelated AND no shared behaviors -> BLOCK
            decision = "BLOCK"
            risk_level = self._score_to_risk_level(fusion_score)
            reasoning.append(
                "Functions are semantically unrelated and share no "
                "behavioral tags."
            )

        else:
            # Standard mapping from fusion score to decision
            decision, risk_level = self._score_to_decision(
                fusion_score, all_tags, reasoning
            )

        return FusionDecision(
            fusion_decision=decision,
            fusion_risk_score=fusion_score,
            fusion_risk_level=risk_level,

            semantic_score=semantic_score,
            semantic_decision=semantic_decision,
            behavior_a_tags=sorted(tags_a),
            behavior_b_tags=sorted(tags_b),
            behavior_a_risk=behavior_a_risk,
            behavior_b_risk=behavior_b_risk,

            opposing_behavior_detected=opposing_detected,
            shared_behavior_tags=shared_tags,

            reasoning=reasoning,
        )

    # -----------------------------------------------------
    # Internal: Opposing behavior detection
    # -----------------------------------------------------

    def _detect_opposing(
        self,
        tags_a: Set[str],
        tags_b: Set[str],
    ) -> bool:

        for tag_a in tags_a:
            for tag_b in tags_b:
                pair = frozenset([tag_a, tag_b])
                if pair in OPPOSING_BEHAVIORS:
                    return True

        return False

    # -----------------------------------------------------
    # Internal: Behavior risk scoring
    # -----------------------------------------------------

    def _compute_behavior_risk(
        self,
        tags_a: Set[str],
        tags_b: Set[str],
        risk_a: str,
        risk_b: str,
        reasoning: List[str],
    ) -> int:
        """
        Compute a 0-100 behavior risk score.
        Higher = riskier change.
        """

        # Start with the max of the two function risks
        base_score = max(
            RISK_NUMERIC.get(risk_a, 0),
            RISK_NUMERIC.get(risk_b, 0),
        )

        # Boost if any high-impact behaviors are present
        high_impact_present = (tags_a | tags_b) & HIGH_IMPACT_BEHAVIORS

        if high_impact_present:
            reasoning.append(
                f"High-impact behaviors detected: "
                f"{sorted(high_impact_present)}"
            )
            base_score = max(base_score, 60)

        # If both functions have NO behavioral tags, this is safer
        if not tags_a and not tags_b:
            reasoning.append(
                "Neither function exhibits tracked behaviors."
            )
            base_score = min(base_score, 20)

        return base_score

    # -----------------------------------------------------
    # Internal: Score to decision mapping
    # -----------------------------------------------------

    def _score_to_decision(
        self,
        fusion_score: int,
        all_tags: Set[str],
        reasoning: List[str],
    ):
        """
        Map fusion score + behavior tags to (decision, risk_level).
        """

        # High-impact behaviors floor the decision at REVIEW
        if all_tags & HIGH_IMPACT_BEHAVIORS:
            if fusion_score >= 80:
                reasoning.append(
                    "High fusion score with high-impact behaviors."
                )
                return "BLOCK", "CRITICAL"
            else:
                reasoning.append(
                    "High-impact behavior present; minimum REVIEW."
                )
                return "REVIEW", self._score_to_risk_level(fusion_score)

        # Standard thresholds
        if fusion_score >= 80:
            return "BLOCK", "CRITICAL"
        elif fusion_score >= 50:
            return "REVIEW", "HIGH"
        elif fusion_score >= 25:
            return "REVIEW", "MEDIUM"
        else:
            return "SAFE", "LOW"

    # -----------------------------------------------------
    # Internal: Score to risk level
    # -----------------------------------------------------

    def _score_to_risk_level(self, fusion_score: int) -> str:

        if fusion_score >= 80:
            return "CRITICAL"
        elif fusion_score >= 60:
            return "HIGH"
        elif fusion_score >= 30:
            return "MEDIUM"
        else:
            return "LOW"


# ---------------------------------------------------------
# STANDALONE MANUAL TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    engine = FusionEngine()

    print("=" * 70)
    print("FUSION ENGINE MANUAL TEST")
    print("=" * 70)

    # Test 1: BACKUP vs RECOVERY -> opposing -> BLOCK
    result = engine.fuse(
        semantic_score=0.55,
        semantic_decision="REVIEW",
        behavior_a_tags=["BACKUP_OPERATION"],
        behavior_b_tags=["RECOVERY_OPERATION"],
        behavior_a_risk="MEDIUM",
        behavior_b_risk="HIGH",
    )

    print(f"\nTest 1: BACKUP vs RECOVERY")
    print(f"  Decision: {result.fusion_decision}")
    print(f"  Score:    {result.fusion_risk_score}")
    print(f"  Risk:     {result.fusion_risk_level}")
    print(f"  Reasoning: {result.reasoning}")

    # Test 2: Both clean -> SAFE
    result = engine.fuse(
        semantic_score=0.85,
        semantic_decision="SAFE",
        behavior_a_tags=[],
        behavior_b_tags=[],
        behavior_a_risk="LOW",
        behavior_b_risk="LOW",
    )

    print(f"\nTest 2: Both clean (no behaviors)")
    print(f"  Decision: {result.fusion_decision}")
    print(f"  Score:    {result.fusion_risk_score}")
    print(f"  Risk:     {result.fusion_risk_level}")
    print(f"  Reasoning: {result.reasoning}")

    # Test 3: Two delete functions -> REVIEW (high-impact floor)
    result = engine.fuse(
        semantic_score=0.85,
        semantic_decision="REVIEW",
        behavior_a_tags=["DELETE_OPERATION"],
        behavior_b_tags=["DELETE_OPERATION"],
        behavior_a_risk="HIGH",
        behavior_b_risk="HIGH",
    )

    print(f"\nTest 3: Both DELETE")
    print(f"  Decision: {result.fusion_decision}")
    print(f"  Score:    {result.fusion_risk_score}")
    print(f"  Risk:     {result.fusion_risk_level}")
    print(f"  Reasoning: {result.reasoning}")
