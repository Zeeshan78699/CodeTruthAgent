"""
run_codetruth.py — CodeTruth PLATFORM entry point (NOT part of any module).

Orchestrates the full deterministic pipeline per PLATFORM_CONTRACT.md:

    Module 1 (cognition + gate) -> gate check -> Module 2 (structure, scanned ONCE)
    -> Module 3 (reasoning, RECEIVES the M2 scan; does not re-scan)

Responsibilities (and ONLY these): execution order, governance gate enforcement,
data passing (one scan), error handling, final report assembly.
NO reasoning, type inference, or graph analysis of its own.

Dev entry points (run_m1.py / run_m2.py / run_m3.py) are untouched — this is the
production pipeline that runs all three in one governed pass.

USAGE:
    python run_codetruth.py "C:\\repos\\your_repo"
    python run_codetruth.py "C:\\repos\\your_repo" --json --save
    python run_codetruth.py "C:\\repos\\your_repo" --force   # proceed past REVIEW_REQUIRED
"""

import sys
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import json
from pathlib import Path
from datetime import datetime as dt, UTC

# ---------------------------------------------------------------------------
# Location-robust import bootstrap — finds the folder that CONTAINS the `v3`
# package by walking upward, so this runner works from ANY location (e.g. a
# main_pipeline_to_run/ subfolder or a future final-files layout) without the
# `from v3....` imports breaking. Honours a CODETRUTH_ROOT env override; falls
# back to the original assumption if no marker is found.
# ---------------------------------------------------------------------------
import os
from pathlib import Path


def _find_codetruth_root(start: Path) -> Path:
    env = os.environ.get("CODETRUTH_ROOT")
    if env and (Path(env) / "v3" / "repository_cognition").is_dir():
        return Path(env)
    for parent in [start, *start.parents]:
        if (parent / "v3" / "repository_cognition").is_dir():
            return parent
    return start.parent


CODETRUTH_ROOT = _find_codetruth_root(Path(__file__).resolve().parent)
sys.path.insert(0, str(CODETRUTH_ROOT))          # enables `import v3.<pkg>`
sys.path.insert(0, str(CODETRUTH_ROOT / "v3"))   # enables bare v3-relative imports
V3_ROOT = CODETRUTH_ROOT / "v3"                   # backward-compatible alias

GATE_EMOJI = {"APPROVED": "OK", "REVIEW_REQUIRED": "WARN", "BLOCKED": "STOP"}

# language detection + adapter selection — inlined (avoids importing pipeline.py,
# which does its own sys.path manipulation as a script). Same logic as pipeline.py.
DOMAIN_TO_LANGUAGE = {
    "ERP_SYSTEM": "sql", "WELL_LOGGING": "python", "DRILLING_SYSTEM": "python",
    "RESERVOIR_ENGINEERING": "python", "FLUIDS_ENGINEERING": "python",
    "AEROSPACE_STRUCTURAL_SIMULATION": "python", "ENERGY_SYSTEM": "python",
    "SPACE_SYSTEM": "python", "MEDICAL_SYSTEM": "python", "FINANCE_SYSTEM": "python",
}


import contextlib


@contextlib.contextmanager
def _deep_recursion(limit=20000):
    """Temporarily raise Python's recursion limit for parsers that recurse deeply
    on very large ASTs (javalang on elasticsearch-scale Java hits the default
    1000-frame cap and raises RecursionError, aborting the whole scan).

    The limit is ALWAYS restored, so this never leaks into the rest of the
    pipeline. This raises the ceiling on *catchable* recursion; it does not make
    parsing unbounded — a genuinely pathological file can still exhaust the C
    stack, which the caller reports honestly as M2_ERROR rather than hiding.
    """
    old = sys.getrecursionlimit()
    if limit > old:
        sys.setrecursionlimit(limit)
    try:
        yield
    finally:
        sys.setrecursionlimit(old)


def _files_for_language(repo_root, language):
    """Real file list for the selected language, via the language bridge's
    classify_files (the same source the validated bridge paths use). Returns []
    on any failure, so behaviour is never worse than the previous file_paths=[]."""
    try:
        from v3.repository_reasoning.language_adapter_bridge import files_for_language
        return files_for_language(repo_root, language) or []
    except Exception:
        return []


# --------------------------------------------------------------------------- #
# Per-language Module 3 reasoning (ADDITIVE — frozen Python M3 untouched).
#
# Each language declares, in a COMMON ENVELOPE, the engine that ran, the
# capabilities it genuinely provides, and its real limitations. No language is
# forced into Python-M3's schema: `truth_boundary.guesses` / `edge_provenance`
# are Python-3A/3B concepts, and emitting them for Java would assert a guarantee
# that path never measured.
# --------------------------------------------------------------------------- #
_M3_ENGINES = {
    # standard call-graph shape -> bridge.answer()
    "java":       ("bridge.answer", "advanced",
                   ["call_graph", "who_calls", "impact", "dead_code", "depends_on_class"],
                   "Java structural reasoning over the verified call graph",
                   ["reflection", "runtime bytecode generation", "dynamic proxies",
                    "cross-file calls not type-resolvable", "annotation-driven invocation"]),
    "javascript": ("bridge.answer", "advanced",
                   ["call_graph", "who_calls", "impact", "dead_code"],
                   "JavaScript structural reasoning over the verified call graph",
                   ["dynamic dispatch", "eval / dynamic import", "prototype mutation",
                    "framework-injected callbacks"]),
    "c_cpp":      ("bridge.answer", "advanced",
                   ["call_graph", "who_calls", "impact", "dead_code"],
                   "C/C++ structural reasoning over the verified call graph",
                   ["function pointers", "preprocessor-conditional code",
                    "template instantiation", "linker-resolved symbols"]),
    # custom adapter shape -> Module 3 re-parses to recover callers
    "go":         ("bridge.advanced_reparsed", "advanced_reparsed",
                   ["call_graph", "hotspots", "chokepoints", "recursion", "reachable"],
                   "Go reasoning over a caller-aware re-parse (the Module 2 adapter "
                   "records callees but not callers)",
                   ["cross-package calls", "interface dispatch", "struct embedding",
                    "generics", "brace-heuristic parse (no Go AST)"]),
    "csharp":     ("bridge.advanced_reparsed", "advanced_reparsed",
                   ["call_graph", "hotspots", "chokepoints", "recursion", "reachable"],
                   "C# reasoning over a caller-aware re-parse (the Module 2 adapter "
                   "records callees but not callers)",
                   ["overloads", "inheritance", "partial classes", "generics",
                    "interface dispatch", "regex + brace heuristic (no C# AST)"]),
    # different paradigm entirely -> data lineage, not a call graph
    "sql":        ("bridge.sql_lineage", "sql_lineage",
                   ["data_lineage", "table_reads", "table_writes", "upstream", "impact"],
                   "SQL data lineage (reads/writes attributed to enclosing objects) — "
                   "a data-flow model, not a call graph",
                   ["dynamic SQL (EXECUTE IMMEDIATE)", "CTEs",
                    "dialect-specific constructs", "regex + scope heuristic (no SQL grammar)"]),
}


def _module3_for_language(repo_root, language):
    """Run the validated language-bridge reasoning path for a non-Python language
    and wrap it in the common envelope. Never fabricates: if the language has no
    reasoning engine (e.g. the rust stub) or the engine fails, that is reported
    plainly and no capabilities are claimed."""
    spec = _M3_ENGINES.get(language)
    if spec is None:
        return {
            "language": language,
            "engine": None,
            "status": "NOT_IMPLEMENTED",
            "capabilities": [],
            "truth_boundary": {
                "scope": f"No Module 3 reasoning engine is implemented for {language}.",
                "limitations": ["no call graph", "no reasoning queries"],
            },
            "note": f"Module 2 structure only; {language} reasoning not implemented "
                    f"(honest boundary — nothing is inferred).",
        }

    engine_name, kind, capabilities, scope, limitations = spec
    env = {
        "language": language,
        "engine": engine_name,
        "status": "COMPLETE",
        "capabilities": capabilities,
        "truth_boundary": {"scope": scope, "limitations": limitations},
    }
    try:
        from v3.repository_reasoning import language_adapter_bridge as B
        with _deep_recursion(20000):   # bridge engines re-parse source; same cap applies
            if kind == "advanced":
                qs = B.query_repo(repo_root, language)
                env["graph"] = {"functions_in_index": len(qs.fwd),
                                "callers_in_index": len(qs.rev)}
            elif kind == "advanced_reparsed":
                qs = B.query_repo_reparsed(repo_root, language)
                env["graph"] = {"functions_in_index": len(qs.fwd),
                                "callers_in_index": len(qs.rev)}
            elif kind == "sql_lineage":
                summary = B.sql_lineage(repo_root, "summary")
                env["lineage"] = summary.get("counts", {})
                env["truth_boundary"]["scope"] = summary.get("boundary", scope)
    except Exception as e:
        # Honest failure: engine exists but could not run on this repository.
        env["status"] = "ENGINE_ERROR"
        env["capabilities"] = []
        env["error"] = f"{type(e).__name__}: {e}"
        env["truth_boundary"]["limitations"] = limitations + [
            "reasoning engine did not complete on this repository; no findings claimed"]
    return env


def _has_reasoning_artifacts(m3_block):
    """True iff Module 3's reasoning engine produced primary artifacts.

    Extracted so there is exactly ONE implementation. It was previously inline in
    run_platform, which forced any inspector (pipeline.py) to re-implement it —
    producing one router and two guards. A second implementation of a pipeline
    decision will drift, and nothing will catch it."""
    m3 = m3_block or {}
    if m3.get("status") != "COMPLETE":
        return False
    graph = m3.get("graph", {}) or {}
    lineage = m3.get("lineage", {}) or {}
    return ((graph.get("functions_in_index", 0) or 0) > 0
            or any(isinstance(v, int) and v > 0 for v in lineage.values()))


def _has_primary_artifacts(language, m2_summary, m2_scan):
    """True iff the selected adapter produced meaningful PRIMARY artifacts for its
    analysis mode. Language-agnostic and paradigm-aware, so it stays correct as more
    languages integrate:
      - graph languages (python/java/javascript/c_cpp/go/csharp):
            functions > 0 OR call_graph_edges > 0
      - sql (data-lineage paradigm, no functions):
            objects/tables/reads/writes/data_flows > 0
    Reads only Module 2's OUTPUT — it does not touch or re-run any frozen adapter."""
    m2 = m2_summary or {}
    if language == "sql":
        # SQL's primary artifacts are schema objects + lineage, not functions.
        # The SQL adapter emits these at the TOP LEVEL of its scan (no 'counts'
        # dict): tables/views/procedures/functions/triggers/packages as lists,
        # plus edge_counts / resolved_calls for lineage.
        scan = m2_scan or {}
        for key in ("tables", "views", "procedures", "functions",
                    "triggers", "packages"):
            v = scan.get(key)
            if isinstance(v, (list, dict)) and len(v):
                return True
        for key in ("edge_counts", "node_counts", "resolved_calls"):
            v = scan.get(key)
            if isinstance(v, (list, dict)) and len(v):
                return True
            if isinstance(v, int) and v > 0:
                return True
        return False
    # default: graph-based languages
    try:
        functions = int(m2.get("functions", 0) or 0)
        edges = int(m2.get("call_graph_edges", 0) or 0)
    except (TypeError, ValueError):
        functions, edges = 0, 0
    return functions > 0 or edges > 0


# Declaration files. A header is #included into a translation unit and counted
# again in the object that unit produces. Counting it as source double-counts the
# same code — and on a header-heavy C++ tree it can outvote a language whose files
# are all translation units.
#
# Measured on PyTorch:
#     c_cpp  4,733 = 2,361 declarations + 2,372 translation units
#     python 4,609 = 4,609 translation units
# Headers are 49.9% of the c_cpp count. They routed the repository to c_cpp,
# forfeiting a 143,436-function Python analysis carrying `guesses: 0` and exact
# edge provenance. Strip them and Python leads 1.94x. micropython flips the same
# way. Across the 74-repo corpus, exactly two repositories change language.
#
# `.d.ts` is matched by name, not suffix — Path('x.d.ts').suffix is '.ts'.
_DECLARATION_EXTENSIONS = {
    ".h", ".hpp", ".hh", ".hxx",   # C / C++ headers
    ".cuh",                        # CUDA headers
    ".inl", ".ipp", ".tcc",        # inline / template bodies, included not compiled
    ".pyi",                        # Python stubs — declarations, never executed
}
_DECLARATION_SUFFIXES = (".d.ts",)  # TypeScript declaration files


def _is_declaration(path):
    name = os.path.basename(str(path)).lower()
    if name.endswith(_DECLARATION_SUFFIXES):
        return True
    return os.path.splitext(name)[1] in _DECLARATION_EXTENSIONS


def _dominance_counts(classified, adapter_langs):
    """Files that get a VOTE in deciding the repository's language.

    This is NOT the file list handed to the adapter. The C/C++ adapter parses
    headers for declarations and must keep receiving them. They simply do not
    vote on which language the repository *is*.

    Header-only libraries are real: many C++ template libraries ship nothing but
    `.hpp`. For those, the declarations ARE the source. So the rule is not
    'strip headers' — it is 'prefer translation units, and fall back to the full
    count for any language that has none'.

    Returns {language: (votes, translation_units, declarations)} for audit.
    """
    out = {}
    for lang, d in classified.items():
        if lang == "_unclassified" or lang not in adapter_langs:
            continue
        files = d.get("files") or []
        if not files:
            continue
        decls = sum(1 for f in files if _is_declaration(f))
        units = len(files) - decls
        # header-only: the declarations are this language's source
        votes = units if units else len(files)
        out[lang] = (votes, units, decls)
    return out


def _dominant_or_tie(tally):
    """The winner, or None when the top two are tied.

    `max()` breaks ties by iteration order. A dictionary's insertion order is not
    evidence. If two languages have equal votes, nothing in the repository
    decides between them, and the router must say so rather than let adapter
    load order pick a language.
    """
    if not tally:
        return None, None
    ranked = sorted(tally.items(), key=lambda kv: -kv[1][0])
    if len(ranked) > 1 and ranked[0][1][0] == ranked[1][1][0]:
        return None, [ranked[0][0], ranked[1][0]]
    return ranked[0][0], None


def detect_language(m1_core, repo_root=None):
    """Select the analysis language by EVIDENCE (actual file composition), not by
    a domain guess. Order of preference:
      1. Module 1's language_composition (if populated) — ranked by file_count.
      2. The language bridge's classify_files(repo_root) — counts real files per
         language on disk (evidence-based; the correct primary source).
      3. DOMAIN_TO_LANGUAGE fallback — LAST RESORT only, when neither above yields
         a language. Flagged low-confidence via detect_language_meta(); never the
         primary router. (This is the path that mis-routed odoo ERP_SYSTEM->sql.)
    Returns just the language string; use detect_language_meta() for provenance."""
    return detect_language_meta(m1_core, repo_root)[0]


def detect_language_meta(m1_core, repo_root=None):
    """Like detect_language but returns (language, source, confidence) so callers
    can flag fallback-based selections honestly.

    IMPORTANT: every language with a registered adapter belongs here — INCLUDING
    stubs like rust. Excluding a stub does not make the pipeline honest; it makes
    it silently analyze the wrong language. (Omitting rust routed a 36,176-file
    Rust repository to its 190 JavaScript files and reported COMPLETE.) A stub
    must be *selected* so it can *honestly refuse*: dominant language wins, then
    the adapter/Module-3 envelope reports NOT_IMPLEMENTED and claims nothing.
    """
    adapter_langs = {"python", "csharp", "sql", "go", "java", "javascript",
                     "c_cpp", "rust"}

    # 1. Module 1's own composition, if it actually populated file counts
    lang_comp = getattr(m1_core, "language_composition", {}) or {}
    if lang_comp:
        ranked = sorted(lang_comp.items(),
                        key=lambda x: x[1].get("file_count", 0) if isinstance(x[1], dict) else 0,
                        reverse=True)
        for lang, _ in ranked:
            if lang in adapter_langs:
                return (lang, "module1_language_composition", "high", {})

    # 2. Evidence-based: count real files on disk via the language bridge.
    #    Declarations do not vote (see _dominance_counts). The adapter still
    #    receives them; they merely do not decide which language the repo IS.
    if repo_root:
        try:
            from v3.repository_reasoning.language_adapter_bridge import classify_files
            cf = classify_files(repo_root)
            tally = _dominance_counts(cf, adapter_langs)
            dominant, tied = _dominant_or_tie(tally)
            if dominant:
                return (dominant, "bridge_classify_files", "high", tally)
            if tied:
                # Nothing in the repository decides. Do not let dict order pick.
                # Analyze the first alphabetically so the result is reproducible,
                # but mark it low-confidence: the caller forces REVIEW_REQUIRED.
                return (sorted(tied)[0], f"bridge_classify_files_TIE:{'/'.join(sorted(tied))}",
                        "low", tally)
        except Exception:
            pass  # bridge unavailable in this environment; fall through honestly

    # 3. LAST RESORT: domain guess. Honest low-confidence; caller should flag it.
    guessed = DOMAIN_TO_LANGUAGE.get(getattr(m1_core, "application_type", ""), "python")
    return (guessed, "domain_fallback_low_confidence", "low", {})


def get_adapter(language):
    """Return the adapter for `language`. Every language that detect_language can
    select MUST be represented here — otherwise a non-Python repo silently gets
    the PythonAdapter and parses nothing (the spring-boot / nginx / react bug:
    routed to java/c_cpp/javascript, handed PythonAdapter, 0 functions)."""
    _MAP = {
        "python":     ("python_adapter", "PythonAdapter"),
        "java":       ("java_adapter", "JavaAdapter"),
        "javascript": ("javascript_adapter", "JavaScriptAdapter"),
        "c_cpp":      ("c_cpp_adapter", "CCppAdapter"),
        "csharp":     ("csharp_adapter", "CSharpAdapter"),
        "go":         ("go_adapter", "GoAdapter"),
        "sql":        ("sql_adapter", "SQLAdapter"),
        "rust":       ("rust_adapter", "RustAdapter"),   # declared stub; honest empty report
    }
    if language not in _MAP:
        raise ValueError(
            f"no adapter registered for language '{language}'. "
            f"known: {sorted(_MAP)}. Refusing to substitute a different "
            f"language's adapter (that would analyze the wrong files).")
    modname, clsname = _MAP[language]
    mod = __import__(f"v3.repository_graph.languages.{modname}", fromlist=[clsname])
    return getattr(mod, clsname)()


def _m1(repo_root):
    """Module 1 — cognition + gate. Returns (m1_summary_dict, m1_core, gate)."""
    from v3.repository_cognition import RepositoryCognitionEngine
    from v3.repository_cognition.module1_extensions import EnhancedReportBuilder
    m1_core = RepositoryCognitionEngine(repo_root).scan()
    m1_enh = EnhancedReportBuilder().build(m1_core, repo_root)
    gate = m1_enh.gate.gate_decision
    app_type = getattr(getattr(m1_enh, "identity", None), "application_type",
                       getattr(m1_core, "application_type", "UNKNOWN"))
    try:
        from v3.repository_cognition.module1_extensions.domain_signatures import (
            get_enhanced_application_type)
        app_type = get_enhanced_application_type(app_type, repo_root)
    except Exception:
        pass
    fw = getattr(getattr(m1_enh, "identity", None), "primary_framework", None) \
        or getattr(m1_core, "primary_framework", "unknown")
    summary = {
        "application_type": app_type,
        "framework": fw,
        "gate": gate,
        "architecture": getattr(getattr(m1_enh, "architecture", None), "pattern", "UNKNOWN"),
        "confidence": getattr(m1_core, "confidence_score", 0.0),
    }
    return summary, m1_core, gate


def _m2_summary(m2_scan, language, files_routed=None):
    """Compact Module 2 summary for the report (NOT the full graph).

    Adapter output shapes differ: the Python adapter emits a `files_scanned`
    count; java/c_cpp/javascript emit only graphs.

    `files_routed` is what classify_files() sent to the adapter. It is NOT what
    the adapter parsed. Adapters declare `file_extensions` broadly enough to
    reach the metadata they need — GoAdapter claims `.mod` so it can read
    go.mod — then filter it out of their source list. On the Go compiler:
    11,294 routed, 23 of them `go.mod`, 11,271 parsed.

    So when an adapter emits no `files_scanned`, we report it as UNKNOWN rather
    than substituting the routed count. A routed file is not a scanned file, and
    a missing measurement is not a measurement of something else.
    """
    def _cg(g):
        return (sum(len(v) if isinstance(v, list) else 1 for v in g.values())
                if isinstance(g, dict) else 0)
    edges = 0
    cg = m2_scan.get("call_graph", {})
    if isinstance(cg, dict):
        edges = sum(len(v) for v in cg.values() if isinstance(v, list))
    unresolved = m2_scan.get("unresolved", [])
    out = {
        "language": language,
        "functions": _cg(m2_scan.get("function_graph", {})),
        "classes": _cg(m2_scan.get("class_graph", {})),
        "call_graph_edges": edges,
        "unresolved_calls": len(unresolved) if isinstance(unresolved, list) else 0,
        "gate": m2_scan.get("governance_gate", "UNKNOWN"),
    }
    scanned = m2_scan.get("files_scanned")
    if scanned is not None:
        out["files_scanned"] = scanned
    else:
        out["files_scanned"] = None
        out["files_scanned_note"] = (
            f"the '{language}' adapter does not emit a scanned-file count; "
            f"{files_routed} files were routed to it, which is not the same "
            f"measurement")
    if files_routed is not None:
        out["files_routed"] = files_routed
    # some adapters (go) report their own parse failures — surface them
    if "parse_errors" in m2_scan:
        out["parse_errors"] = m2_scan["parse_errors"]
    return out


# ---------------------------------------------------------------------------
# Pre-flight venv guard (Module 2 is FROZEN; this lives above it).
# Module 2's file walker skips these directory NAMES. We mirror that exact set
# here — we do NOT modify M2. A virtual environment whose folder name is NOT in
# this set would be walked by M2 (its deep site-packages tree can blow the
# recursion limit), so we detect that specific case up front, by the definitive
# venv marker (pyvenv.cfg), and stop with an honest, actionable message instead
# of a cryptic RecursionError. Standard '.venv'/'venv' are skipped by M2 and
# pass straight through — this guard never fires for them.
_M2_FROZEN_SKIP = {".git", "__pycache__", "node_modules", ".venv", "venv"}
# The guard's OWN walk prunes only these (NOT venv names) — it must be able to
# step one level into a venv folder to see its pyvenv.cfg marker and flag it.
_GUARD_PRUNE = {".git", "__pycache__", "node_modules"}


def _unskippable_venvs(repo_root):
    """Directories that ARE virtual environments (have a pyvenv.cfg marker),
    which Module 2 walks as if they were source — its deep site-packages tree can
    exhaust the recursion limit. We flag EVERY venv (regardless of name), because
    the live M2 build does not reliably skip even '.venv'. Fast: steps one level
    into a venv to detect the marker, then never descends further. Returns paths."""
    found = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in _GUARD_PRUNE]
        if "pyvenv.cfg" in filenames:
            found.append(dirpath)
            dirnames[:] = []  # a venv — never walk into its deep tree
    return found


def run_platform(repo_root, force=False):
    """Full M1 -> gate -> M2 -> M3 pipeline. One scan, one integrated report."""
    result = {
        "repo": repo_root,
        "run_time": dt.now(UTC).isoformat(),
        "status": "",
        "gate": "",
        "module1": {},
        "module2": {},
        "module3": {},
    }
    if not Path(repo_root).exists():
        result["status"] = "ERROR"; result["reason"] = "path not found"
        return result

    # ---- Module 1 ----
    try:
        m1_summary, m1_core, gate = _m1(repo_root)
    except Exception as e:
        result["status"] = "M1_ERROR"; result["reason"] = f"{type(e).__name__}: {e}"
        return result
    result["module1"] = m1_summary
    result["gate"] = gate

    # ---- gate enforcement ----
    if gate == "BLOCKED":
        result["status"] = "BLOCKED"
        return result
    if gate == "REVIEW_REQUIRED" and not force:
        result["status"] = "REVIEW_REQUIRED"
        return result

    # ---- pre-flight: guard against venvs M2's frozen walker will NOT skip ----
    # (Standard '.venv'/'venv' are skipped by M2 and never reach here.)
    try:
        bad_venvs = _unskippable_venvs(repo_root)
    except Exception:
        bad_venvs = []
    if bad_venvs:
        names = ", ".join(sorted(os.path.basename(v) for v in bad_venvs))
        result["status"] = "M2_PREFLIGHT_VENV"
        result["reason"] = (
            f"Repository contains a virtual environment ({names}) that Module 2 "
            f"would walk as source — its deep dependency tree can exhaust the "
            f"recursion limit. Fix: move the environment OUTSIDE the repository "
            f"folder (or point CodeTruth at a copy without it), then re-run. "
            f"CodeTruth analyzes your source, not installed dependencies.")
        result["preflight"] = {"venvs_detected": bad_venvs}
        return result

    # ---- Module 2 (scanned ONCE) ----
    try:
        language, lang_source, lang_conf, lang_tally = detect_language_meta(
            m1_core, repo_root)
        adapter = get_adapter(language)
        result["language_selection"] = {
            "language": language, "source": lang_source, "confidence": lang_conf,
        }
        if lang_tally:
            # The vote, so the routing decision can be audited rather than trusted.
            result["language_selection"]["dominance_vote"] = {
                lang: {"votes": v, "translation_units": u, "declarations": d}
                for lang, (v, u, d) in sorted(
                    lang_tally.items(), key=lambda kv: -kv[1][0])}
            result["language_selection"]["vote_rule"] = (
                "translation units decide; declarations (.h/.hpp/.cuh/.pyi/.d.ts) "
                "are #included into units and do not vote. A language with zero "
                "translation units votes with its declarations (header-only "
                "libraries are real).")
        # Build the REAL file list for the selected language before scanning.
        # Passing file_paths=[] left non-Python adapters (java, c_cpp, ...) with no
        # input: they scanned 0 files and their gate BLOCKed, which the completeness
        # guard then surfaced. The language bridge already computes this list
        # correctly (classify_files -> per-language file lists), and the same
        # adapters produce real call graphs when fed it. Python's adapter
        # self-discovers, so it is unaffected by this change.
        file_paths = _files_for_language(repo_root, language)
        # Deep-recursion guard: parsers like javalang recurse per AST node and hit
        # Python's default 1000-frame cap on very large sources (elasticsearch:
        # 22,101 Java files -> RecursionError aborted the entire scan). The limit
        # is raised only for the duration of the scan and always restored.
        with _deep_recursion(20000):
            m2_scan = adapter.scan(repo_root=repo_root, file_paths=file_paths)
        result["language_selection"]["files_routed"] = len(file_paths)
    except Exception as e:
        result["status"] = "M2_ERROR"; result["reason"] = f"{type(e).__name__}: {e}"
        return result
    result["module2"] = _m2_summary(m2_scan, language, files_routed=len(file_paths))

    # ---- Module 3 (reasoning) — reuse the M2 scan, pass m1 for future use ----
    # ---- Module 3: per-language reasoning dispatch (ADDITIVE) ----
    # Python keeps the frozen M3 pipeline unchanged. Non-Python languages are
    # routed to the validated language-bridge paths. Each language emits a COMMON
    # ENVELOPE declaring what it actually computed — no language is forced into
    # Python-M3's vocabulary (e.g. `guesses` is a Python-3A/3B concept; claiming
    # it for Java would assert a guarantee that path never measured).
    if language == "python":
        try:
            from v3.repository_reasoning.module3_pipeline import run_module3
            m3 = run_module3(repo_root, m2_scan=m2_scan, m1_result=m1_summary)
            m3.pop("call_index", None)  # large; internal artifact
            result["module3"] = m3
        except Exception as e:
            result["status"] = "M3_ERROR"; result["reason"] = f"{type(e).__name__}: {e}"
            result["module3"] = {}
            return result
    else:
        result["module3"] = _module3_for_language(repo_root, language)

    # ---- Phase 1: completeness guard (pipeline-level; frozen adapters untouched) ----
    # The pipeline may report COMPLETE only if MEANINGFUL PRIMARY ARTIFACTS exist.
    # For non-Python languages the Module 3 bridge engine may build a real call
    # graph even when the Module 2 adapter's own counts are sparse (Go: the frozen
    # adapter records callees without callers, so M2 shows 0 functions while the
    # caller-aware re-parse yields a full graph). Accept either source of evidence.
    m3_block = result.get("module3", {}) or {}
    m3_has_artifacts = _has_reasoning_artifacts(m3_block)
    if not (_has_primary_artifacts(language, result.get("module2", {}), m2_scan)
            or m3_has_artifacts):
        result["status"] = "REVIEW_REQUIRED"
        result["gate"] = "REVIEW_REQUIRED"
        sel = result.get("language_selection", {})
        n_files = sel.get("files_routed")
        m3_status = m3_block.get("status")
        if m3_status == "NOT_IMPLEMENTED":
            # A DECLARED stub, not a mysterious empty result. Name it plainly:
            # the language was identified correctly and analysis is not supported.
            result["reason"] = (
                f"This repository is predominantly {language}"
                + (f" ({n_files} {language} files)" if n_files else "")
                + f", identified from actual file composition. CodeTruth does not "
                f"implement {language} analysis: its adapter is a declared stub. "
                f"No analysis was performed and no findings are claimed. This is a "
                f"known capability boundary, not a failure to parse.")
        elif sel.get("confidence") == "high":
            # Routing was evidence-based and correct; the adapter itself produced
            # nothing. Say that honestly rather than blaming language selection.
            result["reason"] = (
                f"Language '{language}' was identified from actual file composition "
                f"(evidence-based, high confidence"
                + (f"; {n_files} files provided" if n_files is not None else "")
                + f"), but the '{language}' adapter produced no primary analysis "
                f"artifacts (0 functions / 0 call-graph edges / 0 SQL objects). "
                f"This is an honest capability boundary of the current pipeline for "
                f"this language — not a language-selection error. Analysis is not "
                f"COMPLETE and no findings are claimed.")
        else:
            result["reason"] = (
                f"No primary analysis artifacts were produced by the '{language}' "
                f"adapter, and the language was selected by a low-confidence "
                f"fallback. The repository may have been routed to a language that "
                f"does not match its contents. Analysis is not COMPLETE; review the "
                f"language selection for this repository.")
        return result

    # ---- Phase 3: honest handling of low-confidence (fallback) language choice ----
    # If the language was picked by the domain fallback (neither Module 1 composition
    # nor on-disk file counting could determine it), do not silently APPROVE. The
    # analysis may be on the wrong language; say so.
    sel = result.get("language_selection", {})
    if sel.get("confidence") == "low" and _has_primary_artifacts(language, result.get("module2", {}), m2_scan):
        result["status"] = "REVIEW_REQUIRED"
        result["gate"] = "REVIEW_REQUIRED"
        result["reason"] = (
            f"Language '{language}' was selected by a low-confidence domain "
            f"fallback (file composition could not be determined). Analysis "
            f"produced artifacts but may target the wrong language — review the "
            f"language selection before relying on these results.")
        return result

    result["status"] = "COMPLETE"
    return result


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if not args:
        print("usage: python run_codetruth.py <repo_root> [--json] [--save] [--force]")
        return 2
    repo = args[0]
    rep = run_platform(repo, force=("--force" in flags))

    if "--json" in flags:
        text = json.dumps(rep, indent=2, default=str)
        print(text)
        if "--save" in flags:
            out = "codetruth_report.json"
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"\nsaved -> {out}")
    else:
        g = rep.get("gate", "?")
        print("=" * 68)
        print("CodeTruth Platform — full pipeline")
        print("=" * 68)
        print(f"repo    : {repo}")
        print(f"status  : {rep['status']}")
        if rep.get("reason"):
            print(f"reason  : {rep['reason']}")
        print(f"M1 gate : [{GATE_EMOJI.get(g,'?')}] {g}")
        m1 = rep.get("module1", {})
        if m1:
            print(f"M1      : {m1.get('application_type')} / {m1.get('framework')} / {m1.get('architecture')}")
        m2 = rep.get("module2", {})
        if m2:
            print(f"M2      : {m2.get('language')}  files={m2.get('files_scanned')}  "
                  f"edges={m2.get('call_graph_edges')}  unresolved={m2.get('unresolved_calls')}")
        m3 = rep.get("module3", {})
        if m3 and "phase_3a" in m3:
            a = m3["phase_3a"]; ep = m3.get("edge_provenance", {})
            print(f"M3      : 3A resolved {a.get('attr_calls_total')}/{a.get('baseline_attr_calls')}  "
                  f"edges {ep.get('total_edges')} (+{ep.get('local_receiver_added')} reasoning)")
        elif m3.get("note"):
            print(f"M3      : {m3['note']}")
    return 0 if rep.get("status") == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))