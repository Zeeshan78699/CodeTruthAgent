import ast
from pathlib import Path
from typing import Dict, Set, Optional

from .flatten_class_graph import flatten_class_graph


class ReturnFlowTrackerV2:
    """
    FIX: was checking `candidate in self.class_graph` against the raw,
    module-keyed class_graph - same root cause fixed elsewhere. Now
    flattens internally and exposes class_name_index (the flattened
    class graph's key set) for downstream classifiers
    (constructor_call_classifier.py etc.) to reuse without each
    re-flattening it themselves.
    """
    def __init__(self, repo_root: str, class_graph: Dict, function_graph: Dict = None):
        self.repo_root = Path(repo_root)
        self.class_graph = flatten_class_graph(class_graph or {}, function_graph or {})
        self.class_name_index = set(self.class_graph.keys())
        self.return_type_table = {}

    def _collect_imports(self, tree):
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imports[alias.asname or alias.name] = alias.name
        return imports

    def _collect_assignments(self, function_node):
        assignments = {}
        for node in ast.walk(function_node):
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            assignments[target.id] = node.value
        return assignments

    def _resolve_call_type(self, call_node, imports) -> Optional[str]:
        if not isinstance(call_node, ast.Call):
            return None
        if isinstance(call_node.func, ast.Name):
            candidate = call_node.func.id
            if candidate in self.class_graph:
                return candidate
            imported = imports.get(candidate)
            if imported and imported in self.class_graph:
                return imported
        return None

    def _process_function(self, function_node, imports):
        function_name = function_node.name
        assignments = self._collect_assignments(function_node)
        return_types: Set[str] = set()
        for node in ast.walk(function_node):
            if not isinstance(node, ast.Return):
                continue
            value = node.value
            resolved = self._resolve_call_type(value, imports)
            if resolved:
                return_types.add(resolved)
                continue
            if isinstance(value, ast.Name):
                origin = assignments.get(value.id)
                resolved = self._resolve_call_type(origin, imports)
                if resolved:
                    return_types.add(resolved)
        if len(return_types) == 1:
            self.return_type_table[function_name] = next(iter(return_types))

    def _scan_file(self, filepath):
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return
        imports = self._collect_imports(tree)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_function(node, imports)

    def build(self):
        for py_file in self.repo_root.rglob("*.py"):
            self._scan_file(py_file)
        return self.return_type_table


def build_return_type_table_v2(repo_root, class_graph):
    tracker = ReturnFlowTrackerV2(repo_root, class_graph)
    return tracker.build()
