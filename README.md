# inverse_galois: an IGP24 entry (degree-24 inverse Galois problem)

The SAIR Foundation's IGP24 competition asked for irreducible monic integer polynomials of degree 24
whose Galois groups realize the transitive groups `24T1` to `24T25000`. Each group is scored
separately for each signature `(t, r)`, where `r` is the number of real roots. There are 165,836
valid pairs. A pair's score is `2^(1-k) * log(D0)/log(D)`, where `k` is the number of teams credited
with it, `D0` is the smallest field discriminant submitted by any team and `D` is ours. Pairs already
in the frozen LMFDB baseline (286 groups, 622 pairs) score only if the exact `nfdisc` beats the
baseline's. SAIR verified every submission with Magma. This repository holds the search pipeline,
the experiment write-ups, and the record of the autonomous agents that built and ran it.

## Status

- **Paused on 2026-07-14.** I shut down the search daemon and the agent loops to work on another
  project. The entry worked on the competition from 2026-06-24 to 2026-07-14 and submitted nothing
  after that. It finished **28th of about 200** at the Stage-1 deadline (2026-08-15).
- **The polynomial data is not published**: no coefficients, and no per-group or per-pair results.
  The pipeline writes them locally to the gitignored `data/targets/realized.csv` and `submissions/`.
  Only aggregate numbers are published.

## Results

Details and the source of each number are in [docs/results.md](docs/results.md).

| | LMFDB baseline | This project at the last snapshot (2026-07-14) |
|---|---:|---:|
| Groups realized | 286 | **7,956** |
| Scoreable pairs | 622 | **22,708** by local flags (25,296 credited on the official leaderboard) |
| Distinct verified polynomials | | **1,713,813** (each returned by SAIR's verifier with an official `24Tt` label) |

- **Score history.** Best rank: **12**, first reached on 2026-07-04 at 855.1 points. Peak official
  score: **1,091.1** at rank 14 on 2026-07-05 03:08 UTC. Last reading: **597.7, rank 19**
  (2026-07-14 13:23 UTC; the last coverage snapshot at 13:09 read 598.3).
- **Why the score fell while coverage kept growing.** From 2026-07-05, other teams realized many of
  the same pairs, which raised `k`, and submitted smaller discriminants, which lowered `D0`. By
  2026-07-14 a rival held a smaller discriminant on 97% of our scoreable pairs. The pipeline was
  strong at breadth and weak at discriminant minimization. A late attempt to close that gap was
  refuted by SAIR's labels; see
  [docs/agent-failures.md](docs/agent-failures.md) section 5.
- **Where the coverage came from.** `C2` kernels over degree-12 base fields (`gen12`, `gen12treal`,
  `sigfill`, `mb2`) account for most scoreable pairs. Per-producer counts are in
  [docs/results.md](docs/results.md#where-the-coverage-came-from).
- **Experiments.** 77 numbered write-ups, positive and negative, in [docs/tests/](docs/tests/),
  indexed in [docs/research_log.md](docs/research_log.md).

## How it works

**Targets.** `data/targets/` holds the 25,000-group index (built with GAP,
`scripts/q01_build_target_index.py`), the minimal block size of every group
(`block_structure_deg24.csv`, test 0040), and the official valid pairs and baseline copied from the
competition package (`scripts/fetch_competition_package.py`). Every group except five is
imprimitive, so almost everything is built as a tower over a smaller field.

**Constructions** (in `src/igp/gp.py`, which drives PARI/GP; group predictions in `src/igp/gap.py`):

- `C2` kernels: `K = K0(sqrt(alpha))` over a degree-12 base `K0`, where `alpha` is built from
  generators of primes above a completely split prime `q`. The pattern of `alpha`'s valuations sets
  the block kernel, and its signs at the real places set `r`
  ([tests 0005](docs/tests/0005-ws4-c2-kernel-poc.md) to
  [0015](docs/tests/0015-general-base-big-tops.md),
  [0036](docs/tests/0036-multiprime-sweep.md), [0062](docs/tests/0062-gen12-totpos-r24.md)).
- Larger kernels: `V4` biquadratic (6x4), cubic and quartic Kummer and radical kernels (8x3, 6x4),
  and cyclic `C_n` ray-class-field kernels ([test 0065](docs/tests/0065-abelian-kernel-producer.md)).
- Compositions `f(g(x))` and composita for wreath and product shapes, quadratic "orbit-sign" lifts,
  resolvent constructions for octic-over-cubic groups (tests 0044 to 0060), complement-cocycle
  twists for specific minimal-block-2 groups (tests 0068 to 0077), and published families for named
  groups (`M24`, `M12.2`, `PGL(2,23)`).

**Pipeline.**

```
producers (scripts/search_ctl.py, 26 run by the refill tick)
   -> SQLite work queue (src/igp/searchstore.py)
   -> daemon (scripts/searchd.py): build in a 10-thread gp pool, drop provable S24s, POST to SAIR
   -> SAIR verifier (Magma label + r, PARI nfdisc)
   -> collect results (src/igp/engine.py) -> data/targets/realized.csv (local, unpublished)
```

- **S24 filter** (test 0028). A Frobenius cycle of prime length 13, 17 or 19 forces a primitive,
  non-Mathieu group, so the group is `A24` or `S24`. If the discriminant is not a square it is
  `S24`, which is worth almost nothing, and the daemon skips it. This never discards a valuable
  group.
- **Ranking** (`src/igp/rank.py`, test 0025). Queue priority = a UCB1 bandit weight per producer,
  rewarded by scoreable and sole pairs, multiplied by `1 +` a gradient-boosted surrogate's
  `P(scoreable)` for the row.
- **Local gates** before spending verifier budget: degree and irreducibility, `polsturm` for `r`, a
  Frobenius cycle-type density fingerprint matched against GAP distributions, and a check that the
  target is still open on the live leaderboard.
- **Operations.** systemd user services run the daemon, a refill tick, a fast feed, an hourly
  watchdog (`scripts/hourly_watch.py`), invariant checks (`scripts/check_invariants.py`) and a
  read-only dashboard (`scripts/dashboard/`). The runbook is [docs/harness_notes.md](docs/harness_notes.md).

## Autonomous agents

The code, the experiments and most of the notes were written by Claude Code agents that I directed.
An interactive session ran under my supervision. Three headless loops ran on systemd user timers through
`scripts/run_headless_agent.sh`:

| Loop | Schedule | Job |
|---|---|---|
| research | every 2 h | one research dive on the top topic of a self-refilling research agenda |
| build | every 3 h (from 2026-07-07) | build the top ready item from a build backlog, gate it locally, pilot it, enqueue it |
| audit | daily 08:17 | self-audit: score trend, resources used versus available, invariants, an adversarial re-check of the last day's claims |

Each run was a non-interactive `claude -p` call with permission prompts turned off, so the loops
could run unattended. Opus ran 208 of the 216 runs. The prompts are in
`scripts/headless_prompts/`, and the interactive playbooks in `.claude/skills/`. OpenAI Codex acted
as an outside reviewer and kept `AGENTS.md`. Outside reviews are in
[docs/project_review_2026-06-28.md](docs/project_review_2026-06-28.md) and
[docs/project_review_2026-07-11.md](docs/project_review_2026-07-11.md); the agent's own review is
[docs/project_review_2026-06-30.md](docs/project_review_2026-06-30.md).

**Run ledger** (from the loop logs): 216 headless runs, 152 research, 51 build and 13 audit, from
2026-07-01 to 2026-07-14. The 209 runs that logged usage used 580.8M tokens, of which 548.9M were
cache reads and 7.6M were output.

**Failures and controls.** I caught the agents, and the agents caught each other:

- blaming SAIR's service for hours when our own client was at fault;
- declaring a ceiling three times on a search space they had barely sampled;
- overstating a count about 20x;
- relaying a "greenlit" target that landed on a different group;
- building and optimizing a producer before testing its signal against the official verifier;
- announcing next steps instead of doing them;
- stating unproven claims as fact.

[docs/agent-failures.md](docs/agent-failures.md) gives the dates, the controls added (an automated
adversarial counter-check in the daily audit, an evidence ladder with pilot labels required before
scaling, resource-denominator audits, invariant tripwires) and the original records. The 13 audit
entries are reproduced in [docs/audit_log.md](docs/audit_log.md). The rest of the agent journal
(about 140 research-dive entries) and the agenda and backlog files are not published.

## Layout

```
src/igp/            library: PARI/GP + GAP drivers, SAIR client, queue, ranking, coverage, LMFDB mirror client
scripts/            producers and daemon (search_ctl.py, searchd.py), per-experiment builders, ops + installers
scripts/headless_prompts/, .claude/skills/   agent prompts and playbooks
scripts/oscar/      Julia/OSCAR verifier spike (test 0026) and Hecke.fields driver (test 0053)
tests/              pytest suite (46 tests)
data/targets/       group index, block structure, official valid pairs + baseline, GAP screens
docs/               results, audit log, agent failures, reviews, commentary, rules, survey, bibliography
docs/tests/         numbered experiment write-ups 0001..0077 (index: docs/research_log.md)
CLAUDE.md, AGENTS.md  agent instruction files as they stood (historical; see their banners)
```

## Reproducing

```bash
uv sync                                  # Python 3.12 deps into .venv
.venv/bin/python -m pytest -q            # 46 tests
```

System dependencies, installed outside `uv`: **PARI/GP 2.15.4** and **GAP 4.12.1** with the
`transgrp` library (the Ubuntu packages `pari-gp` and `gap`). OSCAR experiments used Julia 1.12 with
OSCAR. Some producers read base fields from the LMFDB's public read-only Postgres mirror
(`src/igp/lmfdb.py`).

Build a degree-24 field locally, with no network access. This is a `C2` kernel over `Q(zeta_13)`
with split prime 53, plus GAP's prediction of its group:

```bash
.venv/bin/python -c "from igp import gp, gap; w=[1,1]+[0]*10; f=gp.cyclotomic_c2(w,13,53); \
print(len(f)-1, gp.real_roots(f), gap.kernel_label(w))"    # prints: 24 0 24T12727
```

Running the full service (`scripts/install_systemd_services.sh`, then `scripts/search_ctl.py tick`
and `scripts/searchd.py`) needs a SAIR API key, in `data/raw/sair_api_key.txt` or `SAIR_API_KEY`,
and the SAIR verifier, which may no longer accept IGP24 submissions. `scripts/q02_pull_signature_index.py`
and `search_ctl.py refresh` pull the live leaderboard state that several producers need. The agent
loops (`scripts/install_headless_loops.sh`) read and write the unpublished journal, agenda and
backlog files, so they would need new ones before they could run. The loops run `claude` with
`--dangerously-skip-permissions` and no sandbox, so run them only in an isolated account or
container. Note that
`scripts/fetch_competition_package.py` overwrites `src/igp/mixed_disc.gp` with the package's older
version.

## License

MIT; see [LICENSE](LICENSE). Files copied or derived from the IGP24 competition package
(Apache-2.0) and other third-party material are listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

This repository was published with a fresh history on 2026-10-20; commit IDs cited in the notes refer to the private development history.
