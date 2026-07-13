"""
cceval_gap_refine.py — refine the 219 imported_name unresolved cases: split into
  imported_INREPO   - imported from another file IN the repo (deterministically solvable)
  imported_EXTERNAL - imported from a third-party/stdlib package (correctly unresolved)
Also surface the 21 self_or_cls misses (should already resolve -> possible bug).
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


def import_origin(recv, source, repo_dir, repo_field):
    """For an imported receiver, determine if it's imported from IN-REPO or EXTERNAL.
    Look at the import statement; check if the module resolves to a repo file."""
    try:
        tree = ast.parse(source)
    except Exception:
        return "imported_unknown"
    mod = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for n in node.names:
                if (n.asname or n.name) == recv:
                    mod = node.module or ""
        if isinstance(node, ast.Import):
            for n in node.names:
                if (n.asname or n.name.split(".")[0]) == recv:
                    mod = n.name
    if mod is None:
        return "imported_unknown"
    # relative import (from . / from ..) -> definitely in-repo
    # check if first segment matches a top-level dir/file in the repo
    top = mod.split(".")[0]
    if mod.startswith(".") or top == "":
        return "imported_INREPO"
    # does <repo>/<top>.py or <repo>/<top>/ exist?
    try:
        for dirpath, dirnames, filenames in os.walk(repo_dir):
            depth = dirpath[len(repo_dir):].count(os.sep)
            if depth > 2:
                dirnames[:] = []
                continue
            if f"{top}.py" in filenames or top in dirnames:
                return "imported_INREPO"
    except Exception:
        pass
    return "imported_EXTERNAL"


def run():
    examples = load_examples(DATA)
    top = [r for r, _ in collections.Counter(e["repository"] for e in examples).most_common(20)]
    avail = availability_report(top, clone_root=CLONE_ROOT, method="clone")
    statuses = {s["repo_field"]: s for s in avail["statuses"]}
    by_repo = group_examples_by_repo(examples)

    buckets = collections.Counter()
    self_miss_examples = []

    for repo_field, exs in by_repo.items():
        st = statuses.get(repo_field, {})
        if not st.get("commit_ok"):
            continue
        repo_dir = st.get("path") or os.path.join(CLONE_ROOT, repo_field)
        resolved = resolve_repo(repo_dir)
        if isinstance(resolved, dict) and resolved.get("_error"):
            continue
        by_site = {}; by_fm = {}
        for ed in resolved:
            if ed["lineno"] is not None:
                by_site[(ed["caller_file"], ed["lineno"])] = ed
            by_fm.setdefault((ed["caller_file"], ed["method"]), ed)

        for e in exs:
            fstem = os.path.splitext(os.path.basename(e["file"] or ""))[0]
            ed = by_site.get((fstem, e["call_line"])) or by_fm.get((fstem, e["method"]))
            is_unres = (not ed) or (ed.get("target_file") is None) or (ed.get("target_file") == fstem)
            if not is_unres:
                continue
            recv = e.get("receiver", "")
            src = e.get("_source", "")
            if recv in ("self", "cls"):
                buckets["self_or_cls_MISS"] += 1
                if len(self_miss_examples) < 5:
                    self_miss_examples.append((repo_field, e.get("method"), e.get("call_line")))
                continue
            # is it imported?
            try:
                tree = ast.parse(src); imported = False
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        for n in node.names:
                            if (n.asname or n.name.split(".")[0]) == recv:
                                imported = True
                if imported:
                    buckets[import_origin(recv, src, repo_dir, repo_field)] += 1
                else:
                    buckets["non_import_receiver"] += 1
            except Exception:
                buckets["parse_error"] += 1

    total = sum(buckets.values())
    print(f"total unresolved re-classified: {total}\n")
    print("REFINED BREAKDOWN:")
    for cat, n in buckets.most_common():
        print(f"  {cat:22} {n:4}  ({100.0*n/max(1,total):4.1f}%)")
    print("\nKEY QUESTION: imported_INREPO = deterministically solvable (build an")
    print("imported-receiver emitter). imported_EXTERNAL = correctly unresolved")
    print("(Truth Boundary - callee not in repo).")
    if self_miss_examples:
        print("\nself/cls MISSES (should resolve - investigate):")
        for r, m, l in self_miss_examples:
            print(f"   {r[:30]} method={m} line={l}")


if __name__ == "__main__":
    run()
