# AGENTS.md — inverse_galois (IGP24)

> **Historical snapshot (published 2026-10-20).** This is the instruction file read by the OpenAI Codex
> reviewer. It was last edited on 2026-06-29 and largely mirrors [CLAUDE.md](CLAUDE.md) as of that date,
> so its numbers, limits and "active" plan are stale. See [README.md](README.md) for the final state.
> Files it mentions that are not in this release include the phase plans, `docs/design/`,
> `docs/exploration_backlog.md`, `data/targets/realized.csv` and `submissions/`.

> SAIR Foundation **Inverse Galois Problem, degree 24 (IGP24)**: find irreducible integer
> polynomials of degree 24 realizing as many of the 25,000 transitive permutation groups
> `24T1..24T25000` (and their `(t, r)` real-root signatures) as possible, minimizing
> discriminant. This file is project state + operational conventions; keep it in sync with
> `README.md`. (`AGENTS.md`, if present, is maintained separately by a Codex reviewer — not by us.)

## Active phase / plan

**Phase 1 — execute the imprimitive/tower attack to maximize score — ACTIVE (2026-06-28,
user-confirmed).** Plan: `docs/phase_1_plan.md`. The chosen attack is built + running as the 24/7
search service (current-state below; tests 0021–0030). **Binding constraint: 100 submissions/day/team**
(429 cap, test 0030); the **confirmed `2^(1-k)·log(D0)/log(D)` scoring ⇒ breadth toward UNDISCOVERED
(`teamCount==0`) pairs (~1.0 each) is the dominant lever**, disc-min on shared pairs (≤0.5) secondary.
Real estate (2026-06-28): ~101k undiscovered / ~64k discovered pairs, competitors claiming ~4k/day.

**Phase 0 — scope & survey — CLOSED (2026-06-28; synthesis `docs/phase_0_synthesis.md`).** Plan:
`docs/phase_0_plan.md`.
Goal: lay the foundation without committing to a search strategy yet — (1) survey the landscape
of *constructive* inverse-Galois techniques and what actually realizes transitive degree-24
groups (resolvent/specialization families, class field theory for solvable groups, rigidity,
database mining), and (2) stand up the verification loop (local PARI/GP + the SAIR MAGMA API)
and reproduce the **LMFDB baseline (286 groups / 622 signatures already covered)**. Phase 0 ends
with a synthesis that picks the Phase-1 attack.

**Landscape survey round 1 DONE (2026-06-24, `docs/landscape_survey.md`).** Top-level strategy settled:
**imprimitive/wreath/tower constructions are the coverage workhorse** (only **5 of 25,000 groups are
primitive**; Hulpke builds the rest recursively from fields of degrees dividing 24), with
discriminant-minimization + signature-diversification as always-on post-processors; the **807
non-solvable groups (incl. the 5 primitive) are the hard residual** (some via explicit `Q(t)`-families,
e.g. Müller's `M_24`). **Verification is fast, not the bottleneck** — Magma's degree-independent
`GaloisGroup` IDs degree-24 groups "in seconds"; the *scoring* discriminant is PARI `nfdisc` (the field
disc). Arsenal catalogued in `docs/design/arsenal.md` (methods M1–M8 + Stage-1 sequencing).

**Verification loop + target map DONE (test 0001, 2026-06-24).** CAS installed (system PARI/GP 2.15.4 +
GAP, shelled out from `src/igp/{gp,gap}.py`); SAIR public API wired (`src/igp/sair.py`, Bearer key in
`data/raw/`). Authoritative target map in hand: 25,000 groups + **165,836 `(t,r)` signatures**
(`data/targets/`), live coverage **47,727 discovered / 13,459 groups → ~118,109 open**, each with a
`minimumDiscAbs` to beat. `nfdisc` (scoring disc) live; local cycle-type pre-filter live. Submission =
API POST `{polynomials:[str]}` (≤100, ≤100 KB). **Next concrete steps:** (1) the polynomial-string
grammar (`docs/reference/submission-spec`) → submission builder + first M2 construction → submit;
(2) survey **round 2** (per-method recipes + map the 807 hard groups). Authoritative Magma label only
returns from a scored submission (no igp24 playground).

No prior phases. Durable deliverables so far: survey + arsenal; the group + signature target indexes
(`data/targets/`); the gp/gap/SAIR clients + local pre-filter.

**Current state (2026-06-28).** The survey's chosen attack — imprimitive/wreath/tower constructions —
is **built and running as a 24/7 search service**, so we are effectively executing the Phase-1 attack
inside the Phase-0 container (a formal Phase-1 declaration may be warranted — deferred to user).
Pipeline: producers (`scripts/search_ctl.py`) enqueue targets → SQLite queue (`data/processed/search.db`)
→ daemon (`scripts/searchd.py`: builds via PARI/GP, applies a provably-safe S₂₄-skip filter, submits)
→ SAIR verify → `data/targets/realized.csv`; an `igp/rank.py` bandit + scoreable/disc surrogates set
queue priority. **~13 producers**, including inexhaustible cursor fillers (quadrinomials/pentanomials)
and minimal-radical disc-min (`discmin2`). **Operational runbook: `docs/harness_notes.md`** — note it's
**session-scoped** (daemon + read-only dashboard `scripts/dashboard/` die on session end; resume with
`search_ctl tick`). **Our coverage — distinct `(t,r)` is the scoring metric, NOT per-poly rows (test
0029): 319 distinct groups (> baseline 286), 263 distinct scoreable signatures (258 beyond baseline;
< the 622 baseline), 5 currently-sole signatures.** Disc-min headroom: ~173/202 covered sigs are beaten
on disc. Build documented in tests **0021–0030** (`docs/research_log.md`); live scoreboard:
`scripts/analyze_coverage.py`. Also: an OSCAR local-verifier spike (`scripts/oscar/`, test 0026 —
correct but too slow to wire in).

## Competition origin

Third SAIR Foundation competition, announced 2026-06-16 by **Terence Tao** (UCLA) with
**John Jones** (ASU), **Jen Paulhus**, **David Roe** (MIT), **Andrew Sutherland** (MIT), in
collaboration with the **LMFDB**. The inverse Galois problem asks whether every finite group
occurs as the Galois group of a number field; IGP24 attacks the **degree-24** case
constructively. Methods are **explicitly unrestricted** — any computational tool, AI/LLMs,
agents, external databases, and collaboration (Zulip) are all permitted; it is a "black box"
challenge that rewards *results*, not methodology. Refs: overview
`https://competition.sair.foundation/competitions/igp24/overview`; announcement
`https://terrytao.wordpress.com/2026/06/16/third-sair-competition-inverse-galois-challenge/`.

## Competition facts (confirmed in survey round 1, 2026-06-24)

Full spec + sources in `docs/competition_rules.md`. Headlines (verified 3-0 unless noted):
- **Task:** for each transitive subgroup `G ≤ S_24` (labeled `24Tt`, `t = 1..25000`; `24T1 = C_24`,
  `24T25000 = S_24`), exhibit an irreducible degree-24 integer polynomial whose Galois group is `G`.
  **5 of the 25,000 are primitive** (~24,995 imprimitive); **24,193 solvable / 807 non-solvable.**
- **Signatures `(t, r)`:** `r` = real-root count, even (`{0,2,…,24}`); **165,836** achievable pairs
  (aggregate confirmed; per-group reachable-`r` list not yet confirmed). **LMFDB baseline = 286 groups /
  622 signatures** (frozen) — the threshold to beat.
- **Verify / score split:** **Magma** verifies irreducible + degree-24 + `24Tt` label + `r` (the
  mathematical check, "in seconds", degree-independent Fieker–Klüners). **PARI/GP `nfdisc`** computes
  the **scoring discriminant** — the *field* discriminant, 60 s/poly, mixed-disc fallback (prime bound
  100000). Per-poly score `[0,1]` = f(disc smallness vs best-known, **rarity**); `S_24` ≈ negligible,
  rare pairs worth more; duplicates removed.
- **Submission:** one `submission.txt`, **≤ 100,000 bytes**, one polynomial per line as **25
  comma-separated integer coefficients**. (Coefficient ordering / per-pair multiplicity still to confirm
  on `/api`.)
- **Timeline:** opened 2026-06-15; **Stage-1 deadline 2026-08-15T12:00:00Z (noon UTC).** Stage 2
  (harder groups, more conceptual) — TBD.

## Repository layout

```
src/igp/             — main package: group metadata, Galois verification client, LMFDB client,
                       discriminant/dedup, candidate search, submission builder, scoring (scaffold)
scripts/             — one-off named runs / analyses (e.g. q01_lmfdb_baseline.py)
notebooks/           — exploratory notebooks
tests/               — pytest tests, one test_*.py per src/igp module
data/raw/            — read-only external dumps: LMFDB exports, GAP group tables, SAIR data (gitignored; symlink large)
data/processed/      — derived caches: candidate pools, computed discriminants (gitignored; reproducible)
data/targets/        — committed canonical index: the (t,r) targets + 24T group metadata (reproducibility)
submissions/         — committed built submission.txt artifacts (the deliverable; ≤100 KB each)
archive/             — completed plans + per-plan CHANGELOG entries
trash/               — soft-deleted files (gitignored; `mv` here instead of `rm`)
docs/                — reference materials, design docs
docs/phase_0_plan.md        — active plan (scope & survey)
docs/competition_rules.md   — official rules / scoring / submission format (verify vs /api, /evaluation-setup)
docs/research_log.md        — results entry point: problem-space narrative + numbered-test index
docs/commentary.md          — dated log of interpretive discussion (raw material for any writeup)
docs/related_work.md        — annotated bibliography (constructive inverse Galois, degree-24, LMFDB tooling)
docs/exploration_backlog.md — living list of candidate search directions
docs/harness_notes.md       — how the SAIR API + MAGMA/PARI verification work (fill once stood up)
docs/design/architecture.md — high-level system architecture (search → verify → minimize-disc → submit)
docs/tests/                 — one write-up per numbered experiment (NNNN-slug.md)
docs/papers/                — reference PDFs
pyproject.toml, uv.lock     — uv-managed env (pure-Python deps; PARI/GAP/MAGMA are system/network)
AGENTS.md, README.md — project state + conventions; must stay in sync
```

`src/igp/` is the library; `scripts/` and `notebooks/` depend on it, not the reverse. `archive/`
and `trash/` are write-only from active phases. The SAIR MAGMA API and LMFDB are *external services
we query*, not vendored. A **submission** is a `submission.txt` built (reproducibly) from our
discovered-polynomial database by a script in `src/igp`/`scripts/`.

## Project state — durable deliverables

Artifacts that survive between phases:
- **Target index** (`data/targets/`): the 25,000 groups + 165,836 `(t,r)` targets with metadata
  (group order, solvability, parity constraints, LMFDB coverage flag).
- **Verification loop:** a client that takes a candidate polynomial and returns its `24Tt` label +
  discriminant via PARI/GP locally and/or the SAIR MAGMA API, with results reproducible from code.
- **The survey:** `docs/related_work.md` + a cited landscape synthesis from the deep-research pass.
- **Discovered-polynomial database** (committed, `data/targets/realized.csv`): every realized poly with
  `24Tt`, `(t,r)`, `field_disc`, `scoreable`, provenance; the source of truth a `submission.txt` builds
  from. **Coverage metric = distinct `(t,r)`, not row count** (test 0029); `scripts/analyze_coverage.py`.
- **The 24/7 search service:** producers (`scripts/search_ctl.py`) → SQLite queue → daemon
  (`scripts/searchd.py`, S₂₄ filter) → SAIR verify → `realized.csv`; bandit + surrogate ranking
  (`igp/rank.py`). Operate via `search_ctl` (runbook: `docs/harness_notes.md`). Session-scoped.
- **Read-only dashboard** (`scripts/dashboard/`) + **OSCAR local-verifier spike** (`scripts/oscar/`).

## Operational rules

- **Never `rm` files; always move to `trash/`** so removals are reversible. Empty directories can be `rmdir`'d, but any file goes through `trash/`.
- **Commit at granular logical breakpoints**, not in giant batches. Each commit should pass tests if applicable.
- **Never edit an active plan markdown unilaterally** — surface problems as questions and let the user decide. If you do deviate, update the plan to match reality AND add a `CHANGELOG.md` entry in the same commit.
- **When the user adds a planning markdown**, read it critically before implementing — like a code reviewer scrutinizing a PR. Surface methodology issues, inconsistencies, ambiguities. Wait for resolution on criticals before starting. Only flag issues that would actually change the implementation.
- **README.md and AGENTS.md must stay in sync.** When AGENTS.md changes the active plan, the current best result, or other project-state facts, update README.md in the same commit.
- **Never skip pre-commit hooks** (`--no-verify`) unless the user explicitly requests it. If a hook fails, fix the underlying issue.
- **Risky / destructive operations need user confirmation before proceeding.** Examples: `git reset --hard`, `git push --force`, deleting branches, removing dependencies. Pausing costs little; an unwanted destructive action costs a lot.
- **Investigate before deleting unfamiliar state.** Unfamiliar files, branches, or lock files may be the user's in-progress work. Don't `git clean -fd` or `rm -rf` without context.
- **Don't add error handling for impossible scenarios.** Trust internal code guarantees. Only validate at system boundaries (user input, external APIs — here, the SAIR/LMFDB responses, which DO need validation).
- **No emojis in code or commits unless the user explicitly asks.**
- **Default to writing no comments in code.** Only add one when the WHY is non-obvious — a hidden constraint, a workaround, behavior that would surprise a reader. Don't narrate WHAT the code does.
- **Reproducibility.** Any committed analysis output (CSV/parquet/summary/figure) must be reproducible from committed code in the same commit — a script in `scripts/` or a notebook. **A realized polynomial must record how it was found** (provenance: which strategy/family/seed/database query), and the `submission.txt` must rebuild from the committed polynomial database + a build script.

## Working memory conventions

- **Plan iteration via numbered questions.** Open questions get labeled Q1, Q2, ... or P0Q1, P0Q2, ... Walking through them one at a time keeps decisions resolvable in isolation. Each resolution moves into a "Decisions log" with a brief rationale.
- **Numbered tests for every designed experiment.** Each run/analysis answering a stated question gets a write-up `docs/tests/NNNN-slug.md` (sequential zero-padded ID; family tag in the header) **and** a row in the `docs/research_log.md` index **and** a touch of that doc's narrative — all committed *in the same commit as the result*. `docs/research_log.md` is the results entry point (problem-space story + test index); the per-test file holds full setup/result/learnings; the per-phase synthesis summarizes across tests. Smoke / calibration runs go under the research log's *Infrastructure* section, not numbered. Every test must be reproducible from its recorded command + code commit + inputs.
- **Log ALL commentary as work proceeds — not just results.** A first-class obligation: the numbered tests record *what happened*, but the interpretive discussion — framings, debates, corrections, rejected ideas — is the raw material for any writeup. After any substantive exchange about *what results mean*, append a dated entry to `docs/commentary.md` (the insight/decision, not a transcript). Don't delete superseded interpretations; the trail is part of the record.
- **Empirical findings via dated changelog entries inside spec docs.** When a spec/design doc is iterated on a finding, append a dated block (`Empirical update (YYYY-MM-DD):`) explaining what was learned and what changed.
- **Phase work breakdown with checkboxes.** Multi-step phases get a 1-N numbered list at the bottom of the plan.
- **Synthesis writeup at end of each phase.** A short `phase_N_synthesis.md`: headline numbers, what we learned, surprises, what didn't pan out, what's deferred.
- **Known-issues block in plan docs.** Each plan has an explicit "Known issues / constraints" section.
- **One-off scratch files for empirical work.** Quick characterizations go in `scripts/` as named runs. Commit if findings are durable; move to `trash/` if one-shot.

## Collaboration style

- **Brief over verbose.** A clear sentence beats a clear paragraph. Match response length to the question.
- **No time estimates** (hours / days / weeks). State what will be done; let cadence reveal itself.
- **Surface options with a recommendation, not a decision.** "Option A: X. Option B: Y. My lean: A because <reason>. Want me to proceed?"
- **State what you're about to do in one sentence** before non-trivial tool calls. Silent work is harder to redirect.
- **End-of-turn summary: one or two sentences max.** What changed; what's next. No retrospective recaps of work the user just watched happen.
- **Don't narrate internal deliberation.** Output decisions and results; skip the thinking-out-loud.
- **When the user types "wait" or stops you, halt immediately.** Don't finish the current action "for completeness."
- **Quote artifacts, don't invent timestamps or estimates.** Skip follow-up offers if no concrete date exists.
- **Trust but verify on memory.** A memory file naming a function/path is a claim that it existed when written. Verify before recommending. Use `git log` over recalled snapshots for "recent" / "current" state.
- **Self-correction visible in workflow.** When you catch a mistake, flag and fix it — don't hide it.

## Data hygiene

- **Don't modify files in `data/raw/`.** Treat as read-only — this holds external dumps: LMFDB exports (known polynomials/fields), GAP transitive-group tables, and any SAIR-provided target data. All processing goes to `data/processed/` (gitignored) or per-study dirs.
- **Commit the target index** to `data/targets/` (the `(t,r)` targets + 24T group metadata) so coverage accounting is reproducible. **Commit the discovered-polynomial database** (it's our crown-jewel results, small, and the submission's source of truth) and **commit built `submission.txt` files** to `submissions/`.
- **Gitignore caches** explicitly: `.venv/`, `__pycache__/`, `data/processed/`, `vendor/`, `logs/`, `*.log`.
- **Symlinks under `data/raw/`** for large external sources — don't copy.
- **Record provenance for every realized polynomial** — which strategy/family/seed/query produced it — so results are auditable and reproducible.

## Compute / tooling

This is a **CPU / computational-algebra** project, not GPU/ML. No torch/wandb/HuggingFace. The
workhorses:
- **PARI/GP** (local, via `gp` or `cypari2`) — number-field arithmetic, polynomial discriminants,
  and Galois-group work where degree permits. (System install; not a `uv` dep.)
- **GAP** transitive-groups library — degree-24 group metadata (`24Tt` labels, orders, parity,
  solvability). (System install.)
- **MAGMA via the SAIR API** — authoritative Galois-group identification ("within seconds"). The
  API is **rate-limited/free-tier**, so verification calls are a **budgeted resource**: cache every
  result, batch where possible, and prefer cheap local pre-filters (degree, irreducibility,
  discriminant, resolvent factorization) before spending an API call. (Optional: personal MAGMA
  license; SageMath bundles PARI + GAP and can drive both.)
- **The binding constraints** are the **100 KB `submission.txt`**, **verification throughput**
  (API limits + local CPU), and the **Stage-1 deadline 2026-08-15** — not VRAM.

## Numbers / metrics convention

**Coverage is the headline.** Track two coverage counters against the LMFDB baseline (**286/25,000
groups; 622/165,836 signatures**): (1) **groups realized** = distinct `t` with ≥1 valid polynomial;
(2) **signatures realized** = distinct `(t, r)` pairs covered. The competition's own score is a
per-`(t,r)` sum in `[0, 1]` weighted toward **harder signatures** and **smaller discriminants** — so
secondary metrics are **per-`(t,r)` discriminant** (smaller is better; compare to the public
leaderboard's current best) and **estimated points** under the announced scoring once the exact
formula is confirmed. **Authoritative verification is MAGMA (or PARI/GP) Galois-group ID — never a
reimplementation;** a polynomial counts only once its `24Tt` label is confirmed by the official path.
Compute the discriminant convention (field vs polynomial) explicitly — confirm which the grader uses.

## Memory and other persistence

This project has `~/.Codex/projects/<project>/memory/` for per-user notes that
persist across conversations. Memory is for facts/preferences/context that survive a conversation;
in-conversation tracking belongs in plan files / synthesis docs / numbered tests.

When a memory file names a specific function/path/flag, verify it still exists before recommending
it. Memories can go stale; the code is authoritative.
