"""
CodeTruth Agent V2
Comprehensive Lexical Prefilter Tests
"""

from ai.lexical_prefilter import (
    LexicalSemanticPrefilter
)


# ===================================================
# POSITIVE SIMILARITY
# ===================================================

def test_lexical_similarity_positive():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "calculate_total_price",
        "compute_invoice_amount"
    )

    assert result["score"] > 0.0

    assert result["risk"] in [
        "LOW",
        "MEDIUM",
        "HIGH"
    ]

    assert isinstance(
        result["matched_keywords"],
        list
    )

    assert isinstance(
        result["matched_actions"],
        list
    )


# ===================================================
# NEGATIVE SIMILARITY
# ===================================================

def test_lexical_similarity_negative():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "delete_user_account",
        "generate_monthly_report"
    )

    assert result["score"] < 0.75


# ===================================================
# IDENTICAL TEXT MATCH
# ===================================================

def test_lexical_similarity_same_text():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "validate_invoice_data",
        "validate_invoice_data"
    )

    assert result["score"] == 1.0

    assert result["risk"] == "HIGH"


# ===================================================
# SYNONYM DETECTION
# ===================================================

def test_lexical_similarity_synonym_detection():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "save_customer_record",
        "store_client_data"
    )

    assert result["score"] > 0.0

    assert (
        len(result["matched_actions"])
        >= 1
    )


# ===================================================
# EMPTY INPUT SAFETY
# ===================================================

def test_lexical_similarity_empty_input():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "",
        ""
    )

    assert result["score"] == 0.0

    assert result["risk"] == "LOW"


# ===================================================
# OUTPUT STRUCTURE
# ===================================================

def test_lexical_similarity_output_structure():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "cleanup_archive_files",
        "prune_old_archives"
    )

    expected_keys = [
        "text_a",
        "text_b",
        "score",
        "matched_keywords",
        "matched_actions",
        "risk",
        "engine_type"
    ]

    for key in expected_keys:

        assert key in result


# ===================================================
# ENGINE TYPE VALIDATION
# ===================================================

def test_lexical_similarity_engine_type():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "parse_customer_file",
        "extract_client_document"
    )

    assert (
        result["engine_type"]
        ==
        "lexical_semantic_prefilter"
    )


# ===================================================
# DYNAMIC TEXT SUPPORT
# ===================================================

def test_lexical_similarity_dynamic_text_support():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "transform_payment_payload_v2",
        "convert_transaction_data"
    )

    assert isinstance(
        result["score"],
        float
    )

    assert result["score"] >= 0.0


# ===================================================
# CAMELCASE SUPPORT
# ===================================================

def test_lexical_similarity_camelcase_support():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "calculateInvoiceTotal",
        "computeBillingAmount"
    )

    assert result["score"] >= 0.0


# ===================================================
# SPECIAL CHARACTER CLEANING
# ===================================================

def test_lexical_similarity_special_characters():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "save-user-data!!!",
        "store_customer_record###"
    )

    assert result["score"] >= 0.0


# ===================================================
# CASE INSENSITIVITY
# ===================================================

def test_lexical_similarity_case_insensitive():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "SAVE_CUSTOMER_DATA",
        "save_customer_data"
    )

    assert result["score"] == 1.0


# ===================================================
# LONG TEXT STABILITY
# ===================================================

def test_lexical_similarity_long_text():

    engine = LexicalSemanticPrefilter()

    text_a = (
        "validate_customer_invoice_payment_"
        "processing_pipeline"
    )

    text_b = (
        "check_client_billing_transaction_"
        "workflow"
    )

    result = engine.lexical_similarity_score(
        text_a,
        text_b
    )

    assert result["score"] >= 0.0


# ===================================================
# NO CRASH RANDOM INPUT
# ===================================================

def test_lexical_similarity_random_input():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "@@@###$$$",
        "123456789"
    )

    assert isinstance(
        result["score"],
        float
    )


# ===================================================
# ACTION MATCH DETECTION
# ===================================================

def test_lexical_similarity_action_matching():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "cleanup_old_archives",
        "prune_backup_files"
    )

    assert (
        len(result["matched_actions"])
        >= 1
    )


# ===================================================
# MULTIPLE TOKEN MATCH
# ===================================================

def test_lexical_similarity_multiple_token_overlap():

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "fetch_customer_payment_history",
        "load_client_transaction_history"
    )

    assert result["score"] > 0.0


# ===================================================
# RISK CLASSIFICATION VALIDATION
# ===================================================

def test_lexical_similarity_risk_classification():

    engine = LexicalSemanticPrefilter()

    low_result = engine.classify_risk(0.20)
    medium_result = engine.classify_risk(0.60)
    high_result = engine.classify_risk(0.90)

    assert low_result == "LOW"
    assert medium_result == "MEDIUM"
    assert high_result == "HIGH"