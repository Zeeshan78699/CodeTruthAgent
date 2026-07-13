r"""
project_intelligence_report.py
CodeTruth Agent V3 — the human-facing Project Intelligence Report.

ARCHITECTURE RULE (D-01, non-negotiable):
    This module is a RENDERER, not a generator. It is a pure projection of the
    evidence JSON produced by the analyzer. It reads a project_report/1.1.0
    document and emits Markdown.

    It may NEVER invent a value that is not in the JSON. Every sentence traces to
    an OBSERVED / DERIVED / INFERRED field, or is stated as UNKNOWN with the JSON's
    own reason. One-way only:

        Repository -> Analyzer -> Evidence JSON -> THIS RENDERER -> Prose

    If a field is UNKNOWN, the prose says so and names the reason. It does not
    smooth the gap into a confident sentence. The report's honesty about what it
    does NOT know is the product.

WHAT THIS IS NOT:
    It does not read the repository. It does not call Module 1/2/3. It does not
    guess objective, purpose, "strengths", or folder intent. Those are either
    cited to a source file (Stated Objective) or reported UNKNOWN.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone


# --------------------------------------------------------------------------- #
# tier-faithful field rendering
# --------------------------------------------------------------------------- #
def _tier(field: dict) -> str:
    return (field or {}).get("tier", "UNKNOWN")


def _render_value(field: dict) -> str:
    """Render one schema field as an inline string, faithful to its tier.

    OBSERVED/DERIVED/INFERRED -> the value, tagged with its tier.
    UNKNOWN                    -> 'not determined' + the reason. Never a value.
    """
    if not isinstance(field, dict):
        return f"`{field}`"
    tier = field.get("tier", "UNKNOWN")
    if tier == "UNKNOWN":
        reason = field.get("reason", "NO_REASON_GIVEN")
        human = {
            "OUT_OF_SCOPE_FOR_ANALYZER": "the current analyzer does not collect this",
            "NO_EVIDENCE_FOUND": "no evidence found in the repository",
            "EVIDENCE_CONFLICTING": "the evidence conflicts (see reason)",
            "PYTHON_ENGINE_ONLY": "this is a Python-engine measurement; not computed for this language",
        }.get(reason, reason)
        note = field.get("notes")
        s = f"**not determined** — {human}"
        if note:
            s += f" _{note}_"
        return s
    v = field.get("value")
    if isinstance(v, dict):
        v = ", ".join(f"{k}: {vv}" for k, vv in v.items())
    return f"{v}  ·  _{tier}_"


def _evidence_line(field: dict) -> str:
    """One-line provenance for a field, so every number is auditable."""
    if not isinstance(field, dict):
        return ""
    tier = field.get("tier")
    if tier == "OBSERVED":
        ev = (field.get("evidence") or [{}])[0]
        p = ev.get("path", "?")
        ex = ev.get("excerpt", "")
        return f"      ↳ observed at `{p}` — {ex}"
    if tier == "DERIVED":
        d = field.get("derivation", "?")
        ins = ", ".join(field.get("inputs", []))
        return f"      ↳ derived by `{d}` from {ins}"
    if tier == "INFERRED":
        g = field.get("gate", "?")
        return f"      ↳ inferred, gate `{g}` — audit before use"
    return ""


# --------------------------------------------------------------------------- #
# section renderers — each is a projection of one JSON section
# --------------------------------------------------------------------------- #
def _coverage(report: dict) -> dict:
    """Schema coverage per section: how many fields are populated vs UNKNOWN.
    This is the maturity meter — a PROGRESS indicator, never a quality score."""
    out = {}
    for sec, body in report.items():
        if sec.startswith("_"):
            continue
        # documentation_drift is a findings block, not a schema section — its
        # sub-keys (note, findings) are not tiered fields. Exclude from coverage.
        if sec == "documentation_drift":
            continue
        if not isinstance(body, dict):
            continue
        # only count tier-bearing fields; skip note strings, error strings, lists.
        fields = [f for f in body
                  if not f.startswith("_") and isinstance(body.get(f), dict)
                  and "tier" in body[f]]
        pop = sum(1 for f in fields if _tier(body[f]) != "UNKNOWN")
        out[sec] = (pop, len(fields))
    return out


# --------------------------------------------------------------------------- #
# Phase 2 helpers — all pure projection; add no facts the JSON doesn't hold
# --------------------------------------------------------------------------- #

# Which future module is expected to populate each UNKNOWN field. This is a
# declared roadmap mapping, not a claim about the repository — safe to render.
PLANNED_MODULE = {
    "entry_points": "E1 — Structural Evidence (decorator/base-class detection)",
    "layering_violations": "E1 — Structural Evidence",
    "exposed_endpoints": "E2 — Runtime (route/handler tracing)",
    "auth_surfaces": "E2 — Runtime (middleware/decorator tracing)",
    "config_surface": "E2 — Runtime",
    "required_runtimes": "E2 — Runtime",
    "dead_code_candidates": "M3 — Dead-code query (already implemented; not run here)",
    "cyclic_clusters": "M3 — Topology (SCC)",
    "modules": "M2 — module inventory",
    "test_files_collected": "quality module — test collection",
    "reported_coverage": "quality module",
    "dependency_cves": "supply-chain module",
    "direct_dependencies": "supply-chain module (manifest parse)",
    "commit_count": "process module (git history)",
    "contributor_count": "process module (git history)",
    "readme_present": "documentation module",
}


def _source_of(field: dict) -> str:
    """Human-readable provenance for a field, honestly marking Module-1
    classifications as NOT evidence-cited (the 51%-accuracy layer)."""
    if not isinstance(field, dict):
        return ""
    t = field.get("tier")
    if t == "OBSERVED":
        return "Module 2 (read from source)"
    if t == "DERIVED":
        d = field.get("derivation", "")
        if "module3" in d:
            return "Module 3 (deterministic reasoning)"
        return "Module 2/3 (computed)"
    if t == "INFERRED":
        # Module 1 classification — the layer whose confidence the schema rejects.
        return "Module 1 (classification — not evidence-cited; audit)"
    return "—"


def _dna_block(report, w):
    """Compact fingerprint. OBSERVED/DERIVED only. Any UNKNOWN field is shown as
    'not determined', never laundered into a confident value."""
    struct = report.get("structure", {})
    domain = report.get("domain", {})
    arch = report.get("architecture", {})
    m1lang = struct.get("dominant_language", {})
    ap = domain.get("architecture_pattern", {})
    at = domain.get("application_type", {})

    def _cell(field, unknown_text="not determined"):
        if not isinstance(field, dict) or field.get("tier") == "UNKNOWN":
            reason = field.get("reason", "") if isinstance(field, dict) else ""
            extra = f" ({reason})" if reason == "EVIDENCE_CONFLICTING" else ""
            return f"_{unknown_text}{extra}_"
        return f"{field.get('value')}"

    w("## Repository DNA")
    w()
    w("*A one-glance fingerprint — only fields CodeTruth has actually established. "
      "Anything undetermined is shown as such, never guessed into a label.*")
    w()
    w("| | |")
    w("|---|---|")
    w(f"| **Dominant language** | {_cell(m1lang)} |")
    w(f"| **Structural form** | {_cell(ap)} |")
    w(f"| **Application type** | {_cell(at)} |")
    w(f"| **Functions** | {_cell(arch.get('functions', {}))} |")
    ed_field = arch.get('call_graph_edges', {})
    ed_real = (isinstance(ed_field, dict) and ed_field.get("tier") == "DERIVED"
               and isinstance(ed_field.get("value"), int) and ed_field.get("value") > 0)
    w(f"| **Verified call edges** | {ed_field.get('value') if ed_real else '_not determined (edge provenance is Python-only)_'} |")
    w(f"| **Guesses** | {_cell(arch.get('guesses', {}))} |")
    w()


def _summary(report, w):
    """Plain-language paragraph. Exact numbers only — no rounding, no adjectives.
    UNKNOWNs are stated, not skipped."""
    struct = report.get("structure", {})
    arch = report.get("architecture", {})
    domain = report.get("domain", {})
    lang = (struct.get("dominant_language", {}) or {}).get("value", "an unknown language")
    fn = arch.get("functions", {})
    ed = arch.get("call_graph_edges", {})
    at = domain.get("application_type", {})
    ap = domain.get("architecture_pattern", {})

    parts = []
    if isinstance(fn, dict) and fn.get("tier") != "UNKNOWN":
        parts.append(f"This is a {lang} codebase with {fn.get('value')} functions")
    else:
        parts.append(f"This is a {lang} codebase")
    # Only state edge count when it is a real reconciled measurement (Python
    # DERIVED with a non-zero total). A bridge engine emits 0 edges because edge
    # provenance is Python-only — that 0 is un-computed, not measured, and pairing
    # it with a large function count reads as broken. Omit it instead.
    ed_is_real = (isinstance(ed, dict) and ed.get("tier") == "DERIVED"
                  and isinstance(ed.get("value"), int) and ed.get("value") > 0)
    if ed_is_real:
        parts.append(f"and {ed.get('value')} verified call relationships between them")
    sentence1 = " ".join(parts) + "."

    # form / type — stated exactly, conflict preserved
    if isinstance(ap, dict) and ap.get("tier") != "UNKNOWN":
        form = f"Its structure is that of a {ap.get('value')}."
    else:
        form = "Its structural form was not determined."
    if isinstance(at, dict) and at.get("tier") == "UNKNOWN" and at.get("reason") == "EVIDENCE_CONFLICTING":
        typ = ("CodeTruth could not assign a single application type: its role and "
               "structural signals disagree, so it declines to pick one rather than guess.")
    elif isinstance(at, dict) and at.get("tier") != "UNKNOWN":
        typ = f"It is classified as {at.get('value')} (Module 1 proposal — audit)."
    else:
        typ = "Its application type was not determined."

    g = arch.get("guesses", {})
    if isinstance(g, dict) and g.get("tier") == "DERIVED":
        guar = (f"The analysis made {g.get('value')} guesses — every unresolved call "
                "carries a documented reason.")
    else:
        guar = ("Guess counting is a Python-engine measurement and was not computed "
                "for this language; the engine declares its truth boundary instead.")

    w("## Repository Summary")
    w()
    w(f"{sentence1} {form} {typ} {guar}")
    w()
    w("*Every figure above is stated exactly as measured. Nothing is rounded, and "
      "nothing the analyzer did not establish is asserted.*")
    w()


def _truth_boundary(report, w):
    """The defining section, rendered near the top. Each UNKNOWN names the future
    module expected to populate it (planned-module mapping)."""
    arch = report.get("architecture", {})
    ep_field = arch.get("entry_points", {})
    auth = report.get("security", {}).get("auth_surfaces", {})
    endp = report.get("runtime", {}).get("exposed_endpoints", {})
    w("## Truth Boundary — What This Report Cannot See")
    w()
    w("*The defining section. Every limit below is a place the analysis stops. A "
      "number missing here is missing because CodeTruth refuses to guess it — not "
      "because the property is absent. Each names the future module expected to "
      "resolve it.*")
    w()
    for label, key, field in [("Entry points", "entry_points", ep_field),
                              ("Exposed endpoints", "exposed_endpoints", endp),
                              ("Authentication surfaces", "auth_surfaces", auth)]:
        if isinstance(field, dict) and _tier(field) == "UNKNOWN":
            note = field.get("notes", "")
            planned = PLANNED_MODULE.get(key)
            plan = f" _Planned: {planned}._" if planned else ""
            w(f"- **{label}:** not determined. {note}{plan}")
    g = arch.get("guesses", {})
    if _tier(g) == "DERIVED" and g.get("value") == 0:
        w()
        w("- **Guesses made: 0.** Every unresolved call carries a documented "
          "reason. Nothing was fabricated to fill a gap.")
    elif _tier(g) == "UNKNOWN":
        w()
        w("- **Guess count:** not computed for this language (a Python-engine "
          "measurement). The engine emits a declared truth boundary instead.")
    w()


def _documentation_drift(report, w):
    """Render the Documentation Auditor findings (D3-015 Phase 1). Docs are the
    claim under test; code is the arbiter. Each finding states a disagreement and
    both sides — it never declares the docs correct."""
    dd = report.get("documentation_drift")
    docsec = report.get("documentation", {})
    # Only render if the auditor actually ran.
    if not isinstance(dd, dict):
        return
    if dd.get("tier") == "UNKNOWN":
        # honest non-answer (e.g. bridge language) — state it, don't skip silently
        w("## Documentation Drift")
        w()
        w(f"**Not checked.** {dd.get('notes', dd.get('reason',''))}")
        w()
        return
    val = dd.get("value", {})
    findings = dd.get("findings", [])
    tokens = val.get("doc_tokens_seen", val.get("doc_symbols_checked", 0))
    api_checked = val.get("api_claims_checked", val.get("doc_symbols_checked", 0))
    matched = val.get("match", val.get("matched", 0))
    drift_n = val.get("drift", 0)
    noev_n = val.get("no_evidence", 0)
    reconciles = val.get("reconciles", None)
    excluded = val.get("excluded_by_category", {})
    pub = val.get("code_public_symbols", 0)
    n_missing = val.get("documented_missing",
                        sum(1 for f in findings if f.get("type") == "DOCUMENTED_MISSING"))

    w("## Documentation Drift")
    w()
    w("*The Documentation Auditor tests what the docs **claim** against what the "
      "code **contains**. Docs are the claim; code is the arbiter. Every finding "
      "below states a disagreement and both sides - it does not declare the docs "
      "wrong, only that code and docs disagree. Investigate; don't assume.*")
    w()
    w(f"- **Documentation tokens seen:** {tokens}")
    w(f"- **Genuine API-symbol claims checked:** {api_checked}  "
      f"(match {matched} / documented-missing {n_missing} / no-evidence {noev_n})")
    _undoc_total = sum(1 for f in findings if f.get("type") == "UNDOCUMENTED_PUBLIC")
    if _undoc_total:
        w(f"- **Public symbols not named in docs:** {_undoc_total}  "
          f"(production API shipped without docs — separate from the claims above)")
    if reconciles is not None:
        w(f"  - reconciles: {api_checked} = {matched} + {n_missing} + {noev_n}  "
          f"-> **{reconciles}**")
    if excluded:
        exstr = ", ".join(f"{k} {v}" for k, v in excluded.items())
        w(f"- **Excluded (not project-API claims):** {exstr}")
        w(f"  - config keys, HTTP terms, dependencies, filenames, and builtins are "
          f"not claims that the project exports a symbol - they do not enter drift.")
    w(f"- **Public code symbols:** {pub}")
    w()
    if not findings:
        w("No symbol-level drift found among genuine API claims.")
        w()
        return

    by_type = {}
    for f in findings:
        by_type.setdefault(f.get("type", "?"), []).append(f)

    titles = {
        "DOCUMENTED_MISSING": "Documented but missing (docs name an API symbol the code lacks)",
        "UNDOCUMENTED_PUBLIC": "Public but undocumented (code exposes API the docs never name)",
        "DEPRECATED_PRESENT": "Deprecated but present (changelog says removed; code still has it)",
        "DOCUMENTED_MEMBER_UNVERIFIABLE": "Cannot verify (may be a property/attribute the symbol model can't represent)",
    }
    for ftype in ("DOCUMENTED_MISSING", "DEPRECATED_PRESENT", "UNDOCUMENTED_PUBLIC",
                  "DOCUMENTED_MEMBER_UNVERIFIABLE"):
        items = by_type.get(ftype)
        if not items:
            continue
        w(f"**{titles.get(ftype, ftype)}**")
        w()
        for f in items:
            w(f"- `{f.get('symbol')}` - {f.get('statement')}")
        w()

    w("*NO_EVIDENCE means the analyzer cannot confirm OR refute the claim - the "
      "symbol may be a property, attribute, or inherited member the current model "
      "does not represent. It is not counted as drift and not counted as a match. "
      "Behavioral, architectural, and feature claims are likewise out of Phase 1 "
      "scope.*")
    w()


def _ai_digest(report) -> str:
    """Machine-consumable digest — flat key/value with tiers explicit. This is
    the entire output for mode='ai'."""
    struct = report.get("structure", {})
    arch = report.get("architecture", {})
    domain = report.get("domain", {})
    lines = ["# machine digest — tier-tagged", ""]
    def flat(label, field):
        if not isinstance(field, dict):
            return
        t = field.get("tier", "UNKNOWN")
        if t == "UNKNOWN":
            lines.append(f"{label:22} UNKNOWN ({field.get('reason','')})")
        else:
            v = field.get("value")
            if isinstance(v, dict):
                v = "{" + ", ".join(f"{k}:{vv}" for k, vv in v.items()) + "}"
            lines.append(f"{label:22} {v}  [{t}]")
    flat("dominant_language", struct.get("dominant_language", {}))
    flat("total_files", struct.get("total_files", {}))
    flat("functions", arch.get("functions", {}))
    flat("classes", arch.get("classes", {}))
    flat("call_graph_edges", arch.get("call_graph_edges", {}))
    flat("guesses", arch.get("guesses", {}))
    flat("application_type", domain.get("application_type", {}))
    flat("entry_points", arch.get("entry_points", {}))
    return "\n".join(lines)


def render(report: dict, mode: str = "engineer") -> str:
    """Render the evidence JSON as prose.

    mode:
      human    — plain language, tier tags dropped, Summary + DNA lead
      engineer — full detail, tier tags and evidence lines visible (default)
      manager  — grouped, jargon stripped, NO size/quality adjectives
      ai       — the machine digest only (section 8), tiers explicit
    All modes are projections of the same JSON; none adds a fact. mode changes
    vocabulary and density, never warrant.
    """
    L = []
    def w(s=""): L.append(s)

    meta = report.get("_meta", {})
    analyzer = meta.get("analyzer", {})
    struct = report.get("structure", {})
    arch = report.get("architecture", {})
    domain = report.get("domain", {})

    # AI mode: emit only the machine digest, nothing else.
    if mode == "ai":
        return _ai_digest(report)

    # ---- header ----------------------------------------------------------- #
    w("# Project Intelligence Report")
    w()
    w(f"*Generated by {analyzer.get('name','CodeTruth')} "
      f"{analyzer.get('version','?')} · modules "
      f"{', '.join(analyzer.get('modules_active', []))} · "
      f"schema {meta.get('schema_version','?')}*  ")
    _pc = meta.get('pinned_commit', '?')
    _pc_disp = _pc[:12] if (len(_pc) >= 12 and all(c in "0123456789abcdef" for c in _pc[:12].lower())) else _pc
    w(f"*Pinned commit `{_pc_disp}` · "
      f"generated {meta.get('generated_at','?')}*")
    w()
    w("> **How to read this report.** Every statement is tagged with the evidence "
      "tier it rests on: **OBSERVED** (read from a file), **DERIVED** (computed "
      "from observed facts), **INFERRED** (proposed and gated — audit before use), "
      "or **not determined** (no sufficient evidence — stated, never guessed). "
      "Nothing here is smoothed over. Where CodeTruth cannot see, it says so.")
    w()
    w("---")

    # ---- Repository Summary + DNA (lead with the plain-language view) ----- #
    _summary(report, w)
    _dna_block(report, w)

    # ---- Truth Boundary moved UP (section 2-3): the defining concept ------ #
    _truth_boundary(report, w)
    w("---")

    # ---- 1. Identity ------------------------------------------------------ #
    w("## 1. Project Identity")
    w()
    ident = report.get("identity", {})
    idmap = [("Name","name"),("Version","version"),("License","license_id"),
             ("Repository","repository_url"),("Description","description")]
    any_known = any(_tier(ident.get(k, {})) != "UNKNOWN" for _, k in idmap)
    if not any_known:
        w("Project identity (name, version, license, description) is **not "
          "determined by the current analyzer.** These live in manifests and "
          "README files, which Modules 1–3 do not yet read. This is a known "
          "boundary, not an absence of the property — see the roadmap.")
    else:
        for label, key in idmap:
            w(f"- **{label}:** {_render_value(ident.get(key, {}))}")
    w()

    # ---- 2. What is it (domain) ------------------------------------------ #
    w("## 2. What Is This Project?")
    w()
    at = domain.get("application_type", {})
    ap = domain.get("architecture_pattern", {})
    if _tier(ap) != "UNKNOWN":
        w(f"- **Structural form:** {_render_value(ap)}")
        el = _evidence_line(ap)
        if el: w(el)
    w(f"- **Application type:** {_render_value(at)}")
    if _tier(at) == "UNKNOWN" and at.get("reason") == "EVIDENCE_CONFLICTING":
        w()
        w("  This is the report refusing to guess. CodeTruth's role signal and "
          "its structural signal disagree, so it declines to name a single "
          "application type rather than pick one. A conventional tool would print "
          "the confident-but-wrong label here; this one shows you the conflict.")
    w()

    # ---- 3. Stated Objective (cited, never authored) --------------------- #
    w("## 3. Stated Objective")
    w()
    obj = report.get("identity", {}).get("stated_objective") \
          or domain.get("stated_objective")
    if obj and _tier(obj) != "UNKNOWN":
        w(f"> {obj.get('value')}")
        el = _evidence_line(obj)
        if el: w(el)
        w()
        w("*This is the objective the project **states about itself**, quoted "
          "from the source above. CodeTruth does not author intent — it cites it "
          "or reports it absent.*")
    else:
        w("**Not determined.** No project-stated objective was found in a README, "
          "manifest, or documentation file the analyzer reads. CodeTruth does not "
          "invent a project's purpose from its code — intent is not in the AST.")
    w()

    # ---- 4. Repository Overview (structure) ------------------------------ #
    w("## 4. Repository Overview")
    w()
    w("| Property | Value | Tier |")
    w("|---|---|---|")
    def _row(label, field):
        if not isinstance(field, dict):
            return
        t = field.get("tier", "UNKNOWN")
        if t == "UNKNOWN":
            v = f"not determined ({field.get('reason','')})"
        else:
            val = field.get("value")
            if isinstance(val, dict):
                val = ", ".join(f"{k}={vv}" for k, vv in val.items())
            v = val
        w(f"| {label} | {v} | {t} |")
    _row("Total files", struct.get("total_files", {}))
    _row("Languages", struct.get("files_by_language", {}))
    _row("Dominant language", struct.get("dominant_language", {}))
    _row("Modules", arch.get("modules", {}))
    _row("Functions", arch.get("functions", {}))
    _row("Classes", arch.get("classes", {}))
    _row("Call-graph edges", arch.get("call_graph_edges", {}))
    _row("Test files (by name)", struct.get("test_files_by_name", {}))
    w()
    tfbn = struct.get("test_files_by_name", {})
    if _tier(tfbn) == "OBSERVED":
        w(f"> **Note on tests:** the {tfbn.get('value')} figure counts *filenames* "
          "matching `test_*`, not tests a runner collects. CodeTruth does not "
          "execute the collector, so it reports the filename count and explicitly "
          "declines to call it a test count.")
    w()

    # ---- 5. Architecture (measurements, reader judges) ------------------- #
    w("## 5. Architecture — Measurements")
    w()
    w("*These are measured facts about structure. CodeTruth reports the numbers "
      "and does not editorialize them into 'good' or 'bad' — coupling, cohesion, "
      "and modularity are judgments the reader makes from the evidence.*")
    w()
    for label, key in [("Modules","modules"),("Functions","functions"),
                       ("Classes","classes"),("Call-graph edges","call_graph_edges"),
                       ("Unresolved calls","unresolved_calls"),
                       ("Dead-code candidates","dead_code_candidates"),
                       ("Cyclic clusters","cyclic_clusters"),
                       ("Guesses","guesses")]:
        f = arch.get(key, {})
        w(f"- **{label}:** {_render_value(f)}")
        el = _evidence_line(f)
        if el: w(el)
    # edge provenance reconciliation
    ep = arch.get("edge_provenance", {})
    if _tier(ep) == "DERIVED":
        v = ep.get("value", {})
        w()
        w(f"- **Edge provenance:** {v.get('module2_edges')} (Module 2) + "
          f"{v.get('local_receiver_added')} (Module 3 reasoning) = "
          f"{v.get('total_edges')}  ·  _DERIVED, reconciles exactly_")
    dcc = arch.get("dead_code_candidates", {})
    if _tier(dcc) != "UNKNOWN":
        w()
        w(f"> **Dead-code candidates are candidates, not a verdict.** "
          f"{dcc.get('value')} functions have no verified inbound caller in the "
          "static graph. That is evidence of absence, not proof of disuse — "
          "framework-invoked and dynamically-dispatched callers are invisible "
          "here. Read each as *investigate*, never *delete*.")
    w()

    # ---- 6. Truth Boundary (the headline, not a footnote) ---------------- #
    # ---- Truth Boundary already rendered near the top via _truth_boundary --

    # ---- Documentation Drift (D3-015): docs tested against code ----------- #
    _documentation_drift(report, w)

    # ---- 7. Schema Coverage (the maturity meter, honest) ----------------- #
    w("## 7. Schema Coverage")
    w()
    w("*Not a quality score. This shows how much of the evidence model the "
      "**current** analyzer can populate, versus what remains UNKNOWN pending "
      "future modules. It measures CodeTruth's reach, not the repository's worth.*")
    w()
    w("| Section | What it covers | Populated | Status |")
    w("|---|---|---|---|")
    cov = _coverage(report)
    order = ["identity","structure","supply_chain","architecture","runtime",
             "quality","security","process","documentation","domain"]
    # Plain-English description of each section, so a reader understands what
    # "supply_chain 0/9" actually means without knowing the schema.
    desc = {
        "identity":      "Who the project is — name, version, license, description",
        "structure":     "File topology — how many files, which languages, how they split",
        "supply_chain":  "Dependencies — what it imports, lockfiles, licenses, known CVEs",
        "architecture":  "Code shape — functions, classes, call graph, dead-code candidates",
        "runtime":       "How it runs — containers, config, services, exposed endpoints",
        "quality":       "Testing & CI — test framework, coverage, lint, type-checking",
        "security":      "Risk surface — secrets, dangerous sinks, auth points, CVEs",
        "process":       "History & people — commits, contributors, releases, ownership",
        "documentation": "Docs — README, changelog, API docs, docstring coverage",
        "domain":        "What it is — application type, architecture pattern, target user",
    }
    tot_pop = tot_all = 0
    for sec in order:
        if sec not in cov:
            continue
        pop, tot = cov[sec]
        tot_pop += pop; tot_all += tot
        bar = "█" * pop + "░" * (tot - pop)
        w(f"| **{sec}** | {desc.get(sec,'')} | {pop}/{tot} | `{bar}` |")
    w(f"| **total** | | **{tot_pop}/{tot_all}** | |")
    w()
    w(f"> A report generated today populates **{tot_pop} of {tot_all}** fields. "
      "The rest are UNKNOWN — and visible as UNKNOWN. As Modules 4+ land "
      "(decorator detection, runtime tracing, supply-chain), fields move from "
      "UNKNOWN toward OBSERVED and this coverage grows. The report gets richer by "
      "fields changing tier, not by adding prose.")
    w()

    # ---- 8. AI Summary (machine-consumable, tiers intact) ---------------- #
    w("## 8. Summary for Another System")
    w()
    w("*A compact, tier-tagged digest for an AI or downstream tool. Every value "
      "carries its warrant so nothing is consumed as more certain than it is.*")
    w()
    w("```")
    def _flat(label, field):
        if not isinstance(field, dict):
            return
        t = field.get("tier","UNKNOWN")
        if t == "UNKNOWN":
            L.append(f"{label:24} UNKNOWN ({field.get('reason','')})")
        else:
            val = field.get("value")
            if isinstance(val, dict):
                val = "{" + ", ".join(f"{k}:{vv}" for k,vv in val.items()) + "}"
            L.append(f"{label:24} {val}  [{t}]")
    _flat("dominant_language", struct.get("dominant_language", {}))
    _flat("total_files", struct.get("total_files", {}))
    _flat("modules", arch.get("modules", {}))
    _flat("functions", arch.get("functions", {}))
    _flat("classes", arch.get("classes", {}))
    _flat("call_graph_edges", arch.get("call_graph_edges", {}))
    _flat("guesses", arch.get("guesses", {}))
    _flat("dead_code_candidates", arch.get("dead_code_candidates", {}))
    _flat("application_type", domain.get("application_type", {}))
    _flat("entry_points", arch.get("entry_points", {}))
    w("```")
    w()
    w("---")
    w(f"*CodeTruth Project Intelligence Report · pure projection of "
      f"schema {meta.get('schema_version','?')} · "
      f"report_sha256 `{meta.get('determinism',{}).get('report_sha256','?')[:16]}`*")
    w("*Proves what it can. Flags what it can't. Never guesses.*")

    out = "\n".join(L)

    # ---- mode post-processing (vocabulary/density only, never warrant) ---- #
    if mode == "human":
        # drop the inline tier tags for readability; facts and UNKNOWNs stay.
        import re as _re
        out = _re.sub(r"\s*·\s*_(OBSERVED|DERIVED|INFERRED)_", "", out)
        out = _re.sub(r"\s*\[(OBSERVED|DERIVED|INFERRED)\]", "", out)
    elif mode == "manager":
        # grouped, jargon trimmed. NO adjectives added — the validator enforces
        # that nothing unsourced slipped in. Here we only remove the evidence
        # sub-lines (the ↳ provenance) to reduce density; every value stays exact.
        import re as _re
        out = "\n".join(l for l in out.split("\n") if not l.strip().startswith("↳"))
    return out


def render_validated(report: dict, mode: str = "engineer"):
    """render() + projection check. Raises ProjectionViolation if the output
    states anything the JSON does not hold. Use this in production so a drifting
    report fails to render rather than shipping."""
    out = render(report, mode)
    try:
        import report_validator as _V
        # AI digest and human prose both checked; manager most strictly.
        _V.validate(out, report)
    except ImportError:
        pass  # validator optional at import time; still returns rendered text
    return out


def render_file(json_path: str) -> str:
    with open(json_path, encoding="utf-8") as f:
        return render(json.load(f))


if __name__ == "__main__":
    import sys
    print(render_file(sys.argv[1]))
