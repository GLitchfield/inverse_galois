# 0010 — General-conductor C_2 constructor + aligned prediction (item C, step 1)

**Family:** construction / WS4 · **Date:** 2026-06-26 · **Modules:** `igp/gp.py`
(`cyclotomic_c2`, `cyclotomic_top_perms`), `igp/gap.py` (`kernel_label_perms`),
`igp/kernelsolve.py`, `scripts/q15_general_conductor.py`

## Question

The deliberate C_2-kernel constructor was special-cased to the cyclic `C_12` top
(`Q(ζ₁₃)`, primitive-root power ordering). Can it be generalized to an **arbitrary
cyclotomic top** — and can we still **predict** the `24Tt` label so the construction is
deliberate (not a guess)? Concretely, does it reach a *new* top, `12T2 = C₂×C₆`
(`Q(ζ₂₁)`), with predictions Magma confirms?

## Method

- **Construct** (`gp.cyclotomic_c2(w, n, q)`): enumerate the Galois action as `ζ → ζ^a`
  over the **units of `n`** (sorted) — works for any conductor, not just cyclic `(Z/n)*`.
  `α = ∏_{w_a=1} σ_a(π)`, `π` a generator of a prime above the split prime `q ≡ 1 (mod n)`.
- **Predict** (`gap.kernel_label_perms(w, top_perms)`): build `A ⋊ H` with `H` given as
  **explicit permutations** and `A = <H-shifts of w>`. Fed the *same* `(Z/n)*` action
  (`gp.cyclotomic_top_perms(n)`) the construction uses → predict and construct share one
  block action, so **intermediate** kernels align (not just the action-invariant extremes).
- **Solver** (`igp/kernelsolve.py`): the inverse map `A → w` as pure GF(2) linear algebra
  (forward `module_basis`, inverse `generators`/`cyclic_generator`) for an arbitrary top —
  the reusable core, no longer tied to the `C_12` ideal lattice.
- **Cases:** `Q(ζ₁₃)` (top `12T1`, cross-check the generalized path reproduces the known
  family under the sorted-units action) and `Q(ζ₂₁)` (top `12T2`, NEW): full + 2 intermediate.

## Result

**Local validation (final):**
- `cyclotomic_top_perms(13)` generates `12T1` (C_12), `cyclotomic_top_perms(21)` generates
  `12T2` (C₂×C₆) — both transitive, order 12. ✓
- `kernel_label_perms` fed the cyclic shift **reproduces** the known-good `kernel_label(·,1,12)`
  on every tested pattern (`24T12727`, `24T10257`, `24T10266`). ✓ (explicit-perms machinery sound)
- `module_basis(x+1, C_12)` → dim 11 (the augmentation ideal). ✓

**Magma ground truth (predict vs label): 5/5 match.**

| top (conductor) | w | predicted | Magma | match |
|---|---|---|---|---|
| 12T1 (ζ₁₃) | 110000000000 | 24T12727 | 24T12727 | ✓ |
| 12T1 (ζ₁₃) | 100100000000 | 24T10257 | 24T10257 | ✓ |
| 12T2 (ζ₂₁) | 100000000000 (full) | 24T14745 | 24T14745 | ✓ |
| 12T2 (ζ₂₁) | 110000000000 | 24T10258 | 24T10258 | ✓ |
| 12T2 (ζ₂₁) | 101000000000 | 24T5339 | 24T5339 | ✓ |

## Learnings

- **The aligned prediction holds — including for intermediate kernels.** The two `Q(ζ₂₁)`
  intermediates (`24T10258`, `24T5339`) are not action-invariant, so their agreement proves
  the shared `(Z/n)*` action makes predict and construct consistent — the constructor is
  deliberate over any cyclotomic top, not just the wreath/diagonal extremes.
- The sorted-units path reproduces the known `C_12` family (`ζ₁₃` rows), so the
  generalization didn't break the prior slice.
- **Scope of step 1:** this reaches *all abelian degree-12 cyclotomic tops*. The abelian
  groups of order 12 are exactly `C_12` and `C₂×C₆`, arising as `(Z/n)*` for `φ(n)=12`
  (`n ∈ {13,26}` → C_12; `{21,28,36}` → C₂×C₆). So step 1 adds the **`12T2` top family** to
  the previously-reachable `C_12` family — but only 2 distinct abelian tops exist this way.
- **What remains in item C** (the frontier-reaching steps): (2) **non-abelian / general tops**
  — build the degree-12 base field `F` for an arbitrary `12Tj` (recursively, via our own
  generators or a known poly), then run the C_2-kernel over general `F` (autos via
  `nfgaloisconj`, split prime + S-unit generators); (3) **size-`k` blocks** (`k=3,4,6`) via
  `ζ_k`-Kummer for the dominant `6×4`/`8×3` frontier shapes.
