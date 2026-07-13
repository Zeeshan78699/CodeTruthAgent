r"""
CodeTruth Live — FastAPI backend (Layer 3a).

Wraps service.py over HTTP. Run locally:
    set CODETRUTH_ROOT=C:\AI_Project\CodeTruthAgent
    set CODETRUTH_CORPUS=C:\repos\v3
    python -m uvicorn app:app --reload --port 8000
Then open http://localhost:8000

Endpoints:
    GET  /                      -> the single-page UI
    GET  /api/curated          -> list curated instant-demo repos
    POST /api/analyze          -> run an analysis (mode: repo | method | class)
"""
import os, sys, traceback
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import service

# config from env (deployment-agnostic)
PROJECT_ROOT = os.environ.get("CODETRUTH_ROOT", r"C:\AI_Project\CodeTruthAgent")
CORPUS_DIR   = os.environ.get("CODETRUTH_CORPUS", r"C:\repos\v3")
CLONE_BASE   = os.environ.get("CODETRUTH_CLONE", os.path.join(_HERE, "_clones"))
os.makedirs(CLONE_BASE, exist_ok=True)

app = FastAPI(title="CodeTruth Live")


class AnalyzeReq(BaseModel):
    mode: str            # "repo" | "method" | "class" | "demo" | "deadcode" | "report"
    source: str          # "curated" | "url"
    repo: str = ""       # curated name OR github url
    target: str = ""     # method/class id (for method/class modes)
    force: bool = False  # proceed past a REVIEW_REQUIRED governance gate (repo mode)
    report_mode: str = "human"  # for mode="report": human | engineer | manager | ai


@app.get("/api/curated")
def curated():
    return {"repos": service.list_curated(CORPUS_DIR)}


class BrowseReq(BaseModel):
    path: str = ""


@app.post("/api/browse")
def browse(req: BrowseReq):
    """Local folder picker: list sub-directories of a path (LOCAL USE ONLY)."""
    return service.list_dirs(req.path)


@app.get("/api/pick_folder")
def pick_folder():
    """Open a NATIVE OS folder dialog on the server machine (LOCAL USE ONLY)."""
    try:
        path = service.pick_folder_native()
        if not path:
            return {"ok": False, "error": "No folder selected (or native dialog unavailable on this machine)."}
        return {"ok": True, "path": path}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def _resolve_repo(req: AnalyzeReq):
    """Return (repo_path, error, cleanup_path)."""
    cleanup = None
    if req.source == "curated":
        path = os.path.join(CORPUS_DIR, req.repo)
        if not os.path.isdir(path):
            return None, f"Curated repo '{req.repo}' not found.", None
    elif req.source == "url":
        path, err = service.clone_repo(req.repo, CLONE_BASE)
        if err:
            return None, err, None
        cleanup = path  # cleanup the clone after
    elif req.source == "local":
        # LOCAL USE ONLY: analyze a folder on this host in place (no clone).
        path, err = service.resolve_local(req.repo)
        if err:
            return None, err, None
    else:
        return None, "Unknown source.", None

    # ---- venv guard (all sources): Module 2 walks a virtual environment as
    # source and can hang. Refuse up front with a clear message. ----
    venvs = service.find_venvs(path)
    if venvs:
        names = ", ".join(sorted(os.path.basename(v) for v in venvs))
        if cleanup:
            try:
                import shutil
                shutil.rmtree(cleanup, ignore_errors=True)
            except Exception:
                pass
        return None, (f"Repository contains a virtual environment ({names}). "
                      f"CodeTruth analyzes your source, not installed dependencies "
                      f"— move the environment outside the project folder and try "
                      f"again."), None
    return path, None, cleanup


@app.post("/api/analyze")
def analyze(req: AnalyzeReq):
    import shutil
    repo_path, err, cleanup = _resolve_repo(req)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    try:
        if req.mode == "repo":
            md, meta = service.analyze_repository(
                PROJECT_ROOT, repo_path, force=req.force,
                display_name=(req.repo or None))   # show the user's input, not the temp clone path
            return {"ok": True, "markdown": md, **meta}
        elif req.mode == "method":
            if not req.target:
                return JSONResponse({"ok": False, "error": "target method required"}, status_code=400)
            md, _ = service.analyze_method(PROJECT_ROOT, repo_path, req.target,
                                           display_name=(req.repo or None))
        elif req.mode == "class":
            if not req.target:
                return JSONResponse({"ok": False, "error": "target class required"}, status_code=400)
            md, _ = service.analyze_class(PROJECT_ROOT, repo_path, req.target)
        elif req.mode == "demo":
            pop, emp = (service.demo_targets_for(req.repo)
                        if req.source == "curated" else (None, None))
            md, dmeta = service.truth_boundary_demo(PROJECT_ROOT, repo_path, pop, emp)
            # The demo is route-aware: for a stub/bridge language it returns the
            # pipeline's REAL status (e.g. rust -> REVIEW_REQUIRED). Do NOT
            # hardcode COMPLETE — that would report success on a refusal.
            dmeta = dmeta or {}
            return {"ok": True, "markdown": md,
                    "status": dmeta.get("status", "COMPLETE"),
                    "gate": None,
                    "module3_ran": dmeta.get("module3_ran", True),
                    "language": dmeta.get("language")}
        elif req.mode == "deadcode":
            md, _ = service.dead_code(PROJECT_ROOT, repo_path)
        elif req.mode == "report":
            md, rmeta = service.project_report(PROJECT_ROOT, repo_path,
                                               display_name=(req.repo or None),
                                               mode=req.report_mode)
            rmeta = rmeta or {}
            return {"ok": True, "markdown": md,
                    "status": rmeta.get("status", "COMPLETE"),
                    "gate": None,
                    "module3_ran": rmeta.get("module3_ran", True),
                    "language": rmeta.get("language"),
                    "report_json": rmeta.get("report_json")}
        else:
            return JSONResponse({"ok": False, "error": "unknown mode"}, status_code=400)
        # reasoning modes (method/class/deadcode) run Module 3 directly over the
        # verified graph — genuinely complete and zero-guess; they are not
        # governed by the M1 assessment gate.
        return {"ok": True, "markdown": md, "status": "COMPLETE",
                "gate": None, "module3_ran": True}
    except Exception as e:
        return JSONResponse({"ok": False,
                             "error": f"{type(e).__name__}: {e}",
                             "trace": traceback.format_exc()[-800:]}, status_code=500)
    finally:
        if cleanup and os.path.isdir(cleanup):
            shutil.rmtree(cleanup, ignore_errors=True)


class StructReq(BaseModel):
    source: str
    repo: str = ""


@app.post("/api/meta")
def meta(req: StructReq):
    import shutil
    ar = AnalyzeReq(mode="repo", source=req.source, repo=req.repo)
    repo_path, err, cleanup = _resolve_repo(ar)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    try:
        m = service.repo_meta(PROJECT_ROOT, repo_path)
        return {"ok": True, **m}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
    finally:
        if cleanup and os.path.isdir(cleanup):
            shutil.rmtree(cleanup, ignore_errors=True)


@app.post("/api/structure")
def structure(req: StructReq):
    import shutil
    ar = AnalyzeReq(mode="repo", source=req.source, repo=req.repo)
    repo_path, err, cleanup = _resolve_repo(ar)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    try:
        s = service.repo_structure(PROJECT_ROOT, repo_path)
        return {"ok": True, **s}
    except Exception as e:
        import traceback
        return JSONResponse({"ok": False, "error": f"{type(e).__name__}: {e}",
                             "trace": traceback.format_exc()[-800:]}, status_code=500)
    finally:
        if cleanup and os.path.isdir(cleanup):
            shutil.rmtree(cleanup, ignore_errors=True)


@app.get("/", response_class=HTMLResponse)
def index():
    with open(os.path.join(_HERE, "index.html"), encoding="utf-8") as f:
        return f.read()
