"""
inheritance_resolver.py

FIX (main-pipeline integration): class_graph is now keyed by fully
qualified name ("module.ClassName"), not bare name - see
flatten_class_graph.py for why. The starting class for a given
unresolved entry is qualified directly using entry["module"] +
entry["class_name"] (reliable: a method's enclosing class is always
defined in the same file as the method itself). Base classes inside
class_info["bases"], however, are stored as bare names as written in
source - which module they actually live in isn't known without
resolving that module's own import aliases (real work not built here).
So base-class resolution tries the SAME module as the current class
first (the common case - a class and its base both defined locally),
and only falls back to the disclosed, ambiguity-aware bare_name_index
when that fails - never silently guessing among multiple same-named
candidates.
"""

from typing import Any, Dict, List, Optional, Set


class InheritanceResolver:
    def __init__(self, class_graph: Dict[str, Any], bare_name_index: Dict[str, List[str]] = None):
        self.class_graph = class_graph or {}
        self.bare_name_index = bare_name_index or {}

    def _resolve_base_name(self, base_name, current_module):
        """Same-module guess first (most common real case), then the
        disclosed, ambiguity-aware fallback - never guesses among
        multiple same-named candidates."""
        same_module_candidate = f"{current_module}.{base_name}"
        if same_module_candidate in self.class_graph:
            return same_module_candidate
        matches = self.bare_name_index.get(base_name)
        if matches and len(matches) == 1:
            return matches[0]
        return None

    def _find_method_in_hierarchy(self, qualified_class_name, method_name, visited=None):
        if visited is None:
            visited = set()
        if qualified_class_name in visited:
            return None
        visited.add(qualified_class_name)
        class_info = self.class_graph.get(qualified_class_name)
        if not class_info:
            return None
        methods = set(class_info.get("methods", []))
        if method_name in methods:
            return qualified_class_name
        current_module = class_info.get("module")
        for base_name in class_info.get("bases", []):
            qualified_base = self._resolve_base_name(base_name, current_module)
            if not qualified_base:
                continue  # genuinely unresolvable base, not guessed - correctly stays unresolved
            result = self._find_method_in_hierarchy(qualified_base, method_name, visited)
            if result:
                return result
        return None

    def resolve_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        class_name = entry.get("class_name")
        method_name = entry.get("method_name")
        module = entry.get("module")
        if not class_name or not method_name or not module:
            return None
        qualified_class_name = f"{module}.{class_name}"
        owner_class = self._find_method_in_hierarchy(qualified_class_name, method_name)
        if not owner_class:
            return None
        return {
            "resolved": True, "resolver": "inheritance",
            "resolution_source": "INHERITANCE_TRAVERSAL",
            "owner_class": owner_class, "method_name": method_name,
            "original_entry": entry,
        }

    def resolve_batch(self, unresolved_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        resolved, remaining = [], []
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
            "resolver": "inheritance", "resolved_count": len(resolved),
            "remaining_count": len(remaining), "resolved_entries": resolved,
            "remaining_entries": remaining,
        }


def run_inheritance_resolution(unresolved_entries, class_graph, bare_name_index=None):
    resolver = InheritanceResolver(class_graph, bare_name_index=bare_name_index)
    return resolver.resolve_batch(unresolved_entries)
