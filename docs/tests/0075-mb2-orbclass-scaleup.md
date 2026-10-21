# 0075 — Orbital-class scale-up: the sibling is FORCED, not sampled (family: MINBLK=2)

**Date:** 2026-07-14 · **Backlog item:** "ORBITAL CLASSES, SCALE-UP — the 9 residual in-class groups
(LABEL-GATED on test 0074's five)"
**Producer:** `scripts/mb2_orbclass.py` (+ new `--no-repair`) · **Outcome:** PARTIAL — 4 candidates /
2 tc=0 pairs enqueued (24T19373, 24T16759); the **7 residual multi-sibling targets are REFUTED** as
unreachable by this engine.

## The label gate cleared, 5 of 5

Test 0074's five pilots have all returned an **official SAIR/Magma label matching the group they aimed
at** — 24T14958, 24T19769, 24T18528, 24T18526, 24T16758 — every one `scoreable=True` with an
`exact_nfdisc`, and every one now sits at **`teamCount=1` with `minDisc` equal to our own disc** in
`progress.json`. Those are five landed sole-1.0s, and the weight-2 orbital engine is `PILOT-LABELED`.
This authorized the scale-up.

## Question

Test 0074 built one candidate per class and left 9 in-class siblings unbuilt: 14957/14959/14960
(12T63), 19770/19771 (12T154), 18527 (12T107), 18525 (12T106), plus 16759 (12T69) and 19373 (12T126),
which the PILOT cap had skipped. The backlog item's premise: *the engine aims at the MODULE, and 2–12
siblings share it, so raising `--ncand` and keeping the candidates whose fingerprint names a given
sibling should reach the residual ones.*

## Result — the premise is wrong, and the failure is structural

Two classes are **single-sibling** (the aimed module has exactly one group), and both built cleanly:

| class | q | (a,b) | landed | L1 | margin | rivals killed | field disc |
|---|---|---|---|---|---|---|---|
| 12T126 | 6011 | (1,4) | **24T19373** | 0.043 | 0.316 | 45 of 47 | 3.46e47 |
| 12T126 | 6011 | (1,5) | **24T19373** | 0.044 | 0.313 | 45 of 47 | 8.45e46 |
| 12T69  | 21851 | (1,2) | **24T16759** | 0.046 | 0.175 | 103 of 107 | 3.30e50 |
| 12T69  | 21851 | (1,6) | **24T16759** | 0.047 | 0.173 | 103 of 107 | 2.06e49 |

All four: deg-24 irreducible, `polsturm = 24`, `scoreable_disc` non-blank, target re-verified `tc=0` +
non-baseline + `minDisc = None` at r=24. Enqueued
`lit:orbclasspair:<t>.24:base12T<top>:q<q>_<a><b>:repnone` @115 (tier `pair` — we hold both groups at
other `r`; the `(t, 24)` pair is the new sole-1.0). All four reached `submitted` within the run.

The four **multi-sibling** classes produced **zero** enqueueable candidates, and the reason is the
finding:

> Over **80 totally-positive radicals** — 4 tops × 2 completely-split primes × ~10 orbital `(a,b)` pairs
> each — **78 landed the single sibling we already hold** (24T14958 ×20, 24T19769 ×20, 24T18526 ×20,
> 24T18528 ×18, all now `tc=1` ⇒ correctly rejected as NOT-OPEN), and **not one** landed a residual
> sibling. The other 2 were even-`f` repair-arm builds that inflated to kdim 11 (24T19719, off-class).

**The sibling is determined by the module, not sampled from it.** This is exactly **dive #48's
complement-cocycle law**, which this build re-confirms on a fourth family: the siblings sharing an
orbital module differ by a complement cocycle `χ ∈ Hom(H, F₂)`, cut out by `Q(√N(α))`. Our divisor
`P_{q,a}·P_{q,b}` has **even weight**, so `N(α) = ±q²·(unit)` ≡ ±1 mod squares ⇒ **χ is forced trivial**
⇒ the split complement, always. `(a,b)`, `q`, and the unit twist move the *kernel*; **none of them can
move the twist.** So the 7 residual multi-sibling targets are not under-searched — they are the
**twisted** siblings, and no weight-2 split-prime radical reaches them at any parameter.

Corollary: the seven-class orbital board is now **exhausted at its reachable frontier**. Its split
sibling is built in every one of the 7 classes (5 from test 0074, +19373 +16759 here). What remains
needs a genuinely different construction, not a bigger sweep.

## `--no-repair`: the fix that unlocked 24T16759, and a correction to my own first read

The first 12T69 run reported all 12 totally-positive α landing **24T18512 at kdim 11** (off-class, not
open) and I read that as *kernel inflation blocks this class*. **That was wrong.** Every one of those
12 carried the tag `rep2-1` — they were **even-`f` repair-arm** builds. The repair prime adds valuation
vectors that inflate the kernel (dim 10 → 11), and because repair candidates are enumerated alongside
control ones they **consumed the entire `--ncand` budget after only 2 split primes**, so the control
arm never got a deeper `q` sweep.

New flag `--no-repair` (control arm only) fixes it. Re-running 12T69 with `--nq 30 --no-repair`:

```
q = 839, 2953, 4259, 4441, 4703, 7481, 7649, 8461, 10499, 11807, 11987,
    12721, 13267, 15319, 17189, 17467, 20719, 21319, 21419   ->  0 totally-positive  (19 primes)
q = 21851                                                     ->  8 of 8 totally-positive  -> 24T16759
```

This sharpens test 0074's "`h⁺` obstruction is a per-`q` coin flip" to something more actionable: **the
coin can be badly biased** — here 1 usable prime in 20, far worse than the `1/h⁺ = 1/4` heuristic — so
a base that looks dead after a handful of primes may simply need `--nq` in the tens. It also means the
even-`f` repair (test 0072) is **not free on these bases**: it buys the sign at the cost of the kernel,
so the control arm should be swept to exhaustion *first*.

## Honest notes

* The two concurrent runs shared `data/processed/mb2orbclass/winners.json`, so the last writer
  clobbered it. The enqueues are unaffected (each process enqueues from its own in-memory list, and all
  4 are confirmed in the queue with well-formed 25-int payloads), but the JSON artifact is not a record
  of this test — the numbers above come from the run logs.
* `n = 80` for the forced-sibling claim, on 4 tops. The *mechanism* is dive #48's, proven; this is
  confirmation, not a new proof.
* 24T19768 (tc=1, a rival's) was never enqueued, as specified.
