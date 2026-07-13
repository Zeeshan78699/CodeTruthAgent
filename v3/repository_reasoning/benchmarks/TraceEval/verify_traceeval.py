import io, os, json, sys, tempfile, shutil
_root = r"C:\AI_Project\CodeTruthAgent"; sys.path.insert(0, _root)
sys.path.insert(0, r"v3\repository_reasoning\benchmarks\TraceEval")
import traceeval_harness as H
import v3.repository_reasoning.java_type_inference as JT

JAVA_DIR = r"C:\repos\TraceEva\data\benchmark\java"
raw = json.loads(io.open(r"C:\repos\TraceEva\data\traceeval_split\test_ids.json", encoding="utf-8").read())
test = sorted(set(raw["java"]))

self_gt = other_gt = 0
sample_shown = 0
for inst in test[:60]:
    d0 = os.path.join(JAVA_DIR, inst)
    gtp = os.path.join(d0, "callgraph.json")
    if not os.path.exists(gtp): continue
    srcf = fc = None
    for r,_,fs in os.walk(d0):
        for f in fs:
            if f.endswith(".java"): srcf=os.path.join(r,f); fc=f[:-5]; break
        if srcf: break
    if not srcf: continue
    gold = H._apply_init(H.ground_truth_edges(json.loads(io.open(gtp,encoding="utf-8").read())))
    same,_ = H.partition_by_file(gold, fc)
    for caller,callee in same:
        cc = caller.rsplit(":",1)[0].split(".")[-1]
        ce = callee.rsplit(":",1)[0].split(".")[-1]
        if cc==ce: self_gt+=1
        else: other_gt+=1
    if sample_shown < 3:
        d=tempfile.mkdtemp(); shutil.copy(srcf, os.path.join(d,os.path.basename(srcf)))
        pred=H._apply_init(H.codetruth_edges(JT.enriched_report(d).get("call_graph",{})))
        shutil.rmtree(d,ignore_errors=True)
        matched = sorted(pred & same)
        if matched:
            print(f"{inst} matched (sample): {matched[:3]}")
            sample_shown+=1

tot = self_gt+other_gt or 1
print(f"\nsame-file GT composition (first 60 instances):")
print(f"  self/intra-class: {self_gt} ({100*self_gt/tot:.0f}%)")