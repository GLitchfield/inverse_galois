# Project review - pipeline, scoring, and optimization audit

**Date:** 2026-06-28  
**Scope:** mathematical strategy, live search pipeline, ranking/scoring logic, data hygiene, and near-term
optimization opportunities.  
**Inputs reviewed:** Phase 1 plan, harness notes, competition rules, recent tests 0025/0028/0029/0030,
`src/igp/*`, `scripts/searchd.py`, `scripts/search_ctl.py`, `scripts/analyze_coverage.py`, live
`search.db`, `realized.csv`, `progress.json`, and read-only SAIR submission history.

## Executive summary

The project is pointed in the right mathematical direction: imprimitive/tower/radical constructions are
the correct coverage workhorse, the scoring model correctly prioritizes scarce `(t,r)` signatures, and
the S24 skip filter is mathematically sound for the intended low-value generic-polynomial flood.

The biggest problems are now operational and metric-related:

1. The daemon is spending the hard 100 POST/day cap on underfilled submissions.
2. Ranking still optimizes too much for scoreable rows instead of marginal distinct `(t,r)` value.
3. Some realized scoreable signatures lack recorded discriminants.
4. Signature diversification has large untapped headroom among groups already reached.

Fixing POST packing and ranking should increase value per day before any new mathematical family is
added.

## Current measured state

From `scripts/analyze_coverage.py`:

| Metric | Value |
|---|---:|
| Realized rows | 3221 |
| Distinct groups | 319 |
| Scoreable rows | 2005 |
| Distinct scoreable signatures | 263 |
| Beyond-baseline scoreable signatures | 258 |
| Currently sole signatures | 5 |
| Scoreable row/signature duplication | 7.6x |
| Scoreable signatures with our disc and leaderboard min | 202 |
| Behind on disc among those | 172/202 |

From live `progress.json`:

| Metric | Value |
|---|---:|
| Total signatures | 165836 |
| `teamCount == 0` signatures | 101391 |
| Participant-discovered signatures | 64445 |
| Max observed `teamCount` | 37 |

From read-only SAIR submission history:

| Date | POSTs | Polynomials | Avg polys/POST | Min/max |
|---|---:|---:|---:|---:|
| 2026-06-24 | 2 | 4 | 2.0 | 2-2 |
| 2026-06-25 | 14 | 392 | 28.0 | 1-100 |
| 2026-06-26 | 8 | 31 | 3.9 | 1-6 |
| 2026-06-27 | 81 | 341 | 4.2 | 1-50 |
| 2026-06-28 | 100 | 2485 | 24.9 | 6-50 |

Tests pass: `./.venv/bin/python -m pytest` -> 31 passed.

## Priority findings

### P0 - POST packing is the largest immediate throughput leak

The daemon claims `build_batch` rows, filters S24 candidates, then submits whatever remains:

- `scripts/searchd.py`: claim at `build_batch`, filter, submit one batch.
- Live `build_batch` is 50.
- The S24 filter drops a large fraction of sparse-polynomial rows before submission.
- 2026-06-28 used all 100 POSTs for only 2485 polynomials, average 24.9 per POST.
- Recent submissions were often 11-17 polynomials.

Since the binding competition cap is POSTs/day, not polynomials/day, the daemon should pack submissions
after filtering. This is likely a 3x-4x daily throughput improvement under the same cap.

Recommended fix:

- Replace one `claim(build_batch) -> filter -> submit` cycle with an accumulator loop.
- Claim more queued rows while `len(cands) < 100`.
- Build/filter each candidate, stopping at 100 polynomials, 100 KB payload, queue exhaustion, or a
  reasonable work cap.
- Track and display `polys_per_post` and `filtered_per_post_attempt`.
- Split knobs into `claim_batch`, `submit_target`, and `max_builds_per_post`.

### P0 - Ranker overcredits sole discoveries and optimizes rows, not distinct signatures

`src/igp/rank.py` checks `progress[f"{t},0"]` for sole credit regardless of the realized row's actual
`r`. That gives the wrong reward whenever the realized signature is not `(t,0)`.

Measured effect:

- Current ranker stats: quad has 6 sole hits.
- Actual `(t,r)`-matched stats: quad has 0 sole hits.
- Current producer weights overcredit the broad sparse flood.

The bigger issue is that the reward model is row-level:

| Producer | Scoreable rows | Distinct scoreable sigs | Duplication | Current sole sigs |
|---|---:|---:|---:|---:|
| quad | 1315 | 54 | 24.4x | 0 |
| tri | 336 | 38 | 8.8x | 1 |
| lmfdb6x4 | 56 | 40 | 1.4x | 0 |
| discmin | 26 | 26 | 1.0x | 0 |

Recommended fix:

- Join `store.verified_rows()` to `realized.csv` by coefficient line, then score the actual `(t,r)`.
- Reward producers by marginal distinct-signature value: new `(t,r)`, actual `teamCount == 0`,
  smaller field discriminant for an already-held signature, and baseline unlocks with exact `nfdisc`.
- Penalize duplicate rows per signature, especially for sparse flood producers.
- Train the surrogate on labels like `new_sig`, `sole_sig`, and `disc_improved`, not only `scoreable`.

### P0 - Realized DB has scoreable signatures with missing discriminants

Audit result:

- 97 scoreable rows have blank `field_disc`.
- These affect 61 distinct scoreable signatures.
- 83 rows belong to signatures where no alternative row has a recorded field discriminant.

This affects disc-headroom analysis, final best-poly selection, score estimation, and ranking by
discriminant quality.

Root cause:

- Historical scripts wrote older row schemas.
- `src/igp/db.py` uses `existing.setdefault(r["coeffs"], norm)`, so a later richer result cannot update
  an existing row with missing fields.

Recommended fix:

- Change `record_realized` to merge missing/blank fields from newer data.
- Add fields to `realized.csv` or a companion table: `disc_source`, `scoring_status`,
  `baseline_disc_abs`, `submission_id`, and `polynomial_index`.
- Backfill missing `field_disc` from saved SAIR JSON if available, otherwise local PARI/GP `nfdisc`.
- Add an audit gate: no `scoreable=true` row may have blank `field_disc` unless `disc_source=mixed_disc`
  and the API genuinely omits a numeric value.

### P1 - Collection should handle partial scoring and failed polynomials explicitly

`engine.collect()` records `verifiedPolynomials` and removes the submission from pending once
`queuedPolynomials` is empty. It does not record `failedPolynomials`, and the queue sync can leave failed
submitted rows stuck.

Live SAIR history showed:

- 3240 verified polynomials.
- 13 failed polynomials.
- 1 scoreable mixed-disc result without a numeric disc.

Recommended fix:

- Persist `submission_id` and `polynomialIndex` per queued row.
- Mark queue rows as `failed` when the API reports `failedPolynomials`.
- If a verified row has `scoreable=true` but no numeric disc, record `disc_source` and keep a follow-up
  state such as `verified_incomplete_scoring` or `mixed_disc_no_numeric`.
- Avoid marking all candidates `submitted` when `engine.submit` dedupes a subset.

### P1 - Signature diversification is the cleanest mathematical scoring lever

Current coverage hits many groups at very few real-root counts:

- 241 of 319 realized groups have only one observed `r`.
- 178 scoreable groups have only one scoreable `r`.
- Among already-realized groups, there are 1888 allowed but unrealized `r` values.
- Of those, 304 currently have `teamCount == 0`.

This is a high-value target class because it avoids the uncertainty of finding new groups from generic
sparse polynomials while still going after first-claim signatures.

Recommended work:

- Build a `signature_fill` producer from realized groups and authoritative allowed `r`.
- Prioritize `teamCount == 0` missing `r`, then low `teamCount`, then disc-improvable signatures.
- Extend the totally-real base approach for C2 kernels using sign-controlled alpha.
- For composita/product-action, explicitly derive target real-root counts from factor signatures and
  enqueue combinations that hit missing allowed `r`.

### P1 - Add a final submission builder

`src/igp/submission.py` validates coefficient strings, but there does not appear to be a committed script
that builds the final deliverable from `realized.csv`.

Recommended builder behavior:

- Select one polynomial per `(t,r)`.
- Prefer smallest numeric `field_disc`.
- For non-baseline pairs, include scoreable rows and rank by expected score.
- For baseline pairs, include only exact `nfdisc < baselineDiscAbs`.
- Exclude or separately report rows with unknown/mixed numeric discriminant.
- Enforce 100-polynomial and 100 KB limits.
- Emit a manifest with selected label, `r`, disc, source, and reason.

### P1 - Recover baseline membership and stale doc state

There is a documentation mismatch:

- `docs/competition_rules.md` says the frozen baseline CSV is in git at
  `competition/baseline/lmfdb_baseline.csv`.
- The current tree does not show that file.
- `docs/harness_notes.md` still says baseline membership is not exposed by `/labels/progress` and the
  baseline list is still needed.
- `docs/phase_0_synthesis.md` says per-group reachable `validR` is still unconfirmed, while the API
  `allowedR` data is now being used as authoritative.

Recommended fix:

- Decide the current source of truth for baseline membership.
- Update stale docs in one small documentation commit.
- If possible, build `data/targets/baseline_signatures_deg24.csv` with `t,r,D_base`.

## Mathematical strategy review

### What looks sound

- The imprimitive/wreath/tower focus is mathematically appropriate.
- The C2-kernel framework over degree-12 bases is a strong deliberate-construction primitive.
- Composition vs compositum is correctly distinguished.
- The score interpretation is right: `2^(1-k)` dominates log-discriminant improvements.
- The S24 filter is sound for the intended skip.

### What needs more caution

- `discovered=false` in `/labels/progress` is participant-only. It is not identical to non-baseline.
- Generic sparse-polynomial searches find many scoreable rows but duplicate signatures heavily.
- Discriminant minimization should target field construction quality, not coefficient reduction.
- Mixed-disc results need special handling because they may be scoreable while lacking a comparable
  numeric `field_disc` in the API response.

## Recommended execution order

1. Fix POST packing in the daemon.
2. Fix ranker rewards to use actual `(t,r)` and distinct marginal value.
3. Backfill and harden `realized.csv` discriminant/scoring fields.
4. Add a final submission builder from `realized.csv`.
5. Add a signature-fill producer targeting missing allowed `r`, especially `teamCount == 0`.
6. Clean up stale baseline/validR documentation and decide the baseline source of truth.
7. Continue disc-min as a post-processor, focused on minimal-base constructions and the largest
   log-disc gaps.

## Suggested new tests

- Daemon packing: simulate 80% filter drop and verify one POST accumulates up to the target number of
  survivors.
- Ranker: producer sole credit uses actual `(t,r)`, not `(t,0)`.
- Ranker: duplicate scoreable rows do not dominate distinct-signature producers.
- DB merge: later rows fill blank `field_disc`, `disc_source`, and `scoring_status`.
- Collector: failed polynomial indices mark the matching queue rows failed.
- Collector: scoreable rows without numeric disc are not silently treated as ordinary complete rows.
- Submission builder: one row per `(t,r)`, smallest disc wins, baseline rows require a strict disc beat,
  and byte/poly limits are enforced.

## Review caveats

- I did not mutate code or data during the review.
- `data/targets/realized.csv` was already modified and `AGENTS.md` was already untracked when checked.
- The SAIR API was queried read-only for submission history and current scoring shape.
- The final recommendations assume the current 100 POST/day team cap remains binding.
