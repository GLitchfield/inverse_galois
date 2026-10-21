# 0020 — Routing campaign: targeting fully-undiscovered groups (sole realizers)

**Family:** infra / coverage · **Date:** 2026-06-26 · **Modules:** `scripts/campaign.py`,
`igp/gap.py` (`kernel_labels_for_top`)

## Question

10,426 groups are completely undiscovered (test 0018) — each a sole realizer worth 1.0. Can we
*target* them: invert our constructors into a `{label → recipe}` map, intersect with the
undiscovered set, and build only the matches?

## Method

- **Batched forward map** (`gap.kernel_labels_for_top`): build the wreath product once, identify
  many kernel groups in one GAP process — the enumeration was infeasible per-`w`.
- **Exact-labeling families only** (construction↔label validated, tests 0010–0011): C_12
  (`Q(ζ₁₃)`), C₂×C₆ (`Q(ζ₂₁)`), D₆ (12T3), A₄ (12T4) — size-2 C_2-kernels.
- Per top: enumerate **cyclic** kernels (one generator `w` each, popcount 1..4, deduped by
  `kernelsolve.module_basis`), batch-label, build `{label → (top, w)}`. Intersect with
  undiscovered `(t,0)` from the fresh leaderboard; construct matches; submit (engine dedups).

## Result

| top | cyclic kernels | distinct labels |
|---|---|---|
| C_12 | 16 | 16 |
| C₂×C₆ | 28 | 12 |
| D₆ | 49 | 17 |
| A₄ | 33 | 10 |

**55 reachable labels; 4 UNDISCOVERED** (teamCount 0, confirmed in fresh data): **24T3039**
(C_12), **24T5503**, **24T1627** (C₂×C₆), **24T5504** (A₄) — all constructed, **Magma-verified
scoreable, sole realizers** (we built them while teamCount was 0).

**Multi-generator extension (`campaign2.py`):** non-cyclic kernels via multi-prime α
(`gp.cyclotomic_c2_multi` / `galois_c2_multi`, `gap.kernel_labels_multigen`). Enumerating the
2-generated submodule lattice found **2 MORE undiscovered** via non-cyclic A₄ kernels —
**24T7825, 24T7871**, also Magma-verified scoreable sole realizers. **Total: 6 sole
realizers** from the campaign.

## Learnings

- **The campaign works** — route → construct → sole target, end to end, **6 sole realizers
  verified** (4 cyclic + 2 non-cyclic). But the size-2 Galois families are **mostly saturated**
  (most labels already taken): the exactly-labelable inventory is just the 4–5 order-12
  *regular* (Galois) tops. **Multi-generator kernels** (`campaign2`) squeezed out 2 more via
  the non-cyclic A₄ lattice — lever #2 delivered, modestly.
- **Scaling levers, in yield order:** (1) **big-top alignment** — solving the prime↔block
  alignment for non-Galois bases unlocks hundreds of `12Tj` with `|H|>12` (the bulk of reachable
  labels); (2) **multi-generator kernels** (multi-prime α) → the full submodule lattice per top
  (~+50%); (3) **harder families** (size-3/4, non-solvable) via *construct-then-identify* — they
  hit less-popular groups, so a higher undiscovered fraction, at the cost of a-priori targeting.
- Reusable + resumable: re-run `campaign.py` with more families/`MAXPC` as bases are added.
