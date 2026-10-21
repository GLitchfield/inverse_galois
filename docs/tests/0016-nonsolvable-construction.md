# 0016 — First non-solvable degree-24 groups: C_2-kernel over an A_5 base (item C)

**Family:** construction / non-solvable · **Date:** 2026-06-26 · **Modules:** `igp/gp.py`
(`general_c2`), `scripts/q21_nonsolvable.py`

## Question

All construction so far hit *solvable* imprimitive groups. Can the same machinery reach the
**807 non-solvable** residual?

## Method

`general_c2` (test 0015) works over *any* degree-12 base — including one with a **non-solvable
top**, which forces the degree-24 group to be non-solvable. So the problem reduces to *building
a degree-12 base field with a non-solvable top*.

- **Base = degree-12 A_5 field** (top = A_5 on 12 points = cosets of a C_5, the icosahedral
  12-vertex action). Built cheaply as a **resolvent** of the A_5 quintic `x⁵+x⁴−4x+4`: take a
  C_5-invariant of the 5 roots that is *not* reflection-invariant
  (`θ = Σ_i r_{σ(i)}·r_{σ(i+1)}²`, stabilizer exactly C_5), evaluate over the 12 cosets →
  degree-12 irreducible. (The degree-60 splitting-field route OOM'd / was too heavy; the
  resolvent avoids it entirely — rounding error ~1e-240, exact integers.)
- `h(F)=5`, so `general_c2`'s **product-ideal** path is required (a pattern is realizable iff
  `∏ p_j` is principal). [Bug fixed en route: `I` is reserved in gp (the imaginary unit).]

## Result

5 patterns over the A_5 base (`q=691`), Magma-verified — **3 distinct, all NON-SOLVABLE**:

| pattern | Magma | order | solvable? |
|---|---|---|---|
| 111111111111 (diagonal) | **24T203** | 120 = C₂×A₅ | **False** |
| 110000000000, 110011000000 | **24T17923** | 122880 = 2¹¹·60 | **False** |
| 111000000000, 111110000000 | **24T19236** | 245760 = 2¹²·60 = C₂≀A₅ | **False** |

**First non-solvable degree-24 constructions.** `24T19236` is the full wreath `C₂ ≀ (A_5 on
12)`; `24T203` is the diagonal `C₂ × A_5`.

## Learnings

- **The 807 non-solvable residual is reachable** by the C_2-kernel machinery — just feed it a
  non-solvable-top base. No new construction engine needed; the lever is the *base field*.
- **The base field is built by a resolvent**, not a splitting field: from a low-degree
  polynomial with the target group (here an A_5 quintic), a subgroup-invariant of the roots
  gives the degree-12 field directly — cheap and OOM-free. This generalizes: any non-solvable
  group with a faithful action on ≤12 points whose "parent" polynomial we can write down
  (A_5 other actions, S_5, PSL(2,11) on 12, ...) yields a base → a non-solvable 24Tt family.
- **Scope:** these are *imprimitive* non-solvable groups (block system 12×2, non-solvable
  top). The genuinely hard **primitive** degree-24 groups (M_24, PSL(2,23) on 24 points — no
  block system) are still separate and need different methods (rigidity / explicit families).
