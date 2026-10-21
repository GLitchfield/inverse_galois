# 0001 — Verification loop + authoritative target/coverage map

**Family:** infra / baseline · **Date:** 2026-06-24 · **Status:** loop stood up; target map established.

## Question

Stand up the verification loop and establish the authoritative target index + current coverage
(Phase-0 Track 2): which `(t,r)` signatures exist, which are already taken, and the discriminant to
beat for each.

## Setup

- **CAS:** system PARI/GP 2.15.4 (`gp`) + GAP (`transgrp`, degree-24 library), shelled out from the uv
  env (`src/igp/gp.py`, `src/igp/gap.py`).
- **Local pre-filter:** `src/igp/polys.py` + `verify.local_prefilter` (irreducibility, poly disc +
  square class → A_24?, real-root count `r`, Frobenius cycle-type fingerprint). 7 unit tests.
- **SAIR API client:** `src/igp/sair.py` — `Authorization: Bearer` (key in `data/raw/`, gitignored);
  endpoints `/me`, `/competitions/igp24`, `/competitions/igp24/labels/progress` (cursor-paginated).
- **Scripts:** `q01_build_target_index.py` (groups, from GAP), `q02_pull_signature_index.py`
  (signatures + coverage, from the API).

## Results

- **Groups (GAP):** `data/targets/transitive_groups_deg24.csv`, 25,000 rows with order / solvable /
  primitive / transitivity / in-A_24. **24,193 solvable, 807 non-solvable, 5 primitive** — independent
  exact match to the survey. (Also: 15,067 in A_24.)
- **Signatures (API):** `data/targets/signatures_deg24.csv`, **165,836 achievable `(t,r)` rows** —
  exact match to the survey/backend total (sum of per-group `allowedR`).
- **Live coverage (2026-06-24 snapshot):** **47,727 signatures discovered across 13,459 of the 25,000
  groups** → **~118,109 signatures still open**. Every signature carries the current
  `minimumDiscAbs` (the discriminant to beat) and `teamCount`.
- **`nfdisc` live:** `verify.pari_nfdisc` returns the official scoring (field) discriminant via `gp`.

## Learnings

- **Submission is an API POST**, not a file upload: `POST /competitions/igp24/submissions` with
  `{"polynomials": [<string>, …]}`, **≤ 100 polynomials, ≤ 100,000 bytes** (req ≤ 131,072). The
  earlier "submission.txt, 25 comma-separated coeffs/line" was a research guess — **corrected**. The
  exact **polynomial-string grammar** is still open (in the `docs/reference/submission-spec` doc;
  resolve before first submit).
- **Authoritative degree-24 Galois ID is only available via submission** — igp24 has no playground
  (`capabilities.playground = false`), and PARI `polgalois` stops at degree 11. So pre-submission we
  rely on **construction-guaranteed groups** (M2) + the local **cycle-type fingerprint**; the official
  Magma label comes back from the submission result. `verify.magma_verify` stays a stub accordingly.
- **The frozen 286/622 LMFDB baseline vs. live 47,727/13,459:** the `/labels/progress` numbers are the
  *live* competitor coverage (already far past the baseline). The actionable target is the **~118,109
  open signatures** + beating `minimumDiscAbs` on taken ones.
- The signature CSV mixes a **static** part (`t, r` ∈ allowedR — fixed by the math) and a **live** part
  (`discovered`, `min_disc_abs`); it's a dated snapshot, refresh by re-running `q02`.

## Reproduce

```
uv run python scripts/q01_build_target_index.py      # groups (GAP)
uv run python scripts/q02_pull_signature_index.py    # signatures + coverage (SAIR API; needs key)
```

## Empirical update (2026-06-24) — "discovered" is participant-only, not "open"

A first verified submission (C_24 / 24T1) showed the verifier returns `inBaseline` + `baselineDiscAbs`,
and that **`discovered=false` in `/labels/progress` means only "no participant has it"** — the feed does
**not** expose LMFDB-baseline membership. So the "~118,109 open" above = signatures with no *participant*
yet; it **includes the ~622 baseline pairs** (which need beating `D_base`, worth 0.5, not 1.0). Genuine
1.0-point targets = **non-baseline AND non-discovered** (≈ 117k). Retargeting needs the frozen
`lmfdb_baseline.csv`. (24T1 itself is a baseline group — our submission scored 0.)
