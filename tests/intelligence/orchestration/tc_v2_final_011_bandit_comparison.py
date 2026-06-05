r"""
TC_V2_FINAL_011 — Bandit vs CodeTruth V2 Comparison (v2)

Title:
    Where do CodeTruth V2's findings overlap with Bandit's?

Change from v1:
    v1 matched findings by file + line proximity (within 5 lines).
    This produced misleading 1/3 overlap because Bandit and CodeTruth
    locate the same concern at different lines: CodeTruth flags the
    call site inside the function, Bandit flags individual subprocess
    statements and the import line.

    v2 matches findings by file + risk-pattern keyword. A CodeTruth
    subprocess finding in _termui_impl.py matches any Bandit subprocess
    finding in the same file, regardless of line number.

    This produces the more honest answer to the actual question:
    "do the tools agree on risk locations?"

How to use:
    1. Click cloned at C:\scratch\click
    2. CodeTruth report exists at the expected path (see CONFIG)
    3. Install bandit:  pip install bandit
    4. Run:
       python -m tests.intelligence.orchestration.tc_v2_final_011_bandit_comparison
"""

import json
import subprocess
import sys
from pathlib import Path


# =========================================================
# CONFIGURATION
# =========================================================

CLICK_SOURCE = Path(r"C:\scratch\click\src\click")

CODETRUTH_REPORT_PATH = Path(
    r"tests/output/v2/click_governance_reports/tc_v2_final_004_click_report.json"
)
CODETRUTH_REPORT_FALLBACK = Path(
    r"tests/output/v2/click_governance_reports/tc_v2_final_003_report.json"
)

OUTPUT_DIR = Path(r"tests/output/v2/bandit_comparison_reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BANDIT_RAW_OUTPUT = OUTPUT_DIR / "bandit_raw_click.json"
COMPARISON_REPORT = OUTPUT_DIR / "tc_v2_final_011_report.json"


# =========================================================
# RISK-PATTERN MAPPING
# =========================================================

# Maps a CodeTruth category to the set of Bandit test_ids that flag
# the same family of risk. This is the heart of the v2 matching logic.
#
# Bandit test ID reference:
#   B102 exec_used
#   B307 eval_used (and similar)
#   B404 import subprocess
#   B603 subprocess without shell=True
#   B606 start_process_with_no_shell
#   B607 start_process_with_partial_path
#   B602 subprocess_popen_with_shell_equals_true
#   B605 start_process_with_a_shell
#
# Bandit does NOT have a default rule for os.remove / os.unlink, which
# is one of CodeTruth's distinct contributions. We map DELETE_OPERATION
# to an empty set, which produces honest "no Bandit overlap" results
# for that category.
CATEGORY_TO_BANDIT_TESTS = {
    "PROCESS_OPERATION": {
        "B404",  # subprocess import warning
        "B602", "B603", "B605", "B606", "B607",  # subprocess call variants
    },
    "NETWORK_OPERATION": {
        # Bandit does not have direct equivalents for requests.get/post
        # by default. Closest is B113 (request_without_timeout).
        "B113",
    },
    "DELETE_OPERATION": {
        # Bandit has no default rule for os.remove / os.unlink.
        # This is honestly empty.
    },
    "DYNAMIC_EXEC": {
        "B102",  # exec_used
        "B307",  # eval_used
    },
    "GLOBAL_MUTATION": {
        # Bandit has no equivalent.
    },
}


# =========================================================
# BANDIT RUNNER
# =========================================================

def run_bandit(target_path, output_path):
    print(f"Running bandit on {target_path} ...")
    cmd = [
        sys.executable, "-m", "bandit",
        "-r", str(target_path),
        "-f", "json",
        "-o", str(output_path),
        "--quiet",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        print("Bandit failed:")
        print(result.stderr)
        return False
    print(f"Bandit output saved to {output_path}")
    return True


# =========================================================
# LOADERS
# =========================================================

def load_codetruth_report():
    for path in [CODETRUTH_REPORT_PATH, CODETRUTH_REPORT_FALLBACK]:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f), path
    print("ERROR: no CodeTruth report found at expected paths.")
    return None, None


def load_bandit_report(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================================================
# EXTRACTION
# =========================================================

def extract_codetruth_findings(report):
    findings = []
    baseline = report.get("baseline", report)
    per_file = baseline.get("per_file", {})
    for file_path, file_data in per_file.items():
        for f in file_data.get("findings", []):
            findings.append({
                "file_basename": _basename(file_path),
                "file": file_path,
                "function": f.get("function_name"),
                "line": f.get("line_number"),
                "severity": f.get("severity"),
                "category": f.get("category"),
                "evidence": f.get("evidence"),
            })
    return findings


def extract_bandit_findings(report):
    findings = []
    for issue in report.get("results", []):
        findings.append({
            "file_basename": _basename(issue.get("filename", "")),
            "file": issue.get("filename"),
            "line": issue.get("line_number"),
            "severity": issue.get("issue_severity"),
            "confidence": issue.get("issue_confidence"),
            "test_id": issue.get("test_id"),
            "test_name": issue.get("test_name"),
            "issue_text": issue.get("issue_text"),
        })
    return findings


def _basename(path):
    if not path:
        return ""
    return path.replace("\\", "/").split("/")[-1]


# =========================================================
# OVERLAP — v2 (file + risk-pattern match)
# =========================================================

def compute_overlap(codetruth_findings, bandit_findings):
    """For each CodeTruth finding, find Bandit findings in the same file
    that match the same risk pattern (using CATEGORY_TO_BANDIT_TESTS)."""
    overlaps = []
    for ct in codetruth_findings:
        target_test_ids = CATEGORY_TO_BANDIT_TESTS.get(ct["category"], set())
        matches = []
        for ba in bandit_findings:
            if ba["file_basename"] != ct["file_basename"]:
                continue
            if ba["test_id"] in target_test_ids:
                matches.append(ba)
        overlaps.append({
            "codetruth_finding": ct,
            "bandit_matches": matches,
            "match_count": len(matches),
            "overlap": len(matches) > 0,
        })
    return overlaps


# =========================================================
# SEVERITY COMPARISON
# =========================================================

def compare_severities(overlaps):
    pairs = []
    for o in overlaps:
        if not o["overlap"]:
            continue
        ct_sev = o["codetruth_finding"]["severity"]
        order = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, None: 0}
        highest = max(o["bandit_matches"], key=lambda b: order.get(b["severity"], 0))
        pairs.append({
            "file": o["codetruth_finding"]["file_basename"],
            "function": o["codetruth_finding"]["function"],
            "codetruth_severity": ct_sev,
            "bandit_severity_highest": highest["severity"],
            "bandit_match_count": len(o["bandit_matches"]),
        })
    return pairs


def _severities_align(pair):
    ct = pair["codetruth_severity"]
    ba = pair["bandit_severity_highest"]
    if ct == "BLOCK" and ba == "HIGH":
        return True
    if ct == "REVIEW" and ba in ("MEDIUM", "HIGH"):
        return True
    return False


# =========================================================
# UNIQUE-TO-BANDIT
# =========================================================

def collect_bandit_unique(overlaps, bandit_findings):
    """Bandit findings that did not match any CodeTruth finding's
    file + category pairing."""
    matched_keys = set()
    for o in overlaps:
        for m in o["bandit_matches"]:
            matched_keys.add((m["file"], m["line"], m["test_id"]))
    return [
        b for b in bandit_findings
        if (b["file"], b["line"], b["test_id"]) not in matched_keys
    ]


# =========================================================
# MAIN
# =========================================================

def main():
    print("=" * 70)
    print("TC_V2_FINAL_011 — Bandit vs CodeTruth V2 Comparison (v2)")
    print("=" * 70)
    print("Matching method: file basename + risk-pattern keyword "
          "(test_id family)")
    print()

    if not CLICK_SOURCE.exists():
        print(f"Click source not found at {CLICK_SOURCE}")
        return
    if not run_bandit(CLICK_SOURCE, BANDIT_RAW_OUTPUT):
        return

    print("\nLoading reports...")
    ct_report, ct_path = load_codetruth_report()
    if ct_report is None:
        return
    print(f"  CodeTruth report:  {ct_path}")
    ba_report = load_bandit_report(BANDIT_RAW_OUTPUT)

    ct_findings = extract_codetruth_findings(ct_report)
    ba_findings = extract_bandit_findings(ba_report)

    print(f"  CodeTruth V2 findings: {len(ct_findings)}")
    print(f"  Bandit findings:       {len(ba_findings)}")

    # ---- Overlap ----
    print("\n[Option A — Location Overlap (file + risk-pattern match)]")
    overlaps = compute_overlap(ct_findings, ba_findings)
    overlapping = sum(1 for o in overlaps if o["overlap"])
    print(f"  CodeTruth findings whose risk-pattern is also flagged "
          f"by Bandit in the same file: {overlapping}/{len(ct_findings)}")
    print()
    for i, o in enumerate(overlaps, 1):
        ct = o["codetruth_finding"]
        mark = "MATCH" if o["overlap"] else "UNIQUE-TO-CODETRUTH"
        print(f"  [{i}] [{mark}] {ct['file_basename']}::{ct['function']} "
              f"line {ct['line']}")
        print(f"      CodeTruth: {ct['category']} ({ct['severity']}) "
              f"evidence={ct['evidence']!r}")
        if o["overlap"]:
            print(f"      Bandit matches in same file ({o['match_count']}):")
            for m in o["bandit_matches"][:5]:
                print(f"        line {m['line']} {m['test_id']} "
                      f"({m['severity']}/{m['confidence']}): {m['test_name']}")
            if len(o["bandit_matches"]) > 5:
                print(f"        ... and {len(o['bandit_matches']) - 5} more")
        else:
            print(f"      No Bandit finding in same file matches the "
                  f"risk category. (Bandit has no default rule for "
                  f"{ct['category']}.)" if ct["category"] in
                  ("DELETE_OPERATION", "GLOBAL_MUTATION")
                  else f"      No same-category Bandit finding in this file.")

    # ---- Severity ----
    print("\n[Option C — Severity Comparison (where overlap exists)]")
    sev_pairs = compare_severities(overlaps)
    for p in sev_pairs:
        agree = "align" if _severities_align(p) else "differ"
        print(f"  {p['file']}::{p['function']} | "
              f"CodeTruth={p['codetruth_severity']}, "
              f"Bandit highest={p['bandit_severity_highest']} ({agree})")

    # ---- Bandit-unique ----
    bandit_unique = collect_bandit_unique(overlaps, ba_findings)
    print(f"\n[Bandit findings NOT in CodeTruth's risk-pattern overlap]")
    print(f"  Count: {len(bandit_unique)}")

    # Group by test_id for readable summary
    by_test = {}
    for b in bandit_unique:
        by_test.setdefault(b["test_id"], []).append(b)
    print("  Breakdown by Bandit test_id:")
    for tid, items in sorted(by_test.items()):
        sample_name = items[0]["test_name"]
        print(f"    {tid} ({sample_name}): {len(items)} findings")

    # ---- Save ----
    final_report = {
        "test_case": "TC_V2_FINAL_011_BANDIT_COMPARISON_V2",
        "target": str(CLICK_SOURCE),
        "match_method": "file basename + risk-pattern test_id family",
        "totals": {
            "codetruth_findings": len(ct_findings),
            "bandit_findings": len(ba_findings),
            "codetruth_findings_with_bandit_overlap": overlapping,
            "bandit_findings_outside_codetruth_categories": len(bandit_unique),
        },
        "category_to_bandit_tests_map": {
            k: sorted(v) for k, v in CATEGORY_TO_BANDIT_TESTS.items()
        },
        "overlap_detail": [
            {
                "codetruth_finding": o["codetruth_finding"],
                "bandit_match_count": o["match_count"],
                "bandit_matches": o["bandit_matches"],
                "overlap": o["overlap"],
            }
            for o in overlaps
        ],
        "severity_pairs": sev_pairs,
        "bandit_unique_by_test_id": {
            tid: [
                {
                    "file": b["file"],
                    "line": b["line"],
                    "severity": b["severity"],
                    "confidence": b["confidence"],
                    "issue_text": b["issue_text"],
                }
                for b in items
            ]
            for tid, items in by_test.items()
        },
    }
    with open(COMPARISON_REPORT, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=4)
    print(f"\n[Report Saved] {COMPARISON_REPORT}")


if __name__ == "__main__":
    main()
