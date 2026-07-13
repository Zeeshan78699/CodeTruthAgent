"""
language_adapter_bridge.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning), ADDITIVE language bridge.

Fixes the language-layer issues WITHOUT editing any frozen Module 2 file
(adapters or registry.py). It imports the adapters and normalizes them from the
OUTSIDE:

  Problem 1 — registry.classify_files reads `adapter.language_name`; the Go / C# /
              SQL adapters use the older `language` attribute and lack
              `language_name`  ->  AttributeError crash.
  Problem 2 — registry.ADAPTERS omits C# and SQL entirely (they exist in
              run_m2.py's set), so they can't be discovered through the registry.
  Problem 3 — one adapter that fails to import (missing dep) shouldn't take down
              classification for every other language.

This module:
  * reads the language id as `language_name` OR `language` (no adapter edit),
  * assembles the FULL adapter set (all 8) by importing each independently,
  * provides a crash-proof classify_files() and get_adapter().

Frozen files are imported, never modified. Nothing here changes any adapter's
parsing or scan() behaviour.
"""

import os

# (module_name, class_name) for every known adapter, including the two the
# frozen registry omits (csharp, sql).
_ADAPTER_SPECS = [
    ("python_adapter", "PythonAdapter"),
    ("java_adapter", "JavaAdapter"),
    ("javascript_adapter", "JavaScriptAdapter"),
    ("go_adapter", "GoAdapter"),
    ("rust_adapter", "RustAdapter"),
    ("c_cpp_adapter", "CCppAdapter"),
    ("csharp_adapter", "CSharpAdapter"),
    ("sql_adapter", "SQLAdapter"),
]

_ADAPTERS = None


def _load_adapters():
    """Import each adapter independently; a failing import (e.g. missing
    javalang) is skipped, not fatal for the rest."""
    out = []
    for modname, clsname in _ADAPTER_SPECS:
        try:
            mod = __import__(
                f"v3.repository_graph.languages.{modname}", fromlist=[clsname]
            )
            out.append(getattr(mod, clsname)())
        except Exception:
            continue  # adapter unavailable in this environment; skip
    return out


def all_adapters():
    global _ADAPTERS
    if _ADAPTERS is None:
        _ADAPTERS = _load_adapters()
    return _ADAPTERS


def language_name_of(adapter):
    """Language id, tolerant of `language_name` OR the older `language`, never
    raising on a malformed adapter."""
    return (getattr(adapter, "language_name", None)
            or getattr(adapter, "language", None)
            or "unknown")


def get_adapter(language):
    for a in all_adapters():
        if language_name_of(a) == language:
            return a
    return None


def list_languages():
    return sorted(language_name_of(a) for a in all_adapters())


def is_implemented(adapter):
    """Treat adapters without an is_implemented() as implemented (Go/C#/SQL have
    real scan() bodies; they simply predate the contract method)."""
    fn = getattr(adapter, "is_implemented", None)
    if fn is None:
        return True
    try:
        return bool(fn())
    except Exception:
        return True


def classify_files(repo_root, ignore_dirs=None):
    """
    Crash-proof, complete (8-language) replacement for registry.classify_files.
    Returns {language: {"adapter": a, "files": [...]}, "_unclassified": {...}}.
    """
    ignore = ignore_dirs or {
        ".git", "__pycache__", "node_modules", ".venv", "venv",
        "target", "build", "dist", ".gradle", "bin", "obj",
    }
    ext_map = {}
    for a in all_adapters():
        for ext in getattr(a, "file_extensions", set()):
            ext_map.setdefault(ext.lower(), a)

    by_lang = {language_name_of(a): {"adapter": a, "files": []}
               for a in all_adapters()}
    unclassified = {}

    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in ignore]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            a = ext_map.get(ext)
            full = os.path.join(dirpath, fn)
            if a:
                by_lang[language_name_of(a)]["files"].append(full)
            else:
                unclassified[ext] = unclassified.get(ext, 0) + 1

    by_lang["_unclassified"] = {"extensions": unclassified}
    return by_lang


def files_for_language(repo_root, language):
    """Just the file list for one language (used by Module 3's query_repo)."""
    return classify_files(repo_root).get(language, {}).get("files", [])


# --------------------------------------------------------------------------- #
# Self-contained query entry — so NO existing file needs editing.
# Uses reasoning_queries' pure functions (imported, not modified) and this
# module's own resilient adapter discovery (which includes C#/SQL and tolerates
# the missing language_name). Call these instead of editing run_m3/reasoning_*.
# --------------------------------------------------------------------------- #

def query_repo(repo_root, language):
    """
    Build a QuerySurface for any standard-shape language (python/java/
    javascript/c_cpp), additively. C#/Go/SQL emit a custom shape and are
    refused by from_adapter_report with a clear bridge message — honest, not a
    crash. No edit to reasoning_queries.py or run_m3.py required.
    """
    from v3.repository_reasoning.reasoning_queries import from_adapter_report

    adapter = get_adapter(language)
    if adapter is None:
        raise ValueError(
            f"no adapter for language '{language}'. known: {list_languages()}")
    if not is_implemented(adapter):
        raise ValueError(f"{language} adapter is a stub (not implemented)")

    files = files_for_language(repo_root, language)
    if not files:
        raise ValueError(f"no {language} files found under {repo_root}")

    report = adapter.scan(repo_root, files)
    return from_adapter_report(report, language=language)


def answer(repo_root, language, kind, target=None, target2=None, **kw):
    """
    One-call engineering query for any standard-shape language. `kind` is one of:
    who-calls | paths-to | impact | depends-on-class | dead-code | paths-between.
    Returns the same boundary-labeled dict the Python path returns.
    """
    from v3.repository_reasoning import reasoning_queries as RQ
    qs = query_repo(repo_root, language)
    dispatch = {
        "who-calls":        lambda: RQ.who_calls(target, qs.rev),
        "paths-to":         lambda: RQ.paths_to(target, qs.rev, **kw),
        "impact":           lambda: RQ.impact_of(target, qs.rev, **kw),
        "depends-on-class": lambda: RQ.depends_on_class(target, qs.fwd, qs.rev),
        "dead-code":        lambda: RQ.dead_code(qs.fwd, qs.rev, **kw),
        "paths-between":    lambda: RQ.paths_between(target, target2, qs.fwd, **kw),
    }
    if kind not in dispatch:
        raise ValueError(f"unknown query kind '{kind}'. options: {sorted(dispatch)}")
    return dispatch[kind]()


# --------------------------------------------------------------------------- #
# Advanced reasoning entry (language-agnostic, additive).
# --------------------------------------------------------------------------- #
def advanced(repo_root, language, kind, target=None, target2=None, **kw):
    """
    Advanced deterministic reasoning for any standard-shape language.
    `kind`: recursion | impact-depth | chokepoints | hotspots | reachable |
            shortest-path.
    """
    from v3.repository_reasoning import advanced_reasoning as AR
    qs = query_repo(repo_root, language)
    R = AR.AdvancedReasoner(qs.fwd, qs.rev)
    dispatch = {
        "recursion":     lambda: R.recursion_clusters(),
        "impact-depth":  lambda: R.impact_by_depth(target, **kw),
        "chokepoints":   lambda: R.chokepoints_for(target),
        "hotspots":      lambda: R.hotspots(**kw),
        "reachable":     lambda: R.reachable_from(target, **kw),
        "shortest-path": lambda: R.shortest_path(target, target2, **kw),
    }
    if kind not in dispatch:
        raise ValueError(f"unknown advanced kind '{kind}'. options: {sorted(dispatch)}")
    return dispatch[kind]()


# --------------------------------------------------------------------------- #
# Real caller-aware call graphs for adapters that dropped the caller (Go, C#).
# These RE-PARSE source in Module 3 (frozen adapters untouched) to recover the
# enclosing function, producing a standard call_graph the 3B layer consumes.
# --------------------------------------------------------------------------- #
def query_repo_reparsed(repo_root, language):
    """QuerySurface for Go / C# built from Module 3's own caller-aware re-parse,
    since their Module 2 adapters record callees but not callers."""
    from v3.repository_reasoning.reasoning_queries import from_adapter_report
    if language == "go":
        from v3.repository_reasoning import go_call_graph as M
    elif language == "csharp":
        from v3.repository_reasoning import csharp_call_graph as M
    else:
        raise ValueError(f"no re-parser for '{language}' (have: go, csharp)")
    report = M.analyze(repo_root)          # already standard call_graph shape
    return from_adapter_report(report, language=language)


def advanced_reparsed(repo_root, language, kind, target=None, target2=None, **kw):
    from v3.repository_reasoning import advanced_reasoning as AR
    qs = query_repo_reparsed(repo_root, language)
    R = AR.AdvancedReasoner(qs.fwd, qs.rev)
    d = {
        "recursion": lambda: R.recursion_clusters(),
        "impact-depth": lambda: R.impact_by_depth(target, **kw),
        "chokepoints": lambda: R.chokepoints_for(target),
        "hotspots": lambda: R.hotspots(**kw),
        "reachable": lambda: R.reachable_from(target, **kw),
        "shortest-path": lambda: R.shortest_path(target, target2, **kw),
    }
    if kind not in d:
        raise ValueError(f"unknown advanced kind '{kind}'")
    return d[kind]()


# --------------------------------------------------------------------------- #
# SQL is a SEPARATE paradigm (data lineage, not a call graph). Its own entry.
# --------------------------------------------------------------------------- #
def sql_lineage_model(repo_root):
    from v3.repository_reasoning import sql_lineage as S
    return S.analyze(repo_root)


def sql_lineage(repo_root, kind, table=None):
    from v3.repository_reasoning import sql_lineage as S
    m = S.analyze(repo_root)
    d = {
        "writers": lambda: S.writers_of(table, m),
        "readers": lambda: S.readers_of(table, m),
        "upstream": lambda: S.upstream_of(table, m),
        "impact": lambda: S.impact_of_table(table, m),
        "summary": lambda: {"counts": m["counts"], "boundary": m["boundary"]},
    }
    if kind not in d:
        raise ValueError(f"unknown sql lineage kind '{kind}'. options: {sorted(d)}")
    return d[kind]()
