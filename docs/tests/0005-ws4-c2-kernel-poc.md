# 0005 — WS4 C_2-kernel construction (proof of concept): kernel control via α

**Family:** methods / WS4 · **Date:** 2026-06-24 · **Scripts:** `gp.quadratic_ext`,
`scripts/q11_ws4_c2_kernel.py` · Plan: `docs/design/ws4_kernel_construction.md`

## Question

Does `K = F(√α)` with `F` a degree-12 field realize degree-24 imprimitive groups whose **kernel**
`A ⊆ C_2^12` is controlled by `α` (as the F_2-span of the conjugate square-classes)?

## Method

`F = Q(ζ_13)` (degree 12, top group `C_12`). Build `K = F(√α)` via PARI `rnfequation`
(`gp.quadratic_ext`) for varied `α`; read the local fingerprint (parity, subfield degrees, #cycle
types) and submit for Magma's authoritative `24Tt`.

## Result

| `α` | `24Tt` (Magma) | parity (in A_24) | #cycle types | subfield degrees |
|---|---|---|---|---|
| 2, 3, 6 (rational) | **24T2** (baseline) | True | 5–6 | `[2,2,2,3,4,4,4,6,6,6,8,12,12,12]` |
| y+1 | **24T2456** | True | 9 | `[2,3,4,6,12,12,12]` |
| y−2, y²−2, 2y+3 (generic) | **24T14744** | False | 15 | `[2,3,4,6,12]` |

Distinct `α` → distinct group, in three kernel regimes:
- **rational `α`** ⇒ all conjugate classes equal ⇒ **diagonal (minimal) kernel** ⇒ `C_12×C_2` = 24T2.
- **special `α` (y+1)** ⇒ partial relations ⇒ **intermediate** kernel ⇒ 24T2456.
- **generic non-rational `α`** ⇒ near-independent classes ⇒ **large** kernel ⇒ 24T14744 (leaves A_24).

## Learnings

- **The construction + kernel control are validated end-to-end** (Magma ground truth): with the top
  fixed, `α` deliberately selects the kernel, producing different imprimitive `24Tt`.
- **The local identifier tracks the kernel** — parity, subfield set, and cycle-type count all move
  monotonically with kernel size — so we can read off the kernel regime locally before submitting.
- This is the WS4 mechanism working for abelian top `C_12`. **Next (gradient step 2):** non-abelian top
  groups (build `F` with a target's top group, recursively) and **solving for `α` that realizes a
  *prescribed* `H`-submodule `A`** (PARI `bnf*` S-units) to hit specific frontier `24Tt`.
- (Bonus: 24T2456, 24T14744 are non-baseline — but the deliverable here is the *method*, not points.)
