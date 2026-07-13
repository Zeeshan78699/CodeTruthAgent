r"""
pipeline.py
CodeTruth Agent V3 — Module Pipeline Verification Harness.

WHAT THIS IS
    A stage-by-stage view of how the modules compose:

        Module 1 (Cognition) -> language routing -> Module 2 (Structure)
                             -> Module 3 (Reasoning) -> governance

    It exists to REVIEW and VERIFY the pipeline: each stage's inputs, outputs,
    boundary conditions, and the invariants that hold between them. Run it on a
    repository to see exactly what each module contributed and where the Truth
    Boundary falls.

WHAT THIS IS NOT
    It is NOT a second implementation. Every decision — language routing,
    adapter selection, artifact checks, Module 3 dispatch — is IMPORTED from
    `v3.run_codetruth`, the single canonical entry point.

    This matters. A previous version of this file carried its own
    `detect_language()` and its own `DOMAIN_TO_LANGUAGE` map. It drifted from
    the real router and preserved a bug (`"ERP_SYSTEM": "sql"`) that had already
    been fixed elsewhere. Nothing imported it, so nothing caught it.

    Rule: this file may READ the pipeline. It may never DECIDE for it.
    If you find yourself writing `if language == ...` here, stop.

USAGE
    python v3/main_pipeline_to_run/pipeline.py <repo_path> [--force] [--json]
    python v3/main_pipeline_to_run/pipeline.py --registry     (no repo needed)

EXTENDING (Module 4+)
    Append to MODULE_REGISTRY. Each stage declares what it reads, what it emits,
    and what it CANNOT establish. A stage with no declared limitation is a stage
    that has not been thought about.
"""
import argparse
import json
import os
import sys
from pathlib import Path


# --------------------------------------------------------------------------- #
# path bootstrap — locate the project root the same way the app does
# --------------------------------------------------------------------------- #
def _bootstrap_path():
    here = Path(__file__).resolve()
    root = here.parent.parent.parent          # .../CodeTruthAgent
    v3 = root / "v3"
    for p in (str(root), str(v3)):
        if p not in sys.path:
            sys.path.insert(0, p)
    return root


PROJECT_ROOT = _bootstrap_path()

# ---- the ONLY source of pipeline decisions. Imported, never reimplemented. ----
from v3.run_codetruth import (          # noqa: E402
    _m1,
    detect_language_meta,
    get_adapter,
    _files_for_language,
    _deep_recursion,
    _m2_summary,
    _has_primary_artifacts,
    _has_reasoning_artifacts,
    _module3_for_language,
    _unskippable_venvs,
)


# --------------------------------------------------------------------------- #
# MODULE REGISTRY
#
# Each entry declares, for one stage: what it reads, what it emits, and what it
# CANNOT establish. The third field is not decoration — a stage whose limits are
# undeclared is a stage that will eventually be trusted beyond its evidence.
# --------------------------------------------------------------------------- #
MODULE_REGISTRY = [
    {
        "id": "M1",
        "name": "Repository Cognition",
        "status": "FROZEN",
        "reads": "repository files, dependency manifests, framework signatures",
        "emits": "application_type, framework, architecture, confidence, governance gate",
        "cannot_establish": [
            "domain (not computed; reported as 'not yet classified')",
            "reliable confidence — a 94-repo held-out evaluation measured accuracy "
            "INVERSELY correlated with confidence (32% correct at conf 1.0)",
            "language_composition — measured EMPTY on 11 of 11 probed repositories "
            "across 5 languages. detect_language_meta's first branch is dead code.",
        ],
    },
    {
        "id": "ROUTE",
        "name": "Language Routing",
        "status": "ACTIVE",
        "reads": ("bridge.classify_files() file counts. "
                  "(M1.language_composition is checked FIRST in code, but was measured "
                  "EMPTY on 11 of 11 probed repositories across 5 languages — that "
                  "branch has never executed. It is dead code, not a fallback.)"),
        "emits": "language, source, confidence, files_routed",
        "cannot_establish": [
            "the correct language when two are near parity — PyTorch is 4,733 "
            "C/C++ vs 4,609 Python files, a 1.3% margin",
            "which language a user *wants* analyzed; it selects by file count",
            "a language at all when classify_files() finds no classifiable source — "
            "the true fallback is DOMAIN_TO_LANGUAGE, a hardcoded map from "
            "application_type. It routed odoo (ERP_SYSTEM) to sql: 77 files analyzed, "
            "8,485 Python files ignored. Now flagged low-confidence and forced to "
            "REVIEW_REQUIRED.",
        ],
    },
    {
        "id": "M2",
        "name": "Repository Graph",
        "status": "FROZEN",
        "reads": "source files for the selected language",
        "emits": "function_graph, class_graph, call_graph, unresolved, governance_gate",
        "cannot_establish": [
            "directed call edges for Go and C# — those adapters record callees "
            "without enclosing callers (Module 3 re-parses to recover them)",
            "callers invoked via decorators, middleware, or framework registration",
            "in-repo cross-module calls under some src/ layouts (tagged <external>)",
        ],
    },
    {
        "id": "M3",
        "name": "Repository Reasoning",
        "status": "PENDING FREEZE",
        "reads": "M2's graph (Python) or re-parsed source (Go/C#) or SQL lineage",
        "emits": "reasoning index, who-calls, impact, dead-code candidates, truth_boundary",
        "cannot_establish": [
            "complete caller sets — every result is a verified in-repo FLOOR",
            "runtime behaviour; it reads structure, it does not execute",
            "deep resolution outside Python (no MRO, super(), edge provenance, guess count)",
        ],
    },
    # ── EVIDENCE TIERS — not modules. ──────────────────────────────────────── #
    # These are E1/E2/E3, NOT M4/M5/M6. The frozen architecture already binds
    # M4 (Data-Flow Tracing), M5 (Failure & Impact), M6 (Engineering
    # Intelligence) and M7–M10 to V3-### requirement IDs and success criteria.
    # Numbering evidence tiers as modules collides with six of them. The tiers
    # bind to labels, not requirements. Declare before you build.
    {
        "id": "E1",
        "name": "Structural Evidence (decorators, base classes)",
        "status": "NOT BUILT",
        "reads": "decorator_list and base-class names from the AST",
        "emits": "structural_evidence: which functions carry framework-shaped decorators",
        "cannot_establish": [
            "that the framework actually CALLS the decorated function — "
            "@app.route is a token in the source, not a proven caller",
            "anything about runtime behaviour",
        ],
    },
    {
        "id": "E2",
        "name": "Behavioral Evidence (runtime tracing)",
        "status": "NOT BUILT",
        "reads": "actual execution under a named workload",
        "emits": "observed_runtime(workload=X): edges that executed",
        "cannot_establish": [
            "that an unobserved edge does not exist — untested code is not dead code",
            "behaviour on any workload other than the one that was run",
        ],
    },
    {
        "id": "E3",
        "name": "Sound Symbolic Analysis",
        "status": "NOT BUILT",
        "reads": "abstract semantics over bounded property classes",
        "emits": "proven_sound | unknown  (never a probability)",
        "cannot_establish": [
            "arbitrary semantic properties — undecidable (Rice's theorem)",
            "any property outside the domains the abstraction is sound for",
        ],
    },
]

# Labels must never merge into one confidence number. They carry different warrants.
EVIDENCE_LABELS = {
    "verified_static":     "this edge exists in the analyzed source",
    "structural_evidence": "this decorator or base class is written here",
    "observed_runtime":    "this edge executed under a named workload",
    "proven_sound":        "this property holds on every execution",
    "unknown":             "the analysis refuses to decide",
}


# --------------------------------------------------------------------------- #
# stage runners — each DELEGATES; none decides
# --------------------------------------------------------------------------- #
def stage_preflight(repo_root):
    venvs = _unskippable_venvs(repo_root)
    return {
        "stage": "PREFLIGHT",
        "ok": not venvs,
        "venvs_found": [os.path.basename(v) for v in venvs],
        "note": ("A virtual environment inside the repository would cause Module 2 "
                 "to walk installed dependencies as source. Move it outside."
                 if venvs else "no virtual environment inside the repository"),
    }


def stage_m1(repo_root):
    summary, core, gate = _m1(repo_root)
    return {
        "stage": "M1",
        "output": summary,
        "gate": gate,
        "language_composition_populated": bool(getattr(core, "language_composition", {}) or {}),
    }, core


_KNOWN_LANG_TOKENS = {
    "python", "rust", "go", "golang", "java", "javascript", "typescript",
    "c", "c++", "cpp", "c#", "csharp", "ruby", "php", "kotlin", "swift",
    "scala", "perl", "r", "julia", "dart", "elixir", "haskell",
}


def _language_review(m1_framework, m2_language):
    """The corpus harness's neutral flag, surfaced here so it is visible per-run.

    It fires ONLY when Module 1's framework value is itself a bare language name.
    That makes it structurally blind to product-name frameworks:

        rust : framework 'Rust'  vs language 'javascript'  -> Yes  (caught)
        odoo : framework 'Odoo'  vs language 'sql'         -> No   (invisible)

    odoo was never caught by this flag. It was caught by the `guesses != 0`
    invariant misfiring on a `None` — and repairing that misfire removed the only
    mechanism that saw it. The flag is demonstrated at n=1, not n=2.

    Neither wrong-language bug shares a framework-string signature. Both share
    one this flag does not look at: the selected language's SHARE of classified
    files (odoo sql 0.53%, rust javascript 0.52%). That check does not exist.
    """
    fw = (m1_framework or "").strip().lower()
    lang = (m2_language or "").strip().lower()
    if not fw or not lang or fw in ("none", "unknown", "not detected"):
        return "No", "framework not comparable"
    if fw in _KNOWN_LANG_TOKENS and fw != lang and not (fw == "golang" and lang == "go"):
        return "Yes", f"M1 framework '{m1_framework}' names a language; M2 selected '{m2_language}'"
    if fw not in _KNOWN_LANG_TOKENS:
        return "No", (f"BLIND: framework '{m1_framework}' is not a language name. "
                      f"This flag cannot detect a wrong-language route here.")
    return "No", "framework and language agree"


def stage_route(core, repo_root, m1_framework=None):
    language, source, confidence, tally = detect_language_meta(core, repo_root)
    files = _files_for_language(repo_root, language)
    flag, why = _language_review(m1_framework, language)
    # `files_provided` is what classify_files() ROUTED here — not what the adapter
    # will parse. Adapters declare `file_extensions` broadly enough to reach the
    # metadata they need (GoAdapter claims `.mod` so it can read go.mod for the
    # module name), then filter that metadata out of their source list. On the Go
    # compiler: 11,294 routed, 23 of them `go.mod`, 11,271 parsed. Both numbers
    # are correct. They measure different things, and printing them adjacent
    # invites reading their difference as a loss.
    ext = sorted(getattr(get_adapter(language), "file_extensions", set()))
    return {
        "stage": "ROUTE",
        "language": language,
        "source": source,
        "confidence": confidence,
        "files_routed": len(files),
        "dominance_vote": ({lang: f"{v} votes ({u} translation units + {d} declarations)"
                            for lang, (v, u, d) in sorted(tally.items(), key=lambda kv: -kv[1][0])}
                           if tally else None),
        "files_routed_note": (f"classify_files() output for '{language}' "
                              f"(extensions {ext}). The adapter may filter this "
                              f"further; compare with M2 files_scanned only after "
                              f"accounting for non-source extensions."),
        "language_review_required": flag,
        "language_review_note": why,
        "warning": ("language selected by a low-confidence domain fallback; "
                    "file composition could not be determined"
                    if confidence == "low" else None),
    }, language, files


def stage_m2(repo_root, language, files):
    adapter = get_adapter(language)
    with _deep_recursion(20000):
        scan = adapter.scan(repo_root=repo_root, file_paths=files)
    summary = _m2_summary(scan, language, files_routed=len(files))
    out = {"stage": "M2", "adapter": type(adapter).__name__, "output": summary}

    # Deep Resolution breakdown, if the adapter emitted one. `_m2_summary` drops
    # it. Every resolver present is reported — not a hardcoded subset. A resolver
    # that ran and is not displayed is a resolver nobody will ever question.
    #
    # Absent fields are OMITTED, never defaulted to 0. A missing measurement is
    # not a zero — that conflation is what made `guesses: None` compare unequal
    # to 0 and fail three C++ repositories that had done nothing wrong.
    dr = (scan or {}).get("deep_resolution") or {}
    view = {}
    if dr:
        final = dr.get("final", {}) or {}
        for src, key in ((dr, "baseline_unresolved"),
                         (final, "resolved_by_pipeline"),
                         (final, "remaining_unresolved"),
                         (final, "reduction_pct")):
            if key in src:
                view[key] = src[key]
        rr = dr.get("resolver_results") or {}
        if rr:
            view["by_resolver"] = dict(rr)
        view["note"] = ("Deep Resolution is a Module 2 capability. Its counts are "
                        "resolutions computed, not necessarily net-new call-graph "
                        "edges. `reflection` returning 0 is correct by design — "
                        "dynamic getattr() is not statically resolvable.")

    # The C# adapter emits its own shape. Adapter outputs differ; read what is
    # there rather than assuming the Python shape.
    for key in ("dr_field_type", "overall_pct"):
        if key in (scan or {}):
            view[key] = scan[key]

    if view:
        out["deep_resolution"] = view
    return out, scan, summary


def _assert_guarantee_vocabulary(language, m3):
    """`guesses` is a Phase 3A/3B MEASUREMENT. Python's frozen engine computes it.
    No bridge engine does. A non-Python envelope claiming `guesses` would assert a
    guarantee that engine never produced — a fabrication, in the schema.

    This is INV_C_007's sibling, and it is the one fabrication this harness could
    otherwise print without noticing. Raises rather than reports: a fabricated
    guarantee is not a finding to display."""
    tb = (m3 or {}).get("truth_boundary", {}) or {}
    if language == "python":
        if "guesses" not in tb:
            raise AssertionError(
                "Python Module 3 emitted no guess count. The frozen engine must "
                "measure it; its absence means Phase 3A/3B did not complete.")
    else:
        if "guesses" in tb or "guesses" in (m3 or {}):
            raise AssertionError(
                f"'{language}' envelope claims `guesses` — a Phase 3A/3B "
                f"measurement its engine never performs. Fabricated guarantee.")
        if "edge_provenance" in (m3 or {}):
            raise AssertionError(
                f"'{language}' envelope claims `edge_provenance` — same class of "
                f"fabrication.")


def stage_m3(repo_root, language, scan, m1_summary):
    if language == "python":
        from v3.repository_reasoning.module3_pipeline import run_module3
        m3 = run_module3(repo_root, m2_scan=scan, m1_result=m1_summary)
        m3.pop("call_index", None)
        engine = "frozen module3_pipeline (Phase 3A/3B)"
    else:
        m3 = _module3_for_language(repo_root, language)
        engine = m3.get("engine") or "none"
    _assert_guarantee_vocabulary(language, m3)
    return {"stage": "M3", "engine": engine, "output": m3}


def stage_governance(language, m2_summary, m2_scan, m3_block):
    """The completeness guard, READ from the canonical rule. Both halves are
    imported. An earlier version of this function hand-rolled the Module 3 half —
    one router, two guards — in the same file whose docstring forbids it."""
    m2_artifacts = _has_primary_artifacts(language, m2_summary, m2_scan)
    # `_has_reasoning_artifacts` tests for the BRIDGE ENVELOPE's fields
    # (graph.functions_in_index / lineage). Python's frozen Module 3 emits
    # phase_3a / edge_provenance instead, so this is False for Python BY
    # CONSTRUCTION — even though Module 3 plainly ran. The old field name,
    # `m3_reasoning_artifacts`, read as "Module 3 produced nothing." It does not
    # test that. It tests whether a non-Python reasoning engine built an index.
    m3_envelope = _has_reasoning_artifacts(m3_block)
    return {
        "stage": "GOVERNANCE",
        "m2_primary_artifacts": m2_artifacts,
        "m3_envelope_artifacts": m3_envelope,
        "m3_envelope_note": ("False for Python by construction — the frozen engine "
                             "emits phase_3a/edge_provenance, not a bridge index. "
                             "Python's evidence is m2_primary_artifacts."
                             if language == "python" else None),
        "may_report_complete": bool(m2_artifacts or m3_envelope),
        "rule": ("COMPLETE requires primary artifacts appropriate to the language's "
                 "paradigm: functions/edges for code, objects/lineage for SQL, or a "
                 "Module 3 reasoning index."),
    }


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #
def _print_registry():
    print("=" * 78)
    print("MODULE PIPELINE — what each stage can and cannot establish")
    print("=" * 78)
    for m in MODULE_REGISTRY:
        print(f"\n[{m['id']}] {m['name']}  ({m['status']})")
        print(f"    reads : {m['reads']}")
        print(f"    emits : {m['emits']}")
        print("    CANNOT establish:")
        for lim in m["cannot_establish"]:
            print(f"        - {lim}")
    print("\n" + "-" * 78)
    print("Evidence labels never merge into a single confidence number:")
    for k, v in EVIDENCE_LABELS.items():
        print(f"    {k:20} {v}")
    print("-" * 78 + "\n")


# Fields that carry the guarantee. NEVER truncated, regardless of width.
# `truth_boundary` holds `guesses` — the whole contract. The previous printer
# collapsed any nested dict wider than 90 characters, which meant it displayed
# `by_label` (5 short keys) and hid `truth_boundary` (3 longer ones). A harness
# that cannot print `guesses: 0` is not verifying what the pipeline exists to
# guarantee. The truncation rule was arbitrary with respect to what matters.
_NEVER_COLLAPSE = {"truth_boundary", "edge_provenance", "by_label",
                   "by_resolver", "phase_3a", "phase_3b", "graph", "lineage"}


def _print_stage(s):
    print(f"\n-- {s['stage']} " + "-" * max(0, 72 - len(s["stage"])))
    for k, v in s.items():
        if k == "stage" or v is None:
            continue
        if isinstance(v, dict):
            print(f"   {k}:")
            for kk, vv in v.items():
                if kk == "by_resolver" and isinstance(vv, dict):
                    print(f"      {kk}:")
                    width = max((len(str(r)) for r in vv), default=0)
                    for resolver, count in sorted(vv.items()):
                        note = ("   (0 = correct by design; dynamic getattr() is "
                                "not statically resolvable)"
                                if resolver == "reflection" and count == 0 else "")
                        print(f"         {str(resolver):<{width}} : {count}{note}")
                elif kk in _NEVER_COLLAPSE and isinstance(vv, dict):
                    print(f"      {kk}:")
                    width = max((len(str(x)) for x in vv), default=0)
                    for key, val in vv.items():
                        print(f"         {str(key):<{width}} : {val}")
                elif isinstance(vv, (dict, list)) and len(str(vv)) > 90:
                    print(f"      {kk}: <{type(vv).__name__} len={len(vv)}>")
                else:
                    print(f"      {kk}: {vv}")
        else:
            print(f"   {k}: {v}")


def review(repo_root, force=False, as_json=False):
    """Run every stage, reporting each contribution and boundary."""
    stages = []

    pre = stage_preflight(repo_root)
    stages.append(pre)
    if not pre["ok"]:
        return _finish(stages, repo_root, as_json, halted_at="PREFLIGHT")

    s1, core = stage_m1(repo_root)
    stages.append(s1)
    if s1["gate"] != "APPROVED" and not force:
        stages.append({"stage": "HALT",
                       "reason": f"Module 1 governance gate: {s1['gate']}. "
                                 f"No findings generated. Re-run with --force to "
                                 f"proceed under explicit human override."})
        return _finish(stages, repo_root, as_json, halted_at="M1_GATE")

    sR, language, files = stage_route(core, repo_root,
                                      m1_framework=s1["output"].get("framework"))
    stages.append(sR)

    s2, scan, m2_summary = stage_m2(repo_root, language, files)
    stages.append(s2)

    s3 = stage_m3(repo_root, language, scan, s1["output"])
    stages.append(s3)

    sG = stage_governance(language, m2_summary, scan, s3["output"])
    stages.append(sG)

    if not sG["may_report_complete"]:
        stages.append({"stage": "HALT",
                       "reason": "Completeness guard: the selected engine produced no "
                                 "primary artifacts. Analysis is not COMPLETE and no "
                                 "findings are claimed."})
    return _finish(stages, repo_root, as_json)


def _finish(stages, repo_root, as_json, halted_at=None):
    if as_json:
        print(json.dumps({"repo": repo_root, "halted_at": halted_at,
                          "stages": stages, "registry": MODULE_REGISTRY},
                         indent=2, default=str))
    else:
        _print_registry()
        print("=" * 78)
        print(f"PIPELINE REVIEW - {repo_root}")
        print("=" * 78)
        for s in stages:
            _print_stage(s)
        print("\n" + "=" * 78)
        print("Every finding above is a VERIFIED IN-REPO FLOOR, not a complete set.")
        print("External, dynamic, decorator- and framework-invoked callers are")
        print("outside the verified graph and are flagged, never guessed.")
        print("=" * 78)
    return stages


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Review and verify the CodeTruth module pipeline, stage by stage.")
    ap.add_argument("repo", nargs="?", help="repository path to analyze")
    ap.add_argument("--force", action="store_true",
                    help="proceed past a REVIEW_REQUIRED governance gate")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--registry", action="store_true",
                    help="print the module registry and exit (no repository needed)")
    args = ap.parse_args(argv)

    if args.registry or not args.repo:
        _print_registry()
        if not args.repo:
            print("Pass a repository path to run the full stage review.\n")
        return 0

    if not os.path.isdir(args.repo):
        print(f"error: not a directory: {args.repo}", file=sys.stderr)
        return 2

    review(os.path.abspath(args.repo), force=args.force, as_json=args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
