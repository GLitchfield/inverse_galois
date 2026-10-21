# 0074 — The FULLY-OPEN ORBITAL CLASSES: weight-2 totally-positive radical, r=24 (family: MINBLK=2)

**Date:** 2026-07-13 · **Backlog item:** "THE 7 FULLY-OPEN ORBITAL CLASSES — 14 tc=0 sole-1.0s at
r=24" (research dive #55; aiming rule dive #54; measured inflation rate dive #56)
**Producer:** `scripts/mb2_orbclass.py` · **Outcome:** BUILT — 5 candidates / 5 tc=0 pairs enqueued,
one per class, PILOT cap honoured; SAIR labels pending at write-time.
**Resolution (recorded in test 0075):** all five pilots returned official Magma labels matching the
group each aimed at.

## Question

Dive #55 found seven `(top, orbital-module)` classes in which **every** sibling group is `teamCount=0`
at `r=24` — so the weight-2 split radical's sibling ambiguity costs nothing: whatever lands, scores.
We already hold `r = 0…20` on most of the 15 groups (gen12 lands them routinely); the only missing
ingredient is `r = 24`, which needs a **totally-positive** α. Every available base has `h⁺ ∈ {2,4}`,
so there is no free totally-positive generator. **Is r=24 reachable on these bases at all, and does
the orbital pre-filter aim well enough to gate a landing?**

## Setup

Construction (existing engine, two changes): `K = K₀(√α)`, `α` = totally-positive generator of
`P_{q,a} · P_{q,b}`, with `K₀` a totally-real `h=1` degree-12 LMFDB field of the class's top, `q`
completely split (`q < 10⁶`, the grader's factorization bound), and `(a,b)` restricted by the dive-#54
**orbital pre-filter** to the pairs whose orbital graph has `12 − kdim` components — **kdim 9** for the
12T63 class, **kdim 10** for the other six. Sign-fix by the unit sign-lattice solve (`matsolvemod`);
r=24 ⟺ α totally positive (dive #31).

Gate before enqueue: Frobenius-density fingerprint (witness exclusion + L1 over ~5,100 primes,
`mb2_twist.gate`) against the **full submodule × complement library** of the top (`mb2_multi_gdist.g`,
48–131 groups per top); the landed group must be `teamCount=0` + non-baseline at r=24; then deg-24
irreducible, `polsturm == 24`, `gp.scoreable_disc` non-blank.

Targets re-verified against `data/processed/progress.json` (refreshed 2026-07-13 16:18): all 14 are
`teamCount=0`, `minimumDiscAbs = None`, non-baseline at r=24. `24T19768` is `tc=1` and is never
enqueued.

Command:

```
.venv/bin/python scripts/mb2_orbclass.py --ncand 3 --nq 12 --nbases 2 --per-target 1 --pilot 5 --enqueue
```

## Result — 5 of 5 classes attempted produced an in-class, on-dim, gated landing

| class (top) | kdim | q | (a,b) | landed | L1 | margin | rivals killed | field disc |
|---|---|---|---|---|---|---|---|---|
| 12T63  | 9  | 761  | (1,5) | **24T14958** | 0.031 | 0.532 | 53 of 59 | 9.93e51 |
| 12T154 | 10 | 5233 | (1,4) | **24T19769** | 0.048 | 0.181 | 108 of 110 | 6.74e48 |
| 12T107 | 10 | 3257 | (2,3) | **24T18528** | 0.041 | 0.168 | 72 of 82 | 8.40e50 |
| 12T106 | 10 | 4957 | (1,6) | **24T18526** | 0.032 | 0.199 | 112 of 128 | 4.60e49 |
| 12T58  | 10 | 2099 | (1,4) | **24T16758** | 0.030 | 0.178 | 128 of 130 | 2.38e45 |

All five: deg-24 irreducible, `polsturm = 24`, `scoreable_disc` non-blank, **in-class** (a sibling of
the aimed module), **tc=0 + non-baseline** at r=24, and landed at **exactly the predicted kernel dim**
(5/5 — better than dive #56's measured 61–64% at kdim 9–10, but n=5). Enqueued as
`lit:orbclasspair:<t>.24:base12T<top>:q<q>_<a><b>:repnone` @115 (tier `pair`: we hold each group at
other `r`; the `(t, 24)` pair is the new sole-1.0). All five reached `submitted` within the run.

12T69 and 12T126 were skipped by the **pilot cap of 5**, not by any failure — the 12T126 dry run had
already gated `24T19373` cleanly (q=6011, L1 0.043, margin 0.316, 45 of 47 rivals killed, disc 3.5e47).

## The finding: the h⁺ obstruction is a PER-`q` COIN FLIP, not a base-level wall

The item's stated risk was that `h⁺ ∈ {2,4}` blocks the totally-positive generator. The first run —
2 split primes per base, exactly what the shipped producers sample — found **0 totally-positive α out
of 96 (pair, arm) attempts on 12T126** and reported the base dead. That conclusion was **wrong, and
it was an artifact of the `q` sample size.** The narrow class of `P_{q,a} · P_{q,b}` depends on `q`;
raising the sweep to 12 split primes found `q = 6011`, where **2 of 2** pairs are totally positive.
Same pattern on every class: the winning `q` is rarely the first split prime (12T154 gave 0/48 at
q=4049 and 3/7 at q=5233).

So the operative dial is **`--nq` (how many completely-split primes you sweep)**, and the cost of an
extra `q` is a `bnfisprincipal` per surviving pair — no build, no SAIR call. Heuristically ~`1/h⁺` of
split primes work.

**The even-f repair (test 0072) never fired: all 5 winners carry `repnone`.** The repair arms are
still wired in (they add no new prime to the disc, so they are free to try), but on these bases a
wider `q` sweep is what unlocks r=24 — the repair is a fallback, not the mechanism.

## Corrections to the record

* **Self-caught:** an early check reported "12T106's library has no kdim-10 group; 18525/18526 are
  absent — the census does not reproduce". That was a **partially-written `lib106.txt`** read while
  the GAP job was still running. The completed library has 129 groups and contains both siblings at
  kdim 10, and 12T106 produced a clean landing (24T18526, L1 0.032). No census discrepancy exists.
* Dive #56's inflation warning ("budget 2–3 gated builds per target") did not bind here: with the
  orbital filter on, 5 of 5 gated radicals landed the predicted dim on the first accepted pair.
