# 0043 — minblk=4 twisted-Kummer A4 producer (batch extractor)

**Family:** imprimitive quartic-kernel towers (minblk=4, the 150-pair non-solvable cluster).
**Date:** 2026-07-06.
**Question:** the resumed module-control agent cracked 3 groups then died at the session limit —
can the proven construction be turned into a producer that mechanically covers the rest of the
cluster?

## What the engine is

Twisted-Kummer A4-quartic over a totally-real sextic top `F` sharing the cyclic cubic
`x^3-3x-1`. Over the degree-18 field `rnfinit(F, cubic).polabs` (the expensive object — one
`bnfinit` per base, which is why the agent serialized it), pick a completely-split prime `q`
(18 primes above), form the 18 principal generators, and classify each by its **block** (1-6,
which sextic prime it sits over) and **coset** (0-2, mod the cubic). The module-control
parameter is a choice of **3 blocks × the 3 cosets** — `J=[bc[b1,1],bc[b2,2],bc[b3,3]]` — which
selects the C2^12 submodule and thus the exact 24Tt. `buildJ` turns it into the quartic
`x^4-2·S1·x^2-8·T·x+(S1^2-4·S2)`, `rnfequation` lifts to degree 24. Sweeping `C(6,3)=20`
block-triples per prime enumerates the reachable submodules; `match.py` L1-labels each against
the targets' GAP Chebotarev distributions.

## Build

- `scripts/mb4_sweep.gp` — the agent's proven `R_qsweep` driver, generalized to read params
  (`BASE`/`WANT`/`PREF`/`QSTART`/`NQ`/`SPOUT`) and compute the degree-18 `bnf` fresh (no cache),
  so it runs on any LMFDB sextic base.
- `scripts/mb4_producer.py` — orchestrator: per top (6T12/14/15/16) pull totally-real sextics,
  run the sweep, L1-label (`mb4_match.py`), keep OPEN + scoreable + `L1<0.25 ∧ margin>0.05`
  winners → `data/processed/mb4_winners.jsonl` and (`--enqueue`) the search queue @ priority 100.

## Verification

- Port reproduces winner-quality hits from a **fresh** `bnfinit` (no cache) on the s6 base:
  15 candidates emitted, label path confirms 24T22350 r=4 at L1 0.215/0.236, margin ~0.53.
- Design choice — batch extractor, NOT a daemon kind: the per-base `bnfinit(deg-18)` is far too
  heavy for the daemon's hot path; a background batch that emits `lit:` polys the daemon then
  submits keeps the hot path clean and the construction correct.

## Prior recovery (same day)

The dead agent's checkpoints were mined first: `match.py` over its 172 swept cycle-type tallies
gave clean hits (18420 L1=0.064, 19631=0.093, 21449=0.128); 8 finished polys in `R_fin_*.txt`
validated OPEN + scoreable across 24T18420/19631/22350 (5 pairs) and were enqueued directly.
The `.pol` intermediates (L1>1.0) were correctly rejected as pre-breakthrough wreath-sisters.
