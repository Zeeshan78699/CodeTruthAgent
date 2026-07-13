"""
classify_patterns.py — Step A: sub-classify the inrepo_miss + no_bases super()
declines corpus-wide into ROOT-CAUSE PATTERNS, so we fix each pattern ONCE.

Patterns for inrepo_miss (base in-repo, method not found via MRO):
  P_INIT_CHAIN     - method is __init__ and base's __init__ is itself inherited
                     (MRO walk found the base but base has no OWN __init__)
  P_DEEP_MRO       - method exists 2+ levels up; MRO didn't reach it
  P_INDEX_GAP      - method IS defined on an MRO class per AST but not in
                     class_methods_index (indexing miss)
  P_NAME_COLLISION - base name resolves to wrong module's class
Patterns for no_bases:
  N_NESTED_CLASS   - enclosing class defined inside a function (fid too deep)
  N_ROOT_NO_BASE   - class genuinely has no bases (super() -> object, correct)
  N_KEY_MISMATCH   - class exists but bases keyed under a different (module,name)
"""
import os, sys, warnings, ast, collections
warnings.filterwarnings("ignore", category=SyntaxWarning)
_root = r"C:\AI_Project\CodeTruthAgent"
sys.path.insert(0, _root)
import v3.repository_reasoning.local_receiver_edges as LR
from v3.repository_reasoning.variable_type_propagator import _reconstruct_inputs
from v3.repository_graph.languages.python_adapter import PythonAdapter

CORPUS = r"C:\repos\v3"

def classify_repo(repo):
    inp = _reconstruct_inputs(repo, None)
    bases = LR._build_class_bases(inp)
    n2m = bases.get(("__name_to_mods__", ""), {})
    m2 = PythonAdapter().scan(repo_root=repo, file_paths=[])
    attr_sites = {}
    for u in m2.get("unresolved", []):
        if u.get("pattern")=="attribute_call":
            attr_sites.setdefault(u["module"],set()).add(u["lineno"])
    id_by_loc = {}
    for mod, funcs in inp["function_graph"].items():
        for f in funcs:
            id_by_loc[(mod, f["lineno"])] = f["id"]
    cmi = inp.get("class_methods_index", {})

    pat = collections.Counter()
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
                if not (isinstance(recv,ast.Call) and isinstance(recv.func,ast.Name) and recv.func.id=="super"): continue
                method = inner.func.attr
                parts = fid.split(".")
                if len(parts) < 3:
                    pat["N_NESTED_CLASS"] += 1; continue
                enclosing = (".".join(parts[:-2]), parts[-2])
                bs = bases.get(enclosing)
                mro = LR._compute_mro(enclosing, bases)
                # skip resolved ones (only classify DECLINES)
                if mro:
                    resolved = any(LR._method_in_class_named(mn, method, inp) for (mm,mn) in mro[1:])
                    if resolved:
                        continue
                # NO_BASES bucket
                if bs is None:
                    # is the enclosing class in cmi at all?
                    in_cmi = any(enclosing[1] in classes for classes in cmi.values() if isinstance(classes,dict))
                    # is enclosing nested (fid has a func between module and class)?
                    # heuristic: module part of fid != actual module -> nested
                    if in_cmi:
                        pat["N_KEY_MISMATCH"] += 1
                    else:
                        pat["N_ROOT_OR_NESTED"] += 1
                    continue
                # INREPO_MISS bucket (bases exist, method not found)
                if mro is None:
                    pat["P_CYCLIC"] += 1; continue
                if method == "__init__":
                    pat["P_INIT_CHAIN"] += 1
                else:
                    # is the method defined ANYWHERE in the MRO classes per AST
                    # but missing from index? check name collision vs deep-mro
                    defined_somewhere = False
                    for (mm, mn) in mro[1:]:
                        mods = n2m.get(mn, [])
                        if len(mods) > 1:
                            pat["P_NAME_COLLISION"] += 1
                            defined_somewhere = True
                            break
                    if not defined_somewhere:
                        pat["P_DEEP_MRO_OR_INDEX"] += 1
    return pat

def main():
    repos = [d for d in sorted(os.listdir(CORPUS))
             if os.path.isdir(os.path.join(CORPUS,d)) and not d.startswith(".")]
    grand = collections.Counter()
    done = 0
    total_repos = len(repos)
    print(f"classifying {total_repos} repos...\n", flush=True)
    for idx, r in enumerate(repos, 1):
        print(f"  [{idx:2}/{total_repos}] {r[:32]:32} ...", end="", flush=True)
        try:
            pat = classify_repo(os.path.join(CORPUS, r))
            grand.update(pat)
            done += 1
            n = sum(pat.values())
            print(f" done  (+{n} declines classified)", flush=True)
        except Exception as e:
            print(f" SKIP ({type(e).__name__})", flush=True)
    print(f"\nclassified {done}/{total_repos} repos\n")
    print("=== DECLINE PATTERN BREAKDOWN (corpus-wide) ===")
    total = sum(grand.values())
    for pat, n in grand.most_common():
        print(f"  {pat:22} {n:6}  ({100.0*n/max(1,total):4.1f}%)")
    print(f"\n  TOTAL classified declines: {total}")
    print("\nFIX GUIDE:")
    print("  P_INIT_CHAIN      -> walk to object/implicit __init__; or resolve to")
    print("                       nearest ancestor WITH __init__ (one fix)")
    print("  P_DEEP_MRO_OR_INDEX-> method-index completeness / deeper MRO walk")
    print("  P_NAME_COLLISION  -> qualified-name resolution (the big rewrite)")
    print("  N_KEY_MISMATCH    -> _build_class_bases keying (one fix)")
    print("  N_ROOT_OR_NESTED  -> super()->object (correct) OR nested (rewrite)")

if __name__ == "__main__":
    main()
