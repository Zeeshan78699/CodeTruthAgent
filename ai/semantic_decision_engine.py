"""
CodeTruth Agent V2
Semantic Decision Engine

Objective:
Combine semantic intelligence layers
to generate safe engineering decisions.

This is an EARLY-STAGE semantic
decision layer.

Deterministic + explainable first.
"""

from typing import Dict
from typing import List

from ai.lexical_prefilter import (
    LexicalSemanticPrefilter
)

from ai.embedding_similarity import (
    EmbeddingSemanticEngine
)

from ai.purpose_analysis_engine import (
    PurposeAnalysisEngine
)


class SemanticDecisionEngine:

    def __init__(self):

        # ===============================================
        # LOAD ENGINES
        # ===============================================

        self.lexical_engine = (
            LexicalSemanticPrefilter()
        )

        self.embedding_engine = (
            EmbeddingSemanticEngine()
        )

        self.purpose_engine = (
            PurposeAnalysisEngine()
        )

    # ===================================================
    # GENERATE ENGINEERING DECISION
    # ===================================================

    def generate_decision(
        self,
        lexical_score: float,
        embedding_score: float,
        purpose_domain_match: bool,
        side_effects_detected: bool
    ) -> Dict:

        reasoning = []

        # ===============================================
        # CONFIDENCE CALCULATION
        # ===============================================

        confidence = round(
            (
                lexical_score * 0.20
                +
                embedding_score * 0.50
                +
                (
                    0.20
                    if purpose_domain_match
                    else 0.0
                )
                +
                (
                    0.10
                    if side_effects_detected
                    else 0.0
                )
            ),
            2
        )

        # ===============================================
        # REASONING
        # ===============================================

        if embedding_score >= 0.70:

            reasoning.append(
                "High semantic similarity detected"
            )

        elif embedding_score >= 0.50:

            reasoning.append(
                "Moderate semantic similarity detected"
            )

        else:

            reasoning.append(
                "Low semantic similarity detected"
            )

        # ===============================================

        if purpose_domain_match:

            reasoning.append(
                "Shared business domain detected"
            )

        else:

            reasoning.append(
                "Business domains differ"
            )

        # ===============================================

        if side_effects_detected:

            reasoning.append(
                "Behavioral side effects detected"
            )

        else:

            reasoning.append(
                "No major side effects detected"
            )

        # ===============================================
        # FINAL DECISION
        # ===============================================
        
        #print(
        #    "DEBUG:",
        #    embedding_score,
        #    confidence,
        #    purpose_domain_match,
        #    side_effects_detected
        #    )

        if (
            confidence >= 0.80
            and
            not side_effects_detected
        ):

            decision = "SAFE"

            risk_level = "LOW"

        elif (
            embedding_score >= 0.80 
            or confidence >= 0.50 
            or (
                purpose_domain_match
                and not side_effects_detected
                and embedding_score >= 0.35
                )
            ):

           # print("REVIEW CONDITION HIT")
            decision = "REVIEW"

            risk_level = "MEDIUM"

        else:

         #   print("BLOCK CONDITION HIT")
            decision = "BLOCK"

            risk_level = "HIGH"

        return {

            "decision":
            decision,

            "confidence":
            confidence,

            "risk_level":
            risk_level,

            "reasoning":
            reasoning
        }

    # ===================================================
    # MAIN ANALYSIS PIPELINE
    # ===================================================

    def analyze_change(
        self,
        function_a: str,
        function_b: str,
        code_a: str = "",
        code_b: str = "",
        docstring_a: str = "",
        docstring_b: str = ""
    ) -> Dict:

        # ===============================================
        # LEXICAL ANALYSIS
        # ===============================================

        lexical_result = (
            self.lexical_engine
            .lexical_similarity_score(
                function_a,
                function_b
            )
        )

        # ===============================================
        # EMBEDDING ANALYSIS
        # ===============================================

        embedding_result = (
            self.embedding_engine
            .semantic_similarity_score(
                function_a,
                function_b
            )
        )

        # ===============================================
        # PURPOSE ANALYSIS
        # ===============================================

        purpose_a = (
            self.purpose_engine
            .analyze_purpose(
                function_name=function_a,
                code=code_a,
                docstring=docstring_a
            )
        )

        purpose_b = (
            self.purpose_engine
            .analyze_purpose(
                function_name=function_b,
                code=code_b,
                docstring=docstring_b
            )
        )

        # ===============================================
        # PURPOSE MATCH
        # ===============================================

        purpose_domain_match = (
            purpose_a["business_domain"]
            ==
            purpose_b["business_domain"]
        )

        # ===============================================
        # SIDE EFFECT ANALYSIS
        # ===============================================

        combined_side_effects = (
            purpose_a["side_effects"]
            +
            purpose_b["side_effects"]
        )

        side_effects_detected = (
            len(combined_side_effects)
            > 0
        )

        # ===============================================
        # DECISION GENERATION
        # ===============================================

        decision_result = (
            self.generate_decision(
                lexical_score=
                lexical_result["score"],

                embedding_score=
                embedding_result["score"],

                purpose_domain_match=
                purpose_domain_match,

                side_effects_detected=
                side_effects_detected
            )
        )

        # ===============================================
        # FINAL OUTPUT
        # ===============================================

        return {

            "function_a":
            function_a,

            "function_b":
            function_b,

            "lexical_score":
            lexical_result["score"],

            "embedding_score":
            embedding_result["score"],

            "purpose_domain_match":
            purpose_domain_match,

            "side_effects_detected":
            side_effects_detected,

            "decision":
            decision_result["decision"],

            "confidence":
            decision_result["confidence"],

            "risk_level":
            decision_result["risk_level"],

            "reasoning":
            decision_result["reasoning"],

            "engine_type":
            "semantic_decision_engine"
        }


# =======================================================
# MANUAL TEST
# =======================================================

if __name__ == "__main__":

    engine = SemanticDecisionEngine()

    code_a = '''

def process_refund(payment_id):

    validate_payment(payment_id)

    update_database(payment_id)

    send_email(payment_id)

    db.commit()

'''

    code_b = '''

def refund_handler(payment_id):

    validate_payment(payment_id)

    send_email(payment_id)

'''

    result = engine.analyze_change(
        function_a="process_refund",

        function_b="refund_handler",

        code_a=code_a,

        code_b=code_b,

        docstring_a=
        "Processes customer refunds",

        docstring_b=
        "Handles refund processing"
    )

    print(result)