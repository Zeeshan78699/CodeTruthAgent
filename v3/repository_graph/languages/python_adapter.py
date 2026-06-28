"""
python_adapter.py
The only fully IMPLEMENTED language adapter. Wraps the existing,
frozen Stage A / Stage B engine (function_graph.py, class_graph.py,
module_graph.py, import_graph.py, dependency_graph.py, call_graph.py,
topology.py) without modifying any of it.

Module 3 Python-core gap fixes (D-008 package-root mismatch,
attribute_call return-type tracking) are applied here as a wrapper
layer - see package_root.py and type_inference.py. The frozen
build_repository_graph() call below is unchanged; its output is
corrected/enhanced afterward, never replaced wholesale.
"""

from .base_adapter import LanguageAdapter
from .. import graph_engine
from .. import package_root
from .. import subtree_naming
from .. import type_inference
from ..deep_resolution.resolution_pipeline import run_resolution_pipeline
from ..dependency_graph import load_declared_dependencies

# graph_engine's own Stage A unresolved entries (parse errors) are kept
# as-is; only Stage B (call-resolution) unresolved entries are replaced
# by the type-aware re-run.
_STAGE_A_UNRESOLVED_PATTERNS = {"parse_error"}


class PythonAdapter(LanguageAdapter):
    language_name = "python"
    file_extensions = {".py"}

    def is_implemented(self) -> bool:
        return True

    def scan(self, repo_root: str, file_paths: list) -> dict:
        # D-008: detect the true package root. Falls back to repo_root
        # unchanged whenever detection isn't confidently resolvable -
        # the frozen engine then runs EXACTLY as before this fix.
        # FIX: now uses the combined function so the src-layout check
        # below can reuse the same root_counts instead of re-parsing
        # every file in the repo a second time.
        effective_root, root_counts = package_root.detect_package_root_and_counts(repo_root)

        report = graph_engine.build_repository_graph(effective_root)

        if effective_root != repo_root:
            # requirements.txt lives at the ORIGINAL repo root, not the
            # corrected package root - re-read it from there.
            report["declared_dependencies"] = load_declared_dependencies(repo_root)
            report["package_root_corrected"] = True
            report["requested_root"] = repo_root
        else:
            report["package_root_corrected"] = False

        # src/-layout fix: a second, distinct shape from D-008's
        # root-shift above. Only attempted when D-008 didn't already
        # correct things, since the two mechanisms are mutually
        # exclusive by design - never both at once. Detection is
        # checked now (against the TRUE repo_root), the actual rename
        # is applied at the very end, after both graph_engine and
        # type_inference have produced their final output, so it
        # touches everything consistently in one pass.
        src_prefix = None
        if effective_root == repo_root:
            src_prefix = subtree_naming.detect_src_prefix_to_strip(repo_root, root_counts=root_counts)

        # attribute_call: re-run Stage B with the type-aware resolver.
        # This can only ADD newly-resolved edges versus the frozen run
        # above - see type_inference.py docstring.
        call_graph, call_unresolved, return_type_table = (
            type_inference.build_repository_call_graph_enhanced(effective_root, root_counts=root_counts)
        )
        kept_unresolved = [
            u for u in report["unresolved"]
            if u.get("pattern") in _STAGE_A_UNRESOLVED_PATTERNS
        ]
        report["call_graph"] = call_graph
        report["unresolved"] = kept_unresolved + call_unresolved
        report["return_type_table_size"] = len(return_type_table)
        # FIX: the experimental unresolved_pipeline tools need the actual
        # table, not just its count. Keys are full function ids
        # ("module.func"), values are type_info tuples like
        # ("class", "module", "ClassName") - exploratory tools should
        # consume the class name (index 2 for "class" entries) directly.
        report["return_type_table"] = return_type_table

        if src_prefix:
            report = subtree_naming.rename_report_module_names(report, prefix=src_prefix)
            report["src_layout_prefix_stripped"] = src_prefix
        else:
            report["src_layout_prefix_stripped"] = None

        # Deep resolution: a second-pass attempt at the entries Stage B
        # left unresolved (builtin/constructor/factory/property/
        # inheritance/reflection - see v3/repository_graph/deep_resolution/).
        # Purely additive - never removes or changes anything in
        # report["unresolved"] itself, only adds this new key alongside
        # it. rename_fn mirrors whatever rename was just applied above
        # (identity if none), so this module's own independent file
        # scan (assignment_chain_builder.py) stays consistent with the
        # rest of the report rather than silently using stale names.
        rename_fn = (lambda name: subtree_naming._strip(name, src_prefix + ".")) if src_prefix else None
        report["deep_resolution"] = run_resolution_pipeline(
            unresolved_entries=report["unresolved"],
            return_type_table=report["return_type_table"],
            class_graph=report["class_graph"],
            # FIX: was repo_root - for D-008-corrected repos (ccxt,
            # pydicom, rclpy), that's the ORIGINAL, unshifted root,
            # while the rest of the report (and graph_engine itself)
            # uses effective_root. Confirmed via direct test: scanning
            # from repo_root produced keys like "python.ccxt.toobit"
            # while the real report uses "ccxt.toobit" - a silent
            # mismatch that broke every constructor_class/
            # factory_function lookup for D-008 repos specifically.
            # effective_root is correct for BOTH cases: when D-008
            # fires it's the shifted root (matching graph_engine); when
            # it doesn't, it's just repo_root unchanged (matching the
            # src-layout case, where rename_fn handles the rest).
            repo_path=effective_root,
            function_graph=report["function_graph"],
            module_graph=report["module_graph"],
            rename_fn=rename_fn,
        )

        return report