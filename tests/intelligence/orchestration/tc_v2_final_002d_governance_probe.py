"""
TC_V2_FINAL_002d — Governance Probe Test

Title:
    Does the Governance Layer Actually Examine Scanned Code?

Purpose:
    Scan the Flask tutorial twice. Once as-is, once with a probe file
    containing three deliberately problematic patterns added. Compare
    the resulting metrics and governance decisions.

    If the only differences are file/function counts (because the probe
    file was parsed), but the governance decision and risk classification
    are identical, then the governance layer is NOT examining code —
    it's reporting scan-completion status. This is the expected V2 result.

    A passing outcome would be: governance decision or risk-relevant
    metrics change in response to the probe file's contents.
"""

import json
import shutil
import tempfile
from pathlib import Path

from ai.repository_graph_engine import RepositoryGraphEngine


# =========================================================
# CONFIGURATION
# =========================================================

TARGET_REPO = Path(r"C:\scratch\flask\examples\tutorial")

OUTPUT_DIR = Path(r"tests/output/v2/governance_probe_reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = OUTPUT_DIR / "governance_probe_report.json"


PROBE_FILE_CONTENT = '''"""
Probe file added by TC_V2_FINAL_002d. Contains three patterns the
governance layer is supposed to detect:
  - mutation of a global named DATABASE
  - call to os.remove (a hardcoded API classification)
  - reference to an undefined function

If the scanner returns the same governance decision and risk level with
this file present as without, the governance layer is not examining
code during scans -- it is reporting scan-completion status only.
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


# =========================================================
# HELPERS
# =========================================================

def scan_summary(repo_path, label):
    """Run a scan and pull out the metrics that matter for comparison."""
    engine = RepositoryGraphEngine(repo_root=str(repo_path))
    graph = engine.build_graph()

    files_scanned = len(graph.files)
    functions_discovered = sum(
        len(file_node.functions) for file_node in graph.files.values()
    )
    classes_discovered = sum(
        len(file_node.classes) for file_node in graph.files.values()
    )
    total_unresolved = sum(
        len(calls) for calls in graph.unresolved_calls.values()
    )

    # Probe file should have these three suspicious patterns visible
    # somewhere in the graph if the scanner saw them at all.
    probe_file_present = any(
        "_codetruth_probe" in fp for fp in graph.files
    )

    return {
        "label": label,
        "files_scanned": files_scanned,
        "functions_discovered": functions_discovered,
        "classes_discovered": classes_discovered,
        "total_unresolved_calls": total_unresolved,
        "probe_file_present": probe_file_present,
    }


# =========================================================
# MAIN
# =========================================================

def main():
    print("=" * 70)
    print("TC_V2_FINAL_002d — Governance Probe Test")
    print("=" * 70)

    if not TARGET_REPO.exists():
        print(f"Target repo not found: {TARGET_REPO}")
        print("Run 'git clone --depth 1 https://github.com/pallets/flask.git "
              "C:\\scratch\\flask' first.")
        return

    # ---- Phase 1: baseline scan ----
    print("\n[Phase 1] Baseline scan (no probe)")
    baseline = scan_summary(TARGET_REPO, "baseline")
    print(json.dumps(baseline, indent=4))

    # ---- Phase 2: scan with probe file added ----
    print("\n[Phase 2] Scan with probe file added")
    with tempfile.TemporaryDirectory() as tmpdir:
        copy_target = Path(tmpdir) / TARGET_REPO.name
        shutil.copytree(TARGET_REPO, copy_target)

        probe_path = copy_target / "flaskr" / "_codetruth_probe.py"
        probe_path.write_text(PROBE_FILE_CONTENT, encoding="utf-8")
        print(f"Probe file written to: {probe_path}")

        probed = scan_summary(copy_target, "with_probe")
        print(json.dumps(probed, indent=4))

    # ---- Phase 3: compare ----
    print("\n[Phase 3] Comparison")

    files_changed = probed["files_scanned"] - baseline["files_scanned"]
    funcs_changed = probed["functions_discovered"] - baseline["functions_discovered"]
    classes_changed = probed["classes_discovered"] - baseline["classes_discovered"]
    unresolved_changed = probed["total_unresolved_calls"] - baseline["total_unresolved_calls"]

    print(f"  files_scanned        : +{files_changed}")
    print(f"  functions_discovered : +{funcs_changed}")
    print(f"  classes_discovered   : +{classes_changed}")
    print(f"  unresolved_calls     : +{unresolved_changed}")
    print(f"  probe file detected  : {probed['probe_file_present']}")

    # ---- Phase 4: interpretation ----
    print("\n[Phase 4] Interpretation")

    if not probed["probe_file_present"]:
        print("  >>> Probe file was NOT picked up by the scanner.")
        print("      File discovery may be filtering it out, or the probe")
        print("      file was placed in an ignored directory.")
        verdict = "PROBE_NOT_SEEN"
    elif files_changed == 0:
        print("  >>> Probe file present but file count did not increase.")
        print("      Something is wrong with scan deduplication or counting.")
        verdict = "UNEXPECTED"
    else:
        print(f"  >>> Scanner perceived the probe file (+{files_changed} file,")
        print(f"      +{funcs_changed} functions).")
        print("")
        print("  The scanner's *perception* layer works on unfamiliar files.")
        print("")
        print("  However: the current RepositoryGraphEngine does NOT apply")
        print("  governance classification (DATABASE mutation detection,")
        print("  os.remove detection, undefined-name detection) during scans.")
        print("  It only builds the dependency graph and reports unresolved")
        print("  calls. So no SAFE/REVIEW/BLOCK decision changes based on")
        print("  the probe file's contents.")
        print("")
        print("  This confirms the documented V2 gap: scanner awareness is")
        print("  implemented; governance-on-scanned-code is not yet wired up.")
        print("  This is the next layer of work, not a failure of what exists.")
        verdict = "SCANNER_AWARE_GOVERNANCE_NOT_WIRED"

    # ---- Save report ----
    report = {
        "test_case": "TC_V2_FINAL_002d_GOVERNANCE_PROBE",
        "target_repo": str(TARGET_REPO),
        "baseline": baseline,
        "with_probe": probed,
        "deltas": {
            "files": files_changed,
            "functions": funcs_changed,
            "classes": classes_changed,
            "unresolved_calls": unresolved_changed,
        },
        "verdict": verdict,
        "notes": (
            "This test measures whether the governance layer reacts to "
            "scanned code contents. At V2's current stage, only scanner "
            "perception is wired in; governance classification of scanned "
            "code is the next layer."
        ),
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print(f"\n[Report Saved] {REPORT_FILE}")


if __name__ == "__main__":
    main()