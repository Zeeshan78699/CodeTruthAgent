"""
run_cceval_full.py — full CrossCodeEval cross-file re-measurement WITH the merged
local-receiver edges, across all exact-commit repos. Reports per-repo how many
local-receiver edges were added (so we see which repos the gap-closer actually
helps), plus the aggregate cross-file recall to compare against the 6.6% baseline.
"""
import os, sys, warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, "..", "..", "..", ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)
import json, collections
from v3.repository_reasoning.benchmarks.crosscodeeval.bench_against_crosscodeeval import load_examples
from v3.repository_reasoning.benchmarks.crosscodeeval.cceval_repo_fetch import availability_report
from v3.repository_reasoning.benchmarks.crosscodeeval.cceval_evaluate import (
    group_examples_by_repo, evaluate_set)
from v3.repository_reasoning.reasoning_engine import ReasoningEngine

DATA = r"C:\repos\cceval\data\python\line_completion_rg1_unixcoder_cosine_sim.jsonl"
CLONE_ROOT = r"C:\repos\cceval_clones"

# 1) load in-scope examples, group by repo
examples = load_examples(DATA)
print(f"in-scope method-call examples: {len(examples)}")
top = [r for r, _ in collections.Counter(e["repository"] for e in examples).most_common(20)]

# 2) availability (uses already-cloned repos; HEAD re-verified)
avail = availability_report(top, clone_root=CLONE_ROOT, method="clone")
statuses = avail["statuses"]
print(f"repos: total={avail['repos_total']} commit_ok={avail['commit_ok']} clone_ok={avail['clone_ok']}")

# 3) per-repo: how many local-receiver edges does the merge add? (the lift source)
print("\n--- local-receiver edges added per exact-commit repo ---")
by_repo = group_examples_by_repo(examples)
added_total = 0
for st in statuses:
    if not st.get("commit_ok"):
        continue
    repo_dir = st.get("path") or os.path.join(CLONE_ROOT, st["repo_field"])
    try:
        rep = ReasoningEngine(repo_dir).resolve()
        added = rep.get("edge_provenance", {}).get("local_receiver_added", 0)
        lc = rep.get("local_receiver_counts", {})
        added_total += added
        inh = lc.get("local_inherited_method_call", 0)
        typ = lc.get("local_typed_method_call", 0)
        flag = " <-- LIFT" if added > 0 else ""
        print(f"  {st['repo_field'][:40]:40}  added={added:4}  (inh={inh} typed={typ}){flag}")
    except Exception as e:
        print(f"  {st['repo_field'][:40]:40}  ERROR {type(e).__name__}")
print(f"\nTOTAL local-receiver edges added across exact-commit repos: {added_total}")

# 4) the actual cross-file recall WITH merge (evaluate_set runs Module 3 per repo)
print("\n--- CrossCodeEval cross-file recall (WITH merged edges) ---")
result = evaluate_set(by_repo, statuses, CLONE_ROOT, exact_only=True)
print(json.dumps({k: v for k, v in result.items() if k != "errors"}, indent=2))
if result.get("errors"):
    print("errors:", len(result["errors"]))
