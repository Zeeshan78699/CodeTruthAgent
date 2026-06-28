"""
reflection_resolver.py

Experimental Module 2.5 validation harness.

Purpose:
Resolve safe reflection patterns where the target
method/property name is statically known.

Examples:

getattr(obj, "run")
getattr(service, "process")

Truth Boundary:
- Literal strings only
- Dynamic strings remain unresolved
- No guessing
"""

from typing import Any, Dict, List, Optional


class ReflectionResolver:
    """
    Resolves deterministic getattr patterns.
    """

    def __init__(self, class_graph: Dict[str, Any]):
        self.class_graph = class_graph or {}

    def _method_exists(
        self,
        class_name: str,
        method_name: str
    ) -> bool:

        class_info = self.class_graph.get(class_name)

        if not class_info:
            return False

        methods = set(class_info.get("methods", []))

        return method_name in methods

    def resolve_entry(
        self,
        entry: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        class_name = entry.get("class_name")
        reflection_name = entry.get("reflection_name")

        if not class_name:
            return None

        if not reflection_name:
            return None

        if not isinstance(reflection_name, str):
            return None

        if not self._method_exists(
            class_name,
            reflection_name
        ):
            return None

        return {
            "resolved": True,
            "resolver": "reflection",
            "resolution_source": "STATIC_GETATTR",
            "class_name": class_name,
            "method_name": reflection_name,
            "original_entry": entry,
        }

    def resolve_batch(
        self,
        unresolved_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        resolved = []
        remaining = []

        for entry in unresolved_entries:

            if entry.get("cause") != "reflection_or_dynamic_attribute":
                remaining.append(entry)
                continue

            result = self.resolve_entry(entry)

            if result:
                resolved.append(result)
            else:
                remaining.append(entry)

        return {
            "resolver": "reflection",
            "resolved_count": len(resolved),
            "remaining_count": len(remaining),
            "resolved_entries": resolved,
            "remaining_entries": remaining,
        }


def run_reflection_resolution(
    unresolved_entries: List[Dict[str, Any]],
    class_graph: Dict[str, Any]
) -> Dict[str, Any]:

    resolver = ReflectionResolver(class_graph)

    return resolver.resolve_batch(
        unresolved_entries
    )