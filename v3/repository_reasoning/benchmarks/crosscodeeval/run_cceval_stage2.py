import os, sys, warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)
import json
from v3.repository_reasoning.reasoning_engine import ReasoningEngine

repo = r"C:\repos\cceval_clones\turboderp-exllama-a544085"
rep = ReasoningEngine(repo).resolve()
print("phase_3a:", json.dumps(rep["phase_3a"], indent=2))
print("edge_provenance:", json.dumps(rep.get("edge_provenance", {}), indent=2))
print("local_receiver_counts:", json.dumps(rep.get("local_receiver_counts", {}), indent=2))
# edge resolution-kind counts in the MERGED call_index
kinds = {}
for caller, edges in rep["call_index"].items():
    for e in edges:
        res = e[3] if len(e) > 3 else "?"
        kinds[res] = kinds.get(res, 0) + 1
print("edge resolution-kind counts in call_index:", json.dumps(kinds, indent=2))