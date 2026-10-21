# 0036 — Multi-prime sweep: doubling targeted 1.0 yield

**Family:** search / strategy · **Date:** 2026-06-29 · **Code:** `scripts/search_ctl.py`
(`_tsig_c2`/`_tsig_c2multi`/`_tsig_biq`)

## Question

Targeted discovery (tests 0033/0034) held 19 TRUE 1.0 signatures, all at *one* real-root count `r`
per reachable group — the producer used a single split prime per kernel. For a C₂-tower
`K = F(√α)` over a totally-real base, `r = 2·#{real embeddings σ with σ(α) > 0}`, and α's sign
pattern depends on the prime `q` (α is built from a generator of a prime above `q`). So does
**sweeping primes** realize *different* `r` for the *same* group, multiplying open-`(t,r)` yield?

## Method

Confirmed the mechanism first: one 12T3 kernel, 5 split primes →
- `w=[1,1,0,…]` → 24T2595 at **r ∈ {8, 12, 16}**,
- `w=[1,0,0,…]` → 24T14746 at **r ∈ {10, 12}**, `w=[1,1,1,…]` → 24T14746 at **{12, 14}**.

One prime captures one of these; the rest are missed. So extended the three targeted families to
sweep **N primes × more bases** per kernel (`c2`: 3 bases × 5 primes; `c2multi`: 2 bases × 3
prime-pairs; `biq`: 2 primes), enqueuing every open `(t,r)`. A per-run `covered = {t → r enqueued}`
set + a per-kernel `need = open_r(t) − covered` early-break stop sweeping once a group's open `r` are
all claimed, bounding wasted construction (`r` is computed locally with `polsturm` before the gate).

## Result

| metric | test 0033 | after sweep (0036) |
|---|---|---|
| **TRUE 1.0 held** (non-baseline, teamCount==0) | 19 | **41** |
| distinct scoreable signatures | 408 | 447 |
| distinct groups | 384 | 390 |
| distinct verified tsig `(t,r)` | 19 | 40 |

The `c2` family alone grew from 19 → **38 distinct verified `(t,r)`** — the added ones are new `r`
values for groups we already reached. A sweep run scans ~567 on-target candidates (vs 82
single-prime) and the daemon submits the survivors; Magma confirmed them, taking held 1.0s past 2×.

## Learnings

- **`r` is a free axis we were leaving on the table.** The group is fixed by (top, kernel); the prime
  is a cheap dial on `r`. Sweeping it converts each reachable group from one held signature into all
  of its open ones — a ~2× multiplier with no new mathematics, just more primes.
- **Count the distinct scoring unit, not the per-run "enqueued" number.** The run reported "enqueued
  22," which *looked* flat vs the prior 21 — but those are new *targets that run*, and cumulative
  distinct verified `(t,r)` had gone 19 → 40 (the prior targets already existed, so they don't
  re-count). The scoreboard's TRUE-1.0-held (19 → 41) is the metric that matters. (Quality rule: score
  the metric that counts.)
- **Discard `need` on *obtained*, not *newly-enqueued*.** First cut only cleared the need-set when
  `enq` returned True, so an already-queued `r` never cleared and the early-break never fired → every
  prime got swept. Fixed to clear on any successful construction; new runs stop early once a group's
  open `r` are covered.
- **The sweep self-extends:** it's in the 6h producer tick, so as competitors claim open `(t,r)` the
  next scan targets whatever is still open.
