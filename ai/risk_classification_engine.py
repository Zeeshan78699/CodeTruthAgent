"""
CodeTruth Agent V2
Risk Classification Engine

Objective:
Classify repository modifications into
enterprise governance risk levels.

Used By:
- PatchValidationEngine
- Governance Layer
- HITL Layer
- main_v2.py
- Future CodeGenerationEngine

Risk Levels:

LOW
→ AUTO_APPLY

MEDIUM
→ BATCH_APPROVAL

HIGH
→ INDIVIDUAL_APPROVAL

CRITICAL
→ FREEZE_PATCH
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


# =========================================================
# RISK DECISION
# =========================================================

@dataclass
class RiskDecision:

    risk_score: int

    risk_level: str

    action: str

    explanation: str


# =========================================================
# RISK ENGINE
# =========================================================

class RiskClassificationEngine:

    def __init__(self):

        self.risk_matrix = {

            "LOW": {
                "min": 0,
                "max": 29,
                "action": "AUTO_APPLY",
                "explanation":
                "Low-risk repository modification."
            },

            "MEDIUM": {
                "min": 30,
                "max": 59,
                "action": "BATCH_APPROVAL",
                "explanation":
                "Medium-risk repository modification."
            },

            "HIGH": {
                "min": 60,
                "max": 79,
                "action": "INDIVIDUAL_APPROVAL",
                "explanation":
                "High-risk repository modification."
            },

            "CRITICAL": {
                "min": 80,
                "max": 100,
                "action": "FREEZE_PATCH",
                "explanation":
                "Critical-risk repository modification."
            }
        }

    # =====================================================
    # MAIN CLASSIFICATION
    # =====================================================

    def classify_risk(

        self,

        risk_score: int

    ) -> RiskDecision:

        risk_score = self._normalize_score(
            risk_score
        )

        for risk_level, config in self.risk_matrix.items():

            if (
                config["min"]
                <= risk_score
                <= config["max"]
            ):

                return RiskDecision(

                    risk_score=risk_score,

                    risk_level=risk_level,

                    action=config["action"],

                    explanation=config["explanation"]
                )

        return RiskDecision(

            risk_score=risk_score,

            risk_level="CRITICAL",

            action="FREEZE_PATCH",

            explanation=
            "Unable to classify risk score."
        )

    # =====================================================
    # SCORE NORMALIZATION
    # =====================================================

    def _normalize_score(

        self,

        score: int

    ) -> int:

        if score < 0:

            return 0

        if score > 100:

            return 100

        return score

    # =====================================================
    # PATCH-BASED SCORING
    # =====================================================

    def calculate_patch_risk(

        self,

        patch_type: str

    ) -> int:

        risk_lookup = {

            # -----------------------------------------
            # LOW
            # -----------------------------------------

            "print_to_logger": 10,

            "logging_cleanup": 15,

            # -----------------------------------------
            # MEDIUM
            # -----------------------------------------

            "missing_try_except": 40,

            "refactor_function": 50,

            # -----------------------------------------
            # HIGH
            # -----------------------------------------

            "business_logic_change": 70,

            "authentication_change": 75,

            # -----------------------------------------
            # CRITICAL
            # -----------------------------------------

            "database_change": 90,

            "file_deletion": 95,

            "payment_logic_change": 100,
        }

        return risk_lookup.get(
            patch_type,
            50
        )

    # =====================================================
    # PATCH CLASSIFICATION
    # =====================================================

    def classify_patch(

        self,

        patch_type: str

    ) -> RiskDecision:

        score = self.calculate_patch_risk(
            patch_type
        )

        return self.classify_risk(
            score
        )

    # =====================================================
    # EXPORT
    # =====================================================

    def export_policy(self) -> Dict:

        return {

            risk_level: {

                "range":
                f"{config['min']}-{config['max']}",

                "action":
                config["action"],

                "explanation":
                config["explanation"]
            }

            for risk_level, config
            in self.risk_matrix.items()
        }


# =========================================================
# MANUAL TEST
# =========================================================

if __name__ == "__main__":

    engine = RiskClassificationEngine()

    print("=" * 60)
    print("RISK CLASSIFICATION ENGINE")
    print("=" * 60)

    for score in [

        10,
        45,
        70,
        95
    ]:

        decision = engine.classify_risk(
            score
        )

        print(
            f"\nScore: {score}"
        )

        print(
            f"Risk: "
            f"{decision.risk_level}"
        )

        print(
            f"Action: "
            f"{decision.action}"
        )

        print(
            f"Explanation: "
            f"{decision.explanation}"
        )