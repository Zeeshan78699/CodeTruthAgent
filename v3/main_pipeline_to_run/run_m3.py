"""
run_m3.py
CodeTruth Agent V3 — Module 3 standalone runner (repo root). Mirrors run_m1.py /
run_m2.py.

Usage:
    python run_m3.py "C:\\repos\\v3\\fastapi"
    python run_m3.py "C:\\repos\\v3\\fastapi" --json
    python run_m3.py "C:\\repos\\v3\\fastapi" --json --save

Exit code: 0 always (Module 3 is a reasoning/reporting layer; it makes no
SAFE/REVIEW/BLOCK governance decision - that is Module 2's gate). Kept explicit
so callers don't infer a gate that isn't there.
"""

import sys
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Location-robust import bootstrap — finds the folder that CONTAINS the `v3`
# package by walking upward, so this runner works from ANY location (e.g. a
# main_pipeline_to_run/ subfolder or a future final-files layout) without the
# `from v3....` imports breaking. Honours a CODETRUTH_ROOT env override; falls
# back to the original assumption if no marker is found.
# ---------------------------------------------------------------------------
import os
from pathlib import Path


def _find_codetruth_root(start: Path) -> Path:
    env = os.environ.get("CODETRUTH_ROOT")
    if env and (Path(env) / "v3" / "repository_cognition").is_dir():
        return Path(env)
    for parent in [start, *start.parents]:
        if (parent / "v3" / "repository_cognition").is_dir():
            return parent
    return start.parent


CODETRUTH_ROOT = _find_codetruth_root(Path(__file__).resolve().parent)
sys.path.insert(0, str(CODETRUTH_ROOT))          # enables `import v3.<pkg>`
sys.path.insert(0, str(CODETRUTH_ROOT / "v3"))   # enables bare v3-relative imports
V3_ROOT = CODETRUTH_ROOT / "v3"                   # backward-compatible alias

from v3.repository_reasoning.module3_pipeline import run_module3


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if not args:
        print("usage: python run_m3.py <repo_root> [--json] [--save]")
        print("       python run_m3.py <repo_root> --query <kind> <target> [<target2>]")
        print("       <kind>: who-calls | paths-to | impact | depends-on-class | dead-code | paths-between")
        return 2
    repo_root = args[0]

    # ---- query mode: answer an engineering question about the call graph ----
    if "--query" in flags and len(args) >= 2:
        from v3.repository_reasoning import reasoning_queries as RQ
        kind = args[1]
        target = args[2] if len(args) >= 3 else None
        target2 = args[3] if len(args) >= 4 else None

        # --lang <language> uses the language-agnostic surface over any
        # standard-shape adapter (java/javascript/c_cpp/python). Default: the
        # full Python engine (also gives 3A type facts).
        lang = None
        for a in argv:
            if a.startswith("--lang="):
                lang = a.split("=", 1)[1]
        if "--lang" in flags:
            i = argv.index("--lang")
            if i + 1 < len(argv):
                lang = argv[i + 1]

        if lang and lang != "python":
            qs = RQ.query_repo(repo_root, lang)
            fwd, rev = qs.fwd, qs.rev
        else:
            from v3.repository_reasoning.reasoning_engine import ReasoningEngine
            report = ReasoningEngine(repo_root).resolve()
            fwd = report["call_index"]
            rev = RQ.build_reverse_index(fwd)

        if kind == "who-calls":
            ans = RQ.who_calls(target, rev)
        elif kind == "paths-to":
            ans = RQ.paths_to(target, rev)
        elif kind == "impact":
            ans = RQ.impact_of(target, rev)
        elif kind == "depends-on-class":
            ans = RQ.depends_on_class(target, fwd, rev)
        elif kind == "dead-code":
            ans = RQ.dead_code(fwd, rev)
        elif kind == "paths-between":
            ans = RQ.paths_between(target, target2, fwd)
        else:
            print(f"unknown query kind: {kind}")
            return 2

        print(json.dumps(ans, indent=2, default=str))
        return 0

    report = run_module3(repo_root)
    # call_index is large and not part of the published report
    report.pop("call_index", None)

    if "--json" in flags:
        text = json.dumps(report, indent=2, default=str)
        print(text)
        if "--save" in flags:
            out = "module3_report.json"
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"\nsaved -> {out}")
    else:
        a, b = report["phase_3a"], report["phase_3b"]
        print("=== CodeTruth V3 — Module 3 (Repository Reasoning Engine) ===")
        print(f"repo: {repo_root}")
        print(f"[3A] attribute_calls resolved : {a['attr_calls_total']} "
              f"/ {a['baseline_attr_calls']} baseline ({a['pct_of_baseline']}%)")
        print(f"[3A] re-export symbols grounded: {a['reexport_symbols_grounded']}")
        print(f"[3A] registry UNCERTAIN edges  : {a['registry_uncertain_edges']}")
        print(f"[3B] chainable internal edges  : {b['internal_edges_chainable']}")
        print(f"[3B] connected callers         : {b['callers_with_internal_edges']}")
        print(f"labels: {report['by_label']}")
        print(f"truth boundary: {report['truth_boundary']['numeric_confidence_scores']} "
              f"confidence scores, {report['truth_boundary']['guesses']} guesses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))