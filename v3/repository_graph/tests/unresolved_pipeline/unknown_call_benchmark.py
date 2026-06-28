"""
unknown_call_benchmark.py

Benchmark for UnknownCallAnalyzer.

FIX: same class_index / shared-list fix as call_classification_benchmark.py.
"""

from collections import Counter

from v3.repository_graph.languages.python_adapter import PythonAdapter
from .return_flow_tracker_v2 import ReturnFlowTrackerV2
from .constructor_call_classifier import classify_constructor_calls
from .unknown_call_analyzer import analyze_unknown_calls


def main(repo_path):
    adapter = PythonAdapter()
    report = adapter.scan(repo_root=repo_path, file_paths=[])

    tracker = ReturnFlowTrackerV2(
        repo_path, report.get("class_graph", {}), report.get("function_graph", {})
    )
    class_index = tracker.class_name_index

    classification = classify_constructor_calls(repo_path, class_index)
    results = classification.get("results", [])

    analysis = analyze_unknown_calls(results)
    counts = analysis.get("counts", {})
    examples = analysis.get("examples", {})

    total = sum(counts.values())

    print("=" * 80)
    print("UNKNOWN CALL ANALYSIS")
    print("=" * 80)
    print(f"Unknown calls analyzed: {total:,}")
    print("=" * 80)

    for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        pct = round((count / total) * 100, 2) if total else 0
        print(f"{category:<55}{count:<10}{pct}%")
    print("=" * 80)

    print()
    print("CATEGORY EXAMPLES")
    print("=" * 80)
    for category in sorted(examples.keys()):
        print()
        print(category.upper())
        print("-" * 40)
        for example in examples[category][:20]:
            print(example)
    print("=" * 80)

    unknown_counter = Counter(item["call"] for item in results if item["category"] == "unknown")
    print()
    print("TOP UNKNOWN CALLS")
    print("=" * 80)
    for name, count in unknown_counter.most_common(30):
        print(f"{name:<40}{count}")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else r"C:\repos\v3\flask"
    main(repo)
