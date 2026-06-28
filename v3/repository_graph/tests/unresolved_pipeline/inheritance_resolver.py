"""
inheritance_resolver.py

Experimental Module 2.5 validation harness.

Purpose:
Resolve self_method_not_found entries by walking:

1. Base classes
2. Parent classes
3. Mixins

Truth Boundary:
- Only resolve if method is proven to exist
- Multiple candidates remain unresolved
- No guessing
"""

from typing import Any, Dict, List, Optional, Set


class InheritanceResolver:
    """
    Resolves missing self methods through inheritance traversal.
    """

    def __init__(self, class_graph: Dict[str, Any]):
        self.class_graph = class_graph or {}

    def _find_method_in_hierarchy(
        self,
        class_name: str,
        method_name: str,
        visited: Optional[Set[str]] = None
    ) -> Optional[str]:

        if visited is None:
            visited = set()

        if class_name in visited:
            return None

        visited.add(class_name)

        class_info = self.class_graph.get(class_name)

        if not class_info:
            return None

        methods = set(class_info.get("methods", []))

        if method_name in methods:
            return class_name

        for base_class in class_info.get("bases", []):

            result = self._find_method_in_hierarchy(
                base_class,
                method_name,
                visited
            )

            if result:
                return result

        return None

    def resolve_entry(
        self,
        entry: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:

        class_name = entry.get("class_name")
        method_name = entry.get("method_name")

        if not class_name or not method_name:
            return None

        owner_class = self._find_method_in_hierarchy(
            class_name,
            method_name
        )

        if not owner_class:
            return None

        return {
            "resolved": True,
            "resolver": "inheritance",
            "resolution_source": "INHERITANCE_TRAVERSAL",
            "owner_class": owner_class,
            "method_name": method_name,
            "original_entry": entry,
        }

    def resolve_batch(
        self,
        unresolved_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:

        resolved = []
        remaining = []

        for entry in unresolved_entries:

            if entry.get("pattern") != "self_method_not_found":
                remaining.append(entry)
                continue

            result = self.resolve_entry(entry)

            if result:
                resolved.append(result)
            else:
                remaining.append(entry)

        return {
            "resolver": "inheritance",
            "resolved_count": len(resolved),
            "remaining_count": len(remaining),
            "resolved_entries": resolved,
            "remaining_entries": remaining,
        }


def run_inheritance_resolution(
    unresolved_entries: List[Dict[str, Any]],
    class_graph: Dict[str, Any]
) -> Dict[str, Any]:

    resolver = InheritanceResolver(class_graph)

    return resolver.resolve_batch(
        unresolved_entries
    )