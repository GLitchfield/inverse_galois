# 0018 — Leaderboard position + disc-min lever + coverage push (parallel threads)

**Family:** strategy / scoring · **Date:** 2026-06-26 · **Modules:** `scripts/q23_position.py`,
`igp/gp.py` (`quadratic_ext`), fresh `sair.labels_progress`

## Question

Where do we actually stand on the live leaderboard, and can we raise score by (a)
discriminant minimization on what we hold and (b) more coverage — run concurrently?

## Method

Fetched the full live per-signature state (`sair.labels_progress`: 165,836 signatures, each
with `teamCount`, `minimumDiscAbs`, `discovered`). `q23_position.py` classifies our realized
`(t,r)` vs the global minimum; `quadratic_ext` swaps the diagonal-kernel generator (α = split
prime `q`) for **α = −1** (ramifies only at 2) to shrink disc. Coverage thread (background)
built S₅-top non-solvable groups + S₂₄.

## Result

**Position (our realized signatures vs leaderboard):**
- **sole realizer: 0** — every group we hold is also held by ≥2 other teams.
- we hold the min disc: 5; **beatable by disc-min: 27** (our disc > global min).
- **undiscovered signatures: 112,279** (teamCount 0) — each a potential sole-realizer (1.0).
- Worst disc gaps are our big-prime non-solvable builds, e.g. 24T577 r=8 ours 87 / min 33
  digits; 24T203 r=0 ours 67 / min 31.

**Disc-min (α = −1 for diagonal C₂×top groups):**

| group | before | after (√−1) | leaderboard min |
|---|---|---|---|
| 24T203 (C₂×A₅) | 67 digits | **33** | 31 |
| 24T577 (C₂×S₅) | 87 digits | **53** | 30 |

Both recorded as new minima. √−1 roughly halves the digit count; the residual is dominated by
the **base field's** discriminant (the A₅/S₅ resolvent bases have large disc).

**Coverage:** added S₂₄ (24T25000, a primitive) and 3 S₅-top non-solvable groups (24T577,
24T19238, 24T20368, all scoreable) this round.

## Learnings

- **We've been mining popular groups** (0 sole) — low marginal score. The decisive lever is the
  **112k undiscovered signatures**: hitting any reachable one = sole = 1.0. Our current
  recipes mostly produce already-popular labels at r=0.
- **Disc-min is real and partly cheap:** for diagonals, α=−1 instead of α=q is a big, trivial
  win. Beating the leaderboard min the rest of the way needs **smaller-discriminant base
  fields** (smaller defining quintics / smaller-h fields), not just a smaller α.
- **Two concrete next directions:** (1) **signature diversification** — most of our builds are
  r=0 (complex bases); totally-/partially-real bases would hit undiscovered `(t, r>0)`; (2)
  **smaller bases** for disc-min. Both reuse the existing constructors.
