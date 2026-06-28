"""
builtin_type_engine.py

Experimental Module 2.5 validation harness.

Purpose:
Resolve attribute calls that belong to well-known
Python builtin types.

Truth Boundary:
- Resolve only from proven builtin method tables
- Never infer variable type
- Never guess
"""

from typing import Any, Dict, List, Optional


BUILTIN_METHODS = {
    "str": {
        "endswith",
        "startswith",
        "strip",
        "lstrip",
        "rstrip",
        "split",
        "rsplit",
        "replace",
        "lower",
        "upper",
        "title",
        "join",
        "format",
        "encode",
    },

    "list": {
        "append",
        "extend",
        "insert",
        "remove",
        "pop",
        "clear",
        "sort",
        "reverse",
        "copy",
        "count",
        "index",
    },

    "dict": {
        "get",
        "keys",
        "values",
        "items",
        "update",
        "pop",
        "popitem",
        "clear",
        "copy",
        "setdefault",
    },

    "set": {
        "add",
        "remove",
        "discard",
        "union",
        "intersection",
        "difference",
        "update",
    }
}


class BuiltinTypeEngine:

    def __init__(
        self,
        extracted_facts: List[Dict[str, Any]]
    ):
        self.extracted_facts = (
            extracted_facts or []
        )

    def resolve_fact(
        self,
        fact: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        attribute_name = fact.get(
            "attribute_name"
        )

        if not attribute_name:
            return None

        for builtin_type, methods in (
            BUILTIN_METHODS.items()
        ):

            if attribute_name in methods:

                return {
                    "resolved": True,
                    "resolver":
                        "builtin_type_engine",

                    "builtin_type":
                        builtin_type,

                    "attribute":
                        attribute_name,

                    "resolution_source":
                        "BUILTIN_METHOD_TABLE",

                    "original_fact":
                        fact,
                }

        return None

    def resolve_batch(self):

        resolved = []
        remaining = []

        for fact in self.extracted_facts:

            if (
                fact.get("pattern")
                != "attribute_call"
            ):
                remaining.append(fact)
                continue

            result = self.resolve_fact(
                fact
            )

            if result:
                resolved.append(result)
            else:
                remaining.append(fact)

        return {
            "resolver":
                "builtin_type_engine",

            "resolved_count":
                len(resolved),

            "remaining_count":
                len(remaining),

            "resolved_entries":
                resolved,

            "remaining_entries":
                remaining,
        }


def run_builtin_type_engine(
    extracted_facts: List[Dict[str, Any]]
):

    engine = BuiltinTypeEngine(
        extracted_facts
    )

    return engine.resolve_batch()