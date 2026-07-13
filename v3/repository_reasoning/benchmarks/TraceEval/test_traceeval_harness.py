"""Test for TraceEval harness id-transform + scoring (no repo/engine needed).
Run from project root: python v3\repository_reasoning\benchmarks\TraceEval\test_traceeval_harness.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import traceeval_harness as H

def run():
    f = []
    # id transform: doubled-class + separator
    if H.to_traceeval_id("a.b.C.C.m") != "a.b.C:m": f.append("doubled-class/sep")
    # nested class stripped to bare (both sides)
    if H.to_traceeval_id("a.b.Outer.Inner.m") != "a.b.Inner:m": f.append("nested CT")
    if H.normalize_gt_id("a.b.Outer.Inner:m(int)") != "a.b.Inner:m": f.append("nested GT")
    # arg strip on GT
    if H.normalize_gt_id("a.b.C:m(int,int)") != "a.b.C:m": f.append("gt args")
    # edge extraction skips internal keys
    cg = {"mod":[{"caller":"a.b.C.C.f","callee":"a.b.C.C.g"}], "__java_3a_type_resolved__":[]}
    e = H.codetruth_edges(cg)
    if e != {("a.b.C:f","a.b.C:g")}: f.append(f"edge-extract {e}")
    # scoring
    pred = {("x","y"),("x","z")}; gold = {("x","y"),("x","w")}
    tp,fp,fn = H.score(pred, gold)
    if (tp,fp,fn) != (1,1,1): f.append(f"score {(tp,fp,fn)}")
    p,r,fl = H.prf(1,1,1)
    if (p,r,fl) != (0.5,0.5,0.5): f.append(f"prf {(p,r,fl)}")
    if f:
        print("FAIL"); [print("  -",x) for x in f]; return 1
    print("PASS - TraceEval harness: id transform (doubled-class, separator, "
          "nested-class, arg-strip), edge extraction, micro P/R/F1")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())
