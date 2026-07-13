"""SQL lineage on a known fixture with a transitive data flow.
Run from /home/claude (or as module once placed in tests/)."""
import os, tempfile, shutil
try:
    from v3.repository_reasoning import sql_lineage as S
except Exception:
    import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import sql_lineage as S

FIX = tempfile.mkdtemp()
def w(rel, txt):
    p = os.path.join(FIX, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(txt)

# raw -> (load_staging) -> staging -> (build_report) -> report
w("schema.sql",
  "CREATE TABLE raw (id INT);\nCREATE TABLE staging (id INT);\nCREATE TABLE report (id INT);\n")
w("procs.sql",
  "CREATE PROCEDURE load_staging AS\nBEGIN\n  INSERT INTO staging SELECT * FROM raw;\nEND;\n\n"
  "CREATE PROCEDURE build_report AS\nBEGIN\n  INSERT INTO report SELECT * FROM staging;\nEND;\n")

def run():
    m = S.analyze(FIX)
    f = []
    # writers/readers
    if S.writers_of("staging", m)["writers"] != ["load_staging"]:
        f.append(f"writers_of staging = {S.writers_of('staging', m)['writers']}")
    if S.readers_of("staging", m)["readers"] != ["build_report"]:
        f.append(f"readers_of staging = {S.readers_of('staging', m)['readers']}")
    # direct flows: raw->staging (load_staging), staging->report (build_report)
    flows = {(a, b) for a, o, b in m["data_flows"]}
    if ("raw", "staging") not in flows or ("staging", "report") not in flows:
        f.append(f"data_flows = {flows}")
    # transitive: report's upstream includes raw (raw->staging->report)
    up = S.upstream_of("report", m)["upstream_tables"]
    if "raw" not in up or "staging" not in up:
        f.append(f"upstream_of report = {up}")
    # impact: changing raw reaches staging AND report downstream
    down = S.impact_of_table("raw", m)["downstream_tables"]
    if "staging" not in down or "report" not in down:
        f.append(f"impact_of raw = {down}")
    shutil.rmtree(FIX, ignore_errors=True)
    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - SQL lineage: writers/readers attributed to owning procedure; "
          "transitive raw->staging->report upstream + downstream lineage exact")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())
