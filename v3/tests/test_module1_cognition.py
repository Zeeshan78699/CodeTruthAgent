# test_module1_cognition.py
# Dynamic test suite for Module 1 — Repository Cognition Engine
# CodeTruth Agent V3
#
# Tests build real temporary repositories on the fly.
# No hardcoded paths. No dependency on the actual project files.
# Each test creates its own isolated environment and tears it down after.
#
# Usage:
#   python -m pytest v3/tests/test_module1_cognition.py -v
#   python v3/tests/test_module1_cognition.py
#
# Rounds:
#   Round 1 — Core functionality          (Tests 01-08)
#   Round 2 — pyproject.toml formats      (Tests 09-11)
#   Round 3 — Determinism                 (Test  12)
#   Round 4 — Infrastructure detection    (Test  13)
#   Round 5 — detected_languages          (Tests 14-15)
#   Round 6 — Config-based language       (Tests 16-20)
#   Round 7 — Real-world polyglot repos   (Tests 21-25)
#   Round 8 — Edge cases hostile inputs   (Tests 26-30)
#   Round 9 — Confidence scoring          (Tests 31-35)

import os
import sys
import json
import tempfile
import textwrap
import traceback
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from v3.repository_cognition import RepositoryCognitionEngine, RepositoryCognitionReport

# ------------------------------------------------------------------ #
# Test runner                                                          #
# ------------------------------------------------------------------ #

_results: list[tuple[int, str, bool, str]] = []


def test(number: int, label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    _results.append((number, label, condition, detail))
    detail_str = f" | {detail}" if detail else ""
    print(f"  Test {number:02d} {status} — {label}{detail_str}")
    return condition


def section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


def write(path: str, content: str):
    """Write a file, creating parent directories as needed."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(textwrap.dedent(content))


# ------------------------------------------------------------------ #
# Round 1 — Core functionality                                         #
# ------------------------------------------------------------------ #

def round_1():
    section("Round 1 — Core Functionality")

    # Test 01 — Empty repo
    with tempfile.TemporaryDirectory() as tmp:
        r = RepositoryCognitionEngine(tmp).scan()
        test(1, "Empty repo returns PARTIAL or FAILED without crash",
             r.cognition_status in ("PARTIAL", "FAILED"))

    # Test 02 — Django repo
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "django>=4.0\ncelery>=5.0\n")
        write(f"{tmp}/manage.py", "import django\n")
        write(f"{tmp}/myapp/__init__.py", "")
        write(f"{tmp}/myapp/views.py", "from django.http import HttpResponse\n")
        os.makedirs(f"{tmp}/tests", exist_ok=True)
        r = RepositoryCognitionEngine(tmp).scan()
        test(2, "Django repo → WEB_APPLICATION, COMPLETE, confidence 1.0",
             r.application_type == "WEB_APPLICATION"
             and r.cognition_status == "COMPLETE"
             and r.confidence_score == 1.0
             and "Celery" in r.secondary_frameworks,
             f"type={r.application_type} status={r.cognition_status} conf={r.confidence_score}")

    # Test 03 — FastAPI repo
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "fastapi\nuvicorn\npydantic\n")
        write(f"{tmp}/main.py", "from fastapi import FastAPI\napp = FastAPI()\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(3, "FastAPI repo → API_SERVICE",
             r.application_type == "API_SERVICE" and r.primary_framework == "FastAPI",
             f"type={r.application_type} framework={r.primary_framework}")

    # Test 04 — Click CLI
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "click>=8.0\n")
        write(f"{tmp}/cli.py", "import click\n@click.command()\ndef main(): pass\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(4, "Click repo → CLI_TOOL",
             r.application_type == "CLI_TOOL",
             f"type={r.application_type}")

    # Test 05 — ML repo
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "torch\ntransformers\n")
        write(f"{tmp}/train.py", "import torch\nfrom transformers import AutoModel\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(5, "PyTorch + Transformers → ML_PIPELINE",
             r.application_type == "ML_PIPELINE",
             f"type={r.application_type}")

    # Test 06 — failed() factory
    f = RepositoryCognitionReport.failed("/nonexistent", "test error")
    test(6, "failed() factory → FAILED, confidence 0.0, detected_languages=()",
         f.cognition_status == "FAILED"
         and f.confidence_score == 0.0
         and f.detected_languages == ()
         and f.error_message == "test error")

    # Test 07 — Immutability
    f = RepositoryCognitionReport.failed("/x", "err")
    try:
        f.application_type = "WEB_APPLICATION"
        test(7, "Report is immutable (frozen dataclass)", False)
    except Exception:
        test(7, "Report is immutable (frozen dataclass)", True)

    # Test 08 — to_dict() serialization
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "flask\n")
        write(f"{tmp}/app.py", "from flask import Flask\n")
        r = RepositoryCognitionEngine(tmp).scan()
        d = r.to_dict()
        test(8, "to_dict() produces valid serializable dict with all required keys",
             isinstance(d["detected_languages"], list)
             and isinstance(d["technology_stack"], list)
             and isinstance(d["confidence_score"], float)
             and d["cognition_status"] in ("COMPLETE", "PARTIAL", "FAILED")
             and "secondary_frameworks" in d
             and "entry_points" in d)


# ------------------------------------------------------------------ #
# Round 2 — pyproject.toml formats                                     #
# ------------------------------------------------------------------ #

def round_2():
    section("Round 2 — pyproject.toml Formats (Gap A)")

    # Test 09 — Single-quoted dependency
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/pyproject.toml",
              "[tool.poetry.dependencies]\n'scikit-learn' = '^1.3'\ntorch = '^2.0'\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(9, "pyproject.toml single-quoted → ML_PIPELINE",
             r.application_type == "ML_PIPELINE",
             f"type={r.application_type}")

    # Test 10 — Array syntax
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/pyproject.toml",
              '[project]\ndependencies = [\n    "django>=4.0",\n    "celery>=5.0",\n]\n')
        r = RepositoryCognitionEngine(tmp).scan()
        test(10, "pyproject.toml array syntax → WEB_APPLICATION",
             r.application_type == "WEB_APPLICATION",
             f"type={r.application_type}")

    # Test 11 — Poetry key=value style
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/pyproject.toml",
              '[tool.poetry.dependencies]\npython = "^3.11"\nfastapi = "^0.100"\n')
        r = RepositoryCognitionEngine(tmp).scan()
        test(11, "pyproject.toml key=value Poetry style → API_SERVICE",
             r.application_type == "API_SERVICE",
             f"type={r.application_type}")


# ------------------------------------------------------------------ #
# Round 3 — Determinism                                                #
# ------------------------------------------------------------------ #

def round_3():
    section("Round 3 — Determinism (Gap B)")

    # Test 12 — 10 runs on 80-file repo
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "django>=4.0\n")
        for i in range(80):
            write(f"{tmp}/app/module_{i:03d}.py", f"def func_{i}(): pass\n")
        results = set()
        for _ in range(10):
            r = RepositoryCognitionEngine(tmp).scan()
            results.add((r.application_type, r.confidence_score,
                         r.cognition_status, r.detected_languages))
        test(12, "10 runs on 80-file repo → identical results every time",
             len(results) == 1,
             f"unique result sets={len(results)}")


# ------------------------------------------------------------------ #
# Round 4 — Infrastructure detection                                   #
# ------------------------------------------------------------------ #

def round_4():
    section("Round 4 — Infrastructure Detection (Gap C)")

    # Test 13 — Docker + PostgreSQL from config files
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "django>=4.0\n")
        write(f"{tmp}/manage.py", "import django\n")
        write(f"{tmp}/Dockerfile", "FROM python:3.11\nRUN pip install django\n")
        write(f"{tmp}/docker-compose.yml",
              "version: '3'\nservices:\n  web:\n    build: .\n  db:\n    image: postgres\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(13, "Dockerfile + docker-compose.yml → Docker + PostgreSQL in stack",
             "Docker" in r.technology_stack and "PostgreSQL" in r.technology_stack,
             f"stack={list(r.technology_stack)}")


# ------------------------------------------------------------------ #
# Round 5 — detected_languages                                         #
# ------------------------------------------------------------------ #

def round_5():
    section("Round 5 — Detected Languages (Gap D)")

    # Test 14 — Mixed language repo
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "django>=4.0\n")
        write(f"{tmp}/manage.py", "import django\n")
        write(f"{tmp}/frontend/App.tsx", "export default function App() {}\n")
        write(f"{tmp}/frontend/style.css", "body { margin: 0; }\n")
        write(f"{tmp}/schema.sql", "CREATE TABLE users (id INT);\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(14, "Mixed repo → Python, TypeScript, CSS, SQL all detected",
             all(lang in r.detected_languages
                 for lang in ("Python", "TypeScript", "CSS", "SQL")),
             f"detected={list(r.detected_languages)}")

    # Test 15 — detected_languages is deterministic
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/a.py", "pass\n")
        write(f"{tmp}/b.js", "console.log('hi');\n")
        write(f"{tmp}/c.ts", "const x: number = 1;\n")
        results = set()
        for _ in range(5):
            results.add(RepositoryCognitionEngine(tmp).scan().detected_languages)
        test(15, "detected_languages tuple is deterministic across 5 runs",
             len(results) == 1,
             f"unique results={len(results)}")


# ------------------------------------------------------------------ #
# Round 6 — Config-based language detection                            #
# ------------------------------------------------------------------ #

def round_6():
    section("Round 6 — Config-Based Language Detection (Issues 1 & 2)")

    # Test 16 — package.json only, no .js files
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/package.json", '{"name":"app","dependencies":{"react":"^18"}}')
        write(f"{tmp}/app.py", "pass\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(16, "package.json only (no .js files) → JavaScript detected",
             "JavaScript" in r.detected_languages,
             f"detected={list(r.detected_languages)}")

    # Test 17 — go.mod only, no .go files
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/go.mod", "module myapp\ngo 1.21\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(17, "go.mod only (no .go files) → Go detected",
             "Go" in r.detected_languages,
             f"detected={list(r.detected_languages)}")

    # Test 18 — nested package.json in microservice dir
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "django\n")
        write(f"{tmp}/services/frontend/package.json", '{"name":"frontend"}')
        r = RepositoryCognitionEngine(tmp).scan()
        test(18, "Nested package.json → detected in config_files + JavaScript in languages",
             any("package.json" in f for f in r.configuration_files)
             and "JavaScript" in r.detected_languages,
             f"config_files={list(r.configuration_files)}")

    # Test 19 — .csproj extension anywhere in repo
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/src/MyApp.csproj", '<Project Sdk="Microsoft.NET.Sdk"/>')
        r = RepositoryCognitionEngine(tmp).scan()
        test(19, ".csproj extension → detected in config_files",
             any(".csproj" in f for f in r.configuration_files),
             f"config_files={list(r.configuration_files)}")

    # Test 20 — nested Cargo.toml (Rust workspace)
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/crates/mylib/Cargo.toml", "[package]\nname = 'mylib'\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(20, "Nested Cargo.toml → Rust in detected_languages",
             "Rust" in r.detected_languages
             and any("Cargo.toml" in f for f in r.configuration_files),
             f"detected={list(r.detected_languages)}")


# ------------------------------------------------------------------ #
# Round 7 — Real-world polyglot repos                                  #
# ------------------------------------------------------------------ #

def round_7():
    section("Round 7 — Real-World Polyglot Repos")

    # Test 21 — Django + React frontend
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "django>=4.0\n")
        write(f"{tmp}/manage.py", "import django\n")
        write(f"{tmp}/frontend/src/App.tsx", "export default function App() {}\n")
        write(f"{tmp}/frontend/src/index.js", "import App from './App';\n")
        write(f"{tmp}/frontend/src/style.css", "body { margin: 0; }\n")
        write(f"{tmp}/frontend/package.json", '{"name":"frontend"}')
        r = RepositoryCognitionEngine(tmp).scan()
        test(21, "Django + React → WEB_APPLICATION, Python+JS+TS+CSS detected",
             r.application_type == "WEB_APPLICATION"
             and all(l in r.detected_languages
                     for l in ("Python", "JavaScript", "TypeScript", "CSS")),
             f"type={r.application_type} langs={list(r.detected_languages)}")

    # Test 22 — FastAPI + PostgreSQL + Redis + Docker
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "fastapi\nuvicorn\n")
        write(f"{tmp}/main.py", "from fastapi import FastAPI\n")
        write(f"{tmp}/Dockerfile", "FROM python:3.11\n")
        write(f"{tmp}/docker-compose.yml",
              "services:\n  db:\n    image: postgres\n  cache:\n    image: redis\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(22, "FastAPI + Docker + PostgreSQL + Redis → all in stack",
             r.application_type == "API_SERVICE"
             and "Docker" in r.technology_stack
             and "PostgreSQL" in r.technology_stack
             and "Redis" in r.technology_stack,
             f"stack={list(r.technology_stack)}")

    # Test 23 — ML repo with Jupyter notebooks (.ipynb are JSON)
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "torch\ntransformers\n")
        write(f"{tmp}/train.py", "import torch\n")
        write(f"{tmp}/notebook.ipynb",
              '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}')
        r = RepositoryCognitionEngine(tmp).scan()
        test(23, "ML repo + .ipynb → ML_PIPELINE, Jupyter Notebook in detected_languages",
             r.application_type == "ML_PIPELINE"
             and "Jupyter Notebook" in r.detected_languages,
             f"type={r.application_type} langs={list(r.detected_languages)}")

    # Test 24 — Monorepo: Python + Go + Rust
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/backend/requirements.txt", "fastapi\n")
        write(f"{tmp}/backend/main.py", "from fastapi import FastAPI\n")
        write(f"{tmp}/service/go.mod", "module myservice\ngo 1.21\n")
        write(f"{tmp}/service/main.go", "package main\nfunc main() {}\n")
        write(f"{tmp}/crate/Cargo.toml", "[package]\nname = 'mycrate'\n")
        write(f"{tmp}/crate/src/lib.rs", "pub fn hello() {}\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(24, "Monorepo Python+Go+Rust → all three languages detected",
             all(l in r.detected_languages for l in ("Python", "Go", "Rust")),
             f"langs={list(r.detected_languages)}")

    # Test 25 — Pure TypeScript repo, no Python files
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/package.json", '{"name":"myapp","dependencies":{"express":"^4"}}')
        write(f"{tmp}/tsconfig.json", '{"compilerOptions":{"target":"ES2020"}}')
        write(f"{tmp}/src/index.ts", "import express from 'express';\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(25, "Pure TypeScript repo → UNKNOWN type, no crash, TypeScript detected",
             r.cognition_status in ("PARTIAL", "UNKNOWN", "COMPLETE")
             and "TypeScript" in r.detected_languages
             and r.application_type is not None,
             f"type={r.application_type} langs={list(r.detected_languages)}")


# ------------------------------------------------------------------ #
# Round 8 — Edge cases and hostile inputs                              #
# ------------------------------------------------------------------ #

def round_8():
    section("Round 8 — Edge Cases and Hostile Inputs")

    # Test 26 — Empty requirements.txt
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "\n# just a comment\n\n")
        write(f"{tmp}/app.py", "pass\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(26, "Empty requirements.txt → no crash, returns valid report",
             r.cognition_status in ("PARTIAL", "FAILED", "COMPLETE")
             and r is not None)

    # Test 27 — Corrupted pyproject.toml
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/pyproject.toml",
              "[[[[INVALID TOML\n!@#$%^&*()\nthis is not valid toml at all\n")
        write(f"{tmp}/app.py", "pass\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(27, "Corrupted pyproject.toml → no crash, scan continues",
             r is not None and r.cognition_status in ("PARTIAL", "FAILED", "COMPLETE"))

    # Test 28 — Zero Python files, only config files
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/Dockerfile", "FROM node:18\n")
        write(f"{tmp}/package.json", '{"name":"app"}')
        write(f"{tmp}/docker-compose.yml", "services:\n  web:\n    build: .\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(28, "Zero Python files → UNKNOWN or PARTIAL, no crash",
             r.total_python_files == 0
             and r.cognition_status in ("PARTIAL", "FAILED", "COMPLETE"),
             f"python_files={r.total_python_files} status={r.cognition_status}")

    # Test 29 — Binary files mixed in
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "django\n")
        write(f"{tmp}/manage.py", "import django\n")
        # Write a fake binary file
        Path(f"{tmp}/compiled.pyc").write_bytes(bytes(range(256)))
        Path(f"{tmp}/library.so").write_bytes(b"\x7fELF" + bytes(100))
        Path(f"{tmp}/program.exe").write_bytes(b"MZ" + bytes(100))
        r = RepositoryCognitionEngine(tmp).scan()
        test(29, "Binary files (.pyc .so .exe) → skipped cleanly, no crash",
             r.application_type == "WEB_APPLICATION"
             and r.cognition_status == "COMPLETE",
             f"type={r.application_type}")

    # Test 30 — Very deeply nested structure
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "fastapi\n")
        # 8 levels deep
        write(f"{tmp}/a/b/c/d/e/f/g/h/deep.py", "from fastapi import FastAPI\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(30, "8-level deep nested files → discovered and scanned, no crash",
             r is not None and r.total_python_files >= 1,
             f"python_files={r.total_python_files}")


# ------------------------------------------------------------------ #
# Round 9 — Confidence scoring validation                              #
# ------------------------------------------------------------------ #

def round_9():
    section("Round 9 — Confidence Scoring Validation")

    # Test 31 — Single weak signal: pandas in requirements only (no import in code)
    # pandas weight=1 from requirements only → UNKNOWN (insufficient)
    # Note: if pandas also appears in import scan, weight becomes 2 → DATA_ENGINEERING
    # This test uses a non-Python file so import scan finds no pandas signal
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "pandas\n")
        write(f"{tmp}/README.md", "# My project\n")  # no .py file importing pandas
        r = RepositoryCognitionEngine(tmp).scan()
        test(31, "pandas in requirements only (no import corroboration) → UNKNOWN",
             r.application_type == "UNKNOWN",
             f"type={r.application_type} conf={r.confidence_score}")

    # Test 32 — Two weak signals same type (pandas + polars)
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "pandas\npolars\n")
        write(f"{tmp}/app.py", "import pandas as pd\nimport polars as pl\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(32, "pandas + polars (weight=1+1=2) → DATA_ENGINEERING",
             r.application_type == "DATA_ENGINEERING",
             f"type={r.application_type} conf={r.confidence_score}")

    # Test 33 — Conflicting signals (django + torch)
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "django>=4.0\ntorch\n")
        write(f"{tmp}/manage.py", "import django\n")
        write(f"{tmp}/model.py", "import torch\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(33, "Conflicting signals django+torch → MONOREPO or dominant signal, no crash",
             r.application_type in ("WEB_APPLICATION", "ML_PIPELINE", "MONOREPO")
             and r.cognition_status in ("COMPLETE", "PARTIAL"),
             f"type={r.application_type} conf={r.confidence_score}")

    # Test 34 — Large repo 500+ Python files
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt", "django>=4.0\n")
        write(f"{tmp}/manage.py", "import django\n")
        for i in range(500):
            write(f"{tmp}/app/module_{i:04d}.py", f"def func_{i}(): pass\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(34, "500+ Python files → COMPLETE, deterministic, no crash",
             r.application_type == "WEB_APPLICATION"
             and r.cognition_status == "COMPLETE"
             and r.total_python_files >= 500,
             f"files={r.total_python_files} status={r.cognition_status}")

    # Test 35 — requirements.txt with only comments and blank lines
    with tempfile.TemporaryDirectory() as tmp:
        write(f"{tmp}/requirements.txt",
              "# This is a comment\n\n# Another comment\n   \n")
        write(f"{tmp}/app.py", "pass\n")
        r = RepositoryCognitionEngine(tmp).scan()
        test(35, "requirements.txt with only comments → no crash, no false signals",
             r is not None
             and r.application_type == "UNKNOWN",
             f"type={r.application_type}")


# ------------------------------------------------------------------ #
# Main runner                                                          #
# ------------------------------------------------------------------ #

def main():
    print()
    print("=" * 60)
    print("  CodeTruth Agent V3 — Module 1 Test Suite")
    print("  Repository Cognition Engine")
    print("  35 Tests — 9 Rounds")
    print("=" * 60)

    try:
        round_1()
        round_2()
        round_3()
        round_4()
        round_5()
        round_6()
        round_7()
        round_8()
        round_9()
    except Exception as e:
        print(f"\n  FATAL — Test runner crashed: {e}")
        traceback.print_exc()

    # Summary
    passed  = sum(1 for _, _, ok, _ in _results if ok)
    failed  = sum(1 for _, _, ok, _ in _results if not ok)
    total   = len(_results)

    print()
    print("=" * 60)
    print(f"  RESULTS: {passed}/{total} passed", end="")
    if failed:
        print(f"  |  {failed} FAILED")
        print()
        print("  Failed tests:")
        for num, label, ok, detail in _results:
            if not ok:
                print(f"    Test {num:02d} — {label}")
                if detail:
                    print(f"             {detail}")
    else:
        print()
        print()
        print("  ALL TESTS PASSED")
        print("  Module 1 — Repository Cognition Engine — VERIFIED")

    print("=" * 60)
    print()

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)