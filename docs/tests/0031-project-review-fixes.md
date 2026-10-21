# 0031 — Project-review fixes: value per POST, distinct-sig ranking, data hygiene, sig-fill

**Family:** infra / review · **Date:** 2026-06-28 · **Input:** `docs/project_review_2026-06-28.md`
**Code:** `scripts/searchd.py`, `src/igp/{rank,db,engine,lmfdb}.py`, `scripts/search_ctl.py`,
`scripts/{backfill_disc,build_submission}.py`

## Question

An independent audit (`project_review_2026-06-28.md`) found operational + metric issues, several of
which the builder had missed or dismissed. Fix them, in priority order, and capture the lessons.

## What was fixed

- **P0 POST packing** (`searchd.py`). The binding cap is 100 POSTs/day, but the daemon submitted the
  post-filter remainder (~25 polys/POST). Now it accumulates survivors up to `submit_target=100`
  across claims before one POST (under a 95KB guard) — ~4× polys/day under the same cap. *(I had
  dismissed this as "marginal" the prior turn; the review was right.)*
- **P0 Ranker → distinct `(t,r)` value** (`rank.py`). `producer_stats` now scores from `realized.csv`
  by the ACTUAL `(t,r)`: reward = (distinct scoreable sigs + 2·sole) / builds. Fixes the rows-not-sigs
  over-credit (quad: 2126 rows / 54 sigs → weight 0.07, bottom; g6x4/discmin → top) and the sole check
  that used `(t,0)` regardless of `r`. Historical sources collapse to one `manual` arm.
- **P0 Data hygiene** (`db.py`, `engine.py`, `backfill_disc.py`). `record_realized` now MERGES (later
  non-blank fields fill blanks) — the `setdefault` was why ~97 scoreable rows had blank `field_disc`;
  backfilled all 97 via local `nfdisc`. Added `disc_source`; `collect` records `failedPolynomials` +
  mixed-disc; `sync_verified` marks failed queue rows.
- **Daemon survives the 100/day cap** — wraps submit, requeues, idles on the 429 (no crash).
- **P1 Signature fill** (`produce_sigfill`, `lmfdb.fields(max_r2=…)`). Totally-real deg-12 bases +
  radicals that are EXPRESSIONS in the base generator give INTERMEDIATE `r` (verified one base →
  r ∈ {0,6,10,12,20,24}); fills the under-covered region (241/319 groups had a single `r`).
- **P1 Submission builder** (`build_submission.py`). Best poly per scoreable `(t,r)`, ranked by
  `2^(1-k)·log(D0)/log(D)`, ≤100-poly/≤100KB files + manifest. First build: 263 sigs → 3 files.

## Result

34 tests green (new: ranker distinct-sig reward, `producer_of_source`, db merge-fills-blanks). Live
ranker now ranks g6x4/discmin top and the duplicated quad/tri flood bottom. 0 blank-disc scoreable
rows. Daemon packs to 100/POST going forward. New quality rules in CLAUDE.md.

## Learnings

- **Adversarial review pays.** Three of the highest-value fixes (packing, rows-vs-sigs ranking, blank
  discs) came from one independent audit — institutionalised as a quality rule (commission review
  periodically).
- **The confirmed `2^(1-k)` reorders levers: breadth ≫ disc-min.** A first/undiscovered pair ≈ 1.0 vs
  ≤0.5 for disc-min on a shared pair — so packing + distinct-sig ranking + sig-fill (toward
  `teamCount==0`) are the Phase-1 priority; disc-min is a secondary post-processor.
- **Metric discipline:** score distinct `(t,r)`, never rows; refresh live state before reasoning;
  verify "marginal" with data; fail safe on external limits; merge data writes. (CLAUDE.md → Quality
  rules.)
