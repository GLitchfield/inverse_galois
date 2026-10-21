# 0015 — C_2-kernel over a general (non-Galois) base: the big-top unlock (item C)

**Family:** construction / WS4 · **Date:** 2026-06-26 · **Modules:** `igp/gp.py`
(`general_c2`), `igp/kernelsolve.py`, `scripts/q20_general_base.py`

## Question

Every prior C_2 construction used a **Galois** base (autos via `nfgaloisconj`), so the top was
**regular**: `|H| = deg F ≤ 12`. The frontier's bigger groups need bigger tops (`|H| > 12`).
Can we reach them — and predict anything before Magma?

## Method

A non-Galois base needs no autos: `gp.general_c2(f, w, q)` sets `α = ∏_{w_j=1} π_j` where
`π_j` generates the j-th prime above a completely-split `q` (in `idealprimedec` order), then
`K = F(√α)`. Requires `h(F)=1` and `q` split completely (12 deg-1 primes).

- **Base:** `F = Q[x]/(x¹²−2)` — non-Galois (2 autos), Galois closure order 48, `h=1`. Its
  top on the 12 roots is the affine group `k ↦ bk+a` on `Z/12` (`b ∈ (Z/12)*`) = **12T28**,
  order 48. Completely-split prime `q = 601`.
- **Order prediction (labeling-independent):** `|G| = 2^{dim⟨H·w⟩} · |H|` via
  `kernelsolve.module_basis` — no prime↔block alignment needed (dimension is basis-invariant).
  The *exact* 24Tt would need H's action aligned to `gp`'s prime order (the Galois closure) —
  deferred; `identify`/Magma pin it.

## Result

3 constructions over `x¹²−2`, all top **12T28**, **order predicted exactly**, Magma-confirmed:

| w | predicted order | Magma | order | top |
|---|---|---|---|---|
| 100000000000 | 196608 | **24T18449** | 196608 | 12T28 |
| 110000000000 | 98304 | **24T16724** | 98304 | 12T28 |
| 101000000000 | 49152 | **24T14789** | 49152 | 12T28 |

`24T18449` (order **196608** = full `C₂ ≀ 12T28`) is **4× larger** than the Galois-base
maximum (49152 = `C₂≀A₄`). The big top `12T28` (order 48) is unreachable from any Galois
degree-12 base. Order matched 3/3.

## Learnings

- **The big-top wall is down.** A non-Galois base reaches tops with `|H| > deg F`; with `h=1`
  + a completely-split prime, `general_c2` builds the C_2-kernel with no autos at all — it's
  *simpler* than `galois_c2`, just sparser split primes (density `1/|H|`).
- **Semi-deliberate:** the *order/structure* is predicted exactly and cheaply (kernelsolve
  dim, no alignment); the exact 24Tt comes from `identify` (item B) + Magma. Full a-priori
  exactness needs the Galois closure for the prime↔block alignment — the one remaining gap.
- **The matrix is now reachable.** Across the session: tops (regular order-12 *and* big
  non-Galois like 12T28) × block sizes (`k=2,3,4,6`) × kernels (any module via `kernelsolve`).
  Next levers: non-Galois bases at *other* block sizes (big-top `6×4`/`8×3`), more base fields
  to sweep specific frontier `12Tj`, and S-units to drop the `h(F)=1` restriction.
