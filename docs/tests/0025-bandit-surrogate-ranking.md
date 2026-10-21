# 0025 — Adaptive ranking: producer bandit + per-row surrogate (ML over the daemon)

**Family:** infra / ML · **Date:** 2026-06-27 · **Modules:** `igp/rank.py`,
`igp/searchstore.py` (priority), `scripts/search_ctl.py` (`rank`)

## Question

The daemon claimed work FIFO — blind. Can we make it **value-prioritized** using the data we've
accumulated (240+ verified constructions with params → 24Tt, scoreable, teamCount), so it builds
high-yield constructions first and wastes fewer Magma calls? (The ML angles #1+#2.)

## Method

Unified through a `priority` column (`claim` is now `ORDER BY priority DESC, id`), set by the tick:
- **Bandit (#2, per producer):** each producer (target prefix) is an arm; reward = (scoreable +
  2·sole)/n; UCB1 weight = reward + 0.7·√(ln N / n) (exploit yield, still explore thin arms).
- **Surrogate (#1, per row):** a `GradientBoostingClassifier` trained on verified rows (features:
  base degree, kernel weight, log prime, kind one-hot) predicting P(scoreable); priority =
  bandit_weight(producer) + surrogate_score(row). Degrades gracefully (no sklearn / <40 rows →
  bandit-only).

## Result

`search_ctl rank` on the live data:
```
producers (UCB):  size3 1.82,  g6x4 1.41,  size4 1.39,  discmin 1.38,
                  spec 1.27,  comp 1.27,  lmfdb6x4 1.24,  tri 0.65
surrogate_scored: 50 queued rows
```
The daemon now claims **size3 (8×3) and g6x4 first, trinomials last** — matching their measured
yield. 29 tests green (bandit ordering + exploration unit-tested).

## Learnings

- **Data says 8×3 (size3) is our most productive shape, trinomials the least** — the bandit turns
  that into action automatically, no hand-tuning. This is the right role for ML here: a
  **heuristic/credit-assignment layer over the expensive Magma oracle**, not a solver (the
  construction itself stays exact algebra).
- Priority unifies coarse (bandit) + fine (surrogate) signals; the tick recomputes it each cycle,
  so it adapts as data accrues. Computed in the tick (not the daemon loop) → daemon stays light,
  sklearn isn't a daemon dependency.
- Next ML follow-ons (as data grows): a disc-min surrogate (predict `nfdisc` to guide the #4 GA),
  and richer features (base Galois label, ramification) for the scoreable model.
