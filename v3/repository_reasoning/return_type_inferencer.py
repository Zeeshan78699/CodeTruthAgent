"""
return_type_inferencer.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Phase 3A, Step 1.

Extends the FROZEN Module 2 return-type inference
(v3/repository_graph/languages/type_inference.py :: build_return_type_table)
with exactly the two gaps that file names in its own docstring:

  1. TRANSITIVE returns   def a(): return b()   resolves once b()'s return
                          type is known. The frozen table "intentionally does
                          NOT do transitive propagation".
  2. MULTI-PATH returns   a function returning >=2 KNOWN types is recorded as a
                          bounded AMBIGUOUS set, instead of being dropped (the
                          frozen result() discards anything with len != 1).

Discipline (identical to type_inference.py's stance on CallResolver):
  * The frozen build_return_type_table is called FIRST and its every result is
    preserved byte-for-byte (RESOLVED, single determinate type). This module
    only ADDS entries the frozen table left absent. It never relabels or
    overwrites a frozen result.
  * Truth Boundary: a function resolves only when EVERY return classifies to a
    known type (directly, or transitively to an already-resolved function).
    Any bare return, any unknown expression, or any dependency on an
    unresolvable/poisoned function leaves the function ABSENT from the table -
    never guessed, never None-as-answer.
  * No numeric/HIGH-MEDIUM confidence. Output carries one categorical label:
    RESOLVED (frozen single) / INFERRED (transitive single) / AMBIGUOUS (>=2
    known types).

The frozen engine is imported LAZILY (inside the functions that need it) so the
pure resolution core (_fixed_point / _label_table) imports with only `ast` and
stays unit-testable without the rest of the repo.
"""

import ast


# ----------------------------------------------------------------------------- #
# Resolution record + labels  (see MODULE3_COMPONENT_CONTRACTS.md)
# ----------------------------------------------------------------------------- #

RESOLVED = "RESOLVED"          # one type, frozen-proven (direct constructor/annotation/single return)
INFERRED = "INFERRED"          # one type, traced transitively through 1..N calls
AMBIGUOUS = "AMBIGUOUS"        # >=2 known types, all enumerated as a bounded set


def _record(type_or_list, label, evidence):
    """Build one ResolvedType record. `type` is a single type_info tuple for
    RESOLVED/INFERRED, or a list of type_info tuples for AMBIGUOUS."""
    return {"type": type_or_list, "label": label, "evidence": evidence}


# ----------------------------------------------------------------------------- #
# PURE CORE  -- no AST, no frozen engine -- fully unit-testable
#
# Inputs:
#   frozen_seed : {full_id: type_info}            from build_return_type_table
#   atoms       : {full_id: [atom, ...]}          per-function return atoms, where
#                 atom is one of:
#                     ("type", type_info)   a return that classifies to a known type
#                     ("call", target_id)   a return of the form `target(...)`
#                     ("unknown",)          a bare/None/unclassifiable return (POISON)
#   type_info is the existing Module 2 shape: ("builtin", name) | ("class", mod, cls)
# ----------------------------------------------------------------------------- #

def _fixed_point(frozen_seed, atoms, max_passes=5):
    """
    Resolve transitive + multi-path return types to a fixed point.

    Returns (determinate, used_call) where:
        determinate : {full_id: frozenset(type_info)}   resolved return-type set
        used_call   : {full_id: bool}                    True if any ("call",..) atom
                                                          was needed (=> INFERRED, not RESOLVED)

    A function is POISONED (permanently undetermined) if any of its atoms is
    ("unknown",) or depends on a poisoned function. Poison propagates, so a
    function returning an unresolvable function is itself unresolvable - the
    honest result, never a guess. Cycles that never ground out simply stay
    absent (the loop terminates when a full pass changes nothing).
    """
    determinate = {fid: frozenset({info}) for fid, info in frozen_seed.items()}
    used_call = {fid: False for fid in frozen_seed}

    poisoned = {fid for fid, a in atoms.items()
                if any(atom[0] == "unknown" for atom in a)}

    changed = True
    passes = 0
    while changed and passes < max_passes:
        changed = False
        passes += 1
        for fid, a in atoms.items():
            if fid in determinate or fid in poisoned:
                continue
            if not a:
                continue  # no return statements -> undetermined, leave absent

            collected = set()
            pending = False
            uc = False
            dead = False
            for atom in a:
                kind = atom[0]
                if kind == "type":
                    collected.add(atom[1])
                elif kind == "call":
                    target = atom[1]
                    if target in poisoned:
                        dead = True
                        break
                    elif target in determinate:
                        collected |= determinate[target]
                        uc = True
                    else:
                        pending = True
                else:  # safety: any other shape is unknown
                    dead = True
                    break

            if dead:
                poisoned.add(fid)
                changed = True
                continue
            if pending:
                continue  # a dependency isn't resolved yet; retry next pass
            if collected:
                determinate[fid] = frozenset(collected)
                used_call[fid] = uc
                changed = True

    return determinate, used_call


def _label_table(frozen_seed, determinate, used_call):
    """
    Turn the resolved sets into categorical ResolvedType records, additively:
      * frozen_seed entries  -> RESOLVED, type preserved exactly (never relabeled)
      * non-seed, 1 type     -> INFERRED  (must have used a transitive call)
      * non-seed, >=2 types  -> AMBIGUOUS (bounded set)
    """
    table = {}
    for fid, types in determinate.items():
        ordered = sorted(types, key=repr)
        if fid in frozen_seed:
            # Preserve the frozen single result byte-for-byte.
            table[fid] = _record(frozen_seed[fid], RESOLVED,
                                  f"frozen build_return_type_table: {fid}")
        elif len(ordered) == 1:
            table[fid] = _record(ordered[0], INFERRED,
                                 f"transitive return resolution: {fid}")
        else:
            table[fid] = _record(ordered, AMBIGUOUS,
                                 f"multi-path/transitive returns: {fid}")
    return table


# ----------------------------------------------------------------------------- #
# AST GLUE  -- extracts return atoms, reusing the frozen _ReturnClassifier for
# the type case so every Module 2 fix (scope-contamination guard, import
# resolution, framework_kb) is preserved. Only the ("call", target) detection
# is new.
# ----------------------------------------------------------------------------- #

def _build_function_indexes(function_graph):
    """
    Returns:
        all_ids        : set of every function full_id in the repo
        top_level_name : {module: {simple_name: full_id}} for MODULE-LEVEL funcs only
                         (a func is module-level iff its id == f"{module}.{simple}").
    Nested functions are deliberately NOT addressable as call targets - resolving
    a return through a closure is an honest scope limit of this increment.
    """
    all_ids = set()
    top_level_name = {}
    for module, funcs in function_graph.items():
        names = {}
        for f in funcs:
            fid = f["id"]
            all_ids.add(fid)
            simple = fid.rsplit(".", 1)[-1]
            if fid == f"{module}.{simple}":
                names[simple] = fid
        top_level_name[module] = names
    return all_ids, top_level_name


def _resolve_call_target(value, module_name, import_alias_map,
                         all_ids, top_level_name, flatten_attribute):
    """
    For a return value of the form `name(...)` or `pkg.mod.func(...)`, return the
    callee's full_id if (and only if) it is a known project function. Otherwise
    None (the caller will treat the atom as ("unknown",)).
    """
    if not isinstance(value, ast.Call):
        return None
    func = value.func

    if isinstance(func, ast.Name):
        name = func.id
        # same-module top-level function
        local = top_level_name.get(module_name, {}).get(name)
        if local:
            return local
        # imported function: alias -> "pkg.mod.func", accept only if it is a
        # real function id in the repo
        target = import_alias_map.get(name)
        if target and target in all_ids:
            return target
        return None

    if isinstance(func, ast.Attribute):
        root, rest = flatten_attribute(func)
        if root and rest and root in import_alias_map:
            full = import_alias_map[root] + "." + ".".join(rest)
            if full in all_ids:
                return full
        return None

    return None


def _collect_atoms(module_trees, function_graph, class_methods_index,
                   import_alias_maps, global_class_methods,
                   framework_kb, real_class_names_index):
    """
    Build {full_id: [atom, ...]} for every function, reusing the frozen
    _ReturnClassifier for the type case and adding ("call", target) detection.
    """
    # Lazy import: keeps the pure core above import-clean for unit tests.
    from v3.repository_graph.type_inference import _ReturnClassifier
    from v3.repository_graph.call_graph import _flatten_attribute

    all_ids, top_level_name = _build_function_indexes(function_graph)

    id_by_location = {}
    for module_name, funcs in function_graph.items():
        for f in funcs:
            id_by_location[(module_name, f["lineno"])] = f["id"]

    class _AtomCollector(_ReturnClassifier):
        """Inherits the frozen depth-guard (nested defs excluded) and _classify;
        records atoms instead of collapsing to a single result()."""
        def __init__(self, *a, current_fid=None, **k):
            super().__init__(*a, **k)
            self.atoms = []
            self._current_fid = current_fid

        def visit_Return(self, node):
            value = node.value
            if value is None:
                self.atoms.append(("unknown",))
                return
            # `return await foo()` has the same return type as `return foo()`.
            if isinstance(value, ast.Await):
                value = value.value
            classified = self._classify(value)
            if classified is not None:
                self.atoms.append(("type", classified))
                return
            # `return self.method()` / `return cls.method()`: inside a method,
            # the receiver IS the enclosing class, so the target is
            # <EnclosingClass>.method - constructed from this function's own id.
            # Only emitted when that exact method id really exists (same-class
            # methods only; inherited methods are an honest miss for now).
            if (isinstance(value, ast.Call)
                    and isinstance(value.func, ast.Attribute)
                    and isinstance(value.func.value, ast.Name)
                    and value.func.value.id in ("self", "cls")
                    and self._current_fid):
                cls_prefix = self._current_fid.rsplit(".", 1)[0]
                target = f"{cls_prefix}.{value.func.attr}"
                if target in all_ids:
                    self.atoms.append(("call", target))
                    return
            target = _resolve_call_target(
                value, self.module_name, self.import_alias_map,
                all_ids, top_level_name, _flatten_attribute,
            )
            if target is not None:
                self.atoms.append(("call", target))
            else:
                self.atoms.append(("unknown",))

    atoms = {}
    for module_name, tree in module_trees.items():
        cm = class_methods_index.get(module_name, {})
        iam = import_alias_maps.get(module_name, {})
        rcn = (real_class_names_index.get(module_name)
               if real_class_names_index is not None else None)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fid = id_by_location.get((module_name, node.lineno))
            if not fid:
                continue
            collector = _AtomCollector(
                module_name, cm, iam, global_class_methods,
                framework_kb=framework_kb,
                real_class_names=rcn,
                global_real_class_names=real_class_names_index,
                current_fid=fid,
            )
            collector.visit(node)
            atoms[fid] = collector.atoms
    return atoms


# ----------------------------------------------------------------------------- #
# PUBLIC API
# ----------------------------------------------------------------------------- #

def build_return_type_table_v3(module_trees, function_graph, class_methods_index,
                               import_alias_maps, global_class_methods, *,
                               framework_kb=None, real_class_names_index=None,
                               max_passes=5):
    """
    Returns {full_function_id: ResolvedType} extending the frozen
    build_return_type_table. Signature mirrors the frozen function (plus
    max_passes) so callers pass exactly the same indexes.

    ResolvedType = {"type": type_info | [type_info,...], "label": <categorical>,
                    "evidence": str}. Functions whose return type cannot be
    proven are ABSENT (treat absence as "don't know").
    """
    from v3.repository_graph.type_inference import build_return_type_table

    frozen_seed = build_return_type_table(
        module_trees, function_graph, class_methods_index,
        import_alias_maps, global_class_methods,
        framework_kb=framework_kb,
        real_class_names_index=real_class_names_index,
    )

    atoms = _collect_atoms(
        module_trees, function_graph, class_methods_index,
        import_alias_maps, global_class_methods,
        framework_kb, real_class_names_index,
    )

    determinate, used_call = _fixed_point(frozen_seed, atoms, max_passes=max_passes)
    return _label_table(frozen_seed, determinate, used_call)


def _reconstruct_inputs(repo_root, root_counts=None):
    """
    Reconstructs Stage-A inputs from a repository, reusing the SAME frozen
    Stage-A functions as type_inference.build_repository_call_graph_enhanced -
    only the orchestration is duplicated, never the parsing/resolution logic.

    Uses the SAME effective package root that python_adapter detects (D-008),
    so module names line up byte-for-byte with PythonAdapter().scan()'s
    `unresolved` entries - otherwise D-008-corrected repos (ccxt, pydicom)
    produce module names that never match the scan and nothing aligns.

    Returns the kwargs dict expected by build_return_type_table_v3, plus the
    effective_root actually used.
    """
    from v3.repository_graph.graph_engine import find_python_files
    from v3.repository_graph.module_graph import module_name_from_path
    from v3.repository_graph.function_graph import build_function_graph_for_module
    from v3.repository_graph.class_graph import build_class_graph_for_module
    from v3.repository_graph.import_graph import collect_raw_imports
    from v3.repository_graph.call_graph import (
        build_import_alias_map, build_global_symbol_index,
    )
    from v3.repository_graph.module_graph import build_module_graph
    from v3.repository_graph.package_root import (
        detect_package_root_and_counts, _collect_absolute_import_roots,
    )
    from v3.repository_graph.framework_knowledge_base import build_active_knowledge_base
    from v3.repository_graph.type_inference import (
        build_real_class_names_index, augment_class_index_with_zero_method_classes,
    )

    # D-008: detect the true package root, exactly as python_adapter does.
    effective_root, detected_counts = detect_package_root_and_counts(repo_root)
    if root_counts is None:
        root_counts = detected_counts

    py_files = find_python_files(effective_root)
    if not root_counts:
        root_counts = _collect_absolute_import_roots(py_files)
    framework_kb = build_active_knowledge_base(root_counts)

    module_trees, function_graph, class_graph, raw_imports = {}, {}, {}, {}
    for filepath in py_files:
        mod_name = module_name_from_path(effective_root, filepath)
        if mod_name == "":
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)
        except (SyntaxError, UnicodeDecodeError):
            continue
        module_trees[mod_name] = tree
        function_graph[mod_name] = build_function_graph_for_module(mod_name, tree)
        class_graph[mod_name] = build_class_graph_for_module(mod_name, tree)
        raw_imports[mod_name] = collect_raw_imports(mod_name, tree)

    module_graph = build_module_graph(effective_root, py_files)
    import_alias_maps = {}
    for mod_name, raw in raw_imports.items():
        is_pkg = module_graph.get(mod_name, {}).get("is_package", False)
        import_alias_maps[mod_name] = build_import_alias_map(mod_name, raw, is_package=is_pkg)

    _, class_methods_index, _ = build_global_symbol_index(function_graph, class_graph)
    class_methods_index = augment_class_index_with_zero_method_classes(
        class_graph, class_methods_index
    )
    real_class_names_index = build_real_class_names_index(class_graph)

    return {
        "module_trees": module_trees,
        "function_graph": function_graph,
        "class_methods_index": class_methods_index,
        "import_alias_maps": import_alias_maps,
        "global_class_methods": class_methods_index,
        "framework_kb": framework_kb,
        "real_class_names_index": real_class_names_index,
        "effective_root": effective_root,
    }


def from_repo(repo_root, root_counts=None, max_passes=5):
    """Run build_return_type_table_v3 over a repository. Returns {full_id: ResolvedType}."""
    inp = _reconstruct_inputs(repo_root, root_counts)
    return build_return_type_table_v3(
        inp["module_trees"], inp["function_graph"], inp["class_methods_index"],
        inp["import_alias_maps"], inp["global_class_methods"],
        framework_kb=inp["framework_kb"],
        real_class_names_index=inp["real_class_names_index"],
        max_passes=max_passes,
    )


def from_repo_debug(repo_root, root_counts=None, max_passes=5):
    """
    READ-ONLY diagnostic. Reports what the atom collector found, so we can tell
    'genuinely zero new resolutions' apart from 'new code paths not firing'.
    Returns a dict of counts (and prints them).
    """
    inp = _reconstruct_inputs(repo_root, root_counts)

    from v3.repository_graph.type_inference import build_return_type_table
    frozen_seed = build_return_type_table(
        inp["module_trees"], inp["function_graph"], inp["class_methods_index"],
        inp["import_alias_maps"], inp["global_class_methods"],
        framework_kb=inp["framework_kb"],
        real_class_names_index=inp["real_class_names_index"],
    )
    atoms = _collect_atoms(
        inp["module_trees"], inp["function_graph"], inp["class_methods_index"],
        inp["import_alias_maps"], inp["global_class_methods"],
        inp["framework_kb"], inp["real_class_names_index"],
    )
    determinate, used_call = _fixed_point(frozen_seed, atoms, max_passes=max_passes)
    table = _label_table(frozen_seed, determinate, used_call)

    nonseed = [f for f in atoms if f not in frozen_seed]

    def kinds(f):
        return [a[0] for a in atoms[f]]

    # would-be AMBIGUOUS: a non-seed function whose returns are ALL typed (no
    # call/unknown) but resolve to >=2 distinct types. Independent of call-target
    # resolution, so this isolates a multi-path bug from a call-resolution bug.
    would_ambiguous = [
        f for f in nonseed
        if atoms[f] and all(k == "type" for k in kinds(f))
        and len({a[1] for a in atoms[f] if a[0] == "type"}) >= 2
    ]
    with_call_atom = [f for f in nonseed if "call" in kinds(f)]
    call_targets_in_seed = [
        f for f in with_call_atom
        if any(a[0] == "call" and a[1] in frozen_seed for a in atoms[f])
    ]
    poisoned = [f for f in nonseed if "unknown" in kinds(f)]
    empty = [f for f in nonseed if not atoms[f]]

    # is the call-target resolver even producing 'call' atoms anywhere?
    total_call_atoms = sum(kinds(f).count("call") for f in atoms)
    total_type_atoms = sum(kinds(f).count("type") for f in atoms)

    report = {
        "functions_total": len(atoms),
        "frozen_seed (RESOLVED)": len(frozen_seed),
        "nonseed": len(nonseed),
        "nonseed_empty (no returns)": len(empty),
        "nonseed_poisoned (>=1 unknown)": len(poisoned),
        "nonseed_would_be_AMBIGUOUS (>=2 typed returns)": len(would_ambiguous),
        "nonseed_with_call_atom": len(with_call_atom),
        "nonseed_call_target_in_seed": len(call_targets_in_seed),
        "TOTAL call atoms across repo": total_call_atoms,
        "TOTAL type atoms across repo": total_type_atoms,
        "FINAL INFERRED": sum(1 for v in table.values() if v["label"] == INFERRED),
        "FINAL AMBIGUOUS": sum(1 for v in table.values() if v["label"] == AMBIGUOUS),
    }
    for k, v in report.items():
        print(f"  {k:48} {v}")
    return report


# ----------------------------------------------------------------------------- #
# POISON BREAKDOWN  (read-only diagnostic)
# Categorises the return shapes of value-returning functions we could NOT type,
# so the next component is chosen from evidence, not assumption.
# ----------------------------------------------------------------------------- #

def _own_returns(func_node):
    """All `return` nodes belonging to THIS function (nested defs/lambdas excluded)."""
    out = []
    def rec(n):
        for child in ast.iter_child_nodes(n):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            if isinstance(child, ast.Return):
                out.append(child)
            rec(child)
    rec(func_node)
    return out


def _categorize_return(value, _await=False):
    pre = "await_" if _await else ""
    if isinstance(value, ast.Await):
        return _categorize_return(value.value, _await=True)
    if isinstance(value, ast.Name):
        return pre + "bare_var"
    if isinstance(value, ast.Attribute):
        base = value.value
        if isinstance(base, ast.Name) and base.id in ("self", "cls"):
            return pre + "self_attr"
        return pre + "other_attr"
    if isinstance(value, ast.Call):
        f = value.func
        if isinstance(f, ast.Attribute):
            if isinstance(f.value, ast.Name) and f.value.id in ("self", "cls"):
                return pre + "self_method_call"
            return pre + "other_method_call"
        if isinstance(f, ast.Name):
            return pre + "func_call(unresolved)"
        return pre + "call_other"
    if isinstance(value, ast.Subscript):
        return pre + "subscript"
    if isinstance(value, ast.Constant):
        return pre + "constant"
    if isinstance(value, (ast.List, ast.Dict, ast.Set, ast.ListComp,
                          ast.DictComp, ast.SetComp, ast.GeneratorExp, ast.Tuple)):
        return pre + "literal_container"
    if isinstance(value, ast.IfExp):
        return pre + "ternary"
    return pre + "other:" + type(value).__name__


def from_repo_poison_breakdown(repo_root, root_counts=None, max_passes=5, top=18):
    """Counts the return shapes of functions we couldn't type. Prints the ranking."""
    from collections import Counter
    inp = _reconstruct_inputs(repo_root, root_counts)
    table = build_return_type_table_v3(
        inp["module_trees"], inp["function_graph"], inp["class_methods_index"],
        inp["import_alias_maps"], inp["global_class_methods"],
        framework_kb=inp["framework_kb"],
        real_class_names_index=inp["real_class_names_index"], max_passes=max_passes,
    )
    resolved_ids = set(table)

    id_by_location = {}
    for module_name, funcs in inp["function_graph"].items():
        for f in funcs:
            id_by_location[(module_name, f["lineno"])] = f["id"]

    cats = Counter()
    poisoned_fns = 0
    for module_name, tree in inp["module_trees"].items():
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            fid = id_by_location.get((module_name, node.lineno))
            if not fid or fid in resolved_ids:
                continue
            valued = [r for r in _own_returns(node) if r.value is not None]
            if not valued:
                continue
            poisoned_fns += 1
            for r in valued:
                cats[_categorize_return(r.value)] += 1

    total = sum(cats.values())
    print(f"  poisoned value-returning functions: {poisoned_fns}")
    print(f"  total untyped return statements:    {total}")
    for cat, n in cats.most_common(top):
        pct = (100.0 * n / total) if total else 0
        print(f"    {cat:28} {n:7}  {pct:5.1f}%")
    return cats