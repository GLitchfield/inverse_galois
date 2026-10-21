# 0035 — Raised submission limits + anti-junk gating

**Family:** infra / ops · **Date:** 2026-06-29 · **Code:** `scripts/searchd.py`,
`src/igp/rank.py`, `src/igp/searchstore.py`, `scripts/search_ctl.py`

## Question

SAIR raised submission limits 10× on 2026-06-29 (Zulip): **1000 polys/submission + 1000
submissions/day** (was 100/100), but organizers asked contestants not to "submit a million random
polynomials." How do we use the new throughput for *quality* without flooding junk?

## Method / findings

Per-producer marginal value (distinct scoreable `(t,r)` per attributed row) cleanly separates the
producers:

| tier | producers | sig/row |
|---|---|---|
| targeted | `tsig` | 1.00 |
| structured | `discmin` .96, `g6x4` .88, `lmfdb6x4` .71, `sigfill` .68, `size4` .62 | 0.6–1.0 |
| **junk (inexhaustible random enumerators)** | `quad` **.01** (9343 rows → 108 sigs), `pent` .02, `tri` .09 | < 0.1 |

But the daemon would have submitted the junk first: the per-row **surrogate score swamped the
bandit signal** (additive `w + prob + disc_bonus`), lifting `quad` rows to priority ~1.15 despite a
bandit weight of 0.034 — so 3842 queued quad polys outranked `sigfill` (1.0). Four fixes:

1. **Multiplicative ranking** (`rank.py`): `priority = w · (1 + prob + disc_bonus)`. The surrogate
   now refines order *within* a producer but can't lift a near-zero-value one. `quad` → 0.07,
   `sigfill` → 1.93 (verified post-change).
2. **`no_submit` denylist** (`searchd.py`, kv-tunable `{quad,pent,tri}`): skip + mark `skipped`
   *before* construct — never build or submit the random enumerators.
3. **Dropped quad/pent/tri from auto-production** (`search_ctl.py` tick) — stop *generating* what we
   won't submit; still runnable by hand (`produce-quad/pent/trinomials`).
4. **Stale-claim recovery** (`searchstore.requeue_building`, called on daemon startup): a row is
   `building` only between claim and its terminal mark, so a stop/crash mid-cycle orphaned those
   claims forever (`claim()` takes only `queued`) — lost work. On the next restart it **recovered
   1867 orphaned rows** (the daemon stops for commits had been silently leaking the queue).

Limits set: `submit_target=1000`, `max_posts_day=1000` (kv).

## Result

After re-rank + daemon restart: queued priority `sigfill 1.93 ≫ pent 0.25 > quad 0.07` (junk last);
the recovered junk rows were claimed and `skipped` (skipped 256 → 2006), **none submitted**;
`engine.submit` still dedups vs `submitted_lines`. The 1000/day capacity is now available for
targeted + structured + disc-min output, with the random floods gated off at both production and
submission.

## Learnings

- **Capacity ≠ permission to flood.** The right response to a 10× limit raise is to *remove the
  bottleneck* (pack 1000/POST, lift the daily cap) while *adding a value gate*, not to drain every
  enumerator. Dedup + ranking + denylist are the anti-abuse safeguards, not the daily cap.
- **A blended priority can invert producer value.** Additive surrogate blending let a 0.03-value
  producer outrank a 0.9 one. Multiplicative keeps the producer signal dominant — the surrogate
  should *order within*, not *override*.
- **Disc-min producers are NOT junk even at low sig/row** — their value is a smaller disc on a held
  pair (`log(D0)/log(D)` rises as `D→D0`), which sig-count misses. So we gate by an explicit
  enumerator denylist, not a blanket sig/row floor that would wrongly cut `discmin`/`discmin2`.
- **`building` is a claim, and claims must be recoverable.** Any status that means "in progress"
  needs a startup sweep back to the work queue, or restarts leak it. (Quality rule: fail safe,
  never lose work.)
