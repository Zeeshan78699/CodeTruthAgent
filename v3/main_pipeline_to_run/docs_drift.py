r"""
docs_drift.py  (v2 - precision-gated)
CodeTruth Agent V3 - D3-015 Documentation Auditor, Phase 1 / Capability 2b.

v2 adds a claim-classification gate: only genuine project-API references enter
DOCUMENTED_MISSING. Config keys, HTTP terms, externals, filenames, builtins are
excluded. Dotted members that may be properties/attributes are NO_EVIDENCE, not
DRIFT. Counts reconcile. Citations carry file:line.
"""
from __future__ import annotations
import ast
import os
import re

PRUNE = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tox",
         "build", "dist", ".mypy_cache", ".pytest_cache", "_scratch", "_clones",
         "test", "tests"}

MATCH = "MATCH"
DRIFT = "DRIFT"
NO_EVIDENCE = "NO_EVIDENCE"

# ===========================================================================
# LEXICAL CLASSIFICATION STAGE  (per D3-015 review)
# A documented token is classified into exactly one lexical category BEFORE any
# drift analysis. Only 'api' tokens proceed to the resolver. Everything else is
# excluded (not a project-API claim) or routed to NO_EVIDENCE (unrepresentable).
#
#   token -> lexical class -> {keyword|builtin|stdlib|dependency|config|filename|
#                              http|example|member|api}
#   only 'api' -> resolver -> MATCH | DRIFT | NO_EVIDENCE
# ===========================================================================
import keyword as _kw

# Python keywords + soft keywords — never API symbols.
_KEYWORDS = set(_kw.kwlist) | set(getattr(_kw, "softkwlist", [])) | {
    "match", "case", "type"}  # soft kws across versions

# HTTP / protocol / format tokens.
_HTTP = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE",
         "HTTP", "HTTPS", "HTML", "CSS", "JSON", "XML", "URL", "URI", "API",
         "ASGI", "WSGI", "CLI", "SQL", "TCP", "UDP", "REST", "CORS", "CSRF",
         "MIME", "UTF", "ASCII", "UUID",
         # cookie attributes / HTTP headers / directives commonly in docs:
         "SameSite", "HttpOnly", "Secure", "Lax", "Strict", "Expires", "Host",
         "Location", "Domain", "Path", "Origin", "Referer", "Cookie", "Accept",
         "Authorization", "ETag", "Vary", "Allow", "Age", "Date", "Server",
         # Apache/nginx/deploy config directives:
         "DocumentRoot", "LoadModule", "ProxyPass", "ServerName", "Listen",
         "WSGIServer", "WSGIDaemonProcess", "WSGIScriptAlias",
         # JS globals frequently in frontend docs:
         "JavaScript", "jQuery", "XMLHttpRequest", "Promise", "FormData",
         "Response", "Request", "Window", "Document", "Event"}

# Third-party dependencies / external projects (not the project's own API).
_DEPENDENCY = {"PyPI", "Gunicorn", "Werkzeug", "Jinja", "Jinja2", "Click",
               "blinker", "Blinker", "itsdangerous", "ItsDangerous", "MarkupSafe",
               "Python", "pip", "venv", "virtualenv", "pytest", "setuptools",
               "wheel", "Quart", "Watchdog", "watchdog", "Gevent", "gevent",
               "greenlet", "eventlet", "asgiref", "hypercorn", "uvicorn",
               "SQLAlchemy", "sqlalchemy", "redis", "celery",
               "MongoEngine", "mongoengine", "WTForms", "wtforms", "Waitress",
               "waitress", "uWSGI", "uwsgi", "SQLite", "sqlite3", "PostgreSQL",
               "MySQL", "Peewee", "peewee", "Marshmallow", "marshmallow",
               "cryptography", "requests", "aiohttp", "httpx", "tornado",
               # werkzeug re-exports frequently documented by Flask:
               "HTTPException", "LocalProxy", "BadRequest", "NotFound",
               "Response", "Request", "Map", "Rule", "Headers", "MultiDict",
               "SecureCookie", "Client", "TestResponse"}

# Standard-library modules/names — imports, not project API.
_STDLIB = {"timedelta", "datetime", "date", "time", "json", "os", "sys", "re",
           "io", "abc", "enum", "typing", "logging", "functools", "itertools",
           "collections", "pathlib", "decimal", "uuid", "hashlib", "base64",
           "asyncio", "threading", "socket", "struct", "pickle", "copy", "math",
           "contextvars", "contextlib", "warnings", "traceback", "inspect",
           "importlib", "types", "weakref", "gc", "signal", "atexit", "tempfile",
           "shutil", "subprocess", "getpass", "secrets", "hmac", "urllib"}

_CONFIG_HINT = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")   # SECRET_KEY, APPLICATION_ROOT
_FILENAME = re.compile(r".*\.(py|html|txt|cfg|ini|toml|yaml|yml|json|rst|md|jinja2?|css|js|po|pot|mo)$", re.I)
import builtins as _builtins_mod
_BUILTINS = set(dir(_builtins_mod))

# Common example / tutorial / placeholder variables and parameter names. These
# appear in docs constantly but are almost never claims that the project exports
# a top-level symbol by that name.
_EXAMPLE = {
    "app", "db", "client", "self", "cls", "request", "session", "response",
    "e", "f", "g", "x", "y", "z", "i", "j", "k", "n", "data", "result",
    "args", "kwargs", "config", "name", "value", "key", "item", "obj",
    # from the review — parameters / placeholders / tutorial vars:
    "message", "category", "context", "template", "rule", "defaults", "person",
    "user", "headers", "payload", "endpoint", "func", "view", "handler",
    "callback", "path", "url", "params", "query", "body", "content", "text",
    "html", "form", "field", "error", "exc", "err", "msg", "code", "status",
    "options", "kwarg", "arg", "default", "values", "keys", "items", "count",
    "index", "start", "end", "size", "length", "output", "input", "buffer",
    "stream", "chunk", "line", "row", "col", "cell", "node", "edge", "tree",
    "email", "password", "username", "token", "secret", "id", "uid", "pk",
    "file", "files", "foo", "bar", "baz", "spam", "eggs", "yourapplication",
    "yourapp", "myapp", "mymodule", "mypackage", "example", "sample", "demo",
}


def classify_token(tok, was_role, deps=None):
    """Lexical classification. Returns exactly one category. Only 'api' proceeds
    to drift analysis. `deps` is the repo's OWN dependency set (from its manifest
    + third-party imports) — passed in so dependency detection is repo-agnostic,
    not a hardcoded list. The module-level _DEPENDENCY set is only a common
    ecosystem seed, unioned with the repo's real deps by the caller."""
    deps = deps or set()
    simple = tok.split(".")[-1]
    head = tok.split(".")[0]

    # order matters: most-specific / highest-confidence exclusions first
    if simple in _KEYWORDS or tok in _KEYWORDS:
        return "keyword"
    if _FILENAME.match(tok):
        return "filename"
    if tok in _HTTP or simple in _HTTP:
        return "http"
    _all_deps = _DEPENDENCY | deps
    if head in _all_deps or tok in _all_deps or simple in _all_deps:
        return "dependency"
    if _CONFIG_HINT.match(tok):
        return "config"
    if simple in _STDLIB or head in _STDLIB or tok in _STDLIB:
        return "stdlib"
    if simple in _BUILTINS:
        return "builtin"
    if simple in _EXAMPLE or tok in _EXAMPLE:
        return "example"
    # dotted member that may be a property/attribute/re-export the symbol model
    # cannot represent -> NO_EVIDENCE (handled by caller), not exclusion.
    if "." in tok and not was_role:
        return "member"
    # a bare lowercase single word without a role is very likely prose.
    if not was_role and "." not in tok and tok.islower() and len(tok) < 14:
        return "prose"
    return "api"


# categories that are EXCLUDED from drift entirely (not project-API claims)
_EXCLUDED_CATEGORIES = ("keyword", "filename", "http", "dependency", "config",
                        "stdlib", "builtin", "example", "prose")


import re as _re_src
# Source-path categories. A symbol's ORIGIN determines whether it is intended
# public API, a tutorial example, doc tooling, a test, or a CLI entry. This one
# capability resolves all three of the review's remaining items: public-API
# visibility, example/tutorial ownership, and production-vs-example separation.
_EXAMPLE_DIRS = _re_src.compile(
    r"(^|/|\\)(examples?|tutorials?|samples?|demos?|docs?|doc)(/|\\)", _re_src.I)
_DOC_TOOLING = _re_src.compile(r"(^|/|\\)(conf\.py$|docs?/conf|sphinx|mkdocs)", _re_src.I)
_TEST_DIRS = _re_src.compile(r"(^|/|\\)(tests?|testing|conftest\.py$)(/|\\|$)", _re_src.I)
_CLI_HINT = _re_src.compile(r"(^|/|\\)(cli|__main__\.py$|scripts?)(/|\\|$)", _re_src.I)
# benchmark / build-tooling / test-shim / standalone-check files: public in the
# file sense but never the project's user-facing API. Matched by filename.
_NONPROD_FILE = _re_src.compile(
    r"(^|/|\\)(benchmarks?|prerelease|release|setup|build|"
    r"[\w]*_shim|[\w]*_check|[\w]*_standalone[\w]*|conftest)\.py$", _re_src.I)


def source_category(rel_path):
    """Classify a source file by its path into an ownership category:
       production  — the project's real code (intended API lives here)
       example     — tutorial/sample/demo code (NOT the project's API)
       doc_tooling — sphinx conf.py, mkdocs, docs build scripts
       test        — test files
       cli         — command-line entry points
    Only 'production' symbols are candidates for UNDOCUMENTED_PUBLIC drift; the
    rest are noted separately, not treated as undocumented API gaps."""
    p = rel_path.replace("\\", "/")
    if _DOC_TOOLING.search(p):
        return "doc_tooling"
    if _NONPROD_FILE.search(p):
        return "tooling"
    if _TEST_DIRS.search(p):
        return "test"
    if _EXAMPLE_DIRS.search(p):
        return "example"
    if _CLI_HINT.search(p):
        return "cli"
    return "production"


def _iter_py(repo_root):
    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in PRUNE and not d.startswith(".")]
        for fn in files:
            if fn.endswith(".py"):
                yield os.path.join(root, fn)


def _is_property(sub):
    """True if a method is decorated with @property or @cached_property."""
    for dec in getattr(sub, "decorator_list", []):
        nm = (dec.id if isinstance(dec, ast.Name)
              else dec.attr if isinstance(dec, ast.Attribute) else None)
        if nm in ("property", "cached_property"):
            return True
    return False


def _instance_fields(class_node):
    """Collect 'self.X = ...' attribute names assigned inside any method of the
    class (primarily __init__). These are instance fields — AST-visible, so their
    documented references (Flask.url_map) can resolve to MATCH instead of falling
    into NO_EVIDENCE."""
    fields = {}
    for sub in class_node.body:
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for n in ast.walk(sub):
                # self.NAME = ...   (Assign or AnnAssign)
                targets = []
                if isinstance(n, ast.Assign):
                    targets = n.targets
                elif isinstance(n, ast.AnnAssign) and n.target:
                    targets = [n.target]
                for t in targets:
                    if (isinstance(t, ast.Attribute)
                            and isinstance(t.value, ast.Name)
                            and t.value.id == "self"
                            and not t.attr.startswith("_")):
                        fields.setdefault(t.attr, sub.lineno)
    return fields


def build_code_symbols(repo_root):
    symbols = {}
    class_methods = set()
    class_attrs = set()   # Class.attr entries that are attributes/properties/fields
    symbol_source = {}    # name -> source_category of first definition site
    parsed = 0
    for path in _iter_py(repo_root):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                tree = ast.parse(f.read())
        except (SyntaxError, ValueError, OSError):
            continue
        parsed += 1
        rel = os.path.relpath(path, repo_root)
        src_cat = source_category(rel)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_"):
                    continue
                symbol_source.setdefault(node.name, src_cat)
                symbols.setdefault(node.name, []).append(f"{rel}:{node.lineno}")
                if isinstance(node, ast.ClassDef):
                    cls = node.name
                    for sub in node.body:
                        # (a) methods and @property methods
                        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if sub.name.startswith("_"):
                                continue
                            key = f"{cls}.{sub.name}"
                            symbols.setdefault(key, []).append(f"{rel}:{sub.lineno}")
                            if _is_property(sub):
                                class_attrs.add(key)   # documented as attribute
                            else:
                                class_methods.add(key)
                        # (b) class-body assignments: NAME = ... / NAME: T = ...
                        elif isinstance(sub, ast.Assign):
                            for t in sub.targets:
                                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                                    key = f"{cls}.{t.id}"
                                    symbols.setdefault(key, []).append(f"{rel}:{sub.lineno}")
                                    class_attrs.add(key)
                        elif isinstance(sub, ast.AnnAssign):
                            t = sub.target
                            if isinstance(t, ast.Name) and not t.id.startswith("_"):
                                key = f"{cls}.{t.id}"
                                symbols.setdefault(key, []).append(f"{rel}:{sub.lineno}")
                                class_attrs.add(key)
                    # (c) instance fields: self.X = ... inside methods
                    for fld, lineno in _instance_fields(node).items():
                        key = f"{cls}.{fld}"
                        symbols.setdefault(key, []).append(f"{rel}:{lineno}")
                        class_attrs.add(key)
    return symbols, class_methods, class_attrs, symbol_source, parsed


_ROLE_RE = re.compile(r":(?:func|meth|class|obj|attr):`~?([A-Za-z_][\w.]*)`")
_BACKTICK_CALL = re.compile(r"`([A-Za-z_][\w.]*)\(\)`")
_BACKTICK = re.compile(r"`([A-Za-z_][\w.]+)`")
# Sphinx autodoc directives — the primary way scientific/library projects
# document their API. `.. autofunction:: X` IS a documentation claim about X,
# just as much as :func:`X`. Missing these made every autodoc-documented symbol
# read as UNDOCUMENTED_PUBLIC (994 false positives on fluids).
_AUTODOC_RE = re.compile(
    r"\.\.\s+auto(?:function|class|method|attribute|data|exception|decorator)::\s*"
    r"([A-Za-z_][\w.]*)")
_STOPWORDS = {"true", "false", "none", "the", "and", "for", "int", "str", "list",
              "dict", "bool", "float", "object", "type"}


def extract_doc_claims(repo_root):
    claims = []
    targets = []
    for name in (os.listdir(repo_root) if os.path.isdir(repo_root) else []):
        if name.lower().startswith("readme"):
            targets.append(name)
    for d in ("docs", "doc"):
        dd = os.path.join(repo_root, d)
        if os.path.isdir(dd):
            for root, dirs, files in os.walk(dd):
                dirs[:] = [x for x in dirs if x not in PRUNE]
                for fn in files:
                    if fn.endswith((".md", ".rst", ".txt")):
                        targets.append(os.path.relpath(os.path.join(root, fn), repo_root))
    seen = set()
    for rel in targets:
        p = os.path.join(repo_root, rel)
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            for pat, is_role in ((_ROLE_RE, True), (_AUTODOC_RE, True),
                                 (_BACKTICK_CALL, False), (_BACKTICK, False)):
                for m in pat.finditer(line):
                    sym = m.group(1)
                    last = sym.split(".")[-1]
                    if last.lower() in _STOPWORDS or len(last) < 2:
                        continue
                    key = (sym, rel, lineno)
                    if key in seen:
                        continue
                    seen.add(key)
                    claims.append({"symbol": sym, "file": rel, "line": lineno,
                                   "excerpt": line.strip()[:100], "was_role": is_role})
    return claims


def _changelog_removals(repo_root):
    removals = []
    for name in (os.listdir(repo_root) if os.path.isdir(repo_root) else []):
        if name.lower().startswith(("changelog", "changes", "history", "news")):
            p = os.path.join(repo_root, name)
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    for lineno, line in enumerate(f, 1):
                        m = re.search(r"\b(?:removed?|deleted?|dropped)\s+`?([A-Za-z_]\w+)`?", line, re.I)
                        if m and m.group(1).lower() not in _STOPWORDS:
                            removals.append((m.group(1), name, lineno, line.strip()[:100]))
            except OSError:
                continue
    return removals


def _simple(name):
    return name.split(".")[-1]


def derive_repo_dependencies(repo_root):
    """Derive the repo's OWN dependency names — repo-agnostic, evidence-based.

    Sources, in order of reliability:
      1. Declared dependencies in the manifest (pyproject.toml / setup.cfg /
         setup.py / requirements*.txt). What the project SAYS it depends on.
      2. Third-party top-level imports: modules imported anywhere in the source
         that are NOT defined in-repo and NOT stdlib. What the project ACTUALLY
         pulls in.

    Returns a set of distribution/module names + their CapWords-ish variants, so
    a documented `Werkzeug`/`werkzeug` both classify as dependency. This replaces
    the hardcoded list with the project's declared reality, so the auditor works
    on Django, FastAPI, or any Python repo without curation.
    """
    deps = set()

    # ---- 1. declared dependencies from manifests ------------------------- #
    def _add_req_name(line):
        # 'flask>=2.0', 'flask[async]==2.0', 'Flask ; python_version>"3"'
        m = re.match(r"\s*([A-Za-z0-9_.\-]+)", line)
        if m:
            name = m.group(1)
            if name and not name.startswith("#"):
                deps.add(name)
                deps.add(name.replace("-", "_"))
                deps.add(name.replace("-", "_").split(".")[0])

    # requirements*.txt
    for fn in (os.listdir(repo_root) if os.path.isdir(repo_root) else []):
        if fn.lower().startswith("requirements") and fn.endswith(".txt"):
            try:
                with open(os.path.join(repo_root, fn), encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if line.strip() and not line.strip().startswith(("#", "-")):
                            _add_req_name(line)
            except OSError:
                pass

    # pyproject.toml (dependencies + project.dependencies + poetry)
    pp = os.path.join(repo_root, "pyproject.toml")
    if os.path.isfile(pp):
        try:
            with open(pp, encoding="utf-8", errors="replace") as f:
                text = f.read()
            # grab quoted requirement strings in any [*dependencies*] context
            for m in re.finditer(r'["\']([A-Za-z0-9_.\-]+)\s*(?:[<>=!~\[;].*?)?["\']', text):
                _add_req_name(m.group(1))
            # poetry table keys: name = "^1.0"
            in_poetry_deps = False
            for line in text.splitlines():
                if re.match(r"\s*\[tool\.poetry\.(dev-)?dependencies\]", line):
                    in_poetry_deps = True; continue
                if line.strip().startswith("["):
                    in_poetry_deps = False
                if in_poetry_deps:
                    m = re.match(r"\s*([A-Za-z0-9_.\-]+)\s*=", line)
                    if m and m.group(1).lower() != "python":
                        _add_req_name(m.group(1))
        except OSError:
            pass

    # setup.cfg / setup.py — install_requires
    for fn in ("setup.cfg", "setup.py"):
        p = os.path.join(repo_root, fn)
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                for m in re.finditer(r'["\']([A-Za-z0-9_.\-]+)\s*(?:[<>=!~\[;].*?)?["\']', text):
                    nm = m.group(1)
                    if len(nm) > 1 and not nm.startswith("."):
                        _add_req_name(nm)
            except OSError:
                pass

    # ---- 2. third-party top-level imports (not in-repo, not stdlib) ------ #
    local_top = set()  # top-level package/module names defined in the repo
    imported = set()
    for path in _iter_py(repo_root):
        rel = os.path.relpath(path, repo_root)
        top = rel.split(os.sep)[0]
        if top.endswith(".py"):
            top = top[:-3]
        local_top.add(top)
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                tree = ast.parse(f.read())
        except (SyntaxError, ValueError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    imported.add(a.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:  # absolute import
                    imported.add(node.module.split(".")[0])
    _STDLIB_MODULES = _STDLIB | set(getattr(__import__("sys"), "stdlib_module_names", set()))
    dep_provided_names = set()  # names imported FROM third-party deps
    for path in _iter_py(repo_root):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                tree = ast.parse(f.read())
        except (SyntaxError, ValueError, OSError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                base = node.module.split(".")[0]
                if base not in local_top and base not in _STDLIB_MODULES:
                    # names pulled from a third-party module are dep-provided,
                    # not this repo's API.
                    for a in node.names:
                        if a.name != "*":
                            dep_provided_names.add(a.name)
    for mod in imported:
        if mod and mod not in local_top and mod not in _STDLIB_MODULES:
            deps.add(mod)
            deps.add(mod.capitalize())
    deps |= dep_provided_names

    deps.discard("")
    return deps


_AUTOMODULE_RE = re.compile(r"\.\.\s+automodule::\s*([A-Za-z_][\w.]*)")
# Whether a given automodule block excludes members. By default sphinx projects
# document members either via inline `:members:` or a global conf.py setting
# (autodoc_default_options). Real projects like fluids write `.. automodule:: X`
# and rely on the global default — so we treat automodule as member-covering
# UNLESS an explicit `:no-members:` / `:members: <explicit list>` narrows it.


def _automodule_covered(repo_root):
    """Find modules documented via `.. automodule:: X`. In practice sphinx
    projects (fluids, numpy, scipy) put one automodule directive per submodule
    and enable members globally in conf.py — so an automodule directive means
    'this module's public API is documented'. Returns covered module names, both
    dotted (fluids.core) and their leaf segment (core), so symbols in
    fluids/core.py resolve. This is the primary doc style for scientific Python."""
    covered = set()
    targets = []
    for d in ("docs", "doc"):
        dd = os.path.join(repo_root, d)
        if os.path.isdir(dd):
            for root, dirs, files in os.walk(dd):
                dirs[:] = [x for x in dirs if x not in PRUNE]
                for fn in files:
                    if fn.endswith((".rst", ".md", ".txt")):
                        targets.append(os.path.join(root, fn))
    for p in targets:
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        for m in _AUTOMODULE_RE.finditer(text):
            mod = m.group(1)
            covered.add(mod)
            covered.add(mod.split(".")[0])   # top package: fluids
            covered.add(mod.split(".")[-1])  # leaf segment: core, atmosphere
    return covered


def audit(repo_root, language="python"):
    if language != "python":
        return {"documentation_drift": {
            "tier": "UNKNOWN", "reason": "LANGUAGE_NOT_SUPPORTED",
            "notes": (f"symbol drift is checked against a Python AST symbol table; "
                      f"the '{language}' engine is not parsed for this.")}}
    code_syms, class_methods, class_attrs, symbol_source, parsed = build_code_symbols(repo_root)
    if parsed == 0:
        return {"documentation_drift": {
            "tier": "UNKNOWN", "reason": "NO_EVIDENCE_FOUND",
            "notes": "no parseable Python source to build a symbol table"}}
    code_simple = {}
    for full in code_syms:
        code_simple.setdefault(_simple(full), []).append(full)
    # repo-agnostic dependency set from THIS repo's manifest + imports
    repo_deps = derive_repo_dependencies(repo_root)
    claims = extract_doc_claims(repo_root)
    findings = []
    n_match = n_noev = 0
    cat_counts = {}
    for c in claims:
        sym, was_role = c["symbol"], c["was_role"]
        cat = classify_token(sym, was_role, deps=repo_deps)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        cite = f"{c['file']}:{c['line']}"
        if cat in _EXCLUDED_CATEGORIES:
            continue
        simple = _simple(sym)
        found = sym in code_syms or simple in code_simple or sym in class_methods or sym in class_attrs
        if found:
            n_match += 1
            continue
        if cat == "member":
            n_noev += 1
            findings.append({
                "type": "DOCUMENTED_MEMBER_UNVERIFIABLE", "outcome": NO_EVIDENCE,
                "symbol": sym, "doc_evidence": cite, "excerpt": c["excerpt"],
                "capability_gap": "property/attribute/inherited-member resolution",
                "statement": (f"Docs reference `{sym}` ({cite}); not a top-level def, "
                              f"but it may be a property, attribute, inherited member, "
                              f"or instance field - categories the current symbol "
                              f"model cannot represent. Cannot confirm or refute. "
                              f"NO_EVIDENCE.")})
            continue
        # A DRIFT claim needs HIGH confidence the symbol is truly missing. The AST
        # table holds top-level defs + direct methods only - NOT re-exports
        # (__init__ imports), submodule members, or deep nesting. So absence is
        # provable DRIFT only for a BARE top-level name. A dotted `X.y` that's
        # absent may be outside the table's reach -> NO_EVIDENCE, not DRIFT.
        if "." in sym:
            n_noev += 1
            findings.append({
                "type": "DOCUMENTED_MEMBER_UNVERIFIABLE", "outcome": NO_EVIDENCE,
                "symbol": sym, "doc_evidence": cite, "excerpt": c["excerpt"],
                "capability_gap": "re-export/submodule/nested-symbol resolution",
                "statement": (f"Docs reference `{sym}` ({cite}); not in the top-level "
                              f"symbol table, but the table does not capture re-exports, "
                              f"submodule members, or deep nesting - absence is not "
                              f"provable. Cannot confirm or refute. NO_EVIDENCE.")})
            continue
        # snake_case bare name absent from top-level defs: likely a property,
        # constructor arg, or instance attribute the symbol model can't represent
        # -> NO_EVIDENCE. BUT an explicit :func:/:meth: role means it IS a function
        # claim even if snake_case, so a missing role-documented function is real
        # DRIFT, not attr-NO_EVIDENCE.
        looks_attrish = ("_" in sym) and sym.islower() and not c.get("was_role")
        if looks_attrish:
            n_noev += 1
            findings.append({
                "type": "DOCUMENTED_ATTR_UNVERIFIABLE", "outcome": NO_EVIDENCE,
                "symbol": sym, "doc_evidence": cite, "excerpt": c["excerpt"],
                "capability_gap": "property/constructor-arg/instance-attribute resolution",
                "statement": (f"Docs reference `{sym}` ({cite}); no top-level def by "
                              f"that name, but it reads like a property, constructor "
                              f"argument, or instance attribute - categories the symbol "
                              f"model cannot represent. Cannot confirm or refute. "
                              f"NO_EVIDENCE.")})
            continue
        # junk / degenerate tokens
        if set(sym) <= set("_") or len(sym) < 2:
            continue
        # A CapWords name absent from code but NOT from an explicit :class:/:func:
        # role is very likely a tutorial/example class (Post, Base, ListView,
        # FirstName) shown in a doc code block, not a claim about THIS project's
        # API. Confident DRIFT requires the role. Otherwise -> NO_EVIDENCE.
        if not c.get("was_role"):
            n_noev += 1
            findings.append({
                "type": "DOCUMENTED_SYMBOL_UNVERIFIABLE", "outcome": NO_EVIDENCE,
                "symbol": sym, "doc_evidence": cite, "excerpt": c["excerpt"],
                "capability_gap": "example-vs-API disambiguation (no role marker)",
                "statement": (f"Docs mention `{sym}` ({cite}) without a :class:/:func: "
                              f"role; it is not in the code, but may be a tutorial or "
                              f"example symbol rather than a claim about this project's "
                              f"API. Cannot confirm it is drift. NO_EVIDENCE.")})
            continue
        findings.append({
            "type": "DOCUMENTED_MISSING", "outcome": DRIFT,
            "symbol": sym, "doc_evidence": cite, "excerpt": c["excerpt"],
            "code_evidence": f"absent from {len(code_syms)} public defs",
            "statement": (f"Docs reference `{sym}` ({cite}) via an explicit API role; "
                          f"no top-level public function or class by that name anywhere. "
                          f"Docs claim it; code lacks it. Investigate: renamed, removed, "
                          f"private, or typo.")})
    documented_sched = {_simple(c["symbol"]) for c in claims} | {c["symbol"] for c in claims}
    automodule_mods = _automodule_covered(repo_root)  # modules with :members:
    undoc_by_source = {}
    automodule_covered_count = 0
    for full, locs in sorted(code_syms.items()):
        if "." in full:
            continue
        if full not in documented_sched:
            # A symbol whose module is documented via `.. automodule:: M` IS
            # documented (scientific/numpydoc style). Match the module's LEAF
            # segment (fluids.core -> file core.py) against the symbol's path.
            # Do NOT fall back to the top package — that would suppress modules
            # with no automodule directive of their own.
            loc0 = (locs[0] if locs else "").replace("\\", "/")
            loc0 = loc0.rsplit(":", 1)[0]  # strip ':lineno' suffix
            path_segs = set(loc0.split("/"))
            path_segs |= {s[:-3] for s in path_segs if s.endswith(".py")}
            # only match on specific covered modules, NOT the bare top package
            specific_covered = automodule_mods - {os.path.basename(os.path.abspath(repo_root))}
            if specific_covered & path_segs:
                automodule_covered_count += 1
                continue
            src = symbol_source.get(full, "production")
            undoc_by_source[src] = undoc_by_source.get(src, 0) + 1
            # Only PRODUCTION symbols are genuine "public API shipped without docs".
            # Example/tutorial/test/CLI/doc-tooling symbols are public in the file
            # sense but are NOT the project's user-facing API — they are not drift.
            if src != "production":
                continue
            findings.append({
                "type": "UNDOCUMENTED_PUBLIC", "outcome": DRIFT, "symbol": full,
                "code_evidence": locs[0], "doc_evidence": "not named in README or docs/",
                "source_category": src,
                "statement": (f"Code exposes public `{full}` ({locs[0]}) in production "
                              f"source; the documentation never names it. Shipped "
                              f"without docs. Investigate: intentional internal, or "
                              f"missing docs.")})
    for sym, cl, lineno, excerpt in _changelog_removals(repo_root):
        if sym in code_syms or sym in code_simple:
            loc = (code_syms.get(sym) or code_simple.get(sym, ["?"]))[0]
            findings.append({
                "type": "DEPRECATED_PRESENT", "outcome": DRIFT, "symbol": sym,
                "doc_evidence": f"{cl}:{lineno}", "excerpt": excerpt,
                "code_evidence": loc if isinstance(loc, str) else str(loc),
                "statement": (f"{cl}:{lineno} states `{sym}` was removed; still "
                              f"defined at {loc}. Changelog says gone; code says "
                              f"present. Investigate: incomplete removal or stale note.")})
    n_missing = sum(1 for f in findings if f["type"] == "DOCUMENTED_MISSING")
    api_claims_checked = n_match + n_missing + n_noev
    drift_total = sum(1 for f in findings if f["outcome"] == DRIFT)
    return {
        "docs_code_drift": {
            "tier": "DERIVED", "value": drift_total,
            "derivation": "docs_drift.symbol_crosscheck.v2@3.0.0",
            "inputs": ["(python AST symbol table)", "(classified doc symbol claims)"]},
        "documentation_drift": {
            "tier": "DERIVED",
            "value": {
                "doc_tokens_seen": len(claims),
                "api_claims_checked": api_claims_checked,
                "match": n_match,
                "documented_missing": n_missing,
                "drift": drift_total,
                "no_evidence": n_noev,
                "reconciles": (api_claims_checked == n_match + n_missing + n_noev),
                "excluded_by_category": {k: v for k, v in sorted(cat_counts.items())
                                         if k in _EXCLUDED_CATEGORIES},
                "code_public_symbols": sum(1 for k in code_syms if "." not in k),
                "undocumented_by_source": undoc_by_source,
                "automodule_covered": automodule_covered_count,
                "files_parsed": parsed},
            "findings": findings,
            "note": ("Counts reconcile: api_claims_checked = match + documented_missing "
                     "+ no_evidence. Non-API tokens (config keys, HTTP terms, "
                     "dependencies, filenames, builtins) are excluded. Dotted members "
                     "that may be properties/attributes are NO_EVIDENCE, not DRIFT. "
                     "Code is the arbiter; a finding states disagreement, never that "
                     "docs are wrong.")},
    }


if __name__ == "__main__":
    import sys, json
    print(json.dumps(audit(sys.argv[1]), indent=2))
