"""
self_attribute_typer.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Phase 3A.

Types instance attributes (`self.x`) from their assignments across a class, then
resolves the `self.x.method()` / `var.attr.method()` attribute-call sites Module 2
left unresolved.

    class Service:
        def __init__(self):
            self.conn = DatabaseConnection()   # self.conn : DatabaseConnection
        def run(self):
            self.conn.execute(...)             # <- resolved here

Typing rule (same Truth Boundary as the rest of Phase 3A):
  self.x is RESOLVED only if every `self.x = <rhs>` across the class types to the
  SAME single class/builtin. Two different types -> AMBIGUOUS (bounded set). Any
  untyped assignment -> self.x is UNCERTAIN and dropped. Never guessed.

RHS of `self.x = <rhs>` is classified with the SAME machinery as returns/locals
(constructor / call-via-table_v3 / self.method). This is the component that
leans on what Module 2 already tracks for `self.x = Foo()` in __init__.

Additive: only sites Module 2 reported as `attribute_call` unresolved are counted.
Frozen imports stay lazy. Embeds a read-only RHS-shape breakdown so the payoff
and the "what shape are these assignments" measurement come from ONE run.
"""

import ast

from v3.repository_reasoning.return_type_inferencer import (
    RESOLVED, INFERRED, AMBIGUOUS,
    _reconstruct_inputs, build_return_type_table_v3, _build_function_indexes,
)
from v3.repository_reasoning.variable_type_propagator import (
    resolve_env, is_class_type, _make_value_classifier, _rhs_shape,
)


def _class_id_of(fid):
    """Enclosing class id for a method `module.Class.method` -> `module.Class`.
    (Honest limit: nested methods land in a deeper bucket and won't pollute the
    class.)"""
    return fid.rsplit(".", 1)[0] if fid else None


def _own_self_attr_assignments(func_node):
    """[(attr_name, value_node)] for `self.x = <rhs>` / `self.x: T = <rhs>` in
    THIS function (nested defs excluded)."""
    out = []
    def rec(n):
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            tgt = None
            if isinstance(child, ast.Assign) and len(child.targets) == 1:
                tgt = child.targets[0]
            elif isinstance(child, ast.AnnAssign):
                tgt = child.target
            if (tgt is not None and isinstance(tgt, ast.Attribute)
                    and isinstance(tgt.value, ast.Name) and tgt.value.id in ("self", "cls")
                    and getattr(child, "value", None) is not None):
                out.append((tgt.attr, child.value))
            rec(child)
    rec(func_node)
    return out


def build_self_attr_types(inp, table_single, all_ids, top_level_name,
                          id_by_location, flatten_attribute):
    """
    Returns:
        attr_types   : {class_id: {attr_name: ResolvedType}}
        rhs_shapes   : Counter of `self.x = <rhs>` shapes (measurement)
    """
    from collections import Counter
    class_assignments = {}   # class_id -> [(attr, atom)]
    rhs_shapes = Counter()

    for module_name, tree in inp["module_trees"].items():
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fid = id_by_location.get((module_name, node.lineno))
            if not fid:
                continue
            assigns = _own_self_attr_assignments(node)
            if not assigns:
                continue
            class_id = _class_id_of(fid)
            classify = _make_value_classifier(
                module_name, inp["class_methods_index"].get(module_name, {}),
                inp["import_alias_maps"].get(module_name, {}),
                inp["global_class_methods"], inp["framework_kb"],
                (inp["real_class_names_index"].get(module_name)
                 if inp["real_class_names_index"] is not None else None),
                inp["real_class_names_index"], all_ids, top_level_name,
                flatten_attribute, fid,
            )
            bucket = class_assignments.setdefault(class_id, [])
            for attr, val in assigns:
                rhs_shapes[_rhs_shape(val)] += 1
                bucket.append((attr, classify(val)))

    attr_types = {}
    for class_id, pairs in class_assignments.items():
        attr_types[class_id] = resolve_env(pairs, table_single)
    return attr_types, rhs_shapes


def trace_self_attr_calls(repo_root, root_counts=None, max_passes=5):
    """Resolve `self.x.method()` (and `var.attr.method()` where var is a typed
    local) at Module 2's unresolved attribute_call sites. Returns (edges, summary,
    rhs_shapes)."""
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
    baseline = sum(len(v) for v in attr_sites.values())

    all_ids, top_level_name = _build_function_indexes(inp["function_graph"])
    id_by_location = {}
    for module_name, funcs in inp["function_graph"].items():
        for f in funcs:
            id_by_location[(module_name, f["lineno"])] = f["id"]

    attr_types, rhs_shapes = build_self_attr_types(
        inp, table_single, all_ids, top_level_name, id_by_location, _flatten_attribute)

    edges = []
    counts = {"self_attr": 0, "ambiguous": 0}

    for module_name, tree in inp["module_trees"].items():
        site_lines = attr_sites.get(module_name)
        if not site_lines:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fid = id_by_location.get((module_name, node.lineno))
            if not fid:
                continue
            class_id = _class_id_of(fid)
            cls_attrs = attr_types.get(class_id, {})
            if not cls_attrs:
                continue
            for inner in ast.walk(node):
                if not (isinstance(inner, ast.Call)
                        and isinstance(inner.func, ast.Attribute)):
                    continue
                if inner.lineno not in site_lines:
                    continue
                recv = inner.func.value
                # self.x.method()
                if (isinstance(recv, ast.Attribute)
                        and isinstance(recv.value, ast.Name)
                        and recv.value.id in ("self", "cls")):
                    rec = cls_attrs.get(recv.attr)
                    if rec is None:
                        continue
                    if rec["label"] == AMBIGUOUS:
                        types = [t for t in rec["type"] if is_class_type(t)]
                        if not types:
                            continue
                        edges.append({"module": module_name, "lineno": inner.lineno,
                                      "receiver": f"self.{recv.attr}", "method": inner.func.attr,
                                      "receiver_type": types, "label": AMBIGUOUS,
                                      "evidence": f"self_attribute_typer: {class_id}.{recv.attr}"})
                        counts["ambiguous"] += 1
                    elif is_class_type(rec["type"]):
                        edges.append({"module": module_name, "lineno": inner.lineno,
                                      "receiver": f"self.{recv.attr}", "method": inner.func.attr,
                                      "receiver_type": rec["type"], "label": RESOLVED,
                                      "evidence": f"self_attribute_typer: {class_id}.{recv.attr}"})
                        counts["self_attr"] += 1

    summary = {
        "baseline_attr_calls": baseline,
        "self_attr_resolved": counts["self_attr"],
        "self_attr_ambiguous": counts["ambiguous"],
        "total": counts["self_attr"] + counts["ambiguous"],
        "classes_with_typed_attrs": sum(1 for a in attr_types.values() if a),
    }
    return edges, summary, rhs_shapes


def from_repo(repo_root, root_counts=None, max_passes=5, top=14):
    edges, s, rhs = trace_self_attr_calls(repo_root, root_counts, max_passes)
    pct = (100.0 * s["total"] / s["baseline_attr_calls"]
           if s["baseline_attr_calls"] else 0.0)
    print(f"  baseline attribute_call sites          : {s['baseline_attr_calls']}")
    print(f"  classes with >=1 typed self attribute  : {s['classes_with_typed_attrs']}")
    print(f"  self.x.method() RESOLVED               : {s['self_attr_resolved']}")
    print(f"  self.x.method() AMBIGUOUS              : {s['self_attr_ambiguous']}")
    print(f"  >>> self-attribute attr_calls resolved : {s['total']}  ({pct:.1f}% of baseline)")
    print(f"  --- shape of `self.x = <rhs>` assignments (what types them) ---")
    total_rhs = sum(rhs.values())
    for shape, n in rhs.most_common(top):
        p = (100.0 * n / total_rhs) if total_rhs else 0
        print(f"    {shape:34} {n:7}  {p:5.1f}%")
    return edges, s, rhs
