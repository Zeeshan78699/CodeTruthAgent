import io
p = r"v3\repository_reasoning\benchmarks\TraceEval\run_traceeval.py"
t = io.open(p, encoding="utf-8").read()

old = '''        shutil.copy(src_file, os.path.join(d, os.path.basename(src_file)))
        import v3.repository_reasoning.java_type_inference as JT'''

new = '''        shutil.copy(src_file, os.path.join(d, os.path.basename(src_file)))
        _root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
        if _root not in sys.path:
            sys.path.insert(0, _root)
        import v3.repository_reasoning.java_type_inference as JT'''

if old in t:
    io.open(p, "w", encoding="utf-8").write(t.replace(old, new))
    print("PATCHED OK - v3 root now injected inside run_instance before import")
else:
    print("OLD NOT FOUND - paste run_instance and I will match it")