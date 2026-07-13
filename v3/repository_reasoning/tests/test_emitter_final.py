import sys, json, warnings, os
warnings.filterwarnings("ignore", category=SyntaxWarning)
_root = r"C:\AI_Project\CodeTruthAgent"; sys.path.insert(0, _root)
import v3.repository_reasoning.local_receiver_edges as LR
for repo in [r"C:\repos\v3\flask", r"C:\repos\v3\django"]:
    if not os.path.isdir(repo): 
        print(f"[skip] {repo}"); continue
    rep = LR.emit_local_typed_edges(repo)
    c = rep["counts"]
    total = sum(len(v) for v in rep["call_graph"].values())
    print(f"\n===== {os.path.basename(repo)} =====")
    print("counts:", json.dumps(c))
    print(f"TOTAL EDGES EMITTED: {total}")
    # show sample inherited edges
    shown = 0
    for mod, edges in rep["call_graph"].items():
        for e in edges:
            if e["resolution"] == "local_inherited_method_call":
                print(f"  [inherited] {e['caller']} -> {e['callee']}")
                shown += 1
                if shown >= 5: break
        if shown >= 5: break