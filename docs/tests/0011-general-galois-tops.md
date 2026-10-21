# 0011 — C_2-kernel over general Galois tops (item C, step 2): non-abelian A_4, D_6

**Family:** construction / WS4 · **Date:** 2026-06-26 · **Modules:** `igp/gp.py`
(`galois_c2`, `galois_action_perms`), `igp/gap.py` (`kernel_label_perms`),
`scripts/q16_galois_tops.py`

## Question

Step 1 (test 0010) reached only the two *abelian* order-12 tops (the cyclotomic `(Z/n)*`).
Can the deliberate C_2-kernel constructor reach **non-abelian** tops — and still predict the
`24Tt` label exactly? Target the order-12 non-abelian groups `A_4 (12T4)` and `D_6 (12T3)`.

## Method

Take the degree-12 base field `F` to be any **Galois** field with the desired group and use
its automorphisms directly (no cyclotomic special-casing):

- `gp.galois_c2(f, w, q)`: `α = ∏_{w_a=1} σ_a(π)`, `σ_a = nfgaloisconj(f)`, `π` a generator
  of one prime above a completely-split `q`; `K = F(√α)`. Requires `h(F)=1` (clean principal
  generators). **Variable-priority fix:** `F` must live in a *lower*-priority PARI variable
  (`y`) than the relative `x`, or `rnfequation` collapses to degree 1.
- `gp.galois_action_perms(f)`: the regular action of `Gal(F/Q)` on its autos (`σ_a·p_b = p_c`,
  `σ_c = σ_a∘σ_b`), so `gap.kernel_label_perms` predicts under the *same* action the field uses.

**Fields** (both Galois, degree 12, `h=1`):
- `A_4 = 12T4`: splitting field of the A_4 quartic `x⁴+8x+12` (`nfsplitting`); split prime `q=71`.
- `D_6 = C₂×S₃ = 12T3`: compositum of `Q(splitting of x³−2)` and `Q(√5)`; split prime `q=31`.

## Result

**Magma 6/6 match** (predict == label), three kernels (`w`) per top:

| top | w | predicted = Magma | scoreable / baseline |
|---|---|---|---|
| A_4 (12T4) | full `100…` | 24T14747 = C₂≀A₄ (ord 49152) | scoreable, non-baseline |
| A_4 (12T4) | `110…` | 24T5341 (ord 3072) | scoreable, non-baseline |
| A_4 (12T4) | `101…` | 24T2568 (ord 768) | scoreable, non-baseline |
| D_6 (12T3) | full `100…` | 24T14746 = C₂≀D₆ (ord 49152) | scoreable, non-baseline |
| D_6 (12T3) | `110…` | 24T10262 (ord 12288) | scoreable, non-baseline |
| D_6 (12T3) | `101…` | 24T2595 (ord 768) | scoreable, non-baseline |

`galois_action_perms` recovers the right top: A_4 field → 12T4, D_6 field → 12T3 (both
order 12, non-abelian, verified in GAP).

## Learnings

- **The constructor is now top-agnostic.** Any Galois degree-12 `F` with `h(F)=1` + aligned
  regular-action prediction reaches that top's whole kernel family, exactly predicted before
  Magma. Step 1 + step 2 together cover **4 of the 5 order-12 tops** (`C_12`, `C₂×C₆`, `D_6`,
  `A_4`); only `Dic_3 = 12T5` is left (a degree-12 dicyclic field).
- The live verifier marked these **scoreable / non-baseline** even though the local frontier
  snapshot calls them "discovered" — confirming (test 0009) that `signatures_deg24.csv` is
  **stale**. Trust the submission response, not the snapshot; refresh (`q02`) before routing.
- **Remaining in item C:** `Dic_3` top (completes order-12); **non-regular tops** (`|H|>12`,
  i.e. *non-Galois* degree-12 `F` — the autos trick fails, need the 12 primes' Frobenius
  action + S-units); and **size-`k` blocks** (`k=3,4,6` via `ζ_k`-Kummer) for the dominant
  `6×4`/`8×3` frontier shapes.
