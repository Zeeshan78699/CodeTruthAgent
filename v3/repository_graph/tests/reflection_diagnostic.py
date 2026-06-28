"""
reflection_diagnostic.py
CodeTruth Agent V3 — Deep Resolution — Reflection Resolver Diagnostic

Finding: across the full 69-repo corpus, dr_reflection == 0 in every single
repo. This script identifies WHAT KINDS of dynamic-dispatch patterns exist
in real source that a reflection resolver would be expected to catch, so
you can compare that list against reflection_resolver.py's actual matching
logic and find the gap.

This does NOT call reflection_resolver.py directly (that requires importing
your private deep_resolution internals, which vary by your local wiring).
Instead it independently re-derives candidate patterns from raw AST, the
same way a reflection resolver should be looking for them, so you have a
ground-truth comparison set.

Patterns checked (the classic "reflection" call-resolution targets):
    1. getattr(obj, "name")(...)              — dynamic attribute call
    2. getattr(obj, name_var)(...)             — dynamic attribute, var name
    3. dispatch_dict[key](...)                 — dict-based dispatch table
    4. dispatch_dict.get(key)(...)              — dict.get dispatch table
    5. globals()[name](...)                     — globals() dispatch
    6. locals()[name](...)                      — locals() dispatch
    7. setattr(obj, "name", value)              — dynamic attribute set
       (not a call site itself, but often paired with pattern 1/2)

Usage:
    python v3\\repository_graph\\tests\\reflection_diagnostic.py <repo_path>
    python v3\\repository_graph\\tests\\reflection_diagnostic.py C:\\repos\\v3\\transformers
"""

import sys
import os
import ast
from pathlib import Path
from collections import defaultdict


def _find_and_add_project_root():
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / "v3" / "repository_graph").is_dir():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("Could not find the 'v3' package root.")


_find_and_add_project_root()


class ReflectionPatternFinder(ast.NodeVisitor):
    """Walks a module's AST looking for the classic dynamic-dispatch
    patterns that a reflection resolver should be matching."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.findings = defaultdict(list)

    def _loc(self, node):
        return f"{self.filepath}:{getattr(node, 'lineno', '?')}"

    def visit_Call(self, node):
        # Pattern 1 & 2: getattr(obj, "name")(...) or getattr(obj, var)(...)
        if isinstance(node.func, ast.Call) and isinstance(node.func.func, ast.Name) \
                and node.func.func.id == "getattr":
            args = node.func.args
            if len(args) >= 2:
                if isinstance(args[1], ast.Constant) and isinstance(args[1].value, str):
                    self.findings["getattr_literal_call"].append(
                        (self._loc(node), f"getattr(..., '{args[1].value}')(...)")
                    )
                else:
                    self.findings["getattr_dynamic_call"].append(
                        (self._loc(node), "getattr(..., <variable>)(...)")
                    )

        # Pattern 3: dispatch_dict[key](...)
        if isinstance(node.func, ast.Subscript):
            try:
                target_repr = ast.unparse(node.func.value)
            except Exception:
                target_repr = "<dict>"
            self.findings["dict_subscript_call"].append(
                (self._loc(node), f"{target_repr}[...](...)")
            )

        # Pattern 4: dispatch_dict.get(key)(...)
        if isinstance(node.func, ast.Call) and isinstance(node.func.func, ast.Attribute) \
                and node.func.func.attr == "get":
            try:
                target_repr = ast.unparse(node.func.func.value)
            except Exception:
                target_repr = "<dict>"
            self.findings["dict_get_call"].append(
                (self._loc(node), f"{target_repr}.get(...)(...)")
            )

        # Pattern 5 & 6: globals()[name](...) / locals()[name](...)
        if isinstance(node.func, ast.Subscript) and isinstance(node.func.value, ast.Call) \
                and isinstance(node.func.value.func, ast.Name) \
                and node.func.value.func.id in ("globals", "locals"):
            self.findings["globals_locals_dispatch"].append(
                (self._loc(node), f"{node.func.value.func.id}()[...](...)")
            )

        self.generic_visit(node)

    def visit_Assign(self, node):
        # Pattern 7: setattr(obj, "name", value) — context for pattern 1/2
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) \
                and node.value.func.id == "setattr":
            self.findings["setattr_call"].append(
                (self._loc(node), "setattr(obj, name, value)")
            )
        self.generic_visit(node)


def scan_repo(repo_path):
    all_findings = defaultdict(list)
    file_count = 0
    error_count = 0

    for root, _, files in os.walk(repo_path):
        if any(skip in root for skip in (".git", "__pycache__", "venv", ".venv", "node_modules")):
            continue
        for fname in files:
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, repo_path)
            file_count += 1
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    source = f.read()
                tree = ast.parse(source, filename=rel_path)
            except SyntaxError:
                error_count += 1
                continue

            finder = ReflectionPatternFinder(rel_path)
            finder.visit(tree)
            for pattern, hits in finder.findings.items():
                all_findings[pattern].extend(hits)

    return all_findings, file_count, error_count


def main():
    if len(sys.argv) != 2:
        print("Usage: python reflection_diagnostic.py <repo_path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    print(f"Scanning for dynamic-dispatch patterns in: {repo_path}")
    print("(This is independent of reflection_resolver.py — ground-truth comparison only)")
    print()

    findings, file_count, error_count = scan_repo(repo_path)

    print(f"Files scanned: {file_count} (parse errors: {error_count})")
    print()
    print("=" * 70)
    print("DYNAMIC-DISPATCH PATTERNS FOUND (candidates for reflection resolver)")
    print("=" * 70)

    total = 0
    for pattern_name, hits in sorted(findings.items(), key=lambda kv: -len(kv[1])):
        print(f"\n{pattern_name}: {len(hits)} occurrence(s)")
        for loc, snippet in hits[:5]:
            print(f"   {loc}  ->  {snippet}")
        if len(hits) > 5:
            print(f"   ... and {len(hits) - 5} more")
        total += len(hits)

    print()
    print("=" * 70)
    print(f"TOTAL candidate dynamic-dispatch call sites: {total}")
    print(f"Your deep_resolution dr_reflection count for this repo should be")
    print(f"compared against this number. If dr_reflection == 0 and this")
    print(f"number is > 0, reflection_resolver.py is not matching these")
    print(f"AST shapes — check its node-matching logic against the patterns")
    print(f"listed above (getattr_literal_call is usually the easiest to")
    print(f"add first — it has a literal string name, fully resolvable).")
    print("=" * 70)


if __name__ == "__main__":
    main()
