"""
run_module_uat.py - CodeTruth module + integration UAT/SIT launcher
(single canonical entry point).

Purpose (and ONLY this): drive UAT/SIT from ONE path. It
  1. pins a single canonical project root (CODETRUTH_ROOT),
  2. invokes VALIDATED entry points - the platform pipeline
     (run_codetruth.run_platform) and the standalone module runners
     (run_m1.run_module1, run_m2.run_module2, v3 ... run_module3) - it
     re-implements NO pipeline, reasoning, or scoring of code,
  3. scores each test against PRE-REGISTERED pass criteria (fixed in TESTS[]
     below, before any run - no post-hoc goalpost moves), and
  4. writes a per-test acceptance record (framework format) + raw JSON evidence.

The runners prove; this harness records. It adds no analysis of its own.

Coverage today (module + integration):
  SMOKE-001  Phase 1  full platform, M1->gate->M2->M3 in one governed pass
  M1-001     Phase 2  Module 1 Repository Cognition (standalone)
  M2-001     Phase 3  Module 2 Structural Intelligence (standalone, Python)
  M3-001     Phase 4  Module 3 Repository Reasoning (standalone)
Phase 5 flagship tests slot into TESTS[] using the same TestSpec shape - each
carries its own runner hook + checks; the scoring and evidence plumbing are
unchanged.

USAGE:
    python run_module_uat.py "C:\\repos\\v3\\flask"
    python run_module_uat.py "C:\\repos\\v3\\flask" --force
    python run_module_uat.py "C:\\repos\\v3\\flask" --out uat_evidence
    python run_module_uat.py --list          # show configured tests, run nothing

This script must live beside the other runners (run_codetruth.py, run_m*.py) -
that co-location is the single-path model.
"""
import sys
import os
import json
import argparse
import hashlib
import platform
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime as dt, UTC

# ---------------------------------------------------------------------------
# DECLARED VERSIONS (human-maintained - EDIT to match the published state).
# These are ASSERTIONS by a human, kept separate in VERSION.json from the
# git-observed anchor, so the pack never claims a version the repo can't back.
# ---------------------------------------------------------------------------
DECLARED_VERSIONS = {
    "codetruth_platform": "v3.0.0",
    "module1": "v3.0.0-module1 (published: GitHub tag / HF / Zenodo)",
    "module2": "v3.0.0-module2 (published: GitHub tag / HF / Zenodo)",
    "module3": "v3.0.0-module3 (frozen; not yet published)",
    "uat_spec_version": "module-uat-1.0.0",
    "benchmark_version": "n/a",
}

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

# Platform pipeline (single source of truth). Import is safe here: run_codetruth
# defers its v3 imports inside functions, so importing it does not run anything.
import run_codetruth


# ===========================================================================
# RUNNER HOOKS  - each returns the runner's OWN result dict (no re-computation).
# Module-runner imports are LAZY (inside the hook) so this launcher stays
# importable even where v3 is absent, and each module is exercised in isolation.
# ===========================================================================
def _runner_platform(repo, force):
    return run_codetruth.run_platform(repo, force=force)


def _runner_m1(repo, force):
    from run_m1 import run_module1
    return run_module1(repo)


def _runner_m2(repo, force):
    from run_m2 import run_module2
    # Standalone M2 defaults to Python (matches run_m2.py default). Multi-language
    # module tests would be separate specs with their own --language.
    return run_module2(repo, "python", False)


def _runner_m3(repo, force):
    from v3.repository_reasoning.module3_pipeline import run_module3
    rep = run_module3(repo)
    if isinstance(rep, dict):
        rep.pop("call_index", None)   # large internal artifact, not scored
    return rep


# ===========================================================================
# PRE-REGISTERED CHECKS (defined before any run)
# Each check: (name, expected_description, evaluator)
#   evaluator(result_dict) -> (passed: bool, observed: str)
# ===========================================================================
# ---- Platform (SMOKE-001) ----
def _c_status_complete(r):
    v = r.get("status")
    return v == "COMPLETE", f"status={v}"


def _c_gate_not_blocking(r):
    v = r.get("gate")
    return v in ("APPROVED", "REVIEW_REQUIRED"), f"gate={v}"


def _c_platform_m1(r):
    m1 = r.get("module1", {}) or {}
    at, fw = m1.get("application_type"), m1.get("framework")
    return (bool(at) and bool(fw)), f"application_type={at}, framework={fw}, arch={m1.get('architecture')}"


def _c_platform_m2(r):
    m2 = r.get("module2", {}) or {}
    fs = m2.get("files_scanned", 0)
    return (isinstance(fs, int) and fs > 0), \
        f"files_scanned={fs}, functions={m2.get('functions')}, edges={m2.get('call_graph_edges')}"


def _c_platform_m3_integrity(r):
    m3 = r.get("module3", {}) or {}
    if "phase_3a" not in m3:
        return True, f"module3 (honest boundary): {m3.get('note', 'python reasoning not present')}"
    g = (m3.get("truth_boundary", {}) or {}).get("guesses", None)
    return (g == 0), f"guesses={g}"


PLATFORM_CHECKS = [
    ("pipeline_completed", "status == COMPLETE", _c_status_complete),
    ("gate_not_blocking", "gate in {APPROVED, REVIEW_REQUIRED}", _c_gate_not_blocking),
    ("m1_produced_identity", "module1 has non-empty application_type and framework", _c_platform_m1),
    ("m2_scanned_structure", "module2.files_scanned > 0", _c_platform_m2),
    ("m3_zero_guesses", "module3.truth_boundary.guesses == 0 (Python); honest note otherwise", _c_platform_m3_integrity),
]

# ---- Module 1 (M1-001) ----
_GATES = ("APPROVED", "REVIEW_REQUIRED", "BLOCKED")


def _c_m1_status(r):
    v = r.get("status")
    return v == "COMPLETE", f"status={v}"


def _c_m1_gate_decided(r):
    v = r.get("gate")
    return v in _GATES, f"gate={v}"


def _c_m1_identity(r):
    at, fw, ar = r.get("application_type"), r.get("framework"), r.get("architecture")
    return (bool(at) and bool(fw) and bool(ar)), f"application_type={at}, framework={fw}, architecture={ar}"


def _c_m1_confidence(r):
    c = r.get("confidence")
    ok = isinstance(c, (int, float)) and 0.0 <= float(c) <= 1.0
    return ok, f"confidence={c}"


M1_CHECKS = [
    ("m1_status_complete", "status == COMPLETE", _c_m1_status),
    ("m1_gate_decided", "gate in {APPROVED, REVIEW_REQUIRED, BLOCKED}", _c_m1_gate_decided),
    ("m1_identity_present", "non-empty application_type, framework, architecture", _c_m1_identity),
    ("m1_confidence_bounded", "confidence is numeric in [0.0, 1.0]", _c_m1_confidence),
]

# ---- Module 2 (M2-001) ----
def _c_m2_status(r):
    v = r.get("status")
    return v == "COMPLETE", f"status={v}"


def _c_m2_gate(r):
    v = r.get("gate")
    return bool(v) and v != "UNKNOWN", f"gate={v}"


def _c_m2_files(r):
    fs = r.get("files_scanned", 0)
    return (isinstance(fs, int) and fs > 0), f"files_scanned={fs}"


M2_CHECKS = [
    ("m2_status_complete", "status == COMPLETE", _c_m2_status),
    ("m2_gate_present", "governance_gate is set (not UNKNOWN)", _c_m2_gate),
    ("m2_files_scanned", "files_scanned > 0", _c_m2_files),
]

# ---- Module 3 (M3-001) ----
def _c_m3_phases(r):
    ok = isinstance(r, dict) and ("phase_3a" in r) and ("phase_3b" in r)
    return ok, f"phase_3a={'y' if 'phase_3a' in (r or {}) else 'n'}, phase_3b={'y' if 'phase_3b' in (r or {}) else 'n'}"


def _c_m3_guesses(r):
    g = (r.get("truth_boundary", {}) or {}).get("guesses", None)
    return (g == 0), f"guesses={g}"


def _c_m3_no_fake_confidence(r):
    n = (r.get("truth_boundary", {}) or {}).get("numeric_confidence_scores", None)
    return (n == 0), f"numeric_confidence_scores={n}"


def _c_m3_3a_produced(r):
    a = r.get("phase_3a", {}) or {}
    ok = "baseline_attr_calls" in a and "attr_calls_total" in a
    return ok, f"attr_calls_total={a.get('attr_calls_total')}/{a.get('baseline_attr_calls')} baseline"


M3_CHECKS = [
    ("m3_phases_present", "report has phase_3a and phase_3b", _c_m3_phases),
    ("m3_zero_guesses", "truth_boundary.guesses == 0", _c_m3_guesses),
    ("m3_no_fabricated_confidence", "truth_boundary.numeric_confidence_scores == 0", _c_m3_no_fake_confidence),
    ("m3_3a_resolution_reported", "phase_3a reports attr_calls_total over baseline", _c_m3_3a_produced),
]


# ===========================================================================
# TEST REGISTRY  (pre-registered - fix specs here BEFORE running)
# ===========================================================================
class TestSpec:
    def __init__(self, id, objective, requirement, maturity, entrypoint,
                 runner, checks, scenario="", expected_result="",
                 repo=None, force=False):
        self.id = id
        self.objective = objective
        self.requirement = requirement
        self.maturity = maturity
        self.entrypoint = entrypoint     # human label of what is exercised
        self.runner = runner             # callable(repo, force) -> result dict
        self.checks = checks
        self.scenario = scenario         # plain-language: what we are testing
        self.expected_result = expected_result  # plain-language pass condition
        self.repo = repo                 # None => supplied on the command line
        self.force = force


TESTS = [
    TestSpec(
        id="SMOKE-001",
        objective="Full platform runs M1 -> gate -> M2 -> M3 as one governed pass "
                  "from the single canonical path, producing a structured report "
                  "with zero fabrications.",
        requirement="Phase 1 - Platform Integration (one-scan governed pipeline).",
        maturity="Impl - Pending UAT",
        entrypoint="run_codetruth.run_platform",
        runner=_runner_platform,
        checks=PLATFORM_CHECKS,
        scenario="GIVEN the full CodeTruth platform and a real repository, WHEN it "
                 "is run in one governed pass (M1 -> gate -> M2 -> M3), THEN the "
                 "pipeline completes end-to-end, the gate is a real decision, "
                 "structure is scanned, and reasoning fabricates nothing.",
        expected_result="status=COMPLETE; gate in {APPROVED, REVIEW_REQUIRED}; M1 "
                        "emits an identity; M2 scans >=1 file; M3 guesses=0.",
    ),
    TestSpec(
        id="M1-001",
        objective="Module 1 alone understands the repository: emits a governance "
                  "decision and a non-empty identity with bounded confidence.",
        requirement="Phase 2 - Module 1 Repository Cognition.",
        maturity="Validated",
        entrypoint="run_m1.run_module1",
        runner=_runner_m1,
        checks=M1_CHECKS,
        scenario="GIVEN only Module 1 and a repository, WHEN cognition runs, THEN "
                 "it produces a governance decision and a non-empty identity "
                 "(application type, framework, architecture) with a bounded "
                 "confidence - with no downstream modules involved.",
        expected_result="status=COMPLETE; gate in {APPROVED, REVIEW_REQUIRED, "
                        "BLOCKED}; identity fields non-empty; confidence in [0,1]. "
                        "(Identity CORRECTNESS is out of scope - Phase 2.)",
    ),
    TestSpec(
        id="M2-001",
        objective="Module 2 alone builds a structural model: scans files and "
                  "returns a governance gate and COMPLETE status (Python).",
        requirement="Phase 3 - Module 2 Structural Intelligence.",
        maturity="Validated",
        entrypoint="run_m2.run_module2 (language=python)",
        runner=_runner_m2,
        checks=M2_CHECKS,
        scenario="GIVEN only Module 2 and a Python repository, WHEN the structural "
                 "scan runs, THEN it parses files and returns a governance gate "
                 "and a COMPLETE status.",
        expected_result="status=COMPLETE; governance_gate set (not UNKNOWN); "
                        "files_scanned>0. (Graph MAGNITUDES are informational - the "
                        "runner return is thin by contract.)",
    ),
    TestSpec(
        id="M3-001",
        objective="Module 3 alone reasons over structure: produces phase 3A/3B "
                  "results with zero guesses and no fabricated confidence.",
        requirement="Phase 4 - Module 3 Repository Reasoning.",
        maturity="Validated",
        entrypoint="v3.repository_reasoning.module3_pipeline.run_module3",
        runner=_runner_m3,
        checks=M3_CHECKS,
        scenario="GIVEN only Module 3 and a repository, WHEN reasoning runs, THEN "
                 "it produces phase 3A and 3B results and holds the Truth Boundary "
                 "- declining what it cannot verify rather than guessing.",
        expected_result="phase_3a and phase_3b present; truth_boundary.guesses=0; "
                        "numeric_confidence_scores=0; 3A reports resolved/baseline. "
                        "(3A COVERAGE %% is informational, not a pass criterion.)",
    ),
]


# ===========================================================================
# ACCEPTANCE RECORD (framework format)
# ===========================================================================
def build_record(spec, repo, started, finished, rows, status):
    dur = (finished - started).total_seconds()
    passed_n = sum(1 for *_, ok in rows if ok)
    failed = [name for name, _, _, ok in rows if not ok]
    sev = "N/A" if status == "PASS" else "HIGH"
    root_cause = "-" if status == "PASS" else \
        f"Failed checks: {', '.join(failed)}. See result.json for runner output."
    resolution = "-" if status == "PASS" else "Investigate runner output; re-run after fix."
    L = []
    L.append(f"# UAT Acceptance Record - {spec.id}")
    L.append("")
    L.append(f"**Status:** {status}  ")
    L.append(f"**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  ")
    L.append(f"**Maturity status:** {spec.maturity}")
    L.append("")
    L.append("| Field | Value |")
    L.append("|---|---|")
    L.append(f"| Test ID | {spec.id} |")
    L.append(f"| Objective | {spec.objective} |")
    L.append(f"| Requirement | {spec.requirement} |")
    L.append(f"| Entry point | {spec.entrypoint} |")
    L.append(f"| Repository | {repo} |")
    L.append(f"| Canonical root | {os.environ.get('CODETRUTH_ROOT')} |")
    L.append(f"| Started (UTC) | {started.isoformat()} |")
    L.append(f"| Finished (UTC) | {finished.isoformat()} |")
    L.append(f"| Duration (s) | {dur:.2f} |")
    L.append(f"| Checks passed | {passed_n}/{len(rows)} |")
    L.append("")
    L.append("## Scenario (what this test verifies)")
    L.append(spec.scenario or "(not specified)")
    L.append("")
    L.append("## Expected result")
    L.append(spec.expected_result or "(not specified)")
    L.append("")
    L.append("## Preconditions")
    L.append("- CODETRUTH_ROOT resolves to a folder containing the `v3` package.")
    L.append("- Target repository exists and is readable.")
    L.append("")
    L.append("## Steps")
    L.append(f"1. Pin CODETRUTH_ROOT and load the entry point ({spec.entrypoint}).")
    L.append("2. Run the entry point on the target repository.")
    L.append("3. Score the returned result against the pre-registered checks.")
    L.append("4. Persist raw output (result.json) and this record.")
    L.append("")
    L.append("## Expected vs Actual")
    L.append("| Check | Expected | Observed | Result |")
    L.append("|---|---|---|---|")
    for name, expected, observed, ok in rows:
        L.append(f"| {name} | {expected} | {observed} | {'PASS' if ok else 'FAIL'} |")
    L.append("")
    L.append("## Evidence")
    L.append(f"- `result.json` - raw runner output for {repo}")
    L.append("- this record (`record.md`)")
    L.append("")
    L.append("## Disposition")
    L.append(f"- **Status:** {status}")
    L.append(f"- **Severity:** {sev}")
    L.append(f"- **Root cause:** {root_cause}")
    L.append(f"- **Resolution:** {resolution}")
    L.append(f"- **Regression required:** {'no' if status == 'PASS' else 'yes'}")
    L.append("")
    return "\n".join(L)


# ===========================================================================
# EVIDENCE PACKAGING  (publishable, reproducible, tamper-evident)
# ===========================================================================
def _git_info(path):
    """Real git provenance or an honest 'unavailable' - never fabricated."""
    p = Path(path)
    if not p.exists():
        return {"status": "unavailable", "reason": "path does not exist"}

    def _run(args):
        try:
            out = subprocess.run(["git", "-C", str(p), *args],
                                 capture_output=True, text=True, timeout=10)
            return out.stdout.strip() if out.returncode == 0 else None
        except Exception:
            return None

    commit = _run(["rev-parse", "HEAD"])
    if not commit:
        return {"status": "unavailable",
                "reason": "not a git repository or git not found"}
    return {
        "status": "ok",
        "commit": commit,
        "describe": _run(["describe", "--tags", "--always", "--dirty"]),
        "branch": _run(["rev-parse", "--abbrev-ref", "HEAD"]),
        "dirty": bool(_run(["status", "--porcelain"])),
    }


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def serialize_spec_snapshot(tests):
    """The frozen, pre-registered criteria - published alongside the results."""
    return {
        "uat_spec_version": DECLARED_VERSIONS["uat_spec_version"],
        "frozen_before_run": True,
        "tests": [
            {
                "id": t.id,
                "objective": t.objective,
                "requirement": t.requirement,
                "maturity": t.maturity,
                "entrypoint": t.entrypoint,
                "scenario": t.scenario,
                "expected_result": t.expected_result,
                "checks": [{"name": n, "expected": e} for n, e, _ in t.checks],
            }
            for t in tests
        ],
    }


def _host_info():
    return {
        "os": os.name,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
    }


def _write_checksums(out_dir):
    """SHA-256 of every evidence file (except the checksum file itself),
    in `sha256sum -c` format so a reviewer can verify integrity."""
    lines = []
    for f in sorted(out_dir.rglob("*")):
        if f.is_file() and f.name != "checksums.sha256":
            rel = f.relative_to(out_dir).as_posix()
            lines.append(f"{_sha256_file(f)}  {rel}")
    (out_dir / "checksums.sha256").write_text("\n".join(lines) + "\n",
                                              encoding="utf-8")
    return len(lines)


def _zip_pack(out_dir, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out_dir.rglob("*")):
            if f.is_file():
                z.write(f, arcname=f.relative_to(out_dir.parent).as_posix())


def _readme(run_stamp, overall, run_results, repos):
    passed = sum(1 for r in run_results if r["status"] == "PASS")
    L = []
    L.append(f"# CodeTruth V3 - UAT/SIT Evidence Pack ({run_stamp})")
    L.append("")
    L.append(f"**Overall:** {overall}  ({passed}/{len(run_results)} tests passed)")
    L.append("")
    L.append("Deterministic, pre-registered UAT/SIT evidence for the CodeTruth "
             "platform (Modules 1-3). Criteria were frozen before the run "
             "(`spec_snapshot.json`); the pipeline is AI-model-free and reports "
             "zero fabrications by construction.")
    L.append("")
    L.append("## Contents")
    L.append("| File | Purpose |")
    L.append("|---|---|")
    L.append("| `manifest.json` | Environment, timestamps, code + analyzed-repo git provenance |")
    L.append("| `VERSION.json` | Declared platform/module versions + observed git anchor |")
    L.append("| `spec_snapshot.json` | Frozen pre-registered UAT criteria (goalposts) |")
    L.append("| `summary.json` | Machine-readable results |")
    L.append("| `SUMMARY.md` | Human-readable results |")
    L.append("| `checksums.sha256` | Integrity hashes for all evidence files |")
    L.append("| `<TEST-ID>/result.json` | Raw runner output per test |")
    L.append("| `<TEST-ID>/record.md` | Per-test acceptance record |")
    L.append("")
    L.append("## Verify integrity")
    L.append("```")
    L.append("sha256sum -c checksums.sha256")
    L.append("```")
    L.append("")
    L.append("## Reproduce")
    L.append("```")
    L.append("python run_module_uat.py <repo_path>")
    L.append("```")
    L.append(f"Repositories analyzed in this run: {', '.join(repos)}")
    L.append("")
    L.append("## Honest bounds")
    L.append("- These records test **integrity and shape** (pipeline completes, "
             "gate decided, zero guesses), not application-type correctness or "
             "resolution coverage - those are tracked separately.")
    L.append("- `git: unavailable` in the manifest means the path was not a git "
             "checkout at run time; it is never a fabricated value.")
    L.append("")
    L.append("*CodeTruth - proves what it can, flags what it can't, never guesses.*")
    return "\n".join(L)


def write_evidence_pack(out_dir, run_stamp, run_results, repos, tests,
                        make_zip=True, make_readme=True):
    """Emit the publishable artifacts into out_dir. Returns (zip_path|None)."""
    overall = "ALL PASS" if all(r["status"] == "PASS" for r in run_results) \
        and run_results else "FAIL / INCOMPLETE"

    # manifest
    manifest = {
        "generated_utc": dt.now(UTC).isoformat(),
        "run_stamp": run_stamp,
        "host": _host_info(),
        "codetruth": {
            "root": str(CODETRUTH_ROOT),
            "git": _git_info(CODETRUTH_ROOT),
        },
        "analyzed_repos": [
            {"path": rp, "git": _git_info(rp)} for rp in repos
        ],
        "tests": [r["id"] for r in run_results],
        "overall": overall,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, default=str), encoding="utf-8")

    # version
    version = {
        "declared": DECLARED_VERSIONS,
        "observed_code_git": _git_info(CODETRUTH_ROOT),
        "note": "declared versions are human-maintained; observed_code_git is "
                "captured automatically and is the objective anchor.",
    }
    (out_dir / "VERSION.json").write_text(
        json.dumps(version, indent=2, default=str), encoding="utf-8")

    # spec snapshot (frozen criteria)
    (out_dir / "spec_snapshot.json").write_text(
        json.dumps(serialize_spec_snapshot(tests), indent=2, default=str),
        encoding="utf-8")

    # summary.json
    summary = {
        "run_stamp": run_stamp,
        "overall": overall,
        "tests_total": len(run_results),
        "tests_passed": sum(1 for r in run_results if r["status"] == "PASS"),
        "tests": [
            {
                "id": r["id"],
                "status": r["status"],
                "requirement": r["requirement"],
                "maturity": r["maturity"],
                "entrypoint": r["entrypoint"],
                "scenario": r.get("scenario", ""),
                "expected_result": r.get("expected_result", ""),
                "repo": r["repo"],
                "checks_passed": sum(1 for c in r["checks"] if c["passed"]),
                "checks_total": len(r["checks"]),
                "checks": r["checks"],
            }
            for r in run_results
        ],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8")

    # SUMMARY.md
    S = [f"# UAT/SIT Summary - {run_stamp}", "",
         f"**Overall:** {overall}", "",
         "| Test | Requirement | Status | Checks |",
         "|---|---|---|---|"]
    for r in run_results:
        cp = sum(1 for c in r["checks"] if c["passed"])
        S.append(f"| {r['id']} | {r['requirement']} | {r['status']} | "
                 f"{cp}/{len(r['checks'])} |")
    (out_dir / "SUMMARY.md").write_text("\n".join(S) + "\n", encoding="utf-8")

    # README (dataset card)
    if make_readme:
        (out_dir / "README.md").write_text(
            _readme(run_stamp, overall, run_results, repos), encoding="utf-8")

    # checksums LAST (covers everything above)
    n = _write_checksums(out_dir)

    zip_path = None
    if make_zip:
        zip_path = out_dir.parent / f"{run_stamp}.zip"
        _zip_pack(out_dir, zip_path)

    return zip_path, overall, n


# ===========================================================================
# RUNNER
# ===========================================================================
def run_test(spec, repo, force, out_dir):
    started = dt.now(UTC)
    if not Path(repo).exists():
        result = {"status": "ERROR", "reason": "path not found", "repo": repo}
    else:
        try:
            result = spec.runner(repo, force or spec.force)
        except Exception as e:
            result = {"status": "HARNESS_ERROR",
                      "reason": f"{type(e).__name__}: {e}", "repo": repo}
    finished = dt.now(UTC)

    # A runner may attach human-readable artifacts (e.g. an 11-section report)
    # under the "_artifacts" key: {filename: text}. These are written into the
    # test's evidence folder and removed before scoring/serialization.
    artifacts = result.pop("_artifacts", {}) if isinstance(result, dict) else {}

    rows = []
    all_pass = True
    for name, expected, fn in spec.checks:
        try:
            ok, observed = fn(result if isinstance(result, dict) else {})
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
        build_record(spec, repo, started, finished, rows, status),
        encoding="utf-8")
    for fname, content in (artifacts or {}).items():
        (tdir / fname).write_text(str(content), encoding="utf-8")
    return status, rows, tdir


def print_list(tests):
    print("Configured UAT/SIT tests:")
    for t in tests:
        print(f"  {t.id:10} [{t.maturity:16}] {t.requirement}")
        print(f"             entry: {t.entrypoint}")
        if t.scenario:
            print(f"             scenario: {t.scenario}")
        print(f"             checks: {', '.join(n for n, _, _ in t.checks)}")


def main(argv, tests=None, title="CodeTruth module + integration UAT/SIT launcher"):
    if tests is None:
        tests = TESTS
    ap = argparse.ArgumentParser(description="CodeTruth UAT/SIT launcher")
    ap.add_argument("repo", nargs="?", help="target repository (for tests with repo=None)")
    ap.add_argument("--force", action="store_true", help="proceed past REVIEW_REQUIRED")
    ap.add_argument("--out", default="uat_evidence", help="evidence output directory")
    ap.add_argument("--list", action="store_true", help="list configured tests and exit")
    ap.add_argument("--only", help="run only the test with this ID")
    ap.add_argument("--no-zip", action="store_true", help="do not create the .zip pack")
    ap.add_argument("--no-readme", action="store_true", help="do not write README.md")
    args = ap.parse_args(argv[1:])

    if args.list:
        print_list(tests)
        return 0

    print("=" * 68)
    print(title)
    print("=" * 68)
    print(f"canonical root : {os.environ.get('CODETRUTH_ROOT')}")

    run_stamp = dt.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = Path(args.out) / run_stamp
    print(f"evidence dir   : {out_dir}")
    print("-" * 68)

    specs = [t for t in tests if (args.only is None or t.id == args.only)]
    if not specs:
        print(f"no test matches --only {args.only}")
        return 2

    overall_ok = True
    summary = []
    run_results = []
    repos_seen = []
    for spec in specs:
        repo = spec.repo or args.repo
        if repo is None:
            print(f"[{spec.id}] SKIPPED - no repository provided")
            overall_ok = False
            summary.append((spec.id, "SKIP"))
            continue
        status, rows, tdir = run_test(spec, repo, args.force, out_dir)
        overall_ok = overall_ok and (status == "PASS")
        summary.append((spec.id, status))
        if repo not in repos_seen:
            repos_seen.append(repo)
        run_results.append({
            "id": spec.id,
            "status": status,
            "requirement": spec.requirement,
            "maturity": spec.maturity,
            "entrypoint": spec.entrypoint,
            "scenario": spec.scenario,
            "expected_result": spec.expected_result,
            "repo": repo,
            "checks": [{"name": n, "expected": e, "observed": o, "passed": ok}
                       for n, e, o, ok in rows],
        })
        print(f"[{spec.id}] {status}  ({sum(1 for *_, ok in rows if ok)}/{len(rows)} checks)  "
              f"repo={repo}")
        if spec.scenario:
            print(f"    scenario : {spec.scenario}")
        if spec.expected_result:
            print(f"    expected : {spec.expected_result}")
        for name, _, observed, ok in rows:
            print(f"    {'ok ' if ok else 'XX '} {name}: {observed}")
        print(f"    evidence -> {tdir}")
        print()

    print("-" * 68)
    for tid, st in summary:
        print(f"  {tid:10} {st}")
    print("-" * 68)

    # ---- publishable evidence pack ----
    zip_path = None
    if run_results:
        zip_path, overall, n_hashed = write_evidence_pack(
            out_dir, run_stamp, run_results, repos_seen, specs,
            make_zip=not args.no_zip, make_readme=not args.no_readme)
        print("EVIDENCE PACK")
        print(f"  folder    : {out_dir}")
        print(f"  files      : manifest.json, VERSION.json, spec_snapshot.json, "
              f"summary.json, SUMMARY.md" + ("" if args.no_readme else ", README.md"))
        print(f"  checksums  : checksums.sha256 ({n_hashed} files hashed)")
        if zip_path:
            print(f"  zip        : {zip_path}")
        print("-" * 68)

    print("UAT RESULT: " + ("ALL PASS" if overall_ok else "FAIL / INCOMPLETE"))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
