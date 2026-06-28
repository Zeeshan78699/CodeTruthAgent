"""
fact_extractor.py

Experimental Module 2.5 validation harness.

Purpose:
Convert raw unresolved entries into richer facts that
specialized deterministic engines can reason about.

This file DOES NOT resolve anything.

Truth Boundary:
- Extract facts only
- Never infer missing facts
- Never guess types
"""

import re
from typing import Any, Dict, List


ATTRIBUTE_PATTERN = re.compile(
    r"\.([A-Za-z_][A-Za-z0-9_]*)\("
)


class FactExtractor:

    def __init__(
        self,
        unresolved_entries: List[Dict[str, Any]]
    ):
        self.unresolved_entries = (
            unresolved_entries or []
        )

    def extract_fact(
        self,
        entry: Dict[str, Any]
    ) -> Dict[str, Any]:

        fact = dict(entry)

        note = str(
            entry.get(
                "note",
                ""
            )
        )

        pattern = entry.get(
            "pattern",
            "unknown"
        )

        fact["attribute_name"] = None
        fact["method_name"] = None
        fact["variable_name"] = None

        # ---------------------------------
        # Attribute Call
        # ---------------------------------

        if pattern == "attribute_call":

            match = ATTRIBUTE_PATTERN.search(
                note
            )

            if match:
                fact[
                    "attribute_name"
                ] = match.group(1)

        # ---------------------------------
        # self_method_not_found
        # ---------------------------------

        elif pattern == "self_method_not_found":

            method_match = re.search(
                r"self\.([A-Za-z_][A-Za-z0-9_]*)\(",
                note
            )

            if method_match:
                fact[
                    "method_name"
                ] = method_match.group(1)

            class_match = re.search(
                r"class '([^']+)'",
                note
            )

            if class_match:
                fact[
                    "class_name"
                ] = class_match.group(1)

        # ---------------------------------
        # name_call_unresolved
        # ---------------------------------

        elif pattern == "name_call_unresolved":

            name_match = re.search(
                r"Call to '([^']+)'",
                note
            )

            if name_match:
                fact[
                    "variable_name"
                ] = name_match.group(1)

        return fact

    def extract_all(self) -> List[Dict[str, Any]]:

        results = []

        for entry in self.unresolved_entries:

            results.append(
                self.extract_fact(
                    entry
                )
            )

        return results


def extract_facts(
    unresolved_entries: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:

    extractor = FactExtractor(
        unresolved_entries
    )

    return extractor.extract_all()