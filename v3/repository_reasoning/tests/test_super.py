import sys, warnings, tempfile, os, json
warnings.filterwarnings("ignore", category=SyntaxWarning)
sys.path.insert(0, r"C:\AI_Project\CodeTruthAgent")
from v3.repository_reasoning.local_receiver_edges import emit_local_typed_edges

FIX = """
class A:
    def foo(self):
        return 1

class E(A):
    def foo(self):
        return super().foo()
    def bar(self):
        return super().foo()
"""
d = tempfile.mkdtemp(prefix="sup_")
open(os.path.join(d,"mod.py"),"w",encoding="utf-8").write(FIX)
rep = emit_local_typed_edges(d)
print("counts:", json.dumps(rep["counts"], indent=2))
for mod, edges in rep["call_graph"].items():
    for e in edges:
        print(f"  [{e['resolution']}] {e['caller']} -> {e['callee']} (line {e['lineno']})")