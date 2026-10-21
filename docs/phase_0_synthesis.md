# Phase 0 synthesis — scope, survey, and (over-delivered) the search engine

**Closed 2026-06-28.** Phase 0's charter was to scope the problem, survey constructive techniques,
stand up the verification loop, and reproduce the baseline — *without* committing to a search
strategy. It did all that and then ran well past it: the chosen attack got built and run, so we exit
Phase 0 already executing. Phase 1: `docs/phase_1_plan.md`.

## Headline numbers (2026-06-28)

- **319 distinct groups** realized (baseline 286), **263 distinct scoreable signatures** (258 beyond
  the 622-pair LMFDB baseline), **5 currently sole**. *Distinct `(t,r)` — not per-poly rows.*
- Build documented in tests **0001–0030**; coverage source of truth `data/targets/realized.csv`;
  scoreboard `scripts/analyze_coverage.py`.

## What Phase 0 delivered

- **Survey + chosen attack:** imprimitive/wreath/tower constructions are the coverage workhorse
  (only 5 of 25,000 groups are primitive); disc-min + signature-fill as post-processors; the 807
  non-solvable groups are the hard residual. (`docs/landscape_survey.md`, `docs/design/arsenal.md`.)
- **Verification + targets:** PARI/GP + GAP shelled out; SAIR public API wired; the 25,000-group /
  165,836-signature target index.
- **The 24/7 search engine (beyond original scope):** producers → queue → daemon (S₂₄ filter) →
  SAIR verify → `realized.csv`, with a bandit + scoreable/disc surrogates, a read-only dashboard, and
  an OSCAR local-verifier spike. Runbook: `docs/harness_notes.md`.

## Key learnings & surprises

- **The binding constraint is 100 submissions/day/team, not the verifier.** Magma verifies fast; we
  *crashed into* a 429 `TEAM_DAILY_LIMIT` (test 0030). So the game is **value per POST**, and the
  earlier "verifier unlimited, flood hard" read was wrong.
- **`2^(1-k)` dominates the score (confirmed).** A first/undiscovered pair ≈ 1.0; a shared pair ≤ 0.5.
  So **breadth toward undiscovered (`teamCount==0`) pairs ≫ disc-min** on shared ones — disc-min is a
  secondary post-processor. (I over-weighted disc-min mid-Phase-0; corrected.)
- **Coverage = distinct `(t,r)`, not poly rows** (test 0029) — the dashboard had been ~6× overcounting.
- **The race is live and shrinking:** undiscovered pairs fell ~117k→~101k in four days (~4k/day claimed
  across teams); our sole count eroded ~15→5. Speed matters.
- **Most sparse degree-24 polys are S₂₄** (negligible) — a provably-safe cycle-type filter (test 0028)
  is essential so the daily POST budget isn't wasted.

## Deferred / didn't pan out

- **OSCAR local Galois verifier** — correct but too slow/heavy at degree 24 (test 0026); kept as a
  cross-check, not wired in.
- **p-adic resolvent identifier** (Fieker–Klüners core) and **robust CFT** (`bnrclassfield` too heavy)
  — real but low-priority sub-projects.
- **A₂₄** (square-disc family; completes the primitive 5) — needs a parametric construction; deferred.
- Per-group reachable-`r` is the API's authoritative `allowedR` (used by `sigfill`); per-pair baseline
  membership comes per-poly from the submission `inBaseline` field (recorded in `realized.csv`). [Both
  resolved 2026-06-28; the only gap is a *pre-submission* baseline CSV for target filtering.]
