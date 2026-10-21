# 0051 — gen12 field-disc DEFENSE: rebuild behind pairs over smaller-disc bases

**Family:** disc-defense (self-competition) over the `gen12` = general_c2 producer.
**Date:** 2026-07-07. **Depends on:** the `defend_held.py` diagnosis (ranked recoverable loss),
test 0036 (split prime is the `r`-dial), `produce_general12`/`produce_harden` (the machinery reused).
**Question:** Our score slipped (828 → 824.7) because rivals hold SMALLER FIELD discs than us on
shared pairs. `defend_held.py` found ~150 recoverable points, 137 (91%) of them in `gen12`-produced
pairs concentrated at teamCount `k=2/3/4`, with massive disc gaps (24T20054 r12: our 74-digit field
disc vs rival min 34; ratio 0.454). Can we programmatically rebuild those pairs over genuinely
SMALLER-disc degree-12 bases of the SAME top group, at the SMALLEST split primes, and produce
strictly-smaller field discs — recovering the loss?

**VERDICT: NO (as designed). BLOCKED by label variance — do not integrate.** Building a smaller FIELD
over the same top at the right `r` works (705 built, 392 Magma-verified, `r` always correct), but the
`24Tt` is NOT preserved: **0/390** verified models hit the intended pair (the same `w`-index selects a
different kernel submodule per base — `idealprimedec` order isn't canonical; test 0038's alignment
problem, base-dependent + non-invertible). Net incidental value ≈21 disc-improvements + 7 low-value
new pairs on OTHER groups. The `defend_producer.py` machinery (source→(top,w) recovery, totally-real
`r`-dial pool, batched `bnfinit` sweep) is reusable; the targeted single-`w` gate is the wrong design.
See "OUTCOME" below for the fix (harvest-broad-`w` + post-hoc Magma filter, i.e. fold into
`produce_selfcomp`). **Self-corrected an initial "~20.7 points recovered" over-claim via the
`realized.csv` counter-check.**

## Why it *looked* recoverable (mechanism — the premise that broke)

`gen12` = `general_c2`: a degree-24 field `K = F(√α)` is a C₂-kernel extension over a degree-12 base
`F`. The **scoring disc is the FIELD disc** (`nfdisc`), driven mainly by the BASE disc:
`disc(K) ≈ disc(F)² · Norm(relative disc)`. `gen12` cursors LMFDB by smallest disc but takes the
**first base hit** for a given top and a **lazy large split prime** (idealprimedec order, q often in
the thousands), so the recorded model is frequently over a large-disc base. A **much smaller-disc
degree-12 base of the SAME top group `12Tj`**, built at the **smallest** completely-split prime,
realizes the same `24Tt` with a far smaller field disc. Critically, the field disc is **invariant
under polredabs** — so "smaller model" means a genuinely SMALLER FIELD (smaller base / smaller
ramification), NOT a reduced representative of the same field.

## Recovery path (simpler than the queue-payload route)

Each held `gen12` row's `source` already encodes everything needed:
`daemon:gen12:12T227:d<basedisc>:q<prime>:110110000000`. We parse the **top `12Tj`** and the
length-12 binary **kernel w-pattern** directly from the source string — **no queue-payload lookup
needed** (`produce_harden` recovers the old base from the queue; here we DISCARD the old base and pull
fresh small ones by label, so we only need the top + w). Then:

1. `defend_held.load()` → behind pairs (ratio<1); keep **family==gen12**, **k∈{2..5}**, weight≥0.06,
   rank by recoverable loss `weight·(1−ratio)`, cap top 400.
2. Pull the **smallest-disc LMFDB degree-12 bases of the same `12Tj`** (`lmfdb.fields`, disc-sorted
   ascending). Signature/`r` reachability: `K` has `r_K = 2·#{real places of F with α>0}`, so `F`
   needs `r1 ≥ target_r/2`. We pull the smallest bases meeting `max_r2=(12−r/2)/2` **AND** the
   totally-real ones (`max_r2=0`) — the latter can dial ANY even `r` via the split prime and are
   **essential for high `r`** (the just-enough-real bases can't get all α-signs positive; see below).
3. **Batched sweep**: build `general_c2(base, w, q)` for the smallest ~12 split primes in ONE gp
   process (`bnfinit` amortized across all primes — a big speedup over `general_c2`'s per-call
   `bnfinit`), `polredbest` each, print `q | polsturm | coeffs`.
4. **GATE (mandatory):** deg-24 irreducible (guaranteed by `rnfequation` of a field) ∧ `polsturm ==
   target r` ∧ local `nfdisc` **STRICTLY < our current field disc** for the pair (never enqueue a
   model ≥ ours — wasted submission budget). Prefer ≤ the rival min disc.
5. **Enqueue survivors** as pre-built `ready` polys (the daemon submits them verbatim; Magma
   arbitrates the `24Tt` label — same-top same-construction should preserve it, a wrong label just
   doesn't score), target `defend:<t>.<r>:d24:b<basedisc>`, priority **150** (above `lit:new` 130).

**Deliverable:** `scripts/defend_producer.py` (standalone, reusable, `--enqueue`, `--limit`,
`--only t.r,...`). Winners checkpoint incrementally to `data/processed/defend_winners.jsonl`.

## Validator — before/after on the worst 3 pairs (40-digit gaps)

`python scripts/defend_producer.py --only "20054.12,3226.0,17424.12" --limit 999`

| pair | top | our field-disc | rebuilt | rival min | outcome |
|------|-----|---------------:|--------:|----------:|---------|
| 24T20054 r12 | 12T227 | 74 digits | **56 digits** | 34 | −18 digits (<ours) |
| 24T3226 r0   | 12T25  | 75 digits | **39 digits** | 39 | −36 digits (**== rival min**) |
| 24T17424 r12 | 12T135 | 62 digits | **55 digits** | 34 | −7 digits (<ours) |

All 3 built a smaller-disc valid deg-24 field at the target `r` (61 local disc-digits removed). **BUT
— per the run outcome below — none of these actually land on the intended `24Tt`** (24T3226's model
verified as 24T16715, 24T20054's as 24T22821, 24T17424's as 24T17304): the table shows that a much
smaller FIELD is *buildable* over the same top at the right `r`, which is necessary but NOT sufficient
— the group isn't preserved. The `r=12` sign condition (6 real places of `F` with α>0) needs the
totally-real base pool, confirming the `r`-dial works across the regime.

Gotcha fixed during the build: gp's stdin reader parses **one statement per line**, so a `for(...)`
loop split across newlines fails with "unexpected end of file, expecting )". The batched sweep keeps
the whole loop on ONE line (`general_c2` sidesteps this by keeping each statement single-line).

## Full run (top 400 behind gen12 pairs, `--enqueue`)

`python scripts/defend_producer.py --limit 400 --enqueue` (elapsed 1185 s / ~20 min)

**Build metrics (what the producer THINKS it did — computed against the *intended* pair):**

| metric | value |
|--------|------:|
| behind gen12 pairs attempted | 400 |
| pairs with a smaller-disc model at the target r | 379 (94.8%) |
| winner models built (≤2/pair), enqueued as `defend:` | 705 |
| local field-disc digits removed (vs the intended pair's disc) | 3775 |

**Verification metrics (what it ACTUALLY did — the daemon submitted all 705, SAIR labeled them):**

| outcome | count |
|---------|------:|
| SAIR-verified with a real Magma `24Tt` label at the correct `r` | 392 (`dup`: 313) |
| landed on the **INTENDED** `24Tt` | **0 / 390** |
| landed on a **DIFFERENT** `24Tt` (same `r`) | **390 / 390** |
| incidental: improved disc on some OTHER pair we hold | ≤21 |
| incidental: new coverage of some OTHER pair (all `teamCount>0`, low value) | 7 |
| landed on a pair we already hold ≥ as good (redundant) | 177 |

### OUTCOME: the targeted-recovery premise is FALSE — do not integrate as-is

The construction is **mechanically sound** (705 valid degree-24 fields, 392 Magma-confirmed, and the
**split-prime `r`-dial is perfectly preserved** — every model matched the target `r`). But the
**group is NOT preserved**: **0 of 390** verified models hit the pair they were built to defend. The
same length-12 `w`-pattern over a *different* degree-12 base of the same `12Tj` top realizes a
**different kernel submodule** — because `idealprimedec`'s ordering of the 12 primes above `q` is
**not canonical across bases**, so `w`-index `k` points at a different coset each time. This is
exactly the **alignment problem of test 0038** ("the pattern→group map is alignment-dependent over
non-Galois bases"), now confirmed to also break *disc-defense*. It is **base-dependent and
non-invertible**: 67/270 intended pairs landed on ≥2 *distinct* labels depending on which small base
was drawn — there is no fixed offset to invert.

Net value of the run is therefore **modest and incidental**, not the ~137-point premise: ≤21 possible
disc-improvements + 7 low-value new pairs on OTHER groups, against 177 redundant landings.
Additionally the 392 verified rows are currently recorded `scoreable=False` / blank-disc (collection
lag — SAIR labeled them but the scoring disc hasn't been re-fetched; a known `pending_remove`
artifact per `gp.scoreable_disc`'s note), so even the incidental gains are unrealized until re-fetch.
**The earlier "~20.7 points recovered" figure was WRONG** — it assumed the models hit the intended
pair; they don't. (Self-corrected via the mandatory `realized.csv` counter-check.)

### The real fix (for a v2 that actually recovers the targeted pairs)

To lower a specific pair's FIELD disc while preserving its `24Tt`, the kernel submodule must be pinned
to the SAME `G`-submodule over the new base — i.e. the `w`-index must be *aligned* to the intended
group, not reused raw. Options, in order of tractability:

1. **Same base, smaller prime** (what `produce_harden` already does): preserves the prime-ordering
   structure → preserves the group, but leaves the BASE-disc floor (the dominant term) untouched, so
   it can't close the big gaps. This is why harden helps little on the 40-digit gaps.
2. **Harvest-and-filter (the honest base-swap route):** over each small base, sweep MANY `w` (all low
   popcounts) + primes, enqueue broadly, and let Magma label — then keep only landings that hit a
   behind pair with a smaller disc (the daemon's min-disc merge does this automatically). This is
   essentially `produce_selfcomp`'s atlas-driven design and is the correct pattern; the targeted
   single-`w` gate here is the wrong tool. Cost: many submissions per recovered pair (untargeted).
3. **Align via the atlas:** if the atlas recorded, for a small base of top `12Tj`, which
   `(base, wtag, q)` → which `24Tt`, query it to pick the `w` that lands on the intended pair over
   THAT base. Requires the atlas to have sampled that base — a cold-start problem for rare tops.

**Recommendation: do NOT wire this producer into the tick.** Either (a) fold the "smaller base, same
top, broad-`w`, post-hoc Magma filter" idea into `produce_selfcomp`, or (b) keep base-disc defense to
the pairs where option 1 (harden) or a fresh-base harvest already lands. The spec below is retained
for reference but is superseded by this outcome.

## Tick-wiring spec (for the user to review + integrate — NOT wired here)

Defense should run 24/7 as a low-cadence tick arm, mirroring `produce_harden`/`produce_selfcomp`.
Recommended wiring (to be added by the user to `scripts/search_ctl.py`, NOT by this agent):

1. **Wrap as `produce_defend(limit=200, force=False)`** in `search_ctl.py` — the same body as
   `defend_producer.main()` but: (a) honor `_queue_full()` (skip the tick when queue > cap, like
   `produce_general12`); (b) throttle with a kv timestamp `defend_last` (run at most every ~6 h, like
   `produce_tsig`'s `tsig_last`) since the leaderboard min-disc set only moves on a `refresh`;
   (c) take `limit` from `store.get_kv("defend_batch", 200)`.
2. **Refresh-gated ordering:** defense reads `progress.json` (rival min discs). Wire it to run
   **after** the tick's `refresh()` so it targets the current-day min-disc gaps, not stale ones.
3. **Tick rotation:** add `produce_defend` to the rotation in the same block as `produce_harden`
   (both are cheap self-competition arms). Suggested cadence: once per ~6 h tick cycle; it is I/O- +
   gp-bound but self-caps at `limit` pairs and short-circuits pairs with no smaller base.
4. **Portfolio quota:** give `defend:` a small floor share in the `claim()` quota kv (e.g. 0.05) so
   the daemon always drains defense rows even when a harvest arm floods the queue — but keep it small
   (defense is a fixed backlog of ~a few hundred pairs, not an infinite feed).
5. **Priority already handled:** the producer sets `set_priority_prefix("defend:", 150.0)`. Leave
   `defend:` above `lit:new` (130) so recovered models submit ahead of speculative harvest.
6. **Re-run cheaply:** the target `defend:<t>.<r>:d24:b<basedisc>` dedups, so re-ticks only add
   genuinely new (smaller-base) models; idempotent.

**Do NOT** wire the r=24 / primitive tops here — defense is strictly the gen12 (2-block) backlog.

## Learnings

- **Headline (negative):** naive `w`-reuse over a smaller-disc base of the same top does **not**
  recover a targeted pair — the `24Tt` isn't preserved (0/390), because the prime ordering that the
  `w`-index rides is base-dependent (test 0038 alignment, now confirmed for defense; base-dependent
  and non-invertible, 67/270 pairs → multiple labels). A smaller FIELD at the right `r` is necessary
  but not sufficient; the KERNEL SUBMODULE must be aligned to the intended group. This kills the
  "targeted single-`w` disc-gate" design; the correct pattern is harvest-broad-`w` + post-hoc Magma
  filter (fold into `produce_selfcomp`) or same-base-smaller-prime (`produce_harden`).
- **Counter-check earned its keep:** the run's own summary looked like a 20.7-point win; the mandatory
  `realized.csv` verification showed 0/390 on-target. Never trust a producer's self-reported recovery
  without checking what SAIR actually labeled the models.
- **Reusable machinery that DID work** (salvageable for a v2): the `source` string is a complete
  (top, w) recovery key (no queue join); the totally-real base pool dials any even `r` (the split
  prime `r`-dial is fully preserved — every model hit its target `r`); batching `bnfinit` across
  primes in one gp process cut per-base cost ~10× (the throughput lever).
- The 392 verified rows record `scoreable=False`/blank-disc — collection lag (`pending_remove`), so
  even the incidental gains need a SAIR re-fetch to realize.
