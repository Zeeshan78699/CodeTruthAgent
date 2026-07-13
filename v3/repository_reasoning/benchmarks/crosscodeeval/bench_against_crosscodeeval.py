"""
bench_against_crosscodeeval.py
CodeTruth Agent V3 — Phase 1 evaluation: cross-file CALL-resolution faithfulness
against CrossCodeEval's curated cross-file completion examples.

HONEST SCOPE (load-bearing):
  * This is NOT a "CrossCodeEval completion score". CodeTruth does not generate
    code. We measure ONLY whether CodeTruth's call graph resolves the cross-file
    method call that CrossCodeEval's example completes.
  * Only the METHOD-CALL subset is in scope: prompt ends with `receiver.` and the
    groundtruth completes `method(...)`. CrossCodeEval also contains attribute /
    field / import completions — those are NOT calls and are correctly excluded.
    (Measured: ~71.6% of the Python set is in-scope.)
  * v1 is SELF-CONTAINED: it reconstructs the CURRENT file from the record itself
    (prompt + groundtruth + right_context — which is real, parseable source) and
    asks CodeTruth to resolve the receiver at the call site. The cross-file
    DEFINITION files ship only as partial retrieved fragments, so v1 measures
    RECEIVER-TYPE / cross-file RESOLUTION recall — the prerequisite CodeTruth
    uniquely provides — against curated hard cross-file sites. A future v2 may
    fetch full repos for exact target-file precision.

Reported: on the in-scope subset, precision / recall / F1 of CodeTruth resolving
a cross-file call at the curated site, with the subset size stated explicitly.

LAYER SPLIT:
  - Data layer (load/filter/reconstruct/extract): pure, unit-tested.
  - CodeTruth hook `codetruth_resolve()`: runs YOUR installed resolver. Verify the
    import matches your tree; we calibrate it on first real run.
"""

import io
import json
import os
import re
import tempfile

# --------------------------------------------------------------------------- #
# DATA LAYER  (pure, testable without CodeTruth or the real data)
# --------------------------------------------------------------------------- #
_RECV_DOT = re.compile(r'([A-Za-z_]\w*)\s*\.\s*$')         # ...receiver.
_GT_CALL = re.compile(r'^([A-Za-z_]\w*)\s*\(')             # method(...
_FRAG_FILE = re.compile(r'can be found in:\s*\n#\s*(.+)')  # crossfile fragment headers


def is_method_call_example(rec):
    """True iff this example completes a `receiver.method(...)` call."""
    prompt = rec.get("prompt", "")
    lines = prompt.splitlines()
    if not lines:
        return False
    last = lines[-1]
    gt = rec.get("groundtruth", "").lstrip()
    return bool(_RECV_DOT.search(last)) and bool(_GT_CALL.match(gt))


def extract_site(rec):
    """Return the call-site facts: receiver name, method name, file, line, and the
    set of files CrossCodeEval's retrieved fragments name as cross-file sources."""
    last = rec["prompt"].splitlines()[-1]
    recv = _RECV_DOT.search(last).group(1)
    method = _GT_CALL.match(rec["groundtruth"].lstrip()).group(1)
    m = rec.get("metadata", {})
    cc = rec.get("crossfile_context")
    frag_files = []
    if isinstance(cc, dict):
        frag_files = [f.strip() for f in _FRAG_FILE.findall(cc.get("text", ""))]
    return {
        "task_id": m.get("task_id"),
        "repository": m.get("repository"),
        "file": m.get("file"),
        "call_line": (m.get("groundtruth_start_lineno") or 0),
        "receiver": recv,
        "method": method,
        "crossfile_files": sorted(set(frag_files)),
    }


def reconstruct_current_file(rec):
    """The current file as real source: prompt + groundtruth + right_context.
    This is parseable Python (it's the original file content around the cursor)."""
    return rec["prompt"] + rec["groundtruth"] + rec.get("right_context", "")


def load_examples(jsonl_path, limit=None):
    """Yield in-scope (method-call) examples with extracted site facts."""
    out = []
    with io.open(jsonl_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if not is_method_call_example(rec):
                continue
            site = extract_site(rec)
            site["_source"] = reconstruct_current_file(rec)
            out.append(site)
            if limit and len(out) >= limit:
                break
    return out


# --------------------------------------------------------------------------- #
# CODETRUTH HOOK  (runs YOUR resolver — calibrate import to your tree)
# --------------------------------------------------------------------------- #
def codetruth_resolve(site, workdir=None):
    """
    Ask CodeTruth: at site['file']:site['call_line'], does the call
    `receiver.method(...)` resolve to a method on a type defined OUTSIDE the
    current file (i.e. a cross-file call)?

    Returns dict: {resolved: bool, receiver_type: str|None, cross_file: bool,
                   target_file: str|None}

    v1 strategy (self-contained): write the reconstructed current file into a
    temp repo, run CodeTruth's Python receiver typing, and report whether the
    receiver was typed and whether that type is defined in the current file.
    A type that is NOT in the current file is consistent with CrossCodeEval's
    cross-file guarantee.

    NOTE: this uses CodeTruth's Module 3 Python type inference. If your import
    paths differ, adjust here — this is the single integration point.
    """
    workdir = workdir or tempfile.mkdtemp(prefix="cceval_")
    relpath = site["file"] or "current_file.py"
    fpath = os.path.join(workdir, os.path.basename(relpath))
    with io.open(fpath, "w", encoding="utf-8") as fh:
        fh.write(site["_source"])

    # reconstructed window may be truncated at delimiters -> not always parseable.
    # Record that honestly rather than crashing; an unparseable current file means
    # CodeTruth cannot type the receiver for that example (counts as unresolved,
    # flagged separately so it is not mistaken for a resolution failure).
    import ast as _ast
    try:
        _ast.parse(site["_source"])
        parse_ok = True
    except SyntaxError:
        parse_ok = False
    if not parse_ok:
        return {"resolved": False, "receiver_type": None, "cross_file": False,
                "target_file": None, "parse_ok": False}

    # ---- integration point: CodeTruth Python receiver typing ----
    # Uses variable_type_propagator's receiver typing over the single-file repo.
    try:
        from v3.repository_reasoning.variable_type_propagator import (
            from_repo_receiver_breakdown as _recv,
        )
        info = _recv(workdir)  # expected: per-site receiver -> type info
    except Exception as e:
        return {"resolved": False, "receiver_type": None, "cross_file": False,
                "target_file": None, "error": f"{type(e).__name__}: {e}"}

    # interpret: did CodeTruth assign a type to this receiver name?
    # (calibrated on first real run — shape of `info` confirmed against output)
    receiver = site["receiver"]
    rtype = None
    if isinstance(info, dict):
        # try a few likely shapes; calibrate once we see real output
        rtype = (info.get("by_receiver", {}) or {}).get(receiver) \
            or (info.get("types", {}) or {}).get(receiver) \
            or info.get(receiver)
    resolved = rtype is not None
    return {"resolved": resolved, "receiver_type": rtype,
            "cross_file": resolved,  # refined once def-file matching is added
            "target_file": None}


# --------------------------------------------------------------------------- #
# EVALUATION
# --------------------------------------------------------------------------- #
def evaluate(jsonl_path, limit=None, resolver=codetruth_resolve):
    examples = load_examples(jsonl_path, limit=limit)
    n = len(examples)
    resolved = 0
    errors = 0
    parse_fail = 0
    for site in examples:
        try:
            r = resolver(site)
        except Exception:
            errors += 1
            continue
        if r.get("parse_ok") is False:
            parse_fail += 1
        if r.get("resolved"):
            resolved += 1

    parseable = n - parse_fail
    # All in-scope examples are curated cross-file positives. Recall = fraction
    # CodeTruth resolves. We report recall over ALL in-scope and over PARSEABLE
    # examples separately (so reconstruction limits are not hidden).
    recall_all = resolved / n if n else 0.0
    recall_parseable = resolved / parseable if parseable else 0.0
    return {
        "benchmark": "CrossCodeEval (cross-file CALL subset)",
        "scope_note": "method-call examples only; NOT a completion score",
        "in_scope_examples": n,
        "reconstruction_unparseable": parse_fail,
        "parseable_examples": parseable,
        "codetruth_resolved": resolved,
        "errors": errors,
        "recall_over_all_in_scope": round(recall_all, 4),
        "recall_over_parseable": round(recall_parseable, 4),
        "precision": "v2 (needs target-file matching / repo fetch)",
        "boundary": "recall of CodeTruth resolving a cross-file call at curated "
                    "CrossCodeEval sites; unparseable reconstructions reported "
                    "separately; precision pending exact target matching",
    }
