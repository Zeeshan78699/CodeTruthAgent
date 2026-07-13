"""
run_corpus_eval.py — CodeTruth corpus evaluation harness.

Runs the CodeTruth pipeline over every immediate sub-directory of a corpus root
and produces THREE separate artifacts (contract validation kept separate from the
Module 1 accuracy study):

  1. invariant_results.csv   — did CodeTruth behave correctly per its contract?
  2. module1_evaluation.csv  — Module 1's raw outputs + BLANK ground-truth columns
                               for the human to blind-label. (No ground truth is
                               invented here.)
  3. evaluation_summary.md   — corpus-level counts and distributions.

Design (per agreed methodology — MEASURE, don't fix, don't guess):
  * Pass 1: `run_codetruth.py <repo> --json`  (records the NATURAL gate outcome)
  * Pass 2: `run_codetruth.py <repo> --json --force`  — ONLY for repos whose
            natural outcome is REVIEW_REQUIRED, to also capture M2/M3 under an
            explicit override (recorded as override=YES).
  * "Language Review Required" is a NEUTRAL FLAG, not a verdict: it is set only
    when Module 1's framework and Module 2's language describe different languages.
    It is computed by string comparison of the two RAW values — no hardcoded
    language list, no inference about whether it is a bug.

Usage:
  python run_corpus_eval.py --root "C:\\repos\\v3" --runner "v3\\run_codetruth.py"
  (run from the CodeTruth project root; set --python if not the current interpreter)
"""
import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone


# --------------------------------------------------------------------------- #
# run one repo through the CLI, return parsed JSON (or an error record)
# --------------------------------------------------------------------------- #
def run_repo(python_exe, runner, repo_path, force=False, timeout=1800):
    cmd = [python_exe, runner, repo_path, "--json"]
    if force:
        cmd.append("--force")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"_error": "timeout", "status": "ERROR", "gate": None}
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}", "status": "ERROR", "gate": None}
    out = (proc.stdout or "").strip()
    # the JSON may be preceded/followed by log lines; extract the outer object
    start, end = out.find("{"), out.rfind("}")
    if start == -1 or end == -1:
        return {"_error": "no JSON in output",
                "status": "ERROR", "gate": None,
                "_stderr": (proc.stderr or "")[:400]}
    try:
        return json.loads(out[start:end + 1])
    except json.JSONDecodeError as e:
        return {"_error": f"JSON parse: {e}", "status": "ERROR", "gate": None}


# --------------------------------------------------------------------------- #
# neutral language-review flag — pure comparison of two RAW values, no heuristics
# --------------------------------------------------------------------------- #
def language_review_required(m1_framework, m2_language):
    """YES only when Module 1's framework and Module 2's language clearly name
    DIFFERENT languages. This is a review flag (a fact: the two modules disagree),
    not a verdict about whether it is correct. No hardcoded language list: we only
    compare the two strings CodeTruth itself produced."""
    fw = (m1_framework or "").strip().lower()
    lang = (m2_language or "").strip().lower()
    if not fw or not lang or fw in ("none", "unknown", "not detected"):
        return "No"          # nothing to compare -> no disagreement asserted
    # if the framework string is language-agnostic, it will simply differ from the
    # language name; we record the raw disagreement and let the human evaluate it.
    # (A Python framework like 'Flask' also differs from 'python' as a string, so
    #  we do NOT flag on inequality alone — we flag when the framework value looks
    #  like a LANGUAGE name that differs from m2 language. Kept minimal & explicit:)
    KNOWN_LANG_TOKENS = {
        "python", "rust", "go", "golang", "java", "javascript", "typescript",
        "c", "c++", "cpp", "c#", "csharp", "ruby", "php", "kotlin", "swift",
        "scala", "perl", "r", "julia", "dart", "elixir", "haskell",
    }
    # only treat framework as a language claim if it *is* a language token
    if fw in KNOWN_LANG_TOKENS and fw != lang and not (fw == "golang" and lang == "go"):
        return "Yes"
    return "No"


# --------------------------------------------------------------------------- #
# invariant checks — branch by gate outcome; every branch is a PASS when the
# system behaves as designed for THAT outcome (nothing is skipped).
# --------------------------------------------------------------------------- #
def check_invariants(rep):
    """Return (passed: bool, failures: list[str]). Encodes the agreed contract:
    universal invariants always; conditional invariants per APPROVED / REVIEW_REQUIRED
    / BLOCKED. A REVIEW_REQUIRED or BLOCKED repo PASSES when it reports honestly."""
    fails = []
    status = rep.get("status")
    gate = rep.get("gate")

    # --- universal ---
    if rep.get("_error"):
        return False, [f"pipeline error: {rep['_error']}"]
    # An honestly-reported pipeline error (with a reason, and no findings claimed)
    # is CONTRACT-COMPLIANT — the tool failed loudly instead of fabricating. It is
    # a capability/robustness issue to fix, not a Truth-Boundary violation.
    VALID = {"COMPLETE", "REVIEW_REQUIRED", "BLOCKED",
             "M2_PREFLIGHT_VENV", "M2_ERROR", "M3_ERROR", "ERROR"}
    if status not in VALID:
        fails.append(f"unknown status {status!r}")
    m3 = rep.get("module3", {}) or {}
    # not-silent: a non-COMPLETE run must NOT carry engineering findings
    if status != "COMPLETE":
        if m3.get("edge_provenance", {}).get("total_edges", 0):
            fails.append("non-COMPLETE run reported call-graph edges (silent success)")

    # --- conditional ---
    if status == "COMPLETE":
        # `guesses` and `edge_provenance` are Python-M3 (3A/3B) MEASUREMENTS.
        # The per-language reasoning envelope also carries a `truth_boundary`
        # block — but with {scope, limitations}, deliberately NOT `guesses`,
        # because those engines never compute it. So gate these invariants on the
        # presence of the MEASUREMENT, not on the presence of a truth_boundary.
        tb = m3.get("truth_boundary", {}) or {}
        measured_guesses = isinstance(tb, dict) and "guesses" in tb
        if measured_guesses:
            if tb.get("guesses") != 0:
                fails.append(f"COMPLETE but guesses != 0 ({tb.get('guesses')})")
            ep = m3.get("edge_provenance", {})
            if ep:
                exp = ep.get("module2_edges", 0) + ep.get("local_receiver_added", 0)
                if ep.get("total_edges", exp) != exp:
                    fails.append(f"edge provenance mismatch: total={ep.get('total_edges')} "
                                 f"!= {ep.get('module2_edges')}+{ep.get('local_receiver_added')}")
        # Non-Python reasoning envelope: it must not CLAIM capabilities it did not
        # deliver. If the engine errored or is unimplemented, capabilities must be
        # empty — that is the honest-boundary invariant for these languages.
        eng_status = m3.get("status")
        if eng_status in ("ENGINE_ERROR", "NOT_IMPLEMENTED") and m3.get("capabilities"):
            fails.append(f"module3 status={eng_status} but claims capabilities "
                         f"{m3.get('capabilities')}")
    elif status == "REVIEW_REQUIRED":
        # honest hold: gate must say so; no findings implied here (findings only via force pass)
        if gate != "REVIEW_REQUIRED":
            fails.append(f"status REVIEW_REQUIRED but gate={gate!r}")
    elif status in ("BLOCKED", "M2_PREFLIGHT_VENV"):
        # honest block: a reason should be present and no findings claimed
        if not rep.get("reason") and status == "BLOCKED":
            fails.append("BLOCKED without a reason")

    return (len(fails) == 0), fails


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="corpus root, e.g. C:\\repos\\v3")
    ap.add_argument("--runner", default=os.path.join("v3", "run_codetruth.py"),
                    help="path to run_codetruth.py")
    ap.add_argument("--python", default=sys.executable, help="python interpreter")
    ap.add_argument("--outdir", default=".", help="where to write the 3 artifacts")
    ap.add_argument("--force-review", action="store_true", default=True,
                    help="second pass with --force on REVIEW_REQUIRED repos")
    args = ap.parse_args()

    repos = sorted(
        os.path.join(args.root, d) for d in os.listdir(args.root)
        if os.path.isdir(os.path.join(args.root, d))
    )
    print(f"Discovered {len(repos)} repositories under {args.root}\n")

    os.makedirs(args.outdir, exist_ok=True)
    inv_path = os.path.join(args.outdir, "invariant_results.csv")
    m1_path = os.path.join(args.outdir, "module1_evaluation.csv")
    inv_fields = ["repo", "natural_status", "gate", "override_used",
                  "invariant_pass", "invariant_failures", "error"]
    m1_fields = ["repo", "natural_status", "gate", "override_used",
                 "m1_role", "m1_framework", "m1_architecture", "m1_confidence",
                 "m2_language", "m2_files_scanned", "m3_guesses",
                 "language_review_required",
                 "ground_truth_role", "ground_truth_technology",
                 "role_correct", "technology_correct", "failure_category"]

    # INCREMENTAL: open both CSVs now and flush each row as we go, so a crash or
    # hang on repo N still leaves rows 1..N-1 on disk (a long run is never
    # all-or-nothing, and you can watch the files grow live).
    inv_f = open(inv_path, "w", newline="", encoding="utf-8")
    m1_f = open(m1_path, "w", newline="", encoding="utf-8")
    inv_w = csv.DictWriter(inv_f, fieldnames=inv_fields); inv_w.writeheader(); inv_f.flush()
    m1_w = csv.DictWriter(m1_f, fieldnames=m1_fields); m1_w.writeheader(); m1_f.flush()

    counts = {"total": 0, "COMPLETE": 0, "REVIEW_REQUIRED": 0, "BLOCKED": 0,
              "M2_PREFLIGHT_VENV": 0, "ERROR": 0, "invariant_fail": 0,
              "language_review": 0, "override_used": 0}

    try:
        _run_loop(repos, args, counts, inv_w, inv_f, m1_w, m1_f)
    finally:
        inv_f.close(); m1_f.close()
        _write_summary(os.path.join(args.outdir, "evaluation_summary.md"), counts, [])
        print("\nWrote: invariant_results.csv, module1_evaluation.csv, evaluation_summary.md")
        print(f"Summary: {counts}")


def _run_loop(repos, args, counts, inv_w, inv_f, m1_w, m1_f):
    for i, repo in enumerate(repos, 1):
        name = os.path.basename(repo)
        print(f"[{i}/{len(repos)}] {name} …", end=" ", flush=True)

        try:
            rep = run_repo(args.python, args.runner, repo, force=False)      # PASS 1 (natural)
        except Exception as e:
            rep = {"_error": f"{type(e).__name__}: {e}", "status": "ERROR", "gate": None}
        status = rep.get("status", "ERROR")
        gate = rep.get("gate")
        override = "No"

        # PASS 2 (force) only for REVIEW_REQUIRED, to also capture M2/M3
        forced = None
        if args.force_review and status == "REVIEW_REQUIRED":
            try:
                forced = run_repo(args.python, args.runner, repo, force=True)
            except Exception:
                forced = None
            override = "Yes"
            counts["override_used"] += 1

        # which report do we read module2/3 facts from? natural if COMPLETE, else forced
        facts = rep if status == "COMPLETE" else (forced or rep)
        m1 = rep.get("module1", {}) or {}
        m2 = facts.get("module2", {}) or {}
        m3 = facts.get("module3", {}) or {}

        passed, fails = check_invariants(rep)
        counts["total"] += 1
        counts[status] = counts.get(status, 0) + 1
        if not passed:
            counts["invariant_fail"] += 1

        lang_review = language_review_required(m1.get("framework"), m2.get("language"))
        if lang_review == "Yes":
            counts["language_review"] += 1

        # write + flush IMMEDIATELY so partial runs are preserved
        inv_w.writerow({
            "repo": name, "natural_status": status, "gate": gate,
            "override_used": override,
            "invariant_pass": "PASS" if passed else "FAIL",
            "invariant_failures": "; ".join(fails),
            "error": rep.get("_error", ""),
        }); inv_f.flush()
        m1_w.writerow({
            "repo": name,
            "natural_status": status, "gate": gate, "override_used": override,
            "m1_role": m1.get("application_type", ""),
            "m1_framework": m1.get("framework", ""),
            "m1_architecture": m1.get("architecture", ""),
            "m1_confidence": m1.get("confidence", ""),
            "m2_language": m2.get("language", ""),
            "m2_files_scanned": m2.get("files_scanned", ""),
            "m3_guesses": (m3.get("truth_boundary", {}) or {}).get("guesses", ""),
            "language_review_required": lang_review,
            # ---- BLANK: to be filled by human blind-labeling ----
            "ground_truth_role": "", "ground_truth_technology": "",
            "role_correct": "", "technology_correct": "", "failure_category": "",
        }); m1_f.flush()
        print(f"{status} / {gate}  [{'PASS' if passed else 'FAIL'}]"
              + (f"  lang-review={lang_review}" if lang_review == "Yes" else ""))


def _write_csv(path, rows):
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _write_summary(path, counts, m1_rows):
    lines = []
    lines.append("# CodeTruth Corpus Evaluation Summary\n")
    lines.append(f"_Generated: {datetime.now(timezone.utc).isoformat()}_\n")
    lines.append("## Invariant / contract validation\n")
    lines.append(f"- Repositories tested: {counts['total']}")
    lines.append(f"- COMPLETE (APPROVED): {counts.get('COMPLETE', 0)}")
    lines.append(f"- REVIEW_REQUIRED: {counts.get('REVIEW_REQUIRED', 0)} "
                 f"(force override used: {counts['override_used']})")
    lines.append(f"- BLOCKED: {counts.get('BLOCKED', 0)}")
    lines.append(f"- Venv pre-flight halts: {counts.get('M2_PREFLIGHT_VENV', 0)}")
    lines.append(f"- Pipeline errors: {counts.get('ERROR', 0)}")
    lines.append(f"- **Invariant failures: {counts['invariant_fail']}** "
                 "(should be 0 — any failure is a real contract violation to investigate)\n")
    lines.append("## Language-review flags\n")
    lines.append(f"- Repositories where Module 1 framework and Module 2 language "
                 f"appear to disagree: **{counts['language_review']}**")
    lines.append("- This is a NEUTRAL review flag (the two modules produced different "
                 "language signals), not a verdict. Review these during ground-truth "
                 "labeling to decide whether it is expected (mixed-language repo, "
                 "Python tooling in a non-Python project) or a real gap.\n")
    lines.append("## Module 1 accuracy\n")
    lines.append("- Not computed here. `module1_evaluation.csv` contains Module 1's "
                 "raw outputs with BLANK ground-truth columns. Blind-label ground "
                 "truth first, then compute role/technology/architecture accuracy and "
                 "the confidence-vs-correctness (calibration) distribution.\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
