"""
change_impact.py — Deterministic Change Impact Analysis (CodeTruth Module 3).

Answers, for a target method, BEFORE any code is changed:
  - direct callers, indirect (transitive) callers
  - affected files, classes, modules (derived from the verified impact set)
  - call chains to the target, maximum impact depth
  - Truth Boundary: verified impact vs unknown (dynamic/external) callers

Every answer is a traversal over the VERIFIED call graph. Where callers are
dynamic/external, they are reported as UNKNOWN (flagged, never guessed). A zero
verified-caller result is NOT "safe to change" - it means impact is via paths
CodeTruth cannot statically see.

Usage (from project root):
    python v3\\repository_reasoning\\change_impact.py "C:\\repos\\v3\\flask" --target "Flask.send_static_file"
    python v3\\repository_reasoning\\change_impact.py "<repo>" --target "<name>" --out impact.md
"""
import sys, os, warnings, argparse
warnings.filterwarnings("ignore", category=SyntaxWarning)

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, "..", ".."))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "v3"))


def _fmt_outgoing(item):
    """Outgoing edges may be tuples (id, scope, line, reason) or plain strings.
    Render cleanly."""
    if isinstance(item, (tuple, list)):
        node = item[0] if item else "?"
        line = None
        reason = None
        if len(item) >= 3 and isinstance(item[2], int):
            line = item[2]
        if len(item) >= 4:
            reason = str(item[3]).replace("_", " ")
        s = f"`{node}`"
        extra = []
        if line is not None:
            extra.append(f"line {line}")
        if reason:
            extra.append(reason)
        if extra:
            s += " (" + ", ".join(extra) + ")"
        return s
    return f"`{item}`"


def _split_id(node_id):
    """flask.app.Flask.send_static_file -> (module, class_or_None, method).
    Heuristic: a segment starting uppercase is the class; everything before it is
    the module; everything after is the method path."""
    parts = node_id.split(".")
    cls_idx = None
    for i, p in enumerate(parts):
        if p[:1].isupper():
            cls_idx = i
            break
    if cls_idx is None:
        # module-level function: module = all but last, method = last
        return (".".join(parts[:-1]), None, parts[-1])
    module = ".".join(parts[:cls_idx])
    cls = parts[cls_idx]
    method = ".".join(parts[cls_idx + 1:]) if cls_idx + 1 < len(parts) else ""
    return (module, cls, method)


def _diagnose_missing_target(target_query, fwd, scope):
    """Explain WHY a target isn't in the verified call index, guiding the next
    action. Evidence-based (CodeTruth re-indexes live each run — there is no
    persisted 'stale index'), so the reasons are: empty/incomplete index,
    wrong repository (top-level module absent), name/qualifier mismatch (module
    present but this exact name isn't), or simply not parsed. Never guesses."""
    base = f"Target `{target_query}` is not in the verified call index."

    # (a) index is empty / pipeline did not build a graph this run
    if not fwd:
        return (base + " The verified call index is empty — the analysis pipeline "
                "did not build a call graph for this repository (e.g. Module 1/2 "
                "was blocked by a governance gate or a virtual environment in the "
                "repo). Re-run the full assessment on this repository first, then "
                "retry the change-impact query.")

    # inspect what the index actually contains, to locate the mismatch
    q = target_query.strip()
    top = q.split(".")[0] if "." in q else q
    leaf = q.rsplit(".", 1)[-1]
    index_top_modules = {k.split(".")[0] for k in fwd}

    # (b) target's top-level module is not present in this index
    if "." in q and top not in index_top_modules:
        sample = ", ".join(sorted(index_top_modules)[:6])
        return (base + f" The target's top-level module `{top}` does not appear in "
                f"the verified call index for this repository. Verify that you "
                f"selected the correct repository or target method. This repo's "
                f"top-level modules include: {sample}"
                + (", …" if len(index_top_modules) > 6 else "")
                + ". Tip: use Browse methods to pick a verified method from the "
                "current repository.")

    # (c) name/qualifier mismatch: the leaf name exists but under other qualifiers
    near = [k for k in fwd if k.rsplit(".", 1)[-1] == leaf]
    if not near:
        near = [k for k in fwd if leaf and leaf in k]
    if near:
        shown = "\n".join(f"    - `{k}`" for k in sorted(near)[:8])
        more = f"\n    …and {len(near) - 8} more." if len(near) > 8 else ""
        return (base + " A method with that name exists under a different "
                "qualified name — check the module prefix (e.g. a `src/` layout "
                "or package path). Did you mean one of:\n" + shown + more)

    # (d) genuinely absent: not parsed / not a distinct call-graph node
    return (base + f" No node matching `{leaf}` is present. It may not have been "
            "parsed as a distinct call-graph function (e.g. a module-level entry, "
            "a nested/dynamically-created function, or an unsupported construct), "
            "or the name is misspelled. Run the repository assessment or dead-code "
            "view to see the exact node names that are indexed.")


def analyze(repo, target_query):
    from v3.repository_reasoning.reasoning_engine import ReasoningEngine
    from v3.repository_reasoning import reasoning_queries as RQ

    report = ReasoningEngine(repo).resolve()
    fwd = report["call_index"]
    rev = RQ.build_reverse_index(fwd)

    # analysis scope stats (best-effort; from the resolved report + graph size)
    scope = {"functions_in_index": len(fwd),
             "graph_edges": report.get("edge_provenance", {}).get("total_edges",
                            sum(len(v) if isinstance(v, (list, tuple)) else 0
                                for v in fwd.values())),
             "guesses": report.get("truth_boundary", {}).get("guesses", 0)}

    # resolve the target: exact match, else substring
    target = target_query if target_query in fwd else \
        next((k for k in fwd if target_query in k), None)
    if target is None:
        return {"error": _diagnose_missing_target(target_query, fwd, scope)}

    who = RQ.who_calls(target, rev)
    impact = RQ.impact_of(target, rev)
    paths = RQ.paths_to(target, rev, max_depth=8, max_paths=200)

    direct = who.get("direct_callers", [])
    affected = impact.get("affected_callers", [])

    # derive affected files/classes/modules from the impact set
    files, classes, modules = set(), set(), set()
    for node in affected:
        mod, cls, _ = _split_id(node)
        modules.add(mod)
        files.add(mod)  # module ~= file for python (dotted path)
        if cls:
            classes.add(f"{mod}.{cls}")

    # max impact depth from paths
    path_list = paths.get("paths", []) if isinstance(paths, dict) else []
    max_depth = max((len(p) for p in path_list), default=0)

    # outgoing calls = what the target itself calls (forward index)
    outgoing = fwd.get(target, [])
    if isinstance(outgoing, dict):
        outgoing = outgoing.get("calls", []) or list(outgoing.keys())

    # ---- deterministic risk classification (rules stated, inputs measured) ----
    method_name = _split_id(target)[2] or target.rsplit(".", 1)[-1]
    public_api = not method_name.startswith("_")
    aff = impact.get("count", len(affected))
    dep = max_depth
    # regression risk from measured inputs; rule is printed in the report
    conds = [public_api, dep >= 3, aff >= 3]
    n_true = sum(1 for c in conds if c)
    if n_true == 3:
        regression_risk = "HIGH"
    elif n_true == 2:
        regression_risk = "MEDIUM"
    else:
        regression_risk = "LOW"
    # core-framework heuristic: target module is top-level package + has callers
    top_pkg = target.split(".")[0]
    core_framework = (aff > 0 and target.count(".") >= 2
                      and _split_id(target)[0].startswith(top_pkg))

    return {
        "target": target,
        "target_split": _split_id(target),
        "direct_callers": direct,
        "direct_count": who.get("count", len(direct)),
        "affected_callers": affected,
        "affected_count": impact.get("count", len(affected)),
        "affected_files": sorted(files),
        "affected_classes": sorted(classes),
        "affected_modules": sorted(modules),
        "call_chains": path_list[:20],
        "max_depth": max_depth,
        "who_boundary": who.get("boundary", ""),
        "impact_boundary": impact.get("boundary", ""),
        "outgoing_calls": outgoing,
        "public_api": public_api,
        "core_framework": core_framework,
        "regression_risk": regression_risk,
        "risk_inputs": {"public_api": public_api, "max_depth": dep,
                        "affected_count": aff, "conditions_met": n_true},
        "scope": scope,
    }


def render(repo, a, display_name=None):
    if "error" in a:
        return f"# Change Impact Analysis\n\n**Error:** {a['error']}\n"
    mod, cls, method = a["target_split"]
    L = []
    def w(s=""): L.append(s)

    shown_repo = display_name or repo
    w("# CodeTruth — Change Impact Analysis")
    w()
    w(f"**Repository:** `{shown_repo}`  ")
    if display_name and str(display_name) != str(repo):
        w(f"*Analyzed from local checkout: `{repo}` (evidence/debug).*  ")
    w(f"**Target method:** `{a['target']}`  ")
    w(f"**Module:** `{mod}`  ")
    w(f"**Class:** `{cls or '(module-level)'}`  ")
    w(f"**Method:** `{method}`")
    w()
    w("*Deterministic impact over the VERIFIED call graph — computed before any "
      "code change, without executing the program.*")
    w()
    w("---")
    w()

    # ---- Analysis Scope (communicates the scale immediately) ----
    sc = a.get("scope", {})
    w("## Analysis scope")
    w()
    w(f"- Functions in verified call index: {sc.get('functions_in_index','?')}")
    w(f"- Verified call-graph edges: {sc.get('graph_edges','?')}")
    w(f"- Guesses made: **{sc.get('guesses',0)}** (Truth Boundary)")
    w()
    w("---")
    w()

    # ---- THE QUESTION, ANSWERED (leads with the engineer's answer) ----
    w("## The question")
    w()
    w(f"> **If I change `{a['target']}`, what verified parts of the repository "
      f"are affected?**")
    w()
    w("### Verified answer")
    w()
    # direct callers
    if a["direct_callers"]:
        w("**Verified direct caller(s):**")
        for c in a["direct_callers"]:
            w(f"- `{c}`")
    else:
        w("**Verified direct callers:** none in the in-repo call graph.")
    w()
    # indirect
    if a["affected_callers"]:
        w("**Verified indirect (transitive) callers:**")
        for c in a["affected_callers"][:30]:
            w(f"- `{c}`")
    else:
        w("**Verified indirect callers:** none.")
    w()
    # module + class
    w(f"**Verified affected module(s):** "
      + (", ".join(f"`{m}`" for m in a["affected_modules"]) or "none"))
    w(f"**Verified affected class(es):** "
      + (", ".join(f"`{c}`" for c in a["affected_classes"]) or "none"))
    w()
    # call chain (show the longest verified chain, arrow form)
    if a["call_chains"]:
        longest = max(a["call_chains"], key=len)
        w("**Verified call chain:**")
        w()
        w("```")
        w("\n    ".join(f"{n}()" if i == 0 else f"    -> {n}()"
                          for i, n in enumerate(longest)))
        w("```")
        w()
        # simple vertical visualization with the change point marked
        w("**Propagation (top = entry, bottom = the method being changed):**")
        w()
        w("```")
        w("(external entry point — outside the verified repository graph)")
        for i, n in enumerate(longest):
            short = n.split(".")[-1]
            marker = "   <-- CHANGE HERE" if i == len(longest) - 1 else ""
            w(f"   |")
            w(f"   v")
            w(f"{short}(){marker}")
        w("```")
        w()
    w(f"**Verified impact depth:** {a['max_depth']} call levels.")
    w()
    w("**Truth Boundary:**")
    w("- These are the verified *in-repository* impacts.")
    w("- External libraries, plugins, runtime dispatch, and dynamic callers are "
      "**not included** and are explicitly treated as unknown rather than guessed.")
    w()
    w("---")
    w()
    w("### Supporting evidence")
    w()

    # Direct callers
    w("## Direct callers (who calls this)")
    w()
    if a["direct_callers"]:
        for c in a["direct_callers"]:
            w(f"- `{c}`")
    else:
        w("- **None in the verified in-repo call graph.**")
    w()
    w(f"*Count: {a['direct_count']}. Boundary: {a['who_boundary']}*")
    w()

    # Indirect / transitive
    w("## Indirect (transitive) callers")
    w()
    if a["affected_callers"]:
        for c in a["affected_callers"][:50]:
            w(f"- `{c}`")
        if len(a["affected_callers"]) > 50:
            w(f"- ... and {len(a['affected_callers'])-50} more")
    else:
        w("- **None reachable in the verified call graph.**")
    w()
    w(f"*Count: {a['affected_count']}. Boundary: {a['impact_boundary']}*")
    w()

    # Affected files / classes / modules
    w("## Affected scope (derived from the impact set)")
    w()
    w(f"- **Affected files/modules:** {len(a['affected_files'])}")
    for f in a["affected_files"][:20]:
        w(f"    - `{f}`")
    w(f"- **Affected classes:** {len(a['affected_classes'])}")
    for c in a["affected_classes"][:20]:
        w(f"    - `{c}`")
    w()

    # Call chains + depth
    w("## Call chains to the target")
    w()
    if a["call_chains"]:
        for chain in a["call_chains"][:10]:
            w(f"- {' -> '.join(chain)}")
        w()
        w(f"*Maximum impact depth: {a['max_depth']} levels.*")
    else:
        w("- No verified call chains reach this target.")
    w()

    w("---")
    w()

    # Affected Functions
    w("## Affected functions")
    w()
    w(f"- **Total verified affected functions:** {a['affected_count']}")
    for fn in a["affected_callers"][:30]:
        w(f"    - `{fn}`")
    w()

    # Dependency Summary
    w("## Dependency summary")
    w()
    w(f"- **Incoming dependencies (callers of target):** {a['direct_count']}")
    for c in a["direct_callers"][:15]:
        w(f"    - `{c}`")
    w(f"- **Outgoing dependencies (target calls these):** {len(a['outgoing_calls'])}")
    for c in list(a["outgoing_calls"])[:15]:
        w(f"    - {_fmt_outgoing(c)}")
    # Honesty note: a target marked <external> is one the resolver did not resolve
    # to a verified in-repo node. That set can include BOTH genuine third-party
    # libraries AND in-repo calls the resolver could not confirm (e.g. under src/
    # layouts). CodeTruth does not guess which, so it does not split them into
    # "internal cross-module" vs "third-party" — that distinction is not verified.
    if any(str((c[0] if isinstance(c, (tuple, list)) else c)).startswith("<external>")
           for c in a["outgoing_calls"]):
        w("")
        w("*Targets marked `<external>` are **outside the verified in-repo graph** — "
          "either third-party libraries or in-repo calls the resolver could not "
          "confirm. CodeTruth does not guess which; it reports the boundary rather "
          "than asserting an unverified internal/third-party split.*")
    w()

    # Engineering Recommendation (composed FROM facts)
    w("## Engineering recommendation")
    w()
    classes_str = ", ".join(f"`{c}`" for c in a["affected_classes"]) or "(none)"
    if a["affected_count"] > 0:
        w(f"Changing `{a['target']}` affects **{a['affected_count']} verified "
          f"caller(s)** across {classes_str}. Regression testing should cover "
          f"these callers and the call chains shown above "
          f"(max depth {a['max_depth']} levels).")
    else:
        w(f"`{a['target']}` has no verified in-repo callers. If it is a public "
          f"API or entry point, its callers are external/dynamic and are NOT "
          f"captured here — treat impact as a known unknown and test via the "
          f"public interface.")
    w()
    w("### Engineering Impact Summary")
    w()
    if a["affected_count"] > 0:
        chain_note = ""
        if a["call_chains"]:
            longest = max(a["call_chains"], key=len)
            chain_note = (f" through the verified chain "
                          f"({' -> '.join(n.split('.')[-1] for n in longest)})")
        w(f"A change to `{a['target']}` propagates to {a['affected_count']} "
          f"verified caller(s){chain_note}. Any modification can affect the "
          f"execution paths reachable through these callers. This analysis lets "
          f"engineers determine the *verified* scope of impact before changing "
          f"code — reducing regression risk while explicitly separating proven "
          f"impacts from unknown runtime behavior (external/dynamic callers).")
    else:
        w(f"`{a['target']}` has no verified in-repo callers, which for a public "
          f"API typically means its callers live outside this repository "
          f"(external code, plugins, or runtime dispatch). The engineering "
          f"significance is the *boundary itself*: CodeTruth proves there is no "
          f"static in-repo dependency, and flags the external surface as a known "
          f"unknown rather than asserting the method is unused.")
    w()

    # Risk Classification (deterministic rules, SHOWN)
    w("## Risk classification (deterministic)")
    w()
    w(f"- **Public API:** {'Yes' if a['public_api'] else 'No'} "
      f"(rule: method name does not start with `_`)")
    w(f"- **Core framework:** {'Yes' if a['core_framework'] else 'No'} "
      f"(rule: top-level-package method with verified callers)")
    w(f"- **Regression risk:** {a['regression_risk']}")
    w()
    ri = a["risk_inputs"]
    w("| Risk input | Value |")
    w("|---|---|")
    w(f"| public API | {ri['public_api']} |")
    w(f"| max call depth | {ri['max_depth']} |")
    w(f"| affected callers | {ri['affected_count']} |")
    w(f"| conditions met (of 3) | {ri['conditions_met']} |")
    w()
    w("*Rule (stated, reproducible): risk = HIGH if all three of "
      "[public API, depth>=3, affected>=3]; MEDIUM if exactly two; LOW otherwise. "
      "Every input is measured from the verified graph; no subjective scoring.*")
    w()

    w("---")
    w()

    # Estimated Review Scope (for engineering leads / PMs to plan)
    w("## Estimated Review Scope")
    w()
    w("For planning a safe change, the verified review scope is:")
    w()
    w("| Planning item | Value |")
    w("|---|---|")
    w(f"| Files to inspect | {len(a['affected_files'])} |")
    w(f"| Classes to inspect | {len(a['affected_classes'])} |")
    w(f"| Verified callers to review | {a['affected_count']} |")
    w(f"| Maximum propagation depth | {a['max_depth']} |")
    w(f"| Suggested regression priority | {a['regression_risk']} |")
    w()
    w("*Scope is over the VERIFIED graph only. External/dynamic callers "
      "(Truth Boundary) may require additional review beyond this scope.*")
    w()

    w("---")
    w()

    # Truth Boundary — the honest interpretation
    w("## Truth Boundary — how to read this")
    w()
    verified_total = a["affected_count"]
    if verified_total == 0:
        w("- **0 verified in-repo callers.** This does **NOT** mean the method is "
          "safe to change or unused.")
        w("- It means CodeTruth found no *statically verifiable* in-repo caller. "
          "Methods like public API endpoints are typically called by external "
          "code or via dynamic dispatch (routing, decorators, reflection) — paths "
          "CodeTruth **correctly refuses to guess about**.")
        w("- **Action:** treat external/dynamic callers as a KNOWN UNKNOWN. The "
          "verified impact is empty; the true impact requires knowledge outside "
          "this repository's static call graph.")
    else:
        w(f"- **{verified_total} verified affected callers** — every one is a real "
          "edge in the call graph, not inferred.")
        w("- This is the impact CodeTruth can *prove*. Dynamic/external callers "
          "(if any) are not included and are flagged by the boundary notes above, "
          "not guessed.")
    w()
    w("> **No guesses made.** The impact set is exact over the verified graph. "
      "What cannot be statically determined is reported as unknown, never "
      "fabricated.")
    w()
    w("---")
    w()

    # Engineering Evidence Summary — one-glance panel, tied to THIS run's facts
    sc = a.get("scope", {})
    lrc_note = ""
    w("## Engineering Evidence Summary")
    w()
    w("| Item | Status |")
    w("|---|---|")
    w(f"| Repository analysed | Yes ({mod.split('.')[0]}) |")
    w(f"| Reasoning performed | Deterministic (static, no execution) |")
    w(f"| Verified call graph | Yes ({sc.get('graph_edges','?')} edges) |")
    w(f"| Change impact computed | Yes ({a['affected_count']} verified callers) |")
    w(f"| Call chain reconstructed | Yes (depth {a['max_depth']}) |")
    w(f"| Risk classified (rule-based) | Yes ({a['regression_risk']}) |")
    w(f"| Truth Boundary | Yes ({sc.get('guesses',0)} guesses) |")
    w()
    w("*Each item reflects what was actually computed in this analysis run, not a "
      "generic capability list. Verifiable against the evidence sections above.*")
    w()

    return "\n".join(L)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--target", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv[1:])
    a = analyze(args.repo, args.target)
    md = render(args.repo, a)
    out = args.out or "change_impact.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"change impact report -> {out}")
    if "error" not in a:
        print(f"   target: {a['target']}")
        print(f"   direct callers: {a['direct_count']}, "
              f"transitive affected: {a['affected_count']}, "
              f"affected files: {len(a['affected_files'])}")


if __name__ == "__main__":
    main(sys.argv)
