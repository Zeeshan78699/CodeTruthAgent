"""
run_traceeval.py — TraceEval evaluation runner for CodeTruth (Java, Option A).

For each instance in TraceEval's Java test split:
  1. read instance README -> source repo + original file path
  2. isolate that ONE source file (TraceEval scores per-file/per-program)
  3. run CodeTruth enriched_report on it
  4. transform edges -> TraceEval name-level ids
  5. score vs the instance's callgraph.json (execution-verified GT)
Micro-average TP/FP/FN across instances -> P/R/F1, with recall as the fair
primary metric (static-vs-dynamic; report precision with the static-finds-more
caveat).

Source resolution: TraceEval README gives `Source: owner/repo` + original file
path. We need that file at the right commit. For a first pass we use whatever
clone is available locally (e.g. C:\\repos\\1brc) and the file path from README;
repos not present are SKIPPED and counted (honest coverage), exactly like the
CrossCodeEval availability approach.
"""

import io
import json
import os
import re
import sys
import tempfile
import shutil
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)

# import the harness (same dir)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import traceeval_harness as H


def parse_readme(readme_path):
    """README -> {source, original_file, edges, functions, ground_truth}."""
    info = {}
    txt = io.open(readme_path, encoding="utf-8").read()
    for line in txt.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip().lower().replace(" ", "_")] = v.strip()
    return info


def find_source_file(info, repo_roots, repos_base=r"C:\repos"):
    """Locate the instance's original source file.

    Resolution order:
      1. explicit REPO_ROOTS mapping (manual override / exceptions)
      2. auto-discover: <repos_base>\<repo_short_name>  (e.g. C:\repos\pki)
    Returns abs path to the file, or None if unresolved / file missing.
    """
    src = info.get("source", "")
    orig = info.get("original_file", "")
    if not orig:
        return None
    repo_name = src.split("/")[-1] if "/" in src else src
    root = repo_roots.get(repo_name) or repo_roots.get(src)
    if not root:
        cand_root = os.path.join(repos_base, repo_name)
        if os.path.isdir(cand_root):
            root = cand_root
    if not root:
        return None
    candidate = os.path.join(root, *orig.split("/"))
    return candidate if os.path.exists(candidate) else None


def run_instance(instance_dir, repo_roots):
    """Score one TraceEval instance. Returns dict with tp/fp/fn or a skip reason."""
    readme = os.path.join(instance_dir, "README.md")
    gt_path = os.path.join(instance_dir, "callgraph.json")
    if not (os.path.exists(readme) and os.path.exists(gt_path)):
        return {"skip": "missing files"}
    info = parse_readme(readme)
    src_file = find_source_file(info, repo_roots)
    if not src_file:
        return {"skip": "source not available locally",
                "source": info.get("source"), "file": info.get("original_file")}

    # isolate the single file (per-program granularity)
    d = tempfile.mkdtemp(prefix="te_")
    try:
        shutil.copy(src_file, os.path.join(d, os.path.basename(src_file)))
        _root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
        if _root not in sys.path:
            sys.path.insert(0, _root)
        import v3.repository_reasoning.java_type_inference as JT
        rep = JT.enriched_report(d)
        pred = H.codetruth_edges(rep.get("call_graph", {}))
    except Exception as e:
        return {"skip": f"analysis error: {type(e).__name__}: {e}"}
    finally:
        shutil.rmtree(d, ignore_errors=True)

    gt_graph = json.loads(io.open(gt_path, encoding="utf-8").read())
    gold = H.ground_truth_edges(gt_graph)
    tp, fp, fn = H.score(pred, gold)
    return {"tp": tp, "fp": fp, "fn": fn,
            "pred_edges": len(pred), "gt_edges": len(gold)}


def run_split(java_dir, repo_roots, test_ids=None, limit=None):
    """Run over instances in java_dir (optionally restricted to test_ids)."""
    insts = sorted(d for d in os.listdir(java_dir)
                   if os.path.isdir(os.path.join(java_dir, d)))
    if test_ids:
        insts = [i for i in insts if i in test_ids]
    if limit:
        insts = insts[:limit]

    TP = FP = FN = 0
    evaluated = 0
    skipped = {}
    per = []
    for inst in insts:
        res = run_instance(os.path.join(java_dir, inst), repo_roots)
        if "skip" in res:
            skipped[res["skip"]] = skipped.get(res["skip"], 0) + 1
            continue
        TP += res["tp"]; FP += res["fp"]; FN += res["fn"]
        evaluated += 1
        per.append({"instance": inst, **res})

    p, r, f = H.prf(TP, FP, FN)
    return {
        "benchmark": "TraceEval (Java, name-level, Option A)",
        "instances_total": len(insts),
        "evaluated": evaluated,
        "skipped": skipped,
        "micro_TP": TP, "micro_FP": FP, "micro_FN": FN,
        "precision": p, "recall": r, "f1": f,
        "primary_metric": "recall (static-vs-dynamic; precision carries "
                          "static-finds-more caveat; name-level matching)",
        "per_instance": per[:50],
    }


if __name__ == "__main__":
    # CONFIG — edit paths to your machine
    JAVA_DIR = r"C:\repos\TraceEva\data\benchmark\java"
    REPO_ROOTS = {
        "1brc": r"C:\repos\1brc",
        "pki": r"C:\repos\pki",
        "questdb": r"C:\repos\questdb",
        "camel": r"C:\repos\camel",
        "nacos": r"C:\repos\nacos",
        "Apktool": r"C:\repos\Apktool",
    }
    TEST_IDS_FILE = r"C:\repos\TraceEva\data\traceeval_split\test_ids.json"

    test_ids = None
    if os.path.exists(TEST_IDS_FILE):
        try:
            raw = json.loads(io.open(TEST_IDS_FILE, encoding="utf-8").read())
            # test_ids.json may be a list or {lang: [ids]}; handle both
            if isinstance(raw, dict):
                test_ids = set(raw.get("java", []))
            elif isinstance(raw, list):
                test_ids = set(raw)
        except Exception:
            test_ids = None

    rep = run_split(JAVA_DIR, REPO_ROOTS, test_ids=test_ids, limit=None)
    print(json.dumps({k: v for k, v in rep.items() if k != "per_instance"}, indent=2))
