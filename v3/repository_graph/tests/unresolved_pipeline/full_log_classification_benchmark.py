"""
full_log_classification_benchmark.py

FIX: previously classified the raw, unresolved baseline directly from
adapter.scan() - before any resolver had a chance to run. That meant
cases builtin_type_engine already proves resolvable (.endswith,
.rsplit, .strip, etc.) showed up labeled "unconfirmed", understating
how much is actually known. Now runs the full ResolutionPipeline first
(builtin_type, constructor, factory, property, inheritance, reflection
- everything already proven and wired) and classifies only what's
genuinely still remaining afterward - the honest "what's left" picture.
"""

import json

from v3.repository_graph.languages.python_adapter import PythonAdapter
from .resolution_pipeline import run_resolution_pipeline
from .cause_classifier import classify_unresolved_causes


def main(repo_path):
    adapter = PythonAdapter()
    report = adapter.scan(repo_root=repo_path, file_paths=[])

    pipeline_results = run_resolution_pipeline(
        unresolved_entries=report.get("unresolved", []),
        return_type_table=report.get("return_type_table", {}),
        class_graph=report.get("class_graph", {}),
        repo_path=repo_path,
        function_graph=report.get("function_graph", {}),
        module_graph=report.get("module_graph", {}),
    )

    baseline = pipeline_results["baseline_unresolved"]
    already_resolved = pipeline_results["final"]["resolved_by_pipeline"]
    remaining_entries = pipeline_results["remaining_unresolved_entries"]

    result = classify_unresolved_causes(remaining_entries)
    counts = result["cause_counts"]
    examples = result["cause_examples"]

    total = sum(counts.values())

    print("=" * 80)
    print("FULL LOG CLASSIFICATION BENCHMARK (post-resolution)")
    print("=" * 80)
    print(f"Total unresolved (baseline): {baseline:,}")
    print(f"Already resolved by pipeline (builtin/constructor/factory/property/inheritance/reflection): {already_resolved:,}")
    print(f"Genuinely still unresolved, being classified here: {total:,}")
    print("=" * 80)

    for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        pct = round((count / total) * 100, 2) if total else 0
        print(f"{category:<55}{count:<10}{pct}%")
    print("=" * 80)

    print()
    print("EXAMPLES")
    print("=" * 80)
    for category in sorted(examples.keys()):
        print()
        print(category.upper())
        print("-" * 40)
        for ex in examples[category]:
            print(f"  {ex.get('module')}:{ex.get('lineno')} - {ex.get('note')}")
    print("=" * 80)

    return {"baseline": baseline, "already_resolved": already_resolved,
            "still_unresolved": total, "cause_counts": counts}


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else r"C:\repos\v3\flask"
    main(repo)