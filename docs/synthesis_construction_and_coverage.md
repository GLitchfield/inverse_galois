# Synthesis — construction toolkit + coverage campaign (tests 0010–0020)

Dated 2026-06-27. Consolidates the deliberate-construction program and the leaderboard
campaign. Headline numbers (from `realized.csv` + live `labels_progress`): **200 distinct
groups, 116 scoreable `(t,r)`, 32 non-solvable/primitive groups, 6 verified sole realizers.**

## The toolkit (what we can build)

A single mechanism — **`K = F(√α)` (or `α^{1/k}`), kernel fixed by α's valuation pattern `w`,
signature fixed by α's real signs** — spans the imprimitive landscape:

| axis | reach | exact a-priori label? |
|---|---|---|
| size-2 (12×2) | C_12, C₂×C₆ (cyclotomic); D₆, A₄ (Galois); 12T28 (non-Galois) | yes for Galois; **partial** for non-Galois |
| size-3 (8×3) | C₃ blocks via ζ₃-Kummer (`Q(ζ₁₅)`) | label via Magma (twisted module) |
| size-4 (6×4) | V₄ blocks (biquadratic over deg-6) | abstract group + `identify` |
| big tops | any non-Galois base via `general_c2` (order predicted exactly) | label via `identify`/Magma |
| non-solvable | A₅/S₅ base (resolvent of a quintic) → non-solvable degree-24 | label via Magma |
| primitive | M₂₄ (Müller `Q(t)`-family), S₂₄ (generic) | given by the family |
| signatures | totally-real base ⇒ `r = 2·#{real places, α>0}`, `α→−α` ⇒ `r↔24−r` | — |

Support tools: `kernelsolve` (F₂[H]-module inverse A→w), `verify.identify`
(Chebotarev-distribution identifier — separates same-invariant collisions), the robust
async engine (`db`/`engine`), and the batched GAP labelers.

## What the leaderboard told us

- **0 sole realizers among the popular groups** — everything everyone builds easily (C_12-top
  families at every `r`, the obvious wreaths) is contested. Disc-min/diversification on those
  barely moves the score.
- **10,426 groups completely undiscovered** (median order ≈24,576) + 112k undiscovered
  signatures — the real prize, sole = 1.0 each.
- **The routing campaign** (invert constructors → `{label→recipe}`, intersect undiscovered)
  delivered **6 sole realizers** (24T3039, 24T5503, 24T1627, 24T5504 cyclic; 24T7825, 24T7871
  non-cyclic A₄) — all Magma-verified scoreable. But yield per top is low (~1–4): even the
  "obvious" tops are mostly saturated.

## What works vs what's partial

- **Reliable:** Galois-base exact targeting (construction action = `nfgaloisconj` order =
  predicted) — the 6 sole realizers are all from this. Order prediction for any base
  (labeling-independent). Signature control over real bases. Disc-min via α=−1 for diagonals.
- **Partial / open:** **non-Galois a-priori labeling.** The 12T28 affine action matched Magma
  for the 3 kernels of test 0015 but mis-predicted another (24T10361 → realized 24T18449), so
  non-Galois targeting is not yet trustworthy — it needs the true prime↔block alignment (the
  Galois closure, or `identify` post-construction).
