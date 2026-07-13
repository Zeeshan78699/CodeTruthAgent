"""
module3_pipeline.py
CodeTruth Agent V3 — Module 3, Integration.

Single-call orchestration for Module 3: runs the ReasoningEngine over a repo and
returns the consolidated report. This is the function the root pipeline.py calls
after Module 2 (M1 -> M2 -> M3). No resolution logic of its own.
"""

from v3.repository_reasoning.reasoning_engine import ReasoningEngine


def run_module3(repo_root, root_counts=None, max_passes=5, max_depth=6,
                m2_scan=None, m1_result=None):
    """Run Module 3 (Phase 3A type resolution + Phase 3B reasoning) over a repo.
    Optionally reuse a precomputed Module 2 scan (m2_scan) to avoid double-scanning,
    and accept m1_result for future framework-aware reasoning (ignored today).
    Returns the Module 3 report dict (see type_fact_aggregator.aggregate)."""
    return ReasoningEngine(repo_root, root_counts=root_counts,
                           max_passes=max_passes, max_depth=max_depth,
                           m2_scan=m2_scan, m1_result=m1_result).resolve()


def run_full_pipeline(repo_root):
    """M1 -> M2 -> M3 in one pass. Module 1/2 are invoked via the frozen adapter
    (which Module 3 already calls internally for the call graph and unresolved
    set), so this returns the Module 3 report; the M1/M2 facts live on the
    adapter scan Module 3 consumes. Kept thin and honest - no re-derivation."""
    return run_module3(repo_root)
