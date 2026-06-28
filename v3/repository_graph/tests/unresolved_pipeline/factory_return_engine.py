"""
factory_return_engine.py

Experimental Module 2.5 validation harness.

Purpose:
Resolve attribute calls that originate from
proven factory-function return types.

Example:

app = create_app()
app.run()

If:

create_app() -> Flask

Then:

app.run() -> Flask.run()

Truth Boundary:
- Factory return type must be proven
- Class must exist
- Method must exist
- No guessing
"""

from typing import Any, Dict, List, Optional


class FactoryReturnEngine:

    def __init__(
        self,
        extracted_facts: List[Dict[str, Any]],
        return_type_table: Dict[str, str],
        class_graph: Dict[str, Any]
    ):
        self.extracted_facts = (
            extracted_facts or []
        )

        self.return_type_table = (
            return_type_table or {}
        )

        self.class_graph = (
            class_graph or {}
        )

    def _method_exists(
        self,
        class_name: str,
        method_name: str
    ) -> bool:

        class_info = self.class_graph.get(
            class_name
        )

        if not class_info:
            return False

        methods = set(
            class_info.get(
                "methods",
                []
            )
        )

        return method_name in methods

    def resolve_fact(
        self,
        fact: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        factory_function = fact.get(
            "factory_function"
        )

        attribute_name = fact.get(
            "attribute_name"
        )

        if not factory_function:
            return None

        if not attribute_name:
            return None

        inferred_type = (
            self.return_type_table.get(
                factory_function
            )
        )

        if not inferred_type:
            return None

        if not self._method_exists(
            inferred_type,
            attribute_name
        ):
            return None

        return {
            "resolved": True,

            "resolver":
                "factory_return_engine",

            "factory_function":
                factory_function,

            "return_type":
                inferred_type,

            "method_name":
                attribute_name,

            "resolution_source":
                "RETURN_TYPE_TABLE",

            "original_fact":
                fact,
        }

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
                "factory_return_engine",

            "resolved_count":
                len(resolved),

            "remaining_count":
                len(remaining),

            "resolved_entries":
                resolved,

            "remaining_entries":
                remaining,
        }


def run_factory_return_engine(
    extracted_facts: List[Dict[str, Any]],
    return_type_table: Dict[str, str],
    class_graph: Dict[str, Any]
):

    engine = FactoryReturnEngine(
        extracted_facts=extracted_facts,
        return_type_table=return_type_table,
        class_graph=class_graph,
    )

    return engine.resolve_batch()