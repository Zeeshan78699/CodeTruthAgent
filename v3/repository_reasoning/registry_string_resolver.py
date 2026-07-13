"""
registry_string_resolver.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Phase 3A, Step 3.

Two halves of the Category-3 dynamic-dispatch problem, in one module:

  registry_map_extractor   - finds module-level `{key: ClassRef}` registries:
                                 SERIALIZERS = {"set": SetSerializer, ...}
  string_to_class_resolver - finds the dispatch site that uses one:
                                 SERIALIZERS[name]()        -> bounded set
                                 SERIALIZERS.get(name)()    -> bounded set

CATEGORY 3 — by definition the runtime key is unknown statically, so the result
is NEVER a single collapsed type. It is the BOUNDED SET of every class the
registry can produce, labelled UNCERTAIN with reason RUNTIME_KEY_UNKNOWN. Every
candidate is enumerated; nothing is guessed.

Honest expectation: low yield on Python corpora (most module-level dicts are
runtime data payloads, not class registries - measured). Built for structural
completeness of Phase 3A and for repos/languages that use the pattern; the
report records its measured yield plainly. Additive, frozen imports lazy.
"""

import ast

from v3.repository_reasoning.return_type_inferencer import _reconstruct_inputs

UNCERTAIN = "UNCERTAIN"
UNRESOLVABLE = "UNRESOLVABLE"


def _value_to_class(v, module_name, local_classes, amap, rcn):
    """Resolve a dict value node to ("class", module, name) if it's a class ref."""
    if isinstance(v, ast.Name):
        if v.id in local_classes:
            return ("class", module_name, v.id)
        target = amap.get(v.id)
        if target:
            mod, _, cls = target.rpartition(".")
            if rcn and cls in rcn.get(mod, set()):
                return ("class", mod, cls)
        return None
    if isinstance(v, ast.Attribute):
        parts = []
        cur = v
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name) and cur.id in amap:
            full = amap[cur.id] + "." + ".".join(reversed(parts))
            mod, _, cls = full.rpartition(".")
            if rcn and cls in rcn.get(mod, set()):
                return ("class", mod, cls)
        return None
    return None


def extract_registries(module_trees, real_class_names_index, import_alias_maps,
                       min_class_values=2):
    """{(module, registry_var): [type_info, ...]} for module-level dicts whose
    values are class references (>= min_class_values of them)."""
    registries = {}
    for module_name, tree in module_trees.items():
        local_classes = (real_class_names_index.get(module_name, set())
                         if real_class_names_index else set())
        amap = import_alias_maps.get(module_name, {})
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and isinstance(node.value, ast.Dict) and node.value.values):
                continue
            types, ok = [], True
            for v in node.value.values:
                info = _value_to_class(v, module_name, local_classes, amap,
                                       real_class_names_index)
                if info is None:
                    ok = False
                    break
                types.append(info)
            if ok and len([t for t in types if t[0] == "class"]) >= min_class_values:
                registries[(module_name, node.targets[0].id)] = sorted(set(types), key=repr)
    return registries


def _dispatch_registry_name(call_node):
    """REG[k](...) or REG.get(k)(...) -> registry var name, else None."""
    func = call_node.func
    if isinstance(func, ast.Subscript) and isinstance(func.value, ast.Name):
        return func.value.id
    if (isinstance(func, ast.Call) and isinstance(func.func, ast.Attribute)
            and func.func.attr == "get" and isinstance(func.func.value, ast.Name)):
        return func.func.value.id
    return None


def resolve_dispatch_sites(module_trees, registries):
    """Emit bounded UNCERTAIN edges for REG[k]()/REG.get(k)() where REG is known."""
    edges = []
    by_module = {}
    for (mod, var), types in registries.items():
        by_module.setdefault(mod, {})[var] = types
    for module_name, tree in module_trees.items():
        regs = by_module.get(module_name)
        if not regs:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            reg_name = _dispatch_registry_name(node)
            if reg_name and reg_name in regs:
                edges.append({
                    "module": module_name, "lineno": node.lineno,
                    "registry": reg_name, "candidate_types": regs[reg_name],
                    "label": UNCERTAIN, "reason": "RUNTIME_KEY_UNKNOWN",
                })
    return edges


def from_repo(repo_root, root_counts=None):
    inp = _reconstruct_inputs(repo_root, root_counts)
    registries = extract_registries(
        inp["module_trees"], inp["real_class_names_index"], inp["import_alias_maps"])
    edges = resolve_dispatch_sites(inp["module_trees"], registries)
    total = sum(len(e["candidate_types"]) for e in edges)
    avg = (total / len(edges)) if edges else 0.0
    print(f"  class registries found ({{key: Class}})   : {len(registries)}")
    print(f"  dispatch sites REG[k]()/REG.get(k)()    : {len(edges)}")
    print(f"  >>> UNCERTAIN edges (bounded sets)      : {len(edges)}")
    print(f"  avg candidate set size                  : {avg:.1f}")
    for (mod, var), types in list(registries.items())[:3]:
        names = [t[2] for t in types if t[0] == 'class'][:5]
        print(f"    sample: {var} in {mod}: {names}")
    return registries, edges
