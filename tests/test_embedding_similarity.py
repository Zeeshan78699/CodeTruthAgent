"""
CodeTruth Agent V2
Comprehensive Embedding Semantic Engine Tests
"""

from ai.embedding_similarity import (
    EmbeddingSemanticEngine
)


# ===================================================
# POSITIVE SEMANTIC MATCH
# ===================================================

def test_embedding_similarity_positive():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "process_refund",
        "refund_handler"
    )

    assert result["score"] >= 0.0

    assert result["risk"] in [
        "LOW",
        "MEDIUM",
        "HIGH"
    ]


# ===================================================
# NEGATIVE SEMANTIC MATCH
# ===================================================

def test_embedding_similarity_negative():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "delete_user_account",
        "generate_monthly_report"
    )

    assert result["score"] <= 1.0


# ===================================================
# SAME TEXT MATCH
# ===================================================

def test_embedding_similarity_same_text():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "validate_invoice_data",
        "validate_invoice_data"
    )

    assert result["score"] >= 0.90

    assert result["risk"] == "HIGH"


# ===================================================
# CONTEXTUAL SEMANTIC MATCH
# ===================================================

def test_embedding_similarity_contextual_match():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "parse_url_string",
        "extract_link_from_text"
    )

    assert result["score"] >= 0.0


# ===================================================
# EMPTY INPUT SAFETY
# ===================================================

def test_embedding_similarity_empty_input():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "",
        ""
    )

    assert result["score"] == 0.0

    assert result["risk"] == "LOW"


# ===================================================
# OUTPUT STRUCTURE
# ===================================================

def test_embedding_similarity_output_structure():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "cleanup_archive_files",
        "prune_old_archives"
    )

    expected_keys = [
        "text_a",
        "text_b",
        "score",
        "risk",
        "engine_type",
        "model"
    ]

    for key in expected_keys:

        assert key in result


# ===================================================
# ENGINE TYPE VALIDATION
# ===================================================

def test_embedding_similarity_engine_type():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "process_customer_payment",
        "handle_billing_transaction"
    )

    assert (
        result["engine_type"]
        ==
        "embedding_semantic_engine"
    )


# ===================================================
# MODEL NAME VALIDATION
# ===================================================

def test_embedding_similarity_model_name():

    engine = EmbeddingSemanticEngine()

    assert (
        engine.model_name
        ==
        "all-MiniLM-L6-v2"
    )


# ===================================================
# EMBEDDING GENERATION
# ===================================================

def test_embedding_generation():

    engine = EmbeddingSemanticEngine()

    embedding = engine.generate_embedding(
        "process_payment"
    )

    assert embedding is not None


# ===================================================
# DYNAMIC TEXT SUPPORT
# ===================================================

def test_embedding_similarity_dynamic_text():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "transform_payment_payload_v2",
        "convert_transaction_data"
    )

    assert isinstance(
        result["score"],
        float
    )


# ===================================================
# LONG TEXT STABILITY
# ===================================================

def test_embedding_similarity_long_text():

    engine = EmbeddingSemanticEngine()

    text_a = (
        "validate_customer_invoice_payment_"
        "processing_pipeline"
    )

    text_b = (
        "check_client_billing_transaction_"
        "workflow"
    )

    result = engine.semantic_similarity_score(
        text_a,
        text_b
    )

    assert result["score"] >= 0.0


# ===================================================
# SPECIAL CHARACTER HANDLING
# ===================================================

def test_embedding_similarity_special_characters():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "save-user-data!!!",
        "store_customer_record###"
    )

    assert result["score"] >= 0.0


# ===================================================
# CASE INSENSITIVITY
# ===================================================

def test_embedding_similarity_case_insensitive():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "SAVE_CUSTOMER_DATA",
        "save_customer_data"
    )

    assert result["score"] >= 0.90


# ===================================================
# RANDOM INPUT SAFETY
# ===================================================

def test_embedding_similarity_random_input():

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "@@@###$$$",
        "123456789"
    )

    assert isinstance(
        result["score"],
        float
    )


# ===================================================
# RISK CLASSIFICATION
# ===================================================

def test_embedding_similarity_risk_classification():

    engine = EmbeddingSemanticEngine()

    low_result = engine.classify_risk(0.20)
    medium_result = engine.classify_risk(0.60)
    high_result = engine.classify_risk(0.90)

    assert low_result == "LOW"
    assert medium_result == "MEDIUM"
    assert high_result == "HIGH"


# ===================================================
# NORMALIZATION TEST
# ===================================================

def test_embedding_similarity_normalization():

    engine = EmbeddingSemanticEngine()

    normalized = engine.normalize_text(
        "SAVE-CUSTOMER_DATA"
    )

    assert (
        normalized
        ==
        "save customer data"
    )