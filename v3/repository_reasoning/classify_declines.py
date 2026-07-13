"""
classify_declines.py — for the heavy-decline repos (odoo, pytorch, pulumi), split
super_unresolved into:
  EXTERNAL_BASE   - enclosing class extends a class NOT in the repo (correct decline)
  NO_BASES        - enclosing class has no bases recorded (nested-class bug OR root)
  NESTED_FID      - caller fid is deeper than module.Class.method (function-nested)
  IN_REPO_MISS    - base IS in repo but method not found (potential real gap)
So we know if 50% is a correct ceiling or a fixable bug.
"""
import os, sys, warnings, ast, json, collections
warnings.filterwarnings("ignore", category=SyntaxWarning)
_root = r"C:\AI_Project\CodeTruthAgent"
sys.path.insert(0, _root)
import v3.repository_reasoning.local_receiver_edges as LR
from v3.repository_reasoning.variable_type_propagator import _reconstruct_inputs
from v3.repository_graph.languages.python_adapter import PythonAdapter

def classify(repo):
    inp = _reconstruct_inputs(repo, None)
    bases = LR._build_class_bases(inp)
    m2 = PythonAdapter().scan(repo_root=repo, file_paths=[])
    attr_sites = {}
    for u in m2.get("unresolved", []):
        if u.get("pattern") == "attribute_call":
            attr_sites.setdefault(u["module"], set()).add(u["lineno"])
    id_by_loc = {}
    for mod, funcs in inp["function_graph"].items():
        for f in funcs:
            id_by_loc[(mod, f["lineno"])] = f["id"]
    cat = collections.Counter()
    for module_name, tree in inp["module_trees"].items():
        sites = attr_sites.get(module_name)
        if not sites: continue
        for node in ast.walk(tree):
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
            fid = id_by_loc.get((module_name, node.lineno))
            if not fid: continue
            for inner in ast.walk(node):
                if not (isinstance(inner,ast.Call) and isinstance(inner.func,ast.Attribute)): continue
                if inner.lineno not in sites: continue
                recv = inner.func.value
                if not (isinstance(recv,ast.Call) and isinstance(recv.func,ast.Name) and recv.func.id=="super"):
                    continue
                method = inner.func.attr
                parts = fid.split(".")
                if len(parts) < 3:
                    cat["NESTED_FID"] += 1; continue
                enclosing = (".".join(parts[:-2]), parts[-2])
                mro = LR._compute_mro(enclosing, bases)
                if mro is None:
                    cat["CYCLIC_MRO"] += 1; continue
                bs = bases.get(enclosing)
                if bs is None:
                    cat["NO_BASES"] += 1; continue
                # bases exist: are any in-repo?
                resolved_here = False
                for (mmod, mname) in mro[1:]:
                    if LR._method_in_class_named(mname, method, inp):
                        resolved_here = True; break
                if resolved_here:
                    cat["WOULD_RESOLVE"] += 1  # shouldn't be in unresolved - odd
                else:
                    # check if ALL bases are external (not in repo)
                    all_ext = all(not any(c==b for (m,c) in bases) for b in bs)
                    cat["EXTERNAL_BASE" if all_ext else "IN_REPO_MISS"] += 1
    return cat

for r in ("odoo", "pytorch", "pulumi", "python"):
    repo = os.path.join(r"C:\repos\v3", r)
    if not os.path.exists(repo):
        print(f"{r}: not found"); continue
    try:
        c = classify(repo)
        print(f"\n{r}: {dict(c)}")
    except Exception as e:
        print(f"{r}: ERROR {type(e).__name__}: {e}")
