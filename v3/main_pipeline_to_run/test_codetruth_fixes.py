"""
test_codetruth_fixes.py — Tier-1 regression tests for CodeTruth report-layer / guard fixes.

These are DETERMINISTIC UNIT tests: they exercise the self-contained fix functions in
isolation (no live repo, no frozen reasoning engine, no network). Each test locks one
fix so a future change cannot silently regress it.

Scope (report-layer / guard only — the frozen reasoning core is NOT touched here):
  1. venv pre-flight guard            (service.find_venvs)
  2. detected-technologies guard      (codetruth_report._tech_display)
  3. guided not-found diagnosis       (change_impact._diagnose_missing_target)
  4. local folder picker listing      (service.list_dirs)

Run:  pytest test_codetruth_fixes.py -v
Set CODETRUTH_ROOT if your project root is not the default below.
"""
import os
import sys
import tempfile
import importlib

import pytest

# --- resolve module locations the same way the running app does -------------
# The app injects PROJECT_ROOT and PROJECT_ROOT/v3 onto sys.path (service._ensure_paths).
# codetruth_report.py lives at the ROOT; change_impact.py lives in v3/repository_reasoning;
# service.py lives beside this test (main_pipeline_to_run). Mirror that here so pytest,
# run standalone, finds each module in its canonical location.
_HERE = os.path.dirname(os.path.abspath(__file__))                     # ...\v3\main_pipeline_to_run
_ROOT = os.environ.get("CODETRUTH_ROOT",
                       os.path.abspath(os.path.join(_HERE, "..", ".."))) # ...\CodeTruthAgent
_V3 = os.path.join(_ROOT, "v3")
for _p in (_ROOT, _V3, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

service = importlib.import_module("service")
codetruth_report = importlib.import_module("codetruth_report")
change_impact = importlib.import_module("v3.repository_reasoning.change_impact")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _make_repo(with_venv_name=None, extra_dirs=()):
    """Create a temp repo with one .py file; optionally a venv dir (pyvenv.cfg)."""
    root = tempfile.mkdtemp()
    open(os.path.join(root, "app.py"), "w").write("x = 1\n")
    for d in extra_dirs:
        os.makedirs(os.path.join(root, d), exist_ok=True)
    if with_venv_name:
        vdir = os.path.join(root, with_venv_name)
        os.makedirs(os.path.join(vdir, "Lib", "site-packages"))
        open(os.path.join(vdir, "pyvenv.cfg"), "w").write("home = /usr\n")
        # a deep dependency file that WOULD blow the recursion limit if walked
        open(os.path.join(vdir, "Lib", "site-packages", "dep.py"), "w").write("y = 2\n")
    return root


# =========================================================================== #
# 1. venv pre-flight guard  — service.find_venvs
#    Fix: detect EVERY virtualenv by pyvenv.cfg (any name), never descend into it,
#    stay silent on clean repos. (Root cause of the M2 recursion hang.)
# =========================================================================== #
class TestVenvGuard:
    @pytest.mark.parametrize("name", [".venv", "venv", ".venv_hidden", "myenv", "env"])
    def test_detects_venv_of_any_name(self, name):
        repo = _make_repo(with_venv_name=name)
        found = service.find_venvs(repo)
        assert [os.path.basename(p) for p in found] == [name], \
            f"venv named {name!r} must be detected"

    def test_clean_repo_not_flagged(self):
        repo = _make_repo(extra_dirs=["src", "tests", "__pycache__"])
        assert service.find_venvs(repo) == [], "a repo with no venv must not be flagged"

    def test_pycache_alone_does_not_trip(self):
        repo = _make_repo()
        pc = os.path.join(repo, "__pycache__")
        os.makedirs(pc)
        open(os.path.join(pc, "app.cpython-311.pyc"), "w").write("")
        assert service.find_venvs(repo) == []

    def test_does_not_descend_into_venv(self):
        # a venv containing a nested pyvenv.cfg-like decoy: only the top venv is reported,
        # proving the guard stops at the venv and does not walk its tree.
        repo = _make_repo(with_venv_name=".venv")
        nested = os.path.join(repo, ".venv", "Lib", "inner")
        os.makedirs(nested)
        open(os.path.join(nested, "pyvenv.cfg"), "w").write("home=/x\n")
        found = [os.path.basename(p) for p in service.find_venvs(repo)]
        assert found == [".venv"], "guard must not descend into a venv's subtree"


# =========================================================================== #
# 2. detected-technologies guard — codetruth_report._tech_display
#    Fix: suppress the folder-name / clone-name fallback (never present a
#    non-detection as a finding), but PRESERVE a genuine framework — even for a
#    repo literally named after it, and even inside a clone dir.
# =========================================================================== #
class TestTechDisplay:
    def test_clone_folder_name_leak_suppressed(self):
        # the exact production bug: requests clone -> "Ctlive Caex6Oyz" at conf 0.75
        m1 = {"framework": "Ctlive Caex6Oyz", "application_type": "UNKNOWN", "confidence": 0.75}
        assert codetruth_report._tech_display(m1, "ctlive_caex6oyz") == "not detected"

    def test_unknown_zero_confidence_suppressed(self):
        m1 = {"framework": "none", "application_type": "UNKNOWN", "confidence": 0.0}
        assert codetruth_report._tech_display(m1, "x") == "not detected"

    def test_real_framework_preserved(self):
        m1 = {"framework": "Flask", "application_type": "ML_PIPELINE", "confidence": 1.0}
        assert codetruth_report._tech_display(m1, "Memory_System") == "Flask"

    def test_repo_named_after_its_framework_not_suppressed(self):
        # regression: a repo literally named "flask" whose framework IS Flask must show Flask
        m1 = {"framework": "Flask", "application_type": "WEB_APPLICATION", "confidence": 0.9}
        assert codetruth_report._tech_display(m1, "flask") == "Flask"

    def test_real_framework_inside_clone_dir_preserved(self):
        m1 = {"framework": "Flask", "application_type": "WEB_APPLICATION", "confidence": 0.9}
        assert codetruth_report._tech_display(m1, "ctlive_abc123") == "Flask"


# =========================================================================== #
# 3. guided not-found diagnosis — change_impact._diagnose_missing_target
#    Fix: replace the generic "not found" with an evidence-based reason
#    (empty index / target-module-absent / name-mismatch / not-parsed), stating
#    ONLY what is verified and never asserting an unproven cause.
# =========================================================================== #
class TestGuidedNotFound:
    FWD = {
        "flask.app.Flask.dispatch_request": [],
        "flask.ctx.AppContext.push": [],
        "flask.cli.CertParamType.convert": [],
        "examples.tutorial.blog.index": [],
        "tests.conftest.app": [],
    }

    def _d(self, q):
        return change_impact._diagnose_missing_target(q, self.FWD, {})

    def test_empty_index(self):
        msg = change_impact._diagnose_missing_target("any.thing", {}, {})
        assert "empty" in msg.lower()

    def test_target_module_absent(self):
        # the real screenshot case: memory_db method requested in the Flask index
        msg = self._d("memory_db.MemoryDB.search_semantic")
        assert "does not appear in the verified call index" in msg
        # states available modules as evidence
        for mod in ("flask", "examples", "tests"):
            assert mod in msg
        # honest wording: does NOT assert it belongs to another repo
        assert "belongs to a different repository" not in msg
        assert "Verify that you selected the correct repository or target method" in msg
        assert "Browse methods" in msg

    def test_name_or_prefix_mismatch(self):
        # top module present (flask), full name absent, leaf exists elsewhere
        msg = self._d("flask.wrong.path.dispatch_request")
        assert "different qualified name" in msg

    def test_genuinely_absent_leaf(self):
        msg = self._d("flask.app.Flask.this_method_does_not_exist")
        assert "not have been" in msg or "misspelled" in msg

    def test_never_fabricates(self):
        # the diagnosis is a plain string, never a fake analysis structure
        msg = self._d("memory_db.MemoryDB.search_semantic")
        assert isinstance(msg, str)
        assert "verified affected callers" not in msg.lower()


# =========================================================================== #
# 4. local folder picker — service.list_dirs
#    Fix: list immediate sub-directories with a parent, for the native/browse picker.
# =========================================================================== #
class TestListDirs:
    def test_lists_subdirs_with_parent(self):
        root = _make_repo(extra_dirs=["src", "tests"])
        r = service.list_dirs(root)
        names = {os.path.basename(p) for p in r["dirs"]}
        assert {"src", "tests"} <= names
        assert r["parent"] is not None
        assert os.path.basename(r["path"]) == os.path.basename(root)

    def test_nonexistent_path_no_crash(self):
        r = service.list_dirs(os.path.join(tempfile.gettempdir(), "definitely_not_here_xyz"))
        assert r["dirs"] == []


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))
