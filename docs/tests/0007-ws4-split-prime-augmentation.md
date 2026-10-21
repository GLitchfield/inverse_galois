# 0007 — WS4 (a): split-prime construction reaches the augmentation kernel

**Family:** methods / WS4 · **Date:** 2026-06-24 · **Script:** `scripts/q13_ws4_split_prime_augmentation.py`
· Result: **Magma-confirmed 24T12727** (the prescribed augmentation kernel).

## Question

Can we deliberately reach a *prescribed* intermediate kernel — the augmentation (sum-zero, dim 11),
predicted `24T12727` — which the unit / ramified-prime recipes missed (test 0006)?

## Construction

`F = Q(ζ_13)` (top `C_12`). The prime `q = 53 ≡ 1 (mod 13)` **splits completely** into 12 primes,
permuted as a **12-cycle** by `σ: ζ → ζ²` (2 is a primitive root mod 13). `h(F)=1`, so each prime
above 53 is principal; let `π` generate one. Set

> **`α = π · σ(π)`**, and `K = F(√α)`.

Each conjugate `σⁱ(α)` has 53-valuation pattern `eᵢ + eᵢ₊₁` (a consecutive pair). The relation space
`Rel = {c ∈ F₂¹² : Σ cᵢ(eᵢ+eᵢ₊₁) = 0} = {c constant} = ⟨(1,…,1)⟩` (dim 1) — and the all-ones relation
holds because `N(α) = 53²` is a square. So the kernel `A = Rel^⊥ =` sum-zero (dim 11) = **augmentation**.

## Result

Magma: **`24T12727`** — exact match to the GAP-predicted augmentation label. The split-prime recipe
reaches the prescribed kernel the earlier (degenerate, ramified-prime) recipes could not.

## The general mechanism (the methods advance)

The **valuation pattern of `α` at a fully-split prime's `m` primes is the `H`-module knob for the
kernel.** Writing `α = ∏ⱼ πⱼ^{wⱼ}` over the split-prime `H`-orbit (`w ∈ Z^m`, `πⱼ` principal), the
conjugate square-classes have valuation vectors = the `H`-translates of `w mod 2`, so

> `Rel = { c : Σ cᵢ · (H-translate pattern of w) ≡ 0 (mod 2) }`,  kernel `A = Rel^⊥`.

Thus **realizing a prescribed `H`-submodule kernel `A` reduces to choosing `w` (an `F₂` `H`-module
element) so that `Rel = A^⊥`**, then building `α` from the split primes (PARI) with a square-norm
adjustment. Augmentation = consecutive-pair `w`. Diagonal/full are the `w=0`-norm / generic extremes.

## Caveats / next

- Unit square-classes can add relations, so still **Magma-verify** until WS-INFRA-A gets the resolvent
  upgrade (the local identifier cannot separate `24T2456`/`24T12727`).
- Next: implement the **general `A → w → α` solver** (`F₂` `H`-module linear algebra over the split
  primes) so any prescribed `C_2`-kernel is constructible; then the resolvent identifier (b) to verify
  locally. Generalizes to size-`k` blocks via `ζ_k`-Kummer extensions.
