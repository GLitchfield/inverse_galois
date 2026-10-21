# 0064 — MINBLK=2 24T14616 DIRECTED-w PILOT — targets rival-claimed at build time

**Family:** mb2 (MINBLK=2 directed single-radical) · **Type:** build (headless igp-build loop) ·
**Date:** 2026-07-12 · **Outcome:** BLOCKED (all targets rival-claimed) — 0 enqueued.

## Setup

Top **## Ready** backlog item (written 2026-07-12 by auto_log dive #43): a PILOT of the DIRECTED
dim-6 single-radical `general_c2` over base 12T183 `[-1,13,26,-105,-63,266,-56,-153,58,31,-14,-2,1]`
(classno=1, narrow h⁺=1, δ=0), sweeping the C(12,6)=924 popcount-6 `w`-subsets to direct the C₂-kernel
at the **dim-6 proper submodule ≅ 24T14616** (|G|=46080), density-gated to rule out the inflations
16607 (dim-7, |G|=92160), 20699 (dim-10, |G|=737280), 22761 (|G|=2949120).

**Targets as written by dive #43:** (24T14616, r∈{8,16,24}), all three claimed VERIFIED **tc=0 OPEN**
(sole-1.0 each if landed). The pilot was framed as the decisive LOCAL-GATE test of dive #42's
unresolved dim-6 inflation question ("do NOT scale until 1–5 official SAIR labels confirm 24T14616").

## Re-verify (step 3) — the premise flipped

Refreshed `progress.json` (`scripts/search_ctl.py refresh`, 25000 labels / 165836 sigs, 2026-07-12
12:23 EDT) and re-checked each target against `progress.json` + `realized.csv` + `igp.baseline`:

| pair | teamCount | in_baseline | rows in realized.csv | verdict |
|---|---|---|---|---|
| 24T14616,8  | **1** | False | **0** | rival-claimed |
| 24T14616,16 | **1** | False | **0** | rival-claimed |
| 24T14616,24 | **1** | False | **0** | rival-claimed |

All three r-values now show `teamCount==1` with a set `minDisc` (≈3.32e91), yet **we hold 0 rows for
t=14616** in `realized.csv` — so the single credited team is a **rival**, not us. Contrast the two
family groups we DO hold, which correctly show tc=1 = *us*: 16607 (34 rows, sole-1.0) and 20699 (274
rows, sole-1.0). Verified no prior enqueue of this construction (`lit:mb2dir%` empty in the search
queue; the "14616" queue hits are disc substrings `d1461681`), so the tc=1 is not our own submission
lag. The git log corroborates: dive #42 already noted **20699 LOST to rival**, tagging 14616 "sole
live make-or-break" — that last live target is now taken too.

## Decision — GATE, do not build

- **Score:** rival-claimed + non-baseline ⇒ landing 14616 now yields at best a *shared* ~0.5 (k=2),
  never the sole-1.0 the item was greenlit for. Step 3 of the build gate: skip rival-claimed pairs.
- **Technique reuse:** the dim-6 directing is 14616-specific. The family's still-OPEN pairs — 9641,
  9642 (r∈{16,24}), 19246 (r∈{20,24}), 9633,4 — carry *different* kernel obstructions (9641/9642 gated
  on a δ=2 solve; 19246 REFUTED non-cyclic, dive #41), so proving the dim-6 recipe unlocks none of them.
- **Trust:** a local density fingerprint alone is exactly the low-trust signal that misled tests
  0044/0045/0051–0054 (all passed local gates on the WRONG group). The only authoritative confirmation
  is a SAIR Magma label, which is not worth spending on a rival-claimed pair. So a build here could
  reach at most LOCAL-GATED on a moot target — no rung of the evidence ladder that matters.

**0 candidates built, 0 enqueued.** No SAIR submission budget burned.
