# 0021 — Search daemon: from one-off scripts to a 24/7 managed service

**Family:** infra / architecture · **Date:** 2026-06-27 · **Modules:** `igp/searchstore.py`,
`scripts/searchd.py`, `scripts/search_ctl.py`

## Question

The work had been a sequence of one-off scripts (q01…q22, campaign). Should the search instead
be **long-running processes I manage** — develop, feed, inspect, harvest — running 24/7?

## Method

A producer/consumer service:
- **`searchstore`** (SQLite): a work queue of construction *targets* (`kind` + JSON payload,
  status `queued→building→submitted→verified/failed/dup`) + a kv table for daemon
  status/config. Concurrency-safe (daemon writes while management reads).
- **`searchd`** (the daemon): each cycle `collect` verified results, then — unless paused / over
  the rate limit (`max_pending`, `max_posts_day`) / verifier backed up — `claim` a batch,
  `construct` (dispatch by `kind` over the whole toolkit), de-dup, `submit`. Resumable.
- **`search_ctl`** (management): `refresh` (leaderboard), `produce` (exact Galois targets),
  `produce-spec` (speculative non-Galois library), `status`, `harvest`, `pause/resume/stop`,
  `set` knobs.

Producers decide WHAT to build; the daemon drains the queue. Verified polynomials still land in
`realized.csv` via the engine.

## Result

**Daemon runs 24/7 and works**: steady cycles of *build 4 → submit → collect*, queue draining
(60→…), verified climbing, verifier keeping pace, all unattended. Two producer types exercised:
- **Exact (Galois)** `produce`: re-derives the campaign's targets — exhausted (the 6 sole
  realizers are already found; re-runs dedup to `dup`).
- **Speculative (non-Galois library)** `produce-spec` over radical bases (`x¹²−2`, `x¹²−x⁶−1`,
  `x¹²−2x⁶−1`): all verified results **contested** (0 sole) — radical bases land on *popular*
  groups, the same saturation we keep seeing.

## Learnings

- **The service model is right** — a coverage/optimization search is a long-running process, and
  the daemon makes it one: I add producers/features and harvest while it runs. The
  construct→submit→**Magma** flow also *sidesteps* the non-Galois alignment problem (Magma is the
  label oracle), so diverse non-Galois bases need no a-priori alignment.
- **Yield = producer quality.** The architecture is done; sole realizers now depend on feeding
  it **obscure** bases. The obvious families (cyclotomic, radicals, simple Galois) are saturated;
  the 10,426 untouched groups want degree-12 fields *others didn't try*. The next work is a
  **base library** of diverse/obscure degree-12 fields (h=1 + a findable split prime), plus the
  fuller kernel lattices over them — all just new producers feeding the same daemon.
