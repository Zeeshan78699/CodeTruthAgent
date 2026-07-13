"""
reasoning_queries.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Phase 3B query surface.

Turns the call graph into deterministic answers to engineering questions. Built on
multi_hop_analyzer's call index. Every answer is exact over INTERNAL edges; calls
that leave the repo (<external>/<builtin>) are honest leaves, never traversed.

Boundary discipline (load-bearing): the "impact" queries answer CALL-REACHABILITY,
not SEMANTIC impact. "What breaks if I change X" returns everything that
transitively CALLS X within the repo - it does NOT decide whether a given caller
actually breaks, and it cannot see ripple through external libraries. Each result
carries an explicit `boundary` field so the answer can never be mistaken for a
complete blast radius.

Pure: all queries operate on a forward index {caller: [(callee, kind, lineno, res)]}
and a reverse index built from it. Unit-testable with synthetic graphs.
"""

from collections import deque


def build_reverse_index(forward_index):
    """{callee: set(caller)} over INTERNAL edges only (chainable)."""
    rev = {}
    for caller, outs in forward_index.items():
        for callee, kind, _lineno, _res in outs:
            if kind == "internal":
                rev.setdefault(callee, set()).add(caller)
    return rev


def all_internal_nodes(forward_index):
    nodes = set(forward_index.keys())
    for outs in forward_index.values():
        for callee, kind, _l, _r in outs:
            if kind == "internal":
                nodes.add(callee)
    return nodes


# --------------------------------------------------------------------------- #
# Q1. who_calls(x)  — direct callers ("Why is this method called?")
# --------------------------------------------------------------------------- #
def who_calls(x, reverse_index):
    return {
        "query": "who_calls", "target": x,
        "direct_callers": sorted(reverse_index.get(x, set())),
        "count": len(reverse_index.get(x, set())),
        "boundary": "internal callers only; external callers not visible",
    }


# --------------------------------------------------------------------------- #
# Q2. paths_to(x) — all internal call paths that reach x ("Show all paths to API")
# --------------------------------------------------------------------------- #
def paths_to(x, reverse_index, max_depth=8, max_paths=500):
    """Reverse BFS: every chain root...->x. Cycle-safe, depth-bounded."""
    paths = []
    q = deque([[x]])
    while q and len(paths) < max_paths:
        path = q.popleft()
        head = path[0]
        callers = reverse_index.get(head, set())
        # a node with no internal callers is a ROOT of a path to x
        real_callers = [c for c in callers if c not in path]  # cycle guard
        if not real_callers or len(path) >= max_depth:
            if len(path) > 1:
                paths.append(path)
            if real_callers and len(path) >= max_depth:
                paths.append(path + ["...(truncated)"])
            continue
        for c in real_callers:
            q.append([c] + path)
    return {
        "query": "paths_to", "target": x,
        "paths": paths, "count": len(paths),
        "boundary": "internal paths only; depth bounded; cycles stop",
    }


# --------------------------------------------------------------------------- #
# Q3. impact_of(x) — reverse transitive closure ("What breaks if I change X?")
# --------------------------------------------------------------------------- #
def impact_of(x, reverse_index, max_nodes=20000):
    """Everything that transitively CALLS x (in-repo). CALL-REACHABILITY, not
    semantic breakage."""
    seen = set()
    q = deque([x])
    while q and len(seen) < max_nodes:
        cur = q.popleft()
        for caller in reverse_index.get(cur, set()):
            if caller not in seen and caller != x:
                seen.add(caller)
                q.append(caller)
    return {
        "query": "impact_of", "target": x,
        "affected_callers": sorted(seen), "count": len(seen),
        "label": "CALL_REACHABLE",
        "boundary": "in-repo call-reachability only; NOT semantic breakage; "
                    "external/dynamic callers not included",
    }


# --------------------------------------------------------------------------- #
# Q4. depends_on_class(class_id) — callers of any method of the class
# --------------------------------------------------------------------------- #
def depends_on_class(class_id, forward_index, reverse_index):
    prefix = class_id + "."
    methods = [n for n in all_internal_nodes(forward_index) if n.startswith(prefix)]
    dependents = set()
    for m in methods:
        dependents |= {c for c in reverse_index.get(m, set()) if not c.startswith(prefix)}
    return {
        "query": "depends_on_class", "target": class_id,
        "methods": sorted(methods),
        "external_dependents": sorted(dependents), "count": len(dependents),
        "boundary": "callers of the class's methods, in-repo; excludes the "
                    "class's own methods",
    }


# --------------------------------------------------------------------------- #
# Q5. dead_code() — internal nodes never called by anything in-repo
# --------------------------------------------------------------------------- #
def dead_code(forward_index, reverse_index, roots_keywords=("main", "test_", "__init__")):
    """Internal callees/callers with ZERO inbound internal edges. Honest caveat:
    entry points, framework callbacks, and dynamically-dispatched targets look
    'dead' but aren't - reported as CANDIDATES, not a verdict."""
    nodes = all_internal_nodes(forward_index)
    candidates = []
    for n in nodes:
        if not reverse_index.get(n):
            simple = n.rsplit(".", 1)[-1]
            likely_entry = any(k in n for k in roots_keywords)
            candidates.append({"node": n, "likely_entry_point": likely_entry})
    return {
        "query": "dead_code",
        "candidates": [c["node"] for c in candidates if not c["likely_entry_point"]],
        "entry_points_excluded": [c["node"] for c in candidates if c["likely_entry_point"]],
        "count": sum(1 for c in candidates if not c["likely_entry_point"]),
        "label": "CANDIDATES",
        "boundary": "no inbound internal call edge; entry points / framework "
                    "callbacks / dynamic dispatch may appear here falsely - "
                    "CANDIDATES, not a verdict",
    }


# --------------------------------------------------------------------------- #
# Q6. paths_between(a, b) — alternative forward paths a..->b
# --------------------------------------------------------------------------- #
def paths_between(a, b, forward_index, max_depth=8, max_paths=200):
    paths = []
    q = deque([[a]])
    while q and len(paths) < max_paths:
        path = q.popleft()
        head = path[-1]
        if head == b and len(path) > 1:
            paths.append(path)
            continue
        if len(path) >= max_depth:
            continue
        for callee, kind, _l, _r in forward_index.get(head, []):
            if kind == "internal" and callee not in path:
                q.append(path + [callee])
    return {
        "query": "paths_between", "from": a, "to": b,
        "paths": paths, "count": len(paths),
        "boundary": "distinct internal forward paths; depth bounded; cycles excluded",
    }


# --------------------------------------------------------------------------- #
# LANGUAGE-AGNOSTIC ENTRY
# The queries above operate on {caller, callee} edges and never inspected the
# language. Any Module 2 adapter that emits the standard `call_graph`
# ({module: [{caller, callee, lineno, resolution}]}) can be queried directly —
# Python, Java, JavaScript, C/C++. Adapters that emit a custom shape (C#, Go,
# SQL) are rejected with a clear message rather than silently mis-handled.
# --------------------------------------------------------------------------- #

from v3.repository_reasoning.multi_hop_analyzer import build_call_index


class QuerySurface:
    """Wraps a forward + reverse call index and exposes the engineering
    queries. Language-agnostic: it only sees {caller, callee} edges."""

    def __init__(self, forward_index, language=None):
        self.fwd = forward_index
        self.rev = build_reverse_index(forward_index)
        self.language = language

    def who_calls(self, x):            return who_calls(x, self.rev)
    def paths_to(self, x, **kw):       return paths_to(x, self.rev, **kw)
    def impact_of(self, x, **kw):      return impact_of(x, self.rev, **kw)
    def depends_on_class(self, c):     return depends_on_class(c, self.fwd, self.rev)
    def dead_code(self, **kw):         return dead_code(self.fwd, self.rev, **kw)
    def paths_between(self, a, b, **kw): return paths_between(a, b, self.fwd, **kw)

    def stats(self):
        internal = sum(1 for outs in self.fwd.values() for _, k, _, _ in outs if k == "internal")
        terminal = sum(1 for outs in self.fwd.values() for _, k, _, _ in outs if k != "internal")
        return {"language": self.language, "internal_edges": internal,
                "terminal_edges": terminal,
                "nodes": len(all_internal_nodes(self.fwd))}


def from_adapter_report(report, language=None):
    """
    Build a QuerySurface from ANY standard-shape Module 2 adapter report.

    Requires `report["call_graph"]` to be {module: [{caller, callee, lineno,
    resolution}, ...]} — the shape Python/Java/JavaScript/C-C++ adapters emit.
    Adapters with a custom shape (C#: `method_calls`+`deep_resolution`; Go:
    `calls`; SQL: tables/procs) raise ValueError with guidance — they need a
    call_graph shape bridge before Module 3B can consume them.
    """
    cg = report.get("call_graph")
    if not isinstance(cg, dict):
        raise ValueError(
            "This adapter does not emit the standard `call_graph` "
            "({module: [{caller,callee,lineno,resolution}]}). Adapters known to "
            "use a custom shape: C# (method_calls + deep_resolution), Go (calls), "
            "SQL (tables/procedures). A call_graph shape bridge is required before "
            "the language-agnostic 3B query surface can consume them."
        )
    edges = [e for edge_list in cg.values() for e in edge_list]
    return QuerySurface(build_call_index(edges), language=language)


def query_repo(repo_root, language):
    """
    Convenience: find the repo's files for `language`, run the matching
    standard-shape adapter, and return a QuerySurface.

    Builds the file list directly from each adapter's `file_extensions` rather
    than via registry.classify_files — the latter constructs EVERY registered
    adapter up front and crashes if any one is malformed (e.g. GoAdapter is
    missing `language_name`). We only touch the adapter we actually need.
    """
    import os
    from v3.repository_graph.languages import registry as REG

    # locate the adapter for this language without iterating broken siblings
    adapter = None
    for a in REG.ADAPTERS:
        try:
            if getattr(a, "language_name", None) == language or \
               getattr(a, "language", None) == language:
                adapter = a
                break
        except Exception:
            continue
    if adapter is None:
        raise ValueError(f"no registered adapter for language '{language}'")
    if hasattr(adapter, "is_implemented") and not adapter.is_implemented():
        raise ValueError(f"{language} adapter is a stub (not implemented)")

    exts = getattr(adapter, "file_extensions", set())
    if not os.path.isdir(repo_root):
        raise ValueError(f"repo path not found: {repo_root}")

    ignore = {".git", "__pycache__", "node_modules", ".venv", "venv", "target", "build"}
    files = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in exts:
                files.append(os.path.join(dirpath, fn))
    if not files:
        raise ValueError(f"no {language} files found under {repo_root}")

    report = adapter.scan(repo_root, files)
    return from_adapter_report(report, language=language)