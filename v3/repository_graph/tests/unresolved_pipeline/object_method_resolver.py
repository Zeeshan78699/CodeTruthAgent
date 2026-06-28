"""
object_method_resolver.py

FIX 1: _classify() took object_name as a parameter but never
referenced it - categories like "response_api" and "flask_test_api"
were assigned purely from the method name, with zero check on what
the object actually is. x.get_json() got called "response_api" even
if x was never shown to be a Response. Renamed to disclose these are
name-pattern heuristics, not verified categories.

FIX 2: object_name being None was displayed as the literal text
"None" in some places and "<unknown>" in others for the exact same
underlying case - standardized to "<unknown>" everywhere here, so the
benchmark script doesn't need its own separate substitution anymore.

Examples:
return app.test_client()
return app.test_cli_runner()
return response.get_json()
return self.view()
return self.finalize_request()

Truth Boundary:
- Classification only
- No guessing
- No runtime execution
"""

import ast
from pathlib import Path
from collections import Counter


class ObjectMethodResolver:

    def __init__(self, repo_root):
        self.repo_root = Path(repo_root)
        self.counter = Counter()
        self.examples = {}
        self.results = []

    def _extract_method_call(self, value):
        if not isinstance(value, ast.Call):
            return None
        if not isinstance(value.func, ast.Attribute):
            return None

        object_name = None
        if isinstance(value.func.value, ast.Name):
            object_name = value.func.value.id

        method_name = value.func.attr
        return (object_name, method_name)

    def _classify(self, object_name, method_name):
        # FIX: renamed to disclose these are method-name heuristics,
        # not proven facts about the object's type.
        if method_name in {"test_client", "test_cli_runner"}:
            return "method_name_suggests_flask_test_api_unconfirmed"

        if method_name in {"get_json", "response"}:
            return "method_name_suggests_response_api_unconfirmed"

        if method_name in {"run", "finalize_request"}:
            return "method_name_suggests_app_lifecycle_unconfirmed"

        if method_name in {"view", "dispatch_request"}:
            return "method_name_suggests_view_dispatch_unconfirmed"

        return "generic_method"

    def _scan_file(self, filepath):
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            return

        for node in ast.walk(tree):
            if not isinstance(node, ast.Return):
                continue
            extracted = self._extract_method_call(node.value)
            if not extracted:
                continue
            object_name, method_name = extracted
            category = self._classify(object_name, method_name)

            self.counter[category] += 1
            self.examples.setdefault(category, [])
            if len(self.examples[category]) < 20:
                # FIX: substitute "<unknown>" here, once, so every
                # consumer of .examples sees the same label as
                # .results does - no more None vs "<unknown>" drift.
                self.examples[category].append((object_name or "<unknown>", method_name))

            self.results.append({
                "object": object_name or "<unknown>",
                "method": method_name,
                "category": category,
            })

    def build(self):
        for py_file in self.repo_root.rglob("*.py"):
            self._scan_file(py_file)
        return {"counts": dict(self.counter), "examples": self.examples, "results": self.results}


def analyze_object_methods(repo_root):
    return ObjectMethodResolver(repo_root).build()
