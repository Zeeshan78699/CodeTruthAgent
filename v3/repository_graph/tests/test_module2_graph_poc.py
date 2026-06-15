"""
test_module2_graph_poc.py
Quick validation script for Module 2's graph_engine.

Run from the CodeTruthAgent project root:
    python v3\\repository_graph\\tests\\test_module2_graph_poc.py
(or adjust the path below if you run it from elsewhere)
"""

import sys
import os
import json

# Add project root to path so "v3" package can be imported
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.graph_engine import build_repository_graph


if __name__ == "__main__":
    # Point this at the folder you want to analyze.
    # Default: Module 1's own source code (known, real, moderately complex)
    target_repo = os.path.join(PROJECT_ROOT, "v3", "repository_cognition")

    print(f"Scanning: {target_repo}\n")

    report = build_repository_graph(target_repo)

    # ---- Summary first ----
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files scanned     : {report['files_scanned']}")
    print(f"Modules parsed    : {report['modules_parsed']}")
    print(f"Governance gate   : {report['governance_gate']}")
    print(f"Unresolved items  : {len(report['unresolved'])}")
    print()

    for module, funcs in report["function_graph"].items():
        print(f"  [function_graph] {module}: {len(funcs)} function(s)")

    print()
    for module, classes in report["class_graph"].items():
        if classes:
            print(f"  [class_graph] {module}: {[c['name'] for c in classes]}")

    print()
    print(f"  [dependency_graph] external packages used: "
          f"{list(report['dependency_graph'].keys())}")

    print()
    print(f"  [call_graph] total resolved call edges: "
          f"{sum(len(v) for v in report['call_graph'].values())}")

    # ---- Unresolved detail ----
    if report["unresolved"]:
        print()
        print("=" * 60)
        print("UNRESOLVED ITEMS (honest log - not bugs, just untracked patterns)")
        print("=" * 60)
        for item in report["unresolved"]:
            print(f"  - [{item.get('pattern')}] {item.get('module')}: {item.get('note')}")

    # ---- Full dump (optional) ----
    print()
    print("=" * 60)
    print("Full report saved to: module2_test_output.json")
    print("=" * 60)
    out_path = os.path.join(os.path.dirname(__file__), "module2_test_output.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
