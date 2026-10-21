# Results (final state at pause, 2026-07-14)

Aggregate numbers only. The polynomials themselves, and any per-group or per-pair lists, are not
published. Every number below names the file it was read from. Most of those files are local
pipeline state that is gitignored (`data/processed/`, `logs/`, `data/targets/realized.csv`), so a
clone of this repository cannot recompute them. The scripts that wrote them are published.

Terms:

- **group**: a transitive group `24Tt`, `t = 1..25000`.
- **pair**: a signature `(t, r)`, where `r` is the number of real roots. There are 165,836 valid
  pairs (`data/targets/valid_pairs.csv`).
- **verified polynomial**: a polynomial that SAIR's verifier returned in its `verifiedPolynomials`
  list, with an official Magma `24Tt` label and `r`. Only these are recorded in `realized.csv`
  (`src/igp/engine.py::collect`).
- **scoreable pair**: a pair for which SAIR flagged at least one of our verified polynomials as
  `scoreable`. That means a non-baseline pair, or a baseline pair where our exact `nfdisc` beats
  `D_base`.

## Coverage at the last snapshot (2026-07-14 13:09 UTC)

| Metric | Value | Source |
|---|---:|---|
| Distinct groups realized (verified polynomial with that `24Tt` label) | **7,956** of 25,000 | `data/processed/coverage_history.jsonl`, last row; matches `data/targets/realized.csv` |
| Distinct scoreable pairs (local flags) | **22,708** | same |
| Scoreable pairs credited on the official leaderboard | 25,296 | `data/processed/leaderboard.json` (fetched 2026-07-14 13:23 UTC) |
| Distinct verified polynomials | **1,713,813** | `data/targets/realized.csv` (one row per distinct coefficient vector) |
| Verified polynomials flagged scoreable | 1,207,327 | `data/targets/realized.csv` |
| Distinct labeled pairs, scoreable or not | 25,352 | `data/targets/realized.csv` |
| Non-solvable groups realized | 316 of 807 | `realized.csv` against `data/targets/nonsolvable_t.txt` |
| Primitive groups realized | 4 of 5 (all except A24) | `realized.csv` against `data/targets/transitive_groups_deg24.csv` |

The local scoreable count trails the official one by about 2.6k pairs. SAIR scores discriminants
asynchronously, and some of our polynomials changed from pending to scoreable after we had already
collected them. The 2026-07-12 and 2026-07-14 audits measured the gap with
`scripts/reconcile_accounting.py` (see [audit_log.md](audit_log.md)). The official count is the
authoritative one.

## Compared with the LMFDB baseline

The frozen LMFDB baseline in the competition package covers **286 groups and 622 pairs**. Source:
`competition/baseline/lmfdb_baseline.csv` in the IGP24 package (snapshot 2026-05-20), reduced to
`data/targets/baseline_signatures.csv`. Both numbers were recomputed from the package file.

| | LMFDB baseline | This project (2026-07-14) |
|---|---:|---:|
| Groups | 286 | 7,956 (7,803 of them outside the baseline's 286) |
| Scoreable pairs | 622 known pairs | 22,708 (22,525 non-baseline, plus 183 baseline pairs where our exact `nfdisc` beat `D_base`) |

Source: `realized.csv` against `baseline_signatures.csv`.

## Official score history

SAIR's leaderboard score sums `2^(1-k) * log(D0)/log(D)` over a team's scoreable pairs. Here `k` is
the number of teams credited on the pair, `D0` is the smallest discriminant any team has submitted,
and `D` is ours (`docs/competition_rules.md`). The daemon copied the official score and rank into
`coverage_history.jsonl` whenever its leaderboard fetch was under 2 hours old, so official values
start on 2026-07-03.

| Highlight | Value | Source |
|---|---|---|
| First official reading logged | 742.5, rank 14 (2026-07-03 20:16 UTC) | `coverage_history.jsonl` |
| Best rank | **12**, first reached 2026-07-04 04:46 UTC at 855.1; held until 21:07 UTC (1,047.4) | `coverage_history.jsonl` |
| Peak official score | **1,091.1** at rank 14 (2026-07-05 03:08 UTC) | `coverage_history.jsonl` |
| Last snapshot | 598.3, rank 19 (2026-07-14 13:09 UTC) | `coverage_history.jsonl` |
| Last leaderboard fetch | 597.7, rank 19 (2026-07-14 13:23 UTC) | `leaderboard.json` |
| Rank-1 team at the last fetch | 26,845.4 points, 87,583 scoreable pairs | `leaderboard.json` |

Daily view, using the last snapshot of each UTC day. The log appends a row only when the coverage
counters change, so a day's last row can come before midnight.

| Date (UTC) | Groups | Scoreable pairs | Local estimate | Official | Rank | Best rank that day | Peak official that day |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-06-30 | 1,840 | 2,973 | 396.4 | | | | |
| 2026-07-01 | 2,882 | 5,234 | 459.1 | | | | |
| 2026-07-02 | 3,882 | 7,820 | 772.8 | | | | |
| 2026-07-03 | 4,808 | 10,399 | 880.7 | 787.9 | 13 | 13 | 787.9 |
| 2026-07-04 | 6,045 | 14,648 | 1,262.8 | 1,048.3 | 13 | 12 | 1,049.5 |
| 2026-07-05 | 6,569 | 16,232 | 621.3 | 701.9 | 15 | 13 | 1,091.1 |
| 2026-07-06 | 6,915 | 18,174 | 682.5 | 826.2 | 15 | 15 | 828.6 |
| 2026-07-07 | 6,974 | 18,400 | 680.1 | 823.3 | 15 | 15 | 838.4 |
| 2026-07-08 | 6,981 | 18,405 | 591.0 | 736.8 | 15 | 15 | 804.3 |
| 2026-07-09 | 7,030 | 18,599 | 525.1 | 649.1 | 15 | 15 | 711.3 |
| 2026-07-10 | 7,209 | 19,904 | 549.0 | 663.2 | 15 | 15 | 663.2 |
| 2026-07-11 | 7,846 | 22,344 | 527.4 | 683.5 | 17 | 15 | 687.0 |
| 2026-07-12 | 7,911 | 22,555 | 486.2 | 640.7 | 17 | 17 | 687.6 |
| 2026-07-13 | 7,952 | 22,647 | 461.9 | 611.6 | 18 | 17 | 639.1 |
| 2026-07-14 | 7,956 | 22,708 | 455.0 | 598.3 | 19 | 18 | 616.4 |

"Local estimate" is the pipeline's own estimate of the same formula, computed from `realized.csv`
and the per-pair leaderboard state in `progress.json` (`src/igp/coverage.py::snapshot`).

**Why the score fell while coverage grew.** After 2026-07-05, other teams realized many of the
same pairs, which raised `k` and halved or quartered each pair's weight. They also submitted
smaller discriminants, which lowered `D0`. Our count of pairs where we were the only credited team
fell from a peak of 576 (2026-07-05 02:30 UTC) to 81 at the last snapshot (`coverage_history.jsonl`,
field `sole`). At the 2026-07-14 audit, a rival held a smaller discriminant on 97% of our scoreable
pairs, and 88% of those pairs had `k >= 6`. That audit concluded the project was value-bound, not
breadth-bound ([audit_log.md](audit_log.md), 2026-07-14 entry). An attempt to recover discriminant
headroom with a fingerprint-gated re-sweep was refuted by SAIR's labels
([commentary.md](commentary.md), 2026-07-13 correction).

## Where the coverage came from

Verified polynomials and distinct scoreable pairs by the producer tag recorded in `realized.csv`
(`source` column). A pair can be scored by several producers, so the pair column does not sum to
the total.

| Producer | What it builds | Verified polynomials | Scoreable pairs |
|---|---|---:|---:|
| `gen12` | `C2` kernel `K0(sqrt(alpha))` over non-Galois degree-12 LMFDB bases (12x2 blocks) | 1,304,840 | 17,497 |
| `gen12treal` | the same over totally real bases, which reach high `r` | 102,215 | 4,459 |
| `sigfill` | signature fill: totally real bases chosen to add missing `r` values | 60,526 | 4,192 |
| `mb2` | targeted bases for unrealized minimal-block-2 groups | 10,452 | 2,311 |
| `lift` | orbit-sign quadratic lifts `K12(sqrt(delta))` | 8,937 | 724 |
| `rfill` | split-prime re-dial of `r` on groups already held | 2,873 | 583 |
| `compose` | compositions `f(g(x))` (wreath shapes 2x12, 3x8, 4x6) | 76,725 | 482 |
| `lmfdb6x4` | biquadratic `V4` kernels over degree-6 LMFDB bases | 3,343 | 360 |
| `g8x3s3` | `S3` cubic kernels over degree-8 bases | 66,349 | 347 |
| `abelian` | cyclic `C_n` ray-class-field kernels (test 0065) | 716 | 166 |
| `quad` | sparse quadrinomials | 9,543 | 109 |
| `c8x3` | degree-8 field x cyclic cubic composita | 19,895 | 79 |
| `g6x4s4` | `S4` quartic kernels over degree-6 bases | 40,294 | 72 |
| all other tags (about 25 targeted, literature and early-script tags) | | 7,105 | 481 |
| **Total** | | **1,713,813** | **22,708** |

Source: `data/targets/realized.csv`. The construction behind each producer is documented in the
numbered tests (`docs/tests/`, indexed in [research_log.md](research_log.md)).

## Autonomous agent run ledger

Headless Claude Code runs launched by systemd timers (`scripts/run_headless_agent.sh`). Counts and
tokens come from `logs/headless_{research,build,audit}.log`. Each completed run appends one
`[usage]` line, written by `scripts/headless_cost_summary.py` from the CLI's JSON result.

| Loop | Runs launched | First run (UTC-4) | Last run (UTC-4) | Runs with a usage record |
|---|---:|---|---|---:|
| research (every 2 h) | 152 | 2026-07-01 09:29 | 2026-07-14 08:41 | 146 |
| build (every 3 h, from 2026-07-07) | 51 | 2026-07-07 12:23 | 2026-07-14 09:23 | 50 |
| audit (daily 08:17) | 13 | 2026-07-02 08:17 | 2026-07-14 08:17 | 13 |
| **Total** | **216** | | | **209** |

Six research runs and one build run have no finish line. The build run was the one in progress
when the runners were shut down on 2026-07-14. Of the runs that finished, 7 exited non-zero
(6 research, 1 build).

Token usage summed over the 209 usage records:

| | Tokens |
|---|---:|
| Total | 580,774,581 |
| Cache reads | 548,863,765 |
| Cache creation | 23,477,512 |
| Uncached input | 800,280 |
| Output | 7,633,024 |

Models, from the run-start lines: 208 runs on `claude-opus-4-8`, 7 on `claude-fable-5` (a trial,
reverted on 2026-07-02 after it hit the subscription session limit), and 1 on `claude-sonnet-4-6`.
The runs used a claude.ai subscription, so no dollar cost is recorded.

Other counts: 77 numbered experiment write-ups (`docs/tests/0001` to `0077`), and 13 audit entries
([audit_log.md](audit_log.md)).
