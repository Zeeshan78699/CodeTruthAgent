"""
call_classification_benchmark.py

Benchmark for ConstructorCallClassifier.

FIX: class_index now comes from ReturnFlowTrackerV2's already-flattened
class_name_index, and constructor_call_classifier.py uses the shared
known_framework_functions list - no more drift between tools.
"""

from collections import Counter

from v3.repository_graph.languages.python_adapter import PythonAdapter
from .return_flow_tracker_v2 import ReturnFlowTrackerV2
from .constructor_call_classifier import classify_constructor_calls


def main(repo_path):
    adapter = PythonAdapter()
    report = adapter.scan(repo_root=repo_path, file_paths=[])

    tracker = ReturnFlowTrackerV2(
        repo_path, report.get("class_graph", {}), report.get("function_graph", {})
    )
    class_index = tracker.class_name_index
    print(f"CLASS INDEX SIZE: {len(class_index)}")

    classification = classify_constructor_calls(repo_path, class_index)
    counts = classification.get("counts", {})
    results = classification.get("results", [])

    print("=" * 80)
    print("CALL CLASSIFICATION BENCHMARK")
    print("=" * 80)

    total = sum(counts.values())
    print(f"Total call returns: {total:,}")
    print("=" * 80)

    for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        pct = round((count / total) * 100, 2) if total else 0
        print(f"{category:<20}{count:<10}{pct}%")
    print("=" * 80)

    call_counter = Counter(item["call"] for item in results)
    print()
    print("TOP CALLS")
    print("=" * 80)
    for name, count in call_counter.most_common(30):
        print(f"{name:<40}{count}")
    print("=" * 80)

    print()
    print("UNKNOWN EXAMPLES")
    print("=" * 80)
    shown = 0
    for item in results:
        if item["category"] != "unknown":
            continue
        print(item["call"])
        shown += 1
        if shown >= 30:
            break
    print("=" * 80)

    return classification


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else r"C:\repos\v3\flask"
    main(repo)
