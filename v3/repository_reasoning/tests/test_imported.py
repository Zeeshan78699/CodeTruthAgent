import sys, json, warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
_root = r"C:\AI_Project\CodeTruthAgent"; sys.path.insert(0, _root)
import v3.repository_reasoning.imported_receiver_edges as IR

repo = r"C:\repos\v3\flask"
rep = IR.emit_imported_receiver_edges(repo)
print("namespace_bridge:", json.dumps(rep["namespace_bridge"], indent=2))
print("counts:", json.dumps(rep["counts"], indent=2))
total = sum(len(v) for v in rep["call_graph"].values())
print(f"\nimported-receiver edges emitted: {total}")
shown = 0
for mod, edges in rep["call_graph"].items():
    for e in edges:
        print(f"  [{e['resolution']}] {e['caller']} -> {e['callee']}")
        shown += 1
        if shown >= 12: break
    if shown >= 12: break