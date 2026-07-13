"""
variable_type_propagator.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Phase 3A, Step 1b.

Types LOCAL VARIABLES inside a function, then measures how many of Module 2's
remaining `attribute_call` sites now have a typed receiver. This is the first
number that speaks to the actual goal (the 11,413 unresolved on FastAPI), not to
return-table growth.

Receiver-typing rule for `var.method()`:
  var is resolvable iff every assignment to var in the function types to the SAME
  single class/builtin. Two different types across assignments -> AMBIGUOUS
  (bounded set, reported separately). Any untyped assignment -> var is UNCERTAIN
  and NOT counted as resolved. Never guessed.

Assignment RHS is classified with the SAME machinery as return inference:
  constructor/builtin   -> ("type", type_info)        via frozen _classify
  func()/self.method()  -> ("call", target_fid)        -> looked up in table_v3
  anything else         -> unknown                      -> var untyped

Reuses return_type_inferencer (table_v3, call-target resolution) and the frozen
engine. Frozen imports stay lazy so the pure core (resolve_env) is unit-testable.
"""

import ast

from v3.repository_reasoning.return_type_inferencer import (
    RESOLVED, INFERRED, AMBIGUOUS,
    _reconstruct_inputs, build_return_type_table_v3,
    _build_function_indexes, _resolve_call_target,
)


# ----------------------------------------------------------------------------- #
# PURE CORE -- unit-testable with synthetic assignments, no AST / frozen engine
# ----------------------------------------------------------------------------- #

def resolve_env(assignments, table_single):
    """
    assignments  : ordered [(var_name, atom)], atom is
                   ("type", type_info) | ("call", target_fid) | ("unknown",)
    table_single : {full_id: type_info}  (RESOLVED+INFERRED entries of table_v3)

    Returns {var: {"type": type_info | [type_info,...], "label": <categorical>}}.
    A var with any untyped assignment is omitted (UNCERTAIN -> not resolved).
    """
    seen = {}  # var -> set(type_info | None)
    for var, atom in assignments:
        if atom[0] == "type":
            t = atom[1]
        elif atom[0] == "call":
            t = table_single.get(atom[1])
        else:
            t = None
        seen.setdefault(var, set()).add(t)

    out = {}
    for var, types in seen.items():
        if None in types:
            continue  # an assignment we couldn't type poisons the variable
        if len(types) == 1:
            out[var] = {"type": next(iter(types)), "label": RESOLVED}
        else:
            out[var] = {"type": sorted(types, key=repr), "label": AMBIGUOUS}
    return out


def is_class_type(type_info):
    """A receiver worth resolving has a class type (instance with methods)."""
    return isinstance(type_info, tuple) and len(type_info) == 3 and type_info[0] == "class"


# ----------------------------------------------------------------------------- #
# AST GLUE
# ----------------------------------------------------------------------------- #

def _own_assignments(func_node):
    """[(var_name, value_node)] for simple `var = <expr>` / `var: T = <expr>` in
    THIS function, in source order, excluding nested defs."""
    out = []
    def rec(n):
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if isinstance(child, ast.Assign) and len(child.targets) == 1 \
                    and isinstance(child.targets[0], ast.Name) and child.value is not None:
                out.append((child.targets[0].id, child.value))
            elif isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name) \
                    and child.value is not None:
                out.append((child.target.id, child.value))
            rec(child)
    rec(func_node)
    return out


def _make_value_classifier(module_name, class_methods, import_alias_map,
                           global_class_methods, framework_kb, real_class_names,
                           real_class_names_index, all_ids, top_level_name,
                           flatten_attribute, current_fid):
    """Returns classify(value) -> atom, reusing the frozen _ReturnClassifier and
    the same self-method / call-target resolution as return inference."""
    from v3.repository_graph.type_inference import _ReturnClassifier
    clf = _ReturnClassifier(
        module_name, class_methods, import_alias_map, global_class_methods,
        framework_kb=framework_kb, real_class_names=real_class_names,
        global_real_class_names=real_class_names_index,
    )

    def classify(value):
        if isinstance(value, ast.Await):
            value = value.value
        info = clf._classify(value)
        if info is not None:
            return ("type", info)
        # self.method() -> EnclosingClass.method
        if (isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute)
                and isinstance(value.func.value, ast.Name)
                and value.func.value.id in ("self", "cls") and current_fid):
            target = f"{current_fid.rsplit('.', 1)[0]}.{value.func.attr}"
            if target in all_ids:
                return ("call", target)
        target = _resolve_call_target(value, module_name, import_alias_map,
                                      all_ids, top_level_name, flatten_attribute)
        if target is not None:
            return ("call", target)
        return ("unknown",)

    return classify


def from_repo_attrcall_payoff(repo_root, root_counts=None, max_passes=5):
    """
    Measures Module 3 Step-1 payoff: of Module 2's remaining `attribute_call`
    sites, how many now have a receiver we can type via table_v3 + local
    variable propagation. Prints the breakdown.
    """
    from v3.repository_graph.type_inference import _ReturnClassifier  # noqa: F401
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

    # Authoritative baseline: Module 2's own unresolved attribute_call sites.
    m2 = PythonAdapter().scan(repo_root=repo_root, file_paths=[])
    attr_sites = {}  # module -> set(lineno)
    for u in m2["unresolved"]:
        if u.get("pattern") == "attribute_call":
            attr_sites.setdefault(u["module"], set()).add(u["lineno"])
    total_attr = sum(len(v) for v in attr_sites.values())

    all_ids, top_level_name = _build_function_indexes(inp["function_graph"])
    id_by_location = {}
    for module_name, funcs in inp["function_graph"].items():
        for f in funcs:
            id_by_location[(module_name, f["lineno"])] = f["id"]

    resolved_class = 0
    resolved_builtin = 0
    ambiguous_recv = 0
    self_recv = 0

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
                (inp["real_class_names_index"].get(module_name)
                 if inp["real_class_names_index"] is not None else None),
                inp["real_class_names_index"], all_ids, top_level_name,
                _flatten_attribute, fid,
            )
            assignments = [(v, classify(val)) for v, val in _own_assignments(node)]
            env = resolve_env(assignments, table_single)

            # Find attribute_call sites inside THIS function and check the receiver.
            for inner in ast.walk(node):
                if not (isinstance(inner, ast.Call)
                        and isinstance(inner.func, ast.Attribute)):
                    continue
                if inner.lineno not in site_lines:
                    continue
                recv = inner.func.value
                if isinstance(recv, ast.Name):
                    if recv.id in ("self", "cls"):
                        self_recv += 1
                    elif recv.id in env:
                        rec = env[recv.id]
                        if rec["label"] == AMBIGUOUS:
                            ambiguous_recv += 1
                        elif is_class_type(rec["type"]):
                            resolved_class += 1
                        else:
                            resolved_builtin += 1

    newly = resolved_class + resolved_builtin
    print(f"  Module 2 attribute_call sites (baseline)   : {total_attr}")
    print(f"  NEW receiver typed -> resolvable (class)    : {resolved_class}")
    print(f"  NEW receiver typed -> resolvable (builtin)  : {resolved_builtin}")
    print(f"  receiver AMBIGUOUS (bounded set, partial)   : {ambiguous_recv}")
    print(f"  receiver = self/cls (M2 scope, not counted) : {self_recv}")
    pct = (100.0 * newly / total_attr) if total_attr else 0.0
    print(f"  >>> NEW attribute_calls resolvable          : {newly}  ({pct:.1f}% of baseline)")
    return {
        "baseline_attr_calls": total_attr,
        "new_resolvable_class": resolved_class,
        "new_resolvable_builtin": resolved_builtin,
        "ambiguous_receiver": ambiguous_recv,
        "new_total": newly,
    }


# ----------------------------------------------------------------------------- #
# RECEIVER-SHAPE BREAKDOWN  (read-only diagnostic)
# Characterises the RECEIVER of each unresolved attribute_call site: what is the
# `X` in `X.method()` that Module 2 couldn't type? This is different from the
# return-shape breakdown - it tells us which receiver-typing component (if any)
# could ever resolve these calls.
# ----------------------------------------------------------------------------- #

def _categorize_receiver(recv, env, assigned_from):
    """recv is the AST node before `.method()`. env = typed locals.
    assigned_from = {var_name: rhs_shape} for vars assigned in the function."""
    if isinstance(recv, ast.Name):
        name = recv.id
        if name in ("self", "cls"):
            return "self/cls"
        if name in env:
            return "local_var_" + env[name]["label"]   # RESOLVED or AMBIGUOUS
        if name in assigned_from:
            return "local_var_assigned_from:" + assigned_from[name]
        return "name_param_or_global"          # not assigned in fn -> param/global/closure
    if isinstance(recv, ast.Attribute):
        base = recv.value
        if isinstance(base, ast.Name) and base.id in ("self", "cls"):
            return "self.attr.method()"        # self.x.method()
        if isinstance(base, ast.Name):
            return "var.attr.method()"
        if isinstance(base, ast.Attribute):
            return "deep.attr.chain.method()"
        if isinstance(base, ast.Call):
            return "call().attr.method()"
        return "other.attr.method()"
    if isinstance(recv, ast.Call):
        f = recv.func
        if isinstance(f, ast.Attribute):
            b = f.value
            if isinstance(b, ast.Name) and b.id in ("self", "cls"):
                return "self.method().method()"
            return "obj.method().method()"     # chained method call
        if isinstance(f, ast.Name):
            return "func().method()"
        return "call().method()"
    if isinstance(recv, ast.Subscript):
        return "subscript[i].method()"
    if isinstance(recv, ast.Await):
        return "await_" + _categorize_receiver(recv.value, env, assigned_from)
    if isinstance(recv, ast.Constant):
        return "literal.method()"
    return "other:" + type(recv).__name__


def _rhs_shape(value):
    """Coarse shape of a `var = <value>` RHS, for the assigned_from bucket."""
    if isinstance(value, ast.Await):
        return "await_" + _rhs_shape(value.value)
    if isinstance(value, ast.Call):
        f = value.func
        if isinstance(f, ast.Name):
            return "func_call"
        if isinstance(f, ast.Attribute):
            b = f.value
            if isinstance(b, ast.Name) and b.id in ("self", "cls"):
                return "self_method_call"
            return "obj_method_call"
        return "call_other"
    if isinstance(value, ast.Attribute):
        return "attr"
    if isinstance(value, ast.Subscript):
        return "subscript"
    if isinstance(value, ast.Name):
        return "name"
    return "other:" + type(value).__name__


def from_repo_receiver_breakdown(repo_root, root_counts=None, max_passes=5, top=20):
    from collections import Counter
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
    total_attr = sum(len(v) for v in attr_sites.values())

    all_ids, top_level_name = _build_function_indexes(inp["function_graph"])
    id_by_location = {}
    for module_name, funcs in inp["function_graph"].items():
        for f in funcs:
            id_by_location[(module_name, f["lineno"])] = f["id"]

    cats = Counter()
    seen = 0
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
                (inp["real_class_names_index"].get(module_name)
                 if inp["real_class_names_index"] is not None else None),
                inp["real_class_names_index"], all_ids, top_level_name,
                _flatten_attribute, fid,
            )
            own = _own_assignments(node)
            env = resolve_env([(v, classify(val)) for v, val in own], table_single)
            assigned_from = {v: _rhs_shape(val) for v, val in own}

            for inner in ast.walk(node):
                if not (isinstance(inner, ast.Call)
                        and isinstance(inner.func, ast.Attribute)):
                    continue
                if inner.lineno not in site_lines:
                    continue
                seen += 1
                cats[_categorize_receiver(inner.func.value, env, assigned_from)] += 1

    print(f"  unresolved attribute_call sites matched: {seen} / baseline {total_attr}")
    for cat, n in cats.most_common(top):
        pct = (100.0 * n / seen) if seen else 0
        print(f"    {cat:42} {n:7}  {pct:5.1f}%")
    return cats


# ----------------------------------------------------------------------------- #
# PARAMETER-SHAPE BREAKDOWN  (read-only diagnostic)
# For attribute_call receivers that are a bare Name resolving to a parameter or
# global, classify by annotation shape. Decides whether parameter typing is a
# cheap win (annotated -> Module 2's annotation_resolver already types these) or
# a hard problem (unannotated -> needs call-site argument inference).
# ----------------------------------------------------------------------------- #

def _params_of(func_node):
    """{param_name: annotation_node_or_None} for all arg kinds."""
    a = func_node.args
    params = {}
    for arg in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs):
        params[arg.arg] = arg.annotation
    if a.vararg:
        params[a.vararg.arg] = a.vararg.annotation
    if a.kwarg:
        params[a.kwarg.arg] = a.kwarg.annotation
    return params


def _annotation_shape(ann):
    if ann is None:
        return "param_UNANNOTATED"
    if isinstance(ann, ast.Name):
        return "param_annot_class_name"          # def f(x: Widget) - resolvable
    if isinstance(ann, ast.Attribute):
        return "param_annot_dotted"              # def f(x: mod.Widget) - resolvable
    if isinstance(ann, ast.Constant) and isinstance(ann.value, str):
        return "param_annot_forwardref(str)"     # def f(x: 'Widget')
    if isinstance(ann, ast.Subscript):
        return "param_annot_generic(Optional/List/..)"
    return "param_annot_other:" + type(ann).__name__


def from_repo_param_breakdown(repo_root, root_counts=None, max_passes=5, top=20):
    from collections import Counter
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

    cats = Counter()
    param_or_global = 0
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
                (inp["real_class_names_index"].get(module_name)
                 if inp["real_class_names_index"] is not None else None),
                inp["real_class_names_index"], all_ids, top_level_name,
                _flatten_attribute, fid,
            )
            own = _own_assignments(node)
            env = resolve_env([(v, classify(val)) for v, val in own], table_single)
            assigned = {v for v, _ in own}
            params = _params_of(node)

            for inner in ast.walk(node):
                if not (isinstance(inner, ast.Call)
                        and isinstance(inner.func, ast.Attribute)):
                    continue
                if inner.lineno not in site_lines:
                    continue
                recv = inner.func.value
                if not isinstance(recv, ast.Name):
                    continue
                name = recv.id
                if name in ("self", "cls") or name in env or name in assigned:
                    continue
                param_or_global += 1
                if name in params:
                    cats[_annotation_shape(params[name])] += 1
                else:
                    cats["global_or_closure"] += 1

    print(f"  name_param_or_global receivers: {param_or_global}")
    for cat, n in cats.most_common(top):
        pct = (100.0 * n / param_or_global) if param_or_global else 0
        print(f"    {cat:38} {n:7}  {pct:5.1f}%")
    return cats