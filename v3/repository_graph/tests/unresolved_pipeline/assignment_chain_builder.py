import ast
from pathlib import Path
from typing import Dict, Any

from v3.repository_graph.module_graph import module_name_from_path


class AssignmentChainBuilder:

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.assignment_table = {}

    def _record_assignment(self, module_name: str, target_name: str, value_node):
        origin = {"origin_type": None, "origin_name": None, "module": module_name}
        if isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                origin["origin_type"] = "call"
                origin["origin_name"] = value_node.func.id
        elif isinstance(value_node, ast.Name):
            origin["origin_type"] = "variable"
            origin["origin_name"] = value_node.id
        self.assignment_table[f"{module_name}:{target_name}"] = origin

    def _scan_function(self, module_name: str, function_node):
        for node in ast.walk(function_node):
            if not isinstance(node, ast.Assign):
                continue
            if len(node.targets) != 1:
                continue
            target = node.targets[0]
            if not isinstance(target, ast.Name):
                continue
            self._record_assignment(module_name, target.id, node.value)

    def _scan_file(self, filepath: Path):
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return
        # FIX: was filepath.stem (bare filename, e.g. "app") - collides
        # across every file in the repo named the same thing, and never
        # matched the real "module" field on unresolved entries anyway
        # (which is the full dotted path, e.g. "src.flask.app"). Using
        # the same naming function the real engine uses means this
        # table's keys now actually align with what gets looked up.
        module_name = module_name_from_path(str(self.repo_root), str(filepath))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._scan_function(module_name, node)

    def build(self):
        for py_file in self.repo_root.rglob("*.py"):
            self._scan_file(py_file)
        return self.assignment_table


def build_assignment_table(repo_root: str):
    builder = AssignmentChainBuilder(repo_root)
    return builder.build()
