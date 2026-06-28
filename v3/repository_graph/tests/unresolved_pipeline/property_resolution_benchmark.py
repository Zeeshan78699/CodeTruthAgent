"""
property_resolution_benchmark.py

Experimental Module 2.5 validation harness.

FIX: build_property_type_table() and run_property_type_engine() were
both receiving the raw, module-keyed class_graph - same root cause as
constructor/factory/inheritance before. Now flattened once via
flatten_class_graph() before either call, same fix already proven to
work in resolution_pipeline.py and return_flow_tracker_v2.py.

Truth Boundary:
- Only proven property types
- Only proven class methods
- No guessing
"""

import json

from v3.repository_graph.languages.python_adapter import PythonAdapter
from .fact_extractor_v2 import extract_facts_v2
from .property_type_table_builder import build_property_type_table
from .property_type_engine import run_property_type_engine
from .flatten_class_graph import flatten_class_graph


class PropertyResolutionBenchmark:

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def run(self):
        print("=" * 80)
        print("PROPERTY RESOLUTION BENCHMARK")
        print("=" * 80)

        adapter = PythonAdapter()
        report = adapter.scan(repo_root=self.repo_path, file_paths=[])

        unresolved = report.get("unresolved", [])
        class_graph = report.get("class_graph", {})
        function_graph = report.get("function_graph", {})

        # FIX: flatten before use.
        flat_class_graph = flatten_class_graph(class_graph, function_graph)

        print(f"Total unresolved: {len(unresolved):,}")

        facts = extract_facts_v2(unresolved)
        property_candidates = [f for f in facts if f.get("property_name")]

        print(f"Property candidates: {len(property_candidates):,}")

        property_type_table = build_property_type_table(self.repo_path, flat_class_graph)

        print(f"Property types proven: {len(property_type_table):,}")

        results = run_property_type_engine(
            extracted_facts=property_candidates,
            property_type_table=property_type_table,
            class_graph=flat_class_graph,
        )

        print(f"Resolved: {results['resolved_count']:,}")
        print(f"Remaining: {results['remaining_count']:,}")

        reduction = 0.0
        if property_candidates:
            reduction = round((results["resolved_count"] / len(property_candidates)) * 100, 2)

        print(f"Reduction: {reduction}%")
        print("=" * 80)

        return {
            "property_candidates": len(property_candidates),
            "property_types_proven": len(property_type_table),
            "property_type_table": property_type_table,
            "resolved": results["resolved_count"],
            "remaining": results["remaining_count"],
            "reduction_pct": reduction,
        }


def run_flask_property_benchmark(repo_path):
    return PropertyResolutionBenchmark(repo_path).run()


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else r"C:\repos\v3\flask"
    results = run_flask_property_benchmark(repo)
    print(json.dumps({k: v for k, v in results.items() if k != "property_type_table"}, indent=2))
