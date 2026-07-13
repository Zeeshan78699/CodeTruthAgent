"""
csharp_call_graph.py
CodeTruth Agent V3 — Module 3, REAL caller-aware call graph for C#. Additive.

The C# Module 2 adapter (regex) records a call's receiver object + method but NOT
the enclosing method, so directed {caller, callee} edges can't be built from it.
This module re-parses C# source with brace-depth scope tracking to recover the
caller, and types receivers from field/parameter/local declarations (the same
signal the adapter's field_type_resolver uses) to resolve `recv.Method()`.

Emits the STANDARD call_graph shape so 3B + advanced_reasoning consume it.

Resolution (deterministic, labelled):
  csharp_same_type_method  - this.M() / M() resolves to a method of the enclosing
                             class -> internal edge
  csharp_field_type_method - recv.M() where recv is a field/param/local typed as
                             a repo class, and M is a method of that class
  (cross-assembly, framework, generics, interface dispatch -> not emitted)

HONESTY: regex + brace heuristic (no Roslyn/C# AST). Strings, chars, and comments
are stripped to keep brace counting sane. Overloads, inheritance, partial classes,
generics, and properties-as-calls are not modelled. Lower confidence than AST.
"""

import os
import re

_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_STRING = re.compile(r'@?"(?:\\.|[^"\\])*"' r"|'(?:\\.|[^'\\])'")

_NS = re.compile(r'^\s*namespace\s+([\w.]+)')
_CLASS = re.compile(r'^\s*(?:public|internal|private|protected|sealed|static|abstract|partial|\s)*\bclass\s+(\w+)')
# return-type Name(  with optional modifiers; excludes control keywords
_METHOD = re.compile(
    r'^\s*(?:public|private|protected|internal|static|virtual|override|async|sealed|abstract|extern|unsafe|\s)+'
    r'[\w<>\[\],\.\?]+\s+(\w+)\s*\([^;]*\)\s*\{?')
_FIELD = re.compile(
    r'^\s*(?:public|private|protected|internal|readonly|static|\s)*'
    r'([A-Z][\w<>]*)\s+(\w+)\s*[;=]')
_LOCAL = re.compile(r'^\s*(?:var|([A-Z][\w<>]*))\s+(\w+)\s*=')
_PARAM = re.compile(r'([A-Z][\w<>]*)\s+(\w+)')
_CALL = re.compile(r'(?:(\w+)\s*\.\s*)?(\w+)\s*\(')

_KW = {
    "if", "for", "foreach", "while", "switch", "return", "using", "lock",
    "catch", "throw", "new", "await", "yield", "get", "set", "var", "class",
    "void", "int", "string", "bool", "double", "float", "char", "object",
    "this", "base", "null", "true", "false", "typeof", "nameof", "sizeof",
    "default", "case", "else", "do", "break", "continue", "namespace",
    "public", "private", "protected", "internal", "static", "readonly",
    "async", "override", "virtual", "abstract", "sealed", "partial",
}


def _strip(src):
    src = _BLOCK_COMMENT.sub(" ", src)
    src = _LINE_COMMENT.sub("", src)
    src = _STRING.sub('""', src)
    return src


def _normalize_lines(src):
    """Make scope tracking formatting-independent: ensure { } ; each break the
    line, so minified / one-line C# parses the same as conventionally formatted
    code. A parser must degrade gracefully on odd formatting, not vanish."""
    src = re.sub(r'([{};])', r'\1\n', src)
    return src


def _csharp_files(repo_root):
    out = []
    ignore = {".git", "bin", "obj", "packages", "node_modules", ".vs"}
    for dp, dn, fn in os.walk(repo_root):
        dn[:] = [d for d in dn if d not in ignore]
        for f in fn:
            if f.endswith(".cs"):
                out.append(os.path.join(dp, f))
    return out


def analyze(repo_root):
    files = _csharp_files(repo_root)
    parsed = {}                  # fp -> stripped lines
    class_methods = {}           # ClassName -> set(methods)

    # pass 1: class -> methods table (simple-name keyed; C# resolves by simple name)
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                lines = _normalize_lines(_strip(fh.read())).split("\n")
        except Exception:
            continue
        parsed[fp] = lines
        cur_class = None
        depth = 0
        cstack = []
        pending_class = None
        for ln in lines:
            cm = _CLASS.match(ln)
            if cm:
                pending_class = cm.group(1)
                class_methods.setdefault(pending_class, set())
            mm = _METHOD.match(ln)
            if mm and cstack:
                class_methods.setdefault(cstack[-1], set()).add(mm.group(1))
            for ch in ln:
                if ch == "{":
                    depth += 1
                    if pending_class is not None:
                        cstack.append(pending_class); pending_class = None
                    else:
                        cstack.append(cstack[-1] if cstack else None)
                elif ch == "}":
                    if cstack: cstack.pop()
                    depth -= 1

    # pass 2: recover caller, type receivers, resolve
    call_graph = {}
    counts = {"csharp_same_type_method": 0, "csharp_field_type_method": 0,
              "external_or_unresolved": 0}

    for fp, lines in parsed.items():
        edges = []
        depth = 0
        # stacks track class + method scopes with their body depth
        cstack = []          # (class_name, body_depth)
        mstack = []          # (method_id, body_depth, locals{})
        pending_class = None
        pending_method = None
        field_types = {}     # class_name -> {field: Type}

        for i, line in enumerate(lines):
            cm = _CLASS.match(line)
            if cm:
                pending_class = cm.group(1)
                field_types.setdefault(cm.group(1), {})
            # field decl (class scope)
            if cstack and not mstack:
                fdm = _FIELD.match(line)
                if fdm and fdm.group(1) not in _KW:
                    field_types.setdefault(cstack[-1][0], {})[fdm.group(2)] = fdm.group(1)
            mm = _METHOD.match(line)
            if mm and cstack and mm.group(1) not in _KW:
                cls = cstack[-1][0]
                mid = f"{cls}.{mm.group(1)}"
                local = {}
                # params
                ps = line.find("("); pe = line.find(")", ps)
                if ps != -1 and pe != -1:
                    for pm in _PARAM.finditer(line[ps + 1:pe]):
                        if pm.group(1) not in _KW:
                            local[pm.group(2)] = pm.group(1)
                pending_method = (mid, local, cls)

            # local var decls inside a method
            if mstack:
                lm = _LOCAL.match(line)
                if lm and lm.group(1) and lm.group(1) not in _KW:
                    mstack[-1][2][lm.group(2)] = lm.group(1)

            # brace accounting
            for ch in line:
                if ch == "{":
                    depth += 1
                    if pending_method is not None:
                        mstack.append([pending_method[0], depth, pending_method[1], pending_method[2]])
                        pending_method = None
                    elif pending_class is not None:
                        cstack.append((pending_class, depth)); pending_class = None
                    else:
                        pass
                elif ch == "}":
                    if mstack and depth == mstack[-1][1]:
                        mstack.pop()
                    elif cstack and depth == cstack[-1][1]:
                        cstack.pop()
                    depth -= 1

            if not mstack:
                continue
            if _METHOD.match(line):
                continue
            caller, _bd, local, cls = mstack[-1]

            for call in _CALL.finditer(line):
                qual, method = call.group(1), call.group(2)
                if method in _KW:
                    continue
                if qual in (None, "this"):
                    if method in class_methods.get(cls, set()):
                        edges.append({"caller": caller, "callee": f"{cls}.{method}",
                                      "lineno": i + 1,
                                      "resolution": "csharp_same_type_method"})
                        counts["csharp_same_type_method"] += 1
                    else:
                        counts["external_or_unresolved"] += 1
                else:
                    if qual in _KW:
                        counts["external_or_unresolved"] += 1
                        continue
                    rtype = local.get(qual) or field_types.get(cls, {}).get(qual)
                    if rtype and method in class_methods.get(rtype, set()):
                        edges.append({"caller": caller, "callee": f"{rtype}.{method}",
                                      "lineno": i + 1,
                                      "resolution": "csharp_field_type_method"})
                        counts["csharp_field_type_method"] += 1
                    else:
                        counts["external_or_unresolved"] += 1
        if edges:
            call_graph[fp] = edges

    return {
        "language": "csharp", "repo": repo_root,
        "files_parsed": len(parsed),
        "classes": len(class_methods),
        "call_graph": call_graph,
        "counts": counts,
        "boundary": "regex + brace heuristic (no C# AST). Resolves same-class "
                    "method calls and field/param/local typed-receiver calls; "
                    "overloads, inheritance, partial classes, generics, interface "
                    "dispatch are not modelled. Caller recovered by scope tracking "
                    "(the adapter dropped it). Lower confidence than AST-based Java.",
    }
