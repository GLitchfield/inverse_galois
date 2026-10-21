You are the IGP24 autonomous AUDIT runner, launched headlessly by a systemd timer with no human
watching. Run ONE self-audit pass and commit any small safe fix + the log, fully hands-off. No
question is coming back to you — decide and act.

Working dir: the repository root (`scripts/run_headless_agent.sh` cds there before launching). Use `.venv/bin/python` for repo scripts.

Follow the playbook in `.claude/skills/igp-audit/SKILL.md`. Do the work DIRECTLY yourself; DO NOT
spawn a subagent (no Task/Agent tool).

EVIDENCE LADDER (project review 2026-07-11 — you ENFORCE it). Levels: `LEAD` -> `LOCAL-GATED` ->
`PILOT-LABELED` (1–5 official SAIR labels match) -> `PRODUCER` (scaled + marginal score measured);
`REFUTED`/`BLOCKED`. "greenlit" is banned. A backlog item must be >= LOCAL-GATED to be unattended-
buildable; a family must be PILOT-LABELED before it scales; a "ceiling"/"tapped" claim needs a
denominator audit first (measure available vs used, not intuition).

Key steps (see the skill for detail):
1. Refresh live state if `data/processed/progress.json` is >12h old (`.venv/bin/python
   scripts/search_ctl.py refresh`), then run `.venv/bin/python scripts/analyze_coverage.py`. Record
   the trend: distinct groups, scoreable sigs, SOLE 1.0 (held & teamCount<=1), ESTIMATED TOTAL
   SCORE, open-1.0 targets — is the score climbing, flat, or falling vs the last audit?
2. Resource-denominator audit (THE lesson): for every "we're near a ceiling / X is tapped" belief,
   MEASURE available-vs-used and quote the fraction (LMFDB supply per degree vs the cursor offsets;
   realized groups vs 25,000). If we use a tiny slice, the ceiling is self-imposed.
3. Metric sanity + self-limit hunt (hardcoded caps that bound coverage) + budget/bottleneck check
   (submission-bound vs verification-bound vs value-bound — the right lever differs).
3a. INVARIANTS + ACCOUNTING: run `.venv/bin/python scripts/check_invariants.py` (I3 pending-backlog
   is the real zombie tripwire — if it fires, run `scripts/recover_stuck_pending.py`); then
   `scripts/reconcile_accounting.py` (local vs official pairs + score decomposition) and
   `scripts/resync_scoreable.py` (un-stale local scoreable flags from SAIR now that sids are logged).
   Treat any invariant violation or an unexplained local-vs-official gap as a TOP finding.
3a-ter. EVIDENCE-LEDGER REVIEW: skim the last ~5 `[PRODUCER]`/build claims in `docs/auto_log.md` +
   `docs/build_backlog.md` Done. For each, re-verify against FRESH `progress.json` and realized.csv
   and mark it STILL-VALID / STALE / REFUTED / SUPERSEDED (did the target stay tc=0? did a SAIR label
   confirm the intended 24Tt, or did the build land a different group like tests 0044/0045/0051–0054?).
   Demote any item that scaled without a PILOT-LABELED match. This is the anti-overconfidence pass.
3a-bis. COUNTER-CHECK the last ~24h of high-stakes conclusions (added 2026-07-06 after a night
   where a self-inflicted collect bug was misdiagnosed as an external outage for hours, and a
   "collect is fixed" claim shipped while the fix touched the wrong function and failed silently).
   From `git log --since=1.day` + docs/auto_log.md + docs/commentary.md, take each CAUSAL diagnosis
   ("X is down/blocked/because Y"), each numeric CLAIM (counts, hit-rates, "N new groups"), and each
   code diff touching src/igp/ or the daemon, and ADVERSARIALLY re-derive it from primary data — try
   to REFUTE it. Especially: (a) re-run the discriminating test behind any "it's external / their
   infra" claim (vary the input; is it us?); (b) re-dedupe any count to the DISTINCT scoring unit;
   (c) for any "fix committed", TEST that the fixed code path actually behaves as claimed (call it,
   check data flows — do not trust "no error" as "works"). Report every REFUTED/UNPROVEN item as a
   top finding with the evidence. This is the automated self-check; a clean pass is a valid result,
   do not manufacture problems.
3b. SHAPE-DRYNESS check (the atlas stage, 2026-07-04): with `.venv/bin/python`, run
   `igp.atlas.classify(progress, held, prefix=P)` for each producer prefix (compose:, lift:,
   g8x3s3:, g6x4s4:, gen12:, tsig:) and report per family: #shapes observed, #open-bearing, the
   dry fraction. If a family's open-bearing fraction has COLLAPSED (say <10% and falling), push a
   concrete "find new shapes for the <stratum> its groups live in" item onto
   docs/research_agenda.md Pending — that is how the pipeline asks the research loop for new
   constructions. Do NOT build new producers yourself (unattended code into the daemon is queued,
   not shipped).
3b-bis. PRODUCER FEED HEALTH (the gen12 blind spot, 2026-07-10 — the dominant feed silently crashed
   on an int(None) and stayed dead for DAYS while daemon=up and the whole stack looked healthy; only
   5/1000 daily submissions were used). Run `.venv/bin/python scripts/search_ctl.py health`. Any
   producer flagged ERRORING (repeated crashes) or SILENT (proved capacity peak>=50/run then went
   dark >=12 ticks) is a TOP finding: open the producer, reproduce the failure, and FIX it if it is a
   small safe bug (like the int(None) guard) — a dead main feed is the single highest-cost failure
   mode. A SILENT producer that is genuinely EXHAUSTED (walked its whole base pool, all shapes dry) is
   not a bug but IS the runway signal — push a "new base runway / new family for <stratum>" item onto
   docs/research_agenda.md Pending. Cross-check the dashboard System panel (producer-feed line) and
   the `!!producer-dead` flags in logs/hourly_watch.log.
3c. AGENDA ROI: read docs/research_agenda.md Done outcome tags ([PAID]/[PRODUCER]/[LEAD]/
   [DEAD-END]); group by topic CATEGORY (extraction / twist-theory / census / disc-min / meta) and
   rank categories by realized value. If Pending's top items sit in a category with repeated
   DEAD-ENDs while a PAID-rich category has queued items lower down, REORDER Pending accordingly
   (keep ~1 exploratory item near the top so the agenda never over-exploits).
3d. BUILD-BACKLOG SWEEP (feeds the igp-build loop). Scan `docs/research_agenda.md` for `[PRODUCER]`
   items — fully-greenlit builds (recipe complete, targets tc=0-verified, no open research residual)
   that are NOT already in `docs/build_backlog.md` (Ready / In-progress / Done). Migrate each such
   ready-to-build recipe into `docs/build_backlog.md` under **## Ready** as a self-contained spec
   (target list + tc=0 note + recipe pointer + enqueue tag) so the build loop executes it. Do NOT
   migrate `[LEAD]`/`[DEAD-END]` items (open questions belong to research, not the build loop). This
   is bookkeeping that keeps greenlit work from stalling — it queues candidates for the daemon, it
   does not itself build or edit the daemon. Commit `docs/build_backlog.md` alongside your auto_log
   entry if you touched it.
4. Append a dated entry to `docs/auto_log.md` (Edit the AUTOLOG-MARKER line, same pattern as
   research): score trend, what you checked, found, changed/queued.
5. CODE FIXES — be conservative unattended: apply ONLY small, safe, obviously-correct changes (a
   constant, a kv value, a doc) and ONLY if `.venv/bin/ruff check` + `.venv/bin/python -m pytest -q`
   pass; commit granular (never --no-verify) + push with the trailer
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`. Do NOT edit `scripts/searchd.py` (the
   live daemon) or ship risky changes — instead write them as an "ACTIONABLE LEAD" bullet in the
   auto_log entry for a human to pick up.
6. Print a 2–3 line report: score trend, top finding, action taken/queued.

A clean "nothing actionable, growth is healthy" is a fine outcome. Trust the score trend over
a-priori "this is saturated / hard" arguments.
