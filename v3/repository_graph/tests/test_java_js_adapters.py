"""
test_java_js_adapters.py
Quick test for the Java and JavaScript adapters - creates small sample
files, runs both adapters, and prints the resulting graphs.

Run from project root:
    python v3\\repository_graph\\tests\\test_java_js_adapters.py

Requires: pip install javalang esprima --break-system-packages
"""

import sys
import os
import json
import tempfile
import shutil

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.languages.java_adapter import JavaAdapter
from v3.repository_graph.languages.javascript_adapter import JavaScriptAdapter


JAVA_SAMPLE = """package com.example;

import com.example.util.Helper;
import java.util.List;

public class MyService extends BaseService {
    public void run() {
        Helper.doWork();
        this.process();
    }
    private void process() {
        System.out.println("hi");
    }
}
"""

JS_SAMPLE = """import { helper } from './utils/helper';
import React from 'react';

function run() {
    helper();
    doSomethingElse();
}

class MyComponent extends React.Component {
    render() {
        return this.process();
    }
    process() {
        return run();
    }
}
"""


def find_files(root, ext):
    matches = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith(ext):
                matches.append(os.path.join(dirpath, f))
    return matches


def print_report(title, report):
    print("=" * 60)
    print(title)
    print("=" * 60)
    print(f"function_graph: {sum(len(v) for v in report['function_graph'].values())} function(s)")
    for mod, funcs in report["function_graph"].items():
        for f in funcs:
            print(f"  - {f['id']}  (line {f['lineno']}, scope={f['scope']})")

    print(f"\nclass_graph: {sum(len(v) for v in report['class_graph'].values())} class(es)")
    for mod, classes in report["class_graph"].items():
        for c in classes:
            print(f"  - {c['id']}  bases={c['bases']}")

    print(f"\nimport_graph (internal): {sum(len(v) for v in report['import_graph'].values())}")
    for mod, imports in report["import_graph"].items():
        for i in imports:
            print(f"  - {mod}: {i['imports']}")

    print(f"\ndependency_graph (external): {list(report['dependency_graph'].keys())}")

    print(f"\ncall_graph: {sum(len(v) for v in report['call_graph'].values())} resolved edge(s)")
    for mod, calls in report["call_graph"].items():
        for c in calls:
            print(f"  - {c['caller']} -> {c['callee']}  [{c['resolution']}]")

    print(f"\nunresolved: {len(report['unresolved'])} item(s)")
    for u in report["unresolved"]:
        print(f"  - [{u['pattern']}] {u['module']} line {u['lineno']}: {u['note']}")
    print()


if __name__ == "__main__":
    tmpdir = tempfile.mkdtemp(prefix="lang_adapter_test_")
    try:
        # ---- Java ----
        java_dir = os.path.join(tmpdir, "java_test", "com", "example")
        os.makedirs(java_dir, exist_ok=True)
        java_file = os.path.join(java_dir, "MyService.java")
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(JAVA_SAMPLE)

        java_root = os.path.join(tmpdir, "java_test")
        java_files = find_files(java_root, ".java")
        java_report = JavaAdapter().scan(java_root, java_files)
        print_report("JAVA ADAPTER", java_report)

        # ---- JavaScript ----
        js_dir = os.path.join(tmpdir, "js_test", "src")
        os.makedirs(js_dir, exist_ok=True)
        js_file = os.path.join(js_dir, "app.js")
        with open(js_file, "w", encoding="utf-8") as f:
            f.write(JS_SAMPLE)

        js_root = os.path.join(tmpdir, "js_test")
        js_files = find_files(js_root, ".js")
        js_report = JavaScriptAdapter().scan(js_root, js_files)
        print_report("JAVASCRIPT ADAPTER", js_report)

        # ---- Optional: test against a real repo path passed as argv[1] ----
        if len(sys.argv) > 1:
            real_root = sys.argv[1]
            print("=" * 60)
            print(f"REAL REPO SCAN: {real_root}")
            print("=" * 60)

            real_java_files = find_files(real_root, ".java")
            if real_java_files:
                print(f"Found {len(real_java_files)} .java file(s) - scanning first 5...")
                report = JavaAdapter().scan(real_root, real_java_files[:5])
                print_report("JAVA (real repo sample)", report)
            else:
                print("No .java files found.")

            real_js_files = find_files(real_root, ".js")
            if real_js_files:
                print(f"Found {len(real_js_files)} .js file(s) - scanning first 5...")
                report = JavaScriptAdapter().scan(real_root, real_js_files[:5])
                print_report("JAVASCRIPT (real repo sample)", report)
            else:
                print("No .js files found.")

    finally:
        shutil.rmtree(tmpdir)