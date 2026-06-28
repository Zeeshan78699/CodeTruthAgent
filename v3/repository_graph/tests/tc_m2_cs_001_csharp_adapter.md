# TC_M2_CS_001 — C# Adapter Validation

| Field | Value |
|---|---|
| Status | PASS |
| Date | 2026-06-26 |
| Framework | aspnet_core |
| Files Scanned | 4 |
| Governance Gate | APPROVED |

## Graph Nodes

| Type | Count |
|---|---|
| Classes | 6 |
| Interfaces | 3 |
| Enums | 0 |
| Structs | 0 |
| Namespaces | 4 |
| **Total** | **13** |

## Graph Edges

| Type | Count |
|---|---|
| Method Calls | 32 |
| Constructor Calls | 3 |
| DI Dependencies | 2 |
| **Total** | **37** |

## Resolution

| Metric | Value |
|---|---|
| Resolved | 4 |
| Unresolved | 33 |
| Resolution % | 10.81% |

## Requirement Traceability

| Requirement | Status |
|---|---|
| CS-001 Class Detection | PASS |
| CS-002 Interface Detection | PASS |
| CS-003 Namespace Resolution | PASS |
| CS-004 DI Pattern Detection | PASS |
| CS-005 Framework Detection | PASS |
| CS-006 Governance Gate | PASS |

## C# Deep Resolution Status

| Resolver | Status | Evidence |
|---|---|---|
| field_type_resolver | ✅ Implemented | ✅ 28 resolutions demonstrated |
| interface_resolver | ✅ Implemented | Not yet independently demonstrated |
| di_constructor_resolver | ✅ Implemented | Not yet independently demonstrated — applicable calls resolved by field_type_resolver in this fixture |

## Overall Resolution

| Stage | Resolved | Total | Pct |
|---|---|---|---|
| Core graph engine | 4 | 37 | 10.81% |
| After Deep Resolution | 32 | 37 | 86.49% |