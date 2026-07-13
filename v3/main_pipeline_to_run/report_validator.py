r"""
report_validator.py
CodeTruth Agent V3 — the projection validator for the Natural Language Layer.

PURPOSE
    Enforce D-01 mechanically. The renderer is a pure projection of the evidence
    JSON: no sentence may state a value the JSON does not hold. This module makes
    that checkable instead of promised.

WHAT IT CATCHES (the STRONG check, not a shape check)
    - Every NUMBER printed in the report must appear as a value somewhere in the
      source JSON (or be a structural number the schema produced: coverage counts,
      the M2/M3 provenance split). A "1,500" where the JSON says 1460 -> RAISES.
    - Every FORBIDDEN ADJECTIVE (medium-sized, well-structured, mature, robust,
      clean, etc.) -> RAISES. These are judgments no evidence field holds.
    - "approximately" / "roughly" / "~" applied to a number -> RAISES. Un-measuring
      an OBSERVED exact is a warrant violation.

WHAT IT ALLOWS
    - Fixed prose templates (the explanatory sentences, tier names, section
      descriptions) — these introduce no facts about the repository.
    - Structural numbers the generator itself produced (coverage X/Y, the
      provenance breakdown a+b=total).

THE TEST THAT PROVES IT WORKS
    validate("... the project is medium-sized ...", doc) MUST raise.
    validate("... 1,500 functions ...", doc_with_1460) MUST raise.
    validate(a_real_rendered_report, its_doc) MUST pass.
"""
from __future__ import annotations
import re


class ProjectionViolation(AssertionError):
    """Raised when a rendered report states something the evidence JSON does not."""


# Adjectives/labels that are judgments, not measurements. None of these can be
# sourced from an evidence field; their presence is drift by definition.
FORBIDDEN_ADJECTIVES = {
    "medium-sized", "small-sized", "large-sized", "medium sized",
    "well-structured", "well structured", "poorly-structured",
    "mature", "immature", "robust", "fragile", "clean", "messy",
    "high-quality", "low-quality", "well-organized", "well organized",
    "modern", "legacy", "elegant", "solid", "healthy", "sound-architecture",
    "production-ready", "enterprise-grade", "battle-tested",
    "reusable package",  # as a confident value — flask's app_type is UNKNOWN
}

# Hedges that un-measure an exact value.
FORBIDDEN_HEDGES = [
    r"\bapproximately\s+[\d,]+", r"\broughly\s+[\d,]+",
    r"~\s*[\d,]{2,}", r"\babout\s+[\d,]{3,}",
    r"\border of\b",
]


def _collect_json_numbers(obj, acc: set):
    """Every integer/float value anywhere in the JSON, as strings, with and
    without thousands separators."""
    if isinstance(obj, dict):
        for v in obj.values():
            _collect_json_numbers(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            _collect_json_numbers(v, acc)
    elif isinstance(obj, bool):
        return
    elif isinstance(obj, int):
        acc.add(str(obj))
        acc.add(f"{obj:,}")
    elif isinstance(obj, float):
        if obj.is_integer():
            acc.add(str(int(obj)))
            acc.add(f"{int(obj):,}")
        acc.add(str(obj))
        # percentages the generator may render (0.51 -> 51)
        acc.add(str(int(round(obj * 100))))
    elif isinstance(obj, str):
        # digit-runs embedded in strings: evidence paths ('app.py:59'), line
        # numbers, citations. A number the renderer prints that came verbatim from
        # a cited string is sourced by the evidence.
        import re as _re
        for run in _re.findall(r"\d+", obj):
            acc.add(run)


def _structural_numbers(doc: dict) -> set:
    """Numbers the generator legitimately produces that aren't stored verbatim as
    a single JSON value: coverage counts (X of Y), the provenance split, and
    _meta identifiers (commit SHA, hashes) which are structural, not repo facts."""
    s = set()
    # _meta is entirely structural: timestamps, schema version, commit, hashes.
    # None of it is a repository fact; exempt every digit-run and substring.
    import json as _json
    meta_blob = _json.dumps(doc.get("_meta", {}))
    for run in re.findall(r"\d+", meta_blob):
        s.add(run)
        for i in range(len(run)):
            for j in range(i + 2, len(run) + 1):
                s.add(run[i:j])
    # coverage: every section's populated/total, and grand totals. This MUST
    # mirror project_intelligence_report._coverage exactly, or the rendered total
    # won't be in the allowed set. Exclude documentation_drift (a findings block,
    # not a schema section) and count only tier-bearing dict fields.
    sections = [k for k in doc if not k.startswith("_") and k != "documentation_drift"]
    tot_pop = tot_all = 0
    for sec in sections:
        body = doc.get(sec, {})
        if not isinstance(body, dict):
            continue
        fields = [f for f in body
                  if not f.startswith("_") and isinstance(body.get(f), dict)
                  and "tier" in body[f]]
        pop = sum(1 for f in fields if body[f].get("tier") != "UNKNOWN")
        tot_pop += pop; tot_all += len(fields)
        s |= {str(pop), str(len(fields))}
    s |= {str(tot_pop), str(tot_all), f"{tot_all:,}", f"{tot_pop:,}"}
    # single-digit structural noise (section counts, list lengths)
    s |= {str(i) for i in range(0, 13)}
    return s


def validate(rendered: str, doc: dict, *, strict_numbers: bool = True) -> None:
    """Raise ProjectionViolation if `rendered` states anything `doc` doesn't hold.

    strict_numbers=True checks every multi-digit number against the JSON. Set
    False only for prose-heavy modes where you accept template-only checking.
    """
    low = rendered.lower()

    # For adjective/hedge checks, scan the renderer's OWN PROSE only — not the
    # evidence it quotes. A symbol named `clean` or a doc excerpt containing
    # "clean" is EVIDENCE the renderer is citing, not a judgment it is making.
    # Strip backtick-quoted spans (symbol names, citations) and italicized doc
    # excerpts before the adjective scan. (Same principle as exempting line
    # numbers inside cited paths: quoted evidence is sourced, not editorial.)
    prose = re.sub(r"`[^`]*`", " ", rendered)          # `symbol` spans
    prose = re.sub(r"\([^)]*:\d+[^)]*\)", " ", prose)   # (file:line) citations
    # drop finding-excerpt lines: bullets that quote doc text after an em dash
    prose_lines = []
    for ln in prose.split("\n"):
        # a drift finding line quotes evidence; skip its quoted tail
        if " - Docs " in ln or " - Code exposes " in ln or "Investigate:" in ln:
            continue
        prose_lines.append(ln)
    prose_low = "\n".join(prose_lines).lower()

    # 1. forbidden judgment adjectives — checked against PROSE, not evidence
    for adj in FORBIDDEN_ADJECTIVES:
        # match as a whole word to avoid 'clean' inside 'cleanup' etc.
        if re.search(r"(?<![a-z])" + re.escape(adj) + r"(?![a-z])", prose_low):
            raise ProjectionViolation(
                f"unsourced judgment '{adj}' in rendered report — no evidence "
                f"field holds this; renderer may not add adjectives")

    # 2. hedges that un-measure an exact
    for pat in FORBIDDEN_HEDGES:
        m = re.search(pat, prose_low)
        if m:
            raise ProjectionViolation(
                f"hedge '{m.group(0)}' un-measures an OBSERVED value — render the "
                f"exact number, not an approximation")

    # 3. every multi-digit number must trace to the JSON or be structural
    if strict_numbers:
        allowed = set()
        _collect_json_numbers(doc, allowed)
        allowed |= _structural_numbers(doc)
        # normalize: strip commas for comparison too
        allowed_bare = {a.replace(",", "") for a in allowed}
        # find numbers in the prose (>=2 digits to skip section headers like "1.")
        for tok in re.findall(r"\b\d[\d,]*\b", rendered):
            bare = tok.replace(",", "")
            if len(bare) < 2:
                continue
            if bare not in allowed_bare and tok not in allowed:
                raise ProjectionViolation(
                    f"number '{tok}' in rendered report does not appear in the "
                    f"evidence JSON — possible fabricated or rounded value")

    # 4. D3-015 doc-authority guardrail (structural check on the JSON, not prose)
    #    No field OUTSIDE the documentation / documentation_drift blocks may cite a
    #    documentation file as its evidence. If domain/application_type ever draws
    #    its warrant from a README line, that is the flask=WEB_APPLICATION bug
    #    reintroduced through the Documentation Auditor. Enforce the one-way
    #    authority rule mechanically: docs are the claim under test, never the
    #    evidence for a structural classification.
    _assert_doc_authority(doc)


# documentation-file evidence markers: an evidence path pointing at one of these
# is a documentation source, not code.
_DOC_EVIDENCE_RE = re.compile(
    r"(readme|changelog|changes|history|news|\.rst\b|docs?/|/adr/|\.md\b)", re.I)
# sections where citing a doc file IS legitimate.
_DOC_SECTIONS = {"documentation", "documentation_drift"}


def _assert_doc_authority(doc: dict) -> None:
    for section, body in doc.items():
        if section.startswith("_") or section in _DOC_SECTIONS:
            continue
        if not isinstance(body, dict):
            continue
        for field_name, field in body.items():
            if field_name.startswith("_") or not isinstance(field, dict):
                continue
            for ev in field.get("evidence", []) or []:
                path = str(ev.get("path", ""))
                # a bare "." or a code path is fine; a doc-file path is not
                if path in (".", "") or not _DOC_EVIDENCE_RE.search(path):
                    continue
                # allow .md/.rst ONLY if it's clearly a code file path? No — outside
                # the doc sections, a doc-file citation is forbidden, full stop.
                raise ProjectionViolation(
                    f"D3-015 authority violation: field "
                    f"'{section}/{field_name}' cites documentation evidence "
                    f"'{path}'. Documentation may be tested against code, never "
                    f"used as evidence for a structural field. Docs are claims, "
                    f"code is the arbiter.")


def assert_projection(rendered: str, doc: dict, **kw) -> str:
    """Convenience: validate then return the text, so callers can wrap render()."""
    validate(rendered, doc, **kw)
    return rendered


if __name__ == "__main__":
    # self-test: the three cases from the spec
    doc = {"architecture": {"functions": {"tier": "OBSERVED", "value": 1460}},
           "_meta": {}}
    ok = 0
    try:
        validate("the project is medium-sized", doc)
        print("FAIL: medium-sized did not raise")
    except ProjectionViolation:
        print("PASS: 'medium-sized' raised"); ok += 1
    try:
        validate("approximately 1,500 functions", doc)
        print("FAIL: approximately 1,500 did not raise")
    except ProjectionViolation:
        print("PASS: 'approximately 1,500' raised"); ok += 1
    try:
        validate("This project contains 1,460 functions.", doc)
        print("PASS: exact 1,460 passed"); ok += 1
    except ProjectionViolation as e:
        print("FAIL: exact value raised:", e)
    print(f"{ok}/3 self-tests passed")
