# Project review / optimization pass — 2026-06-30

Commissioned after the gen12 base-supply miss ("it seems like there's a whole pipeline missing").
Reviews the running system for self-limits, misallocated effort, throughput, and — bluntly — for
my own repeated premature "ceiling" calls.

## Headline: the base-supply unlock is paying off, and we are NOT near a ceiling

We had been pulling ~481 of LMFDB's **100k+** degree-12 fields (~0.5%); producers were self-limited
(`limit=1000`, small `per_group`). After converting the high-top-count shapes to **cursors** over the
full mirror (gen12/deg-12/301 tops, 8x3/deg-8/50 tops), in the **few hours** of this thread:

| metric | start of thread | now | Δ |
|---|---|---|---|
| distinct groups | 621 | **1080** | +459 |
| scoreable signatures | 734 | **1487** | +753 |
| SOLE 1.0 held (teamCount<=1) | 44 | **59** | +15 |
| **estimated total score** | 72.9 | **122.9** | **+50** |

1080/25,000 groups = **4.3%** — vast headroom. The cursors keep walking into new (often open) tops,
and it converts to **sole 1.0s + score**, not just the groups headline. This is a high-growth phase.

## Throughput: headroom on both ends (NOT the constraint)

- **Submission:** ~100 POSTs/day vs the **1000/day** cap → 10x headroom.
- **Verification:** Magma keeps up — `my_submissions` = 359 subs, **0 still-verifying**, 4s to fetch
  (so `collect()` is cheap, not a cycle bottleneck).
- **Cycle:** ~4-7 min, dominated by *building* 1000 candidates (bnfinit-heavy general_c2/compositum)
  in the 10-thread pool — the only real throughput lever, and only worth pulling once the cursor
  backlog is the limiter (it isn't yet — Magma keeps up). `build_workers` could rise 10 -> ~14 on the
  24-core box IF we become throughput-bound, but each gp can spike to ~2GB (parisizemax), so 16+
  risks the 31GB box; leave at 10 for now.

So we can run the cursors full-tilt; the self-pacing `queue_cap` (30k) keeps the queue bounded.

## The meta-finding (the important one)

**Three times this stretch I called a ceiling that wasn't there** — "near the construction-method
ceiling," "disc-min tapped," "value-bound." All were computed on a search space capped at 0.5% of
the bases. The data (score climbing 73->123) is the truth; my analysis on the capped space was not.
Lesson (saved to memory `verify-limits-before-ceiling`): **measure the available-resource denominator
before declaring diminishing returns**, and trust the score trend over a priori "this is contested /
saturated / hard" arguments. The corollary: conclusions reached on the capped space need re-deriving
now — see "re-open" below.

## Findings + prioritized recommendations

**Done this pass:**
- Cursors for gen12 (deg-12) + 8x3 (deg-8); self-pacing `queue_cap`; reverted the 6x4 cursor
  (deg-6 = only 16 tops, saturated — cursoring it adds no groups + worsens disc).
- Fixed the teamCount metric (test 0039) + added estimated-total-score as the headline.

**R1 (high) — sustain + direct the cursor growth.** It's the engine. Let it walk; watch the score
trend + the usable-rate (rarer tops have larger |H| -> fewer split primes within `hi`; bump `hi`
or accept the drop). The eventual real ceiling is the tower-reachable group set (~a few thousand of
25k) + the primitive/non-solvable residual (explicit families, contested — M24-style).

**R2 (medium) — re-open the conclusions reached on the capped space.** With the full supply:
- disc-min: more bases/top now arrive automatically -> the builder keeps smaller mins; re-measure
  the headroom (it was sized on the capped data).
- the non-Galois predictor (test 0038, "contested"): the contested-ness was measured on the common
  tops; the cursor reaches rarer tops that may be open. Re-check whether a predictor would now gate
  toward open pairs (still bounded by the alignment wall for |S|>=2, but worth a fresh look).

**R3 (medium) — value-per-submission.** We submit ~100k distinct polys/day; only ~hundreds become
new scoreable sigs. As throughput headroom shrinks (backlog growth), prioritise NEW-top bases (skip
bases whose top is already well-covered) and keep tsig/targeted always-funded (it's the pure sole-1.0
engine but supply-bound — 43 verified rows total).

**R4 (low) — cleanups / minor.** `_diverse_deg8_bases` is now dead (size3_compositum cursors LMFDB);
add more cyclic cubics to 8x3 for signature variety; quad/pent/tri dominate realized.csv (~10.7k
rows) but are denylisted — harmless, just noise in row counts (distinct-sig is the real metric).

**Watch items:** queue growth vs `queue_cap`; RAM with 16 build workers (each gp ≤2GB cap, ~12GB
typical — fine on 31GB); the stale-`submitted` status rows (sync gap, cosmetic).

## Bottom line

The system is healthy, resilient (systemd + recovery), and — crucially — **in a high-growth phase
from the base-supply unlock, not at a ceiling.** The single best action is to let the cursors run and
watch the score climb, re-deriving the "hard frontier" conclusions once growth actually plateaus.
