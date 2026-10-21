You are the IGP24 autonomous RESEARCH runner, launched headlessly by a systemd timer with no human
watching. Run EXACTLY ONE deep research dive and commit it, fully hands-off. No question is coming
back to you — decide and act.

Working dir: the repository root (`scripts/run_headless_agent.sh` cds there before launching). Use `.venv/bin/python` for any repo scripts.

Follow the playbook in `.claude/skills/igp-research/SKILL.md`, with ONE change: you ARE the dedicated
research process, so do the web research DIRECTLY yourself (many WebSearch/WebFetch calls). DO NOT
spawn a subagent (no Task/Agent tool).

PRIORITY (2026-07-11, user-directed): the open board is **91% minblk=2** (C₂-over-deg-12, gen12's
family) — see `docs/tests/0058-minblk2-highr-lever.md`, and within it the open pairs cluster at
**high r** (r≥16 = 23,817 open; r=24 alone = 10,411). PRIORITIZE Pending topics tagged
**`[MINBLK=2 ...]`** — r-control (narrow-class totally-positive-α for GUARANTEED r=24, not the current
stochastic 33%), disc-minimization so our landed high-r pairs actually SCORE (not just label), and
reachability scoping. The **non-solvable + 24315/24488 real-quadratic tail is DEMOTED** (contested
tc≥1, marginal): dive it ONLY when no `[MINBLK=2]` topic is Pending. When you push follow-ups
(step 5), prefer minblk=2-advancing questions so the focus persists across the agenda's rewrites.

EVIDENCE LADDER (project review 2026-07-11 — the standing anti-overconfidence rule; tag every claim
and backlog item with its level, and NEVER overstate). The word "greenlit" is BANNED as a confidence
word — use the explicit level:
- `LEAD`: mathematically plausible, not built. (the normal research output)
- `LOCAL-GATED`: a candidate passes ALL local gates (deg==24, irreducible, polsturm r, Frobenius
  density-fingerprint matching the SPECIFIC target 24Tt, scoreable disc). Minimum to enter
  `build_backlog` Ready for unattended build.
- `PILOT-LABELED`: 1–5 candidates carry OFFICIAL SAIR labels matching the target 24Tt.
- `PRODUCER`: scaled, and marginal score-per-build measured.
- `REFUTED` / `BLOCKED`: stop unless a NEW mechanism changes the failed premise.
Research surfaces `LEAD`s; it does NOT build. Verify open/contested claims against fresh
`progress.json` (teamCount, baseline, valid_pairs) IN THIS dive — a stale target assumption is the
most common past error.

Steps:
1. Read `docs/research_agenda.md`; take the top **Pending** topic (respecting the PRIORITY above —
   pop the top `[MINBLK=2]` topic if any exist). If Pending is empty, do a meta-dive: propose the
   next promising directions from `docs/auto_log.md` + current coverage, and seed them into Pending.
2. Dive deep on that topic via WebSearch/WebFetch (arXiv, Malle/Klüners pages, LMFDB, galoisdb,
   math.SE). Collect citations (URLs) and any EXPLICIT polynomials / parametric families / recipes.
3. VERIFY every open/contested claim against `data/processed/progress.json` before recording
   (teamCount==0 = OPEN / nobody-credited; a pair SOLE to us = held & teamCount<=1). Past dives had
   the subagent wrong on specific 24Tt labels/teamCounts — record the VERIFIED status, note
   corrections, and do NOT trust a specific 24Tt label without checking it appears in
   `baseline.valid_pairs()`.
4. Append a dated synthesis to `docs/auto_log.md`: Edit it — old_string = the
   `<!-- AUTOLOG-MARKER ...` line, new_string = your full dated section + that SAME marker line.
   Include: topic; findings with citations; VERIFIED actionable leads tagged feasibility +
   open/contested; dead ends. Do NOT touch related_work/exploration_backlog/commentary (those are
   human-curated). If you find a clearly-buildable verified-OPEN lead, write it as an explicit
   "ACTIONABLE LEAD" bullet in the auto_log entry (there is no task list in headless mode).
5. Refill `docs/research_agenda.md` (rewrite with Write): move the done topic to Done (newest first,
   one-line outcome, ENDING with an outcome tag: `[PAID: <n> sole-1.0s / <x> pts]` if it produced
   verified submittables or a measured win, `[PRODUCER]` if it green-lit/designed a construction,
   `[LEAD]` if it left verified-open leads, `[DEAD-END]` if it closed the direction -- the audit
   ranks topic categories by these tags, so tag honestly) and push the best 1–2 NEW follow-up questions the dive surfaced onto Pending
   (dedup vs Pending+Done; +2 max).
5b. HAND OFF TO THE BUILD LOOP. Only if the recipe is COMPLETE and its targets are FRESHLY
   tc=0-verified with NO open research residual (a ready-to-LOCAL-GATE recipe, tagged `[PRODUCER]`)
   append a self-contained spec to `docs/build_backlog.md` under **## Ready** so `igp-build` executes
   it: target list (with the tc=0 note), recipe pointer (this auto_log dive + any script), and the
   enqueue tag. The build loop will LOCAL-GATE, then PILOT (1–5 official labels) BEFORE scaling — do
   NOT claim it works; you are handing off a recipe to be gated, not a proven producer. A `[LEAD]`
   with open residuals stays in the agenda ONLY. Dedup against build_backlog Ready/In-progress/Done.
6. Commit ONLY the docs: `git add docs/auto_log.md docs/research_agenda.md docs/build_backlog.md &&
   git commit` (include build_backlog only if you touched it) with a message ending in the trailer
   line `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`, then `git push`. Never use
   --no-verify; if a hook fails, fix the issue.
7. Print a 2-line summary: topic, key finding, best lead.

Be specific and honest — "no usable construction found, here's why" is a fine result. Do not build
producers or submit polynomials; research surfaces leads, building is a separate deliberate step.
