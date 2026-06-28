"""
variable_origin_extractor.py

The deeper fix needed beyond flatten_class_graph.py: even with the
class-graph shape corrected, constructor_tracking_engine.py and
factory_return_engine.py can never find anything, because the
unresolved note for attribute_call entries was never given the
variable name in the first place. call_graph.py's
_resolve_attribute_call only records the attribute being accessed
(".run(...)"), never what it was called on ("app") - that information
is computed locally (the `root` variable in _flatten_attribute) but
discarded, not written into the note. So no amount of regex over
"note" could ever recover it; fact_extractor.py was extracting from
text that simply never had this in it.

This re-parses the actual source line - every unresolved entry already
carries (module, lineno), enough to find the real AST node again - and
pulls out the variable name directly, but ONLY for the simple, safe
case: a bare Name on the left of the dot (app.run() -> "app"). Chained
access (a.b.run()) or a call expression (get_x().run()) stay correctly
unresolved here too, since there's no single local variable to trace
back through the assignment table.

Truth Boundary: only a literal local variable name is extracted; no
inference, no guessing about more complex expressions.
"""

import ast
from pathlib import Path
from typing import Dict, Optional


class VariableOriginExtractor:

    def __init__(self, repo_root: str, module_graph: Dict[str, Dict]):
        self.repo_root = Path(repo_root)
        # module_graph: {"module.name": {"path": "/abs/path/to/file.py", ...}}
        # as produced by module_graph.build_module_graph() / PythonAdapter.
        self.module_graph = module_graph or {}
        self._tree_cache: Dict[str, Optional[ast.AST]] = {}

    def _get_tree(self, module_name: str) -> Optional[ast.AST]:
        if module_name in self._tree_cache:
            return self._tree_cache[module_name]

        entry = self.module_graph.get(module_name)
        tree = None
        if entry and entry.get("path"):
            try:
                source = Path(entry["path"]).read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (SyntaxError, UnicodeDecodeError, OSError):
                tree = None

        self._tree_cache[module_name] = tree
        return tree

    def extract_variable_name(
        self,
        module_name: str,
        lineno: int,
        attribute_name: str,
    ) -> Optional[str]:
        """
        Returns the bare variable name an attribute call was made on
        (e.g. "app" for app.run()), or None if the call isn't found,
        the line doesn't match, or the call target isn't a simple
        local variable.
        """
        tree = self._get_tree(module_name)
        if tree is None:
            return None

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if node.lineno != lineno:
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != attribute_name:
                continue
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id

        return None
