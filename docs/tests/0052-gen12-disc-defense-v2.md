# 0052 — gen12 disc-DEFENSE v2: harvest-broad-w + group-preserving harden both BLOCKED

**Family:** disc-defense (self-competition) over the `gen12` = general_c2 producer.
**Date:** 2026-07-07. **Depends on:** test 0051 (v1: base-swap failed 0/390 on-target), test 0038
(the pattern→group alignment problem), test 0036 (split prime is the `r`-dial),
`scripts/defend_producer.py` (reused `sweep_base`), `scripts/search_ctl.py::produce_harden`.
**Deliverable:** `scripts/defend_harden.py` (reusable, `--build-pool`/`--enqueue`/`--limit`/`--only`).

**Question (from build_backlog "gen12 disc-DEFENSE v2"):** v1 proved a targeted single-`w` base-swap
lands the wrong group. v2 proposed two salvage routes: (A) harvest MANY `(w, q)` over small-disc
bases + a post-hoc Magma-label filter, and (B) extend `produce_harden`'s same-base-smaller-prime
(group-PRESERVING) rebuild to the SHARED (behind) pairs for the small-gap subset. Can either produce
enqueueable, LOCALLY-GATED, group-preserved, smaller-disc models to recover the ~117-pt behind-gen12
loss?

**VERDICT: NO — BLOCKED on both routes for a locally-gated (budget-safe) build.** The root cause of
v1 generalizes: gen12's `w`→`24Tt` map is **alignment-dependent on the `idealprimedec` ordering of
the primes above the split prime**, and that ordering is **non-canonical across BOTH different bases
(test 0051) AND different split primes over the SAME base (this test)**. So no local rebuild —
base-swap OR prime-swap — preserves the target group at a smaller disc. The only route that works is
untargeted broad harvest + **post-hoc Magma** filter, which floods submission budget on unverifiable
speculation → **out of scope for the headless build loop** (and test 0051 already spent 705
submissions that way for 0/390 on-target). 0 candidates enqueued.

## The density gate (validated) — the tool that made the verdict honest

To gate group-preservation LOCALLY (not by burning a Magma submission), compare a rebuilt candidate's
Frobenius cycle-type density directly to **our own Magma-confirmed held model's** density (both
empirical, ~1000–1500 unramified primes each). Same field ⇒ same Galois group ⇒ same density (up to
sampling noise); the shared sampling cancels the fingerprint noise that made a raw GAP-fingerprint
match unreliable (our own held 24T20054 model scored L1=0.67 vs a 20k-sample GAP fingerprint — too
noisy to gate on).

**Controls (`scripts/defend_harden.py::frob_density`/`l1`):**

| control | L1 |
|---------|---:|
| same field, two independent prime ranges (24T17775) | **0.063** |
| same field, two independent prime ranges (24T8655) | **0.047** |
| two DIFFERENT groups (24T17775 vs 24T8655) | **1.064** |

Same-group ≈ 0.05, different-group ≈ 1.06 → the gate threshold `l1_max=0.35` is well-separated and
sound. Every "group_not_preserved" case below sits at L1 ≥ 0.35 (mostly 0.5–0.95), i.e. genuinely a
DIFFERENT group, not sampling noise.

## Route A — harvest-broad-w + local density labeler (validation, worst pair 24T20054 r12)

- Harvested general_c2 over the SMALLEST-disc 12T227 base (15-digit disc), sweeping all popcount-1 and
  popcount-2 kernels × the smallest split primes → 156 valid deg-24 fields spanning r=0..16, 18 at r=12.
- Density-matched the 18 r=12 models against a 20k-sample GAP fingerprint of 24T20054 (order 393216).
  **Best L1 = 0.84** — NO match (our own confirmed 24T20054 model scores 0.67 against the same
  fingerprint). The bounded low-popcount harvest over the small base does **not** contain the 24T20054
  submodule, and the GAP-fingerprint labeler is too noisy (0.67 vs 0.84 separation) to gate confidently.
- Conclusion: the honest local filter can't confirm on-target landings; the recipe's actual filter is
  post-hoc Magma (out of scope). Route A does not yield locally-gated candidates.

## Route B — group-preserving harden extended to behind pairs (the primary attempt)

Reuse the EXACT base + EXACT `w` our held model was built from; only lower the completely-split prime
`q` (< old_q). Gate: deg-24 irreducible ∧ `polsturm == r` ∧ local nfdisc **strictly < ours** ∧
density L1 ≤ 0.35 vs the held model. Ran on the top 80 behind-gen12 pairs by recoverable loss
(k∈2..5, weight≥0.06; the top ~2.6% of the 3091-pair pool):

| outcome | count | meaning |
|---------|------:|---------|
| improved (smaller-disc **AND** group-preserved) | **0** | — |
| `no_smaller_prime` | 39 (49%) | held model already uses the smallest split prime < old_q |
| `no_smaller_disc` | 28 (35%) | a smaller prime exists but disc doesn't drop (BASE-dominated) |
| `group_not_preserved` | 13 (16%) | smaller-disc model built, but it's a **DIFFERENT group** (L1 0.35–0.85) |

**0 enqueued.** Two independent failure modes kill it: (1) **84%** of pairs have no smaller-disc harden
model at all — either the split prime is already minimal or the field disc is base² -dominated (harden
can't touch the base); (2) the 16% that DO get a smaller disc land on a **different 24Tt** — confirming
that prime-swap over a fixed base is **not** a pure disc/`r` dial: changing `q` re-orders
`idealprimedec`, and the fixed `w`-index then selects a different kernel submodule (exactly test
0051's base-swap failure, now proven for PRIME-swap too, via the validated density gate).

## Learnings

- **Headline (negative, generalizing test 0051):** the gen12 `w`→`24Tt` map is non-canonical across
  BOTH bases and split primes. There is **no local (base-swap or prime-swap) rebuild** that lowers a
  targeted gen12 pair's field disc while preserving its group. Targeted disc-defense of gen12 is
  structurally impossible without aligning the kernel submodule to a fixed `G`-module (see residual).
- **The prime is not a free disc dial for gen12.** `produce_harden`'s premise ("same base, smaller
  prime ⇒ same group") is FALSE for gen12's popcount≥2 kernels — density-confirmed. Harden "works" for
  our soles only because Magma arbitrates downstream (a wrong relabel silently fails to score); it was
  never verified to preserve the group. For behind pairs where we need a *specific* group at a smaller
  disc, that silent-relabel is the whole failure.
- **A self-relative density gate beats a fingerprint gate.** Matching a candidate to our OWN confirmed
  model (same sampling both sides) cleanly separates same-group (≈0.05) from different-group (≈1.06),
  where a 20k-sample GAP fingerprint could not (0.67 vs 0.84). Reusable for any group-preservation check.
- **Budget discipline held:** the only working route is post-hoc-Magma broad harvest (705 submissions
  for ~21 incidental gains in v1). Refused to flood the queue with unverifiable speculation from a
  headless loop — 0 enqueued, honest BLOCKED.
