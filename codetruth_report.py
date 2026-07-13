"""
codetruth_report.py — CodeTruth Engineering Assessment Report generator.

Runs the real M1->M2->M3 platform pipeline and emits an 11-section engineering
assessment report. Every section is either (a) directly computed from module
output, (b) a derived metric with its inputs SHOWN, or (c) explicitly marked
policy-dependent / not-computed. No value is asserted that the pipeline did not
produce. The report carries the same Truth Boundary discipline as the platform.

Usage (from project root):
    python codetruth_report.py "C:\\repos\\v3\\flask"
    python codetruth_report.py "C:\\repos\\v3\\flask" --out flask_assessment.md
    python codetruth_report.py "C:\\repos\\v3\\flask" --impact flask.app.Flask.dispatch_request
"""
import sys, os, warnings, json, argparse
warnings.filterwarnings("ignore", category=SyntaxWarning)

# ---------------------------------------------------------------------------
# Location-robust import bootstrap — finds the folder that CONTAINS the `v3`
# package by walking upward, so this runner works from ANY location (e.g. a
# main_pipeline_to_run/ subfolder or a future final-files layout) without the
# `from v3....` imports breaking. Honours a CODETRUTH_ROOT env override; falls
# back to the original assumption if no marker is found.
# ---------------------------------------------------------------------------
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


def _health(m2, m3):
    """Derive health/risk from EXPLICIT metrics. Returns (rating, risk, metrics)
    with the metrics dict shown in the report so the rating is reproducible."""
    ep = m3.get("edge_provenance", {})
    tb = m3.get("truth_boundary", {})
    p3a = m3.get("phase_3a", {})

    # SOUND/UNVERIFIED is a Phase 3A/3B judgement: it reads `guesses`,
    # `edge_provenance`, and attribute-call coverage — measurements ONLY the
    # frozen Python engine computes. Bridge languages (java/js/c_cpp/go/csharp/
    # sql) emit a common envelope with `truth_boundary.{scope,limitations}` and
    # NO `guesses` key by construction (MODULE3 D3-002). Reading those absent
    # fields as 0 would rate every non-Python repo SOUND on a guess count its
    # engine never took — a fabricated guarantee, in the deliverable, from a
    # tool built to refuse fabrication. A missing measurement is not a
    # measurement of 0. Refuse to rate instead.
    if "guesses" not in tb:
        language = m2.get("language", "?")
        return "NOT_RATED", "UNKNOWN", {
            "rating_basis": "Phase 3A/3B (Python) — not computed for this language",
            "language": language,
            "note": (f"Health rating requires Python Module 3 measurements "
                     f"(guesses, edge provenance, attribute-call coverage). The "
                     f"'{language}' engine produces a call graph and a declared "
                     f"truth boundary, but none of those metrics. The analysis "
                     f"is not unsound — it is simply not rated on this axis."),
        }
    # coverage = M3 attribute-call resolution rate over the M2 attribute-call
    # baseline (single consistent denominator, stated in the report).
    baseline = p3a.get("baseline_attr_calls", 0) or 1
    attr_resolved = p3a.get("attr_calls_total", 0)
    coverage = attr_resolved / baseline
    guesses = tb.get("guesses", 0)
    lrc = m3.get("local_receiver_counts", {})
    inrepo_miss = lrc.get("super_decline_inrepo_miss", 0)
    metrics = {
        "call_graph_edges_total": ep.get("total_edges", 0),
        "reasoning_edges_added": ep.get("local_receiver_added", 0),
        "attribute_calls_resolved": attr_resolved,
        "attribute_call_baseline": baseline,
        "attr_resolution_coverage_pct": round(100.0 * coverage, 1),
        "unresolved_calls": m2.get("unresolved_calls", 0),
        "guesses": guesses,
        "fixable_inrepo_miss": inrepo_miss,
    }
    # HEALTH = ANALYSIS INTEGRITY, not resolution coverage. CodeTruth's guarantee
    # is "no fabrications; every decline categorized" - NOT "resolves all dynamic
    # calls". A dynamic framework with low coverage but 0 guesses is HEALTHY (the
    # analysis is sound); it is not penalized for the code being dynamic.
    # Signals: guesses (must be 0), uncategorized declines (should be 0),
    # fixable in-repo gaps (informational).
    uncategorized = 0  # every decline is categorized by construction; check anyway
    lrc2 = m3.get("local_receiver_counts", {})
    su = lrc2.get("super_unresolved", 0)
    su_cats = (lrc2.get("super_decline_external", 0)
               + lrc2.get("super_decline_inrepo_miss", 0)
               + lrc2.get("super_decline_nested_fid", 0)
               + lrc2.get("super_decline_no_bases", 0)
               + lrc2.get("super_decline_cyclic", 0))
    uncategorized = max(0, su - su_cats)
    metrics["uncategorized_declines"] = uncategorized

    if guesses > 0 or uncategorized > 0:
        # analysis integrity compromised - the ONE thing that makes it unhealthy
        rating, risk = "UNVERIFIED", "HIGH"
    else:
        # sound analysis (0 guesses, all declines categorized). Risk reflects how
        # much is KNOWN vs flagged-unknown, but the analysis itself is trustworthy.
        rating = "SOUND"
        if inrepo_miss > 200:
            risk = "MEDIUM"   # notable fixable inheritance gaps to be aware of
        else:
            risk = "LOW"
    return rating, risk, metrics


def generate(repo, impact_target=None, policy=None, rep=None, display_name=None):
    if rep is None:
        from v3.run_codetruth import run_platform
        rep = run_platform(repo)
    if rep.get("status") != "COMPLETE":
        return _incomplete_report(rep, display_name=display_name)

    m1 = rep.get("module1", {})
    m2 = rep.get("module2", {})
    m3 = rep.get("module3", {})
    ep = m3.get("edge_provenance", {})
    tb = m3.get("truth_boundary", {})
    by_label = m3.get("by_label", {})
    lrc = m3.get("local_receiver_counts", {})
    p3a = m3.get("phase_3a", {})

    resolved_path = rep.get("repo", "")
    repo_dir = os.path.basename(str(resolved_path).rstrip("/\\"))
    shown_repo = display_name or resolved_path

    rating, risk, metrics = _health(m2, m3)
    # `guesses`/`edge_provenance`/phase_3a are Phase 3A/3B measurements the frozen
    # Python engine computes and no bridge engine does. Gate every line that would
    # print one, so a non-Python report never claims "0 guesses" it never measured.
    _py_m3 = "guesses" in tb
    L = []
    def w(s=""): L.append(s)

    # ---- header ----
    w(f"# CodeTruth Engineering Assessment Report")
    w()
    w(f"**Repository:** `{shown_repo}`  ")
    if display_name and str(display_name) != str(resolved_path):
        w(f"*Analyzed from local checkout: `{resolved_path}` (evidence/debug).*  ")
    w(f"**Generated:** {rep.get('run_time')}  ")
    w(f"**Pipeline:** Module 1 (cognition + gate) -> Module 2 (structure) -> Module 3 (reasoning)")
    w()
    w("---")
    w()

    # ---- 1. Executive Summary ----
    w("## 1. Executive Summary")
    w()
    w(f"- **Repository role:** {m1.get('application_type','UNKNOWN')} "
      f"({m2.get('language','?')}) — *what the codebase is*")
    w(f"- **Architecture:** {m1.get('architecture','UNKNOWN')} "
      f"— *how it is structured (independent of role)*")
    w(f"- **Overall health:** {rating}")
    w(f"- **Risk level:** {risk}")
    w(f"- **Governance gate:** {rep.get('gate')}")
    w()
    w("**Why this rating (explicit metrics):**")
    w()
    w("| Metric | Value |")
    w("|---|---|")
    for k, v in metrics.items():
        w(f"| {k.replace('_',' ')} | {v} |")
    w()
    if rating == "NOT_RATED":
        # Non-Python engine: no Phase 3A/3B measurements exist. State the
        # boundary rather than manufacturing a SOUND from absent fields.
        w(f"**Health rating does not apply to this language.** SOUND/UNVERIFIED "
          f"is a Python Module 3 judgement, computed from guess counts, edge "
          f"provenance, and attribute-call resolution. The "
          f"`{m2.get('language','?')}` engine produces a verified call graph and "
          f"a declared truth boundary, but not those metrics — so the report "
          f"declines to rate integrity on an axis it did not measure, rather "
          f"than reporting a 0 it never observed.")
    else:
        w(f"**Health = analysis integrity, not resolution coverage.** "
          f"CodeTruth's guarantee is *no fabrications; every decline categorized* "
          f"- not *resolves all dynamic calls*. A dynamic framework with low "
          f"coverage but 0 guesses is SOUND (the analysis is trustworthy); it is "
          f"not penalized for the code being dynamic.")
        w()
        w(f"Rating rule: SOUND if `guesses == 0` AND `uncategorized_declines == 0` "
          f"(here: {metrics['guesses']} guesses, {metrics['uncategorized_declines']} "
          f"uncategorized). Otherwise UNVERIFIED. Risk LOW unless notable fixable "
          f"gaps ({metrics['fixable_inrepo_miss']} in-repo inheritance misses).")
        w()
        w(f"*Informational:* attribute-call resolution coverage "
          f"{metrics['attribute_calls_resolved']}/{metrics['attribute_call_baseline']} "
          f"= {metrics['attr_resolution_coverage_pct']}% (low is EXPECTED for dynamic "
          f"frameworks; not a health signal - most unresolved calls are dynamic "
          f"dispatch, correctly declined).")
    w()
    w("**Executive recommendation:** "
      + _exec_reco(rating, risk, metrics, rep.get('gate')))
    w()
    w("---")
    w()

    # ---- 2. Repository Overview (M1) ----
    w("## 2. Repository Overview (Module 1)")
    w()
    w(f"- **Repository role:** {m1.get('application_type','UNKNOWN')} "
      f"*(what the codebase is)*")
    w("- **Domain:** *(not yet classified — a separate Module 1 axis; left "
      "unclassified rather than guessed, pending a Module 1 revision)*")
    w(f"- **Architecture:** {m1.get('architecture','UNKNOWN')} "
      f"*(how it is structured — imported/consumed vs deployed app)*")
    w(f"- **Detected technologies:** {_tech_display(m1, repo_dir)} "
      f"*(frameworks/libraries detected in the code — a dependency the repo "
      f"uses, not the repo's identity)*")
    w(f"- **Governance status:** {m1.get('gate','UNKNOWN')}")
    w(f"- **Cognition confidence:** {m1.get('confidence','n/a')}")
    w()
    w("*These are **independent axes** and should not be conflated: **repository "
      "role** (what it is), **domain** (what it's about), **architecture** (how "
      "it's structured), and **detected technologies** (what it uses). Example: a "
      "web framework has role=LIBRARY and detected-technologies pointing at itself, "
      "while an app that imports it has role=WEB_APPLICATION / detected=Flask. "
      "Domain is not computed by Module 1 today and is intentionally shown as "
      "unclassified rather than inferred.*")
    w()
    w("*Source: Module 1 (Repository Cognition). Detected from code, not assumed.*")
    w()
    w("---")
    w()

    # ---- 3. Structural Analysis (M2) ----
    w("## 3. Structural Analysis (Module 2)")
    w()
    w(f"- **Language:** {m2.get('language','?')}")
    _fs = m2.get('files_scanned')
    if _fs is not None:
        w(f"- **Files scanned:** {_fs}")
    else:
        w(f"- **Files scanned:** not reported — the `{m2.get('language','?')}` "
          f"adapter emits no scanned-file count; {m2.get('files_routed','?')} "
          f"files were routed to it (routed is not scanned)")
    w(f"- **Functions:** {m2.get('functions',0)}")
    w(f"- **Classes:** {m2.get('classes',0)}")
    w(f"- **Call-graph edges (M2):** {m2.get('call_graph_edges',0)}")
    w(f"- **Unresolved attribute-calls:** {m2.get('unresolved_calls',0)} "
      f"(handed to Module 3 for reasoning)")
    w()
    w("*Source: Module 2 (Structural Analysis). Deterministic AST parse + call graph.*")
    w()
    w("---")
    w()

    # ---- 4. Architecture Analysis (M1 + M2) ----
    w("## 4. Architecture Analysis (Module 1 + Module 2)")
    w()
    w(f"- **Detected architecture pattern:** {m1.get('architecture','UNKNOWN')} "
      f"(Module 1) — *structural organization; distinct from the application "
      f"type ({m1.get('application_type','UNKNOWN')}) reported in section 2*")
    total_edges = ep.get("total_edges", 0)
    funcs = m2.get("functions", 1) or 1
    avg_fanout = round(total_edges / funcs, 2)
    w(f"- **Coupling (structural):** {total_edges} call-graph edges across "
      f"{m2.get('functions',0)} functions (avg fan-out {avg_fanout})")
    w()
    w("**Candidate architecture concerns:**")
    if policy:
        w(f"- Checked against provided policy `{policy}` (violations reported below).")
    else:
        w("- **No architecture policy provided.** CodeTruth reports structural "
          "dependency and coupling *facts* only. To assess **violations**, supply "
          "a layering policy (e.g. \"presentation must not import data-layer\"). "
          "Without a declared policy, no dependency is labeled a violation "
          "(Truth Boundary: we do not guess intended architecture).")
    w()
    w("*Source: Module 1 (pattern) + Module 2 (coupling facts). "
      "Violation assessment is policy-dependent.*")
    w()
    w("---")
    w()

    # ---- 5. Engineering Findings (M3) ----
    w("## 5. Engineering Findings (Module 3)")
    w()
    w("**Verified findings (resolved with certainty):**")
    w(f"- Attribute-calls resolved: {by_label.get('RESOLVED',0)}")
    w(f"- Net new edges merged into call graph: {ep.get('local_receiver_added',0)}")
    w(f"- Resolutions computed (may coincide with existing M2 edges): "
      f"inherited {lrc.get('local_inherited_method_call',0)}, "
      f"super() {lrc.get('super_call',0)}")
    w(f"- Total call-graph edges after reasoning: {ep.get('total_edges',0)}")
    w()
    w("**Engineering issues / declines (categorized):**")
    w(f"- Inferred (bounded): {by_label.get('INFERRED',0)}")
    w(f"- Ambiguous: {by_label.get('AMBIGUOUS',0)}")
    w(f"- Uncertain: {by_label.get('UNCERTAIN',0)}")
    w(f"- Unresolvable: {by_label.get('UNRESOLVABLE',0)}")
    w()
    w("**Unknown (Truth Boundary):**")
    if _py_m3:
        w(f"- Guesses made: **{tb.get('guesses',0)}**")
        w(f"- Numeric confidence scores: {tb.get('numeric_confidence_scores',0)} "
          f"(categorical labels only)")
    else:
        w(f"- Guess counting is a Python-engine measurement; the "
          f"`{m3.get('language','?')}` engine does not compute it. It emits a "
          f"declared truth boundary (scope + limitations) instead — see below.")
        _lims = (tb.get("limitations") or [])
        if _lims:
            w(f"- Declared boundary: {tb.get('scope','')} "
              f"— cannot see: {', '.join(map(str, _lims))}")
    w()
    w("*Source: Module 3 (Deterministic Reasoning).*")
    w()
    w("---")
    w()

    # ---- 6. Impact Analysis (M3) ----
    w("## 6. Impact Analysis (Module 3)")
    w()
    if impact_target:
        imp = _impact(repo, impact_target)
        w(f"**Target:** `{impact_target}`")
        w()
        if imp is None:
            w("- Impact analysis unavailable (target not found in call index).")
        else:
            w(f"- Direct callers: {imp.get('direct',0)}")
            w(f"- Transitive impact (functions affected): {imp.get('transitive',0)}")
            w(f"- Affected call chains sampled: {imp.get('sample',[])[:5]}")
        w()
    else:
        w("- No target specified. Run with `--impact <qualified.function.name>` to "
          "compute change impact (who-calls, transitive affected set, call chains) "
          "for a specific method before modifying it.")
        w()
    w("*Source: Module 3 reasoning queries (who-calls / impact-of over the "
      "verified call graph).*")
    w()
    w("---")
    w()

    # ---- 7. Engineering Gaps (M2 + M3) ----
    w("## 7. Engineering Gaps (Module 2 + Module 3)")
    w()
    w(f"- **Unresolved calls:** {m2.get('unresolved_calls',0)} attribute-calls "
      f"whose receiver type is not statically determinable")
    w(f"- **Inheritance limitations:** super() declines broken down as:")
    w(f"    - external base (correct, Truth Boundary): {lrc.get('super_decline_external',0)}")
    w(f"    - in-repo miss (fixable): {lrc.get('super_decline_inrepo_miss',0)}")
    w(f"    - no bases / non-class context: {lrc.get('super_decline_no_bases',0)}")
    w(f"    - cyclic (declined by guard): {lrc.get('super_decline_cyclic',0)}")
    w(f"- **Ambiguous receivers:** {lrc.get('ambiguous_receiver',0)}")
    w()
    w("*Source: Module 2 (unresolved sites) + Module 3 (categorized declines). "
      "Every gap has a documented reason; none is silently dropped.*")
    w()
    w("---")
    w()

    # ---- 8. Recommendations ----
    w("## 8. Recommendations")
    w()
    recos = _recommendations(rep, metrics, lrc)
    for pri in ("HIGH", "MEDIUM", "LOW"):
        items = [r for r in recos if r[0] == pri]
        w(f"**{pri} priority:**")
        if items:
            for _, text, evidence in items:
                w(f"- {text}  ")
                w(f"  *(linked finding: {evidence})*")
        else:
            w("- None.")
        w()
    w("*Every recommendation is linked to a verified finding above.*")
    w()
    w("---")
    w()

    # ---- 9. Confidence & Truth Boundary ----
    w("## 9. Confidence & Truth Boundary")
    w()
    w(f"- **Verified facts:** {by_label.get('RESOLVED',0)} resolved calls, "
      f"{ep.get('total_edges',0)} call-graph edges")
    w(f"- **Unknowns (explicitly flagged):** {m2.get('unresolved_calls',0)} "
      f"unresolved calls, each with a documented reason")
    w(f"- **Declined analyses:** categorized in section 7 (not silently dropped)")
    if _py_m3:
        w(f"- **Guesses made: {tb.get('guesses',0)}**")
    else:
        w(f"- **Guesses made:** not counted — guess accounting is a Python-engine "
          f"measurement; this language emits a declared truth boundary instead")
    w()
    w("> **No unsupported conclusions generated.** Every finding in this report is "
      "either directly computed from module output or explicitly marked as a "
      "derived metric or policy-dependent assessment. Where the analysis cannot "
      "resolve a fact, it is reported as unknown rather than guessed.")
    w()
    w("---")
    w()

    # ---- 10. Evidence & Traceability ----
    w("## 10. Evidence & Traceability")
    w()
    w("| Finding | Source | Evidence | Status |")
    w("|---|---|---|---|")
    w(f"| Repository role = {m1.get('application_type','?')} (architecture "
      f"= {m1.get('architecture','?')}, detected tech = {_tech_display(m1, repo_dir)}) "
      f"| Module 1 | cognition scan | verified |")
    w(f"| {m2.get('call_graph_edges',0)} edges (M2) -> {ep.get('total_edges',0)} "
      f"(after M3) | Module 2 + 3 | AST + reasoning | verified |")
    w(f"| {ep.get('local_receiver_added',0)} reasoning edges added | Module 3 | "
      f"C3 MRO + super() resolution | verified (in index) |")
    if _py_m3:
        w(f"| {tb.get('guesses',0)} guesses | Module 3 | Truth Boundary | verified |")
    else:
        w(f"| guesses not counted (Python-only metric) | Module 3 | "
          f"declared truth boundary | boundary stated |")
    w()
    w("*Every major finding links back to the module and evidence that produced it.*")
    w()
    w("---")
    w()

    # ---- 11. Module Contributions ----
    w("## 11. Module Contributions")
    w()
    w(f"- **Module 1 (Repository Cognition):** repository role "
      f"{m1.get('application_type','?')}, detected technologies "
      f"{_tech_display(m1, repo_dir)}, architecture {m1.get('architecture','?')} "
      f"(independent axes; domain not yet classified); "
      f"governance gate {rep.get('gate')}.")
    _fs2 = m2.get('files_scanned')
    _files_frag = (f"{_fs2} files" if _fs2 is not None
                   else f"{m2.get('files_routed','?')} files routed (scanned count "
                        f"not emitted by the {m2.get('language','?')} adapter)")
    w(f"- **Module 2 (Structural Graph):** {_files_frag}, "
      f"{m2.get('functions',0)} functions, {m2.get('classes',0)} classes, "
      f"{m2.get('call_graph_edges',0)} call-graph edges, "
      f"{m2.get('unresolved_calls',0)} unresolved sites.")
    if "guesses" in tb:
        w(f"- **Module 3 (Deterministic Reasoning):** "
          f"+{ep.get('local_receiver_added',0)} verified reasoning edges, "
          f"declines categorized, {tb['guesses']} guesses.")
    else:
        w(f"- **Module 3 (Deterministic Reasoning):** "
          f"{m3.get('language','?')} call graph via {m3.get('engine','bridge')}; "
          f"declared truth boundary. Guess counting and edge provenance are "
          f"Python-only measurements and are not claimed here.")
    w()
    w("*This shows how the final conclusions were reached — each module's "
      "contribution to the assessment.*")
    w()

    return "\n".join(L)


def _exec_reco(rating, risk, metrics, gate):
    if gate == "BLOCKED":
        return "Repository BLOCKED by governance gate; no structural work advised until reviewed."
    if rating == "UNVERIFIED":
        return ("Analysis integrity issue: guesses or uncategorized declines detected "
                "(both should be 0). Do not rely on findings until investigated.")
    if rating == "NOT_RATED":
        return ("The verified call graph and dependency findings below are usable; "
                "the integrity RATING (SOUND/UNVERIFIED) is a Python-only measurement "
                "and was not computed for this language. Read the findings as a "
                "verified in-repo floor, and the declared truth boundary for what "
                "the engine cannot see.")
    # SOUND
    return ("Analysis is trustworthy (0 fabrications, all declines categorized). "
            "The verified call graph is safe to use for change-impact checks. "
            "Unresolved calls are dynamic/external and correctly flagged, not "
            "guessed - treat them as known-unknowns when refactoring those paths.")


def _recommendations(rep, metrics, lrc):
    recos = []
    if rep.get("gate") == "REVIEW_REQUIRED":
        recos.append(("HIGH", "Resolve governance REVIEW_REQUIRED before automated modification.",
                      "Module 1 gate"))
    miss = lrc.get("super_decline_inrepo_miss", 0)
    if miss > 50:
        recos.append(("MEDIUM",
                      f"{miss} in-repo inheritance resolutions are incomplete; "
                      f"qualified-name resolution would recover these.",
                      "Module 3 super_decline_inrepo_miss"))
    unres = rep.get("module2", {}).get("unresolved_calls", 0)
    if unres > 0:
        recos.append(("LOW",
                      f"{unres} calls remain unresolved (dynamic/external receivers); "
                      f"expected for dynamic code, flagged not guessed.",
                      "Module 2 unresolved_calls"))
    if not recos:
        recos.append(("LOW", "No actionable engineering issues detected.", "all modules"))
    return recos


def _impact(repo, target):
    # SINGLE PRODUCT IMPACT PATH. The inline computation here was retired: it now
    # delegates to the flagship change_impact.analyze() so there is exactly one
    # impact implementation (two paths previously diverged - the _impact key-count
    # bug). Section 6 still consumes {direct, transitive, sample} unchanged.
    try:
        from v3.repository_reasoning.change_impact import analyze
        a = analyze(repo, target)
        if not isinstance(a, dict) or "error" in a:
            return None
        return {"direct": a.get("direct_count", len(a.get("direct_callers", []))),
                "transitive": a.get("affected_count", len(a.get("affected_callers", []))),
                "direct_callers": a.get("direct_callers", []),
                "sample": a.get("affected_callers", [])[:5]}
    except Exception:
        return None


def _incomplete_report(rep, display_name=None):
    shown = display_name or rep.get("repo")
    return (f"# CodeTruth Engineering Assessment Report\n\n"
            f"**Repository:** `{shown}`\n\n"
            f"**Status: {rep.get('status')}** — {rep.get('reason','')}\n\n"
            f"Gate: {rep.get('gate','?')}. "
            f"Pipeline did not complete; no findings generated (Truth Boundary: "
            f"nothing is reported that was not computed).\n")


def _tech_display(m1, repo_basename=None):
    """Detected-technologies string with an honesty guard. Module 1 can fall back
    to a folder-name-derived value (e.g. the temp clone dir 'ctlive_xxxx' shown as
    'Ctlive Xxxx') when it detects no real framework. We show 'not detected' in
    that case so the report never presents a non-detection — or a leaked clone
    folder name — as a finding. Suppression triggers on: 0 confidence, UNKNOWN
    type, empty/none value, OR a value that matches the repo directory name /
    clone prefix (the fallback's signature), regardless of confidence."""
    fw = m1.get("framework", "none")
    app = m1.get("application_type", "UNKNOWN")
    try:
        conf = float(m1.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        conf = 0.0

    def _norm(x):
        return "".join(str(x).lower().split()).replace("_", "").replace("-", "")

    # The reliable fallback signature is our clone-dir prefix 'ctlive_' (title-cased
    # to 'Ctlive ...'). We do NOT suppress merely because the framework matches the
    # folder name — a repo literally named 'flask' whose framework IS Flask is a real
    # detection, not a fallback, and must be preserved.
    looks_like_dirname = bool(fw) and _norm(fw).startswith("ctlive")

    if (conf <= 0.0 or app == "UNKNOWN" or not fw
            or str(fw).strip().lower() in ("none", "unknown", "")
            or looks_like_dirname):
        return "not detected"
    return fw


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", default=None)
    ap.add_argument("--impact", default=None)
    ap.add_argument("--policy", default=None)
    args = ap.parse_args(argv[1:])
    md = generate(args.repo, impact_target=args.impact, policy=args.policy)
    out = args.out or "codetruth_assessment.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"report written -> {out}")
    print(f"   ({len(md)} chars, {md.count(chr(10))} lines)")


if __name__ == "__main__":
    main(sys.argv)
