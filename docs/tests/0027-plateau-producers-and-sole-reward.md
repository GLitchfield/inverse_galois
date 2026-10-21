# 0027 — Breaking the producer plateau: 8×3 expansion + sole-aware bandit reward

**Family:** infra / search · **Date:** 2026-06-28 · **Code:** `scripts/search_ctl.py`
(`produce_trinomials`, `produce_size3`, `produce_size3_compositum`, `_diverse_deg8_bases`),
`src/igp/rank.py` (`bandit_weights`), `src/igp/searchstore.py` (`has_target`)

## Question

After ~a day the search plateaued: queue dry, all 8 producers enqueuing 0 (saturated), coverage
flat at 287 groups / 434 scoreable. Diagnosis (status review): the binding constraint was never
posting throughput (we posted 68 then 1/day against a 500 cap) — it was **producer supply**. Two
fixes the data pointed to: (1) the bandit ranked **8×3 (size3) top** but it was one saturated base
(n=4 samples, rank mostly *exploration bonus*) — supply the shape it's begging for; (2) the bandit
ranked the **trinomial sweep last** (61% scoreable rate) even though trinomials produced **9 of our
14 sole realizers** — the rate-based reward starves the rare-find engine.

## Method

**(2) Reward — credit sole discovery, not just rate** (`bandit_weights`): add an undiluted term
`sole_share = sole_share_weight · producer_sole / total_sole` so a producer earns standing for its
share of ALL sole realizers found, independent of sample count. (UCB efficiency + exploration terms
unchanged.)

**(1) Supply — three producer expansions:**
- `produce_trinomials`: 48 → **200**, widened to `k∈1..12`, `|a|,|b|≤5` (the sole engine).
- `produce_size3`: one base (Q(ζ₁₅)) → **three** ζ-bases {15, 24, 30} (all have φ=8 and 3|n ⇒ clean
  cyclic C₃ Kummer; distinct abelian degree-8 tops), with richer length-8 exponent patterns.
- `produce_size3_compositum` (**new**): diverse irreducible degree-8 fields (`_diverse_deg8_bases`,
  polredbest-deduped sweep) × a fixed **cyclic cubic** (conductor 7) via `gp.compositum` → degree-24
  `ready` polys with group (deg-8 top)×C₃. Generalises 8×3 to *non-abelian* degree-8 tops the three
  cyclotomic bases can't reach. `searchstore.has_target` pre-dedups so the tick skips recomputing the
  expensive composita once seeded.

## Result

Queue 0 → **284** on the spot: trinomials **+200**, size3 **+60** (3 bases), compositum **+24**
(24 diverse degree-8 bases × cyclic cubic). Plateau broken; the daemon claimed and submitted the
first 50 within the minute.

Bandit re-rank with the sole-share term (live stats): trinomials jump from **last (0.829)** to near
the top (sole_share ≈ 9/9 attributed soles), so the rare-find engine is no longer starved; the
under-sampled size3 still leads on its exploration bonus, now with real supply behind it.

Lint clean; **30 tests** green (new `test_bandit_sole_share_rescues_broad_sweep` pins the behavior:
the broad sweep must out-rank a reliable zero-sole producer, and does so *only* via the share term).

## Learnings

- **The plateau was supply, not settings.** Throughput knobs drained the backlog fast and then
  exposed the real ceiling; the fix is producers, exactly as the status review predicted.
- **The bandit was already pointing at the answer.** size3's #1 rank was mostly the exploration
  bonus on n=4 — "sample this shape more." We did (3 bases + compositum).
- **Reward design matters for scoring, not just efficiency.** Sole realizers (teamCount==0) are the
  highest-value, rarest finds and come from broad search, not targeted construction. A pure
  scoreable-rate reward optimises the wrong thing; crediting sole-*discovery share* realigns it.
- **Compositum is a cheap diversity multiplier.** (deg-8)×C₃ `ready` polys need no kernel alignment
  (Magma labels the result), so arbitrary degree-8 tops become reachable 8×3 groups for free.
