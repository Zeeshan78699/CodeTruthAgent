"""Go caller-aware call graph on a known two-file same-package fixture.
Run from /home/claude: python test_go_call_graph.py"""
import os, tempfile, shutil
from v3.repository_reasoning import go_call_graph as G

FIX = tempfile.mkdtemp()
def w(rel, txt):
    p = os.path.join(FIX, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(txt)

w("service/svc.go",
  "package service\n\ntype Service struct { repo *Repo }\n\n"
  "func (s *Service) Run(id int) {\n\thelper(id)\n\tr := Repo{}\n\tr.Save(id)\n}\n\n"
  "func helper(id int) int {\n\treturn id\n}\n")
w("service/repo.go",
  "package service\n\ntype Repo struct {}\n\n"
  "func (r *Repo) Save(id int) {\n\thelper(id)\n}\n")

def run():
    r = G.analyze(FIX)
    es = set()
    for fp, edges in r["call_graph"].items():
        for e in edges: es.add((e["caller"], e["callee"]))
    expect = {
        ("service.Service.Run", "service.helper"),
        ("service.Service.Run", "service.Repo.Save"),
        ("service.Repo.Save", "service.helper"),
    }
    f = []
    if not expect.issubset(es):
        f.append(f"missing edges: {expect - es}")
    if ("service.helper", "service.helper") in es:
        f.append("false self-loop on helper (declaration counted as call)")
    shutil.rmtree(FIX, ignore_errors=True)
    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - Go: caller recovered; same-package (cross-file) func calls + "
          "typed-receiver method calls resolved; no false self-loop")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())
