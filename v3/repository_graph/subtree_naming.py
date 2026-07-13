"""
subtree_naming.py

A second, distinct shape of package-root problem from D-008's
root-shift mechanism (package_root.py): the PyPA "src layout"
convention (e.g. src/flask/__init__.py), where the real package sits
under a literal src/ directory, but tests/ and examples/ are real,
separate Python code that should keep normal repo-root-relative
naming and full scan coverage.

D-008's existing fix (detect_package_root) shifts the WHOLE effective
root, which works correctly for ccxt-shaped repos (the nested
directory genuinely IS the entire relevant codebase) but is wrong here
- shifting root to repo_root/src silently drops every file outside it
from the scan entirely (confirmed on real Flask data: files_scanned
83 -> 24, a ~73% coverage loss, not a fix).

This fix is structurally different on purpose: scan the WHOLE repo
from the TRUE, unmodified repo_root (so coverage is never affected),
then apply a pure renaming pass over the already-collected report -
stripping the literal "src." prefix only from names that actually
have it, leaving every other module name (tests.*, examples.*, etc.)
completely untouched.

Truth Boundary: detection only confirms the specific, well-known src/
layout convention by checking the real filesystem (src/<name>/
__init__.py must exist) - never guesses, never lowers any existing
threshold. If the convention isn't confirmed, returns None and nothing
is renamed.
"""

import os
from typing import Any, Dict, Optional

from .package_root import _collect_absolute_import_roots
from .graph_engine import find_python_files


def detect_src_prefix_to_strip(repo_root: str, root_counts: dict = None) -> Optional[str]:
    """
    Returns "src" if repo_root/src/<top_import_root>/__init__.py
    exists, confirming the convention is genuinely in use - else None.
    top_import_root is the single most-imported absolute import root
    repo-wide, regardless of whether it crosses any dominance
    threshold (that threshold is the wrong test for this shape, per
    real Flask data: "flask" was only 24.55% of all absolute imports,
    diluted by its own large test/example suite, yet the layout is
    genuinely in use).

    root_counts can be passed in directly when the caller already
    computed it (e.g. detect_package_root just did) - avoids
    re-parsing every file in the repo a second time for the same
    information.
    """
    if root_counts is None:
        py_files = find_python_files(repo_root)
        if not py_files:
            return None
        root_counts = _collect_absolute_import_roots(py_files)

    if not root_counts:
        return None

    top_name, _ = max(root_counts.items(), key=lambda kv: kv[1])

    src_dir = os.path.join(repo_root, "src")
    candidate_init = os.path.join(src_dir, top_name, "__init__.py")
    if os.path.isfile(candidate_init):
        return "src"
    return None


def _strip(name: Optional[str], prefix_dot: str) -> Optional[str]:
    if name is None:
        return None
    if name.startswith(prefix_dot):
        return name[len(prefix_dot):]
    return name


def rename_report_module_names(report: Dict[str, Any], prefix: str = "src") -> Dict[str, Any]:
    """
    Renames every module-qualified name in `report` that starts with
    "<prefix>." by stripping that prefix - applied in place, also
    returned for convenience. Names that don't start with the prefix
    (tests.*, examples.*, docs.*, etc.) are returned completely
    unchanged. Safe to call even when nothing in the report actually
    has the prefix - it's then a no-op everywhere.
    """
    prefix_dot = prefix + "."

    def rename_keyed_dict(d):
        return {_strip(k, prefix_dot): v for k, v in d.items()}

    if "function_graph" in report:
        new_fg = {}
        for mod_name, funcs in report["function_graph"].items():
            for f in funcs:
                if "id" in f:
                    f["id"] = _strip(f["id"], prefix_dot)
            new_fg[_strip(mod_name, prefix_dot)] = funcs
        report["function_graph"] = new_fg

    if "class_graph" in report:
        new_cg = {}
        for mod_name, classes in report["class_graph"].items():
            for c in classes:
                if "id" in c:
                    c["id"] = _strip(c["id"], prefix_dot)
            new_cg[_strip(mod_name, prefix_dot)] = classes
        report["class_graph"] = new_cg

    if "module_graph" in report:
        new_mg = {}
        for mod_name, info in report["module_graph"].items():
            if isinstance(info, dict) and info.get("parent"):
                info["parent"] = _strip(info["parent"], prefix_dot)
            new_mg[_strip(mod_name, prefix_dot)] = info
        report["module_graph"] = new_mg

    if "import_graph" in report:
        new_ig = {}
        for mod_name, entries in report["import_graph"].items():
            for entry in entries:
                if isinstance(entry, dict):
                    if "from_module" in entry:
                        entry["from_module"] = _strip(entry["from_module"], prefix_dot)
                    if "imports" in entry:
                        entry["imports"] = _strip(entry["imports"], prefix_dot)
                    if "module_part" in entry:
                        entry["module_part"] = _strip(entry["module_part"], prefix_dot)
                elif isinstance(entry, str):
                    entries[entries.index(entry)] = _strip(entry, prefix_dot)
            new_ig[_strip(mod_name, prefix_dot)] = entries
        report["import_graph"] = new_ig

    if "dependency_graph" in report:
        for ext_pkg, info in report["dependency_graph"].items():
            if isinstance(info, dict) and "used_by" in info:
                info["used_by"] = [_strip(m, prefix_dot) for m in info["used_by"]]

    if "call_graph" in report:
        new_call = {}
        for mod_name, edges in report["call_graph"].items():
            for e in edges:
                if "caller" in e:
                    e["caller"] = _strip(e["caller"], prefix_dot)
                if "callee" in e and isinstance(e["callee"], str):
                    e["callee"] = _strip(e["callee"], prefix_dot)
            new_call[_strip(mod_name, prefix_dot)] = edges
        report["call_graph"] = new_call

    if "unresolved" in report:
        for entry in report["unresolved"]:
            if "module" in entry:
                entry["module"] = _strip(entry["module"], prefix_dot)

    if "cyclic_clusters" in report:
        report["cyclic_clusters"] = [
            [_strip(m, prefix_dot) for m in cluster]
            for cluster in report["cyclic_clusters"]
        ]

    if "return_type_table" in report:
        new_rt = {}
        for full_id, type_info in report["return_type_table"].items():
            new_id = _strip(full_id, prefix_dot)
            if type_info and len(type_info) == 3:
                kind, mod, name = type_info
                type_info = (kind, _strip(mod, prefix_dot), name)
            new_rt[new_id] = type_info
        report["return_type_table"] = new_rt

    return report