import io
p = r"v3\repository_reasoning\benchmarks\TraceEval\run_traceeval.py"
t = io.open(p, encoding="utf-8").read()

old = '''def find_source_file(info, repo_roots):
    """Locate the instance's original source file under one of the local clones.
    repo_roots: {repo_short_name: local_path}. Returns abs path or None."""
    src = info.get("source", "")               # e.g. 'gunnarmorling/1brc'
    orig = info.get("original_file", "")        # e.g. 'src/main/java/.../X.java'
    repo_name = src.split("/")[-1] if "/" in src else src
    root = repo_roots.get(repo_name) or repo_roots.get(src)
    if not root or not orig:
        return None
    candidate = os.path.join(root, *orig.split("/"))
    return candidate if os.path.exists(candidate) else None'''

new = '''def find_source_file(info, repo_roots, repos_base=r"C:\\repos"):
    """Locate the instance's original source file.

    Resolution order:
      1. explicit REPO_ROOTS mapping (manual override / exceptions)
      2. auto-discover: <repos_base>\\<repo_short_name>  (e.g. C:\\repos\\pki)
    Returns abs path to the file, or None if unresolved / file missing.
    """
    src = info.get("source", "")
    orig = info.get("original_file", "")
    if not orig:
        return None
    repo_name = src.split("/")[-1] if "/" in src else src
    root = repo_roots.get(repo_name) or repo_roots.get(src)
    if not root:
        cand_root = os.path.join(repos_base, repo_name)
        if os.path.isdir(cand_root):
            root = cand_root
    if not root:
        return None
    candidate = os.path.join(root, *orig.split("/"))
    return candidate if os.path.exists(candidate) else None'''

if old in t:
    io.open(p, "w", encoding="utf-8").write(t.replace(old, new))
    print("PATCHED OK - find_source_file now auto-discovers under C:\\repos")
else:
    print("OLD NOT FOUND - paste the current find_source_file and I will match it")