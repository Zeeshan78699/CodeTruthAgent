"""
========================================================================
sql_adapter.py
CodeTruth Agent V3 — Module 2 Language Adapter

LANGUAGE:       SQL (PostgreSQL, MySQL, SQLite, Oracle PL/SQL, T-SQL)
PURPOSE:        Builds a call graph from SQL repositories.

ADNOC NOTE:
    Oracle PL/SQL is the primary target.
    Handles: EXECUTE IMMEDIATE, DBMS_* packages,
    PL/SQL blocks, packages, triggers.

GRAPH NODES:  Tables, Views, Procedures, Functions, Triggers, Packages
GRAPH EDGES:  REFERENCES, CALLS, DEFINES, FIRES_ON, USES_PKG

STATUS: Module 2 Language Adapter — Production
========================================================================
"""

from __future__ import annotations
import re
import warnings
from pathlib import Path
from typing import Any

SQL_EXTENSIONS = {
    ".sql", ".ddl", ".dml", ".proc", ".sp", ".fnc",
    ".prc", ".trg", ".pkg", ".pkb", ".pks",
    ".pgsql", ".plpgsql", ".tsql", ".vw", ".view",
}

SQL_KEYWORDS = {
    "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "EXISTS",
    "NULL", "IS", "LIKE", "BETWEEN", "CASE", "WHEN", "THEN", "ELSE",
    "END", "AS", "ON", "SET", "VALUES", "INTO", "BY", "ORDER", "GROUP",
    "HAVING", "LIMIT", "OFFSET", "UNION", "ALL", "DISTINCT", "TOP",
    "ROWNUM", "DUAL", "SYSDATE", "SYSTIMESTAMP", "USER", "LEVEL",
    "TABLE", "INDEX", "VIEW", "SEQUENCE", "SYNONYM", "TRIGGER",
    "PROCEDURE", "FUNCTION", "PACKAGE", "BODY", "BEGIN", "END",
    "DECLARE", "EXCEPTION", "RAISE", "RETURN", "IF", "THEN",
    "ELSIF", "LOOP", "WHILE", "FOR", "EXIT", "COMMIT", "ROLLBACK",
}


def _make_patterns() -> dict:
    return {
        "create_table": re.compile(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:GLOBAL\s+TEMPORARY\s+)?TABLE\s+"
            r"(?:IF\s+NOT\s+EXISTS\s+)?([\w\.]+)",
            re.IGNORECASE
        ),
        "create_view": re.compile(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:FORCE\s+)?(?:MATERIALIZED\s+)?VIEW\s+([\w\.]+)",
            re.IGNORECASE
        ),
        "create_procedure": re.compile(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+([\w\.]+)",
            re.IGNORECASE
        ),
        "create_function": re.compile(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+([\w\.]+)",
            re.IGNORECASE
        ),
        "create_trigger": re.compile(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\s+([\w\.]+)",
            re.IGNORECASE
        ),
        "create_package": re.compile(
            r"CREATE\s+(?:OR\s+REPLACE\s+)?PACKAGE\s+(?:BODY\s+)?([\w\.]+)",
            re.IGNORECASE
        ),
        "from_table": re.compile(
            r"FROM\s+([\w\.]+)(?:\s+(?:AS\s+)?[\w]+)?",
            re.IGNORECASE
        ),
        "join_table": re.compile(
            r"(?:INNER|LEFT|RIGHT|FULL|CROSS|OUTER)?\s*JOIN\s+([\w\.]+)",
            re.IGNORECASE
        ),
        "insert_into": re.compile(
            r"INSERT\s+(?:OR\s+\w+\s+)?INTO\s+([\w\.]+)",
            re.IGNORECASE
        ),
        "update_table": re.compile(
            r"UPDATE\s+([\w\.]+)\s+SET",
            re.IGNORECASE
        ),
        "delete_from": re.compile(
            r"DELETE\s+FROM\s+([\w\.]+)",
            re.IGNORECASE
        ),
        "exec_call": re.compile(
            r"(?:EXEC(?:UTE)?|CALL)\s+([\w\.]+)",
            re.IGNORECASE
        ),
        "dbms_call": re.compile(
            r"(DBMS_[\w]+|UTL_[\w]+|APEX_[\w]+)\.([\w]+)",
            re.IGNORECASE
        ),
        "trigger_on": re.compile(
            r"(?:BEFORE|AFTER|INSTEAD\s+OF)\s+(?:INSERT|UPDATE|DELETE)"
            r"(?:\s+OR\s+(?:INSERT|UPDATE|DELETE))*\s+ON\s+([\w\.]+)",
            re.IGNORECASE
        ),
    }


PATTERNS = _make_patterns()


class SQLFileParser:
    def __init__(self, file_path: Path, content: str):
        self.file_path   = file_path
        self.content     = content
        self.name        = file_path.stem
        self.tables: list[str] = []
        self.views: list[str] = []
        self.procedures: list[str] = []
        self.functions: list[str] = []
        self.triggers: list[str] = []
        self.packages: list[str] = []
        self.table_refs: list[dict] = []
        self.proc_calls: list[dict] = []
        self.dbms_calls: list[dict] = []

    def parse(self) -> "SQLFileParser":
        src = self._strip_comments(self.content)

        self.tables     = self._extract(src, "create_table")
        self.views      = self._extract(src, "create_view")
        self.procedures = self._extract(src, "create_procedure")
        self.functions  = self._extract(src, "create_function")
        self.triggers   = self._extract(src, "create_trigger")
        self.packages   = self._extract(src, "create_package")

        all_defined = set(
            self.tables + self.views + self.procedures +
            self.functions + self.triggers + self.packages
        )

        for pattern_key, ref_type in [
            ("from_table",   "SELECT"),
            ("join_table",   "JOIN"),
            ("insert_into",  "INSERT"),
            ("update_table", "UPDATE"),
            ("delete_from",  "DELETE"),
            ("trigger_on",   "TRIGGER_ON"),
        ]:
            for match in PATTERNS[pattern_key].finditer(src):
                name = match.group(1).strip()
                if self._is_valid(name) and name.upper() not in all_defined:
                    self.table_refs.append({
                        "target": name, "ref_type": ref_type,
                        "source_file": str(self.file_path),
                    })

        for match in PATTERNS["exec_call"].finditer(src):
            name = match.group(1).strip()
            if self._is_valid(name):
                self.proc_calls.append({
                    "target": name, "ref_type": "CALL",
                    "source_file": str(self.file_path),
                })

        for match in PATTERNS["dbms_call"].finditer(src):
            self.dbms_calls.append({
                "package": match.group(1), "method": match.group(2),
                "ref_type": "USES_PKG",
                "source_file": str(self.file_path),
            })

        return self

    def _extract(self, src: str, key: str) -> list[str]:
        return [
            m.group(1).strip() for m in PATTERNS[key].finditer(src)
            if self._is_valid(m.group(1).strip())
        ]

    def _is_valid(self, name: str) -> bool:
        if not name:
            return False
        upper = name.upper().split(".")[-1]
        if upper in SQL_KEYWORDS:
            return False
        return bool(re.match(r"^[\w][\w\.]*$", name))

    def _strip_comments(self, src: str) -> str:
        src = re.sub(r"--[^\n]*", " ", src)
        src = re.sub(r"/\*.*?\*/", " ", src, flags=re.DOTALL)
        return src


class SQLAdapter:
    """Module 2 SQL language adapter."""

    file_extensions = SQL_EXTENSIONS
    language = "sql"

    def scan(self, repo_root: str, file_paths: list | None = None) -> dict:
        root = Path(repo_root)

        if file_paths:
            sql_files = [Path(f) for f in file_paths
                         if Path(f).suffix.lower() in SQL_EXTENSIONS]
        else:
            sql_files = [
                f for f in root.rglob("*")
                if f.suffix.lower() in SQL_EXTENSIONS and f.is_file()
            ]

        if not sql_files:
            return self._empty(repo_root, "NO_SQL_FILES")

        parsed = []
        parse_errors = 0
        for path in sql_files:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                parsed.append(SQLFileParser(path, content).parse())
            except Exception:
                parse_errors += 1

        graph      = self._build_graph(parsed)
        resolution = self._resolve(graph, parsed)
        return self._report(repo_root, sql_files, parsed, graph, resolution, parse_errors)

    def _build_graph(self, parsed: list) -> dict:
        graph = {k: {} for k in ["tables","views","procedures","functions","triggers","packages"]}
        key_map = {
            "tables": "tables", "views": "views",
            "procedures": "procedures", "functions": "functions",
            "triggers": "triggers", "packages": "packages",
        }
        for p in parsed:
            for attr, gkey in key_map.items():
                for name in getattr(p, attr):
                    graph[gkey][name] = {
                        "defined_in": str(p.file_path),
                        "type": attr[:-1].upper(),
                    }
        return graph

    def _resolve(self, graph: dict, parsed: list) -> dict:
        all_known = set()
        for v in graph.values():
            all_known.update(v.keys())

        resolved, unresolved = [], []
        for p in parsed:
            for ref in p.table_refs:
                name = ref["target"]
                if name in all_known or name.split(".")[-1] in all_known:
                    resolved.append({**ref, "resolved": True})
                else:
                    unresolved.append({**ref, "resolved": False,
                                       "reason": "NOT_DEFINED_IN_REPO"})
            for call in p.proc_calls:
                name = call["target"]
                procs = graph["procedures"]
                funcs = graph["functions"]
                if name in procs or name in funcs:
                    resolved.append({**call, "resolved": True})
                else:
                    unresolved.append({**call, "resolved": False,
                                       "reason": "PROCEDURE_NOT_IN_REPO"})
            for pkg in p.dbms_calls:
                unresolved.append({**pkg, "resolved": False,
                                   "reason": "ORACLE_SYSTEM_PACKAGE"})

        total = len(resolved) + len(unresolved)
        return {
            "resolved_count":     len(resolved),
            "unresolved_count":   len(unresolved),
            "resolved_entries":   resolved,
            "unresolved_entries": unresolved,
            "resolution_pct":     round(len(resolved)/total*100,2) if total else 0.0,
        }

    def _report(self, repo_root, sql_files, parsed, graph, resolution, parse_errors):
        nc = {k: len(v) for k, v in graph.items()}
        nc["total"] = sum(nc.values())
        ec = {
            "table_references": sum(len(p.table_refs) for p in parsed),
            "procedure_calls":  sum(len(p.proc_calls) for p in parsed),
            "oracle_pkg_calls": sum(len(p.dbms_calls) for p in parsed),
        }
        ec["total"] = sum(ec.values())
        dialect = self._dialect(parsed)

        total = len(sql_files)
        err_pct = parse_errors / total * 100 if total else 0
        if err_pct > 50:
            gate = "BLOCKED"
        elif nc["total"] == 0 and parse_errors > 0:
            gate = "REVIEW_REQUIRED"
        else:
            gate = "APPROVED"

        return {
            "repo_root":        repo_root,
            "language":         "sql",
            "dialect":          dialect,
            "files_scanned":    total,
            "parse_errors":     parse_errors,
            "tables":           graph["tables"],
            "views":            graph["views"],
            "procedures":       graph["procedures"],
            "functions":        graph["functions"],
            "triggers":         graph["triggers"],
            "packages":         graph["packages"],
            "node_counts":      nc,
            "edge_counts":      ec,
            "resolution":       resolution,
            "resolved_calls":   resolution["resolved_count"],
            "unresolved_total": resolution["unresolved_count"],
            "resolution_pct":   resolution["resolution_pct"],
            "governance_gate":  gate,
            "language_composition": {
                "sql": {"file_count": total, "implemented": True, "dialect": dialect}
            },
        }

    def _dialect(self, parsed: list) -> str:
        exts = {p.file_path.suffix.lower() for p in parsed}
        oracle_exts = {".pkg", ".pkb", ".pks", ".prc", ".fnc", ".trg"}
        if exts & oracle_exts:
            return "oracle_plsql"
        oracle_kw = ["DBMS_", "UTL_", "APEX_", "ROWNUM", "DUAL",
                     "EXECUTE IMMEDIATE", "PRAGMA"]
        for p in parsed:
            for kw in oracle_kw:
                if kw in p.content.upper():
                    return "oracle_plsql"
        if ".pgsql" in exts or ".plpgsql" in exts:
            return "postgresql"
        if ".tsql" in exts:
            return "tsql"
        return "generic_sql"

    def _empty(self, repo_root: str, reason: str) -> dict:
        return {
            "repo_root": repo_root, "language": "sql",
            "files_scanned": 0, "status": reason,
            "node_counts": {"total": 0}, "edge_counts": {"total": 0},
            "resolution": {"resolved_count": 0, "unresolved_count": 0},
            "governance_gate": "BLOCKED",
        }
