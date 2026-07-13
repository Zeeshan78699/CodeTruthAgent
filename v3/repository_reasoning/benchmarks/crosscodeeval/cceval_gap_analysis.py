"""
cceval_gap_analysis.py — classify the 324 UNRESOLVED CrossCodeEval cross-file
call sites by ROOT CAUSE, so the next deterministic improvement is evidence-led,
not blind. For each in-scope example CodeTruth did NOT resolve, categorize the
receiver shape at the call site.

Buckets:
  self_or_cls          - receiver is self/cls (should resolve; if here = real miss)
  local_var_untyped    - receiver is a local var we couldn't type (constructor/return gap)
  param_untyped        - receiver is a function parameter (no annotation -> the param wall)
  imported_name        - receiver is an imported symbol (alias/re-export gap)
  call_result          - receiver is itself a call f(...).method() (return-type chain gap)
  attribute_chain      - receiver is a.b.c (nested attribute; multi-hop typing)
  subscript_or_other   - receiver is x[i].m() etc (container element typing)
  unparseable          - the reconstructed/real file didn't parse (data limit)
  not_found_in_index   - site not present in CodeTruth's edges at all
"""
import os, sys, warnings, ast, collections
warnings.filterwarnings("ignore", category=SyntaxWarning)
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)
import json
from v3.repository_reasoning.benchmarks.crosscodeeval.bench_against_crosscodeeval import load_examples
from v3.repository_reasoning.benchmarks.crosscodeeval.cceval_repo_fetch import availability_report
from v3.repository_reasoning.benchmarks.crosscodeeval.cceval_evaluate import (
    group_examples_by_repo, resolve_repo)

DATA = r"C:\repos\cceval\data\python\line_completion_rg1_unixcoder_cosine_sim.jsonl"
CLONE_ROOT = r"C:\repos\cceval_clones"


def classify_receiver(source_line):
    """Given the prompt's last line ending in `receiver.`, classify the receiver
    expression shape. We re-parse the receiver text heuristically."""
    # strip trailing `.` and whitespace, take the receiver expression
    txt = source_line.rstrip()
    if not txt.endswith("."):
        return "other"
    expr = txt[:-1].strip()
    # take the rightmost receiver token/expression
    # try parsing as a Python expression
    try:
        node = ast.parse(expr, mode="eval").body
    except Exception:
        # fallback: simple name?
        tok = expr.split()[-1] if expr.split() else expr
        if tok.isidentifier():
            return "bare_name"
        return "unparseable_recv"
    # walk the outermost node
    if isinstance(node, ast.Name):
        if node.id in ("self", "cls"):
            return "self_or_cls"
        return "bare_name"          # local/param/global/import - refine below
    if isinstance(node, ast.Call):
        return "call_result"
    if isinstance(node, ast.Attribute):
        return "attribute_chain"
    if isinstance(node, ast.Subscript):
        return "subscript_or_other"
    return "other"


def refine_bare_name(recv, source, ):
    """For a bare-name receiver, is it a param, a local assignment, an import, or
    a global? Parse the reconstructed source and look for how recv is bound."""
    try:
        tree = ast.parse(source)
    except Exception:
        return "local_var_untyped"  # can't tell; default to local
    is_param = is_local_assign = is_import = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for a in list(node.args.args) + list(node.args.posonlyargs) + list(node.args.kwonlyargs):
                if a.arg == recv:
                    is_param = True
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == recv:
                    is_local_assign = True
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for n in node.names:
                if (n.asname or n.name.split(".")[0]) == recv:
                    is_import = True
    if is_import:
        return "imported_name"
    if is_param:
        return "param_untyped"
    if is_local_assign:
        return "local_var_untyped"
    return "global_or_unknown"


def run():
    examples = load_examples(DATA)
    top = [r for r, _ in collections.Counter(e["repository"] for e in examples).most_common(20)]
    avail = availability_report(top, clone_root=CLONE_ROOT, method="clone")
    statuses = {s["repo_field"]: s for s in avail["statuses"]}
    by_repo = group_examples_by_repo(examples)

    buckets = collections.Counter()
    total_unresolved = 0
    examples_checked = 0

    for repo_field, exs in by_repo.items():
        st = statuses.get(repo_field, {})
        if not st.get("commit_ok"):
            continue
        repo_dir = st.get("path") or os.path.join(CLONE_ROOT, repo_field)
        resolved = resolve_repo(repo_dir)
        if isinstance(resolved, dict) and resolved.get("_error"):
            continue
        by_site = {}
        by_fm = {}
        for ed in resolved:
            if ed["lineno"] is not None:
                by_site[(ed["caller_file"], ed["lineno"])] = ed
            by_fm.setdefault((ed["caller_file"], ed["method"]), ed)

        for e in exs:
            examples_checked += 1
            fstem = os.path.splitext(os.path.basename(e["file"] or ""))[0]
            ed = by_site.get((fstem, e["call_line"])) or by_fm.get((fstem, e["method"]))
            # unresolved if: no edge, or edge target is external/None
            is_unres = (not ed) or (ed.get("target_file") is None) or (ed.get("target_file") == fstem)
            if not is_unres:
                continue
            total_unresolved += 1
            src = e.get("_source", "")
            last_line = src.splitlines()[-1] if "\n" in src[:1] else ""
            # the receiver line is the prompt's last line; reconstruct it
            # _source = prompt+gt+right; the call site line is where receiver. sits
            # use the stored receiver name directly
            recv = e.get("receiver", "")
            # classify by receiver name binding in the source
            cat = refine_bare_name(recv, src)
            if recv in ("self", "cls"):
                cat = "self_or_cls"
            buckets[cat] += 1

    print(f"examples checked: {examples_checked}")
    print(f"total unresolved classified: {total_unresolved}\n")
    print("ROOT-CAUSE BREAKDOWN of unresolved cross-file calls:")
    for cat, n in buckets.most_common():
        pct = 100.0 * n / max(1, total_unresolved)
        print(f"  {cat:22} {n:4}  ({pct:4.1f}%)")
    print("\nINTERPRETATION:")
    print("  param_untyped / global_or_unknown -> untyped-receiver wall (structural)")
    print("  local_var_untyped                 -> constructor/return typing (deterministic-improvable)")
    print("  imported_name                     -> alias/re-export resolution")
    print("  call_result / attribute_chain     -> return-type chain (multi-hop)")
    print("  self_or_cls                       -> should already resolve (real miss to investigate)")


if __name__ == "__main__":
    run()
