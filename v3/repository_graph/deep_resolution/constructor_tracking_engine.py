from typing import Any, Dict, List, Optional


class ConstructorTrackingEngine:
    def __init__(self, extracted_facts: List[Dict[str, Any]], class_graph: Dict[str, Any]):
        self.extracted_facts = extracted_facts or []
        self.class_graph = class_graph or {}

    def _method_exists(self, class_name, method_name) -> bool:
        class_info = self.class_graph.get(class_name)
        if not class_info:
            return False
        methods = set(class_info.get("methods", []))
        return method_name in methods

    def resolve_fact(self, fact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        constructor_class = fact.get("constructor_class")
        attribute_name = fact.get("attribute_name")
        if not constructor_class or not attribute_name:
            return None
        if not self._method_exists(constructor_class, attribute_name):
            return None
        return {"resolved": True, "resolver": "constructor_tracking_engine", "constructor_class": constructor_class,
                "method_name": attribute_name, "resolution_source": "CONSTRUCTOR_ASSIGNMENT", "original_fact": fact}

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
        return {"resolver": "constructor_tracking_engine", "resolved_count": len(resolved), "remaining_count": len(remaining),
                "resolved_entries": resolved, "remaining_entries": remaining}


def run_constructor_tracking_engine(extracted_facts, class_graph):
    return ConstructorTrackingEngine(extracted_facts, class_graph).resolve_batch()
