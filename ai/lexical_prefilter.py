"""
CodeTruth Agent V2
Lexical Semantic Prefilter
"""

import re

from typing import Dict
from typing import List
from typing import Set


class LexicalSemanticPrefilter:

    def __init__(self):

        # ===================================================
        # STOP WORDS
        # ===================================================

        self.stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "to",
            "of",
            "in",
            "on",
            "for",
            "with",
            "by",
            "is",
            "are",
            "this",
            "that"
        }

        # ===================================================
        # ACTION WORDS
        # ===================================================

        self.action_keywords = {
            "calculate",
            "compute",
            "generate",
            "create",
            "build",
            "update",
            "delete",
            "remove",
            "fetch",
            "load",
            "save",
            "store",
            "validate",
            "check",
            "compare",
            "analyze",
            "scan",
            "process",
            "merge",
            "rollback",
            "recover",
            "archive",
            "cleanup",
            "parse",
            "extract",
            "convert",
            "transform",
            "verify",
            "read",
            "write"
        }

        # ===================================================
        # SEMANTIC SYNONYM MAP
        # ===================================================

        self.semantic_synonyms = {
            "calculate": [
                "compute",
                "sum",
                "total"
            ],
            "compute": [
                "calculate",
                "derive"
            ],
            "delete": [
                "remove",
                "erase"
            ],
            "remove": [
                "delete",
                "discard"
            ],
            "fetch": [
                "load",
                "retrieve",
                "read"
            ],
            "load": [
                "fetch",
                "read"
            ],
            "save": [
                "store",
                "persist",
                "write"
            ],
            "store": [
                "save",
                "persist"
            ],
            "validate": [
                "check",
                "verify"
            ],
            "check": [
                "validate",
                "verify"
            ],
            "recover": [
                "restore"
            ],
            "rollback": [
                "restore",
                "revert"
            ],
            "cleanup": [
                "prune",
                "trim"
            ],
            "parse": [
                "extract",
                "read"
            ],
            "extract": [
                "parse",
                "retrieve"
            ],
            "convert": [
                "transform"
            ],
            "transform": [
                "convert"
            ],
            "validate": [
                "check",
                "verify",
                "authenticate"
            ],
            "verify": [
            "validate",
            "authenticate"
            ],
            "authenticate": [
            "validate",
            "verify",
            "authorize"
            ],
            "restore": [
            "recover",
            "rollback",
            "revert"
            ],
        }

    # ===================================================
    # NORMALIZE TEXT
    # ===================================================

    def normalize_text(
        self,
        text: str
    ) -> str:

        text = text.lower()

        # camelCase split
        text = re.sub(
            r"([a-z])([A-Z])",
            r"\1 \2",
            text
        )

        # snake_case / kebab-case
        text = text.replace("_", " ")
        text = text.replace("-", " ")

        # remove symbols
        text = re.sub(
            r"[^a-zA-Z0-9\s]",
            "",
            text
        )

        return text

    # ===================================================
    # TOKENIZE
    # ===================================================

    def tokenize(
        self,
        text: str
    ) -> List[str]:

        normalized = self.normalize_text(text)

        raw_tokens = normalized.split()

        cleaned_tokens = []

        for token in raw_tokens:

            if (
                token
                and
                token not in self.stop_words
            ):

                cleaned_tokens.append(token)

        return cleaned_tokens

    # ===================================================
    # EXPAND TOKENS WITH SYNONYMS
    # ===================================================

    def expand_tokens(
        self,
        tokens: List[str]
    ) -> List[str]:

        expanded_tokens: Set[str] = set()

        for token in tokens:

            expanded_tokens.add(token)

            # direct synonym expansion
            if token in self.semantic_synonyms:

                for synonym in (
                    self.semantic_synonyms[token]
                ):

                    expanded_tokens.add(synonym)

            # reverse synonym expansion
            for (
                root_word,
                synonyms
            ) in self.semantic_synonyms.items():

                if token in synonyms:

                    expanded_tokens.add(root_word)

        return list(expanded_tokens)

    # ===================================================
    # EXTRACT ACTIONS
    # ===================================================

    def extract_actions(
        self,
        tokens: List[str]
    ) -> List[str]:

        actions = []

        for token in tokens:

            if token in self.action_keywords:

                actions.append(token)

            else:

                for (
                    root_word,
                    synonyms
                ) in self.semantic_synonyms.items():

                    if token in synonyms:

                        actions.append(root_word)

        return list(set(actions))

    # ===================================================
    # CALCULATE OVERLAP SCORE
    # ===================================================

    def calculate_overlap_score(
        self,
        tokens_a: List[str],
        tokens_b: List[str]
    ) -> float:

        if not tokens_a or not tokens_b:
            return 0.0

        set_a = set(tokens_a)
        set_b = set(tokens_b)

        overlap = set_a.intersection(set_b)

        largest_set_size = max(
            len(set_a),
            len(set_b)
        )

        if largest_set_size == 0:
            return 0.0

        return round(
            len(overlap) / largest_set_size,
            2
        )

    # ===================================================
    # CLASSIFY RISK
    # ===================================================

    def classify_risk(
        self,
        score: float
    ) -> str:

        if score >= 0.75:
            return "HIGH"

        if score >= 0.45:
            return "MEDIUM"

        return "LOW"

    # ===================================================
    # MAIN PREFILTER ENGINE
    # ===================================================

    def lexical_similarity_score(
        self,
        text_a: str,
        text_b: str
    ) -> Dict:

        # ===================================================
        # TOKENIZATION
        # ===================================================

        tokens_a = self.tokenize(text_a)
        tokens_b = self.tokenize(text_b)

        # ===================================================
        # SEMANTIC EXPANSION
        # ===================================================

        expanded_a = self.expand_tokens(tokens_a)
        expanded_b = self.expand_tokens(tokens_b)

        # ===================================================
        # ACTION EXTRACTION
        # ===================================================

        actions_a = self.extract_actions(expanded_a)
        actions_b = self.extract_actions(expanded_b)

        # ===================================================
        # MATCH DETECTION
        # ===================================================

        matched_keywords = list(
            set(expanded_a).intersection(
                set(expanded_b)
            )
        )

        matched_actions = list(
            set(actions_a).intersection(
                set(actions_b)
            )
        )

        # ===================================================
        # SCORE CALCULATION
        # ===================================================

        keyword_score = self.calculate_overlap_score(
            expanded_a,
            expanded_b
        )

        action_score = self.calculate_overlap_score(
            actions_a,
            actions_b
        )

        final_score = round(
            (
                keyword_score * 0.7
                +
                action_score * 0.3
            ),
            2
        )

        # ===================================================
        # RISK CLASSIFICATION
        # ===================================================

        risk = self.classify_risk(final_score)

        # ===================================================
        # FINAL OUTPUT
        # ===================================================

        return {
            "text_a": text_a,
            "text_b": text_b,
            "score": final_score,
            "matched_keywords": matched_keywords,
            "matched_actions": matched_actions,
            "risk": risk,
            "engine_type":
            (
                "lexical_semantic_prefilter"
            )
        }


# =======================================================
# MANUAL TEST
# =======================================================

if __name__ == "__main__":

    engine = LexicalSemanticPrefilter()

    result = engine.lexical_similarity_score(
        "save_customer_record",
        "store_client_data"
    )

    print(result)