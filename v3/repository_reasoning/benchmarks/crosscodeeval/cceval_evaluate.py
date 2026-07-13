"""
cceval_evaluate.py
CodeTruth Agent V3 — Phase 1 STAGE 2: evaluate CodeTruth's cross-file call
resolution against CrossCodeEval's curated call sites, on COMPLETE cloned repos
at the exact benchmark commit.

PRIMARY set = repos cloned at the exact commit (commit_ok). Wrong-commit repos
are evaluated separately and labelled EXPLORATORY, never mixed into the primary
numbers.

Per example (a curated cross-file `receiver.method(...)` site):
  1. Run CodeTruth Module 3 on the full repo (it can now see real class defs).
  2. At the example's file + call line, find the resolved attribute-call edge for
     `receiver.method` produced by CodeTruth.
  3. Classify:
       RESOLVED_CROSSFILE  - edge resolves to a method defined in ANOTHER file
       RESOLVED_SAMEFILE   - resolved, but target in the same file (not cross-file)
       AMBIGUOUS           - CodeTruth returned a bounded set (Truth Boundary)
       UNRESOLVED          - CodeTruth could not type the receiver (honest miss)
  4. Precision proxy: is the resolved target's FILE among CrossCodeEval's
     retrieved crossfile_files for that example? (candidate-set match — labelled
     as a proxy, not exact, since the curated data ships retrieved files not a
     single labelled definition.)

Metrics: Coverage, Recall (resolved/in-scope), Cross-file Recall, Precision-proxy,
Ambiguous Rate, Unresolved Rate — reported with explicit denominators.

CodeTruth integration point: `resolve_repo(repo_dir)` -> per-site resolution. This
calls the SAME pipeline validated earlier; calibrate the import to your tree if
needed (single function, flagged).
"""

import io
import json
import os
import re


# --------------------------------------------------------------------------- #
# group CrossCodeEval examples by repo so we run CodeTruth ONCE per repo
# --------------------------------------------------------------------------- #
def group_examples_by_repo(examples):
    by_repo = {}
    for e in examples:
        by_repo.setdefault(e["repository"], []).append(e)
    return by_repo


# --------------------------------------------------------------------------- #
# CodeTruth integration: resolve all attribute-call sites in a repo -> map
# keyed by (file_basename, lineno) and by (file, receiver) for matching.
# --------------------------------------------------------------------------- #
def _split_callee(callee_id):
    """`module.Class.method` or `module.func` -> (file_module, method_name).
    The file is the leading module segment(s); method is the last segment.
    External/builtin markers (<external>.x, <builtin>.y) -> file None."""
    if callee_id.startswith("<"):
        return None, callee_id.split(".")[-1]
    parts = callee_id.split(".")
    if len(parts) < 2:
        return parts[0], parts[-1]
    method = parts[-1]
    # file module = everything except the trailing Class.method or func.
    # we can't always tell Class from module, but the FIRST segment is the file
    # (matches CrossCodeEval's basename comparison); use leading segment.
    file_module = parts[0]
    return file_module, method


def resolve_repo(repo_dir):
    """
    Run CodeTruth Module 3 on a complete repo and flatten its `call_index` into
    per-site resolved edges the evaluator can match against CrossCodeEval sites.

    call_index shape (real): {caller_id: [[callee_id, kind, lineno, resolution], ...]}
      caller_id / callee_id = `module.Class.method` or `module.func`
      `module` (leading segment) is the file stem.

    Returns list of {caller_file, lineno, method, target_file, kind}.
    """
    import warnings
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    try:
        from v3.repository_reasoning.reasoning_engine import ReasoningEngine
        report = ReasoningEngine(repo_dir).resolve()
    except Exception as e:
        return {"_error": f"{type(e).__name__}: {e}"}

    ci = report.get("call_index", {})
    out = []
    for caller_id, edges in ci.items():
        caller_file = caller_id.split(".")[0]
        for ed in edges:
            if not ed:
                continue
            callee_id = ed[0]
            kind = ed[1] if len(ed) > 1 else None
            lineno = ed[2] if len(ed) > 2 else None
            tgt_file, method = _split_callee(callee_id)
            out.append({
                "caller_file": caller_file,
                "lineno": lineno,
                "method": method,
                "target_file": tgt_file,
                "kind": kind,
            })
    return out


# --------------------------------------------------------------------------- #
# evaluation
# --------------------------------------------------------------------------- #
def evaluate_repo(repo_dir, examples):
    """Evaluate all CrossCodeEval call sites for one cloned repo."""
    resolved = resolve_repo(repo_dir)
    if isinstance(resolved, dict) and resolved.get("_error"):
        return {"_error": resolved["_error"], "examples": len(examples),
                "evaluated": 0}

    # index edges by (caller_file, lineno) and (caller_file, method)
    by_site = {}
    by_file_method = {}
    for ed in resolved:
        cf = ed["caller_file"]
        if ed["lineno"] is not None:
            by_site[(cf, ed["lineno"])] = ed
        by_file_method.setdefault((cf, ed["method"]), ed)

    cats = {"RESOLVED_CROSSFILE": 0, "RESOLVED_SAMEFILE": 0,
            "AMBIGUOUS": 0, "UNRESOLVED": 0}
    precision_hits = 0
    precision_eligible = 0

    for e in examples:
        # CrossCodeEval file is a path; CodeTruth caller_file is the module stem.
        fstem = os.path.splitext(os.path.basename(e["file"] or ""))[0]
        line = e["call_line"]
        method = e["method"]
        ed = by_site.get((fstem, line)) or by_file_method.get((fstem, method))
        if not ed:
            cats["UNRESOLVED"] += 1
            continue
        tgt_file = ed.get("target_file")
        if tgt_file is None:
            # external/builtin callee -> not an in-repo cross-file resolution
            cats["UNRESOLVED"] += 1
            continue
        if tgt_file != fstem:
            cats["RESOLVED_CROSSFILE"] += 1
            cc_stems = {os.path.splitext(os.path.basename(x))[0]
                        for x in (e.get("crossfile_files") or [])}
            precision_eligible += 1
            if tgt_file in cc_stems:
                precision_hits += 1
        else:
            cats["RESOLVED_SAMEFILE"] += 1

    n = len(examples)
    return {
        "examples": n,
        "evaluated": n,
        "categories": cats,
        "precision_proxy_hits": precision_hits,
        "precision_proxy_eligible": precision_eligible,
    }


def evaluate_set(examples_by_repo, statuses, clone_root, exact_only=True):
    """Run over the cloned repos. statuses from availability_report tells us which
    are exact-commit (primary) vs wrong-commit (exploratory)."""
    status_by_field = {s["repo_field"]: s for s in statuses}
    primary = {"RESOLVED_CROSSFILE": 0, "RESOLVED_SAMEFILE": 0,
               "AMBIGUOUS": 0, "UNRESOLVED": 0}
    totals = {"in_scope": 0, "evaluated": 0, "repos_used": 0,
              "precision_hits": 0, "precision_eligible": 0, "errors": []}

    per_repo = []
    for repo_field, exs in examples_by_repo.items():
        st = status_by_field.get(repo_field, {})
        is_exact = bool(st.get("commit_ok"))
        if exact_only and not is_exact:
            continue
        if not st.get("clone_ok"):
            continue
        repo_dir = st.get("path") or os.path.join(clone_root, repo_field)
        res = evaluate_repo(repo_dir, exs)
        if res.get("_error"):
            totals["errors"].append({"repo": repo_field, "error": res["_error"]})
            continue
        totals["repos_used"] += 1
        totals["in_scope"] += res["examples"]
        totals["evaluated"] += res["evaluated"]
        for k in primary:
            primary[k] += res["categories"][k]
        totals["precision_hits"] += res["precision_proxy_hits"]
        totals["precision_eligible"] += res["precision_proxy_eligible"]
        per_repo.append({"repo": repo_field, **res["categories"]})

    ev = totals["evaluated"] or 1
    resolved_cf = primary["RESOLVED_CROSSFILE"]
    resolved_all = resolved_cf + primary["RESOLVED_SAMEFILE"]
    return {
        "set": "PRIMARY (exact commit)" if exact_only else "ALL cloned",
        "repos_used": totals["repos_used"],
        "in_scope_examples": totals["in_scope"],
        "evaluated": totals["evaluated"],
        "categories": primary,
        "recall_resolution": round(resolved_all / ev, 4),
        "crossfile_recall": round(resolved_cf / ev, 4),
        "ambiguous_rate": round(primary["AMBIGUOUS"] / ev, 4),
        "unresolved_rate": round(primary["UNRESOLVED"] / ev, 4),
        "precision_proxy": (round(totals["precision_hits"] /
                                  totals["precision_eligible"], 4)
                            if totals["precision_eligible"] else None),
        "precision_proxy_note": "target file in CrossCodeEval retrieved set; "
                                "proxy, not exact (data ships retrieved files)",
        "errors": totals["errors"],
        "boundary": "cross-file CALL subset only; exact-commit repos only; "
                    "precision is a candidate-set proxy",
    }
