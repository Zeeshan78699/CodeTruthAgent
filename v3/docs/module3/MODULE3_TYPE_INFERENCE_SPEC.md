# CodeTruth V3 — Module 3 Type Inference Specification

**Module:** Module 3 — Repository Reasoning Engine
**Date:** 2026-06-25
**Scope:** Category 2 full solution + Category 3 partial solution

---

## Module 3 Objective

> *Module 2 knows what calls what.*
> *Module 3 knows what type flows where.*

```
Module 1  What is this repository?
Module 2  What calls what?
Module 3  What type flows where?
```

---

## Component Architecture

```
module3_reasoning/
├── __init__.py
├── return_type_inferencer.py      ← Category 2: single-path returns
├── data_flow_tracer.py            ← Category 2: cross-function flow
├── variable_type_propagator.py   ← Category 2: variable type tracking
├── cross_module_type_resolver.py ← Category 2: cross-file resolution
├── registry_map_extractor.py     ← Category 3: dictionary registries
├── string_to_class_resolver.py   ← Category 3: string-based dispatch
├── ambiguity_classifier.py       ← flags UNCERTAIN/AMBIGUOUS results
├── type_confidence_scorer.py     ← scores each resolution 0-100
└── reasoning_report_builder.py   ← builds the Module 3 report
```

---

## Component 1 — return_type_inferencer.py

**Solves:** Category 2, single-path returns

```python
# Input code:
def get_connection():
    return DatabaseConnection()

def get_service(mode: str):
    if mode == "fast":
        return FastService()
    return StandardService()

# Output:
{
  "get_connection": {
    "return_type": "DatabaseConnection",
    "confidence": "HIGH",
    "path_count": 1
  },
  "get_service": {
    "return_type": ["FastService", "StandardService"],
    "confidence": "MEDIUM",
    "path_count": 2,
    "flag": "AMBIGUOUS_RETURN"
  }
}
```

**Algorithm:**
```
1. Parse all function definitions
2. Collect all return statements
3. If all returns → same type: HIGH confidence
4. If returns → multiple types: MEDIUM + AMBIGUOUS flag
5. If return value is a function call: recurse one level
6. If recursive or complex: LOW + UNCERTAIN flag
```

---

## Component 2 — data_flow_tracer.py

**Solves:** Category 2, cross-function variable tracking

```python
# Input code:
conn = get_connection()   # return type: DatabaseConnection (from Component 1)
conn.execute("SELECT")    # UNRESOLVED today → RESOLVED by Module 3

# Trace:
conn = get_connection()
     ↓
get_connection() returns DatabaseConnection   (from return_type_inferencer)
     ↓
conn : DatabaseConnection
     ↓
conn.execute() → DatabaseConnection.execute()
     ↓
RESOLVED — HIGH confidence
```

**Algorithm:**
```
1. Build assignment graph: {var: source_expression}
2. For each assignment: resolve source type
   - Direct constructor: obj = MyClass() → HIGH
   - Factory return:     obj = get_x()   → use return_type_inferencer
   - Parameter:         obj: MyClass    → HIGH (annotation)
   - Unknown:           obj = complex() → UNCERTAIN
3. Propagate type through variable lifetime
4. Resolve attribute_calls using resolved variable types
```

---

## Component 3 — variable_type_propagator.py

**Solves:** Category 2, type tracking within a function

```python
def run():
    conn = DatabaseConnection()   # conn: DatabaseConnection
    conn.connect()                # RESOLVED

    if condition:
        conn = OtherConnection()  # conn reassigned
    
    conn.execute()                # AMBIGUOUS — could be either
```

**Algorithm:**
```
1. Track variable type at each assignment point
2. Detect reassignment — flag as AMBIGUOUS if type changes
3. Within a single type lifetime: resolve confidently
4. After reassignment: flag MULTI_TYPE_CANDIDATE
```

---

## Component 4 — cross_module_type_resolver.py

**Solves:** Category 2, cross-file type inference

```python
# file: services.py
from models import DatabaseConnection

def get_conn():
    return DatabaseConnection()

# file: pipeline.py
from services import get_conn

conn = get_conn()
conn.execute()    # UNRESOLVED today → needs cross-module trace
```

**Algorithm:**
```
1. Build import graph (already in Module 2)
2. Resolve imported function return types
   using return_type_inferencer on the source file
3. Apply to call sites in importing files
4. Limit recursion depth to 3 levels
   (beyond 3 = UNCERTAIN)
```

---

## Component 5 — registry_map_extractor.py

**Solves:** Category 3, dictionary registries (partial)

```python
# Input code:
SERVICES = {
    "email": EmailService,
    "sms":   SMSService,
    "push":  PushService,
}

handler = SERVICES[key]()
handler.send(message)
```

**Algorithm:**
```
1. Find module-level dict assignments
2. Check if values are class references
3. If yes → build REGISTRY_MAP
4. When a dict lookup is used as constructor:
   mark all possible types
5. Resolve method calls against all possible types
6. Flag as MULTI_TYPE_CANDIDATE + UNCERTAIN
```

**Output:**
```json
{
  "SERVICES": {
    "type": "class_registry",
    "entries": {
      "email": "EmailService",
      "sms": "SMSService",
      "push": "PushService"
    },
    "usage_sites": [
      {
        "module": "handler",
        "lineno": 5,
        "resolution": {
          "possible_types": ["EmailService", "SMSService", "PushService"],
          "confidence": "UNCERTAIN",
          "reason": "RUNTIME_KEY_UNKNOWN"
        }
      }
    ]
  }
}
```

---

## Component 6 — string_to_class_resolver.py

**Solves:** Category 3, string-based class dispatch (partial)

```python
# Input code:
class_map = {
    "validator": DataValidator,
    "processor": DataProcessor,
}

cls = class_map.get(config["type"])
obj = cls()
obj.process()
```

**Algorithm:**
```
Same as registry_map_extractor but for:
- dict.get() patterns
- globals()[name] patterns (limited)
- getattr(module, name) patterns (limited)
```

---

## Confidence Scoring

```
RESOLVED        — one type, HIGH confidence
                  direct constructor or annotation

INFERRED        — one type, MEDIUM confidence
                  traced through 1-2 function calls

AMBIGUOUS       — multiple types, all known
                  multi-path return or reassignment

UNCERTAIN       — multiple types, from registry
                  key unknown at static analysis time

UNRESOLVABLE    — dynamic dispatch, runtime input
                  documented with reason, not guessed
```

---

## Resolution Ceiling by Component

```
Component 1  return_type_inferencer     → +20-30% of remaining
Component 2  data_flow_tracer           → +15-20% of remaining
Component 3  variable_type_propagator  → +5-10%  of remaining
Component 4  cross_module_type_resolver → +5-10%  of remaining
Component 5  registry_map_extractor    → +3-5%   of remaining (UNCERTAIN)
Component 6  string_to_class_resolver  → +2-3%   of remaining (UNCERTAIN)

Total Module 3 yield: ~50-75% of what remains after Module 2
Hard wall remaining:  ~25-30% (dynamic runtime dispatch)
```

---

## Integration with Module 2 Output

```python
# Module 3 takes Module 2 output as input:

module2_report = PythonAdapter().scan(repo_root=repo_path)
unresolved     = module2_report["deep_resolution"]["remaining_unresolved_entries"]

# Module 3 runs:
module3_report = ReasoningEngine(
    unresolved_entries = unresolved,
    repo_path          = repo_path,
    module2_graphs     = module2_report,  # uses call/import graphs
).resolve()

# Combined output:
{
  "module2_resolved": 367613,
  "module3_resolved": {
    "return_type":    120000,
    "data_flow":       80000,
    "variable_prop":   25000,
    "cross_module":    30000,
    "registry_map":    15000,
    "string_class":     8000,
  },
  "total_resolved": 645613,
  "remaining":      1424041,
  "hard_wall":      "DOCUMENTED"
}
```

---

## Truth Boundary — Module 3

```
Module 3 resolves what can be proven by reasoning.
Module 3 flags what is ambiguous.
Module 3 documents what is impossible.

NEVER: guess a type without evidence
NEVER: claim HIGH confidence on UNCERTAIN resolution
ALWAYS: document the reason for every unresolved call
ALWAYS: preserve the Truth Boundary
```

---

## Build Order for Module 3

```
Phase 1 — Foundation (build first)
  return_type_inferencer.py
  variable_type_propagator.py

Phase 2 — Flow (build second)
  data_flow_tracer.py
  cross_module_type_resolver.py

Phase 3 — Registry (build third)
  registry_map_extractor.py
  string_to_class_resolver.py

Phase 4 — Reporting
  ambiguity_classifier.py
  type_confidence_scorer.py
  reasoning_report_builder.py
```

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
