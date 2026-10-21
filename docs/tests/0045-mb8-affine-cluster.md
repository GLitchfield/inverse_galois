# 0045 — minblk=8 affine cluster BUILD: validation-first REFUTES the direct-Res recipe

**Family:** minblk=8 octic-over-cubic affine cluster (14051/14052/16060/16061/19280/20408).
**Date:** 2026-07-07.
**Question:** execute the greenlit Route-A build — specialize the Malle Thm 6.1 AGL(3,2)=8T48
octic family at `t = a cubic generator`, `deg24 = Res_y(c(y), f_AGL(a,y,X))`, polredabs,
density-gate — for the six twisted affine targets (28 open pairs). VALIDATION-FIRST: confirm
ONE target lands the right group before mass-building.

**Targets re-verified** tc=0 on every open pair vs `data/processed/progress.json` (this run):
14051 {0,8,24}, 14052 {0,4,8,12,24}, 16060 {0,8,24}, 16061 {0,4,8,12,24}, 19280 {0,4,8,12,16,24},
20408 {0,4,8,12,16,24} = 28 pairs; none in `realized.csv`. (r=24 left to the fix8 agent; I own non-r24.)

## HEADLINE — the greenlit recipe does NOT build the twisted targets

The direct resultant `Res_y(c(y), f_AGL(a,y,X))` lands the **FULL WREATH**, not the twist:

| cubic | direct-Res group | order | element orders |
|---|---|---|---|
| C3 (disc square) | **24T24916 = AGL(3,2) wr C3** | 7,283,146,752 | incl. 9, 18, 84 |
| S3 (disc non-square) | **24T24922 = AGL(3,2) wr S3** | 14,566,293,504 | incl. 8, 9, 18, 84 |

The six assigned targets are the **diagonal-collapsed twists** (the three PSL(3,2) linear parts
identified to ONE): kernel `(C2)^6` for 14051/14052/16060/16061, `(C2)^9=3(+)6` for 19280/20408,
top `(C3|S3)×PSL(3,2)`, max element order 21 — **no order-9 element**. The generic
(disjoint-conjugate-block) resultant never produces that diagonal correlation.

## Evidence (three independent lines, all reproducible)

1. **GAP group orders / element-order sets** (`gap -q`, `TransitiveGroup(24,·)`): 24916 has
   `elordSet ⊇ {9,18,84}`; 19280 = `{1,2,3,4,6,7,12,21}`, 20408 = `{…,8,…,21}`, and
   14051/14052/16060/16061 likewise — **no order-9 element in ANY of the six**.
   `|24916|/|19280| = 28224 = 168²` (the two collapsed PSL(3,2) copies).
2. **Order-9 Frobenius in the built poly.** The direct-Res deg-24 field (C3 cubic
   `y³-y²-2y+1`, several a) has Frobenius cycle type `3,3,9,9` (order 9) at ~12% of primes
   (90/779). An order-9 conjugacy class ⇒ the group has an order-9 element ⇒ it is **none** of
   the six twisted targets. Airtight, independent of the labeler.
3. **Density L1** (`scripts/mb8_affine.py` labeler, dist files in `data/targets/mb8/`):
   C3 candidate → 24T24916 **L1 0.18, 0 impossible**; every twisted target 1.0–1.6 with
   **399–629 impossible** observed types. S3 candidate → 24T24922 **L1 0.22, 0 impossible**;
   20408 shows 482 impossible.

Robust across a ∈ {−4…6} (C3) and the S3 build — every generic specialization is the full wreath.

## Why Route A cannot be steered to the twist, and why Route B is blocked here

- The twist needs the three conjugate octics to **share their PSL(3,2) resolvent** (diagonal).
  Generic fibers over the cubic are independent → full wreath. For a fixed family the
  L3(2)-resolvent is t-dependent (⇒ order-9 elements appear), so no cubic/a choice collapses it.
- The correct construction is **Route B**: realize the AGL(3,2) octic over the cubic as a
  `(C2)^3`-Kummer of a **shared** relative L3(2)-field (the diagonal), radicands module-generated
  by one totally-split prime. This needs the class group / Kummer radicands of a degree-168
  (relative-168-over-cubic) L3(2) field — **out of PARI `bnfinit` reach in-session** (the
  Route-B dive, `docs/auto_log.md` 2026-07-07, flagged exactly this: "far too large to bnfinit").

## Also checked — no Route-A win at any OPEN pair

- Full wreaths 24916/24922: only r{16,20,24} are open (r{0,4,8,12} rival-CLAIMED, tc=1).
- Route-A real-root sweep over 5 cubics × a∈[−9,9] produced **no candidate with r≥14**
  (only r∈{8,12}). So Route A cannot reach the open full-wreath pairs either.

⇒ **Zero polynomials enqueued** — the density gate correctly emits nothing for the twisted
targets, and the reachable Route-A output (24916/24922 r8/12) is rival-claimed. Validation-first
prevented mass-submitting wrong-target polys.

## Deliverables

- `scripts/mb8_affine.py` — reusable Route-A builder + self-contained density labeler + four
  mandatory local gates (deg24+irred; polsturm r; density argmin==requested t with 0 impossible;
  `scoreable_disc` non-blank) + `--enqueue`. For the six twisted targets it emits nothing (by
  design); it correctly builds+labels the full wreaths and is the gate/labeler harness for a
  future Route-B build.
- `scripts/mb8_wreath_dist.g` + `data/targets/mb8/dist_24916.txt`, `dist_24922.txt` — full-wreath
  cycle-type distributions for the labeler (reproducible from the GAP script).

## Correction to the record

The affine-cluster and module-dim dives asserted "DIRECT Res → 19280/20408 (full 9-dim)" and
"sum-zero subfield → 14051/16060." Those were **theoretical GAP-module predictions, never
build-tested**; this build refutes the resultant half of the mapping. The module *structure*
(kernels 6-dim irred / 9-dim 3(+)6, all split & cyclic) stands — but the *field construction* is
NOT the direct Res. This matches the harvest census's own suspicion that generic Res → full wreath
(24916/24922) and the twists need correlated blocks.
