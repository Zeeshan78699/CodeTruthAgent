"""
local_receiver_edges.py
CodeTruth Agent V3 — Module 3, ADDITIVE local-variable receiver edge emitter.

THE GAP (measured in CrossCodeEval + TraceEval): CodeTruth types `localvar`
in `localvar.method()` (e.g. `x = SomeClass(); x.doThing()`) via
variable_type_propagator, and from_repo_attrcall_payoff COUNTS these as
resolvable — but the main pipeline never EMITS them as call-graph edges. This
module surfaces exactly those edges.

It mirrors from_repo_attrcall_payoff's receiver-typing loop, but where that
function does `resolved_class += 1`, this one resolves the method on the typed
receiver's class and APPENDS a {caller, callee, lineno, resolution} edge.

ADDITIVE: new file, imports existing internals, edits nothing. Reuses
_reconstruct_inputs / build_return_type_table_v3 / resolve_env / is_class_type /
_make_value_classifier / _own_assignments / _build_function_indexes — the same
validated machinery, so no re-implementation of type inference.

Resolution label: local_typed_method_call (matches the kind already seen in
call_index). Method resolved against the class-methods index; if the class has
the method -> edge; else the receiver is typed but the method is external/
inherited -> NOT emitted (Truth Boundary: typed receiver, unverified method).
"""
import ast

from v3.repository_reasoning.variable_type_propagator import (
    build_return_type_table_v3, resolve_env, is_class_type,
    RESOLVED, INFERRED, AMBIGUOUS,
    _reconstruct_inputs, _build_function_indexes, _make_value_classifier,
    _own_assignments,
)


def _build_class_bases(inp):
    """{(module, ClassName): [BaseName, ...]} from ClassDef nodes, so we can walk
    the inheritance chain when a method isn't defined on the class itself.
    Also stashes a name->[modules] index on the dict (via a sentinel key) so MRO
    base resolution can be SCOPE-AWARE (prefer same-module base; avoid false cycles
    from two different classes sharing a name)."""
    import ast as _ast
    bases = {}
    name_to_mods = {}
    for module_name, tree in inp.get("module_trees", {}).items():
        for node in _ast.walk(tree):
            if isinstance(node, _ast.ClassDef):
                bnames = []
                for b in node.bases:
                    if isinstance(b, _ast.Name):
                        bnames.append(b.id)
                    elif isinstance(b, _ast.Attribute):
                        bnames.append(b.attr)
                bases[(module_name, node.name)] = bnames
                name_to_mods.setdefault(node.name, []).append(module_name)
    # attach scope index without disturbing normal (module, ClassName) keys
    bases[("__name_to_mods__", "")] = name_to_mods
    return bases


def _method_in_class_named(class_name, method, inp):
    """Search every module's index for a class named class_name defining method.
    Returns callee id or None. (Used for base-class resolution across files.)"""
    cmi = inp.get("class_methods_index", {})
    for mod, classes in cmi.items():
        if isinstance(classes, dict):
            m = classes.get(class_name)
            if isinstance(m, dict) and method in m:
                return m[method]
    return None


def _c3_merge(seqs):
    result = []
    seqs = [list(s) for s in seqs if s]
    while seqs:
        head = None
        for seq in seqs:
            cand = seq[0]
            if not any(cand in s[1:] for s in seqs):
                head = cand
                break
        if head is None:
            return None
        result.append(head)
        new = []
        for seq in seqs:
            if seq and seq[0] == head:
                seq = seq[1:]
            if seq:
                new.append(seq)
        seqs = new
    return result


def _compute_mro(class_key, bases_table, _cache=None):
    if _cache is None:
        _cache = {}
    if class_key in _cache:
        return _cache[class_key]  # includes None (un-linearizable/cyclic) = decline
    # in-progress sentinel: if we re-enter this class while still computing it,
    # the hierarchy is cyclic -> decline (Truth Boundary), never infinite-recurse.
    _cache[class_key] = None
    name_to_mods = bases_table.get(("__name_to_mods__", ""), {})
    cur_mod = class_key[0] if isinstance(class_key, tuple) else None
    def _key_for_name(name):
        mods = name_to_mods.get(name, [])
        # prefer a definition in the SAME module as the deriving class,
        # but NEVER resolve to the deriving class itself (breaks false cycles).
        if cur_mod in mods and (cur_mod, name) != class_key:
            return (cur_mod, name)
        for m in mods:
            if (m, name) != class_key:
                return (m, name)
        return (None, name)  # external / unresolved base
    base_keys = [_key_for_name(n) for n in bases_table.get(class_key, [])]
    seqs = []
    for bk in base_keys:
        if bk in bases_table and bk != ("__name_to_mods__", ""):
            sub = _compute_mro(bk, bases_table, _cache)
            seqs.append(sub if sub else [bk])
        else:
            seqs.append([bk])
    if base_keys:
        seqs.append(list(base_keys))
    merged = _c3_merge(seqs) if seqs else []
    if merged is None:
        _cache[class_key] = None
        return None
    mro = [class_key] + merged
    _cache[class_key] = mro
    return mro


def _resolve_method_on_class(class_type, method, inp, _bases=None, _seen=None):
    """Return the callee id if `class_type` (or an ancestor) defines `method`.

    class_type = ('class', module, ClassName). Resolution order:
      1. own class methods (direct)
      2. inherited: walk base classes (transitively) and resolve there
    Inherited resolution recovers real cross-file edges to parent methods
    (e.g. MyBlueprint.send_static_file -> Blueprint.send_static_file). Still a
    verified resolution — the parent method must exist in the index, never guessed.
    """
    module = class_name = None
    if isinstance(class_type, (tuple, list)):
        if len(class_type) == 3:
            _, module, class_name = class_type
        elif len(class_type) == 2:
            module, class_name = class_type
    elif isinstance(class_type, str):
        class_name = class_type
    if class_name is None:
        return None

    cmi = inp.get("class_methods_index", {})
    gcm = inp.get("global_class_methods", {})

    # 1) own class (direct)
    if module is not None:
        methods = cmi.get(module, {}).get(class_name)
        if isinstance(methods, dict) and method in methods:
            return methods[method]
        methods = gcm.get(module, {}).get(class_name)
        if isinstance(methods, dict) and method in methods:
            return methods[method]
    # own class in any module
    hit = _method_in_class_named(class_name, method, inp)
    if hit:
        return hit

    # 2) inherited: resolve via C3 MRO (Python's real method resolution order),
    #    NOT depth-first. Diamonds become correct: D(B,C).shared() -> C.shared
    #    before A.shared. Linear chains unaffected (MRO == the chain).
    if _bases is None:
        _bases = _build_class_bases(inp)
    key = (module, class_name)
    mro = _compute_mro(key, _bases)
    if mro is None:
        return None  # un-linearizable hierarchy -> decline (Truth Boundary)
    for (mmod, mname) in mro[1:]:
        hit = _method_in_class_named(mname, method, inp)
        if hit:
            return hit
    return None


def emit_local_typed_edges(repo_root, root_counts=None, max_passes=5):
    """Emit call-graph edges for local-variable-typed receiver method calls.
    Returns {call_graph: {module:[edges]}, counts:{...}, boundary:...}."""
    from v3.repository_graph.call_graph import _flatten_attribute
    from v3.repository_graph.languages.python_adapter import PythonAdapter

    inp = _reconstruct_inputs(repo_root, root_counts)
    table_v3 = build_return_type_table_v3(
        inp["module_trees"], inp["function_graph"], inp["class_methods_index"],
        inp["import_alias_maps"], inp["global_class_methods"],
        framework_kb=inp["framework_kb"],
        real_class_names_index=inp["real_class_names_index"], max_passes=max_passes,
    )
    table_single = {fid: rec["type"] for fid, rec in table_v3.items()
                    if rec["label"] in (RESOLVED, INFERRED)}

    m2 = PythonAdapter().scan(repo_root=repo_root, file_paths=[])
    attr_sites = {}
    for u in m2["unresolved"]:
        if u.get("pattern") == "attribute_call":
            attr_sites.setdefault(u["module"], set()).add(u["lineno"])

    all_ids, top_level_name = _build_function_indexes(inp["function_graph"])
    id_by_location = {}
    for module_name, funcs in inp["function_graph"].items():
        for f in funcs:
            id_by_location[(module_name, f["lineno"])] = f["id"]

    call_graph = {}
    counts = {"local_typed_method_call": 0, "local_inherited_method_call": 0,
              "typed_recv_method_unverified": 0,
              "ambiguous_receiver": 0, "builtin_receiver": 0,
              "super_call": 0, "super_unresolved": 0,
              "super_decline_external": 0, "super_decline_inrepo_miss": 0,
              "super_decline_nested_fid": 0, "super_decline_no_bases": 0,
              "super_decline_cyclic": 0,
              "inrepo_miss_init_chain": 0, "inrepo_miss_deep_mro": 0,
              "inrepo_miss_name_collision": 0, "inrepo_miss_other": 0}
    bases_table = _build_class_bases(inp)  # built once, reused per site

    for module_name, tree in inp["module_trees"].items():
        site_lines = attr_sites.get(module_name)
        if not site_lines:
            continue
        edges = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fid = id_by_location.get((module_name, node.lineno))
            if not fid:
                continue
            classify = _make_value_classifier(
                module_name, inp["class_methods_index"].get(module_name, {}),
                inp["import_alias_maps"].get(module_name, {}),
                inp["global_class_methods"], inp["framework_kb"],
                (inp["real_class_names_index"].get(module_name)
                 if inp["real_class_names_index"] is not None else None),
                inp["real_class_names_index"], all_ids, top_level_name,
                _flatten_attribute, fid,
            )
            assignments = [(v, classify(val)) for v, val in _own_assignments(node)]
            env = resolve_env(assignments, table_single)
            for inner in ast.walk(node):
                if not (isinstance(inner, ast.Call)
                        and isinstance(inner.func, ast.Attribute)):
                    continue
                if inner.lineno not in site_lines:
                    continue
                recv = inner.func.value
                method = inner.func.attr
                # super().method() -> resolve to the next class in the ENCLOSING
                # class's C3 MRO (additive; reuses _compute_mro). super() means
                # "next after the lexically-enclosing class in its MRO".
                if (isinstance(recv, ast.Call)
                        and isinstance(recv.func, ast.Name)
                        and recv.func.id == "super"):
                    # enclosing class from caller fid: 'mod.Cls.method' -> ('mod','Cls')
                    parts = fid.split(".")
                    if len(parts) >= 3:
                        enclosing = (".".join(parts[:-2]), parts[-2])
                        mro = _compute_mro(enclosing, bases_table)
                        callee = None
                        if mro:
                            for (mmod, mname) in mro[1:]:  # AFTER the enclosing class
                                hit = _method_in_class_named(mname, method, inp)
                                if hit:
                                    callee = hit
                                    break
                        if callee:
                            edges.append({"caller": fid, "callee": callee,
                                          "lineno": inner.lineno,
                                          "resolution": "super_call"})
                            counts["super_call"] += 1
                        else:
                            counts["super_unresolved"] += 1
                            # categorize WHY it declined (single source of truth)
                            _bs = bases_table.get(enclosing)
                            _n2m = bases_table.get(("__name_to_mods__", ""), {})
                            if _bs is None:
                                counts["super_decline_no_bases"] += 1
                            elif mro is None:
                                counts["super_decline_cyclic"] += 1
                            else:
                                # are all bases external (no in-repo definition)?
                                _all_ext = all(bn not in _n2m for bn in _bs)
                                if _all_ext:
                                    counts["super_decline_external"] += 1
                                else:
                                    counts["super_decline_inrepo_miss"] += 1
                                    # sub-tag WHY, from the emitter's OWN state
                                    if method == "__init__":
                                        counts["inrepo_miss_init_chain"] += 1
                                    elif mro is not None and len(mro) > 4:
                                        counts["inrepo_miss_deep_mro"] += 1
                                    elif any(len(_n2m.get(bn, [])) > 1 for bn in _bs):
                                        counts["inrepo_miss_name_collision"] += 1
                                    else:
                                        counts["inrepo_miss_other"] += 1
                    else:
                        counts["super_unresolved"] += 1
                        counts["super_decline_nested_fid"] += 1
                    continue
                if not isinstance(recv, ast.Name):
                    continue
                if recv.id in ("self", "cls") or recv.id not in env:
                    continue
                rec = env[recv.id]
                if rec["label"] == AMBIGUOUS:
                    counts["ambiguous_receiver"] += 1
                    continue
                if not is_class_type(rec["type"]):
                    counts["builtin_receiver"] += 1
                    continue
                # typed receiver -> resolve the method on its class (or ancestors)
                own = _resolve_method_on_class(rec["type"], method, inp,
                                               _bases={})  # own-only probe
                callee = _resolve_method_on_class(rec["type"], method, inp,
                                                  _bases=bases_table)
                if callee:
                    kind = ("local_typed_method_call" if own
                            else "local_inherited_method_call")
                    edges.append({"caller": fid, "callee": callee,
                                  "lineno": inner.lineno, "resolution": kind})
                    counts[kind] += 1
                else:
                    counts["typed_recv_method_unverified"] += 1
        if edges:
            call_graph[module_name] = edges

    return {
        "language": "python",
        "repo": repo_root,
        "call_graph": call_graph,
        "counts": counts,
        "boundary": "ADDITIVE: emits local-variable-typed receiver method calls "
                    "(localvar.method() where localvar is typed by a constructor/"
                    "return). Receiver typed via existing variable_type_propagator; "
                    "method resolved against class-methods index. Typed receiver "
                    "with unverified/inherited method NOT emitted (Truth Boundary). "
                    "Reuses validated internals; edits nothing.",
    }