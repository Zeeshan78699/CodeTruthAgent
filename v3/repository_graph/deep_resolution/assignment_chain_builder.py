import ast
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from v3.repository_graph.module_graph import module_name_from_path


class AssignmentChainBuilder:

    def __init__(self, repo_root: str, rename_fn: Optional[Callable[[str], str]] = None):
        self.repo_root = Path(repo_root)
        self.assignment_table = {}
        # FIX: this builder used to compute module names independently
        # via module_name_from_path(repo_root, ...) on the raw,
        # unmodified repo_root - meaning for any repo where the
        # src-layout fix applies (subtree_naming.py), this table's keys
        # ("src.flask.app:app") never matched the report's actual,
        # renamed module names ("flask.app:app") used everywhere else -
        # silently breaking origin lookups for every file under src/,
        # while files outside it (tests/, examples/) happened to still
        # work, since they were never renamed either way. rename_fn
        # lets the caller apply the SAME rename this report already
        # applied elsewhere - identity (no-op) by default, so behavior
        # is unchanged for any repo where no rename ever applies.
        self.rename_fn = rename_fn or (lambda name: name)

    def _record_assignment(self, module_name: str, target_name: str, value_node):
        origin = {"origin_type": None, "origin_name": None, "module": module_name}
        if isinstance(value_node, ast.Call):
            if isinstance(value_node.func, ast.Name):
                origin["origin_type"] = "call"
                origin["origin_name"] = value_node.func.id
            elif isinstance(value_node.func, ast.Attribute):
                # FIX (found via deeper testing on httpx): a factory
                # implemented as a METHOD (self.build_request()) or a
                # cross-module constructor (flask.Flask()) was
                # previously invisible here - only bare Name calls were
                # recorded. The rightmost name (.attr) is what
                # downstream lookups (factory_return_engine,
                # bare_name_index) already match against regardless of
                # whether the original call was a bare name or an
                # attribute access, so this is a real, not just
                # cosmetic, fix.
                origin["origin_type"] = "call"
                origin["origin_name"] = value_node.func.attr
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
        # rename_fn applied on top so this stays aligned even after the
        # src-layout rename has been applied to the rest of the report.
        module_name = self.rename_fn(module_name_from_path(str(self.repo_root), str(filepath)))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._scan_function(module_name, node)

    def build(self):
        for py_file in self.repo_root.rglob("*.py"):
            self._scan_file(py_file)
        return self.assignment_table


def build_assignment_table(repo_root: str, rename_fn: Optional[Callable[[str], str]] = None):
    builder = AssignmentChainBuilder(repo_root, rename_fn=rename_fn)
    return builder.build()