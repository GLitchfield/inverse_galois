# 0041 — Kernel screen of the open minblk∈{3,4} pool → the g8x3s3/g6x4s4 producers

**Family:** coverage / construction-strategy. **Date:** 2026-07-02. Follow-on to test 0040.
**Question:** which quartic/cubic kernel types do the 1,355 open minblk∈{3,4} groups (7,720 open
signatures) actually require — i.e. what exactly should the 6×4/8×3 producer expansion build?

## Method

For each open (teamCount==0, non-baseline, unrealized) minblk∈{3,4} group: GAP computes the minimal
block system, the top action on blocks (`TransitiveIdentification` of the block action), and the
**kernel type** = the block stabilizer's induced action on one block (4T/3T id). Screen:
`AllBlocks → Orbit → Action → Stabilizer` over the 1,355 targets (~7 min).
Data committed: `data/targets/kernel_screen_minblk34.csv` (t, minblk, kernel id, top label).

## Result (decisive)

| shape | required kernel | groups | open sigs |
|---|---|---|---|
| 8×3 | **S3** (non-Galois cubic) | 606 | 2,728 |
| 6×4 | **S4** (generic quartic) | 541 | 3,706 |
| 6×4 | **A4** (square rel. disc) | 206 | 1,279 |
| 8×3 | C3 (cyclic) | 2 | 2 |

**Zero open groups need V4, C4, or D4 kernels.** The planned `_BIQ_PAIRS`/biquadratic expansion
(V4) would have hit nothing; `x^4-α` (D4-type closure — its resolvent cubic always factors) would
also miss the S4 stratum. Top base-groups by demand: 6T3/6T11/6T13/6T9/6T7 (S4-kernel), 8T35/8T26/
8T31 (S3-kernel) — all abundantly available in the LMFDB mirror.

## Built (this test)

- `gp.general_cubic` — x³−α over a deg-8 base (α = product-ideal generator over a completely-split
  prime, exactly `general_c2`'s α) → S3-type blocks. `gp.general_quartic` — x⁴+αx+α over a deg-6
  base; resolvent cubic x³−4αx−α² generically irreducible → S4-type blocks. Shared `_general_radical`
  driver, base degree inferred from coeffs.
- Daemon kinds `general_cubic`/`general_quartic` (parallel-pool construction); producers
  `produce_g8x3`/`produce_g6x4` (`search_ctl produce-g8x3/-g6x4`, force-first-wave): LMFDB cursor
  (kv `g8x3s3_offset`/`g6x4s4_offset`, per_group=3, class_number=None), split-prime sweep
  (n_primes=3 — the free `r` dial, test 0036), 3 α-patterns; in the 30-min tick rotation,
  self-pacing on queue depth. Bandit prefixes `g8x3s3`/`g6x4s4` registered (+`lit`/`monster`).
- Smoke-verified: both builders produce monic irreducible degree-24 polys on first-try LMFDB bases
  (6T5, 8T17). First wave: 504 rows enqueued at priority 5.0 (above the recovery backlog).

## Learnings

1. Screen before building: the "obvious" expansion (more V4 patterns) had literally zero targets.
2. The A4 stratum (1,279 sigs) needs relative-disc-square steering — deferred (needs a different α
   selection, not a different kernel poly).
3. Yield check pending: Magma labels of the first wave tell us the realized-vs-predicted kernel mix
   (the S4-generic claim is generic, not per-candidate — the bandit + labels calibrate it).

## Reproducibility

Screen: `scripts/gap/` pattern of test 0040 (AllBlocks + Stabilizer + TransitiveIdentification; the
one-off GAP driver is recorded in this test's commit). Producers: committed code; first wave =
`search_ctl produce-g8x3 && produce-g6x4` with cursors at 0.
