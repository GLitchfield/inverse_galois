# 0065 — Abelian-kernel producer: class-field-theory generalization of general_c2 (C_n ray class fields)

**Family:** construction / class-field-theory (task #3)
**Date:** 2026-07-12
**Status:** PRODUCER, MEASURED LOW-VALUE — technically works + reaches minblk=3/4, but the strata are
contested so marginal score ≈ 0.25 pts (one low-k hit). Kept at LOW priority (30), not scaled.

## Question

`general_c2` reaches only the **C2** block (a single `√α` radical over a deg-12 base). Can we
generalize the *kernel* to an arbitrary cyclic `C_n` — reaching the solvable **minblk=3** (deg-8
base) and **minblk=4** (deg-6 base) strata the C2-tower structurally can't — using only PARI (no
Magma)? This is the tractable form of the Klüners–Malle systematic (class-field-theory)
construction.

## Mechanism

`gp.abelian_kernel(base_coeffs, n)` builds a deg-24 field as a degree-`n` **cyclic ray class field**
over a deg-`(24/n)` base `F`:

1. `bnfinit(F)`; scan moduli `m = 2..hi_modulus` for a **cyclic** ray class group `Cl_m(F)` whose
   order is divisible by `n` (`#cyc==1 && cyc[1] % n == 0`).
2. `bnrclassfield(bnr, matdiagonal([n]))` — the `C_n` subfield's class field (relative defining poly).
3. `rnfequation` → absolute deg-24 poly; `polredabs`; keep iff irreducible + `nfdisc` is
   `smooth_bound`-smooth. Returns `(ascending coeffs, polsturm r)`.

Two knobs, both validated below:
- **kernel `n`** picks the block: `(deg 6, n=4)` = C4/minblk=4; `(deg 8, n=3)` = C3/minblk=3.
- **base signature is a clean `r` dial:** totally-real base (`max_r2=0`) → **r=24**; mixed → r=8;
  complex → r=0. So each group `24Tt` is reachable at several `r` → several scoreable pairs.

## Result

**The label is DETERMINISTIC per base Galois label** (so it is open-gateable):
`6T5→24T65, 6T11→24T397, 6T13→24T643`; `8T17→24T113, 8T47→24T7221` (each reproduced ≥2×).

**Pilot + validation yield (44 daemon builds):** **22 scoreable rows (50%), 18 distinct scoreable
`(t,r)` pairs**, spread across `r ∈ {0, 8, 24}` (r=24 = 10 pairs — the high-value end of the open
board) and groups **24T14, 15, 19, 27, 65, 113, 133, 168, 397, 643, 713, 714, 5329, 7221, 7223** —
low-t and high-t alike, the solvable minblk=3/4 strata. ≈**0.41 scoreable-pairs/build**, far denser
than the saturated harvest producers (gen12 ≈ 0.34 pts / 1000 builds).

End-to-end validated on the restarted daemon (new `abelian_kernel` construct dispatch): 3/3 fresh
test specs came back scoreable (24T168 r=8, 24T397 r=0, **24T5329** r=0 — a fresh group).

## Marginal VALUE (the corrective — `producer_value.py`, 66 builds)

The pair-count above is a **coverage number, not a score number** — and the two diverge hard here.
`producer_value`: abelian **wins 38 pairs but earns only 0.247 pts total**, of which **0.243 is a
SINGLE pair** (24T265 r=24, teamCount=3). Every other win is a heavily-contested group
(`teamCount ≥ 10 ⇒ 2^(1-k) ≈ 0`) — the minblk=3/4 strata this reaches are **already claimed by many
teams**, so a technically-fresh pair is worth ~nothing. This is the exact rows-vs-value trap the
quality rules warn about: "0.41 pairs/build, denser than harvest" was counting distinct pairs, not
score; the honest marginal value is ≈0.25 pts (one lucky low-k hit), ~0 ongoing.

**Consequence:** abelian builds are ~15× more expensive than gen12_treal's (10-20s vs <1s), so at a
high priority they would *starve the real lever* for ~0 return. Dropped to **priority 30** (below all
harvest producers) — retained as cheap exploration for the rare low-k pair, NOT scaled. The genuine
lever remains minblk=2 high-r (gen12_treal), which is 91% of the open board.

## Build

- `src/igp/gp.py::abelian_kernel` — the constructor (single-line gp for-loop: gp parses stdin
  line-by-line). LOCAL-GATED internally (deg24 + irreducible + nfdisc-smooth).
- `scripts/searchd.py::construct` — new `"abelian_kernel"` kind → daemon's parallel gp pool does the
  heavy `bnfinit`+modulus-scan+`polredabs`; the producer only enqueues cheap `{base, n}` specs.
- `scripts/search_ctl.py::produce_abelian` — cursored deg-6(C4)+deg-8(C3) bases, **alternates
  totally-real (r=24) and general (r∈{0,8})** each call; priority 110 (below gen12treal 128).
  Wired into `TICK_PRODUCERS`. `"abelian"` added to `rank.PREFIXES`.
- `scripts/abelian_pilot.py` — the standalone pilot enqueuer (evidence-ladder PILOT step).

## Learnings

- The C2→C_n generalization is **real and cheap** (pure PARI), and it opens fresh strata — the first
  producer to systematically hit minblk=3/4 with a high scoreable rate.
- **C6/deg-4 (minblk=6) did NOT build** under `hi_modulus≤60` (C6=C2×C3 needs a rarer cyclic-6 ray
  class quotient); minblk=6 is a tiny slice and was not pursued.
