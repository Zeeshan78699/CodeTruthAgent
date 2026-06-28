# CodeTruth V3 — Attribute Call Gap Analysis

**Module:** Module 2 — Repository Graph Intelligence
**Date:** 2026-06-25
**Evidence:** 76-repo corpus run — DEEP_RESOLUTION_FULL_SUMMARY.json

---

## The Problem

```
Total calls scanned    : 3,918,744
Resolved (core)        : 1,521,476  (38.8%)
Resolved (DR pipeline) :   367,613  (+9.4%)
Remaining unresolved   : 2,029,655  (51.8%)

Of remaining unresolved:
  attribute_call pattern : 2,269,534  (82.1%)
```

An `attribute_call` occurs when the core engine sees `obj.method()`
but cannot determine what type `obj` is.

---

## Three Categories

### Category 1 — Type-Annotated Parameters

```python
def process(conn: DatabaseConnection, repo: UserRepository):
    conn.execute("SELECT")   # UNRESOLVED — annotation present
    repo.find_all()          # UNRESOLVED — annotation present
```

**Why unresolved:** Core engine does not read type annotations.
**Solution:** `annotation_resolver.py` — Module 2 Extension (built today)
**Estimated yield:** 15-25% of remaining attribute_calls
**Confidence:** HIGH — annotation is ground truth written by developer
**Module:** 2 (solved now)

---

### Category 2 — Untyped Function Returns

```python
def get_connection():           # no return annotation
    return DatabaseConnection()

conn = get_connection()
conn.execute("SELECT")          # UNRESOLVED — type lost
```

**Why unresolved:** Return type not annotated.
Core engine cannot trace through function boundaries.
**Solution:** Data flow tracing engine — Module 3
**Estimated yield:** 40-50% of remaining after Category 1
**Confidence:** HIGH for single-path returns
                MEDIUM for multi-path (if/else returns)
                LOW for recursive returns
**Module:** 3

#### Sub-patterns Module 3 will resolve:

```python
# Single-path — HIGH confidence
def get_conn():
    return DatabaseConnection()    # traceable

# Multi-path — MEDIUM confidence
def get_service(mode: str):
    if mode == "fast":
        return FastService()       # either FastService
    return StandardService()       # or StandardService → AMBIGUOUS

# Conditional with default — MEDIUM confidence
def get_processor(config):
    if config.enabled:
        return ActiveProcessor()
    return NoOpProcessor()         # resolvable with UNCERTAIN flag
```

---

### Category 3 — Dynamic/Runtime Dispatch

```python
# Pattern A — Dictionary registry
SERVICES = {"email": EmailService, "sms": SMSService}
service = SERVICES[user_input]()   # key unknown at write time
service.send(message)              # UNRESOLVED

# Pattern B — String to class
cls = globals()[class_name]        # class_name from config
obj = cls()
obj.run()                          # UNRESOLVED

# Pattern C — Plugin registry
handler = registry.get("processor") # registered at runtime
handler.process()                    # UNRESOLVED
```

**Why unresolved:** Class identity determined at runtime.
Static analysis cannot know the key/string value.
**Solution:** Registry map extraction — Module 3 (partial)
             Full resolution requires runtime instrumentation
**Estimated yield:** ~10% (registry maps only)
**Confidence:** UNCERTAIN — all possible types listed, none confirmed
**Module:** 3 partial / Module 9 documents the remainder

#### What Module 3 CAN do for Category 3:

```python
# Module 3 reads the registry definition:
SERVICES = {
    "email": EmailService,
    "sms":   SMSService,
    "push":  PushService,
}

# Builds REGISTRY_MAP:
#   "email" → EmailService
#   "sms"   → SMSService
#   "push"  → PushService

# When it sees: service = SERVICES[key]()
# Output:
#   POSSIBLE_TYPES: [EmailService, SMSService, PushService]
#   CONFIDENCE: UNCERTAIN
#   REASON: RUNTIME_KEY_UNKNOWN
```

#### What can never be resolved (hard wall):

```python
obj = importlib.import_module(module_name).get_class()
obj.run()   # module_name is runtime input — impossible
```

---

## Resolution Roadmap

| Category | Pattern | Module | Confidence | Estimated Yield |
|---|---|---|---|---|
| 1 | Type-annotated params | Module 2 (now) | HIGH | 15-25% |
| 2 | Untyped returns — single path | Module 3 | HIGH | 30-40% |
| 2 | Untyped returns — multi path | Module 3 | MEDIUM | 10-15% |
| 3 | Registry maps | Module 3 | UNCERTAIN | ~10% |
| 3 | String-to-class | Module 3 | UNCERTAIN | ~5% |
| 3 | Plugin/dynamic | Module 9 (documented) | NONE | 0% |
| — | Hard wall | Never | — | ~30% |

---

## Real-World Evidence from 76-Repo Corpus

| Resolver | Resolved | Note |
|---|---|---|
| builtin_type | 286,477 | list/dict/str methods |
| constructor | 54,194 | obj = MyClass() patterns |
| factory | 558 | create_x() patterns |
| property | 3,175 | @property access |
| inheritance | 23,209 | child.parent_method() |
| reflection | 0 | known gap — dynamic getattr |
| annotation (new) | TBD | type-annotated params |

---

## Truth Boundary Statement

```
CodeTruth V3 does not claim to resolve all attribute_calls.

What it resolves: evidence-based, statically provable calls.
What it documents: every unresolved call with a specific reason.
What it never does: guess or fabricate a resolution.

The ~30% hard wall is not a failure.
It is the honest limit of static analysis.
Any tool claiming 100% resolution is either:
  - Requiring mandatory type annotations (mypy mode)
  - Guessing
  - Using runtime data (not static analysis)

CodeTruth documents the limit.
That IS the Truth Boundary.
```

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
