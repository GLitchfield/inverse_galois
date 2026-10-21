---
name: igp-audit
description: IGP24 downtime self-scrutiny + deeper-research pass. Run periodically while the search daemon runs autonomously — audit assumptions/limits/metrics/budget against LIVE data, re-derive stale conclusions, do one rotating research dive, then report + fix quick wins. Use when invoked by the audit cron, when the user asks for a self-review/audit, or proactively during idle time.
---

# IGP24 self-audit + research playbook

Purpose: turn the daemon's downtime into productive self-scrutiny. Born from a real failure pattern —
I declared a "construction-method ceiling" / "disc-min tapped" / "predictor contested" THREE times
while the producers were quietly pulling **0.5% of the available bases** (limit=1000 of LMFDB's
100k+). The score was climbing the whole time. **Trust the score trend over a-priori "this is
saturated / contested / hard" arguments, and measure the resource denominator before ever saying
"diminishing returns."** (See `docs/project_review_2026-06-30.md`, memory `verify-limits-before-ceiling`.)

Work top-to-bottom. Be data-grounded and honest; a clean "nothing actionable, growth is healthy" is
a fine outcome. Don't spawn multi-agent research fan-out (direct WebSearch/WebFetch is fine). Keep
the daemon running; pause it only for a clean `realized.csv` commit (stop → commit → start).

## 1. Refresh live state, read the trend
- `search_ctl refresh` if `progress.json` is >12h old; then `analyze_coverage`.
- Record: distinct groups, scoreable sigs, **SOLE 1.0 (teamCount<=1)**, **ESTIMATED TOTAL SCORE**,
  open-1.0 targets. Compare to the last audit's commentary entry — **is the score climbing,
  flat, or falling?** That single number decides the tone of the whole audit.

## 2. Resource-denominator audit (THE lesson — do this every time)
For every belief of the form "we're near the ceiling / X is tapped / diminishing returns," MEASURE
available-vs-used and quote the fraction:
- LMFDB field supply per degree (`lmfdb.fields(d, per_group=None, limit=100000)` → it caps at 100k,
  so "at least 100k") vs the cursor offsets (`gen12_offset`, `c8x3_offset`) — how much have we walked?
- reachable groups (e.g. deg-d transitive-group count × kernels) vs realized; 1080/25000 = 4.3% today.
- If we're using a tiny slice, the ceiling is self-imposed → expand (raise a cursor, add a shape).

## 3. Metric sanity
- Headline = **estimated total score** (Σ 2^(1-k)·logD0/logD, baseline-capped). SOLE = held ∧
  teamCount<=1 (1=us, 0=submission-lag); teamCount==0 ≠ sole (it = nobody-credited / open target).
- Coverage is distinct (t,r), never row counts. Confirm any number you're about to headline is the
  unit that actually scores.

## 4. Self-limit hunt
`grep -nE "limit=|per_group=|per_run=|cap=|[:][0-9]+]|range\(|hi=|max_" scripts/search_ctl.py
scripts/searchd.py` — flag any hardcoded cap that bounds coverage. Which shapes have MANY tops
(deg-12: 301, deg-8: 50) and deserve a cursor vs FEW (deg-6: 16, saturated) and don't?

## 5. Budget allocation + bottleneck type
- Where does verification go? Verified realized rows by producer (`rank.producer_of_source`). Is the
  budget on high-sole-yield (tsig, open-top harvest) or low-yield (contested/dup floods)?
- Bottleneck type: posts/day vs the 1000 cap (submission-bound?); `sair.my_submissions` still-verifying
  count + fetch time (verification-bound? collect() slow?); new-scoreable-sigs/day vs submitted/day
  (value-bound?). The right lever differs for each — don't add volume if value-bound.

## 6. Re-open conclusions reached on stale/capped data
List the project's standing "it's hard / contested / tapped" conclusions (disc-min headroom, the
non-Galois predictor, the explicit-family frontier) and ask: were they measured on a now-obsolete
(capped) search space? Re-derive the one most likely to have flipped.

## 7. One rotating research dive (pick the next, note it in commentary)
(a) literature for the hard non-solvable/primitive residual — explicit Q(t) families beyond M24
(check teamCount FIRST: famous ≠ open); (b) a construction/block shape not yet built; (c) disc-min
methods; (d) LMFDB / external-DB mining angles. Direct WebSearch/WebFetch; capture findings (with
citations) in `docs/exploration_backlog.md`.

## 8. Output (always)
- Record via the **Edit/Write tools, NOT shell `cat >>`** (shell append isn't pre-approved; Edit/Write
  on the repo IS — so this runs unattended). **Append to `docs/auto_log.md`**: Edit it — old_string =
  the `<!-- AUTOLOG-MARKER ... -->` line, new_string = your dated entry (score trend, what you
  checked, found, changed/queued) + the marker. Don't touch the curated docs (commentary etc. are
  human-curated from the log). If a designed experiment, add a numbered `docs/tests/NNNN-*.md`.
- **Code fixes — be conservative when unattended.** Apply ONLY small, safe, obviously-correct changes
  (a constant, a kv value, a doc), and only if `ruff` + `pytest` pass; commit granular (never
  `--no-verify`) + push. **Queue anything risky or non-trivial (esp. changes to `searchd.py`/the live
  daemon) as a TASK instead of editing** — don't ship unreviewed code into the 24/7 system. Update
  CLAUDE.md/README if project-state facts changed.
- End with a 2-3 line report: score trend, top finding, action taken/queued.
