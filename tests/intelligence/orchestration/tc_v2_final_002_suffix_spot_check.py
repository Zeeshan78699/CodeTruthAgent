"""
TC_V2_FINAL_002 — Suffix Resolution Spot Check

Purpose:
    The previous inspection showed 109 of 331 resolved edges (~33%) came
    from suffix matching — i.e., the resolver couldn't match the full call
    name and fell back to matching only the trailing segment after the
    last dot. Suffix matching is the fragile path: it resolves obj.do_thing
    to whatever file defines a function named do_thing, regardless of
    whether 'obj' actually belongs to that file.

    This script lists every suffix-resolved edge and flags two warning
    signals so you can spot false positives quickly:
      - "name_collision": the suffix matches multiple files in the index
        (so the resolver picked one arbitrarily)
      - "qualifier_mismatch": the qualifier before the dot doesn't appear
        in the from_file (heuristic — suggests obj is not from that file)

    Read the list. Decide honestly:
      - If most edges look correct: suffix matching is a net positive.
      - If many look wrong: ~33% of resolved edges are noise, and the
        headline cross-file number is inflated by that fraction.
"""

from pathlib import Path
import json

from ai.repository_graph_engine import RepositoryGraphEngine


REPO_ROOT = Path(r"C:\AI_Project\CodeTruthAgent")

OUTPUT_DIR = Path(r"tests/output/v2/dependency_inspection_reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "suffix_resolution_spot_check.json"


def should_ignore(call_name, ignored_calls):
    if call_name in ignored_calls:
        return True
    suffix = call_name.split(".")[-1]
    if suffix in ignored_calls:
        return True
    return False


def main():
    print("=" * 70)
    print("TC_V2_FINAL_002 — Suffix Resolution Spot Check")
    print("=" * 70)

    engine = RepositoryGraphEngine(repo_root=str(REPO_ROOT))
    graph = engine.build_graph()
    ignored_set = engine.ignored_calls

    suffix_edges = []

    for file_path, file_node in graph.files.items():
        # Read the file content once so we can do qualifier-mismatch heuristic.
        try:
            file_text = (REPO_ROOT / file_path).read_text(
                encoding="utf-8", errors="ignore"
            )
        except Exception:
            file_text = ""

        for function in file_node.functions:
            all_calls = list(function.calls) + list(function.method_calls)

            for called_name in all_calls:
                if should_ignore(called_name, ignored_set):
                    continue
                if "." not in called_name:
                    continue
                # Skip if it would have been resolved by exact-function match.
                if called_name in graph.function_index:
                    continue
                if called_name in graph.class_index:
                    continue

                suffix = called_name.split(".")[-1]
                qualifier = called_name.split(".")[0]

                # Only interested in cases that did resolve via suffix to function_index.
                if suffix not in graph.function_index:
                    continue

                target_files = graph.function_index[suffix]
                target_file = target_files[0]

                name_collision = len(target_files) > 1

                # Heuristic: is the qualifier even mentioned in the from_file?
                # If not, the resolver probably picked the wrong target.
                qualifier_in_file = qualifier in file_text if file_text else None

                suffix_edges.append({
                    "from_file": file_path,
                    "from_func": function.name,
                    "called_name": called_name,
                    "qualifier": qualifier,
                    "suffix": suffix,
                    "resolved_to": target_file,
                    "name_collision_count": len(target_files),
                    "all_candidates": target_files,
                    "qualifier_appears_in_from_file": qualifier_in_file,
                    "warning_flags": [
                        f for f in [
                            "name_collision" if name_collision else None,
                            "qualifier_missing_in_from_file"
                            if qualifier_in_file is False else None,
                        ] if f
                    ],
                })

    total = len(suffix_edges)
    flagged = [e for e in suffix_edges if e["warning_flags"]]
    clean = [e for e in suffix_edges if not e["warning_flags"]]

    print(f"\nTotal suffix-resolved edges:       {total}")
    print(f"  Edges with warning flags:        {len(flagged)}")
    print(f"  Edges with no warnings:          {len(clean)}")

    # Show all flagged edges first — these are the most likely false positives.
    print("\n" + "=" * 70)
    print("FLAGGED EDGES (most likely false positives)")
    print("=" * 70)
    for i, e in enumerate(flagged, 1):
        print(f"\n[{i}] {e['from_file']}::{e['from_func']}")
        print(f"    called:        {e['called_name']}")
        print(f"    resolved to:   {e['resolved_to']}")
        print(f"    warnings:      {', '.join(e['warning_flags'])}")
        if "name_collision" in e["warning_flags"]:
            print(f"    candidates:    {e['all_candidates']}")

    # Show the clean ones too — these are probably correct, but worth scanning.
    print("\n" + "=" * 70)
    print("UNFLAGGED EDGES (likely correct, but skim a few)")
    print("=" * 70)
    for i, e in enumerate(clean[:20], 1):
        print(f"[{i}] {e['from_file']}::{e['from_func']}"
              f"  ->  {e['called_name']}  ({e['resolved_to']})")
    if len(clean) > 20:
        print(f"... and {len(clean) - 20} more.")

    # Save full data for reference.
    report = {
        "test_case": "TC_V2_FINAL_002_SUFFIX_RESOLUTION_SPOT_CHECK",
        "repository_root": str(REPO_ROOT),
        "total_suffix_resolved": total,
        "flagged_count": len(flagged),
        "clean_count": len(clean),
        "flagged_edges": flagged,
        "clean_edges": clean,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print(f"\n[Report Saved] {OUTPUT_FILE}")
    print("\nNext step: read the flagged list above. For each one, decide:")
    print("  - Is the resolved_to file plausibly where that method lives?")
    print("  - Or did the resolver pick a wrong file because of a name clash?")
    print("If most flagged edges look correct, suffix matching is working.")
    print("If most look wrong, you have a known noise floor of ~33%.")


if __name__ == "__main__":
    main()