"""
object_method_benchmark.py

Benchmark for ObjectMethodResolver.

FIX: object_method_resolver.py now substitutes "<unknown>" itself at
the source, so this benchmark no longer needs (and no longer has) a
second, separate substitution that could drift out of sync with it.
"""

from collections import Counter

from .object_method_resolver import analyze_object_methods


def main(repo_path):
    analysis = analyze_object_methods(repo_path)

    counts = analysis.get("counts", {})
    examples = analysis.get("examples", {})
    results = analysis.get("results", [])

    total = sum(counts.values())

    print("=" * 80)
    print("OBJECT METHOD ANALYSIS")
    print("=" * 80)
    print(f"Object method calls: {total:,}")
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
        for obj, method in examples[category][:20]:
            print(f"{obj}.{method}")

    print("=" * 80)

    method_counter = Counter(item["method"] for item in results)
    print()
    print("TOP METHODS")
    print("=" * 80)
    for name, count in method_counter.most_common(30):
        print(f"{name:<40}{count}")
    print("=" * 80)

    object_counter = Counter(item["object"] for item in results)
    print()
    print("TOP OBJECTS")
    print("=" * 80)
    for name, count in object_counter.most_common(30):
        print(f"{name:<40}{count}")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else r"C:\repos\v3\flask"
    main(repo)
