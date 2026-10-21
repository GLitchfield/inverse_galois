# 0022 — Resolvent identifier (research): the rigorous separator and its hard core

**Family:** infra / verify · **Date:** 2026-06-27 · **Modules:** `igp/gap.py`
(`subset2_orbits`) · **Status:** researched + scoped (not fully built)

## Question

Can we upgrade the (statistical) Chebotarev identifier to a **rigorous, local** one — exact
labels without Magma, separating even Gassmann-equivalent (same cycle-type-distribution)
groups — so the daemon could pre-filter to undiscovered/sole entirely offline?

## Method / findings

The rigorous separator beyond cycle types is the **2-subset orbit structure** (orbit lengths
of `G` on the 276 pairs of the 24 roots).

- **Group side is trivial** (`gap.subset2_orbits`): e.g. `24T203 → [12,12,12,60,60,60,60]`
  (sum 276). Cheap and exact.
- **Poly side is the hard part.** The matching invariant is the factorization of the degree-276
  pair resolvent `∏_{i<j}(x − (rᵢ+rⱼ))`. Empirically:
  - It computes FAST (0.1 s) but **degenerates**: for 24T203 the additive resolvent factored as
    `[6,12,12,30,30,60,60]` (sum **210 ≠ 276**) — the group's structure forces `rᵢ+rⱼ`
    collisions, so the resolvent is non-separable and the factor degrees are wrong.
  - The fix (Tschirnhaus perturbation `sᵢ = rᵢ+rᵢ²`, or multiplicative `rᵢ·rⱼ`) needs
    **precision scaling**: the resolvent coefficients are already ~263 digits for the additive
    case and overflow 300-digit precision under perturbation, collapsing to garbage.

This is exactly the **Fieker–Klüners hard core** (separable resolvents + Tschirnhaus +
precision/`p`-adic lifting) that Magma's `GaloisGroup` implements. A robust poly-side resolvent
is a real sub-project, not a quick add.

## Decision

- **`subset2_orbits` (group side) is committed** — useful now for a metadata index and ready
  for the poly side later.
- **The Chebotarev identifier (`verify.identify`) remains the working local tool** — it has
  separated every *actual* collision we've hit (5/5, test 0012); **no Gassmann case has blocked
  us**, so the rigorous resolvent is scoped for when one does.
- **Local labeling for the daemon:** the exact-labeling (Galois) producers already pre-filter to
  undiscovered via their predictions; the general/non-Galois producers correctly rely on
  Magma + harvest (computing their label locally *is* the Galois-group problem). So "submit only
  sole" is already achieved where it's feasible; the rest is genuinely Magma's job.
