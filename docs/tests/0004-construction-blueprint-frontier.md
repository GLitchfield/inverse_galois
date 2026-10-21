# 0004 — Construction blueprints for the frontier (WS1) + a framing correction

**Family:** methods / WS1 · **Date:** 2026-06-24 · **Scripts:** `gap.wreath_decompose_batch`,
`scripts/q10_wreath_reachability.py`

## Question

For the untouched-solvable frontier, can we extract a construction blueprint (block structure + induced
groups) per target, and how much is reachable by the *easy* full-wreath recipe (G2) vs needs deliberate
kernel construction (WS4)?

## Method

`gap.wreath_decompose_batch`: per group, for each block system give (block size `k`, #blocks `m`,
block-action group `kTi`, top-action group `mTj`, and `full_wreath = |G| == |K|^m·|H|`). full_wreath ⇒
the full wreath `K≀H` ⇒ reachable by composition with constituents realizing `K`, `H`.

## Correction (verified)

The detector was sanity-checked against a *built* group, and it overturned a wrong assumption:
- Full `S_3 ≀ S_8` = **`24T24932`**, order **67,722,117,120** (`= 6⁸·8!`).
- Our `24T19234` has order **241,920 = |S_3|·|S_8|** — it is the **product action `S_3 × S_8`**, NOT a
  wreath.

So **our compositions/composita produce product-action / proper subgroups, not *full* wreaths** (full
wreaths are rare and huge). The detector is correct; my earlier "G2 = wreath" label was loose.

## Result (`q10`, 200 untouched-solvable, sampled across the order range)

- **Full-wreath (easy recipe): 0/200.** ⇒ **100% need deliberate kernel construction (WS4).** The full
  wreaths are a handful of huge groups, essentially never on the frontier.
- **Frontier block-structure profile** (each group has several block systems): most common shapes are
  **6 blocks of size 4** (270), **12 blocks of size 2** (179), **3 blocks of size 8** (172), **2 blocks
  of size 12** (122), then 4×6, 8×3. Top-action groups are **small and realizable**: `2T1 (C_2)`,
  `3T2 (S_3)`, `3T1 (C_3)`, several `6Tx`.

## Learnings

- `wreath_decompose` is the **WS1 blueprint extractor**: for a target it gives the tower skeleton
  (build the degree-`m` top field with group `mTj` — small/realizable — then a degree-`k` extension
  realizing the **specific kernel**).
- The frontier's hardness is entirely in the **kernel** (the easy full-wreath case never applies). So
  the leverage method is **WS4: deliberate kernel construction.**
- Most tractable + common entry point: **`C_2` kernels** (size-2 blocks; "12 blocks of size 2", 179/200
  have such a system). Recipe to develop: build a degree-12 field `F` with the top group, then a
  quadratic `K = F(√α)` whose conjugate signs realize the target kernel `⊆ C_2¹²`. → next test.
