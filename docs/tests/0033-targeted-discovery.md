# 0033 — Targeted discovery: constructing toward open 1.0 signatures

**Family:** search / strategy · **Date:** 2026-06-29 · **Code:** `scripts/search_ctl.py`
(`produce_sigfill_targeted`), `src/igp/gp.py` (`real_roots`)

## Question

We hold **0 true 1.0 signatures** (test 0032): our breadth lands on already-discovered (shared,
≤0.5) pairs, never on undiscovered ones. Can we construct *directly* at open 1.0 targets — `(t,r)`
that is valid, non-baseline, and `teamCount==0` (being first ≈ 1.0)?

## Method

The blocker was that we couldn't know a candidate's `(t,r)` before paying for a Magma submission. Two
local computations remove it:
- **group** — a C_2-kernel pattern `w` over a **Galois** degree-12 base has a predictable group
  (`gap.kernel_label_perms(w, perms)`), no construction needed;
- **r** — `gp.real_roots` (new; PARI `polsturm`) computes the real-root count locally and exactly.

`produce_sigfill_targeted` builds the open-target set `{(t,r) : valid, non-baseline, teamCount==0}`,
then over **totally-real** Galois degree-12 bases (so the kernel spans intermediate `r`) it: predicts
each pattern's group (cheap, batched), skips groups with no open target, constructs only the rest,
computes local `r`, and **enqueues only candidates whose `(predicted t, local r)` is an open target**.
Self-throttled ~6h.

## Result

```
89,504 open 1.0 targets (18,190 groups); scanned 72 on-target patterns; enqueued 19 1.0 candidates
```
Across 5 totally-real Galois bases (12T1–5) × 2 each, **19 degree-24 polynomials targeting open 1.0
signatures** — all intermediate-r, undiscovered — queued at top priority (open targets get claimed
~4k/day, so speed matters).

**Confirmed by Magma (same day):** all 19 verified, and **every one landed on exactly the predicted
`(t,r)`** (label *and* real-root count) — a 19/19 hit rate for the local predict-group + `polsturm`-`r`
gate. The scoreboard moved **TRUE 1.0 held 0 → 19** (`analyze_coverage`); these are the project's
first held 1.0 signatures. Labels/r realized: 24T5343@16, 24T5344@12, 24T5345@12, 24T5347@{4,12,20},
24T5503@{12,14}, 24T5504@{6,10,14,18}, 24T5506@12, 24T10264@{8,16}, 24T10268@8, 24T10271@{4,8,16}.

## Learnings

- **First mechanism that aims at 1.0s — and it works.** Everything prior produced shared pairs
  (≤0.5); this targets the only pairs worth ~1.0 we can currently reach, and converted: 0 → 19 held.
  The enablers are purely local: `polsturm` for `r` + kernel-label prediction for the group ⇒ we know
  `(t,r)` *before* submitting, so every submitted candidate is a deliberate 1.0 attempt.
- **Prediction is exact, not approximate.** 19/19 verified at the predicted label and `r`. Over a
  *Galois* base the kernel-label group map is deterministic, and `polsturm` is an exact real-root
  count — so the gate has no false positives. This means we can submit targeted candidates with
  confidence rather than spraying and hoping, which matters under the 100-POST/day cap.
- **Scales easily:** 19 came from just 10 bases; more bases/tops (and the other Galois families)
  multiply the reachable open targets. The producer self-throttles, so it re-scans for newly-open
  targets every ~6h.
- Honest caveat: only C_2-extensions of order-12 groups are reachable this way; the bulk of the
  89,485 open 1.0s need the other tower families extended with the same predict-group + local-r gate
  (the clear next lever).
