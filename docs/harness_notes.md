# Harness notes — SAIR verification + submission (IGP24)

> Operational notes on the SAIR API, the local PARI/GP + GAP toolchain, and the search service,
> written while they were being stood up (2026-06-24 to 2026-06-28). Behavior that differs from
> `docs/competition_rules.md` is noted where observed. The runners were shut down on 2026-07-14.

## Known so far (see competition_rules.md for confirmed facts)

- Verifier: **Magma** checks irreducible + degree-24 + `24Tt` label + `r`; **PARI/GP `nfdisc`** sets the
  scoring (field) discriminant. SAIR offers a limited free MAGMA API.
- Submission: single `submission.txt`, raw ≤ 100,000 bytes, 25 comma-separated int coeffs/line.
- Score: per `(t,r)`, small discriminant × rarity; trivial duplicates removed.

## Toolchain (2026-06-24) — installed & working

- **PARI/GP 2.15.4** (`/usr/bin/gp`) and **GAP** (`/usr/bin/gap`, with the `transgrp` degree-24
  library) are installed system-wide (`sudo apt-get install pari-gp gap`). We **shell out** to the
  `gp`/`gap` binaries from the uv-managed Python (`src/igp/gp.py`, `src/igp/gap.py`) — one Python env,
  CAS as external CLI tools. `libpari-dev` did **not** land, so `cypari2`-in-venv is unavailable; not
  needed (shelling out covers `nfdisc`, `polredbest`, …). `micromamba` is bootstrapped at
  `~/bin/micromamba` as an escape hatch (e.g. for conda-forge `cypari2`/`sagemath`) if ever needed.
- **Local capabilities now live:** `gp.nfdisc` (the official scoring discriminant), `gp.poldisc`,
  `gp.polredbest`; `gap.num_transitive_groups`, `gap.transitive_group_info`,
  `gap.all_transitive_group_info` (the full 25,000-group catalogue). `verify.pari_nfdisc` is wired to
  `gp`. Still external: the **authoritative degree-24 Galois label** (PARI `polgalois` only ≤ deg 11;
  needs **Magma** via the SAIR API — `verify.magma_verify` remains a stub) and the **competition
  baseline / `validR`** (see below).
- **LMFDB API is reCAPTCHA-walled** to automated access (even with a browser UA) — so the baseline
  can't be pulled via the LMFDB API. We source the **target index from GAP instead** (done:
  `data/targets/transitive_groups_deg24.csv`, 25,000 rows, built by `scripts/q01_build_target_index.py`;
  counts 24,193 solvable / 807 non-solvable / 5 primitive independently match the survey). The frozen
  **286/622 baseline + per-group `validR`** still need the **SAIR `/api`** (pending) or LMFDB bulk files.

## What runs now without a CAS

`src/igp/polys.py` + `src/igp/verify.py:local_prefilter` (pure sympy): irreducibility, polynomial
discriminant + square class (Gal ≤ A_24?), real-root count `r`, and the Frobenius cycle-type
fingerprint (Dedekind/Chebotarev). The cheap local pre-filter (arsenal M7) that narrows a candidate
before the authoritative Magma call.

## SAIR public API (verified 2026-06-24) — `src/igp/sair.py`

Base `https://api.sair.foundation/api/public/v1`; auth `Authorization: Bearer <key>` (key in
`data/raw/sair_api_key.txt`, gitignored; the key needs competition.read + write
scopes). Responses are `{"ok":bool,"data":…}`; errors `{"ok":false,"error":{code,message}}`.

- `GET /me` — scopes/owner.
- `GET /competitions/igp24` — `submissionSpec` (kind `igp24-polynomial`; `{polynomials:[str]}`, 1–100,
  ≤100,000 bytes, req ≤131,072; optional `meta.description`), window `2026-06-15 → 2026-08-15T12:00Z`.
- `GET /competitions/igp24/labels/progress?limit=500[&cursor=]` — cursor pages (base64 `[offset]`); per
  group: `t,label,allowedR,teamCount,minimumDiscAbs,discoveredSignatures,remainingSignatures,
  signatures[{r,teamCount,minimumDiscAbs,discovered}]`. Pulled in full by `scripts/q02_*`.
  **`discovered`/`minimumDiscAbs` here are PARTICIPANT-only — this feed does NOT expose LMFDB-baseline
  membership**, but `allowedR` per group IS authoritative (the reachable `r` list, used by `sigfill`).
  **Baseline membership is learned per-poly from the submission response** (`inBaseline`, recorded in
  `realized.csv`), so we don't need a separate baseline CSV for membership — only to *pre-filter*
  targets before submitting (a 1.0 target is non-baseline AND `teamCount==0`). The frozen
  `lmfdb_baseline.csv` (622 pairs + `D_base`) is not in the tree; obtain it only if pre-filtering pays.
- `POST /competitions/igp24/submissions` (write; team is now **enrolled**) — body
  `{"payload":{"polynomials":[…]},"meta":{"description":…}}`. Each `polynomials[*]` must be a **bare**
  25-integer ascending string — a trailing `#` comment is rejected ("all coefficients must be decimal
  integers"; that's a `submission.txt`-file affordance only). Verification is **async**: returns
  `queuedPolynomials`, then poll `GET …/submissions/me` for `verifiedPolynomials[{label,t,r,inBaseline,
  baselineDiscAbs,fieldDiscAbs,discSource,scoringStatus,scoreable,scoringReason}]` / `failedPolynomials`.
  Strict body schema: unknown top-level keys → 400 `MALFORMED_BODY`; missing `polynomials` → 422; the
  authoritative 24Tt label only comes from here (no igp24 playground) — `verify.magma_verify` stays a stub.
- Docs (React SPA, content not curl-able): `https://docs.sair.foundation/docs` — `authentication`,
  `reference/submission-spec`, `rate-limiting`, `endpoints/*`. (Poly format now known — see above.)

## Search service — operational runbook (2026-06-28)

The 24/7 search is a producer→queue→daemon→verify→record pipeline, run as **resilient systemd USER
services** (`scripts/install_systemd_services.sh`) so it survives a terminal close / WSL teardown
(the old failure mode where closing the terminal SIGHUP'd the daemon):

- `igp24-searchd.service` — the daemon (`Restart=on-failure`; clean `stop` exit 0 ⇒ no restart).
- `igp24-dashboard.service` — the dashboard on :5057 (`Restart=on-failure`).
- `igp24-tick.timer` — runs `search_ctl tick` every 30 min (producers + rank + ensure-daemon).
- `loginctl enable-linger` keeps them running with no login session and **auto-starts them on WSL
  boot**. Manage with `systemctl --user {status,restart,stop} igp24-searchd` (logs:
  `journalctl --user -u igp24-searchd`). `search_ctl pause/resume/stop` still work (via the kv
  control row); the systemd unit owns the *process*, the kv owns the *behaviour*.

**Caveat (Windows side, can't set from inside WSL):** a full Windows reboot leaves WSL stopped until
something invokes it; to auto-start the whole stack, add a Windows Task Scheduler task running
`wsl.exe -d <distro> -- true` (or open any WSL terminal) at logon — linger does the rest. State is on
disk regardless (`realized.csv`, `search.db`), so nothing is ever lost.

**Pipeline.** Producers (`scripts/search_ctl.py`) enqueue construction *targets* into a SQLite work
queue (`data/processed/search.db`, gitignored). The daemon (`scripts/searchd.py`, one cycle / 60s)
collects verified results, then claims a batch by `priority`, builds each (PARI/GP), drops forced-S₂₄
candidates (`verify.likely_negligible_s24`), and submits the rest to the SAIR API. Verified polys land
in `data/targets/realized.csv` (committed — the coverage source of truth) via `igp/engine.py`. The
ranker (`igp/rank.py`) sets `priority` = producer bandit (UCB, sole-share) + per-row scoreable
surrogate + disc surrogate; computed in the tick, not the daemon. Queue-row lifecycle:
`queued → building → submitted → verified | failed | dup | filtered`.

**Manage it** (`uv run python scripts/search_ctl.py <cmd>`):
- `tick` — the maintenance cycle: ensure daemon alive (relaunch if dead), refresh leaderboard if
  >12h stale, run all producers, recompute ranking, print status. (Run periodically; user-fired —
  there is no durable cron in this environment.)
- `status` / `rank` — print queue counts + daemon state / recompute+show bandit weights.
- `pause` / `resume` / `stop` — daemon control (via the kv `control` row).
- `set <key> <value>` — set a kv knob (below). `produce-<name>` — run one producer manually.
- Coverage truth: `uv run python scripts/analyze_coverage.py` (distinct sigs + disc headroom — NOT
  the per-poly row counts).

**Producers** (all run each tick; saturated ones enqueue 0; the two cursor families are inexhaustible):
`produce` (exact-Galois), `spec`, `compositum` (deg-12×C₂), `size4`/`size4_general`/`lmfdb` (6×4
biquadratic over Galois / diverse / LMFDB bases), `trinomials`, `discmin` (C₂ kernels over LMFDB
minimal deg-12 bases), `discmin2` (minimal-radical `F(√α)` disc-min), `size3` (8×3 Kummer over
ζ₁₅/₂₄/₃₀), `size3_compositum` (deg-8×C₃, diverse tops), `pentanomials` + `quadrinomials` (the
inexhaustible cursor fillers; quad self-regulates the buffer, runs last).

**kv knobs** (in `search.db`; set with `search_ctl set`): `max_posts_day` (**98 — under the hard SAIR
100 POSTs/day/team cap**; the API returns `429 TEAM_DAILY_LIMIT` past 100 and the daemon idles until
the next UTC day), `build_batch` (50 polys/POST; ≤100 allowed), `max_pending` (300, verifier
backpressure), `interval` (60s), `quad_target` (8000 buffer depth), `quad_max_add` (4000/run),
`s24_filter` (unset ⇒ defaults ON), `quad_cursor`/`pent_cursor` (generator position), plus runtime
`control`/`status`/`posts`.

**Dashboard** (`scripts/dashboard/`, read-only): `uv run python scripts/dashboard/app.py` →
http://localhost:5057. Coverage trajectory, queue pipeline, throughput, producer weights, sole sigs,
behind-on-disc.

**Local Galois ID** (`scripts/oscar/`, OSCAR/Julia): correct but slow/heavy (test 0026) — kept as an
occasional cross-check, **not** in the daemon loop.
