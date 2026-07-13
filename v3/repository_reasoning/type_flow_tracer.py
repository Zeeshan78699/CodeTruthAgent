"""
type_flow_tracer.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Phase 3A, Step 2.

Banks the measured payoff of Step 1. Takes the receivers that
return_type_inferencer + variable_type_propagator can type, and emits CONCRETE
resolved attribute-call edges for the sites Module 2 left unresolved:

    conn = get_conn()        # typed by variable_type_propagator (via table_v3)
    conn.execute(...)        # <- this edge: (call_site) -> DatabaseConnection.execute

Each edge carries a categorical label (RESOLVED / AMBIGUOUS), never a numeric
score, and is produced ONLY for sites Module 2 reported as `attribute_call`
unresolved - so this strictly ADDS resolutions, never overrides Module 2.

Scope (honest, measured limits - see MODULE3_VALIDATION findings):
  * Receivers handled: local variables typed by Step 1, and self/cls (class-scope).
  * NOT handled here: parameters, globals/closures, deep attribute chains,
    subscripts, method-call chains. Those are the ~98% beyond Step 1 and are
    left as documented unresolved, not guessed.

Reuses variable_type_propagator (receiver typing) and return_type_inferencer
(table_v3). Frozen imports stay lazy.
"""

import ast

from v3.repository_reasoning.return_type_inferencer import (
    RESOLVED, INFERRED, AMBIGUOUS,
    _reconstruct_inputs, build_return_type_table_v3,
    _build_function_indexes,
)
from v3.repository_reasoning.variable_type_propagator import (
    resolve_env, is_class_type, _own_assignments, _make_value_classifier,
)


def _class_of_method_scope(fid):
    """For a method id `module.Class.method`, the enclosing class id
    `module.Class`. Used to type a `self`/`cls` receiver."""
    return fid.rsplit(".", 1)[0] if fid else None


def trace_attribute_calls(repo_root, root_counts=None, max_passes=5):
    """
    Returns the list of resolved Module-3 attribute-call edges:

        {
          "module": str, "lineno": int,
          "receiver": str, "method": str,
          "receiver_type": type_info | [type_info, ...],
          "label": "RESOLVED" | "AMBIGUOUS",
          "evidence": str,
        }

    plus a summary dict. Only sites Module 2 reported as `attribute_call`
    unresolved are considered.
    """
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
    class_real_names = inp["real_class_names_index"] or {}
    for module_name, funcs in inp["function_graph"].items():
        for f in funcs:
            id_by_location[(module_name, f["lineno"])] = f["id"]

    edges = []
    counts = {"RESOLVED": 0, "AMBIGUOUS": 0, "self_cls": 0}

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
            classify = _make_value_classifier(
                module_name, inp["class_methods_index"].get(module_name, {}),
                inp["import_alias_maps"].get(module_name, {}),
                inp["global_class_methods"], inp["framework_kb"],
                (class_real_names.get(module_name) if class_real_names else None),
                inp["real_class_names_index"], all_ids, top_level_name,
                _flatten_attribute, fid,
            )
            own = _own_assignments(node)
            env = resolve_env([(v, classify(val)) for v, val in own], table_single)
            self_class = _class_of_method_scope(fid)

            for inner in ast.walk(node):
                if not (isinstance(inner, ast.Call)
                        and isinstance(inner.func, ast.Attribute)):
                    continue
                if inner.lineno not in site_lines:
                    continue
                recv = inner.func.value
                method = inner.func.attr
                if not isinstance(recv, ast.Name):
                    continue
                name = recv.id

                # self/cls receiver -> the enclosing class
                if name in ("self", "cls"):
                    counts["self_cls"] += 1
                    continue  # M2's own scope; not double-counted as a Module-3 win

                rec = env.get(name)
                if rec is None:
                    continue

                if rec["label"] == AMBIGUOUS:
                    types = [t for t in rec["type"] if is_class_type(t)]
                    if not types:
                        continue
                    edges.append({
                        "module": module_name, "lineno": inner.lineno,
                        "receiver": name, "method": method,
                        "receiver_type": types, "label": AMBIGUOUS,
                        "evidence": f"variable_type_propagator: {name} in {fid}",
                    })
                    counts["AMBIGUOUS"] += 1
                elif is_class_type(rec["type"]) or isinstance(rec["type"], tuple):
                    edges.append({
                        "module": module_name, "lineno": inner.lineno,
                        "receiver": name, "method": method,
                        "receiver_type": rec["type"], "label": RESOLVED,
                        "evidence": f"variable_type_propagator: {name} in {fid}",
                    })
                    counts["RESOLVED"] += 1

    summary = {
        "baseline_attr_calls": baseline,
        "resolved_edges": counts["RESOLVED"],
        "ambiguous_edges": counts["AMBIGUOUS"],
        "self_cls_sites": counts["self_cls"],
        "module3_resolved_total": counts["RESOLVED"] + counts["AMBIGUOUS"],
    }
    return edges, summary


def from_repo(repo_root, root_counts=None, max_passes=5):
    """Print the Step-1 banked result for a repo and return (edges, summary)."""
    edges, s = trace_attribute_calls(repo_root, root_counts, max_passes)
    pct = (100.0 * s["module3_resolved_total"] / s["baseline_attr_calls"]
           if s["baseline_attr_calls"] else 0.0)
    print(f"  baseline attribute_call sites : {s['baseline_attr_calls']}")
    print(f"  Module 3 RESOLVED edges       : {s['resolved_edges']}")
    print(f"  Module 3 AMBIGUOUS edges      : {s['ambiguous_edges']}")
    print(f"  self/cls sites (M2 scope)     : {s['self_cls_sites']}")
    print(f"  >>> Module 3 attribute_calls resolved : "
          f"{s['module3_resolved_total']}  ({pct:.1f}% of baseline)")
    return edges, s
