# 0039 — The "TRUE 1.0 = teamCount==0" metric was wrong (it measured submission lag)

**Family:** infra / metrics · **Date:** 2026-06-30 · **Code:** `scripts/analyze_coverage.py`,
`src/igp/rank.py`

## Trigger

Morning status check: `analyze_coverage` reported **TRUE 1.0 held: 41 → 0** overnight, alongside big
coverage gains (groups 457 → 621, scoreable sigs 524 → 734). Losing all 41 sole pairs while only
~2,400 of 87k open targets were claimed didn't add up.

## Investigation

`progress.json` refreshed overnight (the 12h tick). Our held tsig pairs (e.g. 24T5343 r12,
24T10268 r8) flipped from teamCount==0 to **teamCount==1**. Two facts settle the semantics:

- **87,155 entries have teamCount==0** — these are the OPEN targets (we report "open 1.0 = teamCount
  ==0, not ours = 87,045"). If teamCount==0 meant "we're sole," we'd be claiming 87k pairs. So
  **teamCount==0 = NOBODY is credited.**
- For all **44** non-baseline scoreable pairs at teamCount==1, **minDisc == our disc** (0 mismatches)
  — i.e. we ARE the single credited team. So **teamCount==1 (held) = us alone = sole = 1.0** (score
  2^(1-1)·log(D0)/log(D) = 1.0, sole ⇒ we hold the min).

So a freshly-submitted-but-not-yet-counted pair shows teamCount==0 (lag); once the leaderboard
counts us it becomes teamCount==1. The old metric `TRUE 1.0 = held ∧ teamCount==0` was reading the
**submission lag**, not sole-ness — it inflates right after a submission burst and collapses to 0 on
the next progress refresh. (This also revises the test 0032/0033 interpretation: those "sole" counts
were the lag; the real sole metric is teamCount==1.)

## Fix

- `analyze_coverage`: `SOLE 1.0 held = held ∧ non-baseline ∧ teamCount<=1` (1 = us, 0 = pending). Added
  **ESTIMATED TOTAL SCORE** = Σ 2^(1-k)·log(D0)/log(D) over held scoreable (baseline-capped 0.5) — the
  honest headline, robust to the lag.
- `rank.py`: the bandit's `sole` reward used teamCount==0 → changed to `<=1` (it was crediting the lag).
- Open-target definition (teamCount==0, not ours) is unchanged — that one was correct.

## Result (corrected, 2026-06-30)

```
distinct groups 621 | scoreable sigs 734 (721 non-baseline + 13 baseline-unlocks)
SOLE 1.0 held (teamCount<=1) = 44      [was misread as 0]
ESTIMATED TOTAL SCORE ~ 72.9 points
open 1.0 targets 87,045 | disc-min: we hold the min on 140/734
```

## Learnings

- **Know exactly what a leaderboard field counts (does it include you?) before building a metric on
  it.** The whole "sole 1.0" headline hung on a wrong assumption about teamCount, and it took a
  scary-looking 41→0 to catch it. (Same family as the rows-vs-sigs and "famous≠open" lessons: verify
  the unit that actually scores.)
- **Track an estimated TOTAL SCORE, not just a sole count** — it's lag-robust and is what we actually
  optimize. ~73 points now (44 from sole pairs + the shared-pair tail).
