# CodeTruth Agent V3 — Unresolved Pipeline Research Log

**Location:** `v3/repository_graph/tests/unresolved_pipeline/`
**Status:** Research workbench — NOT production code
**Date:** 2026-06-17 to 2026-06-19
**Purpose:** Investigation of attribute_call dominance problem
**Outcome:** Led directly to Module 2 Deep Resolution pipeline design

---

## What This Folder Is

During Module 2 development, the following question emerged:

> *82% of unresolved calls are attribute_calls.*
> *Why? What patterns cause them? Can they be resolved?*

The `unresolved_pipeline/` folder contains research scripts
written to investigate and understand this problem from first
principles. These scripts were never part of the production
pipeline — they are the research that shaped it.

---

## Research Scripts — What Each One Did

### Classification Research

| Script | Purpose | Finding |
|---|---|---|
| `cause_classifier.py` | Classify unresolved calls by root cause | Identified builtin_like, constructor, factory, property, inheritance, reflection as distinct categories |
| `call_classification_benchmark.py` | Benchmark classification accuracy | Validated category boundaries |
| `unknown_call_analyzer.py` | Analyze what remains unclassified | Found edge cases in naming conventions |
| `unknown_call_benchmark.py` | Measure unclassified rate | ~8% of calls genuinely unclassifiable |
| `full_log_classification_benchmark.py` | Full corpus classification run | Confirmed category distribution |

### Variable Origin Research

| Script | Purpose | Finding |
|---|---|---|
| `variable_origin_extractor.py` | Trace where variables come from | Exposed O(n²) scaling bug — fixed |
| `assignment_chain_builder.py` | Follow assignment chains | Constructor pattern identified |
| `origin_resolution_benchmark.py` | Benchmark origin tracing | 54,194 constructor resolutions possible |
| `fact_extractor_v2.py` | Extract type facts from code | Became foundation of DR fact extraction |

### Resolution Research

| Script | Purpose | Finding |
|---|---|---|
| `object_method_resolver.py` | Resolve object.method() calls | Prototype of builtin_type resolver |
| `object_method_benchmark.py` | Benchmark resolution accuracy | 286,477 builtin resolutions confirmed |
| `constructor_call_classifier.py` | Classify constructor patterns | new MyClass() → 54,194 resolvable |
| `return_flow_tracker_v2.py` | Track return values | Prototype of factory resolver |
| `resolution_pipeline.py` | Combine all resolvers | First prototype of DR pipeline |
| `resolution_scorecard.py` | Score overall resolution | Established 25.9% improvement baseline |
| `final_resolution_benchmark.py` | Final benchmark run | Validated DR pipeline numbers |

### Framework Research

| Script | Purpose | Finding |
|---|---|---|
| `known_framework_functions.py` | Map framework-specific calls | Framework method resolution scope |
| `flatten_class_graph.py` | Flatten class hierarchy | Inheritance resolver prototype |

### Reflection Research

| Script | Purpose | Finding |
|---|---|---|
| `reflection_diagnostic.py` | Analyze dynamic getattr() | 1,032/1,054 sites in transformers are ModuleList/Sequential — confirmed known limit |

### Corpus Research

| Script | Purpose | Finding |
|---|---|---|
| `corpus_package_root_scan.py` | Find src-layout repos | D-008 discovery — 6 repos affected |
| `test_unresolved_resolution_pipeline.py` | Test pipeline on real repos | Validated pipeline on fastapi, pytorch |
| `test_real_repo.py` | Single repo test harness | Integration test prototype |
| `resolution_pipeline.py` | Full pipeline test | 76-repo corpus validated |

### Debug Scripts

| Script | Purpose |
|---|---|
| `debug_assignment_trace.py` | Debug variable assignment tracing |
| `debug_ast_minimal.py` | Minimal AST parsing debug |
| `debug_factory_trace.py` | Debug factory pattern detection |

---

## Research → Production Mapping

Every production resolver traces back to a research script:

```
Research script                    → Production component
────────────────────────────────────────────────────────
cause_classifier.py                → cause_classifier.py (DR)
object_method_resolver.py          → builtin_type resolver
constructor_call_classifier.py     → constructor resolver
return_flow_tracker_v2.py          → factory resolver
flatten_class_graph.py             → inheritance resolver
fact_extractor_v2.py               → DR fact extraction
corpus_package_root_scan.py        → D-008 fix
variable_origin_extractor.py       → fixed O(n²) bug
reflection_diagnostic.py           → confirmed known limit
```

---

## Key Findings from This Research

```
Finding 1 — Attribute call dominance
  82.1% of unresolved calls = attribute_call pattern
  obj.method() where type of obj is unknown

Finding 2 — Category distribution
  builtin_like:   largest category
  constructor:    54,194 resolvable
  factory:        558 resolvable
  property:       3,175 resolvable
  inheritance:    23,209 resolvable
  reflection:     0 resolvable (confirmed hard limit)

Finding 3 — D-008 discovered
  corpus_package_root_scan found 6 repos
  with src-layout causing 0 files parsed
  Fixed in Module 2 final run

Finding 4 — O(n²) scaling bug
  variable_origin_extractor had quadratic
  complexity on large repos (pytorch 50K+)
  Fixed before production run

Finding 5 — Reflection hard limit
  1,032/1,054 transformers dynamic dispatch
  sites are ModuleList/Sequential indexing
  → not statically resolvable
  → confirmed Truth Boundary
```

---

## Status — Research Complete

```
All findings incorporated into:
  Module 2 Deep Resolution pipeline
  annotation_resolver.py (DR Resolver #7)
  MODULE2_VALIDATION_REPORT.md
  ATTRIBUTE_CALL_GAP_ANALYSIS.md

These scripts are kept as:
  Research provenance
  Debugging reference
  Future Module 3 starting point

They are NOT run in production.
They are NOT part of run_m1.py / run_m2.py / pipeline.py
```

---

## Relationship to Module 3

```
The research that could NOT be completed
in this workbench becomes Module 3:

return_flow_tracker_v2.py → could not cross
                             function boundaries
                           → Module 3:
                             data_flow_tracer.py

assignment_chain_builder.py → could not trace
                               across files
                             → Module 3:
                               cross_module_type_resolver.py

The workbench exposed the exact boundary
between Module 2 (pattern matching) and
Module 3 (reasoning across boundaries).
```

---

*CodeTruth Agent V3 — AI imagines. CodeTruth checks. Nature tests. Humans decide.*
