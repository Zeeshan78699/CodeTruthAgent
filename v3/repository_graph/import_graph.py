"""
import_graph.py
V3-007: Static declaration tracing matrix

Stage A component: collects raw import statements per module.
Splitting into INTERNAL (this file's job) vs EXTERNAL (dependency_graph.py)
happens after Stage A, once the full set of project module names is known
(see graph_engine.py).
"""

import ast


class ImportCollector(ast.NodeVisitor):
    """Collects all import statements in one module."""

    def __init__(self, module_name):
        self.module_name = module_name
        self.raw_imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self.raw_imports.append({
                "from_module": self.module_name,
                "imports": alias.name,
                "type": "import",
                "lineno": node.lineno,
            })

    def visit_ImportFrom(self, node):
        target = node.module or ""
        level = node.level  # relative import dots, e.g. "from . import x" -> level=1
        for alias in node.names:
            full = f"{target}.{alias.name}" if target else alias.name
            self.raw_imports.append({
                "from_module": self.module_name,
                "imports": full,
                "type": "from_import",
                "relative_level": level,
                # D-007: kept separately so relative imports can be resolved
                # to an absolute module path using the importING module's
                # own package location (see call_graph.build_import_alias_map).
                "module_part": target,
                "symbol_part": alias.name,
                "lineno": node.lineno,
            })


def collect_raw_imports(module_name, tree):
    """Returns raw import list for a single module (unsplit internal/external)."""
    collector = ImportCollector(module_name)
    collector.visit(tree)
    return collector.raw_imports


def split_internal_external(raw_imports, project_module_roots):
    """
    Splits a list of raw import entries into (internal, external).
    project_module_roots: set of top-level package/module names that belong
    to this project (e.g. {"main", "pkg"}).
    """
    internal, external = [], []
    for entry in raw_imports:
        root = entry["imports"].split(".")[0]
        if entry.get("relative_level", 0) > 0 or root in project_module_roots:
            internal.append(entry)
        else:
            external.append(entry)
    return internal, external