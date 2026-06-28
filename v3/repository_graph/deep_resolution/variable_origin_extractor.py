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

FIX (deep resolution at scale - found via Django, 104,941 unresolved
entries): the original version re-walked the ENTIRE file AST from
scratch on EVERY call to extract_variable_name, even though the tree
itself was cached. Fine for Flask's ~2,700 entries; on Django's scale
this never finished within a reasonable time, since the same file's
full tree gets walked again and again, once per fact querying it. Now
builds a (lineno, attribute_name) -> variable_name INDEX once per
module on first access, alongside the tree cache - the walk happens
once per module total, not once per fact, regardless of how many
facts end up querying that same module.
"""

import ast
from pathlib import Path
from typing import Dict, Optional, Tuple


class VariableOriginExtractor:

    def __init__(self, repo_root: str, module_graph: Dict[str, Dict]):
        self.repo_root = Path(repo_root)
        # module_graph: {"module.name": {"path": "/abs/path/to/file.py", ...}}
        # as produced by module_graph.build_module_graph() / PythonAdapter.
        self.module_graph = module_graph or {}
        self._index_cache: Dict[str, Dict[Tuple[int, str], str]] = {}

    def _get_index(self, module_name: str) -> Dict[Tuple[int, str], str]:
        """
        Builds (and caches) the full (lineno, attribute_name) ->
        variable_name index for a module in ONE pass, the first time
        it's needed - every subsequent fact querying the same module
        is then an O(1) dict lookup instead of a fresh tree walk.
        """
        if module_name in self._index_cache:
            return self._index_cache[module_name]

        index: Dict[Tuple[int, str], str] = {}
        entry = self.module_graph.get(module_name)
        if entry and entry.get("path"):
            try:
                source = Path(entry["path"]).read_text(encoding="utf-8")
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    if not isinstance(node.func, ast.Attribute):
                        continue
                    if not isinstance(node.func.value, ast.Name):
                        continue
                    key = (node.lineno, node.func.attr)
                    # FIX consideration: if the same (lineno, attribute)
                    # appears more than once on one line (e.g. two
                    # chained calls to the same method name at the same
                    # line), this keeps the first - same conservative
                    # behavior as the original line-by-line ast.walk
                    # match, which also returned on first match found.
                    if key not in index:
                        index[key] = node.func.value.id
            except (SyntaxError, UnicodeDecodeError, OSError):
                pass

        self._index_cache[module_name] = index
        return index

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
        index = self._get_index(module_name)
        return index.get((lineno, attribute_name))