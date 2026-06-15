"""
test_module2_repository_graph.py
CodeTruth Agent V3 - Module 2 - Unit Tests

Tests the 6 core graph builders (V3-004 through V3-009) using small,
self-contained temporary repos with known expected output.

Run from project root:
    python -m pytest v3/repository_graph/tests/test_module2_repository_graph.py -v
"""

import sys
import os
import ast
import tempfile
import shutil
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.graph_engine import build_repository_graph, find_python_files
from v3.repository_graph.module_graph import module_name_from_path, build_module_graph
from v3.repository_graph.function_graph import build_function_graph_for_module
from v3.repository_graph.class_graph import build_class_graph_for_module
from v3.repository_graph.import_graph import collect_raw_imports, split_internal_external
from v3.repository_graph.dependency_graph import build_dependency_graph


def write_files(root, files: dict):
    """files: {relative_path: content}"""
    for rel_path, content in files.items():
        full_path = os.path.join(root, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)


class TestModuleNameFromPath(unittest.TestCase):
    """V3-006 helper: path -> module name conversion."""

    def test_simple_file(self):
        self.assertEqual(
            module_name_from_path("/root", "/root/main.py"), "main"
        )

    def test_nested_file(self):
        self.assertEqual(
            module_name_from_path("/root", "/root/pkg/utils.py"), "pkg.utils"
        )

    def test_init_file_collapses_to_package(self):
        self.assertEqual(
            module_name_from_path("/root", "/root/pkg/__init__.py"), "pkg"
        )


class TestFunctionGraph(unittest.TestCase):
    """V3-004: function/method definition tracking."""

    def setUp(self):
        self.source = """
def top_level_func():
    pass

class Foo:
    def method_a(self):
        pass

    def method_b(self):
        def nested():
            pass

async def async_func():
    pass
"""
        self.tree = ast.parse(self.source)

    def test_top_level_function_found(self):
        funcs = build_function_graph_for_module("mymod", self.tree)
        names = {f["name"] for f in funcs}
        self.assertIn("top_level_func", names)

    def test_class_methods_have_class_scope(self):
        funcs = build_function_graph_for_module("mymod", self.tree)
        method_a = next(f for f in funcs if f["name"] == "method_a")
        self.assertEqual(method_a["scope"], "Foo")
        self.assertEqual(method_a["id"], "mymod.Foo.method_a")

    def test_nested_function_has_compound_scope(self):
        funcs = build_function_graph_for_module("mymod", self.tree)
        nested = next(f for f in funcs if f["name"] == "nested")
        self.assertEqual(nested["scope"], "Foo.method_b")

    def test_async_function_flagged(self):
        funcs = build_function_graph_for_module("mymod", self.tree)
        async_f = next(f for f in funcs if f["name"] == "async_func")
        self.assertTrue(async_f["is_async"])


class TestClassGraph(unittest.TestCase):
    """V3-005: class inheritance tracking."""

    def setUp(self):
        self.source = """
class Base:
    pass

class Child(Base):
    pass

import ast
class Visitor(ast.NodeVisitor):
    pass
"""
        self.tree = ast.parse(self.source)

    def test_classes_found(self):
        classes = build_class_graph_for_module("mymod", self.tree)
        names = {c["name"] for c in classes}
        self.assertEqual(names, {"Base", "Child", "Visitor"})

    def test_simple_inheritance_base_captured(self):
        classes = build_class_graph_for_module("mymod", self.tree)
        child = next(c for c in classes if c["name"] == "Child")
        self.assertEqual(child["bases"], ["Base"])

    def test_dotted_base_captured(self):
        classes = build_class_graph_for_module("mymod", self.tree)
        visitor = next(c for c in classes if c["name"] == "Visitor")
        self.assertEqual(visitor["bases"], ["ast.NodeVisitor"])

    def test_no_base_is_empty_list(self):
        classes = build_class_graph_for_module("mymod", self.tree)
        base = next(c for c in classes if c["name"] == "Base")
        self.assertEqual(base["bases"], [])


class TestImportGraphSplit(unittest.TestCase):
    """V3-007/V3-008: internal vs external import classification."""

    def setUp(self):
        self.source = """
import os
import json
from pkg.utils import helper
from . import sibling
"""
        self.tree = ast.parse(self.source)

    def test_raw_imports_collected(self):
        raw = collect_raw_imports("main", self.tree)
        targets = {r["imports"] for r in raw}
        self.assertIn("os", targets)
        self.assertIn("json", targets)
        self.assertIn("pkg.utils.helper", targets)

    def test_internal_external_split(self):
        raw = collect_raw_imports("main", self.tree)
        internal, external = split_internal_external(raw, project_module_roots={"pkg"})
        internal_targets = {r["imports"] for r in internal}
        external_targets = {r["imports"] for r in external}

        self.assertIn("pkg.utils.helper", internal_targets)
        self.assertIn("os", external_targets)
        self.assertIn("json", external_targets)

    def test_relative_import_is_internal(self):
        raw = collect_raw_imports("main", self.tree)
        internal, external = split_internal_external(raw, project_module_roots=set())
        internal_targets = {r["imports"] for r in internal}
        # "from . import sibling" -> relative_level=1 -> always internal
        self.assertIn("sibling", internal_targets)


class TestDependencyGraph(unittest.TestCase):
    """V3-008: external package aggregation."""

    def test_aggregates_usage_across_modules(self):
        external_imports = {
            "main": [{"imports": "os.path", "type": "import", "lineno": 1}],
            "pkg.utils": [{"imports": "os", "type": "import", "lineno": 1}],
        }
        deps = build_dependency_graph(external_imports)
        self.assertIn("os", deps)
        self.assertEqual(deps["os"]["import_count"], 2)
        self.assertEqual(set(deps["os"]["used_by"]), {"main", "pkg.utils"})


class TestGraphEngineEndToEnd(unittest.TestCase):
    """Full engine: build_repository_graph() on a small synthetic repo."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="module2_test_")
        write_files(cls.tmpdir, {
            "main.py": (
                "from pkg.utils import helper, Greeter\n"
                "import os\n"
                "\n"
                "def main():\n"
                "    g = Greeter('World')\n"
                "    helper()\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            "pkg/__init__.py": "",
            "pkg/utils.py": (
                "import json\n"
                "\n"
                "def helper():\n"
                "    return load_config()\n"
                "\n"
                "def load_config():\n"
                "    return json.dumps({'ok': True})\n"
                "\n"
                "class Greeter:\n"
                "    def __init__(self, name):\n"
                "        self.name = name\n"
                "\n"
                "    def greet(self):\n"
                "        helper()\n"
            ),
        })
        cls.report = build_repository_graph(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def test_files_scanned_count(self):
        self.assertEqual(self.report["files_scanned"], 3)

    def test_governance_gate_approved(self):
        self.assertEqual(self.report["governance_gate"], "APPROVED")

    def test_function_graph_v3_004(self):
        funcs = self.report["function_graph"]["pkg.utils"]
        names = {f["name"] for f in funcs}
        self.assertEqual(names, {"helper", "load_config", "__init__", "greet"})

    def test_class_graph_v3_005(self):
        classes = self.report["class_graph"]["pkg.utils"]
        self.assertEqual([c["name"] for c in classes], ["Greeter"])

    def test_module_graph_v3_006_package_detection(self):
        mg = self.report["module_graph"]
        self.assertTrue(mg["pkg"]["is_package"])
        self.assertFalse(mg["main"]["is_package"])
        self.assertEqual(mg["pkg.utils"]["parent"], "pkg")

    def test_import_graph_v3_007_internal_only(self):
        ig = self.report["import_graph"]["main"]
        imported = {e["imports"] for e in ig}
        self.assertIn("pkg.utils.helper", imported)
        self.assertIn("pkg.utils.Greeter", imported)
        self.assertNotIn("os", imported)  # os is external, not in import_graph

    def test_dependency_graph_v3_008_external_only(self):
        dg = self.report["dependency_graph"]
        self.assertIn("os", dg)
        self.assertIn("json", dg)
        self.assertNotIn("pkg", dg)

    def test_call_graph_v3_009_cross_module_resolution(self):
        """D-001: helper() called from main.py must resolve to pkg.utils.helper,
        not be left unresolved."""
        all_calls = [e for edges in self.report["call_graph"].values() for e in edges]
        callees = {c["callee"] for c in all_calls}
        self.assertIn("pkg.utils.helper", callees)

    def test_call_graph_constructor_resolution(self):
        """D-002: Greeter('World') must resolve to Greeter.__init__."""
        all_calls = [e for edges in self.report["call_graph"].values() for e in edges]
        callees = {c["callee"] for c in all_calls}
        self.assertIn("pkg.utils.Greeter.__init__", callees)

    def test_call_graph_self_method_resolution(self):
        """self.name = name inside __init__ is an assignment, not a call -
        but helper() inside greet() (same-module direct call) must resolve."""
        utils_calls = self.report["call_graph"]["pkg.utils"]
        resolutions = {(c["caller"], c["callee"]) for c in utils_calls}
        self.assertIn(
            ("pkg.utils.Greeter.greet", "pkg.utils.helper"), resolutions
        )

    def test_no_crashes_no_parse_errors(self):
        parse_errors = [u for u in self.report["unresolved"] if u["pattern"] == "parse_error"]
        self.assertEqual(parse_errors, [])


class TestSyntaxErrorHandling(unittest.TestCase):
    """Engine must not crash on files with syntax errors - logs and continues."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="module2_syntax_test_")
        write_files(cls.tmpdir, {
            "good.py": "def ok():\n    pass\n",
            "broken.py": "def broken(:\n    this is not valid python\n",
        })
        cls.report = build_repository_graph(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def test_governance_still_approved(self):
        # files exist and were scanned, even if one failed to parse
        self.assertEqual(self.report["governance_gate"], "APPROVED")

    def test_good_file_still_processed(self):
        self.assertIn("good", self.report["function_graph"])
        names = {f["name"] for f in self.report["function_graph"]["good"]}
        self.assertIn("ok", names)

    def test_broken_file_logged_as_parse_error(self):
        parse_errors = [u for u in self.report["unresolved"]
                         if u["pattern"] == "parse_error" and u["module"] == "broken"]
        self.assertEqual(len(parse_errors), 1)


class TestEmptyRepo(unittest.TestCase):
    """Engine must handle a repo with no Python files (governance BLOCKED)."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp(prefix="module2_empty_test_")
        write_files(cls.tmpdir, {"README.md": "# nothing here\n"})
        cls.report = build_repository_graph(cls.tmpdir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def test_governance_blocked_when_no_python_files(self):
        self.assertEqual(self.report["governance_gate"], "BLOCKED")

    def test_zero_files_scanned(self):
        self.assertEqual(self.report["files_scanned"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
