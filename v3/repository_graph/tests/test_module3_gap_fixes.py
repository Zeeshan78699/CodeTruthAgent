"""
test_module3_gap_fixes.py
Permanent regression tests for package_root.py and type_inference.py
(D-008 and attribute_call fixes) plus their wiring into python_adapter.py.

Run from project root:
    python -m pytest v3/repository_graph/tests/test_module3_gap_fixes.py -v
"""

import sys
import os
import ast
import tempfile
import shutil
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.graph_engine import build_repository_graph
from v3.repository_graph.package_root import detect_package_root
from v3.repository_graph.type_inference import (
    build_return_type_table,
    build_call_graph_with_type_inference,
    build_repository_call_graph_enhanced,
)
from v3.repository_graph.call_graph import build_call_graph
from v3.repository_graph.languages.python_adapter import PythonAdapter


def write_files(root, files: dict):
    for relpath, content in files.items():
        full = os.path.join(root, relpath)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)


def parse_all(root, py_files_rel):
    """Helper: build module_trees/function_graph/class_graph/import_alias_maps
    for a small fixture, mirroring graph_engine's own Stage A, for tests that
    need to call build_call_graph_with_type_inference directly."""
    from v3.repository_graph.module_graph import build_module_graph, module_name_from_path
    from v3.repository_graph.function_graph import build_function_graph_for_module
    from v3.repository_graph.class_graph import build_class_graph_for_module
    from v3.repository_graph.import_graph import collect_raw_imports
    from v3.repository_graph.call_graph import build_import_alias_map

    py_files = [os.path.join(root, p) for p in py_files_rel]
    module_trees, function_graph, class_graph, raw_imports = {}, {}, {}, {}
    for fp in py_files:
        mod = module_name_from_path(root, fp)
        with open(fp) as f:
            tree = ast.parse(f.read())
        module_trees[mod] = tree
        function_graph[mod] = build_function_graph_for_module(mod, tree)
        class_graph[mod] = build_class_graph_for_module(mod, tree)
        raw_imports[mod] = collect_raw_imports(mod, tree)

    module_graph = build_module_graph(root, py_files)
    project_roots = {m.split(".")[0] for m in module_trees}
    alias_maps = {
        mod: build_import_alias_map(mod, raw, is_package=module_graph.get(mod, {}).get("is_package", False))
        for mod, raw in raw_imports.items()
    }
    return module_trees, function_graph, class_graph, alias_maps, project_roots


# --------------------------------------------------------------------- #
# D-008: package_root.py
# --------------------------------------------------------------------- #

class TestPackageRootDetection(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_no_change_when_package_already_at_root(self):
        """Common case (67/69 real repos): package sits directly under
        repo_root. Must return repo_root UNCHANGED."""
        write_files(self.tmpdir, {
            "pkg/__init__.py": "",
            "pkg/mod.py": "import pkg.mod\n",
        })
        result = detect_package_root(self.tmpdir)
        self.assertEqual(os.path.normpath(result), os.path.normpath(self.tmpdir))

    def test_detects_nested_package_root(self):
        """ccxt-style layout: repo_root/python/ccxt/ with absolute
        imports rooted at 'ccxt', not 'python'."""
        write_files(self.tmpdir, {
            "setup.py": "print('noise')\n",
            "python/ccxt/__init__.py": "",
            "python/ccxt/base/__init__.py": "",
            "python/ccxt/base/exchange.py": "class Exchange:\n    pass\n",
            "python/ccxt/binance.py": "from ccxt.base.exchange import Exchange\n",
        })
        result = detect_package_root(self.tmpdir)
        expected = os.path.join(self.tmpdir, "python")
        self.assertEqual(os.path.normpath(result), os.path.normpath(expected))

    def test_falls_back_when_no_dominant_import_root(self):
        """No single absolute-import root dominates (mixed external
        libs, no internal self-imports) - must NOT guess."""
        write_files(self.tmpdir, {
            "src/lib/a.py": "import os\nimport sys\nimport json\n",
            "src/lib/b.py": "import re\nimport math\nimport itertools\n",
        })
        result = detect_package_root(self.tmpdir)
        self.assertEqual(os.path.normpath(result), os.path.normpath(self.tmpdir))

    def test_falls_back_when_candidate_directory_does_not_exist(self):
        """Dominant import root name has no corresponding real package
        directory anywhere under repo_root - must NOT guess."""
        write_files(self.tmpdir, {
            "app/main.py": "import numpy\nimport numpy.linalg\nimport numpy.fft\n",
        })
        result = detect_package_root(self.tmpdir)
        self.assertEqual(os.path.normpath(result), os.path.normpath(self.tmpdir))

    def test_empty_repo_returns_repo_root_unchanged(self):
        result = detect_package_root(self.tmpdir)
        self.assertEqual(os.path.normpath(result), os.path.normpath(self.tmpdir))

    def test_relative_imports_are_ignored_for_detection(self):
        """A package using only relative imports internally shouldn't
        cause a false-positive root override."""
        write_files(self.tmpdir, {
            "pkg/__init__.py": "",
            "pkg/a.py": "from . import b\n",
            "pkg/b.py": "from .a import something\n",
        })
        result = detect_package_root(self.tmpdir)
        self.assertEqual(os.path.normpath(result), os.path.normpath(self.tmpdir))


# --------------------------------------------------------------------- #
# attribute_call: type_inference.py
# --------------------------------------------------------------------- #

class TestReturnTypeTable(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_simple_constructor_return_is_classified(self):
        write_files(self.tmpdir, {"main.py": (
            "class Parser:\n    def process(self):\n        return 1\n\n"
            "def make_parser():\n    return Parser()\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        from v3.repository_graph.call_graph import build_global_symbol_index
        _, class_methods_index, _ = build_global_symbol_index(fg, cg)
        table = build_return_type_table(trees, fg, class_methods_index, aliases, class_methods_index)
        self.assertEqual(table.get("main.make_parser"), ("class", "main", "Parser"))

    def test_ambiguous_return_excluded_from_table(self):
        """Two different return types across branches -> must NOT
        appear in the table at all (honest unknown, not a guess)."""
        write_files(self.tmpdir, {"main.py": (
            "class Parser:\n    pass\n\n"
            "def maybe(flag):\n"
            "    if flag:\n        return Parser()\n"
            "    return None\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        from v3.repository_graph.call_graph import build_global_symbol_index
        _, class_methods_index, _ = build_global_symbol_index(fg, cg)
        table = build_return_type_table(trees, fg, class_methods_index, aliases, class_methods_index)
        self.assertNotIn("main.maybe", table)

    def test_no_return_statement_excluded_from_table(self):
        write_files(self.tmpdir, {"main.py": "def noop():\n    x = 1\n"})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        from v3.repository_graph.call_graph import build_global_symbol_index
        _, class_methods_index, _ = build_global_symbol_index(fg, cg)
        table = build_return_type_table(trees, fg, class_methods_index, aliases, class_methods_index)
        self.assertNotIn("main.noop", table)

    def test_recursive_function_does_not_crash_or_hang(self):
        write_files(self.tmpdir, {"main.py": (
            "def f(n):\n    return f(n - 1)\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        from v3.repository_graph.call_graph import build_global_symbol_index
        _, class_methods_index, _ = build_global_symbol_index(fg, cg)
        table = build_return_type_table(trees, fg, class_methods_index, aliases, class_methods_index)
        self.assertNotIn("main.f", table)  # honest unknown, no crash

    def test_nested_function_return_not_attributed_to_parent(self):
        write_files(self.tmpdir, {"main.py": (
            "class Parser:\n    pass\n\n"
            "def outer():\n"
            "    def inner():\n        return Parser()\n"
            "    return 'plain'\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        from v3.repository_graph.call_graph import build_global_symbol_index
        _, class_methods_index, _ = build_global_symbol_index(fg, cg)
        table = build_return_type_table(trees, fg, class_methods_index, aliases, class_methods_index)
        self.assertEqual(table.get("main.outer"), ("builtin", "str"))


    def test_zero_method_class_constructor_stays_unresolved_pre_existing_limitation(self):
        """DISCOVERED during thorough testing, NOT introduced by this fix:
        build_global_symbol_index (frozen call_graph.py) only adds a class
        to class_methods_index if it has at least one method - a class with
        zero methods is invisible to ALL constructor-call resolution,
        including the original frozen Gap 2 logic, independent of anything
        in type_inference.py. Documented here as a known pre-existing gap,
        not something this fix is responsible for."""
        write_files(self.tmpdir, {"main.py": (
            "class Empty:\n    pass\n\n"
            "def make_one():\n    return Empty()\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        from v3.repository_graph.call_graph import build_global_symbol_index
        _, class_methods_index, _ = build_global_symbol_index(fg, cg)
        # Confirms the root cause: Empty never appears as a key at all.
        self.assertNotIn("Empty", class_methods_index.get("main", {}))
        table = build_return_type_table(trees, fg, class_methods_index, aliases, class_methods_index)
        self.assertNotIn("main.make_one", table)  # correctly excluded, not a new bug


class TestTypeAwareCallResolver(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_resolves_call_through_known_return_type(self):
        write_files(self.tmpdir, {"main.py": (
            "class Parser:\n"
            "    def process(self):\n        return 'done'\n\n"
            "def make_parser():\n    return Parser()\n\n"
            "def run():\n"
            "    result = make_parser()\n"
            "    return result.process()\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        call_graph, unresolved, table = build_call_graph_with_type_inference(
            trees, fg, cg, aliases, project_module_roots=roots
        )
        resolutions = {(e["caller"], e["callee"]) for e in call_graph["main"]}
        self.assertIn(("main.run", "main.Parser.process"), resolutions)
        self.assertFalse(any(u["pattern"] == "attribute_call" for u in unresolved))

    def test_ambiguous_case_correctly_stays_unresolved(self):
        write_files(self.tmpdir, {"main.py": (
            "class Parser:\n"
            "    def process(self):\n        return 'done'\n\n"
            "def maybe(flag):\n"
            "    if flag:\n        return Parser()\n"
            "    return None\n\n"
            "def run(flag):\n"
            "    x = maybe(flag)\n"
            "    return x.process()\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        call_graph, unresolved, table = build_call_graph_with_type_inference(
            trees, fg, cg, aliases, project_module_roots=roots
        )
        self.assertTrue(any(u["pattern"] == "attribute_call" for u in unresolved))

    def test_identical_to_frozen_resolver_when_no_inferable_types(self):
        """Strongest regression guarantee: on a fixture with NO
        constructor-returning functions at all, the type-aware resolver
        must produce byte-for-byte identical output to the frozen
        build_call_graph - proving super() is genuinely called first."""
        write_files(self.tmpdir, {"main.py": (
            "class Greeter:\n"
            "    def __init__(self):\n        self.name = 'x'\n"
            "    def greet(self):\n        return self.name\n\n"
            "def use():\n"
            "    g = Greeter()\n"
            "    return g.greet()\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        frozen_call_graph, frozen_unresolved = build_call_graph(
            trees, fg, cg, aliases, project_module_roots=roots
        )
        new_call_graph, new_unresolved, _ = build_call_graph_with_type_inference(
            trees, fg, cg, aliases, project_module_roots=roots
        )
        self.assertEqual(frozen_call_graph, new_call_graph)
        self.assertEqual(frozen_unresolved, new_unresolved)

    def test_reassignment_uses_latest_type_same_as_frozen_gap2(self):
        """Confirms the new fallback doesn't interfere with existing
        Gap 2 reassignment-overwrite behavior (inherited unchanged)."""
        write_files(self.tmpdir, {"main.py": (
            "class Parser:\n"
            "    def process(self):\n        return 1\n\n"
            "def run():\n"
            "    x = []\n"
            "    x = Parser()\n"
            "    return x.process()\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        call_graph, unresolved, table = build_call_graph_with_type_inference(
            trees, fg, cg, aliases, project_module_roots=roots
        )
        resolutions = {(e["caller"], e["callee"]) for e in call_graph["main"]}
        self.assertIn(("main.run", "main.Parser.process"), resolutions)

    def test_zero_method_class_now_resolves_through_full_pipeline(self):
        """The augmentation fix: same zero-method class as the test in
        TestReturnTypeTable above, but run through
        build_call_graph_with_type_inference (the actual pipeline)
        instead of the raw frozen index builder. Must now resolve,
        proving the fix closes the gap end-to-end - this is the same
        shape of bug discovered in real ccxt data (exception classes
        like ArgumentsRequired silently mislabeled as external)."""
        write_files(self.tmpdir, {"main.py": (
            "class Empty:\n    pass\n\n"
            "def make_one():\n    return Empty()\n\n"
            "def use():\n    return make_one()\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        call_graph, unresolved, table = build_call_graph_with_type_inference(
            trees, fg, cg, aliases, project_module_roots=roots
        )
        callees = {e["callee"] for edges in call_graph.values() for e in edges}
        self.assertIn("main.Empty.<class>", callees)
        self.assertFalse(any(u["pattern"] in ("name_call_unresolved", "attribute_call")
                              for u in unresolved))

    def test_zero_method_class_as_inheritance_base_now_resolves(self):
        """A zero-method base class (e.g. a custom exception hierarchy,
        the exact ccxt shape) should now be walkable by D-004's
        inheritance chain, since it's present in the augmented index."""
        write_files(self.tmpdir, {"main.py": (
            "class BaseError(Exception):\n    pass\n\n"
            "class ArgumentsRequired(BaseError):\n    pass\n\n"
            "def use():\n    return ArgumentsRequired()\n"
        )})
        trees, fg, cg, aliases, roots = parse_all(self.tmpdir, ["main.py"])
        call_graph, unresolved, table = build_call_graph_with_type_inference(
            trees, fg, cg, aliases, project_module_roots=roots
        )
        callees = {e["callee"] for edges in call_graph.values() for e in edges}
        self.assertIn("main.ArgumentsRequired.<class>", callees)



# --------------------------------------------------------------------- #
# Integration: python_adapter.py wrapper
# --------------------------------------------------------------------- #

class TestPythonAdapterIntegration(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_no_correction_path_matches_frozen_engine_exactly_for_call_graph(self):
        """When D-008 doesn't trigger, the adapter's call_graph/unresolved
        must still equal the frozen engine's output on a fixture with no
        inferable return types (isolates the 'no fix needed' path)."""
        write_files(self.tmpdir, {"main.py": (
            "def add(a, b):\n    return a + b\n\n"
            "def use():\n    return add(1, 2)\n"
        )})
        frozen = build_repository_graph(self.tmpdir)
        after = PythonAdapter().scan(self.tmpdir, [])
        self.assertFalse(after["package_root_corrected"])
        self.assertEqual(frozen["call_graph"], after["call_graph"])
        self.assertEqual(frozen["unresolved"], after["unresolved"])

    def test_parse_error_entries_survive_the_swap(self):
        write_files(self.tmpdir, {
            "good.py": "def f():\n    return 1\n",
            "broken.py": "def f(:\n",
        })
        after = PythonAdapter().scan(self.tmpdir, [])
        self.assertTrue(any(u["pattern"] == "parse_error" for u in after["unresolved"]))

    def test_declared_dependencies_read_from_original_root_when_corrected(self):
        write_files(self.tmpdir, {
            "requirements.txt": "requests==2.31.0\n",
            "python/ccxt/__init__.py": "",
            "python/ccxt/base/__init__.py": "",
            "python/ccxt/base/exchange.py": "class Exchange:\n    pass\n",
            "python/ccxt/binance.py": "from ccxt.base.exchange import Exchange\nimport requests\n",
        })
        after = PythonAdapter().scan(self.tmpdir, [])
        self.assertTrue(after["package_root_corrected"])
        self.assertIn("requests", after["declared_dependencies"])

    def test_governance_gate_unaffected_by_either_fix(self):
        write_files(self.tmpdir, {"main.py": "def f():\n    return 1\n"})
        after = PythonAdapter().scan(self.tmpdir, [])
        self.assertEqual(after["governance_gate"], "APPROVED")


if __name__ == "__main__":
    unittest.main()
