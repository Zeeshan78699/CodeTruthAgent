r"""
project_report_generator.py
CodeTruth Agent V3 — evidence-JSON generator for the Project Intelligence Report.

    Repository -> run_platform() -> THIS GENERATOR -> project_report/1.1.0 JSON
                                                          -> renderer -> prose

This is the ONLY place that reads the pipeline. It maps run_platform()'s output
onto the evidence schema, assigning each field a tier (OBSERVED / DERIVED /
INFERRED / UNKNOWN) with the correct warrant.

Two rules it must never break:

  D-01  It emits ONLY what the pipeline measured. Every field CodeTruth cannot
        populate today is emitted as UNKNOWN with a reason — never omitted, never
        defaulted to 0. Absence of a key is a schema violation.

  D-02  `guesses` and `super_resolutions` are Phase 3A/3B measurements the frozen
        PYTHON engine computes and no bridge engine does. For a non-Python repo
        they are UNKNOWN:PYTHON_ENGINE_ONLY — NEVER DERIVED:0. Emitting 0 there is
        the `_health` SOUND bug reborn in the report layer: a fabricated
        measurement standing in for an absent one.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone


# --------------------------------------------------------------------------- #
# tier constructors — every field is built through exactly one of these
# --------------------------------------------------------------------------- #
def OBSERVED(value, path, excerpt, sha="0" * 64):
    return {"tier": "OBSERVED", "value": value,
            "evidence": [{"path": path, "excerpt": excerpt, "sha256": sha}]}


def DERIVED(value, derivation, inputs):
    return {"tier": "DERIVED", "value": value,
            "derivation": derivation, "inputs": inputs}


def INFERRED(value, gate, evidence):
    return {"tier": "INFERRED", "value": value, "gate": gate, "evidence": evidence}


def UNKNOWN(reason, notes=None, partial=None):
    f = {"tier": "UNKNOWN", "reason": reason}
    if notes:
        f["notes"] = notes
    if partial:
        f["partial_evidence"] = partial
    return f


OUT = "OUT_OF_SCOPE_FOR_ANALYZER"
NOEV = "NO_EVIDENCE_FOUND"
CONFLICT = "EVIDENCE_CONFLICTING"
PYONLY = "PYTHON_ENGINE_ONLY"


def _all_unknown(keys, reason=OUT):
    return {k: UNKNOWN(reason) for k in keys}


# --------------------------------------------------------------------------- #
# the generator
# --------------------------------------------------------------------------- #
def build_report(rep: dict, pinned_commit: str = "0" * 40,
                 repo_root: str | None = None) -> dict:
    """rep = run_platform() output. Returns a project_report/1.1.0 document."""
    m1 = rep.get("module1", {}) or {}
    m2 = rep.get("module2", {}) or {}
    m3 = rep.get("module3", {}) or {}
    language = m2.get("language", "unknown")
    is_python = language == "python"
    tb = m3.get("truth_boundary", {}) or {}
    ep = m3.get("edge_provenance", {}) or {}

    doc = {}

    # ---- _meta ----------------------------------------------------------- #
    doc["_meta"] = {
        "schema_id": "https://codetruth.dev/schema/project_report/1.1.0",
        "schema_version": "1.1.0",
        "tier_semantics": {
            "OBSERVED": "Read directly from a file. evidence cites path and line.",
            "DERIVED": "Computed deterministically from OBSERVED facts by a named algorithm.",
            "INFERRED": "Proposed by pattern-matching or a model and passed a deterministic gate. NOT fact.",
            "UNKNOWN": "No evidence sufficient to emit a value. Terminal and first-class.",
        },
        "reader_contract": ("OBSERVED and DERIVED may be relied upon. INFERRED are "
                            "proposals with citations and MUST be audited. UNKNOWN is "
                            "terminal and MUST NOT be imputed. Absence of a key is a "
                            "schema violation, not an absence of the property."),
        "analyzer": {"name": "CodeTruth Agent", "version": "3.0.0-module3",
                     "modules_active": ["M1", "M2", "M3"]},
        "pinned_commit": pinned_commit,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    # ---- identity : entirely out of scope today -------------------------- #
    doc["identity"] = _all_unknown(
        ["name", "description", "version", "license_id", "license_files",
         "repository_url", "citation", "doi", "lifecycle_stage"])

    # ---- structure ------------------------------------------------------- #
    files_scanned = m2.get("files_scanned")
    files_routed = m2.get("files_routed")
    lang_val = {language: files_scanned} if files_scanned is not None else {language: files_routed}
    doc["structure"] = {
        "total_files": (OBSERVED(files_scanned, ".", "adapter files_scanned")
                        if files_scanned is not None
                        else UNKNOWN(NOEV, f"adapter emitted no scanned count; "
                                          f"{files_routed} routed (routed != scanned)")),
        "files_by_language": OBSERVED(lang_val, ".", "classify_files extension map"),
        "language_share": DERIVED({language: 1.0}, "language_share.normalize@3.0.0",
                                  ["/structure/files_by_language"]),
        "dominant_language": DERIVED(language,
                                     "detect_language_meta.bridge_classify_files@3.0.0",
                                     ["/structure/files_by_language"]),
        "lines_of_code": UNKNOWN(OUT),
        "generated_files": UNKNOWN(OUT),
        "vendored_paths": UNKNOWN(OUT),
        "duplicate_basenames": UNKNOWN(OUT),
        "test_files_by_name": UNKNOWN(OUT),  # requires a filename walk M1-3 don't do
    }

    # ---- supply_chain : out of scope ------------------------------------- #
    doc["supply_chain"] = _all_unknown(
        ["manifests", "lockfiles", "direct_dependencies", "transitive_count",
         "dependency_licenses", "license_conflicts", "pinned_versions",
         "sbom_present", "provenance_attestation"])

    # ---- architecture ---------------------------------------------------- #
    m2_functions = m2.get("functions", 0)
    classes = m2.get("classes", 0)
    edges_m2 = m2.get("call_graph_edges", 0)

    # Bridge languages (go/java/c_cpp/js/c#) route their real call graph through
    # Module 3's re-parse: Module 2's adapter emits 0 functions, and the true
    # count lives in module3.graph.functions_in_index. Reporting M2's 0 for a
    # 33,428-function Go compiler misrepresents a working analysis. Surface the
    # M3 index for bridge languages; Python's function count comes from M2.
    m3_graph = m3.get("graph", {}) or {}
    m3_index = m3_graph.get("functions_in_index")
    if not is_python and (m2_functions == 0) and (m3_index is not None):
        functions_field = DERIVED(m3_index,
            "module3.bridge_reparse.functions_in_index@3.0.0",
            ["/architecture (module3 re-parse index)"])
    else:
        functions_field = OBSERVED(m2_functions, "(repo)", "function_graph node count")

    # The true post-reasoning edge count is M2 edges + M3 local-receiver edges.
    # Use the reconciled total from edge_provenance when Python M3 computed it;
    # otherwise M2's count is all there is. Reporting the M2-only number while a
    # provenance line says "686 + 11 = 697" three lines down contradicts itself.
    edges_total = (ep.get("total_edges") if (is_python and ep and ep.get("total_edges") is not None)
                   else edges_m2)
    unresolved = m2.get("unresolved_calls", 0)

    arch = {
        "modules": UNKNOWN(OUT),  # module count is not in m2 summary; don't fabricate
        "functions": functions_field,
        "classes": OBSERVED(classes, "(repo)", "class_graph node count"),
        "call_graph_edges": DERIVED(edges_total,
                                    "module2.call_graph + module3.local_receiver@3.0.0",
                                    ["/architecture/functions", "/architecture/classes"]),
        "unresolved_calls": OBSERVED(unresolved, "(repo)",
                                     "receiver not statically determinable; each carries a reason"),
        "entry_points": UNKNOWN(NOEV,
                                "The verified call graph carries no decorator metadata. "
                                "Route decorators, console_scripts, and WSGI callables are invisible."),
        "layering_violations": UNKNOWN(NOEV,
                                       "No layering policy supplied; without a declared "
                                       "architecture no dependency is a violation."),
        "cyclic_clusters": UNKNOWN(OUT),  # only if the pipeline emits SCC; else honest UNKNOWN
    }

    # edge_provenance + guesses + super_resolutions: PYTHON-ONLY (D-02)
    if is_python and ep:
        arch["edge_provenance"] = DERIVED(
            {"module2_edges": ep.get("module2_edges"),
             "local_receiver_added": ep.get("local_receiver_added"),
             "total_edges": ep.get("total_edges")},
            "edge_provenance.reconcile@3.0.0", ["/architecture/call_graph_edges"])
    else:
        arch["edge_provenance"] = UNKNOWN(PYONLY,
            "edge provenance is a Python Phase-3A/3B measurement; "
            f"the {language} engine does not compute it")

    if is_python and "guesses" in tb:
        arch["guesses"] = DERIVED(tb.get("guesses", 0),
                                  "truth_boundary.guess_count@3.0.0",
                                  ["/architecture/call_graph_edges"])
    else:
        # D-02: NEVER DERIVED:0 for a non-Python engine.
        arch["guesses"] = UNKNOWN(PYONLY,
            "guess counting is a Python-engine measurement; "
            f"the {language} engine emits a declared truth boundary instead")

    lrc = m3.get("local_receiver_counts", {}) or {}
    if is_python and lrc:
        sr = lrc.get("local_inherited_method_call", 0) + lrc.get("super_call", 0)
        arch["super_resolutions"] = DERIVED(sr,
            "call_graph.c3_mro_super_resolution@3.0.0", ["/architecture/classes"])
    else:
        arch["super_resolutions"] = UNKNOWN(PYONLY,
            f"C3/super() resolution is Python-only; not computed for {language}")

    arch["dead_code_candidates"] = UNKNOWN(OUT)  # emitted only if the run computed it
    doc["architecture"] = arch

    # ---- runtime / quality / security / process / documentation --------- #
    doc["runtime"] = {
        **_all_unknown(["containerfiles", "compose_definitions", "iac_definitions",
                        "config_surface", "service_dependencies", "required_runtimes"]),
        "exposed_endpoints": UNKNOWN(NOEV,
                                     "Route decorators are tokens the call graph does not carry."),
    }
    doc["quality"] = _all_unknown(
        ["test_framework", "test_files_collected", "reported_coverage",
         "ci_definitions", "lint_configs", "type_checking", "pre_commit_hooks"])
    doc["security"] = {
        **_all_unknown(["hardcoded_secrets", "crypto_usage", "dangerous_sinks",
                        "taint_paths", "dependency_cves", "security_policy", "scorecard"]),
        "auth_surfaces": UNKNOWN(NOEV,
            "Authentication is decorator- and middleware-invoked — exactly the "
            "callers this analyzer cannot see. A low verified-caller count means "
            "'cannot see the callers', never 'few dependencies'."),
    }
    doc["process"] = _all_unknown(
        ["commit_count", "first_commit", "last_commit", "contributor_count",
         "bus_factor", "release_tags", "codeowners", "commit_convention",
         "contributing_guide"])
    # ---- documentation : D3-015 Documentation Auditor (Phase 1) ---------- #
    # If repo_root is available, run the three doc-audit engines to populate this
    # section with OBSERVED/DERIVED facts. Otherwise leave UNKNOWN (honest — we
    # cannot inventory docs we cannot read). The engines read ONLY the repo files;
    # their output enters ONLY this section. The validator's doc-authority
    # guardrail forbids any doc citation leaking into a structural field.
    doc["documentation"] = _all_unknown(
        ["readme_present", "readme_sections", "changelog_present", "adrs",
         "api_docs", "docstring_coverage", "docs_code_drift"])
    if repo_root:
        try:
            import docs_inventory, docstring_coverage, docs_drift
            doc["documentation"].update(docs_inventory.inventory(repo_root))
            doc["documentation"].update(
                docstring_coverage.measure(repo_root, language,
                                           m2_function_count=m2.get("functions")))
            _drift = docs_drift.audit(repo_root, language)
            if "docs_code_drift" in _drift:
                doc["documentation"]["docs_code_drift"] = _drift["docs_code_drift"]
            # the detailed drift block is its own top-level section for rendering
            if "documentation_drift" in _drift:
                doc["documentation_drift"] = _drift["documentation_drift"]
        except Exception as e:
            # a doc-audit failure must not fabricate — leave UNKNOWN, note why.
            doc["documentation"]["_audit_error"] = f"{type(e).__name__}: {e}"

    # ---- domain : the axis where Module 1's confidence is REJECTED -------- #
    app_type = m1.get("application_type", "UNKNOWN")
    arch_pattern = m1.get("architecture", "UNKNOWN")
    # M1 emits a confidence scalar; the schema rejects it. If role and structure
    # disagree, application_type is UNKNOWN:EVIDENCE_CONFLICTING, not a picked winner.
    role_is_app = app_type not in ("UNKNOWN", "LIBRARY", None)
    struct_is_lib = str(arch_pattern).upper() == "LIBRARY"
    if role_is_app and struct_is_lib:
        at_field = UNKNOWN(CONFLICT,
            f"Role axis proposes {app_type}; architecture axis observes LIBRARY. "
            "Module 1 cites no evidence references and carries a confidence scalar "
            "this schema rejects.")
    elif app_type in ("UNKNOWN", None):
        at_field = UNKNOWN(NOEV, "Module 1 did not classify an application type.")
    else:
        # single, non-conflicting signal — still INFERRED, never OBSERVED,
        # because M1's classification is a proposal, not a read fact.
        at_field = INFERRED(app_type, "module1.classifier (no evidence refs; audit)",
                            [{"path": "(module1)", "excerpt": f"application_type={app_type}"}])
    doc["domain"] = {
        "application_type": at_field,
        "architecture_pattern": (OBSERVED(arch_pattern, "(module1)", "architecture pattern")
                                 if str(arch_pattern).upper() != "UNKNOWN"
                                 else UNKNOWN(NOEV, "Module 1 abstained on architecture pattern.")),
        "target_user": UNKNOWN(OUT),
        "vertical": UNKNOWN(OUT),
        "maturity": UNKNOWN(OUT),
    }

    # ---- determinism hash (excludes volatile fields) --------------------- #
    clone = json.loads(json.dumps(doc))
    clone["_meta"].pop("generated_at", None)
    payload = json.dumps(clone, sort_keys=True, separators=(",", ":")).encode()
    doc["_meta"]["determinism"] = {
        "reproducible": True,
        "hash_excludes": ["/_meta/generated_at", "/_meta/determinism/report_sha256"],
        "report_sha256": hashlib.sha256(payload).hexdigest(),
    }
    return doc


def generate_for_repo(repo_root: str, pinned_commit: str = "0" * 40) -> dict:
    """Run the pipeline and build the evidence report. Requires v3 on sys.path."""
    from v3.run_codetruth import run_platform
    rep = run_platform(repo_root)
    return build_report(rep, pinned_commit, repo_root=repo_root)


if __name__ == "__main__":
    import sys
    print(json.dumps(generate_for_repo(sys.argv[1]), indent=2))
