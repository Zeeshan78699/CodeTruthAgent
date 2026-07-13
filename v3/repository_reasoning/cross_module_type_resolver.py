"""
cross_module_type_resolver.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Phase 3A, Step 2.

The repo-wide table_v3 already resolves a function imported with a DIRECT alias
(`from a.b import f` -> `a.b.f`, looked up in the table). What it does NOT do is
follow RE-EXPORT chains through package __init__ files:

    # django/http/__init__.py
    from django.http.response import HttpResponse      # re-export
    # django/shortcuts.py
    from django.http import HttpResponse               # alias -> django.http.HttpResponse
    HttpResponse(...)                                  # but the class is DEFINED at
                                                       # django.http.response.HttpResponse

The alias map stops at the re-export id (`django.http.HttpResponse`); the symbol
is actually defined one or more hops deeper. This component builds the re-export
graph from every module's import alias map and resolves an alias to its DEFINING
id, so table_v3 lookups (and class-constructor checks) hit.

Output: a {reexport_id -> defining_id} map, plus a measured count of how many
previously-unresolved `name_call_unresolved` / `attribute_call` sites this newly
grounds. Additive, categorical, frozen imports lazy. Cycle-safe (bounded hops).
"""

import ast

from v3.repository_reasoning.return_type_inferencer import (
    RESOLVED, INFERRED, AMBIGUOUS,
    _reconstruct_inputs, build_return_type_table_v3, _build_function_indexes,
)

MAX_HOPS = 5   # honest bound; chains longer than this -> left unresolved


# ----------------------------------------------------------------------------- #
# PURE CORE -- unit-testable: resolve a name to its defining id by following
# re-export edges, with cycle safety and a hop bound.
# ----------------------------------------------------------------------------- #

def resolve_reexport(symbol_id, reexport_edges, defined_ids, max_hops=MAX_HOPS):
    """
    symbol_id      : "module.path.Name" an alias points at (may be a re-export)
    reexport_edges : {reexport_id: target_id}  (one hop, built from alias maps)
    defined_ids    : set of ids that are actually DEFINED (functions/classes)

    Returns the defining id if the chain terminates at a defined symbol within
    max_hops, else None. Never loops (visited set), never guesses.
    """
    if symbol_id in defined_ids:
        return symbol_id
    seen = set()
    cur = symbol_id
    for _ in range(max_hops):
        if cur in seen:
            return None           # cycle
        seen.add(cur)
        nxt = reexport_edges.get(cur)
        if nxt is None:
            return None           # chain ends without reaching a definition
        if nxt in defined_ids:
            return nxt
        cur = nxt
    return None                   # exceeded hop bound


# ----------------------------------------------------------------------------- #
# Build the re-export graph from import alias maps
# ----------------------------------------------------------------------------- #

def build_reexport_edges(import_alias_maps, defined_ids):
    """
    A module that imports `Name` and (by being a package __init__ or otherwise)
    makes it importable under its OWN module path is re-exporting it. We model
    this from the alias maps: for module M, alias `local -> target`, the symbol
    is reachable as `M.local`. If `M.local` is NOT itself a defined id but
    `target` is closer to a definition, record edge `M.local -> target`.

    This captures the `from .response import HttpResponse` in `django/http/
    __init__.py` making `django.http.HttpResponse` an alias of
    `django.http.response.HttpResponse`.
    """
    edges = {}
    for module_name, amap in import_alias_maps.items():
        for local, target in amap.items():
            reexport_id = f"{module_name}.{local}"
            if reexport_id == target:
                continue
            if reexport_id in defined_ids:
                continue  # actually defined here, not a re-export
            edges[reexport_id] = target
    return edges


def build_defining_index(inp):
    """All ids that are DEFINED (functions + classes), to terminate chains on."""
    defined = set()
    for module_name, funcs in inp["function_graph"].items():
        for f in funcs:
            defined.add(f["id"])
    rcn = inp.get("real_class_names_index") or {}
    for module_name, classnames in rcn.items():
        for cn in classnames:
            defined.add(f"{module_name}.{cn}")
    return defined


# ----------------------------------------------------------------------------- #
# Repo entry + measured payoff
# ----------------------------------------------------------------------------- #

def from_repo(repo_root, root_counts=None, max_passes=5):
    """
    Builds the re-export resolution map and measures how many of Module 2's
    `name_call_unresolved` sites (calls to a name not found locally/imported)
    now ground to a defining id via a re-export chain. Prints the breakdown.
    """
    from v3.repository_graph.languages.python_adapter import PythonAdapter

    inp = _reconstruct_inputs(repo_root, root_counts)
    defined_ids = build_defining_index(inp)
    reexport_edges = build_reexport_edges(inp["import_alias_maps"], defined_ids)

    # Resolve every re-export id to its defining id (the deliverable map).
    resolved_map = {}
    multi_hop = 0
    for rid in reexport_edges:
        target = resolve_reexport(rid, reexport_edges, defined_ids, MAX_HOPS)
        if target is not None and target != rid:
            resolved_map[rid] = target
            if reexport_edges.get(rid) != target:
                multi_hop += 1

    # Measure: how many alias targets that were NOT defined ids become defined
    # via the chain. This is the set of imported symbols that previously looked
    # unresolvable but now point at a real definition.
    newly_grounded = 0
    for module_name, amap in inp["import_alias_maps"].items():
        for local, target in amap.items():
            if target in defined_ids:
                continue
            chained = resolve_reexport(target, reexport_edges, defined_ids, MAX_HOPS)
            if chained is not None:
                newly_grounded += 1

    print(f"  modules                                 : {len(inp['import_alias_maps'])}")
    print(f"  defined ids (functions + classes)       : {len(defined_ids)}")
    print(f"  re-export edges built                   : {len(reexport_edges)}")
    print(f"  re-exports resolved to a definition     : {len(resolved_map)}")
    print(f"  ...of which multi-hop (>1 chain step)   : {multi_hop}")
    print(f"  >>> imported symbols newly grounded     : {newly_grounded}")
    return resolved_map
