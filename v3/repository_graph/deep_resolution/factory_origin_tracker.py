from typing import Dict, Any

FACTORY_PREFIXES = {"create_", "build_", "get_", "make_", "load_"}


class FactoryOriginTracker:
    def __init__(self, assignment_table: Dict[str, Any], class_graph: Dict[str, Any]):
        self.assignment_table = assignment_table or {}
        self.class_graph = class_graph or {}

    def _looks_like_factory(self, function_name: str) -> bool:
        if not function_name:
            return False
        if function_name in self.class_graph:
            return False
        for prefix in FACTORY_PREFIXES:
            if function_name.startswith(prefix):
                return True
        return False

    def build(self):
        results = {}
        for variable_key, origin in self.assignment_table.items():
            if origin.get("origin_type") != "call":
                continue
            candidate = origin.get("origin_name")
            if not self._looks_like_factory(candidate):
                continue
            results[variable_key] = {"factory_function": candidate, "source": "FACTORY"}
        return results


def build_factory_origins(assignment_table, class_graph):
    tracker = FactoryOriginTracker(assignment_table, class_graph)
    return tracker.build()
