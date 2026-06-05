
import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.append(PROJECT_ROOT)

from ai.embedding_similarity import (
    EmbeddingSemanticEngine
)

engine = EmbeddingSemanticEngine()

print(
    engine.semantic_similarity_score(
        "process_refund",
        "refund_handler"
    )
)

print(
    engine.semantic_similarity_score(
        "parse_url_string",
        "extract_link_from_text"
    )
)

print(
    engine.semantic_similarity_score(
        "delete_user_account",
        "generate_monthly_report"
    )
)