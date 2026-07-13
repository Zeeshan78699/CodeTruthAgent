"""
truth_boundary_demo.py — CodeTruth "Zero-Guess" Truth Boundary demonstration.

The front-door demo. For a target method it contrasts the SURFACE reading (the
tempting inference from raw numbers) with CodeTruth's VERIFIED reading. The point
is NOT that CodeTruth finds more callers than other approaches - it is that when
CodeTruth cannot verify something, it reports UNKNOWN instead of guessing.

Honest framing (matches the UAT/SIT evidence):
  - The "surface reading" is the naive inference from the data, not a claim about
    any specific competing tool's output.
  - CodeTruth is designed for deterministic, reproducible static reasoning with an
    explicit Truth Boundary: 0 verified callers is a KNOWN-UNKNOWN, never "safe".

Reuses the proven engine queries (who_calls / impact_of) - no new analysis.

Usage:
    python v3\\repository_reasoning\\truth_boundary_demo.py "<repo>" --target <qualified.method>
    python v3\\repository_reasoning\\truth_boundary_demo.py "<repo>" \\
        --populated <method_with_callers> --empty <method_without_callers>
"""
import sys, os, warnings, argparse
warnings.filterwarnings("ignore", category=SyntaxWarning)

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, "..", ".."))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "v3"))


# ----- pure classification core (engine-independent; unit-testable) -----
VERIFIED_IMPACT = "VERIFIED_IMPACT"
KNOWN_UNKNOWN = "KNOWN_UNKNOWN"
NOT_FOUND = "NOT_FOUND"


def _classify(target, resolved, direct_callers, affected_callers, guesses):
    """Pure: decide the verdict and the two readings from query results."""
    if not resolved:
        return {
            "target": target, "verdict": NOT_FOUND, "guesses": guesses,
            "direct_callers": [], "direct_count": 0, "affected_count": 0,
            "surface_reading": "The name was not found in the verified call index.",
            "codetruth_reading": ("CodeTruth does not fabricate a target it cannot "
                                  "locate. Provide a fully-qualified name, or this is "
                                  "reported as not-found - not assumed."),
        }
    direct = list(direct_callers or [])
    affected = list(affected_callers or [])
    if len(direct) > 0:
        verdict = VERIFIED_IMPACT
        surface = ("A guess-based reading might overstate or understate impact, "
                   "or miss that these are exact call-graph edges.")
        ct = (f"{len(direct)} VERIFIED direct caller(s), each a real edge in the "
              f"call graph (not inferred): "
              + ", ".join(f"`{c}`" for c in direct) + ". "
              f"Transitive verified impact: {len(affected)}. Guesses made: {guesses}.")
    else:
        verdict = KNOWN_UNKNOWN
        surface = ("A guess-based reading might conclude: \"0 callers found -> the "
                   "method is unused and safe to delete.\"")
        ct = ("0 VERIFIED in-repo callers. This is a KNOWN-UNKNOWN, NOT a safety "
              "verdict: the method may be reached via dynamic dispatch, framework "
              "routing, decorators, or code outside this repository - paths static "
              "analysis cannot see. CodeTruth reports this as UNKNOWN rather than "
              f"guessing \"unused\". Guesses made: {guesses}.")
    return {
        "target": target, "verdict": verdict, "guesses": guesses,
        "direct_callers": direct, "direct_count": len(direct),
        "affected_count": len(affected),
        "surface_reading": surface, "codetruth_reading": ct,
    }


# ----- engine-wired classify -----
def classify(repo, target_query):
    from v3.repository_reasoning.reasoning_engine import ReasoningEngine
    from v3.repository_reasoning import reasoning_queries as RQ
    report = ReasoningEngine(repo).resolve()
    fwd = report["call_index"]
    rev = RQ.build_reverse_index(fwd)
    guesses = report.get("truth_boundary", {}).get("guesses", 0)

    target = target_query if target_query in fwd else \
        next((k for k in fwd if target_query in k), None)
    if target is None:
        return _classify(target_query, False, [], [], guesses)

    who = RQ.who_calls(target, rev)
    imp = RQ.impact_of(target, rev)
    return _classify(target,
                     True,
                     who.get("direct_callers", []) if isinstance(who, dict) else [],
                     imp.get("affected_callers", []) if isinstance(imp, dict) else [],
                     guesses)


# ----- rendering -----
_VERDICT_BADGE = {
    VERIFIED_IMPACT: "🟢 VERIFIED IMPACT",
    KNOWN_UNKNOWN: "🟡 KNOWN-UNKNOWN (not 'safe')",
    NOT_FOUND: "⚪ NOT FOUND (not assumed)",
}


def render_single(repo, r):
    L = []
    L.append("# CodeTruth — Zero-Guess Truth Boundary")
    L.append("")
    L.append(f"**Repository:** `{repo}`  ")
    L.append(f"**Target:** `{r['target']}`  ")
    L.append(f"**Verdict:** {_VERDICT_BADGE[r['verdict']]}  ")
    L.append(f"**Guesses made:** {r['guesses']}")
    L.append("")
    L.append("*When CodeTruth cannot verify something, it reports UNKNOWN instead "
             "of guessing. Deterministic; reproducible.*")
    L.append("")
    L.append("---")
    L.append("")
    L.append("| | Reading |")
    L.append("|---|---|")
    L.append(f"| **Surface reading** (a guess) | {r['surface_reading']} |")
    L.append(f"| **CodeTruth** (zero-guess) | {r['codetruth_reading']} |")
    L.append("")
    if r["verdict"] == VERIFIED_IMPACT:
        L.append("## Verified evidence")
        L.append("")
        for c in r["direct_callers"]:
            L.append(f"- `{c}`")
        L.append("")
        L.append(f"*{r['direct_count']} direct, {r['affected_count']} transitive — "
                 f"every one a real call-graph edge.*")
    else:
        L.append("## Truth Boundary")
        L.append("")
        L.append("> 0 verified callers is **evidence of absence in the static graph — "
                 "not proof the method is unused.** External and dynamic callers are "
                 "flagged as unknown, never assumed away.")
    L.append("")
    return "\n".join(L)


def render_pair(repo, populated, empty):
    """The front-door demo: same tool, same repo — it finds real callers where they
    exist, and refuses to fabricate where they don't."""
    L = []
    L.append("# CodeTruth — Zero-Guess Engineering Intelligence")
    L.append("")
    L.append(f"**Repository:** `{repo}`")
    L.append("")
    L.append("Same tool, same repository. One method has verified callers; the other "
             "does not. Watch what CodeTruth does with the second one.")
    L.append("")
    L.append("| Method | Verified direct callers | CodeTruth verdict |")
    L.append("|---|---|---|")
    pc = ", ".join(f"`{c}`" for c in populated["direct_callers"]) or "—"
    L.append(f"| `{populated['target']}` | {populated['direct_count']} — {pc} "
             f"| {_VERDICT_BADGE[populated['verdict']]} |")
    L.append(f"| `{empty['target']}` | {empty['direct_count']} "
             f"| {_VERDICT_BADGE[empty['verdict']]} |")
    L.append("")
    L.append("### The point")
    L.append("")
    L.append("- It **finds real callers when they exist** — these are exact call-graph "
             "edges, not inferences.")
    L.append("- It **refuses to fabricate when they don't** — 0 verified callers is "
             "reported as a KNOWN-UNKNOWN, never as \"safe to delete.\"")
    L.append(f"- **Guesses made across both: {populated['guesses'] + empty['guesses']}.**")
    L.append("")
    # ---- Truth Boundary Summary (at-a-glance) ----
    verified_n = sum(1 for r in (populated, empty) if r["verdict"] == VERIFIED_IMPACT)
    unknown_n = sum(1 for r in (populated, empty) if r["verdict"] == KNOWN_UNKNOWN)
    total_guesses = populated["guesses"] + empty["guesses"]
    L.append("### Truth Boundary Summary")
    L.append("")
    L.append("| | |")
    L.append("|---|---|")
    L.append(f"| ✓ Verified findings | {verified_n} |")
    L.append(f"| ✓ Known-unknowns | {unknown_n} |")
    L.append(f"| ✓ Guesses | {total_guesses} |")
    L.append("| ✓ Deterministic | YES |")
    L.append("")
    L.append("*CodeTruth proves what can be verified and explicitly reports what "
             "cannot. It never fills evidence gaps with guesses. Deterministic and "
             "reproducible — the same inputs yield the same result, every time.*")
    L.append("")
    return "\n".join(L)


def demo_pair(repo, populated_target, empty_target):
    p = classify(repo, populated_target)
    e = classify(repo, empty_target)
    return render_pair(repo, p, e), {"populated": p, "empty": e}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--target")
    ap.add_argument("--populated")
    ap.add_argument("--empty")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv[1:])
    if args.populated and args.empty:
        md, _ = demo_pair(args.repo, args.populated, args.empty)
    elif args.target:
        md = render_single(args.repo, classify(args.repo, args.target))
    else:
        print("provide --target OR (--populated AND --empty)")
        return 2
    out = args.out or "truth_boundary_demo.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"truth boundary demo -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
