"""Java 3A on multi-file fixtures with KNOWN cross-file type resolution.
Run from /home/claude: python test_java_type_inference.py"""
import sys, os, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import java_type_inference as J

FIX = tempfile.mkdtemp()
def w(rel, txt):
    p = os.path.join(FIX, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(txt)

w("com/example/util/Helper.java",
  "package com.example.util;\npublic class Helper {\n public void process(){}\n public boolean validate(){return true;}\n}\n")
w("com/example/Thing.java",
  "package com.example;\npublic class Thing { public void go(){} }\n")
w("com/example/Service.java",
  "package com.example;\nimport com.example.util.Helper;\n"
  "public class Service {\n private Helper helper;\n"
  " public void run(Thing t){\n"
  "  Helper local = new Helper();\n"
  "  local.process();\n"        # local -> Helper.process (cross-file)
  "  helper.validate();\n"      # field -> Helper.validate (cross-file)
  "  t.go();\n"                 # param -> Thing.go (same-pkg)
  "  var x = makeThing();\n"
  "  x.go();\n"                 # var->Thing.go (return-type infer)
  " }\n private Thing makeThing(){ return new Thing(); }\n}\n")

def run():
    r = J.analyze(FIX)
    edges = {(e["caller"].split(".")[-1], e["callee"]) for e in r["new_resolved_edges"]}
    expect = {
        ("run", "com.example.util.Helper.Helper.process"),
        ("run", "com.example.util.Helper.Helper.validate"),
        ("run", "com.example.Thing.Thing.go"),
    }
    f = []
    if not expect.issubset(edges):
        f.append(f"missing cross-file edges: {expect - edges}")
    if r["counts"]["RESOLVED"] != 4:
        f.append(f"RESOLVED={r['counts']['RESOLVED']} != 4 (3 fields/param + 1 var-from-return)")
    if r["files_parsed"] != 3:
        f.append(f"files_parsed={r['files_parsed']} != 3")
    shutil.rmtree(FIX, ignore_errors=True)
    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - Java 3A: field/param/local + var-from-return receivers type-"
          "resolved across files (4 RESOLVED, incl. 2 cross-file)")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())
