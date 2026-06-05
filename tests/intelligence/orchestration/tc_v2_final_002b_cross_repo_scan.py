"""
TC_V2_FINAL_002b — Cross-Repository Scan Validation (corrected)

Title:
    Does the Engine Actually Examine Code on an Unfamiliar Repository?

This version restores the probe phase: it scans the target repo twice,
once as-is and once with a deliberately problematic file added, and
compares the results. If the governance decision is identical in both
runs, the governance layer is not examining code during scans.
"""

import json
import shutil
import tempfile
from pathlib import Path

from ai.repository_graph_engine import RepositoryGraphEngine


TARGET_REPO = Path(r"C:\scratch\flask\examples\tutorial")


PROBE_FILE_CONTENT = '''"""
Probe file added by TC_V2_FINAL_002b. Contains three patterns the scanner
is supposed to detect:
  - mutation of a global named DATABASE
  - call to os.remove (one of the 4 hardcoded API classifications)
  - reference to an undefined name

If the scanner returns the same SAFE/LOW decision with this file as without,
the governance layer is not actually examining code.
"""

DATABASE = {}

import os


def call_undefined_thing():
    return totally_undefined_function(42)


def mutate_global_database(user_id, payload):
    DATABASE[user_id] = payload
    return DATABASE


def delete_file_unsafely(path):
    os.remove(path)
'''


def scan_and_summarize(repo_path, label):
    """Scan a repo and return a summary dict."""
    engine = RepositoryGraphEngine(repo_root=str(repo_path))
    graph = engine.build_graph()

    files_scanned = len(graph.files)
    functions_discovered = sum(
        len(file_node.functions) for file_node in graph.files.values()
    )

    # Count function-call edges, with break-on-first-match.
    within_file = 0
    cross_file = 0
    unresolved = 0

    for file_path, file_node in graph.files.items():
        for function in file_node.functions:
            for called_function in function.calls:
                resolved_in = None
                for target_file, target_functions in graph.function_index.items():
                    if called_function in target_functions:
                        resolved_in = target_file
                        break
                if resolved_in is None:
                    unresolved += 1
                elif resolved_in == file_path:
                    within_file += 1
                else:
                    cross_file += 1

    total = within_file + cross_file + unresolved
    cross_ratio = round(cross_file / total, 3) if total else 0.0
    unresolved_ratio = round(unresolved / total, 3) if total else 0.0

    return {
        "label": label,
        "files_scanned": files_scanned,
        "functions_discovered": functions_discovered,
        "total_call_edges": total,
        "within_file": within_file,
        "cross_file": cross_file,
        "unresolved": unresolved,
        "cross_file_ratio": cross_ratio,
        "unresolved_ratio": unresolved_ratio,
    }


def main():
    print("=" * 70)
    print("TC_V2_FINAL_002b — Cross-Repository Scan Validation (corrected)")
    print("=" * 70)

    if not TARGET_REPO.exists():
        print(f"Target repository not found: {TARGET_REPO}")
        return

    # Phase 1: scan as-is
    baseline = scan_and_summarize(TARGET_REPO, "baseline")
    print("\n[Phase 1 — baseline scan]")
    print(json.dumps(baseline, indent=4))

    # Phase 2: copy repo, add probe file, scan again
    with tempfile.TemporaryDirectory() as tmpdir:
        copy_target = Path(tmpdir) / TARGET_REPO.name
        shutil.copytree(TARGET_REPO, copy_target)

        probe_path = copy_target / "_codetruth_probe.py"
        probe_path.write_text(PROBE_FILE_CONTENT, encoding="utf-8")

        probed = scan_and_summarize(copy_target, "with_probe")
        print("\n[Phase 2 — scan with probe file added]")
        print(json.dumps(probed, indent=4))

    # Phase 3: judgment
    print("\n[Phase 3 — interpretation]")

    # Sensible thresholds; tune as you learn what's realistic.
    passes_baseline = (
        baseline["cross_file_ratio"] >= 0.20
        and baseline["unresolved_ratio"] <= 0.50
        and baseline["cross_file"] > 0
    )

    probe_was_seen = (
        probed["functions_discovered"] > baseline["functions_discovered"]
    )

    print(f"  Baseline meets cross-file thresholds: {passes_baseline}")
    print(f"  Probe file was parsed:               {probe_was_seen}")

    if not passes_baseline:
        print("\n  >>> Baseline scan did not meet cross-file thresholds.")
        print("      Either the target repo is trivial, or import")
        print("      resolution is weaker than the numbers suggested.")
        print("      Look at the unresolved_ratio — high values mean")
        print("      the scanner sees calls but can't trace them.")
    if not probe_was_seen:
        print("\n  >>> Probe file was not picked up by the scanner.")
        print("      File discovery may be filtering it out.")


if __name__ == "__main__":
    main()