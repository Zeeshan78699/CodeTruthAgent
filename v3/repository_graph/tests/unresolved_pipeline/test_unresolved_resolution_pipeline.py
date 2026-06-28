"""
test_unresolved_resolution_pipeline.py

Experimental Module 2.5 validation harness. Runs the full resolution
pipeline (builtin/constructor/factory/property/inheritance/reflection)
against a real repository and prints the resolver-by-resolver results.

IMPORTANT: imports explicitly from
v3.repository_graph.tests.unresolved_pipeline.resolution_pipeline -
the real, maintained file with all fixes applied (fact_extractor_v2
switch, flatten_class_graph, origin enrichment, etc.). If a different,
older copy of this test file exists elsewhere in the project with
stale dependencies, this one should replace it.

This file does NOT modify Module 2. It only consumes Module 2 output.
"""

import json
import os

from v3.repository_graph.languages.python_adapter import PythonAdapter
from v3.repository_graph.tests.unresolved_pipeline.resolution_pipeline import (
    run_resolution_pipeline,
)

REPO_PATH = r"C:\repos\v3\flask"
OUTPUT_DIR = r"v3\outputs\unresolved_pipeline"


def main(repo_path=REPO_PATH):
    print("=" * 80)
    print("FLASK UNRESOLVED PIPELINE")
    print("=" * 80)

    adapter = PythonAdapter()
    report = adapter.scan(repo_root=repo_path, file_paths=[])

    unresolved = report.get("unresolved", [])
    print(f"\nUNRESOLVED COUNT: {len(unresolved):,}")

    result = run_resolution_pipeline(
        unresolved_entries=unresolved,
        return_type_table=report.get("return_type_table", {}),
        class_graph=report.get("class_graph", {}),
        repo_path=repo_path,
        function_graph=report.get("function_graph", {}),
        module_graph=report.get("module_graph", {}),
    )

    print("=" * 80)
    print(f"Baseline Unresolved: {result['baseline_unresolved']:,}")
    print(f"Remaining Unresolved: {result['final']['remaining_unresolved']:,}")
    print(f"Reduction: {result['final']['reduction_pct']}%")
    print()
    print("Resolver Results")
    for resolver, count in result["resolver_results"].items():
        print(f"  {resolver}: {count}")
    print("=" * 80)

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        out_path = os.path.join(OUTPUT_DIR, "flask_resolution_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"\nReport saved: {out_path}")
    except Exception as e:
        print(f"\n(Could not save report: {e})")

    return result


if __name__ == "__main__":
    main()
