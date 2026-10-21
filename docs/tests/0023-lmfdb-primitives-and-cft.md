# 0023 — LMFDB mirror access, primitive coverage (#5), CFT research (#3)

**Family:** infra / DB / construction · **Date:** 2026-06-27 · **Modules:** `igp/lmfdb.py`,
`scripts/search_ctl.py` (`produce-lmfdb`)

## LMFDB access (the enabler — no user action needed)

The LMFDB web UI **and** JSON API are reCAPTCHA-walled, but the underlying database is a public
**read-only PostgreSQL mirror** (`devmirror.lmfdb.xyz`, user/pass `lmfdb`) — no captcha. So DB
mining (#1) is fully unblocked: `igp/lmfdb.py` queries `nf_fields` for `coeffs`, `galois_label`,
`disc_abs`, `class_number`. `produce-lmfdb` mines diverse small-disc degree-6 bases (exact 6Tj
labels, h=1) → general 6×4 for the daemon (21 fields, 60 constructions, first run).

Note: LMFDB's degree-24 fields are **exactly the frozen 286-group baseline** (18,252 fields, 286
distinct labels).

## #5 — primitive / hard groups via LMFDB + families

LMFDB *has* degree-24 fields for the two hard primitives we lacked: pulled and verified
**PSL(2,23) (24T7817)** and **PGL(2,23) (24T10255)**. They're baseline (`scoreable=False` —
coverage, not new points), but this completes **4 of 5 primitive groups** (M₂₄, S₂₄, PSL(2,23),
PGL(2,23)). **M₂₄ is the one NOT in LMFDB** — our Müller realization is genuinely beyond
baseline (and scored). Remaining: **A₂₄ (24T24999)** — not in LMFDB, so non-baseline and would
*score*, but needs a square-discriminant degree-24 polynomial (deferred).

## #3 — class field theory (researched, deferred)

CFT (ray class fields) is the principled small-disc route: `bnrinit` + `bnrclassfield` build
abelian-over-F extensions with prescribed conductor → minimal, controlled discriminant. But
**`bnrclassfield` is heavy** here — timed out (>90 s) even over a degree-6 base. A robust CFT
producer needs conductor selection + timeout engineering (a real sub-project, like #2's p-adic
resolvent). For now disc-min is served by **#1's LMFDB small-disc bases** + the α=−1 diagonal
trick; CFT is scoped for when those plateau.

## Status of the six angles

#1 done (LMFDB mining live). #2 researched/scoped. #3 researched/scoped. #5 partial (4/5
primitive; A₂₄ + non-LMFDB families remain). #4 (disc-min GA) and #6 (trinomial/generic sweeps)
not yet started. The daemon runs all producers hands-off.
