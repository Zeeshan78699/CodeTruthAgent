"""
origin_resolution_benchmark.py

Experimental Module 2.5 validation harness.

FIX: constructor_origin_tracker.py and return_flow_tracker.py (v1)
both check `candidate in self.class_graph` against the raw, module-
keyed class_graph - same root cause fixed elsewhere. Flattened once
here before either is called.

Pipeline:
Assignment Chain Builder -> Constructor Origin Tracker
                          -> Factory Origin Tracker
                          -> Return Flow Tracker
                          -> Origin Resolution Metrics

Truth Boundary:
- Proven origins only
- No guessing
"""

import json

from v3.repository_graph.languages.python_adapter import PythonAdapter
from .assignment_chain_builder import build_assignment_table
from .constructor_origin_tracker import build_constructor_origins
from .factory_origin_tracker import build_factory_origins
from .return_flow_tracker import build_return_type_table
from .flatten_class_graph import flatten_class_graph


class OriginResolutionBenchmark:

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def run(self):
        print("=" * 80)
        print("ORIGIN RESOLUTION BENCHMARK")
        print("=" * 80)

        adapter = PythonAdapter()
        report = adapter.scan(repo_root=self.repo_path, file_paths=[])

        unresolved = report.get("unresolved", [])

        # FIX: flatten before use.
        flat_class_graph = flatten_class_graph(
            report.get("class_graph", {}), report.get("function_graph", {})
        )

        print(f"Total unresolved: {len(unresolved):,}")

        assignment_table = build_assignment_table(self.repo_path)
        print(f"Assignments found: {len(assignment_table):,}")

        constructor_origins = build_constructor_origins(assignment_table, flat_class_graph)
        print(f"Constructor origins: {len(constructor_origins):,}")

        factory_origins = build_factory_origins(assignment_table, flat_class_graph)
        print(f"Factory origins: {len(factory_origins):,}")

        return_type_table = build_return_type_table(self.repo_path, flat_class_graph)
        print(f"Return types proven: {len(return_type_table):,}")

        total_origins = len(constructor_origins) + len(factory_origins)
        print(f"Total origins proven: {total_origins:,}")
        print("=" * 80)

        return {
            "unresolved": len(unresolved),
            "assignments": len(assignment_table),
            "constructor_origins": len(constructor_origins),
            "factory_origins": len(factory_origins),
            "return_types": len(return_type_table),
            "total_origins": total_origins,
        }


def run_flask_origin_benchmark(repo_path):
    return OriginResolutionBenchmark(repo_path).run()


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else r"C:\repos\v3\flask"
    results = run_flask_origin_benchmark(repo)
    print(json.dumps(results, indent=2))
