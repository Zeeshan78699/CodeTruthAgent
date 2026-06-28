# CodeTruth V3 — Module 2 Capability Matrix

**Date:** 2026-06-25
**Standard:** Implementation status and validation status tracked separately.
No capability is claimed without empirical evidence.

---

## Language Adapter Status

| Adapter | Structural Graph | Deep Resolution Evidence |
|---|---|---|
| Python | ✅ Mature | ✅ Multiple validated resolvers — 76-repo corpus |
| Oracle PL/SQL | ✅ Demonstrated | N/A — structural validation only |
| C# / ASP.NET Core | ✅ Demonstrated | ✅ Field-type resolver demonstrated |
| Go | ✅ Demonstrated | ⚠️ Planned — receiver_type, interface_impl, package_call resolvers |
| Rust | ⚠️ Stub | Not yet implemented |

---

## Python Deep Resolution Resolvers

| Resolver | Implementation | Independent Evidence | Corpus Count |
|---|---|---|---|
| builtin_type | ✅ | ✅ TC_M2_DR_001 — 10/10 resolved | 286,477 |
| constructor | ✅ | ✅ TC_M2_DR_002 — no crash | 54,194 |
| factory | ✅ | ✅ TC_M2_DR_003 — no crash | 558 |
| property | ✅ | ✅ TC_M2_DR_004 — no crash | 3,175 |
| inheritance | ✅ | ✅ TC_M2_DR_005 — no crash | 23,209 |
| reflection | ✅ | ✅ TC_M2_DR_006 — 0 = correct (known gap) | 0 |
| annotation | ✅ | ✅ TC_M2_DR_008 — 15/15 + 27,183 corpus | 27,183 |

---

## C# Deep Resolution Resolvers

| Resolver | Implementation | Independent Evidence |
|---|---|---|
| field_type_resolver | ✅ | ✅ TC_M2_CS_001 — 28 resolutions, 84.85% reduction |
| interface_resolver | ✅ | Not yet independently demonstrated |
| di_constructor_resolver | ✅ | Not yet independently demonstrated — applicable calls resolved by field_type_resolver in TC_M2_CS_001 fixture |

---

## Oracle PL/SQL — Deep Resolution

| Capability | Status | Reason |
|---|---|---|
| Deep Resolution | N/A | SQL does not have attribute_call dominance problem |
| Table references | ✅ Resolved (72%) | Schema-level resolution |
| DBMS_* calls | ✅ Documented | External system packages — correct to leave unresolved |

---

## Go Deep Resolution — Planned Resolvers

| Resolver | Status | Estimated Yield |
|---|---|---|
| receiver_type_resolver | Planned — Phase 1 | 30-40% of remaining |
| package_call_resolver | Planned — Phase 2 | 20-30% of remaining |
| interface_implementation_resolver | Planned — Phase 3 | 25-35% of remaining |

Current Go resolution: 30.43% (structural)
Estimated after DR: 58-67%
See: `docs/GO_DEEP_RESOLUTION_ROADMAP.md`

---

## Overall Resolution Numbers

### Python (76-repo corpus)

```
Core engine              : 1,521,476 calls resolved
DR pipeline              :   367,613 additional (+24.2%)
annotation_resolver      :    27,183 additional (+1.8%)
Total                    : 1,916,272
```

### C# (TC_M2_CS_001 fixture)

```
Core engine              : 4  / 37  (10.81%)
field_type_resolver DR   : 28 / 33  (84.85% of unresolved)
Combined                 : 32 / 37  (86.49%)
```

### Oracle SQL (TC_M2_SQL_001 fixture)

```
Schema resolution        : 18 / 25  (72.0%)
External (DBMS_*)        :  7       (correctly unresolved)
```

---

## Truth Boundary Statement

```
Claimed only:
  What has been measured on real repositories
  or validated synthetic fixtures.

Not claimed:
  Capabilities implemented but not yet
  independently demonstrated on isolating fixtures.

Tracked separately:
  Implementation status  — code exists
  Validation status      — empirically proven
```

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
