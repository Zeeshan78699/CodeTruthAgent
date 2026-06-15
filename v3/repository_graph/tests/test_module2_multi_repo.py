"""
test_module2_multi_repo.py
Module 2 multi-repo validation - runs graph_engine against several repos
and reports a comparison table.

Usage:
    1. Edit REPO_PATHS below to point at folders you want to test
       (e.g. your existing cloned repos from Module 1's 69-repo set)
    2. Run: python v3\\repository_graph\\tests\\test_module2_multi_repo.py
"""

import sys
import os
import json
from collections import Counter

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.graph_engine import build_repository_graph


# ---- EDIT THIS LIST ----
# Add paths to repos you want to validate against.
# Tip: reuse paths from Module 1's clone_repos.ps1 / scan_all_repos_v3.py
REPO_PATHS = [
    os.path.join(PROJECT_ROOT, "v3", "repository_cognition"),
    os.path.join(PROJECT_ROOT, "v3", "repository_graph"),
    os.path.join(PROJECT_ROOT, "core"),
    os.path.join(PROJECT_ROOT, "ai"),
    # Add more, e.g.:
    # r"C:\path\to\cloned_repos\flask",
    # r"C:\path\to\cloned_repos\django",
]


def run_one(repo_path):
    if not os.path.isdir(repo_path):
        return {"repo": repo_path, "error": "PATH NOT FOUND"}

    try:
        report = build_repository_graph(repo_path)
    except Exception as e:
        return {"repo": repo_path, "error": f"{type(e).__name__}: {e}"}

    unresolved_counts = Counter(u["pattern"] for u in report["unresolved"])
    call_resolution_counts = Counter(
        edge["resolution"]
        for edges in report["call_graph"].values()
        for edge in edges
    )

    total_calls = sum(call_resolution_counts.values())
    total_unresolved = len(report["unresolved"])
    total_edges_attempted = total_calls + total_unresolved
    resolved_pct = (
        round(100 * total_calls / total_edges_attempted, 1)
        if total_edges_attempted else 100.0
    )

    # Detail dump for the two patterns worth inspecting
    interesting = [
        u for u in report["unresolved"]
        if u["pattern"] in ("name_call_unresolved", "self_method_not_found")
    ]

    return {
        "repo": os.path.basename(repo_path.rstrip("\\/")),
        "files_scanned": report["files_scanned"],
        "modules_parsed": report["modules_parsed"],
        "functions": sum(len(v) for v in report["function_graph"].values()),
        "classes": sum(len(v) for v in report["class_graph"].values()),
        "external_deps": len(report["dependency_graph"]),
        "resolved_calls": total_calls,
        "unresolved": total_unresolved,
        "unresolved_breakdown": dict(unresolved_counts),
        "call_resolution_breakdown": dict(call_resolution_counts),
        "resolved_pct": resolved_pct,
        "governance_gate": report["governance_gate"],
        "interesting_unresolved": interesting,
    }


if __name__ == "__main__":
    results = []
    for path in REPO_PATHS:
        print(f"Scanning: {path}")
        results.append(run_one(path))

    print()
    print("=" * 100)
    print(f"{'Repo':<25} {'Files':>6} {'Mods':>5} {'Funcs':>6} {'Class':>6} "
          f"{'Deps':>5} {'Resolved':>9} {'Unresolved':>11} {'%Resolved':>10} {'Gate':>10}")
    print("=" * 100)

    for r in results:
        if "error" in r:
            print(f"{os.path.basename(r['repo']):<25} ERROR: {r['error']}")
            continue
        print(f"{r['repo']:<25} {r['files_scanned']:>6} {r['modules_parsed']:>5} "
              f"{r['functions']:>6} {r['classes']:>6} {r['external_deps']:>5} "
              f"{r['resolved_calls']:>9} {r['unresolved']:>11} "
              f"{r['resolved_pct']:>9}% {r['governance_gate']:>10}")

    print()
    print("=" * 100)
    print("UNRESOLVED PATTERN BREAKDOWN PER REPO")
    print("=" * 100)
    for r in results:
        if "error" in r:
            continue
        print(f"\n{r['repo']}:")
        print(f"  unresolved : {r['unresolved_breakdown']}")
        print(f"  resolved   : {r['call_resolution_breakdown']}")

    print()
    print("=" * 100)
    print("INTERESTING UNRESOLVED ITEMS (name_call_unresolved / self_method_not_found)")
    print("=" * 100)
    for r in results:
        if "error" in r or not r.get("interesting_unresolved"):
            continue
        print(f"\n{r['repo']}:")
        for item in r["interesting_unresolved"]:
            print(f"  [{item['pattern']}] {item['module']} line {item['lineno']}: {item['note']}")

    # Save full results
    out_path = os.path.join(os.path.dirname(__file__), "module2_multi_repo_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to: {out_path}")