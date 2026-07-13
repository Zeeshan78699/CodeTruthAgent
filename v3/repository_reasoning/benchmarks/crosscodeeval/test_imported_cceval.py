"""Test the imported-receiver emitter on the CrossCodeEval repos (where the 218
imported-in-repo cases were measured). Shows per-repo how many edges emit, and
crucially whether the methods RESOLVE or hit None (dynamic/absent)."""
import os, sys, warnings, collections
warnings.filterwarnings("ignore", category=SyntaxWarning)
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)
import json
import v3.repository_reasoning.imported_receiver_edges as IR

CLONE_ROOT = r"C:\repos\cceval_clones"

repos = [d for d in os.listdir(CLONE_ROOT)
         if os.path.isdir(os.path.join(CLONE_ROOT, d))]
print(f"testing {len(repos)} CrossCodeEval repos\n")

grand = collections.Counter()
for r in sorted(repos):
    repo = os.path.join(CLONE_ROOT, r)
    try:
        rep = IR.emit_imported_receiver_edges(repo)
        c = rep["counts"]
        emitted = c.get("imported_class_method_call", 0) + c.get("imported_inherited_method_call", 0)
        for k, v in c.items():
            grand[k] += v
        if emitted or c.get("imported_unresolved", 0):
            print(f"  {r[:38]:38} emitted={emitted:3}  unresolved={c.get('imported_unresolved',0):3}  external={c.get('imported_target_external',0):3}")
    except Exception as e:
        print(f"  {r[:38]:38} ERROR {type(e).__name__}: {str(e)[:40]}")

print("\n=== AGGREGATE across all CrossCodeEval repos ===")
print(json.dumps(dict(grand), indent=2))
emitted_total = grand.get("imported_class_method_call",0) + grand.get("imported_inherited_method_call",0)
print(f"\nTOTAL imported-receiver edges emitted: {emitted_total}")
print(f"TOTAL bridged-but-method-unresolved: {grand.get('imported_unresolved',0)}")
print("\nINTERPRETATION:")
print("  emitted > 0  -> the bridge closes real cross-file edges (payoff)")
print("  unresolved high -> methods are dynamic/absent (gap analysis over-counted;")
print("                     the 218 aren't statically resolvable even with bridge)")
