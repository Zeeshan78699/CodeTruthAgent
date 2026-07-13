"""
multi_hop_analyzer.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Phase 3B.

Reasons over Module 2's call graph: "function A calls B calls C calls D, in this
structural order." This is a DIFFERENT capability from Phase 3A — it does not
resolve more types; it traverses the call structure we already have, optionally
annotating each hop with the receiver/return type resolved by Phase 3A.

Edge shape (from python_adapter call_graph):
    {caller: full_id, callee: full_id, lineno, resolution: <category>}

Chaining boundary (honest):
  * INTERNAL callees (project full_ids) continue a chain.
  * `<builtin>.*` and `<external>.*` callees are TERMINAL leaves — the chain ends
    there with that label; we do not traverse outside the repo.
  * Cycles are detected (visited set) and reported, never infinite-looped.
  * Depth is bounded (max_depth); chains longer than the bound are truncated and
    marked, never silently dropped.

Pure core (build_call_index / walk_chains) is unit-testable with synthetic edges;
the repo entry reuses return_type_inferencer's reconstruction. Frozen imports lazy.
"""

import ast
from collections import deque


def _callee_kind(callee):
    if callee.startswith("<builtin>."):
        return "builtin"
    if callee.startswith("<external>."):
        return "external"
    return "internal"


# ----------------------------------------------------------------------------- #
# PURE CORE -- synthetic-edge testable
# ----------------------------------------------------------------------------- #

def build_call_index(edges):
    """
    edges : iterable of {caller, callee, lineno, resolution}
    Returns {caller_id: [ (callee_id, kind, lineno, resolution), ... ]}.
    """
    index = {}
    for e in edges:
        kind = _callee_kind(e["callee"])
        index.setdefault(e["caller"], []).append(
            (e["callee"], kind, e.get("lineno"), e.get("resolution"))
        )
    return index


def walk_chains(start, call_index, max_depth=6, max_chains=200):
    """
    Bounded BFS of call chains from `start`. Returns a list of chains, each a list
    of hop dicts. Internal callees extend the chain; builtin/external terminate it.
    Cycle-safe (a node already on the current path is marked, not re-entered).

    Each chain is [{from, to, kind, lineno, resolution}, ...]. A chain that hits
    max_depth is tagged with a final {"truncated": True} marker hop.
    """
    chains = []
    # queue items: (current_node, path_edges, visited_on_path)
    q = deque([(start, [], frozenset({start}))])
    while q and len(chains) < max_chains:
        node, path, visited = q.popleft()
        outs = call_index.get(node)
        if not outs:
            if path:
                chains.append(path)
            continue
        extended = False
        for callee, kind, lineno, resolution in outs:
            hop = {"from": node, "to": callee, "kind": kind,
                   "lineno": lineno, "resolution": resolution}
            if kind != "internal":
                chains.append(path + [hop])           # terminal leaf
                extended = True
                continue
            if callee in visited:
                chains.append(path + [dict(hop, cycle=True)])  # cycle, stop
                extended = True
                continue
            if len(path) + 1 >= max_depth:
                chains.append(path + [hop, {"truncated": True}])
                extended = True
                continue
            q.append((callee, path + [hop], visited | {callee}))
            extended = True
        if not extended and path:
            chains.append(path)
    return chains


def annotate_with_types(chains, table_single):
    """For each internal hop whose callee is a function with a known return type,
    attach `callee_type`. Read-only; uses Phase 3A's table_single {fid: type_info}."""
    for chain in chains:
        for hop in chain:
            if hop.get("kind") == "internal" and hop.get("to") in table_single:
                hop["callee_type"] = table_single[hop["to"]]
    return chains


# ----------------------------------------------------------------------------- #
# Repo entry
# ----------------------------------------------------------------------------- #

def from_repo(repo_root, start=None, root_counts=None, max_depth=6):
    """
    Builds the call index for a repo and reports reach/chain statistics. If
    `start` (a function full_id) is given, prints the chains from it.
    """
    from v3.repository_graph.languages.python_adapter import PythonAdapter
    from v3.repository_reasoning.return_type_inferencer import (
        _reconstruct_inputs, build_return_type_table_v3, RESOLVED, INFERRED,
    )

    m2 = PythonAdapter().scan(repo_root=repo_root, file_paths=[])
    cg = m2["call_graph"]
    all_edges = [e for edges in cg.values() for e in edges]
    index = build_call_index(all_edges)

    internal = sum(1 for e in all_edges if _callee_kind(e["callee"]) == "internal")
    external = sum(1 for e in all_edges if _callee_kind(e["callee"]) == "external")
    builtin = sum(1 for e in all_edges if _callee_kind(e["callee"]) == "builtin")

    print(f"  total call edges                 : {len(all_edges)}")
    print(f"    internal (chainable)           : {internal}")
    print(f"    external (terminal)            : {external}")
    print(f"    builtin  (terminal)            : {builtin}")
    print(f"  callers with >=1 internal edge   : "
          f"{sum(1 for c, outs in index.items() if any(k=='internal' for _,k,_,_ in outs))}")

    if start:
        inp = _reconstruct_inputs(repo_root, root_counts)
        table_v3 = build_return_type_table_v3(
            inp["module_trees"], inp["function_graph"], inp["class_methods_index"],
            inp["import_alias_maps"], inp["global_class_methods"],
            framework_kb=inp["framework_kb"],
            real_class_names_index=inp["real_class_names_index"],
        )
        table_single = {fid: rec["type"] for fid, rec in table_v3.items()
                        if rec["label"] in (RESOLVED, INFERRED)}
        chains = annotate_with_types(
            walk_chains(start, index, max_depth=max_depth), table_single)
        print(f"\n  chains from {start}: {len(chains)}")
        for ch in chains[:10]:
            path = " -> ".join(h.get("to", "?") for h in ch if "to" in h)
            tail = ""
            if ch and ch[-1].get("cycle"):
                tail = "  [cycle]"
            elif ch and ch[-1].get("truncated"):
                tail = "  [truncated]"
            print(f"    {start} -> {path}{tail}")
        return index, chains
    return index, None
