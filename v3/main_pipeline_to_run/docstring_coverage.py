r"""
docstring_coverage.py
CodeTruth Agent V3 — D3-015 Documentation Auditor, Phase 1 / Capability 2a.

Measures docstring coverage: of the functions and classes actually defined in the
repository's Python source, how many carry a docstring.

WHY DIRECT AST, NOT M2's COUNT
------------------------------
run_platform()'s Module-2 summary emits only a function COUNT, not the function
nodes (it collapses `function_graph` to an integer before the report sees it). A
count cannot tell you which functions have docstrings. So coverage is measured by
parsing the source directly — an INDEPENDENT OBSERVED measurement, not a
derivation from an already-summarized number.

This keeps the merge with Module 2 honest: rather than reconstructing per-function
detail from a summary that threw it away, docstring coverage stands on its own
source evidence. Where the two disagree on the denominator, that disagreement is
itself reportable (see `denominator_note`) rather than hidden.

SCOPE (D3-015): Python only. For non-Python repos this returns
UNKNOWN:LANGUAGE_NOT_SUPPORTED — CodeTruth does not fabricate a coverage number
for a language whose source it did not parse for docstrings. Bridge languages get
an honest non-answer, exactly like `guesses` does.

AUTHORITY: this measures the code (do functions have docstrings). It reads no
documentation claims and assigns no domain value.
"""
from __future__ import annotations
import ast
import os


def _OBSERVED(value, path, excerpt):
    return {"tier": "OBSERVED", "value": value,
            "evidence": [{"path": path, "excerpt": excerpt, "sha256": "0" * 64}]}


def _DERIVED(value, derivation, inputs):
    return {"tier": "DERIVED", "value": value,
            "derivation": derivation, "inputs": inputs}


def _UNKNOWN(reason, notes=None):
    f = {"tier": "UNKNOWN", "reason": reason}
    if notes:
        f["notes"] = notes
    return f


PRUNE = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tox",
         "build", "dist", ".mypy_cache", ".pytest_cache", "_scratch", "_clones"}


def _iter_py_files(repo_root: str):
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in PRUNE and not d.startswith(".")]
        for fn in files:
            if fn.endswith(".py"):
                yield os.path.join(root, fn)


def _count_in_tree(tree: ast.AST):
    """Return (functions, functions_with_doc, classes, classes_with_doc) for one
    parsed module. Nested functions/methods are counted — a docstring is a
    docstring regardless of nesting."""
    fn = fn_doc = cls = cls_doc = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn += 1
            if ast.get_docstring(node) is not None:
                fn_doc += 1
        elif isinstance(node, ast.ClassDef):
            cls += 1
            if ast.get_docstring(node) is not None:
                cls_doc += 1
    return fn, fn_doc, cls, cls_doc


def measure(repo_root: str, language: str = "python",
            m2_function_count: int | None = None) -> dict:
    """Return docstring-coverage fields for the `documentation` section.

    language: the routed language from Module 2. Only 'python' is measured; any
              other language yields UNKNOWN:LANGUAGE_NOT_SUPPORTED.
    m2_function_count: optional. If provided, compared against the AST function
              count and any mismatch is surfaced as `denominator_note` — never
              silently reconciled.
    """
    if language != "python":
        return {
            "docstring_coverage": _UNKNOWN(
                "LANGUAGE_NOT_SUPPORTED",
                f"docstring coverage is measured from Python AST; the '{language}' "
                f"engine does not parse docstrings. Planned: per-language doc "
                f"extraction."),
        }

    total_fn = total_fn_doc = total_cls = total_cls_doc = 0
    parsed = skipped = 0
    for path in _iter_py_files(repo_root):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                tree = ast.parse(f.read())
        except (SyntaxError, ValueError, OSError):
            skipped += 1
            continue
        f_, fd, c_, cd = _count_in_tree(tree)
        total_fn += f_; total_fn_doc += fd
        total_cls += c_; total_cls_doc += cd
        parsed += 1

    if parsed == 0:
        return {"docstring_coverage": _UNKNOWN(
            "NO_EVIDENCE_FOUND", "no parseable Python files found")}

    denom = total_fn + total_cls
    documented = total_fn_doc + total_cls_doc
    pct = round(100.0 * documented / denom, 1) if denom else 0.0

    field = _DERIVED(
        {"documented": documented, "total": denom, "pct": pct,
         "functions": total_fn, "functions_documented": total_fn_doc,
         "classes": total_cls, "classes_documented": total_cls_doc},
        "docstring_coverage.ast_walk@3.0.0",
        ["(repository Python source)"])

    result = {"docstring_coverage": field,
              "_docstring_files_parsed": parsed,
              "_docstring_files_skipped": skipped}

    # Honest cross-check against Module 2's count — surfaced, never reconciled.
    if m2_function_count is not None and m2_function_count != total_fn:
        result["_denominator_note"] = (
            f"AST function count ({total_fn}) differs from Module 2's reported "
            f"function count ({m2_function_count}). Both are counting real things "
            f"by different definitions (M2 counts call-graph nodes; this counts AST "
            f"function defs including nested/local). The difference is reported, "
            f"not reconciled.")
    return result


if __name__ == "__main__":
    import sys, json
    print(json.dumps(measure(sys.argv[1]), indent=2))
