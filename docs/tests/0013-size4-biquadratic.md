# 0013 — Size-4 (V_4-block) biquadratic construction (item C, size-k axis)

**Family:** construction / WS4 · **Date:** 2026-06-26 · **Modules:** `igp/gp.py`
(`biquadratic_c2`), `igp/gap.py` (`biquadratic_label`), `igp/verify.py` (`identify`),
`scripts/q18_size4_biquadratic.py`

## Question

All prior construction was **size-2 blocks** (`12×2`). Can we build off that axis to
**size-4 blocks** — the dominant frontier shape (`6×4`, test 0004) — and label the result?

## Method

Klein-four (V_4) block over a Galois degree-6 base — no `ζ_k` needed, reuses the autos:
- `gp.biquadratic_c2(f, w1, w2, q)`: two independent square-classes `β_i = ∏_{w_i[a]=1}
  σ_a(π)` from a completely-split `q`; `K = F(√β₁, √β₂)` (the degree-24 compositum of
  `F(√β₁)`, `F(√β₂)`). `m=6` blocks of size 4, block group `C₂×C₂`.
- **Labeling — two stages.** `gap.biquadratic_label` builds the explicit degree-24 action of
  `M ⋊ H` on `(block, sign₁, sign₂)` and identifies it; but the hand-built action lands on a
  *sibling* 24Tt (same abstract group, different permutation rep — a branch/cocycle subtlety:
  24T1156 and 24T1157 are isomorphic groups, distinct `S₂₄` reps). The exact rep is then
  resolved by **`verify.identify`** (item B) from the field's own cycle-type distribution.

Base: `F = Q(ζ₇)` (`C₆ = 6T1`, `h=1`), split prime `q=29`.

## Result

3 constructions, all degree-24 with `6×4` block structure (subfield degrees `[2,3,6,…]`),
Magma-verified:

| (w₁ / w₂) | biquad_label (abstract grp) | identify (exact) | Magma |
|---|---|---|---|
| 100000 / 010000 | 24T1157 | **24T1156** | 24T1156 |
| 110000 / 001000 | 24T1168 | **24T1168** | 24T1168 |
| 101000 / 010100 | 24T443 | **24T448** | 24T448 |

**identify resolves the exact rep 3/3** (Magma-confirmed). The construction reaches the
dominant `6×4` shape; the deliberate pipeline is **construct → biquad_label (abstract group)
→ identify (exact 24Tt) → Magma**.

## Learnings

- **Size-4 construction works** — first build off the size-2 axis, reaching the dominant
  frontier block shape. The V_4-block / two-square-roots trick reuses all the autos machinery.
- **Item B closes item C here.** The a-priori action model is exact *up to the abstract
  group*; the cycle-type identifier (test 0012) then pins the exact permutation rep from the
  field — the two tools compose into a deliberate labeler. (A fully a-priori exact predictor
  would need the precise sign cocycle / point stabilizer; deferred — `identify` covers it.)
- **Scope:** an order-6 *Galois* base gives smallish groups (≤384). Bigger `6×4` groups need
  bigger tops on 6 points (`6Tj`, `|H|>6`) — i.e. **non-Galois** degree-6 bases (no autos →
  the general-base construction). Other block sizes (`k=3,6,8`) remain; `k=3,6` need `ζ_k`
  (cyclic-Kummer), `k=8` iterates this V_4 trick once more.
