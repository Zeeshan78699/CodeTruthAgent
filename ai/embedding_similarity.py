"""
CodeTruth Agent V2
Embedding Semantic Engine

REAL semantic similarity using embeddings.
"""

from typing import Dict

from sentence_transformers import SentenceTransformer
from sentence_transformers import util

import os

from dotenv import load_dotenv

load_dotenv()


class EmbeddingSemanticEngine:

    def __init__(self):

        # ===================================================
        # LOAD EMBEDDING MODEL
        # ===================================================

        self.model_name = "all-MiniLM-L6-v2"
        
        self.hf_token = os.getenv(
            "HF_TOKEN"
        )

        self.model = SentenceTransformer(
            self.model_name,
            token=self.hf_token
        )

    # ===================================================
    # CLEAN INPUT TEXT
    # ===================================================

    def normalize_text(
        self,
        text: str
    ) -> str:

        if not text:
            return ""

        text = text.replace("_", " ")
        text = text.replace("-", " ")

        return text.strip().lower()

    # ===================================================
    # CREATE EMBEDDING
    # ===================================================

    def generate_embedding(
        self,
        text: str
    ):

        normalized_text = self.normalize_text(
            text
        )

        return self.model.encode(
            normalized_text,
            convert_to_tensor=True
        )

    # ===================================================
    # CLASSIFY RISK
    # ===================================================

    def classify_risk(
        self,
        score: float
    ) -> str:

        if score >= 0.80:
            return "HIGH"

        if score >= 0.50:
            return "MEDIUM"

        return "LOW"

    # ===================================================
    # MAIN SEMANTIC ENGINE
    # ===================================================

    def semantic_similarity_score(
        self,
        text_a: str,
        text_b: str
    ) -> Dict:

        # ===================================================
        # EMPTY INPUT SAFETY
        # ===================================================

        if not text_a or not text_b:

            return {
                "text_a": text_a,
                "text_b": text_b,
                "score": 0.0,
                "risk": "LOW",
                "engine_type":
                (
                    "embedding_semantic_engine"
                )
            }

        # ===================================================
        # GENERATE EMBEDDINGS
        # ===================================================

        embedding_a = self.generate_embedding(
            text_a
        )

        embedding_b = self.generate_embedding(
            text_b
        )

        # ===================================================
        # COSINE SIMILARITY
        # ===================================================

        similarity_score = util.cos_sim(
            embedding_a,
            embedding_b
        ).item()

        similarity_score = round(
            float(similarity_score),
            2
        )

        # ===================================================
        # RISK CLASSIFICATION
        # ===================================================

        risk = self.classify_risk(
            similarity_score
        )

        # ===================================================
        # FINAL OUTPUT
        # ===================================================

        return {
            "text_a": text_a,
            "text_b": text_b,
            "score": similarity_score,
            "risk": risk,
            "engine_type":
            (
                "embedding_semantic_engine"
            ),
            "model":
            (
                self.model_name
            )
        }


# =======================================================
# MANUAL TEST
# =======================================================

if __name__ == "__main__":

    engine = EmbeddingSemanticEngine()

    result = engine.semantic_similarity_score(
        "process_refund",
        "refund_handler"
    )

    print(result)

    result_2 = engine.semantic_similarity_score(
        "parse_url_string",
        "extract_link_from_text"
    )

    print(result_2)