"""Data-layer test for the CrossCodeEval harness (no CodeTruth/real-data needed).
Run from /home/claude: python test_bench_crosscodeeval.py"""
import os, json, tempfile, io, ast
from v3.repository_reasoning import bench_against_crosscodeeval as B

RECS = [
  # in-scope, parseable
  {"prompt":"import x\ngenerator = ExLlamaAltGenerator(model)\nold_tail = decode(generator.",
   "groundtruth":"gen_begin(in_tokens)",
   "right_context":")\nreturn old_tail\n",
   "metadata":{"task_id":"t1","repository":"foo/bar","file":"example_ws.py","groundtruth_start_lineno":3},
   "crossfile_context":{"text":"# the below code fragment can be found in:\n# alt_generator.py\n#   def gen_begin(self,x): pass\n"}},
  # out-of-scope: attribute (no call)
  {"prompt":"old = decode(generator.","groundtruth":"sequence_actual[:, -m:])[0]",
   "right_context":"\n","metadata":{"file":"a.py","groundtruth_start_lineno":1}},
  # out-of-scope: not receiver.
  {"prompt":"x = helper(","groundtruth":"a, b)","right_context":"\n",
   "metadata":{"file":"b.py","groundtruth_start_lineno":1}},
]

def run():
    d = tempfile.mkdtemp(); p = os.path.join(d, "mini.jsonl")
    with io.open(p, "w", encoding="utf-8") as f:
        for r in RECS: f.write(json.dumps(r) + "\n")
    ex = B.load_examples(p)
    f = []
    if len(ex) != 1: f.append(f"filter: got {len(ex)} in-scope, expected 1")
    if ex:
        s = ex[0]
        if s["receiver"] != "generator": f.append(f"receiver={s['receiver']}")
        if s["method"] != "gen_begin": f.append(f"method={s['method']}")
        if s["crossfile_files"] != ["alt_generator.py"]: f.append(f"files={s['crossfile_files']}")
        if s["call_line"] != 3: f.append(f"call_line={s['call_line']}")
        try:
            ast.parse(s["_source"])
        except SyntaxError:
            f.append("reconstructed source should parse for this record")
        if "generator = ExLlamaAltGenerator(model)" not in s["_source"]:
            f.append("reconstruction missing the type-assignment")
    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - CrossCodeEval data layer: call-subset filter, site extraction "
          "(receiver/method/files/line), parseable reconstruction")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())