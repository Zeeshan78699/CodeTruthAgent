"""
property_type_table_builder.py

FIX (main-pipeline integration): class_graph is now keyed by fully
qualified name, not bare name (see flatten_class_graph.py). A
class-level property assignment like `response_class = Response`
only ever has the bare name "Response" available syntactically -
resolved via the same disclosed, ambiguity-aware bare_name_index
fallback used elsewhere in this resolver set, and the QUALIFIED name
is what gets stored in property_type_table going forward, so
downstream consumers (property_type_engine.py) can do a direct,
unambiguous lookup without needing their own fallback.
"""

import ast
from pathlib import Path
from typing import Dict, Any

from .flatten_class_graph import resolve_bare_class_name


class PropertyTypeTableBuilder:
    def __init__(self, repo_root: str, class_graph: Dict[str, Any], bare_name_index: Dict[str, Any] = None):
        self.repo_root = Path(repo_root)
        self.class_graph = class_graph or {}
        self.bare_name_index = bare_name_index or {}
        self.property_type_table = {}

    def _resolve_known_class(self, class_name: str):
        return resolve_bare_class_name(class_name, self.bare_name_index)

    def _process_class(self, node: ast.ClassDef):
        for item in node.body:
            if not isinstance(item, ast.Assign):
                continue
            if len(item.targets) != 1:
                continue
            target = item.targets[0]
            if not isinstance(target, ast.Name):
                continue
            property_name = target.id
            value = item.value
            if isinstance(value, ast.Name):
                candidate_type = value.id
                qualified = self._resolve_known_class(candidate_type)
                if qualified:
                    self.property_type_table[property_name] = qualified

    def _scan_file(self, filepath: Path):
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._process_class(node)

    def build(self):
        for py_file in self.repo_root.rglob("*.py"):
            self._scan_file(py_file)
        return self.property_type_table


def build_property_type_table(repo_root: str, class_graph: Dict[str, Any], bare_name_index: Dict[str, Any] = None):
    builder = PropertyTypeTableBuilder(repo_root, class_graph, bare_name_index=bare_name_index)
    return builder.build()
