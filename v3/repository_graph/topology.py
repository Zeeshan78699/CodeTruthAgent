"""
topology.py
Gap 3: Graph Topology Cycle Detection

Post-Stage-B processor: runs Tarjan's Strongly Connected Components (SCC)
algorithm over import_graph's internal-import edges to detect cyclic
dependency clusters (e.g. module A imports B, B imports A).

This does NOT modify the 6 core graphs' edges - it only ANNOTATES
module_graph entries with cycle metadata, per the original Gap 3 design:
"leaves physical code edges intact but explicitly annotates ... downstream
AI agents are now algorithmically warned".
"""


def _build_adjacency(import_graph):
    """
    import_graph: {module: [{"imports": "target.module.symbol", ...}, ...]}

    Returns: {module: set(target_module_names)}
    Only the MODULE portion of each import target is used (an import of
    a function/class still creates a module-level dependency edge).
    """
    adjacency = {}
    all_modules = set(import_graph.keys())

    for module, imports in import_graph.items():
        adjacency.setdefault(module, set())
        for entry in imports:
            target = entry["imports"]
            # Try to match the import target against a known project module,
            # trying progressively shorter prefixes (handles
            # "pkg.utils.helper" -> module "pkg.utils").
            parts = target.split(".")
            for split_point in range(len(parts), 0, -1):
                candidate = ".".join(parts[:split_point])
                if candidate in all_modules and candidate != module:
                    adjacency[module].add(candidate)
                    break

    return adjacency


def find_cycles(import_graph):
    """
    Runs Tarjan's SCC algorithm over the internal import graph.

    Returns:
        {
          "clusters": [["mod.a", "mod.b"], ...],  # only SCCs with size > 1
          "module_to_cluster": {"mod.a": "cluster_00", "mod.b": "cluster_00"}
        }
    """
    adjacency = _build_adjacency(import_graph)

    index_counter = [0]
    stack = []
    lowlink = {}
    index = {}
    on_stack = {}
    result = []

    def strongconnect(v):
        index[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack[v] = True

        for w in adjacency.get(v, ()):
            if w not in index:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif on_stack.get(w):
                lowlink[v] = min(lowlink[v], index[w])

        if lowlink[v] == index[v]:
            scc = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == v:
                    break
            result.append(scc)

    # Iterative wrapper to avoid recursion-depth issues on large repos
    import sys
    old_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(max(old_limit, len(adjacency) * 2 + 100))
        for node in adjacency:
            if node not in index:
                strongconnect(node)
    finally:
        sys.setrecursionlimit(old_limit)

    clusters = [scc for scc in result if len(scc) > 1]
    module_to_cluster = {}
    for i, cluster in enumerate(clusters):
        cluster_id = f"cluster_{i:02d}"
        for mod in cluster:
            module_to_cluster[mod] = cluster_id

    return {
        "clusters": [sorted(c) for c in clusters],
        "module_to_cluster": module_to_cluster,
    }


def annotate_module_graph(module_graph, cycle_info):
    """
    Adds "in_cyclic_loop" and "cyclic_cluster_id" fields to each module_graph
    entry, based on cycle_info from find_cycles(). Does not mutate edges -
    informational metadata only.
    """
    module_to_cluster = cycle_info["module_to_cluster"]
    for module, entry in module_graph.items():
        if module in module_to_cluster:
            entry["in_cyclic_loop"] = True
            entry["cyclic_cluster_id"] = module_to_cluster[module]
        else:
            entry["in_cyclic_loop"] = False
            entry["cyclic_cluster_id"] = None
    return module_graph
