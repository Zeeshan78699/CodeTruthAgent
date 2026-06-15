"""
class_graph.py
V3-005: Class inheritance tree tracker

Stage A component: collects class definitions + their declared base classes
(as written in source - resolving inherited bases to fully-qualified names
happens in Stage B / reasoning layer, not here).
"""

import ast


class ClassCollector(ast.NodeVisitor):
    """Collects all class definitions and their declared bases."""

    def __init__(self, module_name):
        self.module_name = module_name
        self.classes = []
        self._scope_stack = []

    def visit_ClassDef(self, node):
        qualname = ".".join(self._scope_stack + [node.name])
        full_id = f"{self.module_name}.{qualname}"

        bases = []
        for base in node.bases:
            bases.append(_base_name(base))

        self.classes.append({
            "id": full_id,
            "name": node.name,
            "lineno": node.lineno,
            "bases": bases,   # names as written, NOT yet resolved to module paths
            "scope": ".".join(self._scope_stack) or None,
        })

        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()


def _base_name(node):
    """Render a base-class expression as a dotted string, best-effort."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_base_name(node.value)}.{node.attr}"
    return "<unresolved_base_expr>"


def build_class_graph_for_module(module_name, tree):
    """Returns list of class entries for a single module's AST tree."""
    collector = ClassCollector(module_name)
    collector.visit(tree)
    return collector.classes
