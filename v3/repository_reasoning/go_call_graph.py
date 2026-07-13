"""
go_call_graph.py
CodeTruth Agent V3 — Module 3, REAL caller-aware call graph for Go. Additive.

The Go Module 2 adapter records a call's package but NOT its enclosing function,
so directed {caller, callee} edges can't be built from its output. This module
re-parses Go source (the adapter is untouched) and recovers the caller by
tracking function scope via brace depth — the same lightweight technique the
adapters use, made caller-aware.

Produces the STANDARD call_graph shape ({module: [{caller, callee, lineno,
resolution}]}) so the existing 3B query surface + advanced_reasoning consume it
directly.

Resolution (deterministic, labelled):
  same_package_func   - unqualified F() resolves to a func defined in the same
                        Go package (= same directory)  -> internal edge
  method_on_receiver  - v.M() where v's type is known (receiver / param / := /
                        var) and (Type, M) is defined in the package -> internal
  (everything else: cross-package pkg.F(), stdlib, dynamic) -> not emitted as an
  internal edge; left out honestly rather than guessed.

HONESTY: this is brace/heuristic parsing (no Go AST in pure Python). Strings and
comments are stripped first to keep brace counting sane, but generics, embedded
struct promotion, interface dispatch, and multi-package resolution are NOT
modelled. Edges are exact for same-package funcs and typed-receiver methods.
"""

import os
import re

_LINE_COMMENT = re.compile(r"//[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_STRING = re.compile(r'"(?:\\.|[^"\\])*"' r"|`[^`]*`" r"|'(?:\\.|[^'\\])'")

# func Name(  |  func (r *T) Name(  |  func (r T) Name(
_FUNC = re.compile(r'^\s*func\s+(?:\(\s*(\w+)\s+\*?\s*(\w+)\s*\)\s+)?(\w+)\s*\(')
# var x Type   |   x := ...   |   x, y := ...
_VAR_DECL = re.compile(r'^\s*var\s+(\w+)\s+\*?(\w+)')
_SHORT_NEW = re.compile(r'^\s*(\w+)\s*:=\s*&?(\w+)\s*\{')        # x := T{...} / &T{}
_SHORT_CALL = re.compile(r'^\s*(\w+)\s*:=\s*(\w+)\s*\(')          # x := New(...) (return type unknown)
_PARAM = re.compile(r'(\w+)\s+\*?(\w+)')
_CALL = re.compile(r'(?:(\w+)\s*\.\s*)?(\w+)\s*\(')

_GO_KW = {
    "if", "for", "switch", "select", "return", "go", "defer", "func", "range",
    "case", "else", "var", "const", "type", "struct", "interface", "map",
    "chan", "package", "import", "make", "new", "len", "cap", "append", "panic",
    "recover", "print", "println", "string", "int", "error", "bool", "byte",
    "nil", "true", "false", "iota", "default", "break", "continue", "goto",
    "fallthrough", "and", "or",
}


def _strip(src):
    src = _BLOCK_COMMENT.sub(" ", src)
    src = _LINE_COMMENT.sub("", src)
    src = _STRING.sub('""', src)
    return src


def _normalize_lines(src):
    """Formatting-independent scope tracking: break lines on { } so odd
    formatting cannot silently zero the parse."""
    import re as _re
    return _re.sub(r'([{}])', r'\1\n', src)


def _pkg_id(repo_root, filepath):
    rel = os.path.relpath(os.path.dirname(filepath), repo_root)
    if rel in (".", ""):
        return "main"
    return rel.replace(os.sep, ".").replace("/", ".")


def _go_files(repo_root):
    out = []
    ignore = {".git", "vendor", "testdata", "node_modules"}
    for dp, dn, fn in os.walk(repo_root):
        dn[:] = [d for d in dn if d not in ignore]
        for f in fn:
            if f.endswith(".go"):
                out.append(os.path.join(dp, f))
    return out


def _func_id(pkg, recv_type, name):
    return f"{pkg}.{recv_type}.{name}" if recv_type else f"{pkg}.{name}"


def analyze(repo_root):
    files = _go_files(repo_root)

    # ---- pass 1: per-package function + method tables ----
    pkg_funcs = {}     # pkg -> {name: id}
    pkg_methods = {}   # pkg -> {(recv_type, name): id}
    pkg_types = {}     # pkg -> set(type names defined)
    parsed = {}        # filepath -> (pkg, stripped_lines)

    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                src = _normalize_lines(_strip(fh.read()))
        except Exception:
            continue
        pkg = _pkg_id(repo_root, fp)
        lines = src.split("\n")
        parsed[fp] = (pkg, lines)
        pkg_funcs.setdefault(pkg, {})
        pkg_methods.setdefault(pkg, {})
        pkg_types.setdefault(pkg, set())
        for ln in lines:
            fm = _FUNC.match(ln)
            if fm:
                recv_type, name = fm.group(2), fm.group(3)
                if recv_type:
                    pkg_methods[pkg][(recv_type, name)] = _func_id(pkg, recv_type, name)
                else:
                    pkg_funcs[pkg][name] = _func_id(pkg, None, name)
            tm = re.match(r'^\s*type\s+(\w+)\s+struct', ln)
            if tm:
                pkg_types[pkg].add(tm.group(1))

    # ---- pass 2: attribute calls to enclosing function, resolve ----
    call_graph = {}
    counts = {"same_package_func": 0, "method_on_receiver": 0,
              "external_or_unresolved": 0}

    for fp, (pkg, lines) in parsed.items():
        edges = []
        depth = 0
        stack = []          # (func_id, body_depth, local_types{})
        pending = None      # (func_id, local_types) awaiting opening brace
        for i, line in enumerate(lines):
            fm = _FUNC.match(line)
            if fm:
                recv_var, recv_type, name = fm.group(1), fm.group(2), fm.group(3)
                fid = _func_id(pkg, recv_type, name)
                local = {}
                if recv_var and recv_type:
                    local[recv_var] = recv_type
                # params: text between first '(' after name and the matching ')'
                pstart = line.find("(", line.find(name))
                if pstart != -1:
                    pend = line.find(")", pstart)
                    if pend != -1:
                        for pm in _PARAM.finditer(line[pstart + 1:pend]):
                            local[pm.group(1)] = pm.group(2)
                pending = (fid, local)

            # local type tracking inside current function
            if stack:
                cur_local = stack[-1][2]
                vm = _VAR_DECL.match(line)
                if vm:
                    cur_local[vm.group(1)] = vm.group(2)
                nm = _SHORT_NEW.match(line)
                if nm:
                    cur_local[nm.group(1)] = nm.group(2)

            # brace accounting + scope push/pop
            for ch in line:
                if ch == "{":
                    depth += 1
                    if pending is not None:
                        stack.append((pending[0], depth, pending[1]))
                        pending = None
                elif ch == "}":
                    if stack and depth == stack[-1][1]:
                        stack.pop()
                    depth -= 1

            if not stack:
                continue
            caller, _bd, local = stack[-1]

            # skip a func declaration line itself (its name( ) is not a call)
            if _FUNC.match(line):
                continue

            for cm in _CALL.finditer(line):
                qual, method = cm.group(1), cm.group(2)
                if method in _GO_KW:
                    continue
                if qual is None:
                    # unqualified -> same-package func?
                    tgt = pkg_funcs.get(pkg, {}).get(method)
                    if tgt and tgt != caller or (tgt and tgt == caller):
                        if tgt:
                            edges.append({"caller": caller, "callee": tgt,
                                          "lineno": i + 1,
                                          "resolution": "go_same_package_func"})
                            counts["same_package_func"] += 1
                            continue
                    counts["external_or_unresolved"] += 1
                else:
                    if qual in _GO_KW:
                        counts["external_or_unresolved"] += 1
                        continue
                    # qual is a local var with known type -> method on receiver
                    rtype = local.get(qual)
                    if rtype:
                        tgt = pkg_methods.get(pkg, {}).get((rtype, method))
                        if tgt:
                            edges.append({"caller": caller, "callee": tgt,
                                          "lineno": i + 1,
                                          "resolution": "go_method_on_receiver"})
                            counts["method_on_receiver"] += 1
                            continue
                    counts["external_or_unresolved"] += 1  # cross-package / unknown
        if edges:
            call_graph[fp] = edges

    return {
        "language": "go", "repo": repo_root,
        "files_parsed": len(parsed),
        "packages": len(pkg_funcs),
        "call_graph": call_graph,
        "counts": counts,
        "boundary": "brace-heuristic re-parse (no Go AST). Resolves same-package "
                    "function calls and typed-receiver method calls; cross-package, "
                    "interface dispatch, embedding, and generics are not modelled. "
                    "Callers are recovered by scope tracking (the adapter dropped "
                    "them). Lower confidence than AST-based Java.",
    }
