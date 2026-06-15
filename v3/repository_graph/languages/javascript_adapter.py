"""
javascript_adapter.py (v3 - cross-file resolution)
Adds relative-import-based cross-file call resolution on top of v2's
tree-sitter extraction (v2: 0 parse errors, 7,421 functions / 736 classes
across 69 repos, but only 6.6% resolved - the rest was overwhelmingly
cross-file calls to relatively-imported symbols, the D-001-equivalent gap
for JS).

ARCHITECTURE (mirrors Python's D-001 two-stage build):
  STAGE A (per-file, same as v2): parse each file, extract function_graph,
    class_graph, local_funcs/local_classes (same-file symbol table), AND
    relative import specifiers (local_name -> (raw_source_path, imported_name)).
  STAGE B (global): resolve each relative import's raw_source_path to an
    actual scanned module (trying .js/.jsx/.ts/.tsx/.mjs/.cjs and
    index.* files - JS's module resolution algorithm), building
    import_alias_map[module][local_name] = (target_module, imported_name).
  STAGE C (global): call resolution - same-file first (as v2), then
    fall back to import_alias_map + the target module's function_graph/
    class_graph. New resolution category: "imported_call".

SCOPE / LIMITATIONS (honest):
  - Only RELATIVE imports ("./", "../") are resolved - external package
    imports (npm packages) remain unresolved (correct - no source to
    resolve to).
  - Default imports (`import Foo from './bar'`) resolve only if the
    target module has a function/class with id ending ".<default>"
    (i.e. `export default function/class` with no name). Named default
    exports (`export default function Bar(){}` then `import Foo from
    './bar'` - Foo aliases Bar) are NOT resolved - JS allows the importer
    to rename a default export arbitrarily, and without tracking which
    declaration is the default export's target, we can't link "Foo" to
    "Bar". Documented as future work.
  - Namespace imports (`import * as ns from './x'`) are not resolved -
    `ns.something()` stays cross_file_unresolved (member-expression on an
    import namespace - same category as Python's qualified_module_call,
    a possible future enhancement).
  - `new ClassName()` (constructor calls) resolve the same way as function
    calls (same-file local_classes, then import_alias_map + target
    class_graph) - new resolution category "imported_constructor_call"
    for the cross-file case, "local_constructor_call" for same-file.
  - Resolution is only possible if the target file is in `file_paths`
    (the scanned set) - if capped (e.g. 300 files/repo), imports to
    not-yet-scanned files remain unresolved with a distinguishing note.
"""

import os
import tree_sitter_languages

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="tree_sitter")

from .base_adapter import LanguageAdapter


_PARSERS = {}

JS_EXTENSIONS = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]


def _get_parser(ext):
    if ext in (".ts",):
        lang = "typescript"
    elif ext in (".tsx",):
        lang = "tsx"
    else:
        lang = "javascript"
    if lang not in _PARSERS:
        _PARSERS[lang] = tree_sitter_languages.get_parser(lang)
    return _PARSERS[lang]


def _module_name_from_path(repo_root, filepath):
    rel = os.path.relpath(filepath, repo_root)
    rel_no_ext = os.path.splitext(rel)[0]
    return rel_no_ext.replace(os.sep, ".").replace("/", ".")


def _text(src, node):
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _unwrap_export(node):
    if node.type != "export_statement":
        return node
    for child in node.children:
        if child.type in ("function_declaration", "function",
                           "class_declaration", "class",
                           "lexical_declaration", "variable_declaration"):
            return child
    return None


def _member_to_string(src, node):
    if node.type == "this":
        return "this"
    if node.type == "identifier":
        return _text(src, node)
    if node.type == "member_expression":
        obj = node.child_by_field_name("object")
        prop = node.child_by_field_name("property")
        return f"{_member_to_string(src, obj)}.{_text(src, prop)}"
    return "<expr>"


class JavaScriptAdapter(LanguageAdapter):
    language_name = "javascript"
    file_extensions = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}

    def is_implemented(self) -> bool:
        return True

    def scan(self, repo_root: str, file_paths: list) -> dict:
        function_graph = {}
        class_graph = {}
        module_graph = {}
        import_graph = {}
        dependency_graph = {}
        call_graph = {}
        unresolved = []

        # module_name -> per-module data needed across stages
        modules = {}
        path_to_module = {}

        # ---- STAGE A: per-file parse + extraction ----
        for filepath in file_paths:
            module_name = _module_name_from_path(repo_root, filepath)
            ext = os.path.splitext(filepath)[1].lower()
            norm_path = os.path.normpath(os.path.abspath(filepath))
            path_to_module[norm_path] = module_name

            try:
                with open(filepath, "rb") as f:
                    src = f.read()
                parser = _get_parser(ext)
                tree = parser.parse(src)
                root = tree.root_node
            except Exception as e:
                unresolved.append({
                    "module": module_name, "lineno": 0,
                    "pattern": "parse_error",
                    "note": f"{type(e).__name__}: {e}",
                })
                continue

            if root.has_error and len(root.children) == 0:
                unresolved.append({
                    "module": module_name, "lineno": 0,
                    "pattern": "parse_error",
                    "note": "tree-sitter returned an error tree with no parseable content.",
                })
                continue

            module_graph[module_name] = {
                "path": filepath,
                "parent": ".".join(module_name.split(".")[:-1]) or None,
                "is_package": os.path.basename(filepath).split(".")[0] == "index",
            }

            funcs, classes = [], []
            local_funcs, local_classes = set(), {}
            internal_imports = []
            relative_specs = []  # (local_name, imported_name, raw_source, lineno)
            default_count = [0]

            for top in root.children:
                if top.type == "import_statement":
                    _collect_import(src, top, module_name, internal_imports,
                                     dependency_graph, relative_specs)
                    continue
                is_default_export = (top.type == "export_statement"
                                      and any(c.type == "default" for c in top.children))
                decl = _unwrap_export(top)
                if decl is None:
                    continue
                if decl.type == "import_statement":
                    _collect_import(src, decl, module_name, internal_imports,
                                     dependency_graph, relative_specs)
                    continue
                _collect_decl(src, decl, module_name, funcs, classes,
                               local_funcs, local_classes, default_count, is_default_export)

            function_graph[module_name] = funcs
            class_graph[module_name] = classes
            import_graph[module_name] = internal_imports

            modules[module_name] = {
                "filepath": filepath, "norm_path": norm_path,
                "src": src, "root": root,
                "local_funcs": local_funcs, "local_classes": local_classes,
                "relative_specs": relative_specs,
            }

        # ---- STAGE B: resolve relative imports to scanned modules ----
        for module_name, info in modules.items():
            alias_map = {}
            for (local_name, imported_name, raw_source, lineno) in info["relative_specs"]:
                target_module = _resolve_relative_path(
                    info["norm_path"], raw_source, path_to_module)
                if target_module:
                    alias_map[local_name] = (target_module, imported_name, lineno)
                else:
                    alias_map[local_name] = (None, imported_name, lineno)  # path unresolved
            info["import_alias_map"] = alias_map

        # ---- STAGE C: call resolution (same-file, then cross-file) ----
        for module_name, info in modules.items():
            calls = []
            default_count2 = [0]
            for top in info["root"].children:
                decl = _unwrap_export(top) if top.type == "export_statement" else top
                if decl is None or decl is None:
                    continue
                if decl.type == "import_statement":
                    continue
                _walk_calls(info["src"], decl, module_name, None,
                             info["local_funcs"], info["local_classes"],
                             info["import_alias_map"], function_graph, class_graph,
                             calls, unresolved, default_count2)
            call_graph[module_name] = calls

        return {
            "function_graph": function_graph,
            "class_graph": class_graph,
            "module_graph": module_graph,
            "import_graph": import_graph,
            "dependency_graph": dependency_graph,
            "call_graph": call_graph,
            "unresolved": unresolved,
            "cyclic_clusters": [],
        }


def _resolve_relative_path(importing_norm_path, raw_source, path_to_module):
    """Resolve a relative import path (e.g. './utils/helper') to a scanned
    module name, mimicking JS module resolution: try the path as-is, with
    each JS_EXTENSIONS suffix, and as a directory with index.*."""
    base_dir = os.path.dirname(importing_norm_path)
    candidate = os.path.normpath(os.path.join(base_dir, raw_source))

    if candidate in path_to_module:
        return path_to_module[candidate]
    for ext in JS_EXTENSIONS:
        if candidate + ext in path_to_module:
            return path_to_module[candidate + ext]
    for ext in JS_EXTENSIONS:
        index_path = os.path.join(candidate, "index" + ext)
        if index_path in path_to_module:
            return path_to_module[index_path]
    return None


def _collect_import(src, node, module_name, internal_imports, dependency_graph, relative_specs):
    string_node = None
    for child in node.children:
        if child.type == "string":
            string_node = child
            break
    if string_node is None:
        return
    frag = None
    for c in string_node.children:
        if c.type == "string_fragment":
            frag = _text(src, c)
            break
    if frag is None:
        return

    lineno = node.start_point[0] + 1
    entry = {
        "from_module": module_name, "imports": frag,
        "type": "import", "lineno": lineno,
    }
    is_relative = frag.startswith(".") or frag.startswith("/")
    if is_relative:
        internal_imports.append(entry)
    else:
        root_pkg = frag.split("/")[0]
        dependency_graph.setdefault(root_pkg, {"used_by": [], "import_count": 0})
        if module_name not in dependency_graph[root_pkg]["used_by"]:
            dependency_graph[root_pkg]["used_by"].append(module_name)
        dependency_graph[root_pkg]["import_count"] += 1
        return  # only relative imports are tracked for cross-file resolution

    # Extract specifiers (only meaningful for relative imports)
    import_clause = None
    for c in node.children:
        if c.type == "import_clause":
            import_clause = c
            break
    if import_clause is None:
        return

    for c in import_clause.children:
        if c.type == "identifier":
            # default import: `import Foo from './bar'`
            local_name = _text(src, c)
            relative_specs.append((local_name, "default", frag, lineno))
        elif c.type == "named_imports":
            for spec in c.children:
                if spec.type != "import_specifier":
                    continue
                name_node = spec.child_by_field_name("name")
                alias_node = spec.child_by_field_name("alias")
                imported_name = _text(src, name_node)
                local_name = _text(src, alias_node) if alias_node else imported_name
                relative_specs.append((local_name, imported_name, frag, lineno))
        # namespace_import (`* as ns`) - not resolved, intentionally skipped


def _collect_decl(src, decl, module_name, funcs, classes, local_funcs, local_classes, default_count, is_default=False):
    if decl.type in ("function_declaration", "function"):
        name_node = decl.child_by_field_name("name")
        if name_node:
            name = _text(src, name_node)
        else:
            default_count[0] += 1
            name = "<default>" if default_count[0] == 1 else f"<default{default_count[0]}>"
        funcs.append({
            "id": f"{module_name}.{name}", "name": name,
            "lineno": decl.start_point[0] + 1, "scope": None, "is_async": False,
            "is_default": is_default,
        })
        local_funcs.add(name)

    elif decl.type in ("class_declaration", "class"):
        name_node = decl.child_by_field_name("name")
        if name_node:
            name = _text(src, name_node)
        else:
            default_count[0] += 1
            name = "<default>" if default_count[0] == 1 else f"<default{default_count[0]}>"

        bases = []
        for child in decl.children:
            if child.type == "class_heritage":
                for hc in child.children:
                    if hc.type in ("identifier", "member_expression"):
                        bases.append(_member_to_string(src, hc))

        class_methods = {}
        body = decl.child_by_field_name("body")
        if body:
            for member in body.children:
                if member.type == "method_definition":
                    mname_node = member.child_by_field_name("name")
                    if mname_node:
                        mname = _text(src, mname_node)
                        full_id = f"{module_name}.{name}.{mname}"
                        funcs.append({
                            "id": full_id, "name": mname,
                            "lineno": member.start_point[0] + 1,
                            "scope": name, "is_async": False,
                        })
                        class_methods[mname] = full_id

        classes.append({
            "id": f"{module_name}.{name}", "name": name,
            "lineno": decl.start_point[0] + 1, "bases": bases, "scope": None,
            "is_default": is_default,
        })
        local_classes[name] = class_methods

    elif decl.type in ("lexical_declaration", "variable_declaration"):
        for child in decl.children:
            if child.type != "variable_declarator":
                continue
            name_node = child.child_by_field_name("name")
            value_node = child.child_by_field_name("value")
            if name_node is None or value_node is None:
                continue
            if value_node.type in ("arrow_function", "function"):
                name = _text(src, name_node)
                funcs.append({
                    "id": f"{module_name}.{name}", "name": name,
                    "lineno": child.start_point[0] + 1, "scope": None, "is_async": False,
                })
                local_funcs.add(name)


def _target_has_default(function_graph, class_graph, target_module):
    for f in function_graph.get(target_module, []):
        if f.get("is_default"):
            return f["id"]
    for c in class_graph.get(target_module, []):
        if c.get("is_default"):
            return c["id"]
    return None


def _target_function(function_graph, target_module, name):
    for f in function_graph.get(target_module, []):
        if f["name"] == name and f["scope"] is None:
            return f["id"]
    return None


def _target_class(class_graph, target_module, name):
    for c in class_graph.get(target_module, []):
        if c["name"] == name:
            return c["id"]
    return None


def _resolve_via_alias(name, alias_map, function_graph, class_graph, kind):
    """kind: 'call' or 'constructor'. Returns (resolution_label, callee_id) or None."""
    if name not in alias_map:
        return None
    target_module, imported_name, _lineno = alias_map[name]
    if target_module is None:
        return ("path_unresolved", None)

    if imported_name == "default":
        callee = _target_has_default(function_graph, class_graph, target_module)
        if callee:
            label = "imported_constructor_call" if kind == "constructor" else "imported_call"
            return (label, callee)
        return ("symbol_unresolved", None)

    if kind == "constructor":
        callee = _target_class(class_graph, target_module, imported_name)
        if callee:
            return ("imported_constructor_call", callee)
        callee = _target_function(function_graph, target_module, imported_name)
        if callee:
            return ("imported_constructor_call", callee)
    else:
        callee = _target_function(function_graph, target_module, imported_name)
        if callee:
            return ("imported_call", callee)
        callee = _target_class(class_graph, target_module, imported_name)
        if callee:
            return ("imported_constructor_call", callee)  # called as function but is a class

    return ("symbol_unresolved", None)


def _walk_calls(src, node, module_name, current_scope, local_funcs, local_classes,
                alias_map, function_graph, class_graph, calls, unresolved, default_count2):
    t = node.type

    if t in ("function_declaration", "function"):
        name_node = node.child_by_field_name("name")
        if name_node:
            name = _text(src, name_node)
        else:
            default_count2[0] += 1
            name = "<default>" if default_count2[0] == 1 else f"<default{default_count2[0]}>"
        scope = f"{module_name}.{name}"
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                _walk_calls(src, child, module_name, scope, local_funcs, local_classes,
                             alias_map, function_graph, class_graph, calls, unresolved, default_count2)
        return

    if t in ("class_declaration", "class"):
        name_node = node.child_by_field_name("name")
        if name_node:
            cls_name = _text(src, name_node)
        else:
            default_count2[0] += 1
            cls_name = "<default>" if default_count2[0] == 1 else f"<default{default_count2[0]}>"
        body = node.child_by_field_name("body")
        if body:
            for member in body.children:
                if member.type == "method_definition":
                    mname_node = member.child_by_field_name("name")
                    mname = _text(src, mname_node) if mname_node else "<anon>"
                    scope = f"{module_name}.{cls_name}.{mname}"
                    mbody = member.child_by_field_name("body")
                    if mbody:
                        for child in mbody.children:
                            _walk_calls(src, child, module_name, scope, local_funcs, local_classes,
                                         alias_map, function_graph, class_graph, calls, unresolved, default_count2)
        return

    if t in ("lexical_declaration", "variable_declaration"):
        for child in node.children:
            if child.type != "variable_declarator":
                continue
            name_node = child.child_by_field_name("name")
            value_node = child.child_by_field_name("value")
            if value_node is None:
                continue
            if value_node.type in ("arrow_function", "function"):
                scope = f"{module_name}.{_text(src, name_node)}" if name_node else current_scope
                body = value_node.child_by_field_name("body")
                if body and body.type == "statement_block":
                    for c in body.children:
                        _walk_calls(src, c, module_name, scope, local_funcs, local_classes,
                                     alias_map, function_graph, class_graph, calls, unresolved, default_count2)
                elif body:
                    _walk_calls(src, body, module_name, scope, local_funcs, local_classes,
                                 alias_map, function_graph, class_graph, calls, unresolved, default_count2)
            else:
                # e.g. `const t = new Tool()` or `const x = someCall()` -
                # walk the value expression itself for calls/constructors.
                _walk_calls(src, value_node, module_name, current_scope, local_funcs, local_classes,
                             alias_map, function_graph, class_graph, calls, unresolved, default_count2)
        return

    if t in ("call_expression", "new_expression"):
        field = "constructor" if t == "new_expression" else "function"
        fn = node.child_by_field_name(field)
        line = node.start_point[0] + 1
        caller = current_scope or f"{module_name}.<module>"
        kind = "constructor" if t == "new_expression" else "call"

        if fn is not None and fn.type == "identifier":
            name = _text(src, fn)
            if kind == "constructor" and name in local_classes:
                calls.append({
                    "caller": caller, "callee": f"{module_name}.{name}",
                    "lineno": line, "resolution": "local_constructor_call",
                })
            elif kind == "call" and name in local_funcs:
                calls.append({
                    "caller": caller, "callee": f"{module_name}.{name}",
                    "lineno": line, "resolution": "direct_name_call",
                })
            else:
                result = _resolve_via_alias(name, alias_map, function_graph, class_graph, kind)
                if result and result[1]:
                    calls.append({
                        "caller": caller, "callee": result[1],
                        "lineno": line, "resolution": result[0],
                    })
                elif result and result[0] == "path_unresolved":
                    unresolved.append({
                        "module": module_name, "lineno": line,
                        "pattern": "cross_file_unresolved",
                        "note": f"'{name}' imported from a relative path, but "
                                f"target file not found among scanned files "
                                f"(may be outside the scan cap, or path "
                                f"resolution failed).",
                    })
                elif result and result[0] == "symbol_unresolved":
                    target_module = alias_map[name][0]
                    unresolved.append({
                        "module": module_name, "lineno": line,
                        "pattern": "cross_file_unresolved",
                        "note": f"'{name}' resolved to module '{target_module}', "
                                f"but no matching function/class/default-export "
                                f"found there (may be a re-export, namespace "
                                f"export, or named-default-export rename - not "
                                f"yet resolved).",
                    })
                else:
                    unresolved.append({
                        "module": module_name, "lineno": line,
                        "pattern": "cross_file_unresolved",
                        "note": f"{'new ' if kind == 'constructor' else ''}'{name}(...)' "
                                f"- not a locally-defined or relatively-imported "
                                f"symbol (external package, global, or builtin).",
                    })
        elif fn is not None and fn.type == "member_expression":
            obj = fn.child_by_field_name("object")
            prop = fn.child_by_field_name("property")
            obj_str = _member_to_string(src, obj)
            prop_str = _text(src, prop)
            if obj_str == "this":
                parts = caller.split(".")
                cls_name = parts[-2] if len(parts) >= 2 else None
                methods = local_classes.get(cls_name, {}) if cls_name else {}
                if prop_str in methods:
                    calls.append({
                        "caller": caller, "callee": methods[prop_str],
                        "lineno": line, "resolution": "self_method_call",
                    })
                else:
                    unresolved.append({
                        "module": module_name, "lineno": line,
                        "pattern": "cross_file_unresolved",
                        "note": f"Call 'this.{prop_str}(...)' - not found in "
                                f"enclosing class '{cls_name}' (may be inherited - "
                                f"cross-file method resolution not yet implemented).",
                    })
            else:
                unresolved.append({
                    "module": module_name, "lineno": line,
                    "pattern": "cross_file_unresolved",
                    "note": f"Call '{obj_str}.{prop_str}(...)' - qualifier "
                            f"resolution (namespace imports, object properties) "
                            f"not yet implemented.",
                })

    for child in node.children:
        _walk_calls(src, child, module_name, current_scope, local_funcs, local_classes,
                     alias_map, function_graph, class_graph, calls, unresolved, default_count2)