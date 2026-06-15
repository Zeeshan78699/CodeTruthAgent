"""
function_graph.py
V3-004: Tracks AST element (function/method) definitions

Stage A component: pure symbol collection, no relationship resolution.
"""

import ast


class FunctionCollector(ast.NodeVisitor):
    """Collects all function/method definitions in one module's AST."""

    def __init__(self, module_name):
        self.module_name = module_name
        self.functions = []
        self._scope_stack = []  # mix of class and function names, in nesting order

    def visit_ClassDef(self, node):
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_FunctionDef(self, node):
        qualname = ".".join(self._scope_stack + [node.name])
        full_id = f"{self.module_name}.{qualname}"
        self.functions.append({
            "id": full_id,
            "name": node.name,
            "lineno": node.lineno,
            "scope": ".".join(self._scope_stack) or None,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        })
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef


def build_function_graph_for_module(module_name, tree):
    """Returns list of function entries for a single module's AST tree."""
    collector = FunctionCollector(module_name)
    collector.visit(tree)
    return collector.functions
