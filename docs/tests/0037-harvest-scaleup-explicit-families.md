# 0037 — Harvest scale-up (gen12 + parallel daemon) and the explicit-family lesson

**Family:** search / strategy · **Date:** 2026-06-29 · **Code:** `scripts/search_ctl.py`
(`produce_general12`, `produce_m24`, multi-prime harvest), `scripts/searchd.py` (thread pool),
`src/igp/gp.py` (`split_primes`)

## Question

After the multi-prime sweep (test 0036, targeted 1.0s 19→41), how much further can candidate
generation be pushed — broadening harvest, reaching new group regions, and (research) the
non-solvable/primitive residual that towers can't touch?

## What was built + measured

- **Multi-prime across harvest producers** (spec/comp/lmfdb/g6x4): one prime → one `r` per base
  became k primes → many `r`. Mechanical 2–3× on enqueue.
- **`gen12`** — `general_c2` over diverse non-Galois deg-12 LMFDB bases (any class number), the full
  12Tj top range. Two runs (per_group 2→4) enqueued ~15k candidates from ~565 usable bases.
  **Distinct groups 390 → 457+ (climbing)**, scoreable sigs 447 → 524. This is BREADTH: the new
  groups land on shared/baseline pairs, so **TRUE 1.0 held stayed 41** (1.0s come from the targeted
  gate, not harvest).
- **Daemon parallelized** — `construct()` blocks on its own `gp` subprocess (stdin/stdout, thread-
  safe), so a `ThreadPoolExecutor` (10 workers; max-10-concurrent confirmed) overlaps the slow
  `bnfinit` tail. Daemon is **supply-bound, not verification-bound** (pending ~200 ≪ 300 cap; each
  1000-poly POST yields ~100 new rows, ~10% — harvest mostly re-hits held `(t,r)`).
- **`gp.split_primes`** (nfinit, not bnfinit) — fast completely-split-prime finder for large/h>1
  deg-12 bases.

## Research: the non-solvable/primitive residual

- **We realize ~0 of the hard non-solvable groups.** Towers need a completely-split prime (density
  `1/|H|`) — infeasible for primitive/large `|H|`. So primitive groups need **explicit Q(t)
  families**, not towers.
- **M24 — a documented MISS.** Found + transcribed + PARI-validated the Malle-Matzat M24/Q(t) family
  (arXiv 1204.1328): `F=(t-A0)²+(X²+1)B0²`, all specializations totally complex → (M24, r=0). Built
  `produce_m24`, submitted, **expecting a sole-realizer 1.0.** Wrong: **M24 (24T24680,0) has
  teamCount=11** (≈0.001 score) and we already held it (prior "mueller" rows). A famous group with a
  published family is CONTESTED — everyone realizes it the same way. Skipped the 121 queued
  specializations; new CLAUDE quality rule.
- Duds ruled out: LMFDB deg-24 mirror = 104 groups, ALL baseline (no new 1.0s); Malle's `pargal`
  table is mostly smaller-degree groups.

## Learnings

- **Harvest = breadth (groups headline); the targeted gate = 1.0s (score).** gen12 added 67+ groups
  but 0 new 1.0s; every 1.0 we hold came from tsig's predict-and-gate-to-`teamCount==0`. So the
  score lever is *extending the targeted gate to more obscure groups*, not maximizing harvest volume.
- **Famous ≠ open.** The teamCount==0 1.0s are OBSCURE groups (no published family → we're first).
  Named primitives are contested precisely because they're famous. Check teamCount + realized.csv
  before targeting any named group.
- **Supply-bound, so parallel construction + more candidates help** — but value-per-poly is what
  matters, and harvest's is low (~10% new rows). The thread pool overlaps the slow gen12 `bnfinit`
  tail; collect() (growing `my_submissions`) is now the cycle's serial cost.
