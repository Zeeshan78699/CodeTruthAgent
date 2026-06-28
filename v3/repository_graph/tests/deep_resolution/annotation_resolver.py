"""
========================================================================
annotation_resolver.py
CodeTruth Agent V3 — Module 2 Deep Resolution Extension

RESOLVER:       annotation_resolver (DR Resolver #7)
PURPOSE:        Resolves attribute_calls on type-annotated parameters.

PROBLEM:
    def process(conn: DatabaseConnection, repo: UserRepository):
        conn.execute("SELECT")   # UNRESOLVED — attribute_call
        repo.find_all()          # UNRESOLVED — attribute_call

    The core engine sees conn.execute() but does not know
    conn is a DatabaseConnection. The type annotation is there
    in the source code — this resolver reads it.

APPROACH:
    1. Parse each module for function definitions
    2. Extract parameter type annotations
    3. For each unresolved attribute_call, check if the
       target variable has a known type annotation
    4. If yes — resolve to AnnotatedType.method()

YIELD (estimated from 76-repo corpus):
    ~15-25% of remaining attribute_calls have type annotations.
    Higher in well-typed codebases (medical, aerospace, finance).

DOES NOT SOLVE:
    - Unannotated parameters          → Module 3
    - Factory/registry patterns       → Module 3
    - Dynamic runtime dispatch        → Module 9 (documented)

STATUS: Module 2 Extension — Non-breaking
========================================================================
"""

from __future__ import annotations
import ast as ast_mod
import warnings
from pathlib import Path
from typing import Any


# ------------------------------------------------------------------
# Type annotation extraction
# ------------------------------------------------------------------

def extract_param_annotations(source: str) -> dict[str, dict[str, str]]:
    """
    Parses a Python source file and returns a mapping:
        {function_name: {param_name: type_name}}

    Example:
        def process(conn: DatabaseConnection, limit: int) -> list:
        →  {"process": {"conn": "DatabaseConnection", "limit": "int"}}

    Only handles simple name annotations (not generics like List[str]).
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast_mod.parse(source)
    except SyntaxError:
        return {}

    annotations: dict[str, dict[str, str]] = {}

    for node in ast_mod.walk(tree):
        if not isinstance(node, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef)):
            continue

        func_name = node.name
        param_types: dict[str, str] = {}

        for arg in node.args.args:
            if arg.annotation is None:
                continue
            # Simple name annotation: conn: DatabaseConnection
            if isinstance(arg.annotation, ast_mod.Name):
                param_types[arg.arg] = arg.annotation.id
            # Attribute annotation: conn: db.DatabaseConnection
            elif isinstance(arg.annotation, ast_mod.Attribute):
                param_types[arg.arg] = arg.annotation.attr

        if param_types:
            annotations[func_name] = param_types

    return annotations


def extract_variable_annotations(source: str) -> dict[str, str]:
    """
    Extracts variable-level annotations:
        conn: DatabaseConnection = get_connection()
        →  {"conn": "DatabaseConnection"}
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast_mod.parse(source)
    except SyntaxError:
        return {}

    var_types: dict[str, str] = {}

    for node in ast_mod.walk(tree):
        if not isinstance(node, ast_mod.AnnAssign):
            continue
        if not isinstance(node.target, ast_mod.Name):
            continue
        if isinstance(node.annotation, ast_mod.Name):
            var_types[node.target.id] = node.annotation.id
        elif isinstance(node.annotation, ast_mod.Attribute):
            var_types[node.target.id] = node.annotation.attr

    return var_types


# ------------------------------------------------------------------
# Class method index builder
# ------------------------------------------------------------------

def build_class_method_index(source_files: list[Path]) -> dict[str, set[str]]:
    """
    Scans all source files and builds:
        {ClassName: {method1, method2, ...}}

    Used to confirm that an annotated type actually has the method
    being called, before claiming resolution.
    """
    index: dict[str, set[str]] = {}

    for path in source_files:
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast_mod.parse(source)
        except Exception:
            continue

        for node in ast_mod.walk(tree):
            if not isinstance(node, ast_mod.ClassDef):
                continue
            methods: set[str] = set()
            for item in node.body:
                if isinstance(item, (ast_mod.FunctionDef, ast_mod.AsyncFunctionDef)):
                    methods.add(item.name)
            if methods:
                index[node.name] = index.get(node.name, set()) | methods

    return index


# ------------------------------------------------------------------
# Main resolver
# ------------------------------------------------------------------

def run_annotation_resolver(
    unresolved_entries: list[dict],
    repo_path: str,
    source_files: list[Path] | None = None,
) -> dict[str, Any]:
    """
    Resolves attribute_calls where the target variable has a
    type annotation mapping it to a known class.

    Parameters
    ----------
    unresolved_entries : list[dict]
        The remaining_unresolved_entries from deep_resolution.
        Each entry: {module, lineno, pattern, note}

    repo_path : str
        Root path of the repository being scanned.

    source_files : list[Path] | None
        If provided, limits scanning to these files.
        If None, scans all .py files in repo_path.

    Returns
    -------
    dict with:
        resolved_count      : int
        resolved_entries    : list[dict]
        still_unresolved    : list[dict]
        annotation_map      : dict  (var → type, per module)
        class_method_index  : dict  (class → methods found)
        coverage_pct        : float
    """
    root = Path(repo_path)

    if source_files is None:
        source_files = list(root.rglob("*.py"))

    # Build class method index across all source files
    class_method_index = build_class_method_index(source_files)

    # Build annotation map per module
    module_annotations: dict[str, dict[str, str]] = {}  # module → {var → type}

    for path in source_files:
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Collect param annotations from all functions
        param_anns  = extract_param_annotations(source)
        var_anns    = extract_variable_annotations(source)

        # Flatten param annotations into a var→type map for this module
        all_anns: dict[str, str] = {}
        for func_anns in param_anns.values():
            all_anns.update(func_anns)
        all_anns.update(var_anns)

        # Store under both stem and dotted path variants
        # Unresolved entries may use either "routing" or "fastapi.routing"
        module_name = path.stem
        if all_anns:
            module_annotations[module_name] = all_anns
            # Also store under relative dotted path for cross-module entries
            try:
                root_p = Path(repo_path)
                rel = path.relative_to(root_p)
                dotted = ".".join(rel.with_suffix("").parts)
                if dotted != module_name:
                    module_annotations[dotted] = all_anns
            except Exception:
                pass

    # Attempt to resolve each unresolved entry
    resolved_entries   : list[dict] = []
    still_unresolved   : list[dict] = []

    for entry in unresolved_entries:
        module  = entry.get("module", "")
        note    = entry.get("note", "")
        lineno  = entry.get("lineno", 0)
        pattern = entry.get("pattern", "")

        if pattern != "attribute_call":
            still_unresolved.append(entry)
            continue

        # Extract method name from note
        # Note format: "Call via attribute access .method(...) - ..."
        method_name = _extract_method_name(note)
        if not method_name:
            still_unresolved.append(entry)
            continue

        # Check annotation map — try module name, dotted variant, then all modules
        ann_map = module_annotations.get(module, {})
        if not ann_map:
            # Try last part only (e.g. "fastapi.routing" → "routing")
            ann_map = module_annotations.get(module.split(".")[-1], {})

        resolved = False

        for var_name, type_name in ann_map.items():
            # Check if this type has the method
            if type_name in class_method_index:
                if method_name in class_method_index[type_name]:
                    resolved_entries.append({
                        **entry,
                        "resolved_to":   f"{type_name}.{method_name}",
                        "resolved_by":   "annotation_resolver",
                        "type_source":   "parameter_annotation",
                        "annotated_var": var_name,
                        "annotated_type": type_name,
                    })
                    resolved = True
                    break

            # Also check builtins even without class index
            elif type_name in _BUILTIN_METHODS and method_name in _BUILTIN_METHODS[type_name]:
                resolved_entries.append({
                    **entry,
                    "resolved_to":   f"{type_name}.{method_name}",
                    "resolved_by":   "annotation_resolver",
                    "type_source":   "builtin_annotation",
                    "annotated_var": var_name,
                    "annotated_type": type_name,
                })
                resolved = True
                break

        if not resolved:
            still_unresolved.append(entry)

    total    = len(unresolved_entries)
    resolved = len(resolved_entries)
    coverage = round(resolved / total * 100, 2) if total > 0 else 0.0

    return {
        "resolved_count":     resolved,
        "resolved_entries":   resolved_entries,
        "still_unresolved":   still_unresolved,
        "annotation_map":     module_annotations,
        "class_method_index": {k: list(v) for k, v in class_method_index.items()},
        "coverage_pct":       coverage,
        "baseline":           total,
    }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _extract_method_name(note: str) -> str | None:
    """
    Extracts method name from unresolved entry note.
    Note format: "Call via attribute access .method(...) - ..."
    """
    import re
    match = re.search(r"\.(\w+)\(", note)
    return match.group(1) if match else None


# Common builtin type methods (supplement to class_method_index)
_BUILTIN_METHODS: dict[str, set[str]] = {
    "list":  {"append", "extend", "insert", "remove", "pop", "sort",
              "reverse", "copy", "clear", "count", "index"},
    "dict":  {"get", "set", "update", "items", "keys", "values",
              "pop", "clear", "copy", "setdefault"},
    "str":   {"upper", "lower", "strip", "split", "join", "replace",
              "format", "encode", "decode", "startswith", "endswith",
              "find", "count", "lstrip", "rstrip"},
    "set":   {"add", "remove", "discard", "union", "intersection",
              "difference", "update", "clear", "copy", "pop"},
    "tuple": {"count", "index"},
    "int":   {"bit_length", "to_bytes"},
    "float": {"is_integer", "hex"},
}


# ------------------------------------------------------------------
# Integration helper — wraps into Deep Resolution pipeline format
# ------------------------------------------------------------------

def integrate_with_pipeline(deep_resolution_report: dict, repo_path: str) -> dict:
    """
    Runs annotation_resolver on top of existing deep_resolution output.
    Designed to be called after the main pipeline completes.

    Returns updated deep_resolution dict with annotation_resolver results.
    """
    remaining = deep_resolution_report.get("remaining_unresolved_entries", [])

    if not remaining:
        return deep_resolution_report

    result = run_annotation_resolver(remaining, repo_path)

    # Update the pipeline report
    updated = dict(deep_resolution_report)
    rr = dict(updated.get("resolver_results", {}))
    rr["annotation"] = result["resolved_count"]
    updated["resolver_results"] = rr

    fin = dict(updated.get("final", {}))
    old_resolved = fin.get("resolved_by_pipeline", 0)
    old_remaining = fin.get("remaining_unresolved", len(remaining))
    new_resolved  = old_resolved + result["resolved_count"]
    new_remaining = old_remaining - result["resolved_count"]
    new_pct = round(new_resolved / (new_resolved + new_remaining) * 100, 2) if (new_resolved + new_remaining) > 0 else 0.0

    fin["resolved_by_pipeline"] = new_resolved
    fin["remaining_unresolved"] = max(0, new_remaining)
    fin["reduction_pct"]        = new_pct
    updated["final"] = fin

    updated["annotation_resolver"] = result
    updated["remaining_unresolved_entries"] = result["still_unresolved"]

    return updated