"""
constructor_call_classifier.py

FIX: FRAMEWORK_HELPERS replaced with the shared
known_framework_functions.KNOWN_FRAMEWORK_FUNCTIONS - was previously
its own separate list, missing url_for and render_template_string,
which meant those calls fell through to "unknown" here and only got
correctly caught later by a different tool downstream.

Categories: constructor, factory, framework_helper, builtin, unknown
"""

import ast
from pathlib import Path
from collections import Counter

from .known_framework_functions import KNOWN_FRAMEWORK_FUNCTIONS


BUILTINS = {
    "str", "int", "bool", "dict", "list", "set", "tuple",
    "open", "iter", "next", "repr", "isinstance",
}


class ConstructorCallClassifier:

    def __init__(self, repo_root, class_name_index):
        self.repo_root = Path(repo_root)
        self.class_name_index = class_name_index
        self.results = []
        self.counter = Counter()

    def _classify_call(self, call_name):
        if call_name in self.class_name_index:
            return "constructor"
        if call_name == "cls":
            return "factory"
        if call_name in BUILTINS:
            return "builtin"
        if call_name in KNOWN_FRAMEWORK_FUNCTIONS:
            return "framework_helper"
        return "unknown"

    def _extract_call_name(self, value):
        if not isinstance(value, ast.Call):
            return None
        if isinstance(value.func, ast.Name):
            return value.func.id
        if isinstance(value.func, ast.Attribute):
            return value.func.attr
        return None

    def _scan_file(self, filepath):
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return

        for node in ast.walk(tree):
            if not isinstance(node, ast.Return):
                continue
            call_name = self._extract_call_name(node.value)
            if not call_name:
                continue
            category = self._classify_call(call_name)
            self.counter[category] += 1
            self.results.append({"call": call_name, "category": category})

    def build(self):
        for py_file in self.repo_root.rglob("*.py"):
            self._scan_file(py_file)
        return {"counts": dict(self.counter), "results": self.results}


def classify_constructor_calls(repo_root, class_name_index):
    return ConstructorCallClassifier(repo_root, class_name_index).build()
