"""
traceeval_harness.py
CodeTruth Agent V3 — TraceEval evaluation (Option A: name-level matching).

TraceEval (arXiv 2605.11006): recovers a program's call graph from source,
scored against EXECUTION-VERIFIED ground-truth edges. Ground truth is a
{caller: [callees]} dict where ids are `package.Class:method(argtypes)`.

CodeTruth emits static edges; ids look like
`pkg.path.Class.Class.method` (dot-separated, DOUBLED class name, NO arg types).

This harness (Option A):
  1. Transforms CodeTruth ids -> TraceEval id convention `package.Class:method`.
  2. Strips arg types from BOTH sides (TraceEval's own _strip_call_args), so
     scoring is name-level and symmetric.
  3. Computes micro-averaged edge P/R/F1, the same metric as TraceEval's
     compute_metrics.py.

HONEST SCOPE:
  * Name-level (arg types stripped): two overloads collapse to one name. Labelled.
  * Ground truth is DYNAMIC trace (executed edges only); CodeTruth is STATIC.
    Recall is the fair primary metric ("of executed edges, how many did static
    analysis recover"); precision carries the static-finds-more caveat.
  * stdlib edges are dropped on both sides (TraceEval drops them too).
"""

import os
import re


# --------------------------------------------------------------------------- #
# ID TRANSFORM: CodeTruth edge id  ->  TraceEval name-level id
# --------------------------------------------------------------------------- #
def strip_args(name):
    """TraceEval's own arg-stripping: drop everything from first '(' on."""
    if not isinstance(name, str):
        return ""
    return name.split("(", 1)[0].strip()


def _collapse_doubled_class(dotted):
    """CodeTruth emits `pkg.Class.Class.method` (class name doubled). Collapse
    any immediately-repeated segment: a.b.X.X.m -> a.b.X.m. Conservative: only
    collapses adjacent identical segments."""
    parts = dotted.split(".")
    out = []
    for p in parts:
        if out and out[-1] == p:
            continue  # skip the immediate duplicate
        out.append(p)
    return ".".join(out)


def _strip_outer_classes(traceeval_id):
    """TraceEval's `nested_class` mode (Java): collapse `pkg.Outer.Inner:method`
    to `pkg.Inner:method`. The JVM trace records nested classes by their bare
    name. Heuristic (matches TraceEval): the class path is the run of trailing
    Capitalized segments before ':'; keep only the LAST capitalized segment as
    the class. Lowercase segments are the package and are preserved.

    Example: dev.morling.onebrc.CalculateAverage_breejesh.Measurement:merge
          -> dev.morling.onebrc.Measurement:merge
    """
    if ":" not in traceeval_id:
        return traceeval_id
    typepath, method = traceeval_id.split(":", 1)
    segs = typepath.split(".")
    # find trailing run of Capitalized segments (the class chain)
    i = len(segs)
    while i > 0 and segs[i - 1][:1].isupper():
        i -= 1
    pkg = segs[:i]              # lowercase package
    classes = segs[i:]          # Capitalized class chain (Outer...Inner)
    if not classes:
        return traceeval_id
    bare_class = classes[-1]    # JVM trace uses the innermost/bare name
    new_path = ".".join(pkg + [bare_class])
    return f"{new_path}:{method}"


def to_traceeval_id(codetruth_id, nested_class=True):
    """`pkg.path.Class.Class.method`  ->  `pkg.path.Class:method` (name-level).

    Steps: strip args, collapse doubled class segment, ':' before method, then
    (if nested_class) strip outer-class qualifiers to the bare class so nested
    classes match the JVM trace. Arg types intentionally absent (Option A).
    """
    if not isinstance(codetruth_id, str) or not codetruth_id:
        return ""
    s = strip_args(codetruth_id)
    s = _collapse_doubled_class(s)
    parts = s.split(".")
    if len(parts) < 2:
        return s
    method = parts[-1]
    prefix = ".".join(parts[:-1])
    out = f"{prefix}:{method}"
    if nested_class:
        out = _strip_outer_classes(out)
    return out


def normalize_gt_id(gt_id, nested_class=True):
    """TraceEval ground-truth ids are `package.Class:method(args)`. Drop args,
    and (symmetrically) apply nested_class stripping so both sides match."""
    if not isinstance(gt_id, str):
        return ""
    out = strip_args(gt_id)
    if nested_class:
        out = _strip_outer_classes(out)
    return out


# --------------------------------------------------------------------------- #
# EDGE EXTRACTION
# --------------------------------------------------------------------------- #
def codetruth_edges(call_graph):
    """Flatten CodeTruth's call_graph into a set of TraceEval-id (caller, callee)
    edges. call_graph shape: {module: [ {caller, callee, lineno, resolution}, ...]}

    IMPORTANT: CodeTruth emits resolved edges under several keys, including
    `__java_3a_type_resolved__` (real type-resolved Java edges). Only true
    METADATA keys (e.g. `__java_3a_counts__`) must be skipped. So we skip a key
    only when its value is not a list of edge dicts."""
    edges = set()
    if not isinstance(call_graph, dict):
        return edges
    for key, val in call_graph.items():
        if not isinstance(val, list):
            continue  # metadata dicts/counts -> skip
        for e in val:
            if not isinstance(e, dict):
                continue
            if "caller" not in e or "callee" not in e:
                continue
            caller = to_traceeval_id(e.get("caller", ""))
            callee = to_traceeval_id(e.get("callee", ""))
            if caller and callee:
                edges.add((caller, callee))
    return edges


def ground_truth_edges(gt_graph):
    """TraceEval callgraph.json: {caller: [callee, ...]} -> name-level edge set."""
    edges = set()
    if not isinstance(gt_graph, dict):
        return edges
    for caller, callees in gt_graph.items():
        c = normalize_gt_id(caller)
        if not isinstance(callees, list):
            continue
        for cee in callees:
            cc = normalize_gt_id(cee)
            if c and cc:
                edges.add((c, cc))
    return edges


# --------------------------------------------------------------------------- #
# SCORING (micro-averaged, like compute_metrics.py)
# --------------------------------------------------------------------------- #
def score(pred_edges, gt_edges):
    """Per-instance TP/FP/FN."""
    tp = len(pred_edges & gt_edges)
    fp = len(pred_edges - gt_edges)
    fn = len(gt_edges - pred_edges)
    return tp, fp, fn


def prf(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return round(p, 4), round(r, 4), round(f, 4)


# --------------------------------------------------------------------------- #
# <init> CONSTRUCTOR NORMALIZATION + SAME-FILE / CROSS-FILE PARTITION
# --------------------------------------------------------------------------- #
def normalize_init(edge_id):
    """Collapse constructor surface forms to a canonical class endpoint, mirroring
    TraceEval's `init` mode: `Class:<init>` / `Class:constructor` / `Class:Class`
    all -> `Class:<init>`. Operates on a name-level id `pkg.Class:method`."""
    if ":" not in edge_id:
        return edge_id
    typepath, method = edge_id.split(":", 1)
    cls = typepath.split(".")[-1]
    if method in ("<init>", "constructor", "__init__", cls):
        return f"{typepath}:<init>"
    return edge_id


def _apply_init(edges):
    return set((normalize_init(a), normalize_init(b)) for a, b in edges)


def partition_by_file(gt_edges, file_class):
    """Split GT edges into (same_file, cross_file) by whether the CALLEE's class
    matches the bundled file's class. file_class is the bare class stem of the
    instance's bundled .java file (e.g. 'ResChunkPullParser').

    Cross-file edges have a callee defined in another file NOT shipped with the
    instance -> structurally unrecoverable from single-file analysis. Same-file
    edges are the fair scoring target for a static single-file analyzer."""
    same, cross = set(), set()
    for caller, callee in gt_edges:
        callee_class = callee.rsplit(":", 1)[0].split(".")[-1]
        if callee_class == file_class:
            same.add((caller, callee))
        else:
            cross.add((caller, callee))
    return same, cross


def score_with_partition(pred_edges, gt_edges, file_class):
    """Fair scoring: apply <init> norm to both sides, partition GT into
    same-file / cross-file, score CodeTruth against the SAME-FILE subset, and
    report cross-file count separately (structurally unrecoverable)."""
    pred = _apply_init(pred_edges)
    gt = _apply_init(gt_edges)
    same, cross = partition_by_file(gt, file_class)
    tp = len(pred & same)
    fp = len(pred - gt)          # FP measured against ALL gt (real overclaims)
    fn = len(same - pred)        # FN only on the recoverable same-file subset
    return {
        "tp": tp, "fp": fp, "fn_samefile": fn,
        "samefile_gt": len(same),
        "crossfile_gt_unrecoverable": len(cross),
        "pred": len(pred),
    }