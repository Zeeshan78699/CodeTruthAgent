"""
factory_return_engine.py

FIX (main-pipeline integration): class_graph is now keyed by fully
qualified name, not bare name. inferred_type (from
flat_return_type_table) is a bare class name - the call site
("x = create_app()") only ever has that available without resolving
that module's own import aliases, a real, disclosed limitation (see
flatten_class_graph.py's flatten_return_type_table docstring).
Resolved via the same ambiguity-aware bare_name_index fallback used
elsewhere - skips rather than guesses when the bare name matches more
than one class repo-wide.
"""

from typing import Any, Dict, List, Optional

from .flatten_class_graph import resolve_bare_class_name


class FactoryReturnEngine:
    def __init__(self, extracted_facts, return_type_table, class_graph, bare_name_index=None):
        self.extracted_facts = extracted_facts or []
        self.return_type_table = return_type_table or {}
        self.class_graph = class_graph or {}
        self.bare_name_index = bare_name_index or {}

    def _method_exists(self, bare_class_name, method_name) -> bool:
        qualified = resolve_bare_class_name(bare_class_name, self.bare_name_index)
        if not qualified:
            return False
        class_info = self.class_graph.get(qualified)
        if not class_info:
            return False
        methods = set(class_info.get("methods", []))
        return method_name in methods

    def resolve_fact(self, fact):
        factory_function = fact.get("factory_function")
        attribute_name = fact.get("attribute_name")
        if not factory_function or not attribute_name:
            return None
        inferred_type = self.return_type_table.get(factory_function)
        if not inferred_type:
            return None
        if not self._method_exists(inferred_type, attribute_name):
            return None
        return {"resolved": True, "resolver": "factory_return_engine", "factory_function": factory_function,
                "return_type": inferred_type, "method_name": attribute_name,
                "resolution_source": "RETURN_TYPE_TABLE", "original_fact": fact}

    def resolve_batch(self):
        resolved, remaining = [], []
        for fact in self.extracted_facts:
            if fact.get("pattern") != "attribute_call":
                remaining.append(fact)
                continue
            result = self.resolve_fact(fact)
            if result:
                resolved.append(result)
            else:
                remaining.append(fact)
        return {"resolver": "factory_return_engine", "resolved_count": len(resolved), "remaining_count": len(remaining),
                "resolved_entries": resolved, "remaining_entries": remaining}


def run_factory_return_engine(extracted_facts, return_type_table, class_graph, bare_name_index=None):
    return FactoryReturnEngine(extracted_facts, return_type_table, class_graph, bare_name_index=bare_name_index).resolve_batch()
