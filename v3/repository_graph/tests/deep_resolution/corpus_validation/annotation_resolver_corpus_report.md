# Annotation Resolver — Corpus Validation Report

**Date:** 2026-06-26
**Repos:** 5 | **OK:** 5 | **Errors:** 0

## Summary

| Metric | Value |
|---|---|
| Total baseline unresolved | 694,473 |
| Resolved by DR pipeline   | 87,578 |
| Resolved by annotation    | 27,183 |
| Total resolved            | 114,761 |
| Still unresolved          | 579,712 |
| Overall reduction         | 16.52% |

## Per-Repository Results

| Repo | Files | Baseline | DR Resolved | Ann Resolved | Ann% | Total% |
|---|---|---|---|---|---|---|
| fastapi | 1120 | 11,413 | 3,013 | 39 | 0.46% | 26.74% |
| pytorch | 4620 | 488,557 | 41,024 | 26,975 | 6.03% | 13.92% |
| OpenMDAO | 631 | 63,427 | 13,928 | 16 | 0.03% | 21.98% |
| django | 2920 | 104,871 | 21,624 | 25 | 0.03% | 20.64% |
| biopython | 546 | 26,205 | 7,989 | 128 | 0.7% | 30.98% |

## Annotation Resolver Detail

| Repo | Annotations Found | Classes Indexed | Resolved | Coverage |
|---|---|---|---|---|
| fastapi | 2560 | 99 | 39 | 0.46% |
| pytorch | 43007 | 11619 | 26975 | 6.03% |
| OpenMDAO | 58 | 1602 | 16 | 0.03% |
| django | 68 | 4473 | 25 | 0.03% |
| biopython | 406 | 1000 | 128 | 0.7% |

## Resolver Breakdown (DR Pipeline)

| Repo | builtin_type | constructor | factory | property | inheritance |
|---|---|---|---|---|---|
| fastapi | 2,928 | 84 | 1 | 0 | 0 |
| pytorch | 37,144 | 2,952 | 90 | 674 | 164 |
| OpenMDAO | 4,488 | 9,268 | 0 | 0 | 172 |
| django | 12,796 | 1,599 | 171 | 223 | 6,835 |
| biopython | 7,456 | 383 | 2 | 3 | 145 |

## Verdict

```
annotation_resolver validated on 5 real-world repositories.
Total additional resolutions: 27,183
DR pipeline resolved:         87,578
Combined reduction:           16.52%
Category 1 attribute_call gap: ADDRESSED
Module 2 Deep Resolution:      READY FOR FREEZE
```

*CodeTruth Agent V3 — AI imagines. CodeTruth checks. Nature tests. Humans decide.*