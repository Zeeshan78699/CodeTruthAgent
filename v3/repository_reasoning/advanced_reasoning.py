"""
advanced_reasoning.py
CodeTruth Agent V3 — Module 3B, ADVANCED deterministic reasoning.

Additive, language-agnostic: operates on the same forward call index
({caller: [(callee, kind, lineno, resolution)]}) that reasoning_queries uses, so
it works on ANY standard-shape adapter (Python validated; Java validated via the
language bridge). Every result is EXACT (classic graph algorithms, no heuristics,
no probability, no scores) and carries a `boundary` field.

Capabilities beyond the basic 6 queries:
  - recursion_clusters : cycles (mutual recursion) + self-loops (direct recursion)
                         via iterative Tarjan SCC (no recursion-depth limit)
  - impact_by_depth    : reverse blast radius with propagation DEPTH per caller
                         (direct vs transitive made explicit)
  - chokepoints_for    : dominator analysis — functions that EVERY path from an
                         entry point must pass through to reach X ("mandatory
                         predecessors"); the rigorous "what must run before X"
  - hotspots           : fan-in / fan-out centrality (most-depended-on, most-
                         depending) — exact in/out degree over internal edges
  - reachable_from /
    shortest_path      : forward reachability + a concrete shortest call path

Discipline: internal edges only (external/builtin/dynamic dispatch are honest
blind spots, stated in every boundary). Bounded iteration. Cycle-safe.
"""

from collections import deque, defaultdict


# --------------------------------------------------------------------------- #
# shared: internal adjacency (chainable edges only)
# --------------------------------------------------------------------------- #
def _internal_adj(forward_index):
    adj = {}
    nodes = set(forward_index.keys())
    for u, outs in forward_index.items():
        adj.setdefault(u, [])
        for v, kind, _lineno, _res in outs:
            if kind == "internal":
                adj[u].append(v)
                nodes.add(v)
    for n in nodes:
        adj.setdefault(n, [])
    return adj


def _internal_preds(adj):
    preds = defaultdict(set)
    for u in adj:
        for v in adj[u]:
            preds[v].add(u)
    return preds


# --------------------------------------------------------------------------- #
# 1. Strongly Connected Components (iterative Tarjan) -> recursion / cycles
# --------------------------------------------------------------------------- #
def strongly_connected_components(forward_index):
    adj = _internal_adj(forward_index)
    counter = [0]
    index, low, onstack, stack, result = {}, {}, {}, [], []

    for start in adj:
        if start in index:
            continue
        work = [(start, 0)]
        while work:
            v, pi = work[-1]
            if pi == 0:
                index[v] = low[v] = counter[0]
                counter[0] += 1
                stack.append(v)
                onstack[v] = True
            recursed = False
            nbrs = adj[v]
            for j in range(pi, len(nbrs)):
                w = nbrs[j]
                if w not in index:
                    work[-1] = (v, j + 1)
                    work.append((w, 0))
                    recursed = True
                    break
                elif onstack.get(w):
                    low[v] = min(low[v], index[w])
            if recursed:
                continue
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    onstack[w] = False
                    comp.append(w)
                    if w == v:
                        break
                result.append(comp)
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
    return result


def recursion_clusters(forward_index):
    adj = _internal_adj(forward_index)
    sccs = strongly_connected_components(forward_index)
    mutual = sorted([sorted(c) for c in sccs if len(c) > 1], key=lambda c: -len(c))
    direct = sorted(n for n in adj if n in adj[n])

    # Precision guard (deterministic): a self-loop on a method whose short name
    # is a well-known delegation target (equals/hashCode/toString/iterator/of/
    # close/read/write/...) is very likely an adapter NAME-COLLISION artifact —
    # e.g. `this.field.equals(x)` mis-bound to the enclosing equals() because the
    # same-file resolver matched on bare name. We do NOT drop these (the edge is
    # real as far as the graph knows); we SEPARATE them so the result can't be
    # misread as "N recursive algorithms". This is honest labeling, not a fix to
    # the upstream adapter.
    _DELEGATION_NAMES = {
        "equals", "hashcode", "tostring", "iterator", "of", "close", "read",
        "write", "isopen", "length", "size", "charat", "subsequence", "stream",
        "isempty", "get", "from", "run", "start", "stop", "filter", "execute",
    }
    likely_real, likely_artifact = [], []
    for n in direct:
        short = n.rsplit(".", 1)[-1].lower()
        (likely_artifact if short in _DELEGATION_NAMES else likely_real).append(n)

    return {
        "query": "recursion_clusters",
        "mutual_recursion": mutual,              # 2+ functions forming a call cycle
        "direct_recursion": direct,              # all self-loops (unchanged)
        "direct_recursion_likely_real": likely_real,
        "direct_recursion_likely_name_artifact": likely_artifact,
        "count": len(mutual) + len(direct),
        "boundary": "internal call edges only; cycles via external libraries or "
                    "dynamic dispatch are not visible. Self-loops on common "
                    "delegation names (equals/hashCode/toString/...) are flagged "
                    "as LIKELY adapter name-collision artifacts, not verified "
                    "recursion — confirm against source before relying on them.",
    }


# --------------------------------------------------------------------------- #
# 2. Depth-annotated reverse blast radius
# --------------------------------------------------------------------------- #
def impact_by_depth(x, reverse_index, max_depth=25, max_nodes=50000):
    """Reverse BFS from x; each affected caller tagged with its DEPTH (1 = direct
    caller, 2+ = transitive). Sharper than a flat impact list."""
    depth = {x: 0}
    q = deque([x])
    layers = defaultdict(list)
    while q and len(depth) < max_nodes:
        cur = q.popleft()
        d = depth[cur]
        if d >= max_depth:
            continue
        for caller in reverse_index.get(cur, set()):
            if caller not in depth:
                depth[caller] = d + 1
                layers[d + 1].append(caller)
                q.append(caller)
    return {
        "query": "impact_by_depth", "target": x,
        "by_depth": {k: sorted(v) for k, v in sorted(layers.items())},
        "direct_count": len(layers.get(1, [])),
        "transitive_count": sum(len(v) for k, v in layers.items() if k > 1),
        "total": sum(len(v) for v in layers.values()),
        "label": "CALL_REACHABLE",
        "boundary": "in-repo call-reachability with propagation depth; NOT "
                    "semantic breakage; external/dynamic callers not included",
    }


# --------------------------------------------------------------------------- #
# 3. Dominator analysis -> chokepoints ("what must run before X")
# --------------------------------------------------------------------------- #
ENTRY = "<entry>"


def _immediate_dominators(forward_index):
    """Cooper-Harvey-Kennedy immediate dominators from a synthetic super-root
    connected to every entry node (a node with no internal callers).

    Near-linear time, O(n) memory: stores ONE immediate dominator per node, not a
    full dominator set per node (the previous set-intersection version was O(n^2)
    memory and exhausted RAM on very large graphs, e.g. the 180K-node Go compiler).
    Same results, scalable. Returns (idom, ENTRY, reachable_set).
    """
    adj = _internal_adj(forward_index)
    preds = _internal_preds(adj)
    nodes = set(adj.keys())
    entries = [n for n in nodes if not preds.get(n)]

    succ = {ENTRY: list(entries)}
    for u in adj:
        succ[u] = adj[u]
    p2 = {n: set(preds.get(n, ())) for n in nodes}
    for e in entries:
        p2.setdefault(e, set()).add(ENTRY)
    p2[ENTRY] = set()

    # iterative DFS postorder from the super-root
    postorder, visited = [], {ENTRY}
    stack = [(ENTRY, iter(succ.get(ENTRY, [])))]
    while stack:
        node, it = stack[-1]
        advanced = False
        for child in it:
            if child not in visited:
                visited.add(child)
                stack.append((child, iter(succ.get(child, []))))
                advanced = True
                break
        if not advanced:
            postorder.append(node)
            stack.pop()
    pnum = {n: i for i, n in enumerate(postorder)}   # higher = closer to root
    reachable = set(visited)
    rpo = list(reversed(postorder))

    idom = {ENTRY: ENTRY}

    def intersect(b1, b2):
        f1, f2 = b1, b2
        while f1 != f2:
            while pnum[f1] < pnum[f2]:
                f1 = idom[f1]
            while pnum[f2] < pnum[f1]:
                f2 = idom[f2]
        return f1

    changed = True
    while changed:
        changed = False
        for b in rpo:
            if b == ENTRY:
                continue
            new_idom = None
            for p in p2.get(b, ()):
                if p in idom:
                    new_idom = p if new_idom is None else intersect(p, new_idom)
            if new_idom is not None and idom.get(b) != new_idom:
                idom[b] = new_idom
                changed = True
    return idom, ENTRY, reachable


def chokepoints_for(x, forward_index):
    """Functions that EVERY path from an entry point must traverse to reach x.
    These are mandatory predecessors — change/break one and x becomes
    unreachable. The rigorous 'single points of failure on the way to x'.
    Computed from immediate dominators (the idom chain x -> ... -> entry)."""
    idom, entry, reachable = _immediate_dominators(forward_index)
    if x not in reachable or x == entry:
        return {
            "query": "chokepoints_for", "target": x,
            "chokepoints": [], "reachable_from_entry": False,
            "boundary": "x is not reachable from any entry point over internal "
                        "edges (isolated, in a source-less cycle, or only reached "
                        "via external/dynamic dispatch)",
        }
    chain, cur, seen = [], idom.get(x), set()
    while cur is not None and cur != entry and cur not in seen:
        seen.add(cur)
        if cur != x:
            chain.append(cur)
        cur = idom.get(cur)
    chain = sorted(chain)
    return {
        "query": "chokepoints_for", "target": x,
        "chokepoints": chain, "count": len(chain),
        "reachable_from_entry": True,
        "boundary": "every internal path from an entry node to x passes through "
                    "these; dynamic/external entry paths not modeled",
    }


# --------------------------------------------------------------------------- #
# 4. Centrality hotspots (exact in/out degree)
# --------------------------------------------------------------------------- #
def hotspots(forward_index, reverse_index, top_n=15):
    adj = _internal_adj(forward_index)
    fan_in = sorted(((len(reverse_index.get(n, set())), n) for n in adj),
                    key=lambda t: (-t[0], t[1]))
    fan_out = sorted(((len(adj[n]), n) for n in adj),
                     key=lambda t: (-t[0], t[1]))
    return {
        "query": "hotspots",
        "most_depended_on": [{"node": n, "callers": c} for c, n in fan_in[:top_n] if c],
        "most_depending": [{"node": n, "calls": c} for c, n in fan_out[:top_n] if c],
        "boundary": "internal in/out degree only; external calls not counted",
    }


# --------------------------------------------------------------------------- #
# 5. Forward reachability + shortest path
# --------------------------------------------------------------------------- #
def reachable_from(x, forward_index, max_nodes=50000):
    adj = _internal_adj(forward_index)
    seen, q = set(), deque([x])
    while q and len(seen) < max_nodes:
        cur = q.popleft()
        for v in adj.get(cur, []):
            if v not in seen and v != x:
                seen.add(v)
                q.append(v)
    return {
        "query": "reachable_from", "target": x,
        "reachable": sorted(seen), "count": len(seen),
        "boundary": "everything x can transitively trigger over internal edges; "
                    "external/dynamic targets not followed",
    }


def shortest_path(a, b, forward_index, max_depth=64):
    adj = _internal_adj(forward_index)
    if a == b:
        return {"query": "shortest_path", "from": a, "to": b, "path": [a],
                "length": 0, "boundary": "trivial"}
    prev, q = {a: None}, deque([a])
    while q:
        cur = q.popleft()
        for v in adj.get(cur, []):
            if v not in prev:
                prev[v] = cur
                if v == b:
                    path = [b]
                    while prev[path[-1]] is not None:
                        path.append(prev[path[-1]])
                    return {"query": "shortest_path", "from": a, "to": b,
                            "path": list(reversed(path)), "length": len(path) - 1,
                            "boundary": "shortest internal call path; not unique if "
                                        "ties exist"}
                q.append(v)
    return {"query": "shortest_path", "from": a, "to": b, "path": None,
            "length": None,
            "boundary": "no internal call path a..->b exists (may be connected "
                        "only via external/dynamic dispatch)"}


# --------------------------------------------------------------------------- #
# convenience wrapper
# --------------------------------------------------------------------------- #
class AdvancedReasoner:
    def __init__(self, forward_index, reverse_index):
        self.fwd, self.rev = forward_index, reverse_index

    def recursion_clusters(self):      return recursion_clusters(self.fwd)
    def impact_by_depth(self, x, **k): return impact_by_depth(x, self.rev, **k)
    def chokepoints_for(self, x):      return chokepoints_for(x, self.fwd)
    def hotspots(self, **k):           return hotspots(self.fwd, self.rev, **k)
    def reachable_from(self, x, **k):  return reachable_from(x, self.fwd, **k)
    def shortest_path(self, a, b, **k): return shortest_path(a, b, self.fwd, **k)