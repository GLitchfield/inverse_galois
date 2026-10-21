# 0006 — WS4 prescribed kernel: 3 kernels reached, and an identifier false-positive

**Family:** methods / WS4 · **Date:** 2026-06-24 · **Scripts:** `gap.c2_kernel_labels`,
`scripts/q12_ws4_prescribed_kernel.py`

## Question

Can we deliberately realize a *prescribed* `C_2`-kernel (a specific `H`-submodule), e.g. the
augmentation/sum-zero kernel, over top `C_12`?

## What worked (Magma-confirmed)

GAP predicts the canonical-kernel labels over top `C_12`: **diagonal `24T2`, augmentation `24T12727`,
full `24T14744`.** Construction + Magma confirm:
- **diagonal** ← rational `α` → **24T2** ✓ (matches prediction)
- **full** ← generic non-unit `α` → **24T14744** ✓ (matches prediction)
- an **intermediate** ← unit / ramified-prime `α` (`1+ζ`, `(1−ζᵃ)(1−ζᵇ)`) → **24T2456** (a smaller
  intermediate kernel)

So `α`'s square-class structure deliberately selects among (at least) **three distinct kernels**,
Magma-confirmed.

## What failed, and why (the correction)

The **augmentation `24T12727` was NOT reached.** Two things went wrong, both instructive:

1. **The local identifier false-positived.** `verify.confirm_label(construction, 12727)` returned True
   for all attempts — but Magma says **24T2456**. `24T2456` and `24T12727` share parity + subfield set +
   cycle types, so the current invariants cannot separate them. ⇒ **verifying intermediate kernels
   requires the resolvent upgrade to WS-INFRA-A** (it is now load-bearing, not optional). Always
   Magma-check an intermediate-kernel claim until then.
2. **The recipe was degenerate.** In `Q(ζ₁₃)`, 13 is *totally ramified*, so every `(1−ζᵏ)` is an
   **associate** of the one prime `(1−ζ)`; the "norm-square" products were therefore unit-class, giving
   the *same* kernel as the unit `1+ζ` (→ 24T2456), not independent classes.

## Corrected path (next)

- To get **independent** conjugate classes (needed for higher-dim / arbitrary kernels), use a prime
  `q ≡ 1 (mod 13)` (e.g. `q=53`), which **splits completely** into 12 primes in `Q(ζ₁₃)` (class number
  1 ⇒ principal ⇒ generators exist). `α` = a product of split-prime generators with square norm →
  independent classes + the single norm relation → the augmentation. General kernels: `S`-unit square-
  class linear algebra (PARI `bnfsunit`).
- **Upgrade the identifier with resolvents** so we can verify intermediate kernels locally (else every
  intermediate-kernel construction needs a Magma round-trip).

## Learnings

- Deliberate kernel *control* is real (3 Magma-confirmed kernels) — but **arbitrary prescribed kernels
  need split-prime `α` + a resolvent-grade identifier.** The easy extremes (diagonal/full) and the
  ramified-prime intermediate are reachable; the rest is the genuine S-unit/embedding work.
- Self-correction: trust Magma over the local confirmer for same-invariant group pairs.
