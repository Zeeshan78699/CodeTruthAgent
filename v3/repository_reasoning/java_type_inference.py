"""
java_type_inference.py
CodeTruth Agent V3 — Module 3, Phase 3A for JAVA. Additive.

The Java Module 2 adapter resolves only SAME-FILE calls; every `x.method()` where
x is a field/parameter/local lands in `unresolved` as "cross_file_unresolved"
(qualifier resolution not implemented). Java is statically typed, so x's type is
DECLARED — we can recover it and resolve those calls deterministically.

This module re-parses the Java sources (javalang) and:
  1. builds a repo-wide class index  {SimpleName: [fully.qualified.Class ids]}
     and a method table {Class id: {method names}},
  2. for each method builds a type environment: fields + parameters + locals
     (incl. `var x = call()` resolved via the callee's declared return type),
  3. resolves `receiver.member()` by typing the receiver, mapping its simple
     type name to a repo class (imports -> same package -> unique-by-name), and
     checking the method exists on that class.

Categorical labels (no scores):
  RESOLVED         - receiver typed, type maps to a repo class, method exists
  TYPE_KNOWN_EXTERNAL - receiver typed but the type is not a repo class (JDK /
                     3rd-party) -> honestly NOT an internal edge
  AMBIGUOUS        - simple type name maps to >1 repo class, none disambiguated
  UNRESOLVED       - receiver type not determinable (var-from-unknown, chained,
                     etc.)

Everything additive: imports nothing frozen, edits nothing. Output is a set of
NEW resolved edges plus a measured breakdown vs the adapter's unresolved baseline.
"""

import os
import javalang


# --------------------------------------------------------------------------- #
# module / id naming — MUST match java_adapter.py exactly
# --------------------------------------------------------------------------- #
def _module_name(filepath, package_name):
    base = os.path.splitext(os.path.basename(filepath))[0]
    return f"{package_name}.{base}" if package_name else base


def _java_files(repo_root):
    out = []
    ignore = {".git", "target", "build", ".gradle", "bin", "out", "node_modules"}
    for dp, dn, fn in os.walk(repo_root):
        dn[:] = [d for d in dn if d not in ignore]
        for f in fn:
            if f.endswith(".java"):
                out.append(os.path.join(dp, f))
    return out


# --------------------------------------------------------------------------- #
# pass 1 — parse all files, build class index + method table + import maps
# --------------------------------------------------------------------------- #
def _build_indexes(repo_root, files):
    trees = {}            # module -> (tree, package, filepath)
    class_index = {}      # SimpleName -> set(ClassId)  ; ClassId = module.Class
    method_table = {}     # ClassId -> set(method names)
    class_package = {}    # ClassId -> package
    imports_of = {}       # module -> {SimpleName: FQN}
    package_classes = {}  # package -> set(ClassId)

    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                tree = javalang.parse.parse(fh.read())
        except Exception:
            continue
        pkg = tree.package.name if tree.package else None
        mod = _module_name(fp, pkg)
        trees[mod] = (tree, pkg, fp)

        imp = {}
        for i in (tree.imports or []):
            if not i.wildcard:
                imp[i.path.split(".")[-1]] = i.path
        imports_of[mod] = imp

        for _, cls in tree.filter(javalang.tree.ClassDeclaration):
            cid = f"{mod}.{cls.name}"
            class_index.setdefault(cls.name, set()).add(cid)
            method_table.setdefault(cid, set())
            class_package[cid] = pkg
            if pkg:
                package_classes.setdefault(pkg, set()).add(cid)
            for m in cls.methods:
                method_table[cid].add(m.name)
    return {
        "trees": trees, "class_index": class_index, "method_table": method_table,
        "class_package": class_package, "imports_of": imports_of,
        "package_classes": package_classes,
    }


def _resolve_simple_type(simple, module, pkg, idx):
    """Map a simple type name to a repo ClassId. Returns (label, class_id_or_set)."""
    # 1. explicit import
    imp = idx["imports_of"].get(module, {})
    if simple in imp:
        fqn = imp[simple]
        # fqn = a.b.C ; our ClassId is module(=pkg.File).Class — match by suffix .C
        cands = {c for c in idx["class_index"].get(simple, set())}
        # prefer a candidate whose package matches the import's package
        ipkg = ".".join(fqn.split(".")[:-1])
        best = {c for c in cands if idx["class_package"].get(c) == ipkg}
        if len(best) == 1:
            return ("RESOLVED", next(iter(best)))
        if cands:
            return ("RESOLVED", next(iter(cands))) if len(cands) == 1 else ("AMBIGUOUS", cands)
        return ("TYPE_KNOWN_EXTERNAL", fqn)
    # 2. same package
    same = {c for c in idx["class_index"].get(simple, set())
            if idx["class_package"].get(c) == pkg}
    if len(same) == 1:
        return ("RESOLVED", next(iter(same)))
    # 3. unique across repo
    allc = idx["class_index"].get(simple, set())
    if len(allc) == 1:
        return ("RESOLVED", next(iter(allc)))
    if len(allc) > 1:
        return ("AMBIGUOUS", allc)
    # 4. not in repo
    return ("TYPE_KNOWN_EXTERNAL", simple)


# --------------------------------------------------------------------------- #
# pass 2 — per method: type env, then resolve receiver.member() calls
# --------------------------------------------------------------------------- #
def _method_return_types(idx):
    """{ClassId: {method: simple_return_type}} for var-from-return inference."""
    rt = {}
    for mod, (tree, pkg, fp) in idx["trees"].items():
        for _, cls in tree.filter(javalang.tree.ClassDeclaration):
            cid = f"{mod}.{cls.name}"
            d = rt.setdefault(cid, {})
            for m in cls.methods:
                d[m.name] = getattr(m.return_type, "name", None)
    return rt


def analyze(repo_root):
    files = _java_files(repo_root)
    idx = _build_indexes(repo_root, files)
    ret_types = _method_return_types(idx)

    resolved_edges = []
    counts = {"RESOLVED": 0, "TYPE_KNOWN_EXTERNAL": 0, "AMBIGUOUS": 0,
              "UNRESOLVED": 0, "self_or_implicit": 0}

    for mod, (tree, pkg, fp) in idx["trees"].items():
        for _, cls in tree.filter(javalang.tree.ClassDeclaration):
            cid = f"{mod}.{cls.name}"
            # class field types
            field_t = {}
            for _, fd in cls.filter(javalang.tree.FieldDeclaration):
                for d in fd.declarators:
                    field_t[d.name] = fd.type.name
            for m in cls.methods:
                if not m.body:
                    continue
                caller = f"{cid}.{m.name}"
                env = dict(field_t)
                for p in m.parameters:
                    env[p.name] = p.type.name
                # locals (incl. var-from-return)
                for _, lv in m.filter(javalang.tree.LocalVariableDeclaration):
                    tname = lv.type.name
                    for d in lv.declarators:
                        if tname == "var":
                            # infer from RHS if it's a same-class method call
                            inferred = None
                            init = getattr(d, "initializer", None)
                            if isinstance(init, javalang.tree.MethodInvocation) \
                               and init.qualifier in (None, "", "this"):
                                inferred = ret_types.get(cid, {}).get(init.member)
                            env[d.name] = inferred
                        else:
                            env[d.name] = tname
                # resolve invocations with a simple-name receiver
                for _, inv in m.filter(javalang.tree.MethodInvocation):
                    q = inv.qualifier
                    if q in (None, "", "this"):
                        counts["self_or_implicit"] += 1
                        continue
                    if "." in (q or ""):
                        counts["UNRESOLVED"] += 1   # chained a.b.c() — not handled
                        continue
                    tname = env.get(q)
                    if not tname:
                        counts["UNRESOLVED"] += 1
                        continue
                    label, target = _resolve_simple_type(tname, mod, pkg, idx)
                    if label == "RESOLVED":
                        if inv.member in idx["method_table"].get(target, set()):
                            resolved_edges.append({
                                "caller": caller,
                                "callee": f"{target}.{inv.member}",
                                "lineno": inv.position.line if inv.position else 0,
                                "resolution": "java_3a_type_resolved",
                                "receiver_type": tname,
                            })
                            counts["RESOLVED"] += 1
                        else:
                            counts["TYPE_KNOWN_EXTERNAL"] += 1  # repo class, method not found (inherited/overload)
                    elif label == "AMBIGUOUS":
                        counts["AMBIGUOUS"] += 1
                    else:
                        counts["TYPE_KNOWN_EXTERNAL"] += 1
    return {
        "language": "java", "repo": repo_root,
        "files_parsed": len(idx["trees"]),
        "classes": sum(len(v) for v in idx["class_index"].values()),
        "new_resolved_edges": resolved_edges,
        "counts": counts,
        "boundary": "resolves receiver.member() where the receiver is a field / "
                    "parameter / local with a declared type that maps to a repo "
                    "class; chained calls (a.b.c()), generics, inheritance, and "
                    "overloads are not modeled. RESOLVED edges are type-based and "
                    "exact for direct field/param/local receivers.",
    }


# --------------------------------------------------------------------------- #
# 3A -> 3B bridge: merge type-resolved edges INTO the adapter's call graph so
# the reasoning queries chain across files (additive; nothing frozen touched).
# --------------------------------------------------------------------------- #
def enriched_report(repo_root):
    """Run the Java Module 2 adapter, then fold in this module's type-resolved
    edges as additional call_graph entries. Returns a standard-shape report that
    from_adapter_report / the 3B query surface consume unchanged. The new edges
    go in a synthetic bucket — the query layer flattens all call_graph values, so
    the bucket key is irrelevant to reasoning."""
    from v3.repository_reasoning.language_adapter_bridge import get_adapter, files_for_language

    adapter = get_adapter("java")
    files = files_for_language(repo_root, "java")
    report = dict(adapter.scan(repo_root, files))

    res = analyze(repo_root)
    new_edges = [
        {"caller": e["caller"], "callee": e["callee"],
         "lineno": e["lineno"], "resolution": e["resolution"]}
        for e in res["new_resolved_edges"]
    ]
    cg = dict(report.get("call_graph", {}))
    cg["__java_3a_type_resolved__"] = new_edges
    report["call_graph"] = cg
    report["__java_3a_counts__"] = res["counts"]
    return report


def enriched_query_surface(repo_root):
    """QuerySurface over the type-enriched Java call graph (same-file adapter
    edges + cross-file type-resolved edges). Use for deeper 3B on Java."""
    from v3.repository_reasoning.reasoning_queries import from_adapter_report
    return from_adapter_report(enriched_report(repo_root), language="java")
