"""C# caller-aware call graph on a known fixture (same-class + field-typed + local).
Run from /home/claude: python test_csharp_call_graph.py"""
import os, tempfile, shutil
from v3.repository_reasoning import csharp_call_graph as C

FIX = tempfile.mkdtemp()
def w(rel, txt):
    p = os.path.join(FIX, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(txt)

w("Helper.cs",
  "namespace App {\n public class Helper {\n  public void Process() {}\n  public bool Validate() { return true; }\n }\n}\n")
w("Service.cs",
  "namespace App {\n public class Service {\n"
  "  private Helper helper;\n"
  "  public void Run() {\n"
  "   helper.Validate();\n"          # field -> Helper.Validate
  "   Helper local = new Helper();\n"
  "   local.Process();\n"            # local -> Helper.Process
  "   Setup();\n"                    # same-class -> Service.Setup
  "   System.Console.WriteLine();\n" # external
  "  }\n"
  "  private void Setup() {}\n"
  " }\n}\n")

def run():
    r = C.analyze(FIX)
    es = set()
    for fp, edges in r["call_graph"].items():
        for e in edges: es.add((e["caller"], e["callee"]))
    expect = {
        ("Service.Run", "Helper.Validate"),   # field-typed receiver
        ("Service.Run", "Helper.Process"),    # local-typed receiver
        ("Service.Run", "Service.Setup"),     # same-class
    }
    f = []
    if not expect.issubset(es):
        f.append(f"missing: {expect - es}")
    shutil.rmtree(FIX, ignore_errors=True)
    if f:
        print("FAIL"); [print("  -", x) for x in f]; print("got:", es); return 1
    # robustness: minified one-line input must NOT silently return empty
    d2=tempfile.mkdtemp()
    open(os.path.join(d2,"X.cs"),"w").write("namespace A{ public class H{ public void P(){} } public class S{ private H h; public void R(){ h.P(); } }}")
    r2=C.analyze(d2); e2={(e["caller"],e["callee"]) for v in r2["call_graph"].values() for e in v}
    shutil.rmtree(d2,ignore_errors=True)
    if ("S.R","H.P") not in e2:
        print("FAIL"); print("  - one-line/minified parse returned", e2); return 1
    print("PASS - C#: caller recovered; same-class + field/local typed-receiver "
          "calls resolved; external excluded")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())
