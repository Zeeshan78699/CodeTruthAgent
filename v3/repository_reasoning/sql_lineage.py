"""
sql_lineage.py
CodeTruth Agent V3 — Module 3 for SQL. A SEPARATE paradigm: not a call graph,
but DATA LINEAGE — which procedures/views read or write which tables, and how
data flows table -> (procedure) -> table.

The SQL Module 2 adapter records table references and their ref_type
(SELECT/JOIN/INSERT/UPDATE/DELETE) but not the enclosing object that makes the
reference. Like the C#/Go caller problem, lineage needs the *container*: which
CREATE PROCEDURE / VIEW / TRIGGER body a reference sits in. This module re-parses
SQL (adapter untouched) to attribute every read/write to its owning object, then
answers lineage questions deterministically.

Model:
  objects : procedures, views, functions, triggers, tables  (nodes)
  edges   : object --READS-->  table   (SELECT / JOIN / FROM)
            object --WRITES--> table   (INSERT / UPDATE / DELETE)
            trigger --FIRES_ON--> table
            object --CALLS--> procedure
Data flow: if proc P reads table A and writes table B, then A --(P)--> B.

HONESTY: regex + statement-scope heuristic (no full SQL grammar). Dialect quirks,
dynamic SQL (EXECUTE IMMEDIATE building statements at runtime), and CTEs are not
fully modelled. Reads/writes are exact for static FROM/JOIN/INTO/UPDATE/DELETE.
"""

import os
import re
from pathlib import Path

_READ = {"SELECT", "JOIN", "FROM"}
_WRITE = {"INSERT", "UPDATE", "DELETE"}

_SQL_EXT = {".sql", ".ddl", ".dml", ".proc", ".sp", ".fnc", ".prc", ".trg",
            ".pkg", ".pkb", ".pks", ".pgsql", ".plpgsql", ".tsql", ".vw", ".view"}

# object-definition openers — each starts a new "owning scope"
_DEF = re.compile(
    r'\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:FORCE\s+|MATERIALIZED\s+|GLOBAL\s+TEMPORARY\s+)?'
    r'(PROCEDURE|FUNCTION|VIEW|TRIGGER|PACKAGE(?:\s+BODY)?)\s+([\w\.]+)', re.IGNORECASE)

_READ_RE = [
    ("SELECT", re.compile(r'\bFROM\s+([\w\.]+)', re.IGNORECASE)),
    ("JOIN",   re.compile(r'\bJOIN\s+([\w\.]+)', re.IGNORECASE)),
]
_WRITE_RE = [
    ("INSERT", re.compile(r'\bINSERT\s+(?:OR\s+\w+\s+)?INTO\s+([\w\.]+)', re.IGNORECASE)),
    ("UPDATE", re.compile(r'\bUPDATE\s+([\w\.]+)\s+SET', re.IGNORECASE)),
    ("DELETE", re.compile(r'\bDELETE\s+FROM\s+([\w\.]+)', re.IGNORECASE)),
]
_CALL_RE = re.compile(r'\b(?:EXEC(?:UTE)?|CALL)\s+([\w\.]+)', re.IGNORECASE)
_TRIG_ON = re.compile(r'\bON\s+([\w\.]+)', re.IGNORECASE)

_KW = {"DUAL", "TABLE", "SELECT", "WHERE", "SET", "VALUES"}


def _strip(src):
    src = re.sub(r"--[^\n]*", " ", src)
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.DOTALL)
    return src


def _norm(name):
    return name.strip().lower().split(".")[-1]   # unqualify + case-fold


def _sql_files(repo_root):
    out = []
    for dp, dn, fn in os.walk(repo_root):
        dn[:] = [d for d in dn if d not in {".git", "node_modules"}]
        for f in fn:
            if os.path.splitext(f)[1].lower() in _SQL_EXT:
                out.append(os.path.join(dp, f))
    return out


def analyze(repo_root):
    files = _sql_files(repo_root)
    reads = []        # (object, table)
    writes = []       # (object, table)
    calls = []        # (object, proc)
    fires_on = []     # (trigger, table)
    objects = {}      # name -> kind
    tables = set()

    for fp in files:
        try:
            src = _strip(Path(fp).read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue

        # split into owning scopes by definition openers; everything between two
        # openers belongs to the first. A file-level scope catches loose DML.
        markers = [(m.start(), m.group(1).upper(), _norm(m.group(2)))
                   for m in _DEF.finditer(src)]
        # table definitions (for node set)
        for m in re.finditer(r'\bCREATE\s+(?:GLOBAL\s+TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w\.]+)',
                              src, re.IGNORECASE):
            tables.add(_norm(m.group(1)))

        bounds = [pos for pos, _, _ in markers] + [len(src)]
        scopes = []
        if markers:
            if markers[0][0] > 0:
                scopes.append(("__file__", "FILE", src[:markers[0][0]]))
            for i, (pos, kind, name) in enumerate(markers):
                body = src[pos:bounds[i + 1]]
                objects[name] = kind
                scopes.append((name, kind, body))
        else:
            scopes.append(("__file__", "FILE", src))

        for owner, kind, body in scopes:
            if kind == "TRIGGER":
                mt = _TRIG_ON.search(body)
                if mt:
                    fires_on.append((owner, _norm(mt.group(1))))
            for label, rx in _READ_RE:
                for m in rx.finditer(body):
                    t = _norm(m.group(1))
                    if t.upper() not in _KW:
                        reads.append((owner, t))
            for label, rx in _WRITE_RE:
                for m in rx.finditer(body):
                    t = _norm(m.group(1))
                    if t.upper() not in _KW:
                        writes.append((owner, t))
            for m in _CALL_RE.finditer(body):
                calls.append((owner, _norm(m.group(1))))

    # data flow: A --(P)--> B when P reads A and writes B
    reads_by_obj = {}
    writes_by_obj = {}
    for o, t in reads: reads_by_obj.setdefault(o, set()).add(t)
    for o, t in writes: writes_by_obj.setdefault(o, set()).add(t)
    flows = []        # (src_table, via_object, dst_table)
    for o in set(reads_by_obj) | set(writes_by_obj):
        for a in reads_by_obj.get(o, ()):
            for b in writes_by_obj.get(o, ()):
                if a != b:
                    flows.append((a, o, b))

    return {
        "language": "sql", "repo": repo_root,
        "files_parsed": len(files),
        "objects": objects, "tables": sorted(tables),
        "reads": reads, "writes": writes, "calls": calls, "fires_on": fires_on,
        "data_flows": flows,
        "counts": {"objects": len(objects), "tables": len(tables),
                   "reads": len(reads), "writes": len(writes),
                   "calls": len(calls), "data_flows": len(flows)},
        "boundary": "regex + scope heuristic (no SQL grammar). READ = FROM/JOIN, "
                    "WRITE = INSERT/UPDATE/DELETE, attributed to the enclosing "
                    "CREATE object. Dynamic SQL (EXECUTE IMMEDIATE), CTEs, and "
                    "dialect-specific constructs are not fully modelled.",
    }


# --------------------------------------------------------------------------- #
# lineage queries (deterministic, boundary-labelled)
# --------------------------------------------------------------------------- #
def writers_of(table, model):
    t = _norm(table)
    objs = sorted({o for o, x in model["writes"] if x == t})
    return {"query": "writers_of", "table": t, "writers": objs, "count": len(objs),
            "boundary": "objects with INSERT/UPDATE/DELETE on this table (static)"}


def readers_of(table, model):
    t = _norm(table)
    objs = sorted({o for o, x in model["reads"] if x == t})
    return {"query": "readers_of", "table": t, "readers": objs, "count": len(objs),
            "boundary": "objects with FROM/JOIN on this table (static)"}


def upstream_of(table, model, max_hops=10):
    """Tables whose data flows INTO `table` (transitively), via procedures."""
    t = _norm(table)
    adj = {}
    for a, o, b in model["data_flows"]:
        adj.setdefault(b, set()).add(a)
    seen, frontier, hops = set(), {t}, 0
    while frontier and hops < max_hops:
        nxt = set()
        for n in frontier:
            for src in adj.get(n, ()):
                if src not in seen and src != t:
                    seen.add(src); nxt.add(src)
        frontier = nxt; hops += 1
    return {"query": "upstream_of", "table": t, "upstream_tables": sorted(seen),
            "count": len(seen),
            "boundary": "transitive read->write data flow through procedures; "
                        "dynamic SQL not followed"}


def impact_of_table(table, model, max_hops=10):
    """Tables affected DOWNSTREAM if `table` changes (data flows out of it)."""
    t = _norm(table)
    adj = {}
    for a, o, b in model["data_flows"]:
        adj.setdefault(a, set()).add(b)
    seen, frontier, hops = set(), {t}, 0
    while frontier and hops < max_hops:
        nxt = set()
        for n in frontier:
            for dst in adj.get(n, ()):
                if dst not in seen and dst != t:
                    seen.add(dst); nxt.add(dst)
        frontier = nxt; hops += 1
    return {"query": "impact_of_table", "table": t, "downstream_tables": sorted(seen),
            "count": len(seen), "label": "DATA_REACHABLE",
            "boundary": "transitive write-path data flow; NOT semantic column-level "
                        "lineage; dynamic SQL not followed"}
