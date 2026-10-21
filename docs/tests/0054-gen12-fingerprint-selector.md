# 0054 — gen12 disc-defense v3: block-incidence fingerprint selector — the pre-filter works, the build is still BLOCKED

**Family:** disc-defense (self-competition) over the `gen12` = general_c2 producer.
**Date:** 2026-07-07. **Depends on:** test 0052 (v2 harden: reuse-`w` got 0/80), test 0051 (v1
base-swap 0/390), auto_log 2026-07-07 "gen12 kernel-submodule ALIGNMENT" + "Block-system / subfield
alignment" dives (the recipe). **Deliverable:** `scripts/defend_fingerprint.py` (reusable:
`--only`/`--limit`/`--per-pair`/`--l1-max`/`--enqueue`).

**Question (from build_backlog "FINGERPRINT-GUIDED w'-SELECTOR").** test 0052's harden REUSES the
held `w` verbatim over a smaller split prime and lands a different `24Tt` (idealprimedec ordering is
non-canonical, so a fixed `w`-index picks a different `G`-orbit submodule). The 07-07 dive proposed
replacing reuse-`w` with a CANONICAL block-incidence fingerprint selector: the `24Tt` depends only on
the `G`-ORBIT of the selected split-prime subset `S`, and the multiset `{|S ∩ block|}` over all blocks
of all subfields (`nfsubfields`) is a `G`-invariant of that orbit. Validate on 12232,0 (tc=5), then
sweep the prime-slack behind subset: does a fingerprint-matched `w'` at a smaller `q'` pass the density
gate AND shrink `scoreable_disc`?

**VERDICT: BLOCKED — the fingerprint pre-filter works exactly as designed, but 0/500 top-loss behind
pairs yield a group-preserving smaller-disc build.** The selector is not the limiter; the radical
construction's **principality constraint is not orbit-aligned** — no subset in the *held* `G`-orbit is
principal-buildable at a smaller split prime, so the only fingerprint-matched subsets that DO build
(smaller disc, correct `r`) land in *other* orbits sharing the incomplete fingerprint, and the
validated density gate correctly rejects every one. 0 candidates enqueued.

## The selector is correct (validated on 12232,0)

- `block_partitions(base, q)` (gp helper): reduces `θ` and each subfield generator mod the 12 primes
  above a totally-split `q` (`nfmodpr`), groups the primes into the block system of every subfield.
  Fast for good primes (numerator-mod path, ~3 ms); falls back to maximal-order `nfmodpr` for primes
  dividing the field index (12232's only smaller prime, **89**, divides the index — the subfield
  embeddings carry denominator 89). idealprimedec ordering is deterministic across processes (no RNG;
  `bnfinit`'s randomness touches only class-group data), so the partition-call ordering matches the
  build-call ordering.
- On **12232,0** (base disc-35d field, held `w`=popcount-2 at old_q=593, only smaller split prime =
  89): the fingerprint matched **12 subsets**; **all 12 built valid deg-24, r=0 fields** at q'=89 with
  disc **34 digits < our 35** — the selector delivered orbit-plausible, correct-`r`, smaller-disc
  models. But their density L1 vs our held model ran **0.476 … 0.974** (best 0.476) — all decisively
  DIFFERENT groups (validated same-group ≈ 0.05, diff ≈ 1.06; test 0052). The held subset `{0,11}`'s
  orbit has NO principal representative at q'=89, so it is never built; the 12 buildable
  fingerprint-matches are all in the wrong orbit(s).

## Sweep (top-500 behind-gen12 pairs by recoverable loss)

`python scripts/defend_fingerprint.py --limit 500 --per-pair 2` (batched builder: one `bnfinit` per
prime over all fingerprint-matched subsets):

| outcome | count | meaning |
|---------|------:|---------|
| improved (smaller-disc AND group-preserved) | **0** | — |
| `no_smaller_prime` | 276 (55%) | held model already at its smallest split prime |
| `no_group_preserved_smaller` | 224 (45%) | fingerprint matched (up to 144 subsets), all built smaller-disc + correct-`r`, but every one density-rejected (wrong orbit) |

**0 enqueued** (312 s for 500 pairs; `--limit 40` reproduces the same 0/40 in 24 s). Regenerable via
the command above.

## Why the pre-filter can't fix this (the crisp mechanism)

The block-incidence fingerprint is a genuine `G`-invariant, so **every** member of the held orbit
passes it — the selector never wrongly excludes a true-orbit subset. Therefore 0 group-preserved builds
⟹ **no held-orbit subset is principal-buildable at any smaller split prime** for these pairs.
`general_c2` builds `K = F(√α)` only when `∏_{j∈S} p_j` is **principal** (so `α ∈ F`); principality
depends on the ideal class of that product, which is **not** a `G`-orbit invariant and does **not**
transfer to the relabeled subset at a different prime. Empirically the held orbit's principal
representatives simply don't exist at smaller primes, while other orbits (sharing the incomplete
fingerprint) do — hence smaller-disc builds that are the wrong group. This is a sharper, more complete
diagnosis than test 0052's "prime-swap isn't a pure disc dial": the canonical selector removes the
labeling ambiguity, exposing that the true obstruction is **principality ⟂ orbit**, not alignment.

## Learnings

- **The 07-07 dive's selector is sound and now built** — a canonical, order-independent block-incidence
  `G`-invariant pre-filter with a no-false-positive density gate. It is genuinely better than reuse-`w`
  (DOF-1 lottery → DOF-C(12,k) canonically-guided). It just doesn't clear the *real* wall.
- **The real wall is principality, not labeling.** Targeted gen12 disc-defense with a PARI radical is
  structurally blocked: you need a held-orbit subset whose prime-product is principal at a smaller
  prime, and that essentially never occurs. Fixing labeling (this test) doesn't create principal
  representatives.
- **Reusable byproduct:** `block_partitions` + `fingerprint` + `build_subsets_at` (batched one-`bnfinit`
  radical builder over many subsets) — a fast canonical orbit-type toolkit for any general_c2 orbit work.
