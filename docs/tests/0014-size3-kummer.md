# 0014 — Size-3 (C_3-block) cyclotomic Kummer construction (item C, size-k axis)

**Family:** construction / WS4 · **Date:** 2026-06-26 · **Modules:** `igp/gp.py`
(`cyclotomic_kummer`), `scripts/q19_size3_kummer.py`

## Question

Size-4 (test 0013) covered the `6×4` frontier shape. Can we reach the *other* dominant
shape, **`8×3`** (test 0004), with cyclic **C_3** blocks?

## Method

Cyclic-C_k Kummer needs `ζ_k` in the base. `Q(ζ₁₅)` (degree 8 = the 8 blocks, top
`(Z/15)* = C₂×C₄ = 8T2`, `h=1`) contains `ζ₃` (since `3 | 15`), so a radical cube root is a
clean cyclic C_3:
- `gp.cyclotomic_kummer(w, n, q, k)`: `K = Q(ζ_n)(α^{1/k})`, `α = ∏_a σ_a(π)^{w_a}` with
  exponents `w_a ∈ 0..k-1`, `π` over a completely-split `q ≡ 1 (mod n)`. For `k=3, n=15,
  q=31`: degree `3·8 = 24`, `8×3` blocks.

The C_3 block carries a **cyclotomic twist** (complex conjugation in `Q(ζ₃)` inverts `ζ₃`),
so the kernel is a *twisted* `F₃[H]`-module — the exact a-priori predictor is **deferred**;
Magma assigns the label and GAP confirms the block structure.

## Result

5 constructions, every one a degree-24 field with an `8×3` block system (degree-8
subfield), Magma-verified — **4 distinct** `24Tt`:

| w (exponents mod 3) | Magma | order | block / top |
|---|---|---|---|
| 10000000 | **24T15983** | 52488 | 3T1 (C₃) / 8T2 |
| 11000000 | 24T7794 | 5832 | 3T1 / 8T2 |
| 10100000 | 24T1511 | 648 | 3T1 / 8T2 |
| 11100000 | 24T7795 | 5832 | 3T1 / 8T2 |
| 21000000 | 24T7795 | 5832 | 3T1 / 8T2 |

All `r=0` (`Q(ζ₁₅)` is totally complex). Every group has block group **3T1 = cyclic C_3**
over top **8T2 = (Z/15)\*** — exactly the designed Kummer C_3 blocks.

## Learnings

- **Size-3 works** — the second dominant frontier shape reached, with genuine cyclic-C_3
  blocks. `24T15983` is order 52488, larger than the size-4 groups (the C_3 wreath base is
  bigger than V_4).
- **`cyclotomic_kummer` is general in `k`:** any `k | n` works. With the size-2
  (`cyclotomic_c2`) and size-4 (`biquadratic_c2`) constructors, the block sizes now reachable
  over cyclotomic bases are **k = 2, 3, 4** (and **k = 6** via `n=12`, `4×6`, C₆ blocks).
- **Deferred:** the exact deliberate predictor for twisted (`ζ_k`-character) blocks — the
  `F_k[H]`-module with the cyclotomic twist. Labeling currently leans on Magma; an `identify`
  shortlist would need that predictor (or block-structure + order narrowing). As with every
  block size, *bigger* tops need **non-Galois bases** (no autos) — the general-base build.
