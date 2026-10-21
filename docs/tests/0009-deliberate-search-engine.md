# 0009 — Deliberate search loop (engine A + routing), end-to-end

**Family:** infra / search · **Date:** 2026-06-26 · **Modules:** `igp/{db,engine}.py`,
`scripts/search.py`

## Question

Does the full deliberate loop run end-to-end — route a target to a recipe, construct, submit, collect,
record — robustly? And what does the currently-routable slice yield?

## Method

- **Engine** (`igp/engine.py` + `igp/db.py`): `submit` (dedup + log to pending) / `collect` (reconcile
  pending vs server, record verified polys with coeffs into cache + coverage DB; resumable).
- **Routing** (`scripts/search.py`, `C_12`-top `12×2` slice): the kernel is an ideal of
  `F_2[x]/(x^12-1) = (x+1)^4 (x^2+x+1)^4` ⇒ 25 ideals; enumerate `g=(x+1)^a(x^2+x+1)^b → w`, label each
  via `gap.kernel_label` (forward map) → `{label: w}`; intersect with the untouched-solvable frontier;
  construct matches via `gp.c2_split_construct` (the A→w→α solver) → engine.

## Result

- **Resumability works:** `collect()` drained a submission left queued on a prior run (3 verified polys
  recorded) — the persisted-pending design survives the verifier backlog.
- **Routing table:** **24 distinct `C_12`-top labels** reachable (the full family).
- **Routable untouched targets: 1 (`24T2`).** 23 of 24 are already participant-discovered ⇒ the
  easy-to-construct `C_12`-top slice is **saturated**.

## Learnings

- The deliberate search loop (route → construct → submit → collect, resumable) is **complete and
  runnable** — item A is functionally done.
- **The easy-to-construct slice is already covered** (everyone can build `C_12`-top groups), confirming
  test 0002: frontier value is in the **hard constructions**. ⇒ prioritize **item C** (non-abelian tops,
  size-`k` blocks) — groups others *also* can't easily build.
- The frontier snapshot (`signatures_deg24.csv`) is **stale** (predates recent discoveries); refresh
  (`q02`) before any serious routing run.
