"""
run_scenario_uat.py - CodeTruth ENGINEERING-SCENARIO UAT/SIT launcher (Phase 5),
DATA-DRIVEN.

ONE generic engine + ONE generic check library + per-repository JSON PROFILES.
The engine never changes to add a repository; you write a new profile that freezes
that repo's verified targets and expected values as DATA.

Adding a repository:
  1. run the diagnostics once to observe the verified outputs,
  2. freeze those outputs into profiles/<repo>.json,
  3. re-run this launcher with --repo-profile <repo>,
  4. collect the evidence pack.

Scenario kinds (generic, parametrized by profile data):
  health         - repository health verdict (integrity, not coverage)
  impact_method  - change impact for a method (engine who_calls/impact_of)
  dead_code      - dead-code CANDIDATES (bounded, never a verdict)
  impact_class   - class impact / safe refactoring (depends_on_class)
  change_impact  - change impact via the FLAGSHIP tool (change_impact.analyze)

USAGE:
    python run_scenario_uat.py --repo-profile flask  "C:\\repos\\v3\\flask"
    python run_scenario_uat.py --repo-profile django "C:\\repos\\v3\\django"
    python run_scenario_uat.py --profile C:\\path\\to\\custom.json "<repo>"
    python run_scenario_uat.py --repo-profile flask --list

Must live beside run_module_uat.py, run_codetruth.py, codetruth_report.py,
run_m*.py; profiles live in ./profiles/<name>.json .
"""
import sys
import os
import glob
import importlib.util
from pathlib import Path


# ---------------------------------------------------------------------------
# Location-robust bootstrap, then reuse the shared UAT engine.
# ---------------------------------------------------------------------------
def _find_codetruth_root(start: Path) -> Path:
    env = os.environ.get("CODETRUTH_ROOT")
    if env and (Path(env) / "v3" / "repository_cognition").is_dir():
        return Path(env)
    for parent in [start, *start.parents]:
        if (parent / "v3" / "repository_cognition").is_dir():
            return parent
    return start.parent


_THIS_DIR = Path(__file__).resolve().parent
CODETRUTH_ROOT = _find_codetruth_root(_THIS_DIR)
os.environ["CODETRUTH_ROOT"] = str(CODETRUTH_ROOT)
sys.path.insert(0, str(CODETRUTH_ROOT))
sys.path.insert(0, str(CODETRUTH_ROOT / "v3"))
sys.path.insert(0, str(_THIS_DIR))

import run_module_uat as engine
TestSpec = engine.TestSpec


# ===========================================================================
# RUNNER HOOKS  (generic; parametrized only by target - never by expectations)
# ===========================================================================
def _runner_health(repo, force):
    import run_codetruth
    from codetruth_report import _health, generate
    rep = run_codetruth.run_platform(repo, force=force)
    if rep.get("status") != "COMPLETE":
        return rep
    rating, risk, metrics = _health(rep.get("module2", {}), rep.get("module3", {}))
    out = {"status": "COMPLETE", "gate": rep.get("gate"),
           "health_rating": rating, "risk_level": risk,
           "guesses": metrics.get("guesses"),
           "uncategorized_declines": metrics.get("uncategorized_declines"),
           "metrics": metrics}
    try:
        out["_artifacts"] = {"assessment_report.md": generate(repo)}
    except Exception as e:
        out["_artifacts"] = {"assessment_report.md": f"(report error: {type(e).__name__}: {e})"}
    return out


def _make_impact_runner(target):
    def _run(repo, force):
        from v3.repository_reasoning.reasoning_engine import ReasoningEngine
        from v3.repository_reasoning import reasoning_queries as RQ
        fwd = ReasoningEngine(repo).resolve()["call_index"]
        rev = RQ.build_reverse_index(fwd)
        who = RQ.who_calls(target, rev)
        imp = RQ.impact_of(target, rev)
        dc = who.get("direct_callers", []) if isinstance(who, dict) else None
        ac = imp.get("affected_callers", []) if isinstance(imp, dict) else None
        return {"target": target,
                "resolved": isinstance(who, dict) and isinstance(imp, dict),
                "direct_callers": dc,
                "direct_count_field": who.get("count") if isinstance(who, dict) else None,
                "affected_callers": ac,
                "impact_count_field": imp.get("count") if isinstance(imp, dict) else None}
    return _run


def _runner_dead_code(repo, force):
    from v3.repository_reasoning.reasoning_engine import ReasoningEngine
    from v3.repository_reasoning import reasoning_queries as RQ
    fwd = ReasoningEngine(repo).resolve()["call_index"]
    rev = RQ.build_reverse_index(fwd)
    return RQ.dead_code(fwd, rev)


def _make_class_impact_runner(target):
    def _run(repo, force):
        from v3.repository_reasoning.reasoning_engine import ReasoningEngine
        from v3.repository_reasoning import reasoning_queries as RQ
        fwd = ReasoningEngine(repo).resolve()["call_index"]
        rev = RQ.build_reverse_index(fwd)
        ans = RQ.depends_on_class(target, fwd, rev)
        return ans if isinstance(ans, dict) else {"query": "depends_on_class", "_raw": ans}
    return _run


def _make_flagship_impact_runner(target):
    def _run(repo, force):
        from v3.repository_reasoning.change_impact import analyze
        return analyze(repo, target)
    return _run


def _make_truth_boundary_runner(target):
    def _run(repo, force):
        from v3.repository_reasoning.truth_boundary_demo import classify
        return classify(repo, target)
    return _run


# ===========================================================================
# GENERIC CHECK PRIMITIVES  (parametrized by DATA from the profile)
# ===========================================================================
def _get(r, *path, default=None):
    cur = r
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p, default)
    return cur


# -- health --
def _c_health_status(r):
    return r.get("status") == "COMPLETE", f"status={r.get('status')}"


def _c_health_rating(expected):
    def _c(r):
        return r.get("health_rating") == expected, \
            f"health_rating={r.get('health_rating')} (expected {expected}, risk={r.get('risk_level')})"
    return _c


def _c_health_zero_guesses(r):
    return r.get("guesses") == 0, f"guesses={r.get('guesses')}"


def _c_health_categorized(r):
    return r.get("uncategorized_declines") == 0, f"uncategorized_declines={r.get('uncategorized_declines')}"


# -- impact_method (engine-direct) --
def _c_im_resolved(r):
    return bool(r.get("resolved")), f"resolved={r.get('resolved')} target={r.get('target')}"


def _c_im_target(expected):
    def _c(r):
        return r.get("target") == expected, f"target={r.get('target')} (expected {expected})"
    return _c


def _c_im_direct_consistent(r):
    dc, cf = r.get("direct_callers"), r.get("direct_count_field")
    ok = isinstance(dc, list) and (cf is None or cf == len(dc))
    return ok, f"direct_n={len(dc) if isinstance(dc, list) else 'NA'}, count_field={cf}"


def _c_im_impact_consistent(r):
    ac, cf = r.get("affected_callers"), r.get("impact_count_field")
    ok = isinstance(ac, list) and (cf is None or cf == len(ac))
    return ok, f"affected_n={len(ac) if isinstance(ac, list) else 'NA'}, count_field={cf}"


def _c_im_direct_exact(expected_list):
    def _c(r):
        dc = r.get("direct_callers")
        ok = isinstance(dc, list) and sorted(dc) == sorted(expected_list)
        return ok, f"direct_callers={dc} (expected {expected_list}; order-independent)"
    return _c


def _c_im_affected_count(n):
    def _c(r):
        ac = r.get("affected_callers")
        return isinstance(ac, list) and len(ac) == n, \
            f"affected_count={len(ac) if isinstance(ac, list) else 'NA'} (expected {n})"
    return _c


# -- dead_code --
def _c_dc_query(r):
    return r.get("query") == "dead_code", f"query={r.get('query')}"


def _c_dc_candidates_list(r):
    c = r.get("candidates")
    return isinstance(c, list), f"candidates_is_list={isinstance(c, list)}, n={len(c) if isinstance(c, list) else 'NA'}"


def _c_dc_count_consistent(r):
    c, cnt = r.get("candidates"), r.get("count")
    ok = isinstance(cnt, int) and isinstance(c, list) and cnt == len(c)
    return ok, f"count={cnt}, len(candidates)={len(c) if isinstance(c, list) else 'NA'}"


def _c_dc_labeled(r):
    return r.get("label") == "CANDIDATES", f"label={r.get('label')}"


def _c_dc_boundary(r):
    return bool(r.get("boundary")), f"boundary_present={bool(r.get('boundary'))}"


def _c_dc_candidate_count(n):
    def _c(r):
        cnt = r.get("count")
        return cnt == n, f"count={cnt} (expected {n})"
    return _c


# -- impact_class (depends_on_class) --
def _c_cls_query(r):
    return isinstance(r, dict) and r.get("query") == "depends_on_class", \
        f"query={r.get('query') if isinstance(r, dict) else type(r).__name__}"


def _c_cls_target(expected):
    def _c(r):
        return r.get("target") == expected, f"target={r.get('target')} (expected {expected})"
    return _c


def _c_cls_lists(r):
    m, e = r.get("methods"), r.get("external_dependents")
    ok = isinstance(m, list) and isinstance(e, list)
    return ok, (f"methods_is_list={isinstance(m, list)}(n={len(m) if isinstance(m, list) else 'NA'}), "
                f"external_is_list={isinstance(e, list)}(n={len(e) if isinstance(e, list) else 'NA'})")


def _c_cls_boundary(r):
    return bool(r.get("boundary")), f"boundary_present={bool(r.get('boundary'))}"


def _c_cls_count_consistent(r):
    e, cnt = r.get("external_dependents"), r.get("count")
    ok = isinstance(e, list) and isinstance(cnt, int) and cnt == len(e)
    return ok, f"count={cnt}, external_dependents_n={len(e) if isinstance(e, list) else 'NA'}"


def _c_cls_external_count(n):
    def _c(r):
        cnt = r.get("count")
        return cnt == n, f"external_dependents count={cnt} (expected {n})"
    return _c


def _c_cls_methods_count(n):
    def _c(r):
        m = r.get("methods")
        return isinstance(m, list) and len(m) == n, \
            f"methods_n={len(m) if isinstance(m, list) else 'NA'} (expected {n})"
    return _c


# -- change_impact (flagship analyze) --
def _c_fs_no_error(r):
    return isinstance(r, dict) and "error" not in r, \
        f"error={r.get('error', 'none') if isinstance(r, dict) else type(r).__name__}"


def _c_fs_target(expected):
    def _c(r):
        return r.get("target") == expected, f"resolved target={r.get('target')} (expected {expected})"
    return _c


def _c_fs_direct(expected_list):
    def _c(r):
        dc = r.get("direct_callers") or []
        ok = sorted(dc) == sorted(expected_list) and r.get("direct_count") == len(expected_list)
        return ok, f"direct_callers={dc}, direct_count={r.get('direct_count')} (expected {expected_list}; order-independent)"
    return _c


def _c_fs_affected(n):
    def _c(r):
        ac = r.get("affected_callers") or []
        return r.get("affected_count") == n and len(ac) == n, \
            f"affected_count={r.get('affected_count')}, affected_n={len(ac)} (expected {n})"
    return _c


def _c_fs_zero_guesses(r):
    g = _get(r, "scope", "guesses")
    return g == 0, f"guesses={g}"


# ===========================================================================
# PER-KIND CHECK BUILDERS  (assemble parametrized checks from profile data)
# ===========================================================================
def _build_health(s):
    exp = s.get("expected", {})
    rating = exp.get("rating", "SOUND")
    return [
        ("health_completed", "status == COMPLETE", _c_health_status),
        ("health_rating", f"health_rating == {rating}", _c_health_rating(rating)),
        ("health_zero_guesses", "guesses == 0", _c_health_zero_guesses),
        ("health_all_declines_categorized", "uncategorized_declines == 0", _c_health_categorized),
    ]


def _build_impact_method(s):
    exp = s.get("expected", {})
    checks = [
        ("impact_resolved", "who_calls and impact_of both returned", _c_im_resolved),
        ("impact_target", f"target IS {s['target']}", _c_im_target(s["target"])),
        ("impact_direct_consistent", "direct_callers length == who_calls count", _c_im_direct_consistent),
        ("impact_reachable_consistent", "affected_callers length == impact_of count", _c_im_impact_consistent),
    ]
    if "direct_callers" in exp:
        checks.append(("impact_direct_identity", f"direct_callers == {exp['direct_callers']}",
                       _c_im_direct_exact(exp["direct_callers"])))
    if "affected_count" in exp:
        checks.append(("impact_affected_count", f"affected_count == {exp['affected_count']}",
                       _c_im_affected_count(exp["affected_count"])))
    return checks


def _build_dead_code(s):
    exp = s.get("expected", {})
    checks = [
        ("deadcode_query", "query == dead_code", _c_dc_query),
        ("deadcode_candidates_list", "candidates is a list", _c_dc_candidates_list),
        ("deadcode_count_consistent", "count == len(candidates)", _c_dc_count_consistent),
        ("deadcode_labeled_candidates", "label == CANDIDATES (not a verdict)", _c_dc_labeled),
        ("deadcode_boundary_stated", "boundary note present (Truth Boundary)", _c_dc_boundary),
    ]
    if "candidate_count" in exp:
        checks.append(("deadcode_candidate_count", f"count == {exp['candidate_count']}",
                       _c_dc_candidate_count(exp["candidate_count"])))
    return checks


def _build_impact_class(s):
    exp = s.get("expected", {})
    checks = [
        ("class_query", "query == depends_on_class", _c_cls_query),
        ("class_target_echoed", f"target echoes {s['target']}", _c_cls_target(s["target"])),
        ("class_lists_present", "methods and external_dependents are lists", _c_cls_lists),
        ("class_boundary_stated", "boundary note present (Truth Boundary)", _c_cls_boundary),
        ("class_count_consistent", "count == number of external_dependents", _c_cls_count_consistent),
    ]
    if "external_dependents_count" in exp:
        checks.append(("class_external_count", f"external dependents == {exp['external_dependents_count']}",
                       _c_cls_external_count(exp["external_dependents_count"])))
    if "methods_count" in exp:
        checks.append(("class_methods_count", f"methods == {exp['methods_count']}",
                       _c_cls_methods_count(exp["methods_count"])))
    return checks


def _build_change_impact(s):
    exp = s.get("expected", {})
    checks = [
        ("flagship_no_error", "analyze() returned without error", _c_fs_no_error),
        ("flagship_target", f"resolved target IS {s['target']}", _c_fs_target(s["target"])),
    ]
    if "direct_callers" in exp:
        checks.append(("flagship_direct_identity", f"direct_callers == {exp['direct_callers']}",
                       _c_fs_direct(exp["direct_callers"])))
    if "affected_count" in exp:
        checks.append(("flagship_affected_count", f"affected_count == {exp['affected_count']}",
                       _c_fs_affected(exp["affected_count"])))
    checks.append(("flagship_zero_guesses", "scope.guesses == 0", _c_fs_zero_guesses))
    return checks


# -- truth_boundary (front-door demo) --
def _c_tb_resolved(r):
    v = r.get("verdict")
    return v in ("VERIFIED_IMPACT", "KNOWN_UNKNOWN"), f"verdict={v}"


def _c_tb_guesses(r):
    g = r.get("guesses")
    return g == 0, f"guesses={g}"


def _c_tb_no_safe_claim(r):
    # THE load-bearing assertion: CodeTruth's reading must never AFFIRM the method
    # is "safe to delete". (The honest reading may say "NOT a safety verdict" - that
    # negated form is fine; we ban only the affirmative deletion claim.)
    reading = (r.get("codetruth_reading") or "").lower()
    has = "safe to delete" in reading
    return not has, f"'safe to delete' asserted in CodeTruth reading? {'YES (VIOLATION)' if has else 'no'}"


def _c_tb_verdict(expected):
    def _c(r):
        return r.get("verdict") == expected, f"verdict={r.get('verdict')} (expected {expected})"
    return _c


def _c_tb_direct(expected_list):
    def _c(r):
        dc = r.get("direct_callers")
        ok = isinstance(dc, list) and sorted(dc) == sorted(expected_list)
        return ok, f"direct_callers={dc} (expected {expected_list}; order-independent)"
    return _c


def _c_tb_direct_count(n):
    def _c(r):
        return r.get("direct_count") == n, f"direct_count={r.get('direct_count')} (expected {n})"
    return _c


def _build_truth_boundary(s):
    exp = s.get("expected", {})
    checks = [
        ("tb_resolved", "target resolved (verdict not NOT_FOUND)", _c_tb_resolved),
        ("tb_guesses_zero", "guesses == 0", _c_tb_guesses),
        ("tb_never_asserts_safe", "CodeTruth reading never asserts 'safe to delete'", _c_tb_no_safe_claim),
    ]
    if "verdict" in exp:
        checks.append(("tb_verdict", f"verdict == {exp['verdict']}", _c_tb_verdict(exp["verdict"])))
    if "direct_callers" in exp:
        checks.append(("tb_direct_identity", f"direct_callers == {exp['direct_callers']}",
                       _c_tb_direct(exp["direct_callers"])))
    if "direct_count" in exp:
        checks.append(("tb_direct_count", f"direct_count == {exp['direct_count']}",
                       _c_tb_direct_count(exp["direct_count"])))
    return checks


# ===========================================================================
# KIND REGISTRY: kind -> (runner_builder(scenario), checks_builder(scenario),
#                         needs_target, default_requirement)
# ===========================================================================
KINDS = {
    "health": {
        "runner": lambda s: _runner_health,
        "checks": _build_health,
        "needs_target": False,
        "requirement": "Phase 5 - Engineering Scenario: Repository Health Check.",
        "entrypoint": "codetruth_report._health + generate (over run_platform)",
    },
    "impact_method": {
        "runner": lambda s: _make_impact_runner(s["target"]),
        "checks": _build_impact_method,
        "needs_target": True,
        "requirement": "Phase 5 - Engineering Scenario: Change Impact (method).",
        "entrypoint": "reasoning_queries.who_calls / impact_of (engine-direct)",
    },
    "dead_code": {
        "runner": lambda s: _runner_dead_code,
        "checks": _build_dead_code,
        "needs_target": False,
        "requirement": "Phase 5 - Engineering Scenario: Dead Code Candidates / Technical Debt.",
        "entrypoint": "reasoning_queries.dead_code",
    },
    "impact_class": {
        "runner": lambda s: _make_class_impact_runner(s["target"]),
        "checks": _build_impact_class,
        "needs_target": True,
        "requirement": "Phase 5 - Engineering Scenario: Safe Refactoring (class impact).",
        "entrypoint": "reasoning_queries.depends_on_class (engine-direct)",
    },
    "change_impact": {
        "runner": lambda s: _make_flagship_impact_runner(s["target"]),
        "checks": _build_change_impact,
        "needs_target": True,
        "requirement": "Phase 5 - Engineering Scenario: Change Impact (flagship tool).",
        "entrypoint": "v3.repository_reasoning.change_impact.analyze",
    },
    "truth_boundary": {
        "runner": lambda s: _make_truth_boundary_runner(s["target"]),
        "checks": _build_truth_boundary,
        "needs_target": True,
        "requirement": "Phase 5 - Product Front-Door: Zero-Guess Truth Boundary demonstration.",
        "entrypoint": "v3.repository_reasoning.truth_boundary_demo.classify",
    },
}


def _default_scenario_text(s):
    kind, tgt = s["kind"], s.get("target", "")
    exp = s.get("expected", {})
    if kind == "health":
        return ("GIVEN an unfamiliar repository, WHEN a developer asks whether an "
                "automated analysis can be trusted, THEN the health verdict is SOUND "
                "iff zero fabrications and every decline categorized (integrity, not coverage).")
    if kind == "impact_method":
        return (f"GIVEN a developer about to change {tgt}, WHEN they ask 'what verifiably "
                f"breaks?', THEN CodeTruth returns the verified direct callers and "
                f"call-reachable set - identity-checked, no guessing.")
    if kind == "dead_code":
        return ("GIVEN a repository accumulating unused code, WHEN a developer asks 'what "
                "looks unused?', THEN CodeTruth returns functions with no inbound internal "
                "edge, LABELED as CANDIDATES with an explicit boundary - not a deletion verdict.")
    if kind == "impact_class":
        return (f"GIVEN a developer about to refactor {tgt}, WHEN they ask 'what depends on "
                f"this class?', THEN CodeTruth returns the in-repo callers of its methods "
                f"(excluding its own), honestly reporting 0 when callers are internal/dynamic.")
    if kind == "change_impact":
        return (f"GIVEN a developer running the FLAGSHIP change_impact tool on {tgt}, WHEN "
                f"they ask 'what verifiably breaks?', THEN the tool reports exactly the "
                f"engine's verified answer (parity), with zero guesses.")
    if kind == "truth_boundary":
        return (f"GIVEN the front-door demo on {tgt}, WHEN it has 0 verified callers, THEN "
                f"CodeTruth reports KNOWN-UNKNOWN (never 'safe to delete'); when it has "
                f"callers, it reports them as verified edges - proving zero-guess behavior.")
    return f"Scenario {s['id']} ({kind})."


def _default_expected_text(s):
    exp = s.get("expected", {})
    parts = [f"kind={s['kind']}"]
    if s.get("target"):
        parts.append(f"target={s['target']}")
    for k, v in exp.items():
        parts.append(f"{k}={v}")
    parts.append("frozen before the run; identity/consistency-level checks.")
    return "; ".join(parts)


# ===========================================================================
# PROFILE LOADER: Python profile module -> [TestSpec]  (no engine edits per repo)
# A profile is profiles/<repo>.py defining a top-level PROFILE dict:
#     PROFILE = {"repo": "<name>", "tests": { "<ID>": {"kind":..., ...}, ... }}
# "tests" may be a dict keyed by id (recommended) or a list of dicts with "id".
# Python modules allow comments, shared constants, and helpers.
# ===========================================================================
def _load_profile_module(path):
    spec = importlib.util.spec_from_file_location(
        f"ct_profile_{Path(path).stem}", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "PROFILE") or not isinstance(mod.PROFILE, dict):
        raise ValueError(f"{path}: profile module must define a top-level PROFILE dict")
    return mod.PROFILE


def _normalize_tests(profile):
    tests = profile.get("tests", profile.get("scenarios"))
    if tests is None:
        return []
    if isinstance(tests, dict):
        out = []
        for tid, sc in tests.items():
            s = dict(sc)
            s.setdefault("id", tid)
            out.append(s)
        return out
    return [dict(s) for s in tests]


def load_profile(path):
    profile = _load_profile_module(path)
    repo_name = profile.get("repo", Path(path).stem)
    specs = []
    for s in _normalize_tests(profile):
        kind = s.get("kind")
        if kind not in KINDS:
            raise ValueError(f"{s.get('id', '?')}: unknown kind '{kind}' "
                             f"(known: {', '.join(KINDS)})")
        spec = KINDS[kind]
        if spec["needs_target"] and not s.get("target"):
            raise ValueError(f"{s.get('id', '?')}: kind '{kind}' requires a 'target'")
        specs.append(TestSpec(
            id=s["id"],
            objective=s.get("objective", f"{kind} scenario for {repo_name}"),
            requirement=s.get("requirement", spec["requirement"]),
            maturity=s.get("maturity", "Impl - Pending UAT"),
            entrypoint=s.get("entrypoint", spec["entrypoint"]),
            runner=spec["runner"](s),
            checks=spec["checks"](s),
            scenario=s.get("scenario", _default_scenario_text(s)),
            expected_result=s.get("expected_result", _default_expected_text(s)),
        ))
    return repo_name, specs


def _profiles_dir():
    return _THIS_DIR / "profiles"


def _available_profiles():
    names = []
    for p in glob.glob(str(_profiles_dir() / "*.py")):
        stem = Path(p).stem
        if not stem.startswith("_"):
            names.append(stem)
    return sorted(names)


def main(argv):
    argv = list(argv)
    profile_name, profile_path = "flask", None
    if "--repo-profile" in argv:
        i = argv.index("--repo-profile")
        if i + 1 < len(argv):
            profile_name = argv[i + 1]
            del argv[i:i + 2]
        else:
            del argv[i]
    if "--profile" in argv:
        i = argv.index("--profile")
        if i + 1 < len(argv):
            profile_path = argv[i + 1]
            del argv[i:i + 2]
        else:
            del argv[i]

    path = Path(profile_path) if profile_path else (_profiles_dir() / f"{profile_name}.py")
    if not path.exists():
        print(f"profile not found: {path}")
        print(f"available profiles: {', '.join(_available_profiles()) or '(none in ./profiles)'}")
        return 2
    try:
        repo_name, specs = load_profile(path)
    except Exception as e:
        print(f"profile load error ({path}): {type(e).__name__}: {e}")
        return 2
    if not specs:
        print(f"profile '{repo_name}' has no scenarios yet - freeze targets first.")
        return 2

    return engine.main(
        argv, tests=specs,
        title=f"CodeTruth engineering-scenario UAT/SIT launcher (Phase 5A: {repo_name})")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
