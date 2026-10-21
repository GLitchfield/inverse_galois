# 0034 — Targeted discovery across all prediction-capable families

**Family:** search / strategy · **Date:** 2026-06-29 · **Code:** `scripts/search_ctl.py`
(`produce_sigfill_targeted` + `_tsig_c2`/`_tsig_c2multi`/`_tsig_biq`), `src/igp/gap.py`
(`biquadratic_labels_batch`)

## Question

Test 0033's targeted gate (predict group + local `r` → submit only at open 1.0 targets) used one
construction family — single-generator C₂-kernels over deg-12 Galois bases. The gate needs only a
**local group prediction** (local `r` via `polsturm` is already family-agnostic). Which other
construction families have a local predictor, and does extending the gate to them find more open 1.0s?

## Method

Refactored `produce_sigfill_targeted` into a multi-family orchestrator sharing one gate (open-target
set + `_gates` local-`r` check + enqueue) over three **prediction-capable** tower families:

- **`c2`** (2×12) — single quadratic generator over deg-12 Galois totally-real bases;
  predict `gap.kernel_labels_for_top`, construct `gp.galois_c2`. (Test 0033.)
- **`c2multi`** (2×12) — **non-cyclic** kernels (≥2 generators, distinct split primes) over the same
  bases; predict `gap.kernel_labels_multigen`, construct `gp.galois_c2_multi`. Reaches groups whose
  kernel is not cyclic — invisible to `c2`.
- **`biq`** (4×6) — biquadratic V₄-block `F(√β₁,√β₂)` over deg-6 Galois totally-real bases; predict
  the new batched **`gap.biquadratic_labels_batch`**, construct `gp.biquadratic_c2`.

The batched biquadratic labeler was checked against the per-call `biquadratic_label` on the C₆ regular
action (3 patterns) — exact match (24T1156/1158/183).

## Result

```
89,504 open 1.0 targets; scanned 82 on-target, enqueued 21 (c2=19, c2multi=2, biq=0)
```
- **`c2multi` +2 (new):** `24T7825` @ r∈{12,16} — a size-2-block group reachable **only** via a
  2-generator kernel (single-generator `c2` cannot produce it). Queued at top priority; verification
  pending (the `c2` predictor scored 19/19 in 0033 and `c2multi` shares that GAP prediction path, so
  high confidence).
- **`c2` 19 (dedup):** re-confirms the 0033 hits; `engine.submit` dedups against `db.submitted_lines`
  so these are filtered pre-POST (marked `dup`) — no wasted submission under the 100/day cap.
- **`biq` 0 — a strategic finding, not a bug.** The V₄-block groups reachable over deg-6 bases cluster
  in the **low-T / size-4-block region** (24T155–1178), and every one is already discovered
  (teamCount ≥ 1) or baseline. The open 1.0 targets are concentrated in the **high-T size-2-block
  region** (24T5xxx, 24T10xxx) — exactly where the deg-12 `c2`/`c2multi` families work.

## Learnings

- **The gate generalizes cleanly; the binding resource is the per-family group predictor.** Local `r`
  and the open-target set are family-agnostic; each family only needs a local label predictor over a
  Galois base. We now have three (single, multi-gen, biquadratic).
- **Open 1.0s live in the size-2-block region.** Where a family lands in the 24T numbering decides its
  open-target headroom: deg-12 bases (12 blocks of 2) reach the under-explored high-T groups; deg-6
  bases (6 blocks of 4) reach a small, already-saturated low-T set. So the deg-12 families are the
  workhorses and `biq` is currently a no-op — but it self-rescans every ~6h and will catch its region
  if it ever opens.
- **The remaining families (compositum `g6x4`/`size4`/`c8x3`/`size3`, sparse `quad`/`pent`/`tri`) have
  no local predictor** — their group is a sub(direct) product determined by how the base fields glue
  (compositum) or simply unknown until verified (sparse). Extending the gate to them needs either a
  predictor per family (like `biquadratic_label`) or a **family-agnostic local degree-24 Galois-group
  identifier** (the OSCAR spike, test 0026 — correct but slow; viable for a 6h-throttled producer even
  if too slow for the daemon hot path). That is the next lever for true all-family coverage.
