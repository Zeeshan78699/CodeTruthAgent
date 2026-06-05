"""
CodeTruth Agent V2
Semantic Decision Engine Tests
"""

from ai.semantic_decision_engine import (
    SemanticDecisionEngine
)


def test_semantic_decision_review():

    engine = SemanticDecisionEngine()

    code_a = '''

def process_refund(payment_id):

    validate_payment(payment_id)

    db.commit()

'''

    code_b = '''

def refund_handler(payment_id):

    validate_payment(payment_id)

'''

    result = engine.analyze_change(
        function_a="process_refund",
        function_b="refund_handler",
        code_a=code_a,
        code_b=code_b,
        docstring_a="Processes refunds",
        docstring_b="Handles refunds"
    )

    assert result["decision"] in [
        "SAFE",
        "REVIEW",
        "BLOCK"
    ]

    assert isinstance(
        result["confidence"],
        float
    )


def test_semantic_decision_output_structure():

    engine = SemanticDecisionEngine()

    result = engine.analyze_change(
        function_a="save_customer_data",
        function_b="store_client_information"
    )

    expected_keys = [

        "function_a",
        "function_b",
        "lexical_score",
        "embedding_score",
        "purpose_domain_match",
        "side_effects_detected",
        "decision",
        "confidence",
        "risk_level",
        "reasoning",
        "engine_type"
    ]

    for key in expected_keys:

        assert key in result


def test_semantic_decision_engine_type():

    engine = SemanticDecisionEngine()

    result = engine.analyze_change(
        function_a="parse_url",
        function_b="extract_link"
    )

    assert (
        result["engine_type"]
        ==
        "semantic_decision_engine"
    )


def test_semantic_decision_negative_case():

    engine = SemanticDecisionEngine()

    result = engine.analyze_change(
        function_a="delete_user_account",
        function_b="generate_monthly_report"
    )

    assert result["confidence"] >= 0.0


def test_semantic_decision_reasoning_exists():

    engine = SemanticDecisionEngine()

    result = engine.analyze_change(
        function_a="process_payment",
        function_b="payment_handler"
    )

    assert isinstance(
        result["reasoning"],
        list
    )