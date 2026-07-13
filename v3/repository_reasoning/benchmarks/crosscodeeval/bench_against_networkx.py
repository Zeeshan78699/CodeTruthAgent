"""
bench_against_networkx.py
CodeTruth Agent V3 — Module 3 reasoning, DIFFERENTIAL benchmark vs networkx.

networkx is the reference implementation for graph algorithms. This harness runs
CodeTruth's advanced_reasoning AND networkx on the IDENTICAL internal edge set and
asserts exact agreement on:
  - strongly connected components (recursion clusters)
  - immediate dominators / chokepoints
  - forward reachability (descendants)
  - shortest path length

Agreement on real repos = external validation: CodeTruth's reasoning matches the
gold-standard implementation, deterministically. Any divergence is reported with
the exact node(s) so it can be investigated, not hidden.

Usage:
  from v3.repository_reasoning.bench_against_networkx import bench
  bench(fwd_index)                         # any forward call index
  # or convenience loaders:
  bench_python(repo) / bench_java(repo) / bench_go(repo) / bench_csharp(repo)
"""

import random
import networkx as nx

from v3.repository_reasoning.reasoning_queries import build_reverse_index
from v3.repository_reasoning import advanced_reasoning as AR


def _internal_digraph(fwd):
    g = nx.DiGraph()
    for u, outs in fwd.items():
        g.add_node(u)
        for v, kind, _l, _r in outs:
            if kind == "internal":
                g.add_edge(u, v)
    return g


def bench(fwd, sample=40, seed=7):
    g = _internal_digraph(fwd)
    rev = build_reverse_index(fwd)
    results = {}
    rng = random.Random(seed)
    nodes = list(g.nodes())

    # ---- 1. SCCs (recursion) ----
    ours_scc = {frozenset(c) for c in AR.strongly_connected_components(fwd) if len(c) > 1}
    nx_scc = {frozenset(c) for c in nx.strongly_connected_components(g) if len(c) > 1}
    results["scc_mutual"] = {
        "match": ours_scc == nx_scc, "ours": len(ours_scc), "networkx": len(nx_scc),
        "only_ours": [sorted(c) for c in (ours_scc - nx_scc)][:3],
        "only_nx": [sorted(c) for c in (nx_scc - ours_scc)][:3],
    }

    # ---- 2. reachability (descendants) on a sample ----
    mismatches_reach = []
    for n in rng.sample(nodes, min(sample, len(nodes))):
        ours = set(AR.reachable_from(n, fwd)["reachable"])
        ref = set(nx.descendants(g, n))
        if ours != ref:
            mismatches_reach.append({"node": n, "extra": sorted(ours - ref)[:3],
                                     "missing": sorted(ref - ours)[:3]})
    results["reachability"] = {"checked": min(sample, len(nodes)),
                               "match": not mismatches_reach,
                               "mismatches": mismatches_reach[:3]}

    # ---- 3. shortest path length on sampled reachable pairs ----
    mismatches_sp = []
    checked_sp = 0
    for _ in range(sample):
        if len(nodes) < 2:
            break
        a = rng.choice(nodes)
        desc = list(nx.descendants(g, a))
        if not desc:
            continue
        b = rng.choice(desc)
        checked_sp += 1
        ours = AR.shortest_path(a, b, fwd)["length"]
        ref = nx.shortest_path_length(g, a, b)
        if ours != ref:
            mismatches_sp.append({"from": a, "to": b, "ours": ours, "networkx": ref})
    results["shortest_path"] = {"checked": checked_sp,
                                "match": not mismatches_sp,
                                "mismatches": mismatches_sp[:3]}

    # ---- 4. dominators / chokepoints vs nx.immediate_dominators ----
    # build the same synthetic super-root nx-side and compare chokepoint SETS
    entries = [n for n in g.nodes() if g.in_degree(n) == 0]
    dom_mismatch = []
    checked_dom = 0
    if entries:
        ROOT = "<entry>"
        g2 = g.copy()
        for e in entries:
            g2.add_edge(ROOT, e)
        idom = nx.immediate_dominators(g2, ROOT)
        # full dominator set of a node = walk idom chain to ROOT
        def nx_doms(n):
            s, cur = set(), n
            while cur in idom and idom[cur] != cur:
                cur = idom[cur]; s.add(cur)
            return s - {ROOT}
        reach_from_root = set(idom.keys())
        for n in rng.sample(sorted(reach_from_root),
                            min(sample, len(reach_from_root))):
            if n == ROOT:
                continue
            checked_dom += 1
            ours = set(AR.chokepoints_for(n, fwd)["chokepoints"])
            ref = nx_doms(n)
            if ours != ref:
                dom_mismatch.append({"node": n, "extra": sorted(ours - ref)[:3],
                                     "missing": sorted(ref - ours)[:3]})
    results["dominators"] = {"checked": checked_dom, "match": not dom_mismatch,
                             "mismatches": dom_mismatch[:3]}

    results["_summary"] = {
        "nodes": g.number_of_nodes(), "internal_edges": g.number_of_edges(),
        "all_match": all(results[k].get("match", True)
                         for k in ("scc_mutual", "reachability",
                                   "shortest_path", "dominators")),
    }
    return results


# convenience loaders -------------------------------------------------------- #
def _fwd_python(repo):
    from v3.repository_reasoning.reasoning_engine import ReasoningEngine
    return ReasoningEngine(repo).resolve()["call_index"]

def _fwd_java(repo):
    return _from_report_java(repo)

def _from_report_java(repo):
    from v3.repository_reasoning.java_type_inference import enriched_query_surface
    return enriched_query_surface(repo).fwd

def _fwd_go(repo):
    from v3.repository_reasoning.language_adapter_bridge import query_repo_reparsed
    return query_repo_reparsed(repo, "go").fwd

def _fwd_csharp(repo):
    from v3.repository_reasoning.language_adapter_bridge import query_repo_reparsed
    return query_repo_reparsed(repo, "csharp").fwd

def bench_python(repo, **k): return bench(_fwd_python(repo), **k)
def bench_java(repo, **k):   return bench(_fwd_java(repo), **k)
def bench_go(repo, **k):     return bench(_fwd_go(repo), **k)
def bench_csharp(repo, **k): return bench(_fwd_csharp(repo), **k)
