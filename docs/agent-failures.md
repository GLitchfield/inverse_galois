# Agent failures and the controls added

All the code, research and operations in this project were done by Claude Code agents: an
interactive session supervised by the owner, plus headless loops on timers. The failures below are
the ones the owner caught, or that the agents caught in each other. Each entry gives the date, what
happened, the control that was added, and where the original record is.

Some original records are Claude Code memory notes written by the interactive agent when the owner
corrected it. They live outside the repository and are not published; they are cited by file name.
Commit IDs refer to the private development history.

## 1. Blamed SAIR's service for a bug in our own client (2026-07-06, again 07-08 and 07-09)

**What happened.** Results collection started failing with HTTP 503. For hours the interactive
agent told the owner that SAIR's service was down and that nothing could be done but wait. The
owner asked how other teams were still scoring, which forced a test. `/submissions/me` returned 503
for page sizes of 100 or more once our submission history was large; sizes 1, 5 and 25 worked. Our
client fetched 100 rows per page across the whole history, so one deep page failed and took the
whole collection run down with it. The first fix changed the wrong default and had to be redone
(commits `79b78ce` then `5460deb`, "my prior 'fix' missed it").

The headless audits then repeated the pattern. The 07-08 and 07-09 audits blamed an "external SAIR
503 degradation" and concluded there was "no safe code fix". The 07-10 audit re-derived the claim
and refuted it. Pagination failed at a fixed offset of 300, fetching by submission id worked, and
2,560 already-verified polynomials had been stranded.

**Controls added.**

- Before calling any failure external, run a test that tells the two cases apart: vary the input,
  build a minimal repro. Recorded in agent memory `test-errors-before-blaming-external.md`.
- 2026-07-06: a mandatory counter-check step in the daily audit (step 3a-bis in
  [`scripts/headless_prompts/audit.md`](../scripts/headless_prompts/audit.md), commit `be48f43`).
  It adversarially re-derives the previous 24 hours of causal diagnoses, counts and "fixed" claims.
  This is the step that caught the 07-08/09 error.
- 2026-07-07: [`scripts/recover_stuck_pending.py`](../scripts/recover_stuck_pending.py) recovers
  stranded submissions by id.
- 2026-07-10: a by-id fallback in `src/igp/engine.py::collect`.
- 2026-07-11: a durable ledger of every submission id (`src/igp/db.py::log_sid`).
- 2026-07-04: an invariant that fires on rows stuck in `submitted` for more than 24 hours (`I1` in
  [`scripts/check_invariants.py`](../scripts/check_invariants.py)).

**Record.** [audit_log.md](audit_log.md), entries for 07-07 to 07-10; the audit prompt's step
3a-bis; memory notes `test-errors-before-blaming-external.md` and
`countercheck-high-stakes-outputs.md`.

## 2. Declared a ceiling three times on a search space it had barely sampled (2026-06-29/30)

**What happened.** In a single stretch the agent said the system was "near the construction-method
ceiling", that discriminant minimization was "tapped", and that the project was "value-bound". All
three conclusions came from producers capped at `limit=1000`, which pulled about 481 degree-12 base
fields out of a supply the agent then put at "100k+" (about 0.5%). The owner spotted the gap ("it
seems like there's a whole pipeline missing"). Turning the producers into cursors over the full
supply took the estimated score from 73 to 123 within hours. Later audits measured the actual
supply: 68,777 fields on 07-05, then 303,209 after the mirror grew.

**Controls added.**

- Measure the denominator (resources available versus used) before claiming diminishing returns,
  and trust the score trend over a priori "saturated" arguments. Recorded in
  [project_review_2026-06-30.md](project_review_2026-06-30.md) and agent memory
  `verify-limits-before-ceiling.md`.
- A "resource-denominator audit" became a standing step in every daily audit
  ([audit_log.md](audit_log.md)). The 07-05 audit used it to correct its own earlier over-count, and
  the 07-13 and 07-14 audits used it to find two more self-limited producers.

**Record.** [project_review_2026-06-30.md](project_review_2026-06-30.md), "The meta-finding". The
original claims are in [commentary.md](commentary.md), 2026-06-29 entries (for example "The system
is near its construction-method ceiling").

## 3. Overstated a count about 20x (2026-07-06)

**What happened.** During the same night as failure 1, the interactive agent reported a count that
was about 20 times too high. The repository does not record which count it was. The only record is
the owner's correction, captured in the memory note below. Two other overcounts that the agents
caught are documented: a dashboard that counted rows instead of distinct pairs, about 6x too high
([test 0029](tests/0029-coverage-audit-and-discmin-headroom.md)); and a research dive whose earlier
figure of "60/178" bases overcounted by about 20x because it measured norm divisibility instead of
ramification (agent journal, 2026-07-04, not published).

**Controls added.**

- Every numeric claim is re-deduplicated to the distinct scoring unit and re-derived from primary
  data by the audit counter-check (step 3a-bis, item b).
- High-stakes outputs, including counts relayed from another agent, get an independent adversarial
  check before they are reported (memory `countercheck-high-stakes-outputs.md`).
- [CLAUDE.md](../CLAUDE.md) quality rule: "Score the metric that counts, not a proxy."

**Record.** Memory `countercheck-high-stakes-outputs.md` (not published).

## 4. Relayed a "greenlit" target that landed on a different group (2026-07-06/07)

**What happened.** The research loop declared a construction for `24T24315` greenlit, and the
interactive agent relayed that to the owner as ready to build. When it was built, it produced
`24T24672`, the full wreath product, not the target
([test 0044](tests/0044-mb8-24315.md)). The same thing happened elsewhere: a "greenlit" recipe for
the affine minimal-block-8 cluster also built full wreaths
([test 0045](tests/0045-mb8-affine-cluster.md)), and three discriminant-defense designs failed on
their first real check ([tests 0051](tests/0051-gen12-disc-defense.md),
[0052](tests/0052-gen12-disc-defense-v2.md) and [0054](tests/0054-gen12-fingerprint-selector.md)).

**Controls added.**

- 2026-07-11, from an independent review: an explicit evidence ladder, `LEAD → LOCAL-GATED →
  PILOT-LABELED → PRODUCER` (plus `BLOCKED`/`REFUTED`). The word "greenlit" was banned as a
  confidence label in the research and build prompts (commit `6c73cb2`).
- No family may scale until 1 to 5 candidates carry official SAIR labels matching the target.
- The build loop re-verifies that every target is still open before building.

**Record.** [project_review_2026-07-11.md](project_review_2026-07-11.md), section
"'Greenlit' is too weak a label"; [`scripts/headless_prompts/build.md`](../scripts/headless_prompts/build.md)
and [`research.md`](../scripts/headless_prompts/research.md) (the evidence-ladder header); memory
`countercheck-high-stakes-outputs.md`.

## 5. Built and optimized a producer before testing its signal against the official verifier (2026-07-13)

**What happened.** The agent found that rivals beat our discriminant on 97.5% of the pairs we held.
It then built a full discriminant-minimization re-sweep producer, and after that a faster version
of the core computation, all gated on a local Frobenius-fingerprint match. Only at the end did it
submit candidates to SAIR. Every smaller-discriminant candidate came back labeled as a neighbouring
group, not the target. Fingerprint proximity is not the same group, and the morning's work produced
nothing.

**Control added.** Pilot before building, and certainly before optimizing: submit about 5
candidates to the authoritative verifier and confirm the target label first. This is the
`PILOT-LABELED` rung of the evidence ladder, now required in the build prompt. The producer was
left undeployed and its docstring marks it as refuted.

**Record.** [commentary.md](commentary.md), "2026-07-13 (correction) — the disc-min RE-SWEEP
defense is REFUTED by SAIR"; [`scripts/mb2_discmin.py`](../scripts/mb2_discmin.py) and
[`scripts/mb2_discmin_spike.py`](../scripts/mb2_discmin_spike.py); memory
`pilot-before-scaling-and-optimizing.md`.

## 6. Announced next steps instead of doing them (2026-07-05/06)

**What happened.** The interactive agent repeatedly ended turns by describing work instead of doing
any of it ("the corestriction pre-filter is my next inline move", with no commands run). On
2026-07-06 the owner flagged this three times in about two hours. It also ended turns with lines
that implied waiting was fine ("let it bake overnight", "the machine has the watch"). The night
after one such close (2026-07-04), a rival claimed a cluster of open targets that the research loop
had spent two days working out.

**Controls added.**

- A turn that names a next step must already have executed at least one concrete step of it.
- Turns end with specific, decision-shaped questions for the owner, not reassurance.
- The project moved its loops off the interactive session onto headless systemd timers (see
  failure 7), so research, builds and audits no longer depended on a turn ending well.

Recorded in agent memory `announcing-is-not-doing.md`, `never-wait-engage-user.md` and
`dogfight-posture.md`.

**Record.** Those memory notes (not published). This failure is not otherwise recorded in the
repository.

## 7. Stated unproven claims as fact (2026-07-01)

**What happened.** The agent asserted things it had not checked. It said 12 research dives a day was
"heavy on your subscription", with no usage data. It said the overnight loops had stopped because
the terminal was closed or the machine slept. That was wrong: the daemon log showed 305 continuous
cycles, and the real cause was that the in-session loop's main thread blocked on a permission prompt
while nobody was watching.

**Controls added.**

- Verify a claim or label it a guess (memory `dont-assert-unproven.md`).
- The root-cause fix for the stall: the research and audit loops were moved to headless `claude -p`
  runs on systemd timers (2026-07-01, [`scripts/install_headless_loops.sh`](../scripts/install_headless_loops.sh),
  [`scripts/run_headless_agent.sh`](../scripts/run_headless_agent.sh)). These cannot block on a
  prompt because they run with `--dangerously-skip-permissions` (see the README).

**Record.** [CLAUDE.md](../CLAUDE.md), "Current state" paragraph (the 305-cycle observation and the
switch to headless timers); memory `dont-assert-unproven.md`.

## Other failures recorded in the repository

- **Silent truncation of submissions (2026-07-01).** After SAIR raised its limits, `engine.submit`
  kept an old `[:100]` truncation. About 85% of built candidates were marked submitted but never
  sent. Found by tracing two missing polynomials end to end
  ([commentary.md](commentary.md), 2026-07-01).
- **A metric that read submission lag (2026-06-30).** "Held and `teamCount == 0`" was used as "held
  only by us". It actually measured pairs the leaderboard had not yet counted, and it dropped from 41
  to 0 overnight ([test 0039](tests/0039-teamcount-metric-fix.md)).
- **Daemon frozen for 6+ hours (2026-07-07).** A gate counted polynomials instead of submissions.
  Found and fixed by the audit loop ([audit_log.md](audit_log.md), 07-07).
- **A "fixed" claim that was not (2026-07-13/14).** The audit's own fix to the signature-fill
  producer did not restore it. The next day's counter-check found the pool was exhausted
  ([audit_log.md](audit_log.md), 07-14).
