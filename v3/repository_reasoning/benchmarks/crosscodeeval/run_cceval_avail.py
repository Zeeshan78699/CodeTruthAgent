
from v3.repository_reasoning.bench_against_crosscodeeval import load_examples
from v3.repository_reasoning.cceval_repo_fetch import availability_report
import collections, json

ex = load_examples(r"C:\repos\cceval\data\python\line_completion_rg1_unixcoder_cosine_sim.jsonl")
top = [r for r, _ in collections.Counter(e["repository"] for e in ex).most_common(20)]
rep = availability_report(top, clone_root=r"C:\repos\cceval_clones", method="clone")

print(json.dumps({k: v for k, v in rep.items() if k != "statuses"}, indent=2))
print("--- per-repo ---")
for s in rep["statuses"]:
    if s.get("commit_ok"):
        tag = "OK   "
    elif s.get("clone_ok"):
        tag = "clone"
    else:
        tag = "FAIL "
    print(f"  {tag}  {s['repo_field']}  ->  {s.get('owner')}/{s.get('name')}")
