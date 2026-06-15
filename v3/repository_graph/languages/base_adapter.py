"""
base_adapter.py
Extension-point interface for per-language support in Module 2.

Mirrors the philosophy of Module 1's framework_signatures.py: adding a new
language = add a new adapter file + register it in registry.py. The core
engine (graph_engine.py) does NOT need to change.

Each adapter is responsible for ONE language's files. An adapter that is
not yet implemented (is_implemented() == False) still REGISTERS its file
extensions so those files are correctly counted/categorized (per Module 1's
three-tier taxonomy: detected but not parsed) rather than silently ignored.

When an adapter's scan() IS implemented, it must return a dict shaped like
the existing 6-graph report (function_graph, class_graph, module_graph,
import_graph, dependency_graph, call_graph, unresolved, cyclic_clusters) -
the SAME shape Python's report uses - so downstream modules (Module 3+)
can consume any language's output identically.
"""

from abc import ABC, abstractmethod


class LanguageAdapter(ABC):
    """One adapter per language. Subclass and register in registry.py."""

    #: Human-readable name, e.g. "python", "java", "javascript"
    language_name: str = "unknown"

    #: File extensions this adapter handles, e.g. {".py"} or {".js", ".jsx"}
    file_extensions: set = set()

    @abstractmethod
    def is_implemented(self) -> bool:
        """Return True once scan() does real parsing for this language."""
        raise NotImplementedError

    @abstractmethod
    def scan(self, repo_root: str, file_paths: list) -> dict:
        """
        Parse `file_paths` (all files with this adapter's extensions) and
        return a report dict in the same shape as Python's
        build_repository_graph() output:

            {
              "function_graph": {...},   # V3-004
              "class_graph": {...},      # V3-005
              "module_graph": {...},     # V3-006
              "import_graph": {...},     # V3-007
              "dependency_graph": {...}, # V3-008
              "call_graph": {...},       # V3-009
              "unresolved": [...],
              "cyclic_clusters": [...],
            }

        Unimplemented adapters should return `empty_report()` (below) -
        files are still counted in the engine's file inventory, just not
        parsed (consistent with Module 1's "detected, not parsed" tiers).
        """
        raise NotImplementedError


def empty_report() -> dict:
    """Standard empty-but-valid report shape for unimplemented adapters."""
    return {
        "function_graph": {},
        "class_graph": {},
        "module_graph": {},
        "import_graph": {},
        "dependency_graph": {},
        "call_graph": {},
        "unresolved": [],
        "cyclic_clusters": [],
    }
