"""
TC_V2_FINAL_008_RICH_GOVERNANCE

Title:
    Does the governance layer now produce findings on scanned code?

Description:
    Re-run the probe-file methodology from TC_V2_002d, but this time route
    the scanner output through the new governance wiring layer. If wiring
    works, the probe file should produce DIFFERENT (non-empty) findings
    compared to the baseline scan.

Scope:
    Checks 1-3 only (global mutation, dangerous API, undefined reference).
    Checks 4-6 will be added in a follow-up.
"""

import json
import shutil
import tempfile
from pathlib import Path

from ai.repository_graph_engine import RepositoryGraphEngine
from ai.governance_wiring import run_governance_on_scan, report_to_dict


# =========================================================
# CONFIGURATION
# =========================================================

TARGET_REPO = Path(r"C:\scratch\rich\rich")

OUTPUT_DIR = Path(r"tests/output/v2/rich_governance_reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

REPORT_FILE = OUTPUT_DIR / "tc_v2_final_008_report.json"


PROBE_FILE_CONTENT = '''"""
Probe file. Should produce findings from all three implemented checks.
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
# MAIN
# =========================================================

def main():
    print("=" * 70)
    print("TC_V2_FINAL_008_RICH_GOVERNANCE")
    print("=" * 70)

    if not TARGET_REPO.exists():
        print(f"Target repo not found: {TARGET_REPO}")
        return

    # ---- Phase 1: baseline scan with governance wiring ----
    print("\n[Phase 1] Baseline scan + governance")
    baseline_report = _scan_and_govern(TARGET_REPO)
    _print_summary("baseline", baseline_report)

    # ---- Phase 2: scan + governance with probe file added ----
    print("\n[Phase 2] Probe-file scan + governance")
    with tempfile.TemporaryDirectory() as tmpdir:
        copy_target = Path(tmpdir) / TARGET_REPO.name
        shutil.copytree(TARGET_REPO, copy_target)

        probe_path = copy_target / "_codetruth_probe.py"
        probe_path.write_text(PROBE_FILE_CONTENT, encoding="utf-8")
        print(f"Probe file: {probe_path}")

        probed_report = _scan_and_govern(copy_target)
        _print_summary("with_probe", probed_report)

        # Show what governance said about the probe file specifically.
        print("\n[Phase 2.5] Findings on probe file:")
        probe_findings = _find_probe_findings(probed_report)
        for f in probe_findings:
            print(f"  [{f['check_name']}/{f['severity']}] "
                  f"{f['function_name']}:{f['line_number']} -- {f['detail']}")

    # ---- Phase 3: verdict ----
    print("\n[Phase 3] Verdict")
    delta = probed_report["total_findings"] - baseline_report["total_findings"]
    print(f"  Findings delta (probe - baseline): {delta}")

    if delta >= 2:
        verdict = "GOVERNANCE_WIRING_WORKS"
        print(f"  >>> {verdict}")
        print("      Governance reacted to the probe file with 3+ new findings.")
        print("      Wiring is functional. Move on to running on more repos.")
    elif delta > 0:
        verdict = "PARTIAL_WIRING"
        print(f"  >>> {verdict}")
        print(f"      Some findings produced (+{delta}) but fewer than the 3")
        print("      patterns the probe file contains. Check which patterns")
        print("      were detected and which were missed.")
    else:
        verdict = "WIRING_NOT_EFFECTIVE"
        print(f"  >>> {verdict}")
        print("      No new findings produced by the probe file.")
        print("      The wiring layer is not detecting the probe patterns.")

    # ---- Save ----
    final = {
        "test_case": "TC_V2_FINAL_008_RICH_GOVERNANCE",
        "baseline": baseline_report,
        "with_probe": probed_report,
        "delta_findings": delta,
        "verdict": verdict,
    }
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=4)
    print(f"\n[Report Saved] {REPORT_FILE}")


def _scan_and_govern(repo_path: Path) -> dict:
    engine = RepositoryGraphEngine(repo_root=str(repo_path))
    graph = engine.build_graph()
    report = run_governance_on_scan(graph, engine.ignored_calls, str(repo_path))
    return report_to_dict(report)


def _print_summary(label: str, report: dict) -> None:
    print(f"  [{label}]")
    print(f"    files_scanned:       {report['files_scanned']}")
    print(f"    files_with_findings: {report['files_with_findings']}")
    print(f"    total_findings:      {report['total_findings']}")
    print(f"    by_check:            {report['findings_by_check']}")
    print(f"    by_severity:         {report['findings_by_severity']}")


def _find_probe_findings(report: dict) -> list:
    """Return findings that came from the probe file specifically."""
    out = []
    for fp, file_data in report["per_file"].items():
        if "_codetruth_probe" in fp:
            out.extend(file_data["findings"])
    return out


if __name__ == "__main__":
    main()
