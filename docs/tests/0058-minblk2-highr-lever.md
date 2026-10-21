# 0058 — minblk=2 is 91% of the open board, and it's a HIGH-R lever (family: gen12 / signature)

**Question.** Where does the open headroom actually live, and can we point a producer at it?

## Setup / recipe

Bucketed all **45,873 open pairs** (teamCount==0, valid, unheld) by group family, using
`data/targets/block_structure_deg24.csv` (minblk) + `transitive_groups_deg24.csv` (order/solvable).

## Result — where the open board is

Open pairs by minimal block size (the producer-actionable axis):

| minblk | tower | open pairs | open groups |
|---|---|---|---|
| **2** | C₂ over deg-12 | **41,619 (91%)** | 12,026 |
| 4 | 6×4 | 3,593 | 636 |
| 3 | 8×3 | 346 | 155 |
| 6/8/12/prim | — | <320 total | — |

So **91% of the open board is gen12's minblk=2 territory.** Also: 8,995 open pairs are *sig-fill*
(groups we already realize); 806 are non-solvable; the tiny-order (<100) groups have only 47 open
(the contested direct-product family — why nflist compositum was a dead end).

## Result — the r-bias smoking gun

Within minblk=2, held vs open by real-root count:

| r | HELD | OPEN |
|---|---|---|
| 0 | 439,515 | 3,263 |
| 8 | 59,736 | 5,186 |
| 16 | 7,748 | 8,849 |
| 20 | 1,023 | 4,557 |
| 24 | 188 | **10,411** |

We hold **439,515 at r=0 but 188 at r=24**; the open board is the inverse (**23,817 open at r≥16**).
Cause: for K = F(√α), **r(K) = 2·#{real places of F where α>0} ≤ 2·r₁(F)**. gen12's cursor walks
mostly *complex* bases (r₁<12 → r capped low) and its random split-prime α is almost never totally
positive, so we **saturated low-r and structurally cannot reach the high-r open pairs.**

## The lever + producer

Only **totally-real** deg-12 bases (max_r2=0) can reach high r. Feasibility confirmed: **32/40**
totally-real bases have a completely-split prime (usable). Validated the skew: a 45-build sample over
totally-real bases lands **47% at r≥16 and 33% at r=24** — vs 0.03% of our held pairs at r=24, a
**~1000× enrichment** aimed exactly at the 10,411 open r=24 pairs.

Built **`produce_gen12_treal`** (`scripts/search_ctl.py`): the gen12 general_c2 machinery restricted
to `max_r2=0` bases + a wide split-prime sweep (`n_primes=8`), sharing gen12's atlas for open-gating,
own cursor `gen12treal_offset`, priority 128 (above gen12). Wired into `TICK_PRODUCERS`;
`produce-gen12treal` CLI. SAIR is the authoritative label downstream.

## Learnings

- The open board is not exotic — it's **gen12's own family at high r**, which validates the
  session's throughput work (feeding gen12) and adds the missing signature axis.
- α's sign pattern is a square-class invariant (can't be fixed by unit multiplication without
  changing the field), so the only lever is **totally-real base selection + prime sweep**, not
  post-hoc α engineering. A narrow-class totally-positive-α refinement (guaranteed r=24) was
  built afterwards (test 0062).
