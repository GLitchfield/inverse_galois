# 0024 — Disc-min (#4), trinomial sweep (#6), Belyi/A24 (#5 tail)

**Family:** optimization / coverage · **Date:** 2026-06-27 · **Modules:** `scripts/search_ctl.py`
(`produce-trinomials`), `igp/lmfdb.py`

## #4 — discriminant minimization (validated lever)

Re-realize a *beatable* group over an LMFDB **minimal-discriminant base** of the same top. PoC:
**24T2595** (D₆=12T3 top, our disc 37 digits, leaderboard min 26):
- LMFDB's smallest 12T3 field has an **11-digit** disc (vs our compositum base); route to 24T2595
  over it (`kernel_labels_for_top` finds the pattern) + `galois_c2` → **nfdisc 34 digits** (was
  37). Submitted.
- The residual (34 vs 26) is the split prime (139) + kernel weight; the full GA over
  (base × prime × pattern) would close it. The LMFDB producer (#1) already makes *new*
  constructions minimal-disc by using small-disc bases.

## #6 — trinomial sweep (live)

`produce-trinomials` enqueues irreducible degree-24 trinomials `x²⁴+a·xᵏ+b` as `ready` polys
(new daemon kind that submits a pre-built polynomial). 48 enqueued; the daemon submits and Magma
labels (trinomial groups are varied — metacyclic / imprimitive / A24–S24). Cheap fan-out; harvest
reveals coverage (and possibly A24).

## #5 tail — Belyi / A24

- **LMFDB has 0 degree-24 Belyi maps** (`belyi_galmaps`), so non-baseline primitive/non-solvable
  families need per-paper literature fetches (the M₂₄/Müller recipe, group by group) — deferred.
- **A24** (24T24999): not in LMFDB ⇒ non-baseline ⇒ *would score*, but needs a square-discriminant
  degree-24 polynomial — deferred (the trinomial sweep may surface one).
- Primitive coverage stands at **4/5** (M₂₄ scored; PSL(2,23), PGL(2,23), S₂₄ baseline).

## Six-angle status (all touched)

| # | angle | status |
|---|---|---|
| 1 | DB mining | **done** — LMFDB Postgres mirror, `produce-lmfdb` live |
| 2 | resolvent identifier | researched/scoped (p-adic resolvent sub-project) |
| 3 | class field theory | researched/scoped (`bnrclassfield` too heavy) |
| 4 | disc-min | **lever validated** (LMFDB min bases; 24T2595 37→34); GA = extension |
| 5 | Q(t)/Belyi families | 4/5 primitive (M₂₄ scored); A24 + literature families deferred |
| 6 | trinomial/generic sweep | **live** (48 trinomials in the daemon) |
