"""
service.py — CodeTruth Live service layer (Layer 2, deployment-agnostic).

Wraps the real CodeTruth pipeline (run_codetruth.py, change_impact.py,
codetruth_report.py) into clean functions the web layer calls. This layer has NO
web or infra dependencies, so the same code works locally and (later) deployed.

Functions:
  analyze_repository(repo_path)      -> repository assessment (11-section)
  analyze_method(repo_path, target)  -> method change-impact
  analyze_class(repo_path, class_id) -> class change-impact (aggregate of methods)
  clone_repo(url, dest, max_files)   -> clone a GitHub URL (with a size cap)
  list_curated()                     -> pre-configured instant-demo repos

All heavy lifting delegates to the EXISTING validated modules. Nothing is
re-implemented here.
"""
import os, sys, subprocess, tempfile, shutil, re

# project root is injected by the caller (web app) via CODETRUTH_ROOT env or arg
def _ensure_paths(project_root):
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    v3 = os.path.join(project_root, "v3")
    if v3 not in sys.path:
        sys.path.insert(0, v3)
    _install_resolve_cache()   # transparent graph cache (once per process)


# ---------------------------------------------------------------------------
# Resolve cache: building the M2+M3 call graph via ReasoningEngine(...).resolve()
# is the expensive step, and EVERY feature (Browse, Assessment, Change Impact,
# Dead Code, Demo) triggered it independently — re-building the whole graph each
# time. We wrap resolve() to memoize per repo, keyed on a cheap file-change
# SIGNATURE (#.py files + latest mtime), so:
#   * the first action on a repo pays the cost; the rest reuse the graph,
#   * editing any .py file busts the cache and forces a fresh resolve
#     (never serves stale results — required for a determinism tool),
#   * different repos stay isolated, and a server restart clears everything.
# ---------------------------------------------------------------------------
_RESOLVE_CACHE = {}
_RESOLVE_CACHE_MAX = 8   # keep memory bounded


def _repo_signature(repo_path):
    latest = 0.0
    n = 0
    for root, _d, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                n += 1
                try:
                    latest = max(latest, os.path.getmtime(os.path.join(root, f)))
                except OSError:
                    pass
    return (os.path.abspath(repo_path), n, round(latest, 3))


def _install_resolve_cache():
    try:
        from v3.repository_reasoning import reasoning_engine as RE
    except Exception:
        return
    if getattr(RE.ReasoningEngine, "_ct_cached", False):
        return
    orig_init = RE.ReasoningEngine.__init__
    orig_resolve = RE.ReasoningEngine.resolve

    def init(self, repo_path, *a, **k):
        self._ct_repo = str(repo_path)
        orig_init(self, repo_path, *a, **k)

    def resolve(self, *a, **k):
        repo = getattr(self, "_ct_repo", None)
        if repo is None:
            return orig_resolve(self, *a, **k)
        try:
            sig = _repo_signature(repo)
        except Exception:
            return orig_resolve(self, *a, **k)
        if sig in _RESOLVE_CACHE:
            # Return a SHALLOW COPY: some callers pop top-level keys (e.g.
            # 'call_index' is removed downstream as an internal artifact). Handing
            # out the cached dict directly let that pop corrupt the cache, so the
            # NEXT caller hit KeyError: 'call_index'. A shallow copy gives each
            # caller its own top-level dict while sharing the (read-only) values.
            return dict(_RESOLVE_CACHE[sig])
        result = orig_resolve(self, *a, **k)
        if len(_RESOLVE_CACHE) >= _RESOLVE_CACHE_MAX:
            _RESOLVE_CACHE.pop(next(iter(_RESOLVE_CACHE)))  # evict oldest
        _RESOLVE_CACHE[sig] = result
        return dict(result)  # keep the cached original intact for later callers

    RE.ReasoningEngine.__init__ = init
    RE.ReasoningEngine.resolve = resolve
    RE.ReasoningEngine._ct_cached = True


# ----- curated repos (instant demo path) -----
CURATED = {
    # Python — full Phase 3A/3B reasoning (health rating applies)
    "flask":       {"label": "Flask (Python · web framework)", "sample_method": "Flask.dispatch_request"},
    "django":      {"label": "Django (Python · web framework)", "sample_method": "BaseHandler.get_response"},
    "requests":    {"label": "Requests (Python · HTTP library)", "sample_method": "Session.request"},
    # Bridge languages — call graph + queries; health rating is NOT_RATED by design
    "go":          {"label": "Go compiler (Go · bridge engine)"},
    "spring-boot": {"label": "Spring Boot (Java · bridge engine)"},
    "ccxt":        {"label": "ccxt (JavaScript/C# · bridge engine)"},
    "nginx":       {"label": "nginx (C/C++ · bridge engine)"},
    "rust":        {"label": "Rust compiler (Rust · declared stub — honest refusal)"},
}

def list_curated(corpus_dir):
    out = []
    for name, meta in CURATED.items():
        path = os.path.join(corpus_dir, name)
        if os.path.isdir(path):
            out.append({"name": name, "path": path, **meta})
    return out


# ----- clone (bring-your-own-URL path, size-capped) -----
_GH_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+/?$")

def clone_repo(url, dest_base, max_files=6000):
    """Clone a GitHub URL to a temp dir. Returns (path, error). Size-capped:
    after clone, if the repo exceeds max_files .py files, refuse (honest bound:
    huge repos take too long for a live demo)."""
    if not _GH_RE.match(url.strip().rstrip("/") + ""):
        # allow with/without trailing slash and .git
        u = url.strip()
        if not (u.startswith("https://github.com/")):
            return None, "Only https://github.com/<owner>/<repo> URLs are supported."
    dest = tempfile.mkdtemp(prefix="ctlive_", dir=dest_base)
    try:
        # shallow clone for speed
        r = subprocess.run(["git", "clone", "--depth", "1", url, dest],
                           capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            shutil.rmtree(dest, ignore_errors=True)
            return None, f"git clone failed: {r.stderr[:200]}"
    except subprocess.TimeoutExpired:
        shutil.rmtree(dest, ignore_errors=True)
        return None, "Clone timed out (repo too large for the live demo)."
    # size cap
    py_files = sum(1 for _root, _d, files in os.walk(dest)
                   for f in files if f.endswith(".py"))
    if py_files == 0:
        shutil.rmtree(dest, ignore_errors=True)
        return None, "No Python files found (CodeTruth's live demo is Python-only)."
    if py_files > max_files:
        shutil.rmtree(dest, ignore_errors=True)
        return None, (f"Repository has {py_files} Python files (cap {max_files} for "
                      f"the live demo). Large repos take minutes — run the CLI "
                      f"locally for those.")
    return dest, None


# ----- analysis modes (delegate to existing tools) -----
def analyze_repository(project_root, repo_path, force=False, display_name=None):
    """Mode 1: full repository assessment. Returns (markdown, meta) with the REAL
    pipeline status/gate. `force=True` proceeds past a REVIEW_REQUIRED governance
    gate (human-approved override). `display_name` (e.g. the GitHub URL) is shown
    as the repository instead of the temp clone path."""
    _ensure_paths(project_root)
    import importlib
    from v3.run_codetruth import run_platform
    rep = run_platform(repo_path, force=force)         # run once (force-aware)
    rpt = importlib.import_module("codetruth_report")
    md = rpt.generate(repo_path, rep=rep, display_name=display_name)
    # A run that COMPLETED but whose gate was REVIEW_REQUIRED means a human forced
    # past governance review — say so, plainly, at the top of the report.
    if rep.get("status") == "COMPLETE" and rep.get("gate") == "REVIEW_REQUIRED":
        m1 = rep.get("module1", {})
        banner = (
            "> **Analyzed under manual override.** Module 1's governance gate "
            "returned REVIEW_REQUIRED (uncertain classification: "
            f"{m1.get('application_type','UNKNOWN')}, confidence "
            f"{m1.get('confidence','n/a')}). A human chose to proceed. Findings "
            "below are computed normally and remain zero-guess; the gate's caution "
            "about the repository's *classification* still applies.\n\n---\n\n")
        md = md.split("\n", 1)
        md = md[0] + "\n\n" + banner + (md[1] if len(md) > 1 else "")
    meta = {
        "status": rep.get("status"),
        "gate": rep.get("gate"),
        "module3_ran": rep.get("status") == "COMPLETE" and bool(rep.get("module3")),
    }
    return md, meta

def analyze_method(project_root, repo_path, target, display_name=None):
    """Mode 2: method change impact. Returns (markdown, analysis)."""
    _ensure_paths(project_root)
    import importlib
    ci = importlib.import_module("v3.repository_reasoning.change_impact")
    a = ci.analyze(repo_path, target)
    return ci.render(repo_path, a, display_name=display_name), a

def analyze_class(project_root, repo_path, class_id):
    """Mode 3: class change impact = aggregate of the class's methods.
    Finds all methods of the class in the call index, runs impact on each,
    unions the affected sets. Returns markdown + aggregate."""
    _ensure_paths(project_root)
    import importlib
    ci = importlib.import_module("v3.repository_reasoning.change_impact")
    from v3.repository_reasoning.reasoning_engine import ReasoningEngine
    from v3.repository_reasoning import reasoning_queries as RQ

    report = ReasoningEngine(repo_path).resolve()
    fwd = report["call_index"]
    # methods of the class = index keys containing ".<ClassName>."
    short = class_id.split(".")[-1]
    methods = [k for k in fwd if f".{short}." in k]
    if not methods:
        return f"# Class Change Impact\n\n**Class `{class_id}` not found** in the verified call index.\n", None

    rev = RQ.build_reverse_index(fwd)
    all_affected = set()
    per_method = []
    for m in methods:
        imp = RQ.impact_of(m, rev)
        aff = imp.get("affected_callers", [])
        all_affected.update(aff)
        per_method.append((m, len(aff)))

    # render an aggregate report
    L = [f"# CodeTruth — Class Change Impact: `{class_id}`", "",
         f"**Repository:** `{repo_path}`", "",
         f"Aggregate impact of changing **any part of class `{short}`** "
         f"({len(methods)} methods in the verified call index).", "",
         "---", "",
         "## Verified aggregate impact", "",
         f"- **Methods analyzed:** {len(methods)}",
         f"- **Total verified affected callers (union):** {len(all_affected)}", ""]
    L.append("## Per-method impact")
    L.append("")
    L.append("| Method | Verified affected callers |")
    L.append("|---|---|")
    for m, n in sorted(per_method, key=lambda x: -x[1])[:30]:
        L.append(f"| `{m}` | {n} |")
    L.append("")
    L.append("## Truth Boundary")
    L.append("")
    L.append("> Aggregate impact is the union over the VERIFIED call graph for all "
             "methods of this class. External/dynamic callers are not included and "
             "are treated as unknown, not guessed. **No guesses made.**")
    L.append("")
    agg = {"methods": len(methods), "affected_union": len(all_affected)}
    return "\n".join(L), agg


# ----- repository structure for browsing (Phase 1 tree-browse feature) -----
def repo_structure(project_root, repo_path):
    """Return a browsable tree of modules -> classes -> methods, derived from the
    verified call index. Lets the UI let users CLICK a method instead of typing
    its fully-qualified name. Pure exposure of what M3 already computed."""
    _ensure_paths(project_root)
    from v3.repository_reasoning.reasoning_engine import ReasoningEngine
    report = ReasoningEngine(repo_path).resolve()
    fwd = report["call_index"]

    # group node ids: module -> class -> [methods]  and module -> [functions]
    tree = {}
    for node in fwd:
        parts = node.split(".")
        # find class (first Capitalized segment)
        cls_idx = next((i for i, p in enumerate(parts) if p[:1].isupper()), None)
        if cls_idx is not None:
            module = ".".join(parts[:cls_idx]) or "(root)"
            cls = parts[cls_idx]
            method = ".".join(parts[cls_idx + 1:])
            tree.setdefault(module, {"classes": {}, "functions": []})
            tree[module]["classes"].setdefault(cls, [])
            if method:
                tree[module]["classes"][cls].append({"id": node, "name": method})
        else:
            module = ".".join(parts[:-1]) or "(root)"
            fn = parts[-1]
            tree.setdefault(module, {"classes": {}, "functions": []})
            tree[module]["functions"].append({"id": node, "name": fn})

    # to a sorted, serializable list
    out = []
    for module in sorted(tree):
        node = tree[module]
        classes = []
        for cls in sorted(node["classes"]):
            methods = sorted(node["classes"][cls], key=lambda m: m["name"])
            classes.append({"class": cls, "class_id": f"{module}.{cls}",
                            "methods": methods})
        funcs = sorted(node["functions"], key=lambda f: f["name"])
        if classes or funcs:
            out.append({"module": module, "classes": classes, "functions": funcs})
    return {"modules": out,
            "counts": {"modules": len(out),
                       "classes": sum(len(m["classes"]) for m in out),
                       "callable_nodes": len(fwd)}}


# ----- lightweight metadata preview (Module 1 ONLY, for the UI preview) -----
def repo_meta(project_root, repo_path):
    """Fast metadata preview. Runs ONLY Module 1 cognition (language/framework/
    architecture/gate) via run_codetruth._m1 — it does NOT run Module 2's full
    call-graph scan or Module 3 reasoning, which is what made this slow on large
    repos (Django was paying for a 67k-edge scan just to show four fields).
    Falls back to the full platform only if the M1-only path is unavailable."""
    _ensure_paths(project_root)
    try:
        from v3.run_codetruth import _m1
        summary, _core, gate = _m1(repo_path)
        # M1 doesn't emit language directly; derive it the same way the pipeline
        # does, cheaply, without scanning the graph. Use the CANONICAL router
        # (detect_language_meta) — never a hardcoded default. Take [0] so a change
        # in the tuple's arity can't silently break this. If it cannot decide,
        # report "unknown", not "python".
        try:
            from v3.run_codetruth import detect_language_meta
            language = detect_language_meta(_core, repo_path)[0]
        except Exception:
            language = "unknown"
        return {"language": language,
                "framework": summary.get("framework", "?"),
                "architecture": summary.get("architecture", "?"),
                "gate": summary.get("gate", gate or "?")}
    except Exception:
        # fallback: full platform (slower, but keeps the preview working if the
        # M1-only entry point ever changes)
        from v3.run_codetruth import run_platform
        rep = run_platform(repo_path)
        m1 = rep.get("module1", {})
        m2 = rep.get("module2", {})
        return {"language": m2.get("language", "python"),
                "framework": m1.get("framework", "?"),
                "architecture": m1.get("architecture", "?"),
                "gate": rep.get("gate", m1.get("gate", "?"))}


# ----- Truth Boundary demo (front-door differentiator) -----
# Validated target pairs for curated repos: (has-callers, no-callers).
DEMO_TARGETS = {
    "flask":  ("flask.app.Flask.dispatch_request",
               "flask.app.Flask.send_static_file"),
    "django": ("django.db.models.query.QuerySet.filter",
               "django.db.models.functions.comparison.Least.__init__"),
}


def demo_targets_for(curated_name):
    return DEMO_TARGETS.get(curated_name, (None, None))


def truth_boundary_demo(project_root, repo_path, populated=None, empty=None):
    """Route-aware Truth Boundary demo. Shows CodeTruth's honest boundary for
    WHATEVER language the pipeline actually routes this repository to — never a
    fabricated analysis of some other language's files.

    - python  -> caller contrast: one method WITH a verified caller vs one with
                 NONE (reported as known-unknown, never 'safe to delete').
    - bridge  -> the verified call-graph result PLUS the engine's declared
                 limitations (what it structurally cannot see).
    - stub    -> the refusal itself (rust: identified, NOT_IMPLEMENTED, nothing
                 claimed) — the purest form of the truth boundary.
    Returns (markdown, data).
    """
    _ensure_paths(project_root)
    import importlib

    # Route FIRST — the same decision the pipeline makes. Never analyze a
    # language the router did not select. (This is exactly what the old demo
    # skipped: it ran ReasoningEngine directly and, on a Rust repo, analyzed the
    # ~190 stray Python files and reported success on a declared-stub language.)
    from v3.run_codetruth import _m1, detect_language_meta
    _s, _core, _gate = _m1(repo_path)
    language = detect_language_meta(_core, repo_path)[0]

    # --- stub / non-Python: show the pipeline's real verdict, do not fabricate ---
    if language != "python":
        from v3.run_codetruth import run_platform
        rep = run_platform(repo_path)
        m3 = rep.get("module3", {}) or {}
        status = rep.get("status", "?")
        tb = m3.get("truth_boundary", {}) or {}
        engine = m3.get("engine") or "—"
        caps = m3.get("capabilities", []) or []
        md = ["# Truth Boundary Demo",
              "",
              f"**Repository:** `{repo_path}`  ",
              f"**Routed language:** `{language}` (by verified file count)  ",
              f"**Pipeline status:** {status}",
              ""]
        if m3.get("status") == "NOT_IMPLEMENTED" or status == "REVIEW_REQUIRED":
            # the refusal IS the demo
            md += [
                "### The point",
                "",
                f"CodeTruth identified this repository as **{language}**, then "
                f"**refused to analyze it** — no engine is implemented for this "
                f"language, so nothing is claimed.",
                "",
                "| | |", "|---|---|",
                f"| Language identified | {language} (from actual file composition) |",
                f"| Engine | {engine or 'none'} |",
                f"| Capabilities claimed | {caps if caps else '**none**'} |",
                f"| Findings | **none** — no analysis was performed |",
                f"| Guesses | not applicable — nothing was analyzed |",
                "",
                f"> {rep.get('reason', 'This is a known capability boundary, not a failure to parse.')}",
                "",
                "**This is the truth boundary at its purest:** the tool knows what "
                "it cannot do and says so, instead of analyzing whatever files it "
                "*can* parse and calling that a result.",
            ]
        else:
            # bridge language: real call graph + declared limitations
            scope = tb.get("scope", "")
            lims = tb.get("limitations", []) or []
            graph = m3.get("graph", {}) or {}
            md += [
                "### The point",
                "",
                f"CodeTruth built a **verified call graph** for this `{language}` "
                f"repository, and **declares exactly what it cannot see** — it does "
                f"not guess past its own boundary.",
                "",
                "| | |", "|---|---|",
                f"| Functions in index | {graph.get('functions_in_index', '—')} |",
                f"| Engine | {engine} |",
                f"| Capabilities | {', '.join(caps) if caps else '—'} |",
                "",
                f"**Declared truth boundary:** {scope}",
                "",
                "**Cannot see (named, not guessed):**",
            ]
            md += [f"- {l}" for l in lims] or ["- (none declared)"]
            md += [
                "",
                "> Guess counting and edge-provenance are Python-engine "
                "measurements and are deliberately **not claimed** for this "
                "language. The boundary above is what this engine declares it "
                "cannot resolve — reflection, dynamic dispatch, and the like are "
                "flagged, never fabricated.",
            ]
        return "\n".join(md), {"language": language, "status": status,
                               "module3_ran": m3.get("status") not in (None, "NOT_IMPLEMENTED")}

    # --- python: the classic caller contrast (verified vs known-unknown) ---
    tbd = importlib.import_module("v3.repository_reasoning.truth_boundary_demo")

    if not populated or not empty:
        from v3.repository_reasoning.reasoning_engine import ReasoningEngine
        from v3.repository_reasoning import reasoning_queries as RQ
        report = ReasoningEngine(repo_path).resolve()
        fwd = report["call_index"]
        rev = RQ.build_reverse_index(fwd)
        dc = RQ.dead_code(fwd, rev)
        cands = dc.get("candidates", []) or []
        candset = set(cands)
        excluded = set(dc.get("entry_points_excluded", []) or [])
        if not empty and cands:
            empty = cands[0]
        if not populated:
            populated = next((n for n in fwd
                              if n not in candset and n not in excluded), None)

    if not populated or not empty:
        return ("# Truth Boundary Demo\n\nCould not auto-select demo targets for "
                "this repository (need one method with verified callers and one "
                "without). Try a curated repo.\n"), None

    return tbd.demo_pair(repo_path, populated, empty)


# ----- Project Intelligence Report (evidence JSON -> human/AI prose) -----
def project_report(project_root, repo_path, display_name=None, mode="engineer"):
    """Generate the Project Intelligence Report for a repository.

    Two-stage, one-way pipeline (architecture rule D-01):
        run_platform() -> project_report_generator (evidence JSON)
                       -> project_intelligence_report (prose projection)

    The renderer never invents a value absent from the JSON; UNKNOWN fields are
    rendered as UNKNOWN with their reason. Returns (markdown, meta) where meta
    carries the machine JSON so the dashboard can also offer Export JSON.
    """
    _ensure_paths(project_root)
    import project_report_generator as GEN
    import project_intelligence_report as REND

    # Pin the report to the real commit when the source is a git checkout — a
    # report that claims reproducibility must cite the actual commit, not a
    # placeholder. When the source is not a git checkout, say so honestly rather
    # than rendering a zero-hash that looks real.
    import subprocess
    try:
        pinned = subprocess.check_output(
            ["git", "-C", repo_path, "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL).strip()
        if not pinned:
            pinned = "UNPINNED — source is not a git checkout"
    except Exception:
        pinned = "UNPINNED — source is not a git checkout"

    # generator runs the pipeline once, through the canonical router
    doc = GEN.generate_for_repo(repo_path, pinned_commit=pinned)
    # validated render: raises if the prose states anything the JSON doesn't hold,
    # so a drifting report fails loudly rather than shipping fabricated text.
    if mode not in ("human", "engineer", "manager", "ai"):
        mode = "engineer"
    try:
        md = REND.render_validated(doc, mode)
    except Exception as e:
        # a projection violation is a bug in the renderer, not a repo problem —
        # surface it rather than shipping unvalidated prose.
        md = (f"# Report generation halted\n\nThe renderer produced a value the "
              f"evidence model does not contain, so the report was blocked to "
              f"avoid shipping an unverified statement.\n\n`{type(e).__name__}: {e}`")

    lang = (((doc.get("structure") or {}).get("dominant_language") or {}).get("value"))
    return md, {
        "status": "COMPLETE",
        "module3_ran": True,
        "language": lang,
        "mode": mode,
        "report_json": doc,   # the evidence model, for Export JSON
    }


# ----- Dead Code Candidates (Report 3: technical-debt reduction) -----
def dead_code(project_root, repo_path, sample_limit=60):
    """Dead-code CANDIDATES. Delegates to the validated RQ.dead_code and frames
    the result HONESTLY: candidates have no inbound internal call edge, but that
    is evidence of absence in static analysis - NOT proof of unused. The boundary
    (entry points, framework callbacks, dynamic dispatch, external callers) is
    kept front-and-center, and the count is interpreted rather than dumped.
    Returns (markdown, data)."""
    _ensure_paths(project_root)
    from v3.repository_reasoning.reasoning_engine import ReasoningEngine
    from v3.repository_reasoning import reasoning_queries as RQ
    from collections import Counter

    report = ReasoningEngine(repo_path).resolve()
    fwd = report["call_index"]
    rev = RQ.build_reverse_index(fwd)
    dc = RQ.dead_code(fwd, rev)

    candidates = dc.get("candidates", []) or []
    count = dc.get("count", len(candidates))
    label = dc.get("label", "CANDIDATES")
    boundary = dc.get("boundary", "")
    total_nodes = len(fwd)

    # honest distribution: cluster by top-level module so a big number is readable
    dist = Counter((c.split(".")[0] if "." in c else c) for c in candidates)
    top = dist.most_common(10)

    L = []
    L.append("# CodeTruth — Dead Code Candidates")
    L.append("")
    L.append(f"**Repository:** `{repo_path}`  ")
    L.append(f"**Label:** {label} — *not* a deletion verdict  ")
    L.append("**Guesses made:** 0 (Truth Boundary)")
    L.append("")
    L.append("*A candidate is a function with **no inbound internal call edge** in "
             "the verified call graph. That is evidence of absence in static "
             "analysis — it is **not** proof the function is unused.*")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append(f"- **Candidates found:** {count}")
    L.append(f"- **Callable nodes in verified call index:** {total_nodes}")
    L.append("")
    L.append("*The verified call index counts callable nodes that participate in "
             "the call graph. Module 2 may parse a higher function total for the "
             "same repository: module-level entries and nodes that don't participate "
             "as distinct call-graph functions are not counted here. The exact "
             "per-node breakdown is not currently emitted, so it is not asserted.*")
    L.append("")
    L.append("> **How to read this number.** In large repositories the count is "
             "usually dominated by **test methods and framework callbacks** invoked "
             "*dynamically* (by a test runner, router, signal, or plugin) — paths "
             "static analysis cannot see. Those are **known-unknowns**, not "
             "confirmed dead code. Read every candidate as \"investigate,\" never "
             "\"delete.\"")
    L.append("")
    if top:
        L.append("## Where the candidates cluster")
        L.append("")
        L.append("| Top-level module | Candidates |")
        L.append("|---|---|")
        for pkg, n in top:
            L.append(f"| `{pkg}` | {n} |")
        L.append("")
        L.append("*Heavy clustering under test or framework packages is expected — "
                 "those are dynamically invoked, not dead.*")
        L.append("")
    # ---- classification: ONLY evidence-backed categories ----
    # The one unambiguous signal in a candidate node string is the '.<module>'
    # suffix (a module-level execution entry). Everything else has no verified
    # inbound caller and no decorator metadata in the graph, so it is honestly
    # "investigate" - we do NOT infer "Flask route"/"@app.route" (that would be a
    # guess; the call graph carries no decorator information).
    module_scripts = [c for c in candidates if c.endswith(".<module>")]
    investigate = [c for c in candidates if not c.endswith(".<module>")]

    L.append("## Candidate classification")
    L.append("")
    L.append("| Category | Count | Basis (evidence) |")
    L.append("|---|---|---|")
    L.append(f"| Module entry script | {len(module_scripts)} | node is a "
             f"`.<module>` execution entry |")
    L.append(f"| Investigation candidate | {len(investigate)} | no verified "
             f"inbound internal caller |")
    L.append("")
    L.append("*Only evidence-backed categories are shown. Richer labels — "
             "**Framework entry point** (e.g. `@app.route` routes) and **CLI entry "
             "point** — are **not** inferred here: the verified call graph carries "
             "no decorator metadata, so labeling a route would be a guess. Such "
             "candidates remain \"investigate\" until decorator detection is added "
             "to Module 1/2. This is a deferred capability, not a classification.*")
    L.append("")
    if module_scripts:
        L.append(f"### Module entry scripts ({len(module_scripts)})")
        L.append("")
        for c in module_scripts[:sample_limit]:
            L.append(f"- `{c}` — module-level execution entry; no inbound internal caller")
        L.append("")
    if investigate:
        shown = min(sample_limit, len(investigate))
        L.append(f"### Investigation candidates ({len(investigate)}"
                 + (f", first {shown}" if len(investigate) > sample_limit else "") + ")")
        L.append("")
        for c in investigate[:sample_limit]:
            L.append(f"- `{c}` — no verified inbound internal caller")
        if len(investigate) > sample_limit:
            L.append("")
            L.append(f"*… and {len(investigate) - sample_limit} more. Export the "
                     f"full list (JSON) for systematic review.*")
        L.append("")
    L.append("## Truth Boundary")
    L.append("")
    L.append("> " + (boundary or
             "Candidates have no inbound internal call edge; entry points, "
             "framework callbacks, and dynamic dispatch may appear here falsely — "
             "CANDIDATES, not a verdict."))
    L.append("")
    L.append("## Engineering recommendation")
    L.append("")
    L.append("This report **narrows the search** for unused code; it does **not** "
             "authorize removal. For each candidate you intend to remove: confirm "
             "it is not an entry point, framework hook, test, or dynamically "
             "dispatched target — ideally with runtime coverage — then remove under "
             "normal review. CodeTruth proves what it can and flags what it cannot; "
             "the deletion decision stays a human, evidence-backed step.")
    L.append("")

    data = {"count": count, "label": label, "sample": candidates[:sample_limit],
            "clusters": top}
    return "\n".join(L), data


# ----- Local folder source (LOCAL USE ONLY) -----
def resolve_local(path):
    """Resolve a LOCAL folder path for in-place analysis. LOCAL USE ONLY: this
    lets the caller point the server at a directory on the host, which is fine on
    your own machine but must be DISABLED before any public/shared deployment.
    Validates existence / is-dir / has-.py, and enforces an optional root guard
    if CODETRUTH_LOCAL_ROOT is set (off by default). Returns (abspath, error)."""
    if not path or not path.strip():
        return None, "Enter a local folder path."
    p = os.path.abspath(os.path.expanduser(path.strip().strip('"').strip("'")))
    if not os.path.exists(p):
        return None, f"Path does not exist: {p}"
    if not os.path.isdir(p):
        return None, f"Not a folder (must be a directory): {p}"
    root = os.environ.get("CODETRUTH_LOCAL_ROOT")
    if root:
        root_abs = os.path.abspath(os.path.expanduser(root))
        try:
            inside = os.path.commonpath([root_abs, p]) == root_abs
        except ValueError:
            inside = False  # different drive on Windows
        if not inside:
            return None, (f"Local path must be within CODETRUTH_LOCAL_ROOT "
                          f"({root_abs}). Refused: {p}")
    has_py = any(f.endswith(".py") for _r, _d, fs in os.walk(p) for f in fs)
    if not has_py:
        return None, f"No Python files found under: {p} (CodeTruth is Python-only)."
    return p, None


# ----- venv guard (mirror of run_codetruth pre-flight; used by the web layer) -----
def find_venvs(repo_path):
    """Return virtual-environment directories (by pyvenv.cfg marker) inside
    repo_path. Module 2 walks these as source and can hang, so the web layer
    refuses a repo containing one. Fast: steps one level in to see the marker,
    never descends into the venv's deep tree."""
    _prune = {".git", "__pycache__", "node_modules"}
    found = []
    try:
        for dp, dn, fn in os.walk(repo_path):
            dn[:] = [d for d in dn if d not in _prune]
            if "pyvenv.cfg" in fn:
                found.append(dp)
                dn[:] = []
    except Exception:
        pass
    return found


# ----- local folder picker (LOCAL USE ONLY) -----
def list_dirs(path):
    """List immediate sub-directories of `path` for the local folder picker.
    Empty path -> drive letters (Windows) or '/'. Returns
    {path, parent, dirs:[full paths]}."""
    import string
    if not path:
        if os.name == "nt":
            drives = [f"{d}:\\" for d in string.ascii_uppercase
                      if os.path.exists(f"{d}:\\")]
            return {"path": "", "parent": None, "dirs": drives}
        path = os.sep
    path = os.path.abspath(os.path.expanduser(path.strip().strip('"').strip("'")))
    if not os.path.isdir(path):
        return {"path": path, "parent": os.path.dirname(path), "dirs": []}
    try:
        names = sorted(
            (d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))),
            key=lambda s: (s.startswith("."), s.lower()))
        dirs = [os.path.join(path, d) for d in names]
    except (PermissionError, OSError):
        dirs = []
    parent = os.path.dirname(path.rstrip("\\/"))
    if not parent or parent == path:
        parent = None if os.name != "nt" else ""   # "" -> drive list on Windows
    return {"path": path, "parent": parent, "dirs": dirs}


# ----- native OS folder dialog (LOCAL USE ONLY) -----
def pick_folder_native():
    """Open a NATIVE OS folder-selection dialog and return the chosen absolute
    path (or "" if cancelled/unavailable). LOCAL USE ONLY: the dialog appears on
    the machine running the server. Runs in a subprocess so it never blocks or
    conflicts with the web server's event loop, and never needs the main thread."""
    import subprocess, sys
    code = (
        "import tkinter as tk\n"
        "from tkinter import filedialog\n"
        "r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True)\n"
        "p = filedialog.askdirectory(title='Select a repository / project folder')\n"
        "print(p or '')\n"
    )
    try:
        out = subprocess.run([sys.executable, "-c", code],
                             capture_output=True, text=True, timeout=600)
        return (out.stdout or "").strip()
    except Exception:
        return ""
