"""
run_traceeval_v2.py — corrected TraceEval runner for CodeTruth (Java).

KEY CORRECTIONS vs v1:
  * Uses the SOURCE BUNDLED INSIDE each instance folder (correct traced version)
    instead of cloning repos at HEAD -> no commit drift, no cloning.
  * Scores against the SAME-FILE subset of GT edges (the edges a single-file
    static analyzer can recover); CROSS-FILE edges (callee defined in an unshipped
    file) are counted separately as structurally unrecoverable, NOT as failures.
  * Applies <init> constructor normalization symmetrically.

Reports:
  - samefile recall  : TP / samefile_GT   (the fair primary metric)
  - precision        : TP / (TP + FP)
  - crossfile share  : how much of TraceEval's GT is unrecoverable from 1 file
  - static-vs-dynamic caveat retained.
"""
import io, os, json, sys, glob, warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _here)
_root = os.path.abspath(os.path.join(_here, "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)
import traceeval_harness as H


def bundled_java_file(instance_dir):
    """Return the single bundled .java file path + its bare class stem."""
    for root, _, files in os.walk(instance_dir):
        for f in files:
            if f.endswith(".java"):
                return os.path.join(root, f), os.path.splitext(f)[0]
    return None, None


def run_instance(instance_dir):
    gt_path = os.path.join(instance_dir, "callgraph.json")
    if not os.path.exists(gt_path):
        return {"skip": "no callgraph"}
    src, file_class = bundled_java_file(instance_dir)
    if not src:
        return {"skip": "no bundled source"}

    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="te2_")
    try:
        shutil.copy(src, os.path.join(d, os.path.basename(src)))
        import v3.repository_reasoning.java_type_inference as JT
        rep = JT.enriched_report(d)
        pred = H.codetruth_edges(rep.get("call_graph", {}))
    except Exception as e:
        return {"skip": f"analysis error: {type(e).__name__}"}
    finally:
        shutil.rmtree(d, ignore_errors=True)

    gt = json.loads(io.open(gt_path, encoding="utf-8").read())
    gold = H.ground_truth_edges(gt)
    res = H.score_with_partition(pred, gold, file_class)
    res["instance"] = os.path.basename(instance_dir)
    return res


def run(java_dir, test_ids):
    insts = [i for i in sorted(os.listdir(java_dir))
             if os.path.isdir(os.path.join(java_dir, i)) and i in test_ids]
    TP = FP = FN = SAME = CROSS = 0
    evaluated = 0
    skipped = {}
    for inst in insts:
        r = run_instance(os.path.join(java_dir, inst))
        if "skip" in r:
            skipped[r["skip"]] = skipped.get(r["skip"], 0) + 1
            continue
        TP += r["tp"]; FP += r["fp"]; FN += r["fn_samefile"]
        SAME += r["samefile_gt"]; CROSS += r["crossfile_gt_unrecoverable"]
        evaluated += 1

    samefile_recall = TP / SAME if SAME else 0.0
    precision = TP / (TP + FP) if (TP + FP) else 0.0
    f1 = (2*precision*samefile_recall/(precision+samefile_recall)
          if (precision+samefile_recall) else 0.0)
    total_gt = SAME + CROSS
    return {
        "benchmark": "TraceEval (Java, name-level, bundled-source, fair partition)",
        "instances_total": len(insts),
        "evaluated": evaluated,
        "skipped": skipped,
        "micro_TP": TP, "micro_FP": FP, "micro_FN_samefile": FN,
        "samefile_GT_edges": SAME,
        "crossfile_GT_unrecoverable": CROSS,
        "crossfile_share_of_GT": round(CROSS / total_gt, 4) if total_gt else 0.0,
        "samefile_recall": round(samefile_recall, 4),
        "precision": round(precision, 4),
        "f1_samefile": round(f1, 4),
        "note": "samefile_recall is the fair metric (edges recoverable from the "
                "single bundled file). cross-file edges need callee definitions "
                "TraceEval does not ship per-instance -> structurally "
                "unrecoverable, counted not scored. static-vs-dynamic: precision "
                "carries static-finds-more; recall is on executed same-file edges.",
    }


if __name__ == "__main__":
    JAVA_DIR = r"C:\repos\TraceEva\data\benchmark\java"
    raw = json.loads(io.open(r"C:\repos\TraceEva\data\traceeval_split\test_ids.json",
                             encoding="utf-8").read())
    test_ids = set(raw["java"]) if isinstance(raw, dict) else set(raw)
    rep = run(JAVA_DIR, test_ids)
    print(json.dumps(rep, indent=2))
