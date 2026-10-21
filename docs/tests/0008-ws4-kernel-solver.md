# 0008 — WS4 exact A→w→α kernel solver (top C_12)

**Family:** methods / WS4 · **Date:** 2026-06-24 · **Scripts:** `gp.c2_split_construct`,
`gap.kernel_label`, `scripts/q14_ws4_kernel_solver.py`

## Question

An *exact* solver: given a target `C_2`-kernel `A` (a "12 blocks of size 2" group with top `C_12`),
produce a realizing polynomial — no search.

## The solver (exact, no NN/GA)

In the regular case the realized kernel is `A = ⟨H-shifts of w⟩` = the ideal `(w(x))` in
`F₂[C_12] = F₂[x]/(x¹²−1)`. So **given target `A`, `w` is simply a generator of `A`** — a closed-form
choice, confirming the earlier analysis that structure is exact (search tools belong on the *quality*
axis, not here). One knob `w` drives both sides:
- **predict** (group side): `gap.kernel_label(w)` builds `⟨H-shifts of w⟩ ⋊ C_12 ≤ C_2≀C_12` and returns
  its `24Tt`.
- **construct** (field side): `gp.c2_split_construct(w)` builds `K = Q(ζ₁₃)(√α)`,
  `α = ∏ⱼ σʲ(π)^{wⱼ}` over the split prime `q=53` (`σ: ζ→ζ²`); the valuation pattern of `α` is `w`,
  so the realized kernel is exactly `(w(x))`. (`polredbest`-reduced.)

## Result

`gap.kernel_label` returns **distinct, sensible labels** for distinct `w`:

| `w` | kernel | predicted `24Tt` |
|---|---|---|
| single `[1,0,…]` | full `C₂¹²` | 24T14744 |
| pair `[1,1,0,…]` | augmentation | 24T12727 |
| triple `[1,1,1,0,…]` | — | 24T10266 |
| all-ones | diagonal | 24T2 |

- **Augmentation is Magma-confirmed end-to-end** (test 0007: `pair → 24T12727`).
- The full multi-kernel `predict == Magma` check (q14 batches) was **queued** at run time — the SAIR
  verifier was backed up (the *same* augmentation construction verified in seconds during 0007), so this
  is server latency, not the construction. To re-check the queued labels next session.

## Learnings

- **The solver is exact** — `w` = a generator of the target ideal `A`; "construct a group with kernel
  `A`" reduces to ideal-generator selection. No optimization needed for *structure*.
- The **discriminant** of multi-prime `α` is large (slow to verify); `polredbest` shrinks it, and
  *choosing the smallest-disc `α` realizing `A`* is precisely the GA/optimization problem (WS2 hook).
- Next: re-confirm the queued labels; extend to **non-abelian tops** (work in `F^c`) and **size-`k`
  blocks** (`ζ_k`-Kummer); add the **resolvent identifier** so the predict↔construct match verifies
  locally without a Magma round-trip.
