"""
test_lang_adapters_real_repo.py
Runs the C/C++ and JavaScript adapters against a REAL repo and reports
resolved vs unresolved call counts - same style as
scan_all_repos_module2.py, but for the newer language adapters.

Usage:
    python v3\\repository_graph\\tests\\test_lang_adapters_real_repo.py <repo_path> [max_files]

max_files (optional, default 200): cap on files scanned per language, to
keep runtime reasonable on very large repos.
"""

import sys
import os
import json
from collections import Counter

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.languages.c_cpp_adapter import CCppAdapter
from v3.repository_graph.languages.javascript_adapter import JavaScriptAdapter
from v3.repository_graph.languages.java_adapter import JavaAdapter


ADAPTERS = {
    "c_cpp": (CCppAdapter(), {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"}),
    "javascript": (JavaScriptAdapter(), {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}),
    "java": (JavaAdapter(), {".java"}),
}


def find_files(root, extensions, ignore_dirs=None):
    ignore_dirs = ignore_dirs or {".git", "node_modules", "__pycache__", ".venv", "venv"}
    matches = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for f in filenames:
            if os.path.splitext(f)[1].lower() in extensions:
                matches.append(os.path.join(dirpath, f))
    return matches


def summarize(report):
    unresolved = Counter(u["pattern"] for u in report["unresolved"])
    resolved = Counter(e["resolution"] for edges in report["call_graph"].values() for e in edges)
    total_resolved = sum(resolved.values())
    total_unresolved = sum(unresolved.values())
    total = total_resolved + total_unresolved
    pct = round(100 * total_resolved / total, 1) if total else 100.0
    return {
        "files_with_data": len(report["function_graph"]),
        "functions": sum(len(v) for v in report["function_graph"].values()),
        "classes": sum(len(v) for v in report["class_graph"].values()),
        "external_deps": len(report["dependency_graph"]),
        "resolved_calls": total_resolved,
        "unresolved_calls": total_unresolved,
        "resolved_pct": pct,
        "resolved_breakdown": dict(resolved),
        "unresolved_breakdown": dict(unresolved),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_lang_adapters_real_repo.py <repo_path> [max_files]")
        sys.exit(1)

    repo_path = sys.argv[1]
    max_files = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    print(f"Scanning: {repo_path}\n")

    for lang, (adapter, extensions) in ADAPTERS.items():
        files = find_files(repo_path, extensions)
        if not files:
            print(f"{lang}: 0 files found - skipping\n")
            continue

        scanned = files[:max_files]
        print(f"{lang}: {len(files)} file(s) found, scanning {len(scanned)}...")

        report = adapter.scan(repo_path, scanned)
        summary = summarize(report)

        print(json.dumps(summary, indent=2))
        print()