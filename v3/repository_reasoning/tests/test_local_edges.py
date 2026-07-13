import sys, json
_root = r"C:\AI_Project\CodeTruthAgent"; sys.path.insert(0, _root)
import v3.repository_reasoning.local_receiver_edges as LR

repo = r"C:\repos\cceval_clones\turboderp-exllama-a544085"
rep = LR.emit_local_typed_edges(repo)
print("counts:", json.dumps(rep["counts"], indent=2))
cg = rep["call_graph"]
total = sum(len(v) for v in cg.values())
print(f"\nlocal-typed edges emitted: {total} across {len(cg)} modules")
print("\nsample edges:")
shown = 0
for mod, edges in cg.items():
    for e in edges:
        print(f"  {e['caller']} -> {e['callee']}  (line {e['lineno']})")
        shown += 1
        if shown >= 10: break
    if shown >= 10: break