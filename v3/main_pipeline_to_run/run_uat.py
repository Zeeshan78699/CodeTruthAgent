"""
run_uat.py - CodeTruth UAT/SIT launcher (single canonical entry point).

Purpose (and ONLY this): drive UAT/SIT execution from ONE path. It
  1. pins a single canonical project root (CODETRUTH_ROOT),
  2. invokes the VALIDATED platform pipeline (run_codetruth.run_platform) -
     it does NOT re-implement any pipeline, reasoning, or scoring of code,
  3. scores each test against PRE-REGISTERED pass criteria (fixed in TESTS[]
     below, before any run - no post-hoc goalpost moves), and
  4. writes a per-test acceptance record (framework format) + raw JSON evidence.

The pipeline proves; this harness records. It adds no analysis of its own.

Phase coverage today: SMOKE-001 - a single end-to-end plumbing + integrity check
that validates the single-path model before the flagship phases are scaled.
Phase 5 flagship tests slot into TESTS[] using the same TestSpec shape (see the
comment block above TESTS).

USAGE:
    python run_uat.py "C:\\repos\\v3\\flask"
    python run_uat.py "C:\\repos\\v3\\flask" --force
    python run_uat.py "C:\\repos\\v3\\flask" --out uat_evidence
    python run_uat.py --list          # show configured tests, run nothing

This script must live beside the other runners (run_codetruth.py, run_m*.py) -
that co-location is the single-path model.
"""
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime as dt, UTC

# ---------------------------------------------------------------------------
# Location-robust import bootstrap - finds the folder that CONTAINS the `v3`
# package by walking upward, then PINS it as CODETRUTH_ROOT so every downstream
# runner inherits one canonical root. Honours a valid CODETRUTH_ROOT override;
# corrects an invalid one to the resolved root; falls back if no marker found.
# ---------------------------------------------------------------------------
def _find_codetruth_root(start: Path) -> Path:
    env = os.environ.get("CODETRUTH_ROOT")
    if env and (Path(env) / "v3" / "repository_cognition").is_dir():
        return Path(env)
    for parent in [start, *start.parents]:
        if (parent / "v3" / "repository_cognition").is_dir():
            return parent
    return start.parent


_THIS_DIR = Path(__file__).resolve().parent
CODETRUTH_ROOT = _find_codetruth_root(_THIS_DIR)
os.environ["CODETRUTH_ROOT"] = str(CODETRUTH_ROOT)   # pin ONE root for children
sys.path.insert(0, str(CODETRUTH_ROOT))              # enables `import v3.<pkg>`
sys.path.insert(0, str(CODETRUTH_ROOT / "v3"))       # bare v3-relative imports
sys.path.insert(0, str(_THIS_DIR))                   # sibling runner imports

# Single source of truth for the pipeline. Imported AFTER the root is pinned so
# run_codetruth's own bootstrap agrees with ours. Importing it does not run the
# pipeline (v3 imports are deferred inside its functions).
import run_codetruth


# ===========================================================================
# PRE-REGISTERED CHECKS (defined before any run)
# Each check: (name, expected_description, evaluator)
#   evaluator(result_dict) -> (passed: bool, observed: str)
# ===========================================================================
def _c_status(r):
    v = r.get("status")
    return v == "COMPLETE", f"status={v}"


def _c_gate(r):
    v = r.get("gate")
    return v in ("APPROVED", "REVIEW_REQUIRED"), f"gate={v}"


def _c_m1_present(r):
    m1 = r.get("module1", {}) or {}
    at, fw = m1.get("application_type"), m1.get("framework")
    return (bool(at) and bool(fw)), f"application_type={at}, framework={fw}, arch={m1.get('architecture')}"


def _c_m2_scanned(r):
    m2 = r.get("module2", {}) or {}
    fs = m2.get("files_scanned", 0)
    return (isinstance(fs, int) and fs > 0), \
        f"files_scanned={fs}, functions={m2.get('functions')}, edges={m2.get('call_graph_edges')}"


def _c_m3_integrity(r):
    """Core CodeTruth guarantee: zero guesses. For non-Python (reasoning is a
    documented Python-only boundary) the smoke test does not fail - it records
    the honest note."""
    m3 = r.get("module3", {}) or {}
    if "phase_3a" not in m3:
        return True, f"module3 (honest boundary): {m3.get('note', 'python reasoning not present')}"
    g = (m3.get("truth_boundary", {}) or {}).get("guesses", None)
    return (g == 0), f"guesses={g}"


SMOKE_CHECKS = [
    ("pipeline_completed", "status == COMPLETE", _c_status),
    ("gate_not_blocking", "gate in {APPROVED, REVIEW_REQUIRED}", _c_gate),
    ("m1_produced_identity", "module1 has non-empty application_type and framework", _c_m1_present),
    ("m2_scanned_structure", "module2.files_scanned > 0", _c_m2_scanned),
    ("m3_zero_guesses", "module3.truth_boundary.guesses == 0 (Python); honest note otherwise", _c_m3_integrity),
]


# ===========================================================================
# TEST REGISTRY  (pre-registered - fix specs here BEFORE running)
# To add Phase 5 flagship tests, append TestSpec entries with their own checks,
# e.g. a method-change-impact spec whose checks assert the impact report shape
# and 0 guesses. The runner, records, and evidence capture are unchanged.
# ===========================================================================
class TestSpec:
    def __init__(self, id, objective, requirement, maturity, checks,
                 repo=None, force=False):
        self.id = id
        self.objective = objective
        self.requirement = requirement
        self.maturity = maturity
        self.checks = checks
        self.repo = repo          # None => supplied on the command line
        self.force = force


TESTS = [
    TestSpec(
        id="SMOKE-001",
        objective="Full platform runs M1 -> gate -> M2 -> M3 as one governed "
                  "pass from the single canonical path, producing a structured "
                  "report with zero fabrications.",
        requirement="Phase 1 - Platform Integration (one-scan governed pipeline).",
        maturity="Impl - Pending UAT",
        checks=SMOKE_CHECKS,
        repo=None,
        force=False,
    ),
]


# ===========================================================================
# ACCEPTANCE RECORD (framework format)
# ===========================================================================
def build_record(spec, repo, started, finished, rows, status, result):
    dur = (finished - started).total_seconds()
    passed_n = sum(1 for _, _, _, ok in rows)  # placeholder, recomputed below
    passed_n = sum(1 for *_, ok in rows if ok)
    failed = [name for name, _, _, ok in rows if not ok]
    sev = "N/A" if status == "PASS" else "HIGH"
    root_cause = "-" if status == "PASS" else \
        f"Failed checks: {', '.join(failed)}. See result.json for pipeline output."
    resolution = "-" if status == "PASS" else "Investigate pipeline output; re-run after fix."
    lines = []
    lines.append(f"# UAT Acceptance Record - {spec.id}")
    lines.append("")
    lines.append(f"**Status:** {status}  ")
    lines.append(f"**Pre-registered:** yes (criteria fixed in run_uat.py TESTS[] before the run)  ")
    lines.append(f"**Maturity status:** {spec.maturity}")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Test ID | {spec.id} |")
    lines.append(f"| Objective | {spec.objective} |")
    lines.append(f"| Requirement | {spec.requirement} |")
    lines.append(f"| Repository | {repo} |")
    lines.append(f"| Canonical root | {os.environ.get('CODETRUTH_ROOT')} |")
    lines.append(f"| Started (UTC) | {started.isoformat()} |")
    lines.append(f"| Finished (UTC) | {finished.isoformat()} |")
    lines.append(f"| Duration (s) | {dur:.2f} |")
    lines.append(f"| Checks passed | {passed_n}/{len(rows)} |")
    lines.append("")
    lines.append("## Preconditions")
    lines.append("- CODETRUTH_ROOT resolves to a folder containing the `v3` package.")
    lines.append("- Target repository exists and is readable.")
    lines.append("")
    lines.append("## Steps")
    lines.append("1. Pin CODETRUTH_ROOT and load the validated platform pipeline.")
    lines.append("2. Run run_codetruth.run_platform(repo) - one governed M1->M2->M3 pass.")
    lines.append("3. Score the returned report against the pre-registered checks.")
    lines.append("4. Persist raw output (result.json) and this record.")
    lines.append("")
    lines.append("## Expected vs Actual")
    lines.append("| Check | Expected | Observed | Result |")
    lines.append("|---|---|---|---|")
    for name, expected, observed, ok in rows:
        lines.append(f"| {name} | {expected} | {observed} | {'PASS' if ok else 'FAIL'} |")
    lines.append("")
    lines.append("## Evidence")
    lines.append(f"- `result.json` - raw platform output for {repo}")
    lines.append(f"- this record (`record.md`)")
    lines.append("")
    lines.append("## Disposition")
    lines.append(f"- **Status:** {status}")
    lines.append(f"- **Severity:** {sev}")
    lines.append(f"- **Root cause:** {root_cause}")
    lines.append(f"- **Resolution:** {resolution}")
    lines.append(f"- **Regression required:** {'no' if status == 'PASS' else 'yes'}")
    lines.append("")
    return "\n".join(lines)


# ===========================================================================
# RUNNER
# ===========================================================================
def run_test(spec, repo, force, out_dir):
    started = dt.now(UTC)
    try:
        result = run_codetruth.run_platform(repo, force=force or spec.force)
    except Exception as e:
        result = {"status": "HARNESS_ERROR",
                  "reason": f"{type(e).__name__}: {e}",
                  "repo": repo}
    finished = dt.now(UTC)

    rows = []
    all_pass = True
    for name, expected, fn in spec.checks:
        try:
            ok, observed = fn(result)
        except Exception as e:
            ok, observed = False, f"check error: {type(e).__name__}: {e}"
        all_pass = all_pass and ok
        rows.append((name, expected, observed, ok))
    status = "PASS" if all_pass else "FAIL"

    tdir = out_dir / spec.id
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "result.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8")
    (tdir / "record.md").write_text(
        build_record(spec, repo, started, finished, rows, status, result),
        encoding="utf-8")

    return status, rows, tdir


def print_list():
    print("Configured UAT/SIT tests:")
    for t in TESTS:
        print(f"  {t.id:12} [{t.maturity}]  {t.requirement}")
        print(f"               checks: {', '.join(n for n, _, _ in t.checks)}")


def main(argv):
    ap = argparse.ArgumentParser(description="CodeTruth UAT/SIT launcher")
    ap.add_argument("repo", nargs="?", help="target repository (for tests with repo=None)")
    ap.add_argument("--force", action="store_true", help="proceed past REVIEW_REQUIRED")
    ap.add_argument("--out", default="uat_evidence", help="evidence output directory")
    ap.add_argument("--list", action="store_true", help="list configured tests and exit")
    args = ap.parse_args(argv[1:])

    if args.list:
        print_list()
        return 0

    print("=" * 68)
    print("CodeTruth UAT/SIT launcher")
    print("=" * 68)
    print(f"canonical root : {os.environ.get('CODETRUTH_ROOT')}")

    run_stamp = dt.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out) / run_stamp
    print(f"evidence dir   : {out_dir}")
    print("-" * 68)

    overall_ok = True
    for spec in TESTS:
        repo = spec.repo or args.repo
        if repo is None:
            print(f"[{spec.id}] SKIPPED - no repository provided "
                  f"(pass one on the command line)")
            overall_ok = False
            continue
        status, rows, tdir = run_test(spec, repo, args.force, out_dir)
        overall_ok = overall_ok and (status == "PASS")
        mark = "PASS" if status == "PASS" else "FAIL"
        print(f"[{spec.id}] {mark}  ({sum(1 for *_, ok in rows if ok)}/{len(rows)} checks)  repo={repo}")
        for name, _, observed, ok in rows:
            print(f"    {'ok ' if ok else 'XX '} {name}: {observed}")
        print(f"    evidence -> {tdir}")

    print("-" * 68)
    print("UAT RESULT: " + ("ALL PASS" if overall_ok else "FAIL / INCOMPLETE"))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
