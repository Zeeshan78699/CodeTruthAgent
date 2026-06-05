r"\s""""
TC_V2_FINAL_002 — Dependency Inspection Validation (extended v3)

Title:
    Are the Detected Dependencies Truly Cross-File?

What changed from v2 (extended):
  1. Calls to builtins and common stdlib methods (sum, print, endswith,
     replace, json.dump, os.path.join, etc.) are now filtered out before
     counting, using the same ignored_calls set the engine maintains.
     Previously these dragged the resolution rate down artificially.
  2. The report now distinguishes three categories:
       total_call_sites  — every call discovered
       ignored           — calls filtered as builtins / stdlib / common methods
       considered        — total_call_sites minus ignored; the calls that
                           are realistic candidates for cross-file resolution
       resolved          — considered calls that mapped to a defining file
       unresolved        — considered calls that did not map anywhere
  3. resolution_rate is now (resolved / considered), not (resolved / total).
     This measures resolver quality on user-defined code, not on print().
  4. Honest thresholds tuned for the new metric: resolution_rate >= 0.65,
     cross_file_ratio >= 0.10.
  5. Ignored-call examples are also surfaced so it's easy to spot-check
     that the filter is doing the right thing.
"""

from collections import Counter
from pathlib import Path
import json

from ai.repository_graph_engine import RepositoryGraphEngine


# =========================================================
# CONFIGURATION
# =========================================================

REPO_ROOT = Path(r"C:\AI_Project\CodeTruthAgent")

OUTPUT_DIR = Path(r"tests/output/v2/dependency_inspection_reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TEXT_OUTPUT = OUTPUT_DIR / "inspect_dependencies_output.txt"
JSON_OUTPUT = OUTPUT_DIR / "inspect_dependencies_report.json"

# Honest thresholds.
# Higher resolution_rate threshold now because we filter out the noise.
MIN_RESOLUTION_RATE = 0.65
MIN_CROSS_FILE_RATIO = 0.10


# =========================================================
# RESOLUTION HELPERS
# =========================================================

def should_ignore(call_name, ignored_calls):
    """Mirror the engine's filter: skip calls that match the ignore set,
    either by full name or by trailing segment after '.'."""
    if call_name in ignored_calls:
        return True
    suffix = call_name.split(".")[-1]
    if suffix in ignored_calls:
        return True
    return False


def resolve_call(call_name, function_index, class_index):
    """
    Try to resolve a call name to a defining file.

    Returns (target_file, resolution_kind) where resolution_kind is one of:
      function_exact / function_suffix / class_exact / class_suffix / None
    """
    suffix = call_name.split(".")[-1]

    if call_name in function_index:
        return function_index[call_name][0], "function_exact"

    if "." in call_name and suffix in function_index:
        return function_index[suffix][0], "function_suffix"

    if call_name in class_index:
        return class_index[call_name][0], "class_exact"

    if "." in call_name and suffix in class_index:
        return class_index[suffix][0], "class_suffix"

    return None, None


# =========================================================
# MAIN
# =========================================================

def main():
    print("=" * 70)
    print("TC_V2_FINAL_002 — Dependency Inspection Validation (extended v3)")
    print("=" * 70)

    # ---- Build graph ----
    engine = RepositoryGraphEngine(repo_root=str(REPO_ROOT))
    graph = engine.build_graph()
    ignored_set = engine.ignored_calls

    # ---- Walk every call site ----
    total_call_sites = 0
    ignored = 0
    ignored_examples = []

    considered_edges = []

    for file_path, file_node in graph.files.items():
        for function in file_node.functions:
            all_calls = list(function.calls) + list(function.method_calls)

            for called_name in all_calls:
                total_call_sites += 1

                if should_ignore(called_name, ignored_set):
                    ignored += 1
                    if len(ignored_examples) < 5:
                        ignored_examples.append({
                            "from_file": file_path,
                            "from_func": function.name,
                            "ignored_call": called_name,
                        })
                    continue

                target_file, kind = resolve_call(
                    called_name, graph.function_index, graph.class_index
                )
                considered_edges.append({
                    "from_file": file_path,
                    "from_func": function.name,
                    "to_file": target_file,
                    "to_func": called_name,
                    "resolution_kind": kind,
                    "call_style": "method" if "." in called_name else "bare",
                })

    # ---- Classify considered edges ----
    within_file = 0
    cross_file = 0
    unresolved = 0
    recursive = 0

    cross_examples = []
    within_examples = []
    unresolved_examples = []

    resolution_kind_counts = Counter()
    call_style_counts = Counter()

    for edge in considered_edges:
        call_style_counts[edge["call_style"]] += 1

        if edge["to_file"] is None:
            unresolved += 1
            if len(unresolved_examples) < 5:
                unresolved_examples.append(edge)
            continue

        resolution_kind_counts[edge["resolution_kind"]] += 1

        if edge["from_file"] == edge["to_file"]:
            within_file += 1
            if edge["from_func"] == edge["to_func"]:
                recursive += 1
            if len(within_examples) < 5:
                within_examples.append(edge)
        else:
            cross_file += 1
            if len(cross_examples) < 5:
                cross_examples.append(edge)

    considered = len(considered_edges)
    resolved = within_file + cross_file
    resolution_rate = round(resolved / considered, 3) if considered else 0.0
    cross_file_of_resolved = round(cross_file / resolved, 3) if resolved else 0.0
    cross_file_of_considered = round(cross_file / considered, 3) if considered else 0.0
    ignored_fraction = round(ignored / total_call_sites, 3) if total_call_sites else 0.0

    # ---- Coverage ----
    files_with_outgoing = Counter()
    for edge in considered_edges:
        if edge["from_file"]:
            files_with_outgoing[edge["from_file"]] += 1

    # ---- Honest governance decision ----
    passes = (
        resolution_rate >= MIN_RESOLUTION_RATE
        and cross_file_of_resolved >= MIN_CROSS_FILE_RATIO
    )
    governance_decision = "PASS" if passes else "FAIL"

    failure_reasons = []
    if resolution_rate < MIN_RESOLUTION_RATE:
        failure_reasons.append(
            f"resolution_rate {resolution_rate} below threshold {MIN_RESOLUTION_RATE}"
        )
    if cross_file_of_resolved < MIN_CROSS_FILE_RATIO:
        failure_reasons.append(
            f"cross_file_of_resolved {cross_file_of_resolved} below threshold {MIN_CROSS_FILE_RATIO}"
        )

    # ---- Final report ----
    final_report = {
        "test_case": "TC_V2_FINAL_002_DEPENDENCY_INSPECTION_EXTENDED_V3",
        "repository_root": str(REPO_ROOT),

        "totals": {
            "total_call_sites": total_call_sites,
            "ignored": ignored,
            "considered": considered,
            "resolved": resolved,
            "within_file": within_file,
            "cross_file": cross_file,
            "unresolved": unresolved,
            "recursive_self_calls": recursive,
        },

        "ratios": {
            "ignored_fraction_of_total": ignored_fraction,
            "resolution_rate": resolution_rate,
            "cross_file_of_resolved": cross_file_of_resolved,
            "cross_file_of_considered": cross_file_of_considered,
        },

        "call_style_breakdown": dict(call_style_counts),
        "resolution_kind_breakdown": dict(resolution_kind_counts),

        "coverage": {
            "files_with_outgoing_calls": len(files_with_outgoing),
            "total_files_scanned": len(graph.files),
        },

        "thresholds": {
            "min_resolution_rate": MIN_RESOLUTION_RATE,
            "min_cross_file_ratio": MIN_CROSS_FILE_RATIO,
        },

        "governance_decision": governance_decision,
        "failure_reasons": failure_reasons,

        "cross_file_examples": cross_examples,
        "within_file_examples": within_examples,
        "unresolved_examples": unresolved_examples,
        "ignored_examples": ignored_examples,
    }

    # ---- Display ----
    print("\n[Totals]")
    print(json.dumps(final_report["totals"], indent=4))

    print("\n[Ratios]")
    print(json.dumps(final_report["ratios"], indent=4))

    print("\n[Call Style Breakdown]  (after ignore filter)")
    print(json.dumps(final_report["call_style_breakdown"], indent=4))

    print("\n[Resolution Kind Breakdown]")
    print(json.dumps(final_report["resolution_kind_breakdown"], indent=4))

    print("\n[Coverage]")
    print(json.dumps(final_report["coverage"], indent=4))

    print("\n[Ignored Examples] (spot-check these: they should all be"
          " builtins or noise, not real user code)")
    for ex in ignored_examples:
        print(f"  {ex['from_file']}::{ex['from_func']} -> {ex['ignored_call']}")

    print("\n[Unresolved Examples] (spot-check: these are real user-code"
          " calls the resolver missed — investigate why)")
    for ex in unresolved_examples:
        print(f"  {ex['from_file']}::{ex['from_func']} -> {ex['to_func']}")

    print(f"\n[Governance Decision] {governance_decision}")
    if failure_reasons:
        print("Failure reasons:")
        for reason in failure_reasons:
            print(f"  - {reason}")

    # ---- Save ----
    with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=4)

    with open(TEXT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(json.dumps(final_report, indent=4))

    print(f"\n[Reports Generated] {OUTPUT_DIR}")


if __name__ == "__main__":
    main()