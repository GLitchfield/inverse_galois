# 0032 — Integrate the official IGP24 public package (baseline, validR, tools)

**Family:** infra / scoring · **Date:** 2026-06-28 · **Source:** `SAIRcompetition/IGP24-public`
(released by the organizers) · **Code:** `scripts/fetch_competition_package.py`, `src/igp/baseline.py`,
`scripts/analyze_coverage.py`, `src/igp/rank.py`, `scripts/build_submission.py`, `scripts/dashboard/`

## Question

The organizers published the canonical competition package. Vendor it and wire it through the
pipeline — it gives us the three things we'd been missing or guessing: baseline membership + `D_base`,
the authoritative `validR`, and the official scoring definition.

## Method

`fetch_competition_package.py` clones the repo to `data/raw/` and derives committed indexes:
`baseline_signatures.csv` (t,r,`D_base`), `valid_pairs.csv` (165,836 validR), `nonsolvable_t.txt`
(807), + vendors the official `mixed_disc.gp`. `igp/baseline.py` exposes `is_baseline` / `d_base` /
`beats_baseline` / `valid_pairs` / `nonsolvable_t`, wired into the scoreboard, ranker, submission
builder, and dashboard.

## Result

- **`competition.yaml` confirms our model exactly:** scoring `2^(1-k)·log(D0)/log(D)`; non-baseline
  pairs use exact `nfdisc` (60s) → `mixed_disc` (bound 100000) fallback; baseline pairs unlock only on
  exact `nfdisc < D_base`; 25-coeff ascending monic submissions. (Validates the earlier
  reverse-engineering; resolves the `validR` and baseline-membership gaps.)
- **Honest scoreboard** (`analyze_coverage`): 263 scoreable sigs = **258 non-baseline** (shared, each
  ≤0.5 by `2^(1-k)`) **+ 5 baseline-unlocks** (0.5). **TRUE 1.0 held (non-baseline, teamCount==0) = 0**
  — the "5 sole" we'd been counting are baseline pairs we have NOT beaten, worth **0**.
- **Opportunity quantified:** **99,542 open 1.0 targets** (valid, non-baseline, teamCount==0, not
  ours), of which **299 are sig-fill-reachable** — a group we already realize, missing an undiscovered
  valid `r`. These 299 are deterministic first-claim 1.0s.
- Ranker now rewards true 1.0s; builder caps baseline at 0.5 + flags them; dashboard shows "1.0 held =
  0 / open sig-fill = 299". 37 tests green.

## Learnings

- **We hold zero 1.0s.** Our score so far is shared non-baseline pairs (≤0.5 each) + 5 baseline
  unlocks — the "sole realizer" headline was an artifact of conflating `teamCount==0` with non-baseline.
  Sobering, but now measured correctly.
- **The 299 sig-fill 1.0s are the highest-value immediate target** — known group, missing an
  undiscovered `r`, worth ~1.0. Sig-fill (totally-real bases + signature-controlled radicals) + the
  baseline-aware ranker now point straight at them; the next push is to convert them.
- **The official tools are a latent asset:** `mixed_disc.gp` lets us compute the scoring disc the
  evaluator's way; `tools/magma/t24.m` is the verifier (needs Magma, which we lack — so SAIR submission
  stays authoritative).
- Reconciles all the stale baseline/`validR` doc claims against the canonical source.
