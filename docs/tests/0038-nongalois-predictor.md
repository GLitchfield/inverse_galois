# 0038 — Non-Galois group predictor for gen12: validated, but low value (contested)

**Family:** search / research · **Date:** 2026-06-29 · **Code:** `igp.gap.kernel_label`,
ground truth from `gen12` rows in `realized.csv`

## Question

`gen12` (general_c2 over non-Galois deg-12 bases) produces breadth (groups at shared pairs), not
1.0s, because we can't predict its 24T label to gate it to `teamCount==0`. Can we build that
predictor — turning gen12's broad group reach into targeted 1.0s like `tsig` does for Galois bases?

## Model + validation

K = F(√α) over a deg-12 base F has G = **M ⋊ H**, where **H = 12Tj** is the base's Galois-closure
action on the 12 primes/roots (LMFDB's `galois_label`) and **M** is the F₂[H]-submodule the kernel
pattern `w` generates. `gap.kernel_label(w, top_t=j, top_deg=12)` builds `C₂ ≀ 12Tj` and identifies
the kernel group — so the GAP side needs no new code.

Ground truth: 500 verified gen12 rows. For base **12T139**, Magma gives **all single-prime patterns
→ 24T21859**; pairs split by H-orbit (110→24T20772, 101→24T13933).

- **|S|=1 (single prime): PREDICTABLE, alignment-free.** `kernel_label([1,0,…], 139)` = **24T21859**
  — exact match, for every single-prime pattern. All singletons are H-equivalent (H transitive), so
  the full-kernel group is determined by the top alone, independent of prime/labeling. ✓
- **|S|≥2: needs alignment.** `kernel_label` uses GAP's 12-point labeling; the construction uses
  `idealprimedec` order. They differ: GAP gives 101→24T20772 but Magma (construction order) gives
  24T13933. So a specific multi-prime pattern's label isn't predictable without aligning the two
  labelings — which is essentially computing H's action on the q-adic roots (≈ the hard Galois-group
  computation we're avoiding; the splitting field is infeasible for large/non-solvable H).

## The value finding (decisive)

**gen12's groups are CONTESTED — there are no open 1.0s to gate toward.**
- 24T21859 (full-kernel of 12T139): **teamCount = 18**.
- ALL **64** distinct gen12 `(t,r)` are shared (teamCount ≥ 1); **0 are teamCount==0**.

`general_c2` over LMFDB deg-12 bases is a *standard* construction every serious team runs, so its
groups — full-kernel (|S|=1) and proper-submodule (|S|≥2) alike — are already claimed. Same trap as
M24: the obvious construction is contested. So even a fully-solved predictor (alignment included)
would gate gen12 toward ≈0 open 1.0s.

## Conclusion / recommendation

- **Do NOT build the |S|≥2 alignment solver.** It's hard (≈ Galois-action computation) and the payoff
  is ~0 1.0s (gen12 groups are contested). A validated method pointed at contested groups is the M24
  lesson again.
- The predictor is mathematically real (|S|=1 validated) and is kept as documented capability, but
  gen12 stays a **breadth** producer (groups-realized headline), not a 1.0 source.
- **Where the 1.0s actually are:** `tsig`'s gated enumeration over Galois tops at *specific*
  (submodule, r) — a narrow, hard-won niche (41 held), maximized via the multi-prime sweep. The open
  `teamCount==0` targets are specific gaps, not whole construction families (those get contested).
- **Redirect:** the clearer remaining lever is **disc-min on our low-`teamCount` held shared pairs**
  (k=1,2: score = 2^(1-k)·log(D0)/log(D) → disc improvement approaches the full point), not more
  construction families.
