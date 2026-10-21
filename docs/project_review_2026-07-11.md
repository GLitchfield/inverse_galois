# Project review - methodology, scoring, and execution audit - 2026-07-11

Commissioned because the project has been driven by rapidly changing Claude-led strategy, with repeated
strategy flips and concern that conclusions were being made faster than they were being verified.

## Scope and caveats

- Reviewed the local tree at `main` HEAD `ee8664c` plus the current dirty worktree.
- Used the live local state files in `data/processed/` and current `data/targets/realized.csv`.
- Fetched the official IGP24 markdown rules from
  <https://competition.sair.foundation/competitions/igp24.md> on 2026-07-11.
- Did not mutate running data, queue state, active plans, or code. This document is the only intended
  output of the review.
- The worktree was already dirty: `data/targets/realized.csv`, `docs/commentary.md`, and three
  shell scripts had uncommitted changes. `realized.csv` alone showed about 1.46M inserted lines.

## Bottom line

The top-level strategy is basically sound: score is dominated by distinct scoreable `(t,r)` pairs,
especially non-baseline pairs with low `teamCount`, so breadth plus targeted construction is the right
game. The project has made real progress: current local coverage is 7,782 distinct groups and 22,077
local scoreable signatures, with official leaderboard score 671.1 and rank 17 in the cached leaderboard.

The methodology problem is not "no progress." It is unstable evidence handling. The repo contains many
examples where a lead was called greenlit, then later refuted by the first serious build or label check.
The best parts of the system are the validation gates that caught these errors. The worst parts are stale
docs/constants, premature "ceiling" or "greenlit" claims, and a live accounting pipeline that currently
has zombie submitted rows and mixed-discriminant drift.

Recommended posture: keep the breadth/tower strategy, but put a harder evidence ladder around all new
claims and repair scoring/accounting before spending more cycles on new speculative math.

## Current measured state

From `scripts/analyze_coverage.py`:

| metric | current value |
|---|---:|
| realized rows | 1,552,010 |
| distinct groups | 7,782 |
| scoreable signatures | 22,077 |
| scoreable rows | 1,088,489 |
| non-baseline scoreable signatures | 21,935 |
| baseline unlocks | 142 |
| sole 1.0 held by local heuristic | 78 |
| estimated score | 521.4 |
| cached official score | 671.1 |
| cached official rank | 17 |
| official scoreable pairs | 24,656 |
| mixed-disc rows in realized.csv | 1,021 |

From `scripts/analyze_block_structure.py`:

| stratum | realized groups | open groups | open signatures |
|---|---:|---:|---:|
| minblk=2, 12x2 | 7,514 | 8,902 | 30,749 |
| minblk=3, 8x3 | 227 | 144 | 328 |
| minblk=4, 6x4 | 24 | 609 | 3,315 |
| minblk=6 | 5 | 51 | 164 |
| minblk=8 | 5 | 27 | 102 |
| minblk=12 | 3 | 7 | 24 |

Summary: minblk=2 is still the dominant open board, but minblk>=3 remains a structural blind spot with
838 open groups and 3,933 open signatures. The non-solvable tail still has 94 open groups and 334 open
signatures.

From `scripts/check_invariants.py`:

- `I1`: 422 rows stuck in `submitted` for more than 24h.
- `I7`: 1,021 mixed-disc rows.
- Top failure taxonomy: `general_c2/empty=456779`, `general_c2/(untagged)=46695`,
  `lift/empty=15449`, `lift/(untagged)=6693`, `lift/verify-reject=2483`.

Tests:

- `.venv/bin/python -m pytest`: 42 passed.

## Priority findings

### P0 - Official rule drift is not fully integrated

The official rules now say:

- 1,000 submissions/day after the 5-scoreable unlock.
- 1,000 polynomials/submission.
- 1,000,000 bytes raw `submission.txt`.
- As of July 9, mixed discriminant is `nfdisc([f,100000])`.

The repo only partially reflects this.

Evidence:

- `src/igp/engine.py` uses a 1,000-polynomial cap in `submit_batch`, so the daemon path mostly knows the
  new API limit.
- `src/igp/submission.py` still documents and enforces `MAX_POLYS = 100`, `MAX_BYTES = 100_000`.
- `scripts/build_submission.py` still uses `MAX_POLYS, MAX_BYTES = 100, 99000`.
- `src/igp/mixed_disc.gp` still implements the older product-form fallback, not the official July 9
  `nfdisc([f,100000])`.
- `README.md`, `AGENTS.md`, `CLAUDE.md`, and `docs/competition_rules.md` disagree in places about the
  current byte/poly limits and current results.

Impact:

- Final submissions built from `realized.csv` can be underfilled by 10x.
- Local score estimates and scoreability heuristics can diverge from official scoring.
- Agents can make strategy decisions from stale local docs instead of the official rule source.

Recommendation:

1. Update `src/igp/submission.py`, `scripts/build_submission.py`, `src/igp/mixed_disc.gp`, and tests to
   match the official July 9 rules.
2. Treat `docs/competition_rules.md` as generated or explicitly dated. Add a small command that fetches
   and diffs the official markdown.
3. Add tests that assert the current official constants: 1,000 polys, 1,000,000 bytes, and mixed disc
   implemented as `nfdisc([f,100000])`.

### P0 - Local accounting does not currently reconcile with official accounting

Current local estimate is 521.4 points over 22,077 scoreable signatures. Cached official leaderboard
shows 671.1 points and 24,656 scoreable pairs. Some difference is expected because the local estimator is
an approximation, but the gap is large enough that it should be treated as an accounting bug until
explained.

Evidence:

- `scripts/analyze_coverage.py` reports official 671.1 vs estimate 521.4.
- `data/targets/realized.csv` has 936 scoreable rows with blank `field_disc`.
- There are 1,021 rows with `disc_source=mixed_disc`.
- `src/igp/engine.py` stores `field_disc = fieldDiscAbs or scoringDiscAbs`, which can blur exact field
  discriminant and official scoring discriminant.

Impact:

- The ranking and defense loops may optimize the wrong gaps.
- Baseline improvements require exact `nfdisc`; non-baseline mixed-disc rows can still score, but should
  not be mixed with exact field-disc rows in comparisons.
- "We hold min disc" and "recoverable loss" are unreliable unless the source of `D` is explicit.

Recommendation:

1. Store explicit fields: `field_disc_abs`, `mixed_disc_abs`, `scoring_disc_abs`, `disc_source`,
   `points`, `k_teams`, and `best_scoring_disc_abs` when the API provides them.
2. Recompute `analyze_coverage.py` using official `scoring_disc_abs`, not a conflated `field_disc`.
3. Add a reconciliation report: local pairs vs cached official pairs, with missing/excess pair lists.
4. Keep exact-vs-mixed separated in all baseline and disc-defense logic.

### P0 - The collection/queue state still has zombies

The invariant checker reports 422 rows stuck in `submitted` for more than 24h. Current queue status shows
905 `submitted` rows total.

Evidence:

- `scripts/check_invariants.py` fails on I1.
- `scripts/search_ctl.py status` shows 905 submitted rows.
- Queue family/status query shows the largest submitted groups are `gen12` and `lift`.
- `scripts/recover_stuck_pending.py` exists, and comments in `src/igp/engine.py` describe prior zombie
  patterns, but the invariant is still firing.

Impact:

- Some submitted polynomials may be verified officially but not reflected in `realized.csv`.
- `db.submitted_lines()` can suppress resubmission or skew duplicate accounting.
- Producer health and local coverage can lag official reality.

Recommendation:

1. Run the recovery path and reconcile the 905 submitted rows against verify cache and SAIR by submission
   id.
2. Add a queue-level recovery command that resolves old `submitted` rows, not just pending submissions.
3. Make I1 a stop-the-line alert for the headless audit loop.

### P0 - The final submission builder is stale

`scripts/build_submission.py` is useful in shape, but it still packs 100-polynomial / 99KB batches and
selects by `field_disc`, not an explicit official scoring discriminant.

Impact:

- It can leave most of the allowed final artifact capacity unused.
- It can choose the wrong representative for mixed-disc pairs.
- It can accidentally treat baseline rows with mixed-only data as comparable unless guarded elsewhere.

Recommendation:

1. Rebuild the final builder around official limits: 1,000 polys and 1,000,000 bytes.
2. Select one polynomial per expected `(t,r)` per submission, with exact-vs-mixed source rules.
3. For baseline pairs, require exact `nfdisc < D_base`.
4. Emit a manifest containing label, `r`, source, exact/mixed/scoring disc, baseline status, and reason.
5. Add tests for all of the above.

### P1 - The main strategy is sound, but the portfolio is overconcentrated

The core score logic is right: breadth over distinct scoreable signatures dominates small discriminant
improvements on crowded pairs. The minblk=2/gen12 lane is the engine, and recent high-r/totally-positive
work is well aligned with the open board.

But current coverage is highly concentrated:

- `gen12`: 1,216,683 realized rows, 17,270 scoreable signatures.
- `gen12treal`: 101,584 rows, 4,419 scoreable signatures.
- `sigfill`: 21,957 rows, 3,804 scoreable signatures.
- Current open 1.0 pairs: 43,685.
- Open 1.0 pairs in groups already realized: 9,003.
- minblk>=3 blind spot: 3,933 open signatures.

Recommendation:

1. Keep minblk=2 high-r/totally-positive work funded because it matches the largest open bucket.
2. Keep `no_submit` for random sparse enumerators; random quads/pents/tris are no longer a good use of
   official evaluation.
3. Allocate a deliberate lane to minblk>=3, especially minblk=4 and the remaining non-solvable tail.
4. Report marginal score per producer by distinct new signature, not by rows, and include queue cost.

### P1 - Disc defense is real, but the attempted mechanism has been refuted

`scripts/defend_held.py` estimates 131.6 recoverable points if we matched rival minimum discs, with 122.3
of that attributed to current-best `gen12` models. That is a meaningful score lever.

However, tests 0051-0054 show that the naive gen12 defense route is not reliable:

- v1 base-swap landed 0/390 on target.
- v2 same-base/smaller-prime and broad-`w` routes were blocked.
- v3 fingerprint pre-filter worked as a filter, but still produced 0/500 group-preserved improvements.
- The root cause is not just labeling; principality and kernel-submodule alignment are not preserved by
  the cheap swaps.

Recommendation:

1. Do not keep spinning same-top/same-`w`/smaller-base defense as a targeted method.
2. Either use broad post-hoc Magma filtering, accepting low efficiency, or build the relative
   Kummer/ray-class mechanism that can preserve the group.
3. Rank defense only by recoverable loss with fresh official `scoring_disc_abs`.
4. Never claim disc-defense recovery from intended labels; verify against realized `(t,r)`.

### P1 - "Greenlit" is too weak a label

There is a repeated pattern: research derives a plausible recipe, calls it greenlit, then a build refutes
the target group.

Examples:

- Test 0045: direct Res for the affine minblk=8 cluster built full wreaths, not the twisted targets.
- Test 0044: a 24315 route built 24672; later test 0055 found a different conic route that worked for
  low `r`.
- Tests 0051-0054: multiple gen12 disc-defense designs failed despite plausible premises.
- Test 0061: seven mb2 non-solvable split groups were structurally reachable, but only 24T9633 landed
  cleanly under the blind single-radical sweep.

This is not fatal. The validation-first gates prevented many bad submissions. But the terminology should
change because "greenlit" currently overstates confidence.

Recommendation:

Use explicit evidence levels:

- `LEAD`: mathematically plausible; not built.
- `LOCAL-GATED`: degree/r/discriminant/density checks pass locally.
- `PILOT-LABELED`: 1-5 candidates have official SAIR/Magma labels matching the target.
- `PRODUCER`: scaled only after pilot labels match and marginal score is measured.
- `BLOCKED` or `REFUTED`: stop spinning unless a new mechanism changes the premise.

No item should enter `docs/build_backlog.md` as ready for unattended build unless it is at least
`LOCAL-GATED`, and no family should scale until it is `PILOT-LABELED`.

### P1 - Producer health alerts need triage, not just logging

`scripts/search_ctl.py health` reports seven silent producers, including historically important ones
such as `produce_gen12_treal`, `produce_discmin`, and `produce_tr6`.

Some silence is probably benign exhaustion or gating. But the current alert text says "exhausted or
broken?" and leaves the distinction unresolved.

Recommendation:

1. Classify zero-output producers by reason: exhausted, queue full, no open targets, missing dependency,
   exception, stale progress, or actual bug.
2. For each producer, record denominator information: how many targets scanned, how many were dry, how
   many failed local gate, how many were skipped as not open.
3. Do not let silent-but-important producers sit as ambiguous alerts.

### P2 - Documentation is not a reliable source of truth

The repo's state docs are stale or contradictory:

- `AGENTS.md` still has 2026-06-28 numbers and 100/day constraints.
- `README.md` has 2026-07-03 numbers and an estimated score near 877, while current cached official
  score is 671.1.
- `CLAUDE.md` is more current than `AGENTS.md` in places, but still repeats old 100KB limits in places.
- `docs/phase_1_plan.md` still says 100 POST/day in its active plan text.

Recommendation:

1. Create one generated `docs/current_status.md` from `analyze_coverage.py`, queue status, and official
   rule fetch.
2. Make README/AGENTS/CLAUDE point to it instead of duplicating volatile numbers.
3. Keep plans historical unless deliberately revised with a dated change note.

### P2 - The raw coverage store is becoming too large and too duplicate-heavy

`realized.csv` has 1.55M rows for 22,077 scoreable signatures. That is about 49 scoreable rows per
scoreable signature, and many more rows per useful current-best representative.

This is not wrong: provenance matters. But it creates operational drag and review confusion.

Recommendation:

1. Keep the raw realized log, but generate a compact `best_by_pair` table used by ranking, submission,
   and score analysis.
2. Store source/provenance for the selected best row and keep raw rows queryable separately.
3. Add a duplicate pressure metric per producer: rows per distinct scoreable signature and marginal
   score per 1,000 builds.

### P2 - Headless Claude loops need stricter governance

The headless research/build/audit loop is powerful, but the user's concern is justified: the record shows
many rapid reframings, stale target assumptions, and overconfident labels that later needed correction.
The loops should not be removed; they should be constrained.

Recommendation:

1. Require fresh official `teamCount`, baseline, and valid-pair checks in every build note.
2. Require an evidence level on every claim and backlog item.
3. Require denominator audits before any "ceiling" claim.
4. Require a small official-label pilot before scaling any new family.
5. Have audit runs review the last N "greenlit" claims and mark them still-valid, stale, refuted, or
   superseded.

## Recommended execution order

1. Repair rule drift: current limits, July 9 mixed disc, and local docs/constants.
2. Reconcile accounting: zombie submitted rows, official-vs-local score gap, explicit scoring-disc fields.
3. Fix the final submission builder for 1,000 polys / 1MB and exact-vs-mixed source rules.
4. Keep the minblk=2 high-r/totally-positive breadth lane running, but measure marginal score per build.
5. Move speculative math into evidence levels; no scale-up before official pilot labels.
6. Re-scope disc defense away from same-`w` rebuilds and toward a mechanism that preserves the group.
7. Put a deliberate budget on minblk>=3 and the non-solvable tail after the accounting repair.

## What I would not do

- Do not abandon imprimitive/tower constructions. They are still the main path to coverage.
- Do not return to random sparse polynomial flooding as a major lane.
- Do not treat famous primitive groups as likely high score unless current `teamCount` says they are open.
- Do not trust row counts, intended labels, or stale docs as score evidence.
- Do not keep relitigating a refuted construction without a new mechanism that changes the failed premise.

## Verification performed

- Official rules fetched from <https://competition.sair.foundation/competitions/igp24.md>.
- `.venv/bin/python scripts/analyze_coverage.py` completed.
- `.venv/bin/python scripts/check_invariants.py` completed and reported violations.
- `.venv/bin/python scripts/analyze_block_structure.py` completed.
- `.venv/bin/python scripts/search_ctl.py status` and `health` completed.
- `.venv/bin/python scripts/defend_held.py` completed.
- `.venv/bin/python -m pytest` passed: 42 tests.
