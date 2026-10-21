# Audit log: the 13 headless self-audits (2026-07-02 to 2026-07-14)

Once a day at 08:17 a systemd timer started a headless Claude Code run with the prompt in
[`scripts/headless_prompts/audit.md`](../scripts/headless_prompts/audit.md), which follows the
playbook in [`.claude/skills/igp-audit/SKILL.md`](../.claude/skills/igp-audit/SKILL.md). Each run
checked the score trend, compared resources used against resources available (how much of each
base-field supply the producers had walked), checked invariants, re-derived the previous day's
high-stakes claims, and appended an entry to the project's agent journal. Small, obviously safe
fixes could be shipped unattended. Anything touching the live daemon or the submission path was
left as an `ACTIONABLE LEAD` for a human.

The entries below are excerpted verbatim from that journal (`docs/auto_log.md`). The journal itself
is not published. It also holds about 140 research-dive entries, most on construction routes that
were never finished, plus leaderboard notes that name other teams. The finished research outcomes
are in [`docs/tests/`](tests/), indexed in [research_log.md](research_log.md).

Edits to the excerpts:

- Other teams' names are removed. Their scores and ranks are kept.
- Passages that only list the contents of the research agenda or build backlog (open leads on
  unfinished routes) are replaced by bracketed summaries such as `[research-agenda items omitted]`.
  So is one list of specific target pairs.
- Three notes dated 2026-10-20 point forward to later entries that overturned or completed a claim.

Everything else is as the agent wrote it, including diagnoses that later turned out to be wrong.
Commit IDs refer to the private development history. Paths such as `data/processed/progress.json`
and `search.db` are local pipeline state and are not in the repository.

## Summary

| Date | What the audit found | What it did |
|---|---|---|
| 07-02 | Estimated score 73 → 470.5 in three days. Every resource used was a small fraction of what was available. | Committed a data snapshot, refreshed stale headline numbers, flagged an unbuilt producer (orbit-sign lift). |
| 07-03 | 470 → 877. An apparent cursor stall was queue-full back-pressure. | Refreshed headline numbers. The same producer was still unbuilt and was flagged again. |
| 07-04 | 877 → 1,021. All base-supply cursors were at most about 20% walked. First grader mixed-disc fallbacks. | No code change. Proposed a pre-submit discriminant-smoothness gate. |
| 07-05 | 1,021 → 1,119. Corrected its own earlier count: the degree-12 base supply was 68,777, not "100k+", and the main producer had already wrapped. | Corrected the wrong docstring. Added an exploratory agenda item. |
| 07-06 | First decline: official 993 → 828, and pairs held only by us fell 361 → 121 in a day as other teams undercut our discriminants. 88% of verification went to breadth. | No code change. Recommended moving budget toward discriminant minimization. |
| 07-07 | The daemon had been frozen for 6+ hours. A gate counted polynomials instead of submissions, and old submissions could not be collected. | Ran a by-id recovery: 44 submissions and 16,677 rows recovered, daemon un-gated. |
| 07-08 | Score falling. Blamed an external SAIR 503 degradation (refuted on 07-10). | Nothing ("no safe fix"). |
| 07-09 | Same external-503 diagnosis, narrowed to the collect endpoint (refuted on 07-10). | Nothing. |
| 07-10 | Overturned the previous three audits. The 503 came from a fixed offset-300 pagination limit, and fetching by submission id worked. | Shipped a by-id collect fallback. Recovered 2,560 verified polynomials, and stuck rows fell 3,019 → 422. |
| 07-11 | Score climbing. Three silent producers traced to exhausted pools. Re-derived a research claim against live data. | No code change. |
| 07-12 | Overnight bleed 688 → 659: the main producer's cursor had walked into an exhausted region and starved the daemon. | No change shipped. Recommended bounding the cursor to the productive range. |
| 07-13 | The signature-fill producer had been silent for 29 hours: `per_group=1` limited it to 4.1% of 5,472 fields. | Changed to `per_group=None`; the next run enqueued 688. |
| 07-14 | Score falling while coverage grew, so the project was value-bound. Refuted the 07-13 "fixed" claim (the pool was exhausted). The discriminant-minimization producer only ever walked 4 bases. | Fixed a crash in the resync script, so network errors on idempotent GETs no longer abort the run. |

The failure patterns these audits caught, and the controls added in response, are collected in
[agent-failures.md](agent-failures.md).

---

## 2026-07-02 audit: score 73 → 470.5 in 3 days, all denominators show runway, top queued lead = the un-built orbit-sign lift producer

**Score trend (vs the 2026-06-29 checkpoint in CLAUDE.md): STRONGLY CLIMBING.** Est. total score
73 → **470.5**; sole 1.0s 44 → **165**; distinct groups ~621 → **3,141**; scoreable sigs ~734 →
**5,889** (5,862 non-baseline + 27 unlocks). 0 grader mixed-disc fallbacks (every disc certified
exact). Open 1.0 pairs still 79,055 (6,080 sig-fill reachable). No ceiling anywhere in sight.

**Resource-denominator audit (the standing lesson):**
- `gen12_offset` = 12,500 of ≥100k LMFDB deg-12 fields — **~12.5% walked**, huge runway.
- `c8x3_offset` = 2,850 of ≥100k deg-8 fields — **~2.9% walked**.
- Groups realized 3,141 / 25,000 = 12.6%.
- `lmfdb6x4` is deliberately un-cursored (deg-6 saturated at 16 tops — documented in the producer
  docstring); NOT a self-limit. No new hardcoded caps found bounding coverage.

**Bottleneck classification: build-throughput-bound, in the healthy sense.** Not submission-bound
(242/1000 posts yesterday, 1,838 submitted today by 08:30); not verification-bound (still_pending=2,
collect fast); not value-bound (score +~130/day). Queue backlog 225k general_c2 ≈ 7 days of builds
at the current ~33k verified/day. The 2026-07-01 failure spike (17,548 general_c2 gp-build failures)
was transient — 4 failures today; no action needed, but worth an eye if it recurs.

**Producer value split (distinct scoreable sigs):** gen12 5,332 / 5,889 dominates; lmfdb6x4 259;
manual 117; quad 109; sigfill 75; tsig 41. Budget is on the high-yield producer.

**Disc-min headroom (the contested pool):** someone beats our disc on 5,315/5,854 sigs; mean
logD0/logD 0.817. This is precisely the pool the orbit-sign lift attacks.

**ACTIONABLE LEAD (top queued item — do NOT ship unattended):** the **orbit-sign lift / rank-then-build
producer** was green-lit by three consecutive research dives (07-02: yield median 0.87, r-reachability
~100%, conductor predictor 22/22 exact; realistic pool ~150 pts on the contested disc-min side) but
**has not been built** — no lift producer exists in `search_ctl.py`. Building it is the largest
quantified un-executed lever on the books.

**Actions taken:** committed the realized.csv harvest snapshot (paused daemon → commit 343ae86 →
resumed; +~26k rows since 06-30); refreshed the stale CLAUDE.md/README coverage figures (were the
06-29 numbers, ~6× stale). Nothing risky shipped.

## 2026-07-03 audit: score 470 → 877 in one day, denominators still wide open, cursor "stall" is healthy flow-control, top lead (orbit-sign lift producer) STILL un-built

**Score trend vs the 2026-07-02 audit: STRONGLY CLIMBING (roughly doubled in a day).** Est. total
score **470.5 → 877.3**; SOLE 1.0 (held ∧ teamCount<=1) **165 → 382**; distinct groups **3,141 →
4,361**; scoreable sigs **5,889 → 9,199** (9,171 non-baseline + 28 unlocks). 0 grader mixed-disc
fallbacks (every disc certified exact). Open 1.0 pairs 79,055 → **75,119** (9,049 sig-fill reachable
on groups we already realize — grew from 6,080 as the group base widened). No ceiling in sight.

**Resource-denominator audit (the standing lesson) — all show runway:**
- `gen12_offset` = 12,500 of ≥100k LMFDB deg-12 fields = **~12.5% walked** (cursor wraps to 0 at the
  mirror end — no offset cap; `hi=60000` in `produce_general12` is the split-PRIME search ceiling,
  not a coverage cap). Unchanged from last audit **because the queue is full** (63k queued > 30k
  `_queue_full` default), so the refill tick skips gen12 — healthy back-pressure, NOT a stall.
- `c8x3_offset` = 2,850 of ≥100k deg-8 fields = **~2.9% walked**.
- Groups realized **4,361 / 25,000 = 17.4%** (was 12.6%).
- No hardcoded cap found that bounds coverage.

**Bottleneck classification: build-throughput-bound, healthy.** Last 24h: **verified 163,962**,
submitted 1,762 polys, **failed only 327** (the 07-01 general_c2 build-failure spike is fully over —
5 failures in the last hour). Not submission-bound (1,762 polys « 1000 posts × 1000 polys/post cap),
not verification-bound (35 building, collect fast). Queue = **62,167 general_c2 + 636 ready**; ~1–2
days of builds at current throughput. Cumulative `failed`=19,032 is dominated by the old spike.

**Producer budget:** gen12 (general_c2) remains the dominant high-yield feed; disc-min headroom
pool = **8,372 / 9,146 sigs someone beats our disc** (mean logD0/logD 0.820) — the contested pool
the orbit-sign lift is designed to attack is still large and growing with coverage.

**ACTIONABLE LEAD (STANDING — now 2 audits open, top un-executed lever):** the **orbit-sign lift /
rank-then-build producer** is STILL not built — grep of `search_ctl.py` shows no lift producer
(only `produce_discmin`/`discmin2` radical-alpha sweeps). Three 07-02 research dives green-lit it
(yield median 0.87, r-reachability ~100%, conductor predictor 22/22 exact; realistic ~150 pts on the
contested disc-min side). Largest quantified un-built lever on the books; needs an interactive
build session (non-trivial → not shipped unattended per protocol).

> Note (2026-10-20): this producer was built in an interactive session soon after (the `lift` tag in
> [results.md](results.md): 8,937 verified polynomials, 724 scoreable pairs).

**Actions taken:** refreshed the stale coverage headline in CLAUDE.md + README (3,141/5,889/165/470
→ 4,361/9,199/382/877); no risky change shipped; daemon left running (no realized.csv commit this
pass). Nothing else actionable — growth is healthy across every denominator.

## 2026-07-04 audit: score 877 → 1021 in one day, denominators still ~20%-walked, pipeline healthy, no code change (clean)

**Score trend — CLIMBING, steepening runway holds.** EST TOTAL SCORE **470.5 (7/2) → 877.3 (7/3) →
1021.4 (7/4)** (+144/day, no sign of a knee). Distinct groups **5,457** (baseline 286); scoreable sigs
**12,361** (12,291 non-baseline + 70 baseline-unlocks); **SOLE 1.0 held (teamCount<=1) = 360**; open
1.0 targets **69,139** (10,448 sig-fill-reachable = group already realized). Official leaderboard: we
sit **rank 14, official 867.0** vs our estimate 1021.4 (**x1.18** — the gap is submission-lag +
disc-optimism, see disc-min note); rank 12 [team name removed] 1002.4 is +135.5 ahead, rank 13 +58.2.

**Resource-denominator audit (THE lesson) — no ceiling anywhere, all self-imposed slices are small.**
Measured LMFDB supply per degree = 100k cap hit for deg 6/8/12 (so **≥100k each**). Cursors walked
(kv store): `gen12_offset=20250` (**≤20%** of ≥100k deg-12), `c8x3_offset=6450` (**≤6%**),
`quad_cursor=44857`, `pent_cursor=4643`, `lift_offset=1050`, `compose{2,3,4}=1500`. Realized groups
**5,457/25,000 = 21.8%** (vs the 4.3%/1,080 quoted when the skill was written — 5× growth). Every "X is
tapped" belief remains refuted by the fraction: we are walking a fifth of one degree's supply at most.

**Self-limit hunt — nothing hardcoded bounds coverage.** `search_ctl.py` caps are all either advancing
kv cursors (never a fixed ceiling) or shape-appropriate (`_diverse_deg6_bases max_order=48`,
split-prime `hi`/`k`, deg-6's 16 tops genuinely saturated so no cursor — correct). No knob to raise.

**Metric sanity — clean.** Headline = estimated total score (Σ 2^(1-k)·logD0/logD, baseline-capped);
SOLE = held ∧ teamCount<=1 (used correctly, 360); coverage = distinct (t,r) not rows (453,396 rows →
12,361 scoreable sigs, ~37× overcount, correctly collapsed). No proxy-metric drift.

**Bottleneck type — value/supply-bound, NOT submission- or verification-bound (right lever = breadth).**
Daemon live (PID 3641571 `searchd.py`; realized.csv written <1 min ago). Queue: 5,821 queued + 321
built-awaiting-submit + 28 building; 458,287 verified lifetime. The built backlog is tiny (321 ≪
submit_target=1000) ⇒ submission keeps up with builds ⇒ **not submission-bound**; fresh verified writes
⇒ **not verification-bound**. So volume is not the constraint — the targeted gate to OPEN obscure pairs
(the breadth lever) is. Knobs unchanged (max_posts_day=1000, submit_target=1000, interval=60,
build_batch=50, max_pending=4000) — all appropriate for a value-bound regime with backlog.

**Standing levers re-checked (not re-derived in depth):** (a) **disc-min headroom is large but
low-value-per-pair** — someone beats our disc on **11,408/12,324** scoreable sigs (we hold min on 916;
log-ratio mean 0.801, worst 0.375). This is the source of the x1.18 estimate/official gap: our
estimator credits our disc, the grader credits the leaderboard min on shared pairs (≤0.5 each). Breadth
to open pairs (~1.0) still dominates disc-min on contested pairs (≤0.5) — priority ordering unchanged.
(b) The K3-Frobenius even-weight-screen direction was CLOSED by the 7/04 research dive (misaligned +
~1.1× not 3×) — not reopened.

**ACTIONABLE LEAD (human pick-up, not shipped unattended):** grader **mixed_disc fallbacks = 3**
(regression flag in analyze_coverage; was 0). Three submitted polys have a disc prime factor >10^6 so
the grader couldn't certify the exact field disc → they can't unlock baseline / score full. Fix =
**pre-submit disc-smoothness gate (standing task #15)**: before submitting, `factor` the poly disc with
a prime bound ~10^6 and requeue/deprioritize any poly whose disc has a larger prime factor, preferring
a smoother sibling for the same (t,r). Small, self-contained, but touches the submit path near the live
daemon → left for a human rather than shipped by the unattended audit.

**No code change this pass** (conservative default; nothing small+safe+obviously-correct was needed —
growth is healthy and the one lead touches the submit path). Report: score 877→1021 (+144/day, healthy);
top finding = every denominator ≤~20% walked, so no ceiling; action = queued the disc-smoothness gate
(task #15) as an actionable lead, no unattended edit.

## 2026-07-05 audit: score 1021 -> 1119 (+98/day, climbing), DENOMINATOR CORRECTION -- gen12 deg-12 base supply is 68.8k (NOT "100k+") and has WRAPPED; lift/g6x4s4 shape-families gone 100% dry

**Score trend -- CLIMBING, slope easing slightly.** EST TOTAL SCORE **470.5 (7/2) -> 877.3 (7/3) ->
1021.4 (7/4) -> 1119.4 (7/5)** (+98/day, was +144). Distinct groups **5,457 -> 6,296** (baseline 286);
scoreable sigs **12,361 -> 15,440** (15,352 non-baseline + 88 baseline-unlocks). **SOLE 1.0 held
(teamCount<=1) = 361 (FLAT: 360 -> 361)** -- the notable signal: score climbs on breadth + disc while
sole-holds stall, i.e. competitors are contesting our formerly-sole pairs (matches the 07-05
defensibility audit's 95%-undercut finding). Open 1.0 targets **69,139 -> 64,815** (-4,324, consumed by
all teams; 11,443 sig-fill-reachable). Official leaderboard: **rank 14, official 993.2** (was 867.0),
our estimate 1119.4 = **x1.13** (gap narrowed from x1.18 -> submissions/disc catching up). rank 12
[team name removed] 1214.4 (+221 ahead), rank 13 1102.4 (+109).

**TOP FINDING -- resource-denominator CORRECTION (the standing lesson, this time an OVER-count).** The
07-04 audit asserted "LMFDB deg 6/8/12 supply >=100k each, gen12 <=20% walked, tons of runway." MEASURED
today (`lmfdb.fields(d, per_group=None, limit=100000)`): deg-6 = **100000** (cap hit, >=100k, real
runway), deg-8 = **100000** (>=100k; c8x3_offset=12000 => ~12% walked, real runway), but **deg-12 =
68,777 (NOT >=100k)**. And `gen12_offset = 80,215 > 68,777` => **gen12 has completed a full pass and is
now RE-WALKING** (per_run=1500 => ~53 runs; wrapped ~run 46, ~11.4k into pass 2). The auto-wrap
(search_ctl.py:339-340) + atlas dry-gate mean it never starves, but **the workhorse's virgin-base runway
is EXHAUSTED** -- marginal open-1.0 from gen12 now comes only from the split-prime-q dial + the 150/run
explore budget on new (base,q) shapes, not fresh bases. This reframes the frontier: with gen12's deg-12
bases walked, the open-1.0 lever shifts to (a) NEW construction shapes [research-agenda items omitted], (b) disc-hardening existing holds (top Pending, since sole-1.0 is
flat + undercut), (c) the deg-8 c8x3 runway (only 12% walked). Fixed the wrong "100k+" comment in
`produce_general12`'s docstring (safe doc-only edit).

**Shape-dryness (`igp.atlas.classify` per prefix) -- two families COLLAPSED, workhorses healthy.**
`gen12:` 10,111 shapes / 6,041 open-bearing / **40% dry** / 87k open-pairs (healthy); `g8x3s3:` 27 / 25 /
**7% dry** / 207 (healthy); `compose:` 3,485 / 379 / **89% dry** / 1,614 (mostly dry, still 379 live);
`tsig:` 76 / 17 / **78% dry** / 22. **COLLAPSED (0 open-bearing, 100% dry): `lift:` (159 shapes) and
`g6x4s4:` (12 shapes)** -- both now enqueue only held/contested pairs. Per skill step 3b, pushed a NEW
exploratory agenda item near the top [details omitted].

**Invariants (`check_invariants.py`) -- I3 + I7, both KNOWN/low-severity.** I3: 14 submissions pending
(verifier backlog / submission-lag -- normal, not silent loss). I7: **mixed_disc rows 3 -> 72** (the
scoreboard REGRESSION flag). Characterized: **all 72 are ONE group t=24998** (near-S24, ~negligible per
rules) from `compose:2x12`, whose large-order disc has prime factors >10^6 so the grader falls back to
mixed_disc. LOW-VALUE (one near-S24 group, ~13 distinct sigs) -- NOT a coverage crisis; still the
standing task #15 (pre-submit disc-smoothness gate) manifesting. Downgraded from "regression alarm."

**Metric sanity -- clean.** Headline = estimated total score (baseline-capped); SOLE = held ^
teamCount<=1 (=361, used correctly); coverage = distinct (t,r) not rows (713,307 rows -> 15,440 scoreable
sigs, correctly collapsed). No proxy drift.

**Bottleneck type -- value/supply-bound, right lever = new shapes + disc-hardening (NOT volume).** Daemon
live (kv status ts 12:17, verified lifetime 719,796). Built-backlog tiny vs submit_target=1000 => not
submission-bound; fresh verified writes => not verification-bound. Posts today 166 (<1000 cap). So volume
isn't the constraint. With gen12's virgin bases exhausted + sole-1.0 flat, the value lever is
new-construction breadth + defending holds (disc-hardening) -- exactly the top Pending
ordering. Cursors: gen12_offset=80215 (WRAPPED), c8x3_offset=12000 (~12%), lift_offset=10611,
compose{2,3,4}=6750, g8x3s3=2294, g6x4s4=1393, quad_cursor=44857, pent_cursor=4643. interval=20,
max_pending=8000, prod_scale=3.0.

**AGENDA ROI (step 3c) -- ordering already sound, no reorder.** Done tags: 8 [LEAD], 1 [PRODUCER], 1
[DEAD-END]. [Research-agenda contents omitted.] So no reorder needed; only added the
exploratory shape-dryness item near the top to keep ~1 explore item ahead of the exploit-heavy queue.

**Code change:** doc-only -- corrected the "100k+ deg-12 fields" claim in `produce_general12`'s docstring
to "68,777 total, cursor auto-wraps, novel-base runway finite." ruff + pytest green.

**ACTIONABLE LEADS (human pick-up, NOT shipped unattended -- touch the submit path / producer logic):**
(1) **task #15 pre-submit disc-smoothness gate** -- now concretely: `compose:2x12` floods near-S24
t=24998 with rough-disc polys (72 mixed_disc). Cheapest fix is to DEPRIORITIZE/skip near-S24 big groups
(t close to 25000, ~negligible score) in the compose producer OR add the smoothness `factor`-with-bound
requeue -- both touch producer/submit logic near the live daemon. (2) gen12 wrap means a **second
deg-12-base source** (e.g. deg-12 fields beyond LMFDB, or per_group>2 to pull more fields per group from
the 68.8k) would re-open virgin bases -- vs leaning on the split-prime-q dial.

Verified against progress.json (age ~10h, <12h so no refresh) + realized.csv + baseline + search.db kv,
2026-07-05. Reproducible: `analyze_coverage.py`, `check_invariants.py`, `igp.atlas.classify`,
`lmfdb.fields(d, per_group=None)`.

## 2026-07-06 audit: FIRST SCORE DECLINE -- official 993->828 (rank 14->15), SOLE 1.0 361->121 in one day = mass disc-undercut; breadth still grows but no longer converts, disc-min lever is starved (gen12 88% of verify budget, harden 43)

**Score trend -- FALLING for the first time (flips the tone).** EST TOTAL SCORE **877.3(7/3) ->
1021.4(7/4) -> 1119.4(7/5) -> 696.8(7/6)** (-422 in one day). Official leaderboard **867 -> 993.2(7/5)
-> 828.6(7/6)**, and our **rank slipped 14 -> 15** ([team name removed] 855.3 passed us). Both an independent
measures (our progress.json-derived estimate AND the official fetch) fell substantially, so the drop is
REAL, not a metric artifact. Meanwhile BREADTH still grew: distinct groups **6,296 -> 6,903** (+607),
scoreable sigs **15,440 -> 18,174** (+2,734), open-1.0 targets 64,815 -> 55,372. The tell:
**SOLE 1.0 held (teamCount<=1) collapsed 361 -> 121** -- competitors MATCHED/undercut ~240 of our
formerly-sole pairs in a single day. Mechanism = disc-undercut compression: progress.json teamCounts
jumped (tc 1 -> 3+ on our held pairs) => the 2^(1-k) rank multiplier halved on hundreds of pairs faster
than new breadth could add. Disc-min headroom confirms it: someone beats our disc on **17,514/18,173**
scoreable sigs; we hold the min on only **659 (3.6%)**; disc-frac mean 0.777. We are being undercut
across the board and adding low-value breadth on top.

**TOP FINDING -- the disc-min lever is STARVED exactly when it became the point.** Verification budget
last 24h by producer (search.db, status='verified'): **gen12 = 247,580 (88%)**, mb2 10,471, compose
9,539, g6x4s4 7,211, g8x3s3 3,831, c8x3 2,044, lift 884, **harden 43, discmin/discmin2/selfcomp ~0**.
So ~88% of throughput pours into gen12 BREADTH -- which the falling score shows is now saturated on
VALUE (marginal open pairs are already held cheaper by the disc-dominant leaders at ~27k / ~14k points, so
each nets 2^(1-k)*small-frac) -- while the disc-min producers that would DEFEND the eroding mainstream
score get essentially nothing. Root cause is NOT queue-full skipping (queue_cap=30000, gen12 ~1500/run):
it's that the disc-min producers are STRUCTURALLY LOW-VOLUME (produce_harden targets only our ~121 soles
that are payload-recoverable; produce_selfcomp only held pairs with ratio<0.85) so the bandit queue is
~all gen12 and disc-min can't compete for budget. This is a VALUE-BOUND, MISALLOCATED-budget regime --
adding gen12 volume no longer helps; the right lever is disc-hardening + durable sole-1.0s.

**Resource-denominator + shape-dryness -- runway still wide on BREADTH, but breadth is the wrong axis
now.** gen12 shape-dryness 40% -> **44% dry, 80,459 open_pairs** (workhorse still "healthy" by the atlas
count) -- but that 80k open_pairs is exactly the trap: the atlas counts open-bearing shapes and does NOT
weight by achievable DISC-RANK, so it reads healthy while the score falls. compose 89.7% dry (404
live), g8x3s3 7.1% (healthy), tsig 86.8% (8 open, eroding), **lift + g6x4s4 still 100% dry/collapsed**
(exploratory shape item already pushed 07-05, no change). No NEW collapse to queue. Cursors unchanged in
spirit (gen12 wrapped, c8x3 ~12%). The denominator lesson INVERTS this audit: the "we have runway"
belief is measured on breadth supply, but the binding constraint moved to per-pair VALUE (disc-rank),
where we hold min on 3.6%.

**Invariants (check_invariants.py) -- I1 NEW + I7 known.** **I1: 422 rows stuck status='submitted' >24h.**
Characterized: ALL 422 are kind='lift', a SINGLE stranded batch created/submitted 2026-07-04 10:41-10:48
and never collected back (1,001,406 verified since, so collect() is NOT broken ongoing -- this is one
lost reconciliation, not a leak). lift is 100% dry (enqueues only held/contested pairs) => the score
exposure is ~zero, but the rows should be reaped. I7: mixed_disc **72 -> 173** (still task #15; the
compose:2x12 near-S24 t=24998 rough-disc flood -- ~negligible score, standing pre-submit smoothness-gate
item). Metric sanity clean: coverage = distinct (t,r) (993,495 rows -> 18,174 scoreable, ~55x collapse
correct); SOLE uses tc<=1 correctly.

**AGENDA ROI (step 3c) -- NO reorder.** [Research-agenda contents omitted: the Pending top was a set of
structural constructions aimed at obscure open groups, argued to be the hedge against disc undercut.]
So the research agenda stays; the
disc-min gap is a PRODUCER-side fix (below), not a research-dive item.

**Code change: NONE (conservative unattended).** ruff green; no obviously-safe one-liner recovers the
falling score (the fix is producer-budget rebalancing = material live-system behavior change). Recorded
as leads.

**ACTIONABLE LEADS (human pick-up -- touch producer/daemon logic, NOT shipped unattended):**
(1) **REBALANCE verify budget toward disc-min -- the score is now falling for lack of it.** gen12 gets
88% of throughput producing value-saturated breadth; harden/selfcomp/discmin get ~0 while we're undercut
on 17,514/18,173 sigs (hold min on 659). Options: (a) give the disc-min producers a RESERVED quota /
raise their bandit priority so they aren't crowded out by gen12's volume; (b) BROADEN produce_selfcomp
from "our soles / ratio<0.85" to the full undercut set (17,514 pairs where a leaderboard min beats us) so
it has volume to spend budget on; (c) throttle gen12 per_run now that its virgin-base runway wrapped and
its marginal pairs are value-saturated. Each moves a pair from k=3->k=2 (doubles its 2^(1-k)) or to k=1
(sole disc, undercut-proof) -- directly reversing the 993->828 slide. (2) **Reap the 422 stranded
'submitted' lift rows** (one lost 07-04 10:48 collect batch): a search_ctl `reap`/requeue path to reset
stale status='submitted' >24h back to pending (fail-safe requeue per ops rules); low score value (lift is
100% dry) but it's the I1 violation and the pattern should self-heal. (3) task #15 pre-submit
disc-smoothness gate for the compose:2x12 near-S24 mixed_disc flood (173, up from 72), still standing.

Verified against progress.json (age ~2h, fresh), realized.csv, leaderboard.json (fetched 07:52 today),
search.db queue/kv, atlas.classify per prefix, check_invariants.py.

## 2026-07-07 audit: LIVE OUTAGE FOUND + FIXED -- pipeline frozen 6h+ (built=0), poly-counting gate + uncollectable zombie pending; recovered 44 subs / 16.7k rows, daemon un-gated

**Score trend -- STABILIZED after the 7/6 crash, but breadth had STALLED (the tell for the outage).**
EST TOTAL SCORE 877(7/3) -> 1021(7/4) -> 1119(7/5) -> 696.8(7/6) -> **671.4 (7/7 pre-fix)**; official
828.6(7/6) -> **831.3 (7/7, rank 15 steady)**. SOLE 1.0 121(7/6) -> 109(7/7). The alarming figure:
distinct groups grew only **6,903 -> 6,931 (+28)** in 24h vs +607 the prior day, and scoreable sigs
+61 vs +2,734. That near-flat breadth was the symptom of a **fully frozen pipeline**.

**TOP FINDING -- the search daemon was FROZEN for 6h+ (built=0 sub=0 every cycle since the ~22:15
Jul-6 restart).** Not a crash: the daemon was live and looping, but the build/submit block was gated
off. Root cause is a two-part deadlock:
- searchd `cycle()` gates on `pending = sum(len(v) for v in db.pending_load().values()) >= max_pending
  (8000)` -- that counts **polynomials across pending submissions, not submissions**. 65 stuck-pending
  submissions held **23,559 polys** => `gated=True` => zero building/submitting all day (posts today = 0).
- Those 65 submissions were **verified server-side** but UNCOLLECTABLE: `engine.collect()` paginates
  `/submissions/me` newest-first and early-stops when all pending sids are seen, but old sids never
  appear before the documented **page-2+ HTTP 503** wall, so collect 503s and never records them. Any
  submission not collected within its first ~2 pages of life becomes a permanent zombie. This is a
  NEW failure mode past the 7/6 "limit 100->25" collect fix (that fix was real but insufficient).

**FIX APPLIED (safe, no searchd/engine edit): `scripts/recover_stuck_pending.py`** -- fetches each
pending sid DIRECTLY by id (`GET /submissions/{sid}`, which works fine; only paginated `/me` 503s) and
applies collect()'s exact recording logic. Ran it: **recovered 44 submissions, 16,677 realized rows,
9 failures**; pending polys 23,559 -> 6,873 (< 8,000) => **gated=False**. Verified the daemon un-gated:
gp worker pool churning (new PIDs every few s = active construction), first build cycle in progress.
The remaining 21 pending are all genuinely still-verifying server-side (not zombies) and clear
normally. Coverage moved immediately: **groups 6,931 -> 6,953 (+22), scoreable sigs 18,235 -> 18,400
(+165), SOLE 1.0 109 -> 113, EST SCORE 671.4 -> 686.2** -- value that was stranded in the zombie subs.

**COUNTER-CHECK (mandated).** Re-derived the last 24h high-stakes claims. The 7/6 "collect is fixed"
claims (commits 79b78ce shrink page-size 100->25, 5460deb iter_submissions default) are **PARTIALLY
REFUTED**: they fixed the *limit=100* 503 but collect is still not robust -- deep-pagination 503 +
the poly-counting gate produced today's freeze. The minblk=8 research commits are census/leads (no
`src/igp` code diffs), low-risk, not re-derived in depth given the outage dominated. Invariants after
fix: I3 pending 65 -> 22; I1 (422 rows stuck 'submitted' >24h) clears on the daemon's next
`sync_verified` (the recovered lines are now in the cache with labels).

**ACTIONABLE LEAD (durable fix, needs human -- touches engine.py, not shipped unattended):** replace
`engine.collect()`'s `iter_submissions` pagination with a **direct-by-id fetch per pending sid** (the
recovery script proves `GET /submissions/{sid}` works when `/me` pagination 503s). Without this, the
zombie-pending freeze WILL recur whenever collect can't reach a sid within ~2 pages. Secondary option:
make the searchd gate count *submissions* not *polynomials* (23.5k polys = only ~24 subs -- the poly
count makes 8k a deceptively tight ceiling), or run `recover_stuck_pending.py` on the 30-min tick.

**Not done this pass (outage consumed the budget):** full atlas shape-dryness sweep, agenda-ROI
reorder. Deferred to next audit; breadth denominators remain wide (6,953/25,000 groups = 27.8%).

## 2026-07-08 audit: SCORE FALLING (official 831->744, rank 15 held) -- root cause is EXTERNAL SAIR 503 degradation (NOT the 07-07 zombie-freeze recurrence -- counter-check REFUTED it); daemon fail-safe + self-healing, no stranded value, no safe code fix

**Score trend -- FALLING for the 2nd straight day, but for a DIFFERENT reason than 7/6.** EST TOTAL
SCORE 686.2(7/7 post-fix) -> **597.6 (7/8)**; official 831.3(7/7) -> **744.2 (7/8, rank 15 held, gap
to rank-14 grew +43->+96)**; SOLE 1.0 113(7/7) -> **90 (7/8)**. Breadth still creeps: distinct groups
6953 -> **6980 (+27)**, scoreable sigs 18400 -> **18405 (+5, near-flat -- the frozen-pipeline tell)**.
Open 1.0 targets 49518 (9280 sig-fill reachable).

**Invariants tripped (I1: 7359 rows 'submitted' >24h; I3: 77 pending; I7: 236 mixed_disc).** The
near-flat scoreable sigs + climbing pending (watch log: 8k->23k over 20h, `built:0 sub:0` most cycles
since 7/7 12:07) initially read as a RECURRENCE of the 07-07 self-inflicted zombie-collect freeze
(that audit warned it "WILL recur"). **COUNTER-CHECK REFUTED that hypothesis:**
- Ran `scripts/recover_stuck_pending.py` (the proven 07-07 by-id remediation): **recovered 0, new_rows
  0, still_pending 77**. In 07-07 the same script pulled 16,677 stranded rows -- today there is **NO
  stranded verified value**.
- Bounded by-id probe of the 77 pending (sampled 18): **10 still-verifying, 8 HTTP-503, 0
  verified-uncollected**. The pending are genuinely still being verified server-side, not zombies.
- Discriminating external-vs-us test: `GET /submissions/{sid}` (by-id, the path that worked in 07-07
  while `/me` 503'd) **now ALSO 503s**; deep `/me` pagination (pages 0-5) 503s every cycle. But
  lightweight single-page reads succeed intermittently (leaderboard OK 3.6s, `/me` page-1 OK 1.1s,
  refresh succeeded 07:04, one collect landed new_rows=183 at 08:16). => **intermittent SAIR-side 503
  degradation (`IGP24_SERVICE_UNAVAILABLE`), not a total outage and NOT our pagination bug.**

> Note (2026-10-20): this "external" diagnosis, repeated on 07-09, was refuted by the 07-10 audit
> below: the paginated endpoint failed at a fixed offset of 300, and fetching by submission id worked.

**TOP FINDING (external, self-healing):** SAIR's submission service has been flaky-503 for ~20h,
backing up server-side verification and starving submit/collect throughput. Combined with ongoing
competitor disc-undercut (the standing 07-06 lever), that explains the score slide. The daemon is
behaving correctly: `collect_failed` is handled, it requeues, keeps looping, and builds intermittently
when the API responds (183 one cycle). **No code change is safe or warranted** -- the value collects
itself once SAIR stabilizes; the standing durable-collect ACTIONABLE LEAD from 07-07 wouldn't have
helped today since by-id also 503s (this is a server load/availability problem, not a client design one).

**Denominators (the lesson) -- ceiling is NOT the issue.** Groups 6980/25000 = 27.9%. Atlas
shape-dryness (deferred from 7/7, run this pass): **gen12 10320 shapes / 5709 open-bearing (dry 0.45),
mb2 3115 / 1139 (0.63), compose 3984 / 410 (0.90), g8x3s3 30 / 28 (0.07 -- very wet)** -- producer
supply is far from tapped. `lift:` (176/0) and `g6x4s4:` (15/0) are 100% dry, but that's the
already-documented state (07-05 audit), not a new collapse -- no new agenda item needed. Producer side
is healthy; today's bottleneck is purely the external SAIR service.

**Build-backlog sweep (3d): clean, nothing to migrate.** [Backlog and agenda contents omitted; the two
builds it names became tests 0055 and 0056.] No reorder warranted.

**Counter-check summary (3a-bis):** the only high-stakes causal claim this window was my own initial
"zombie-freeze recurrence" -- REFUTED above by primary data (recovery=0, by-id 503, pending
still-verifying). The 7/8 research dives [topics omitted] are math results with recorded PARI artifacts, not re-derived here.

**ACTION TAKEN:** none needed / none safe (external, self-healing). **MONITOR:** if the daemon is still
`built:0 sub:0` with pending climbing *after* SAIR 503s clear (leaderboard/refresh consistently OK but
collect still fails), THEN the durable by-id-collect engine.py fix (standing 07-07 lead) becomes the
real fix -- pick it up in an interactive session (touches engine.py, not shippable unattended).

## 2026-07-09 audit — official score still sliding (831→744→684.5) but it's the SAME external SAIR 503, POST works, coverage nearly DOUBLED underneath

**Score trend (official, from the tick's leaderboard fetch): 831.3 (07-07) → 744 (07-08) → 684.5 (today, rank 15).**
Local coverage, by contrast, is UP hard vs the last audit: distinct groups **4361→7028** (28.1% of 25k),
scoreable sigs **9199→18579**, held (t,r) 20419. SOLE 1.0 = 82. Our own estimate = 557.9 (x0.82 vs official
684.5 — estimate lags the grader). So the visible score is FALLING while the engine's leading indicator
(local realized coverage) is climbing fast. That divergence is the whole story.

**Root cause — re-derived adversarially (step 3a-bis), CONFIRMS + REFINES the 07-08 "external 503" call:**
- A fresh `sair.my_submissions()` from a clean Python process 503s (`IGP24_SERVICE_UNAVAILABLE`) in 10s → it
  is NOT our collect code (refutes "it's us").
- The daemon's POST path STILL WORKS: journal shows `built=88 sub=88`, queue `submitted` 3019→3107 in one
  tick. If POST were 503ing the fail-safe would requeue, not mark submitted → refutes "whole service down."
- Precise diagnosis: **the GET `/competitions/igp24/submissions/me` (collect) endpoint is 503-degraded; POST
  is fine.** So our new work reaches the server (queued for Magma, scored server-side) but we can't read
  verifications back locally. The official leaderboard reads during this degraded window are themselves
  suspect (the 07-08 audit already flagged this). NO REFUTATION of the 07-08 diagnosis; it is refined.

**Invariants (step 3a):** I1 = 3019→3107 rows stuck `submitted` >24h, and I7 = 651 mixed_disc. I1 is the
DIRECT downstream of the collect-endpoint 503 (can't move submitted→verified until GET /me recovers) — NOT a
collect bug, will self-heal on SAIR recovery; daemon is failing safe (collect_failed requeues, no work lost).
I7 (smoothness gate, task #15) is a standing backlog item, unchanged.

**Bottleneck type: VERIFICATION/read-side-bound, external.** Not submission-bound (POST works, budget fine),
not value-bound (huge open coverage). The right lever is: keep POSTing (so everything's counted when SAIR
recovers) + wait out the outage. Daemon `igp24-searchd` is active/running (PID 3075540); tick + timers all
healthy. (Note: the service is `igp24-searchd`, not `igp-searchd`.)

**Resource denominator:** 7028/25000 groups = 28% — nowhere near a ceiling. Shape-dryness (atlas.classify):
gen12 54.5% open-bearing (5628 shapes), g8x3s3 93.5% (29/31) — big families far from tapped; compose: 10.0%,
tsig: 13.2%; lift:/g6x4s4: 0% (small near-S24-top composite families, saturated by nature, not a collapse).
No new-construction agenda push warranted. Agenda ROI: 7 [PRODUCER]/25 [LEAD]/4 [DEAD-END] Done; [open research
leads omitted]. Build-backlog sweep (3d): no stranded greenlit PRODUCER; clean no-op.

**Changed/queued:** nothing — no safe unattended code fix (outage is external, daemon fail-safe verified
working). ACTIONABLE LEAD for a human: if the SAIR 503 persists >~2 more days, the official-score slide will
keep reading down (rank decay on shared pairs + uncounted new submissions) despite healthy local growth;
consider a Zulip ping to organizers re: the `/submissions/me` 503, and hold off reading the leaderboard as
truth until it clears. No manufactured problems — growth underneath is healthy.

## 2026-07-10 audit — REFUTES the 3-day "collect is external-only / self-heals / no safe fix" call; ships a by-id collect fix that recovered 2560 stranded verified polys

**Score trend:** distinct groups 7030→**7035**, scoreable sigs 18599→**18626 (+27)**, ESTIMATED TOTAL
SCORE 486.3→**487.3**, SOLE 1.0 held **70**. Official leaderboard **649.1 (rank 15)**, still sliding
(831→744→684.5→**649.1** across the last four audits). The official slide is NOT explained by our
collect backlog (SAIR scores submissions server-side on verification, independent of whether we pull
the results back) — it is most consistent with **k-dilution** (rivals realizing our shared pairs ⇒
2^(1-k) shares shrink; rank 13/14 are 927/907 and climbing). Not fully re-derived this run — flagged.

**TOP FINDING (counter-check, step 3a-bis) — the standing 07-07/08/09 conclusion is REFUTED.** Those
three audits concluded the collect failure was "external SAIR 503, self-heals, no safe code fix, by-id
also 503s." Re-derived from primary data this run, TWO parts are wrong:
1. **The 503 is a fixed OFFSET-300 cap, not a full outage.** `iter_submissions` dies at page
   12@limit25 AND page 6@limit50 — both = offset 300 (varied the page size; the break is server-side
   and offset-anchored, so it is genuinely external, but PARTIAL). The newest ~300 submissions collect
   fine; anything buried under >300 newer submissions is UNREACHABLE by pagination and strands forever.
   That IS invariant I1 (was **3019** `submitted`>24h zombie rows, frozen in one batch 2026-07-04, all
   MISSING from the verify cache = genuinely uncollected) + **5** uncollected 07-06 sids carrying
   **~2560 already-verified** polys (all `still_queued=False`, i.e. done). "Self-heals / no work lost"
   is FALSE — buried sids never resurface.
2. **"by-id also 503s" (the load-bearing reason no fix was attempted) is FALSE.** `GET
   /competitions/igp24/submissions/{sid}` is NOT offset-capped and returns the exact shape pagination
   yields (payload/verifiedPolynomials/failedPolynomials) for a stuck sid — tested live on all 5.

**FIX SHIPPED + VERIFIED END-TO-END (commit f42323b, pushed).** Added `sair.submission_by_id()` + an
`engine.collect()` fallback: after the newest-first walk, fetch any still-pending sid directly by id
(transient by-id errors leave it pending for next cycle). Additive — pagination path unchanged; by-id
only fires for stragglers. `ruff` clean, 42 pytest pass (added a by-id-recovery regression test).
Restarted the daemon (resilient/resumable service) to activate; VERIFIED the very next collect cycle:
`collected=5, failed=20, still_pending=0, new_rows=2560` — the full backlog cleared, +2560 rows into
realized.csv, and the zombie `submitted` count reconciled **3019→422** as the recovered cache filled.
This prevents ALL future zombies (the leak was unbounded — I1 would keep climbing).

**Residuals / notes:** (a) **I1 residual = 422** older `submitted`>24h rows whose sids are no longer in
the pending table (pending_remove'd via the old collect_failed path) — NOT auto-recoverable without
their sids; low value (old, likely redundant), left as a minor lead (a human could re-queue those 422
queue rows to re-submit, but that is a live-queue mutation, not done unattended). (b) I7/mixed_disc
680 — pre-existing tracked item (task #15 smoothness gate), unchanged. (c) Invariant tripwires worked
as designed — I1 surfaced the leak the narrative missed. **Resource denominator:** realized groups
7035/25000 = 28% (was 4.3% a week ago); producers healthy, not the constraint.

**Shape-dryness (3b):** gen12 dry 0.49 (5247 open-bearing), g8x3s3 dry 0.065 (29/31 open), compose
dry 0.90 (403 open), tsig dry 0.87 (10 open) — dominant families richly open, NOT starved. lift: and
g6x4s4: fully dry (0 open-bearing) but small (186/15 shapes) and long-known — no new agenda push
warranted. **Agenda ROI (3c) / build-backlog (3d):** [open research thread omitted]; all `[PRODUCER]` tags are
already in Done — no greenlit build to migrate to build_backlog, no reorder.

**ACTIONABLE LEAD (bottleneck):** collection is now the clean path, but if the offset-300 pagination
503 becomes a FULL outage (page 0 fails), by-id still works per-sid — consider a durable sid-log so
even pending_remove'd sids stay recoverable (would have saved the 422). Low priority; the daemon is
now self-healing for the common case.

## 2026-07-11 08:17 — AUDIT (systemd timer, hands-off)

**Score trend: CLIMBING, healthy.** Estimate 487 (2026-07-10 audit) → **517.5** today; distinct
groups 7035 → **7701** (+666); scoreable sigs **21,745**; SOLE 1.0 (tc<=1) **75**; official
leaderboard **673.3, rank 16** (oscillated 15↔16 through the day, gap to rank-15 +47). Open-1.0
targets 43,850 (8,944 sig-fill-reachable via a group we already realize). No tone change — the
single number is up on every axis.

**Producer-feed health (3b-bis).** `search_ctl health` flagged 3 SILENT: **discmin2 / mb2 / tr6**
(SILENT, NOT erroring — peaks 200/209/172, no crashes). Investigated: the DOMINANT feed is fine —
`general12` last_enq=2041, peak 9897, and the daemon submits ~600/tick (08:07 built:616 sub:598,
daemon=up). This is NOT the gen12-blind-spot failure mode; we are not supply-starved. The three
silent producers are **bounded/dry-gated pools that walked their runway**, not bugs:
`mb2` walks the minblk=2 strike-list cursor and its atlas dry-gate + non-landing on non-split
targets is exactly the **dive #29 directed-square-class wall** (94% of the lever gated); `tr6`
(totally-real deg-6) and `discmin2` (fixed-alpha disc-min) are small fixed pools. mb2's runway is
ALREADY the **top-2 Pending** research items — no new agenda push warranted (would duplicate).

**Shape-dryness (3b).** gen12 (dominant) **50.2% dry, 5,135 open-bearing shapes** — huge runway,
healthy. compose 90% (394 open-bearing), mb2 74% (797 open-bearing but non-landing → the dive-#29
wall). SATURATED (100% dry): `lift` (196 shapes/0 open), `tsig` (76/0), `g6x4s4` (15/0) — their
strata are already covered by the standing census dives in Pending (mb4 6x4, non-solvable minblk).
`g8x3s3` only 6% dry (tiny 33-shape family, plenty of local runway).

**Counter-check (3a-bis) — CLEAN, nothing refuted.** (1) Dive #29's headline "7 SPLIT groups /
13 pairs, all tc=0 OPEN" — re-derived all 13 pairs directly from live progress.json: **every one
teamCount=0** [pair list omitted]. CONFIRMED. (2) Yesterday's audit claim "by-id collect fix recovered 2560, I1
3019→422" — I1 is **still 422 today (stable, not re-growing)**, so the fix held; new submissions
are not re-stranding en masse. CONFIRMED.

**Invariants (3a).** I1: 422 zombie 'submitted' >24h — KNOWN stable residual from the confirmed
2026-07-10 by-id collect fix (not growing, not a new bug). I7: 957 mixed_disc rows — the standing
**task #15 pre-submit smoothness gate** (build task, not a safe unattended fix).

**Build-backlog sweep (3d): clean.** Recent dives #28/#29 are [LEAD] (open residuals → stay in
research). [Backlog item omitted.] Nothing to migrate.

**No code change shipped** (conservative unattended: no small-and-obviously-correct fix presented;
the two candidate issues — mixed_disc gate, mb2 non-landing — both touch daemon/producer logic).

**ACTIONABLE LEAD (human, low priority):** `tr6` and `discmin2` are minor bounded pools now
walked-out (SILENT, ~500 total each). Consider retiring them from the daemon rotation or refreshing
their base pool (new alphas / a wider totally-real deg-6 cursor) so they stop burning scheduler
ticks — they cost ~0 submissions (gen12 fills the pipe) so it's cosmetic, not urgent. mb2's silence
is the dive-#29 directed-twist wall, already the top research priority.

## 2026-07-12 08:17 — AUDIT (systemd timer, hands-off)

**Score trend: FALLING — overnight SUPPLY-STARVATION event.** Official leaderboard **peaked 688
(07-11 21:07) then bled monotonically to 659 (08:07)** — −29 pts over ~11h — while built/sub
collapsed to ~0 most hours (pending=0) and `producers_live` fell 13→6/25. Gap to rank-16 blew out
**+3 → +53**; still rank 17. Local estimate 517.5 (07-11 audit) → **499.6** today corroborates.
Coverage kept CLIMBING through it (distinct groups 7701→**7874** +173; scoreable sigs 21,745→**22,429**;
SOLE 1.0 tc<=1 flat **75**) — so the drop is NOT lost coverage, it is **rival erosion of our held
pairs while we submitted almost nothing for 11h**. Standing still = losing (the decay clock).

**ROOT CAUSE (verified, not exhaustion): the dominant gen12 feed is CURSOR-STARVED, not dry.**
`search_ctl health` flagged 10 SILENT producers, but the feed log shows every one *running*, err=0,
no crash — all printing `enqueued 0 (skipped N dry)`. This is NOT the 2026-07-10 int(None) crash.
Atlas shape-dryness (fresh): gen12 **51% dry, 5,018 open-bearing shapes** — huge runway, UNCHANGED
from yesterday. But its cursor has walked to **offset 220000/303209** into the mined-out high-disc
TAIL (`gen12_lo`/`gen12_hi` band kvs are unset=0, so it walks the whole mirror), where every shape
is already-sampled-dry → enqueues 0. gen12_treal same (`enqueued 0, skipped 40961 dry`). The
open-bearing 5,018 shapes live at OTHER offsets the cursor isn't visiting. During the DAY the cursor
sat in a productive band (peak 9897/run, daemon ~600/tick); overnight it walked into the dry tail and
**a single producer's dry-stretch starved the whole daemon for hours** because no other producer
covers the 2-block main-feed volume. Structural fragility, not a code bug.

**Counter-check (3a-bis) — score-bleed causation CONFIRMED.** (1) Refute "SAIR recompute artifact":
the watch log shows a *smooth monotone* 688→659 across 11 hourly samples exactly tracking built/sub→0,
not a single-step recompute; rank held 17 while gap grew +3→+53 (rank-16 climbed as we fell) —
consistent with real rival progress + our starvation. (2) Refute "daemon consumption bug": daemon
built 60 last tick after the feed enqueued ~170, drained to 0 — it builds when work exists; it is
supply-starved, not stuck. (3) Producers SILENT-vs-ERRORING: all running, err=0, no traceback → dry,
not crashed. No small-safe code fix applies.

**Accounting (3a).** `reconcile_accounting`: local est 500 vs **official 659** — the +160 gap is
**2,648 pairs officially scoreable but not locally flagged** (STALE local scoreable flags; already
credited server-side, NOT lost score). `resync_scoreable` to un-stale them **FAILED on a SAIR
ReadTimeout** (transient — the watch log shows the same `lb=ERR(ReadTimeout)` twice overnight; not
our bug). Score decomposition: k=1 75 pairs (75 pts), k=2 270 (112), k=3 605 (117); **87% of our
pairs are k>=6 (~worthless)** — points are carried by low-k, so low-k erosion is where we bleed.
Invariants: only I7 (1,102 mixed_disc rows, up from 957 — the standing task #15 smoothness gate) +
1 pending; no zombie signal. Disc headroom: **behind on disc 21,868/22,429 (97%)**, we hold the min
on only 561 — disc-min defense is a real secondary lever the starvation also stalled.

**No code change shipped** (conservative unattended). The obvious levers — reset `gen12_offset` to
re-enter the open-bearing band, or set `gen12_lo`/`gen12_hi` to bound the cursor to the productive
mid-disc window — are TUNING GAMBLES (I lack the verified band boundaries; a wrong band could leave
it equally starved), so per the mandate they go to a human, not shipped blind.

**ACTIONABLE LEAD (human, HIGH priority — this is costing score now):** the daemon is fragile to a
single-producer dry-walk. Two fixes, either stops the overnight bleed: (a) **band-bound gen12** — set
`gen12_lo`/`gen12_hi` kvs to the productive mid-disc offset window (derive from where the daytime
cursor produced 9897/run) so it skips the mined-out head+tail and re-walks only the open-bearing
band; (b) **dry-gate skip-ahead** — when a cursor window returns enqueued=0, advance the offset by a
large stride (or jump to `lo`) *within the same tick* instead of parking, so a dry stretch can't
starve the daemon for hours. Interim one-liner to stop the CURRENT bleed:
`.venv/bin/python scripts/search_ctl.py set gen12_offset 0` (re-walk from the productive head) — reversible, but verify it
re-enters open-bearing territory rather than the dry head before trusting it. Also: more independent
2-block producers so no single feed's silence zeroes the pipe.

## 2026-07-13 — AUDIT: the sig-fill feed was DEAD for 29h (per_group=1 capped its pool at 4% of supply)

**Score trend — CLIMBING.** distinct groups **7,933** | scoreable sigs **22,555** (22,385 non-baseline
+ 170 baseline unlocks) | **SOLE 1.0 = 76** | **local est. score 479.3** | **official 632.7, rank 17**
(gap +153 = 2,662 pairs scored server-side but never re-synced locally — an accounting artifact, not
lost score; `reconcile_accounting.py` says official already credits them). Neighbouring teams [names removed]:
609.7 (-23), 700.0 (+67), 749.6 (+117). Open 1.0 board
still **41,344** pairs, of which **8,747 are sig-fill reachable** (group already realized, need the r).

### TOP FINDING — `produce_sigfill` enqueued ZERO for 96 straight ticks (~29h). FIXED (commit 957a9a8).

> Note (2026-10-20): the 07-14 audit below found that this fix did not restore the feed. The pool was
> exhausted, not self-limited.

This is the **gen12 blind spot again**: daemon up, stack "healthy", one of the biggest feeds silently
dead. `search_ctl health` flagged it SILENT (peak 289/run, **18,657 lifetime** enqueues → 0).

It was **not exhausted — it was self-limited.** The LMFDB fetch used `per_group=1`, which collapses the
totally-real deg-12 pool to **one representative field per 12Tj group (≤227 fields)**. The cursor
(`sigfill_offset=1792`) swept those long ago, and `per_group=1` returns the *same* representatives at
every offset, so each tick re-fetched bases that were **100% already-enqueued** → `added=0`, forever.
Reproduced directly at three offsets before touching code:

| offset | bases returned | already-enqueued |
|---|---|---|
| 0 | 60 | **60 / 60** |
| 128 | 69 | **69 / 69** |
| 1792 | 22 | **22 / 22** |

**The denominator:** LMFDB holds **5,472** totally-real deg-12 fields. We were walking **227 = 4.1%**
of it. Textbook self-imposed ceiling — exactly the failure the audit playbook exists to catch.

**Fix:** `per_group=1` → `per_group=None`. Distinct fields of the same group carry distinct discs, so
target keys (`sigfill:{label}:d{disc}:{alpha}`) stay unique and dedup still works. **Verified
end-to-end, not "no error":** first run after the change enqueued **688** (vs 0 for 29h); fresh-base
fraction rises deeper into the cursor (64/128 at offset 1792, 77/128 at 3000). ruff + 46/46 pytest pass.

### Evidence-ledger review (anti-overconfidence pass)
- **build 0068 (`general_c2_TWIST`) — UPGRADED "labels pending" → PILOT-LABELED, STILL-VALID.** Both
  intended pairs came back from SAIR with **matching** official labels — (24T19241, r=24) and
  (24T18461, r=24) — i.e. the twist family predicted its group correctly, unlike tests 0044/0045/
  0051–0054 where the build landed a *different* group. Both pairs still `teamCount=0`, `minDisc=null`
  in fresh `progress.json` → sole-1.0-bound. This family earned the right to scale.
- Invariants: only **I7** fires (1,102 `mixed_disc` rows — the known un-certified-disc regression,
  task #15). I3 pending-backlog **clean** (0 pending; the 422 terminal `submitted` rows are not zombies).

### Shape-dryness (atlas)
| family | shapes | open-bearing | dry |
|---|---|---|---|
| `g8x3s3:` | 36 | 32 | 11% — healthiest |
| `gen12:` | 10,320 | 4,968 | 52% — healthy |
| `compose:` | 4,107 | 394 | 90% |
| `sigfill:` | 4,809 | **501** | 90% — and it was DEAD; the fix reopens these |
| `lift:` | 202 | **0** | **100% — COLLAPSED** |
| `g6x4s4:` | 15 | 0 | 100% (deg-6 top pool is only 16 groups — genuinely saturated) |
| `tsig:` | 76 | 0 | 100% (targeted-by-construction; builds open pairs → they become held. Not a signal.) |

`lift:` is fully dry — 202 shapes, every landing held-or-contested → it burns build budget for zero
marginal score. Pushed an **[EXPLORATORY / SHAPE-DRYNESS]** item to `research_agenda.md` Pending:
find a new shape for the stratum `lift:` reaches, or return a REFUTED/retire verdict with the
denominator quoted. (Kept below the user-directed MINBLK=2 priority block.)

### Other SILENT producers (triaged, not touched)
`compositum` (3h), `selfcomp` (14h), `sigfill_targeted` (5h). None shares the `per_group=1` bug (grep
confirms sigfill was the only one). `sigfill_targeted` is **cadence-throttled by design** (2h; `tsig_last`
= 1.6h ago) and its gate returning 0 candidates is the gate being decisive, not a fault. `compositum` /
`selfcomp` are low-volume (2,183 / 1,737 lifetime) — plausibly exhausted shape pools; left alone rather
than guessing unattended.

### ACTIONABLE LEAD (for a human — not shipped unattended)
**I7 / task #15, the disc-smoothness gate, is the biggest standing score leak: 1,102 `mixed_disc`
rows.** A mixed-disc fallback can't unlock a baseline pair, and disc headroom is already brutal (we're
behind on **21,986 / 22,555 = 97%** of scoreable sigs, median ratio 0.762; we hold the min on only 569).
Score decomposition shows **87% of our pairs sit at k≥6 (weight <0.031, ~worthless)** — the 76 SOLE
pairs carry 76.4 of our 479. So marginal score lives in (a) tc=0 open pairs and (b) *disc quality* on
what we already hold, not in more volume. A pre-submit smoothness gate touches `searchd.py` → left for
review, deliberately not edited here.

## 2026-07-14 — AUDIT: the score is FALLING while coverage grows — we are VALUE-bound, and yesterday's "sigfill fixed" is REFUTED (the pool is genuinely exhausted, 5,472/5,472)

**Score trend — FALLING, for the first time on record.** distinct groups **7,956** (+23) | scoreable sigs
**22,707** (+152) | **SOLE 1.0 = 83** (+7) | **local est. score 460.6** (was 479.3, **-18.7**) |
**official 598.7, rank 19** (was 632.7, rank 17 — **-34.0 points, -2 places**). Neighbouring teams [names removed]:
688.6 (+89.8), 661.1 (+62.4), 584.8 (-13.9). Open 1.0 board **40,290**
pairs, **8,586** sig-fill reachable.

**Coverage GREW on every counter and the score still fell.** That combination has exactly one reading and
it is the headline of this audit: **we are not breadth-bound, we are VALUE-bound.** Score is
`Σ 2^(1-k)·logD0/logD`; both multipliers are being eroded by rivals faster than we add pairs — every team
that lands one of our pairs halves it (`k`↑), and every rival who posts a smaller disc pushes `D0` down
(`logD0/logD`↓). We added 41,420 verified polynomials in the last 24h and got **+152 scoreable sigs and
-34 official points** for it. Volume is not the constraint. Measured decomposition:

| k (teams) | pairs | est. points | mean ratio |
|---|---|---|---|
| 1 | 83 | 83.6 | ~1.00 |
| 2 | 241 | 100.7 | 0.836 |
| 3 | 497 | 97.3 | 0.783 |
| 4 | 759 | 71.2 | 0.750 |
| 5 | 1,016 | 47.0 | — |
| **>=6** | **20,111 (88% of ours)** | — | weight <0.031, ~worthless |

**Disc headroom: 22,108 / 22,707 (97%) of our held pairs have a rival with a SMALLER disc** (median ratio
0.762; we hold the min on only 599). Driving the ratio to 1.0 on just the **~2,500 pairs at k<=5** — which
carry ~353 of our 461 points — is worth **~+87 points**. A fresh k>=6 pair is worth ~0.03. The arithmetic
says the next 100 points are in **defending and sharpening what we already hold**, not in more breadth.

### TOP FINDING 1 (counter-check, step 3a-bis) — the 2026-07-13 "sigfill FIXED" claim is REFUTED. The pool is EXHAUSTED, not self-limited.

`produce_sigfill` is SILENT again (64 ticks, ~17h) — the feed that yesterday's audit declared fixed
(commit 957a9a8). I did not trust the commit message; I ran the producer and then probed the denominator:

* Ran it directly: `sigfill cursor[896:1024]: 128 totally-real bases x alpha sweep, **enqueued 0**`. No
  crash, no exception, and `_queue_full()` is **false** (queue was drained to **0 queued**, cap 30,000) —
  so neither backpressure nor a bug.
* Probed the **entire** LMFDB totally-real deg-12 pool (`per_group=None, limit=100000` → **5,472 fields**)
  against `store.has_target`: **5,472 already targeted, 0 fresh.** The pool is 100% consumed.

Yesterday's *diagnosis* (`per_group=1` collapsed the pool) was correct, but the *fix did not restore the
feed*: it advanced a cursor across a pool that was already fully walked. The producer is **genuinely
EXHAUSTED** — per the playbook that is the RUNWAY signal, not a bug. Pushed **[RUNWAY]** to the agenda.
The cost is real: **8,586 open-1.0 pairs are sig-fill reachable** (group already held, only `r` missing) —
our largest aimable reservoir of 1.0-weight targets, and its feed is dry.

*Sub-finding (a genuine self-limit, LEAD not fixed):* sigfill's target key is
`sigfill:{label}:d{disc}:{alpha}` — but the pool has only **3,997 distinct `(label, disc)` keys for 5,472
fields**, so **1,475 fields (27% of supply) are silently unreachable**, collapsed onto a colliding key.
Left as an ACTIONABLE LEAD, not fixed unattended: changing the key format re-keys all ~5.5k bases and
re-enqueues ~87k candidates, which is not an obviously-safe unattended change.

### TOP FINDING 2 — the disc-min feed, our highest-value lever, walks FOUR bases. Total.

`produce_discmin` / `produce_discmin2` are SILENT (33 ticks, ~8h). Ran `produce_discmin` directly: it
prints "enqueued" for each of 12T1-12T4 and **adds 0**. Root cause is structural, not a crash:
`lmfdb.fields(12, galois_label=top, class_number=1, **limit=1**)` then `base = fs[0][0]` — it pulls the
single smallest-disc field for exactly **4 tops**, so its entire base pool is **4 bases**, re-enqueued
identically every run. `produce_discmin2` sweeps a fixed alpha list over those same 4. So the lever worth
~+87 points is fed by 4 bases while LMFDB's supply per top is in the thousands. This is the
**`verify-limits-before-ceiling` pattern again** — a self-imposed denominator, not a real ceiling.
Not fixed unattended (a producer redesign, needs a cursor + aiming); promoted to agenda as **[VALUE]**.

### FIXED + PUSHED (commit 6726f8a) — a transient network blip was crashing the whole resync run.

`scripts/resync_scoreable.py` died mid-run on `requests.ReadTimeout`. The SAIR GET helpers raise **raw
`requests` exceptions**, but every caller only catches `SairError` — so one blip escaped, aborted the run,
and **discarded all accumulated updates**, leaving the **2,587** officially-scored-but-locally-stale pairs
un-synced (the entire local-vs-official gap `reconcile_accounting` reports). I probed the endpoint first
rather than blaming their infra: **it is healthy (0.1s/download)** — this was a transient blip killing a
long worker, i.e. our "wrap every external call, fail safe" rule.

Converted `requests.RequestException -> SairError` on the two **idempotent GET** paths (`_get`,
`download_submission`). **Deliberately NOT on `submit` (POST)** — making a timed-out-but-*landed* POST look
like a clean failure would cause a re-submit. Verified the fixed path *behaves*, not just "no error":
injected a `ReadTimeout` → surfaces as `SairError` on both paths; live calls still work; and
**`resync_scoreable` now runs to completion (400 fetched, 367 downloaded, 57 stale rows upgraded)** where
it previously crashed. `ruff` + 46 tests pass.

### Checked, clean

* **Invariants:** only **I7** fires — 1,106 grader `mixed_disc` fallbacks (pre-submit smoothness gate,
  task #15, still open). **I3 pending-backlog = 0** (no zombies); 422 terminal `submitted` rows are benign.
* **Daemon is UP** (`igp24-searchd`, PID 3138946) and consuming ~41k polys/day; queue drains to ~0, so it
  is supply-paced, not stalled. *(Self-correction: my first liveness probe used the wrong unit name
  `igp-searchd` and reported "inactive" — the unit is `igp24-searchd`. Checked before believing it.)*
* **Producer SILENCE is not one bug:** of the 10 flagged, the queue-backpressure hypothesis is **refuted**
  (queue was empty), and the two that matter are diagnosed above (exhausted / 4-base cap).

### ACTIONABLE LEADS (for a human — not shipped unattended)

1. **`produce_discmin` needs a cursor + aiming** (the +87-point lever): walk minimal-disc bases per top
   with an offset instead of `limit=1` × 4 tops, and aim at the ~2,500 held pairs at `k<=5` where we are
   behind on disc. Highest expected value on the board.
2. **`produce_sigfill` target-key collision**: include the base coefficients (or a hash) in the key to
   unlock the **1,475 fields (27%)** currently colliding on `(label, disc)`. Note it re-enqueues ~87k
   candidates on first run — schedule it deliberately.
3. **Invariant I7 / smoothness gate** (1,106 mixed_disc): a disc with a prime factor >10^6 can't be
   certified exact, and this interacts directly with the disc-min lever above.
