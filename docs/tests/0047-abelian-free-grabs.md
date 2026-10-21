# 0047 — abelian order-24 "free sole-1.0s" are BASELINE pairs at the disc floor (unwinnable)

**Family:** abelian order-24 tail — 24T1=C24, 24T2=C2×C12, 24T3=C2²×C6 at r∈{0,24}.
**Date:** 2026-07-07.
**Question:** the 2026-07-06 agenda listed these six (t,r) as "6 free sole-1.0s buildable NOW"
(abelian ⇒ a single cyclotomic-subfield line realizes each, no Magma-gate needed to KNOW the
group). Build all six, local-gate, enqueue for the daemon to submit.

**Verdict: all six are BASELINE pairs, and each sits exactly AT the LMFDB discriminant floor, so
none is winnable. The producer builds + gates all six correctly and enqueues zero.** The agenda
item conflated `teamCount==0` (open / nobody-credited) with a sole-1.0; it never cross-checked
`in_baseline`.

## Setup

Builder: `scripts/abelian_free.py` (reusable; `--enqueue` pushes only strict beaters). Each target
is built as its **minimal-discriminant** abelian model — a compositum of minimal-conductor cyclic
pieces (conductor-discriminant formula), pieces found by a `polsubcyclo` enumeration:
C3 real cond 7 (disc 49); C8 real cond 17; C8 CM cond 32 (disc 2³¹); C4 real cond 15 (disc 1125).
Gates: `poldegree==24`, `polisirreducible`, `polsturm==r`, exact `nfdisc` completes, and the real
scoreability test `nfdisc < D_base` (`igp.baseline.beats_baseline`).

## The three facts that sink the grab

1. **All six are baseline pairs** (`igp.baseline.is_baseline` = True for every one; they are among
   the frozen 622). Progress shows `teamCount==0` = OPEN, but "open" ≠ "sole-1.0" — a baseline pair
   is worth ≤0.5 and *only if* unlocked.
2. **Unlocking a baseline pair requires an exact `nfdisc` STRICTLY < `D_base`** (mixed disc never
   unlocks). Rule: `docs/competition_rules.md` line 62-64; encoded in `igp.baseline`. Empirical
   confirmation: of **1309** scoreable+baseline rows in `realized.csv`, **1309 have disc < D_base
   and 0 are ties** — a tie does not score.
3. **The minimal achievable disc equals `D_base` for every one of the six** (LMFDB already holds the
   global-minimum field for these classical tiny abelian groups). Confirmed by direct enumeration:

| (t,r) | group / sig | minimal model | disc | D_base | beat? |
|-------|-------------|---------------|------|--------|-------|
| 1,24 | C24 TR | C8(cond17) ∘ C3(7) | 2.296…e39 | 2.296…e39 | **tie** |
| 1,0  | C24 CM | C8(cond32) ∘ C3(7) | 3.291…e41 | 3.291…e41 | **tie** |
| 2,24 | C2×C12 TR | C4(cond15) ∘ Q(√21) ∘ C3(7) | 1.617…e35 | 1.617…e35 | **tie** |
| 2,0  | C2×C12 CM | Q(ζ₃₅) | 3.043…e29 | 3.043…e29 | **tie** |
| 3,24 | C2²×C6 TR | Q(√2,√3,√7) ∘ C3(7) | 1.193…e37 | 1.193…e37 | **tie** |
| 3,0  | C2²×C6 CM | Q(i,√3,√7) ∘ C3(7) | 7.114…e29 | 7.114…e29 | **tie** |

Searches over triquadratic/quartic-×-quadratic composita (allowing the third quadratic to share the
cubic's prime 7 — e.g. Q(√21), Q(√7)) and over prime/2-power conductor cyclic octics found nothing
below `D_base`. Since the minimum = `D_base` and unlock needs strictly less, **no polynomial unlocks
any of the six**.

## The canary we already had

`realized.csv` already contained `daemon:lit:abelian:1.24:zeta97` for (1,24): an exact `nfdisc`
(4.96e45) but `scoreable=False` — a prior session built the C24/97 model, submitted it, and it did
not score **because 4.96e45 > D_base=2.30e39**. That row was the evidence the naive "any valid disc
scores" premise was already false.

## Result

`scripts/abelian_free.py --enqueue` → **0 enqueued** (all six SKIP: "baseline pair NOT strictly
beaten"). No submission budget spent. Producer retained: if a genuinely strict-beating abelian
construction is ever found, or `D_base` moves, `--enqueue` picks it up automatically.

## Learnings

- **Cross-check `is_baseline` AND `D_base` before treating a `teamCount==0` pair as a 1.0.** The
  quality rule "famous ≠ open" extends to "baseline ≠ open": these are the MOST classical degree-24
  fields, so LMFDB holds them at the true disc minimum. `teamCount==0` on a baseline pair means
  "no competition team has *beaten* the baseline yet", not "free".
- **The disc floor is the binding constraint on baseline pairs, not the group.** Knowing the group
  for free (abelian construction) buys nothing when you cannot get under `D_base`.
- **`igp.baseline` already encodes this** (`beats_baseline` = strict; docstring: "a baseline pair
  scores ONLY if our exact nfdisc strictly beats D_base"). The agenda item predated / bypassed it.
- gp gotcha (this environment): a `gp` statement must not break across a newline mid-parenthesis,
  and a user-function body `f(x)=...` extends to end-of-line — so multi-piece composita go through
  the tested `gp.compositum` / `gp.polsubcyclo` helpers, not ad-hoc one-line gp function defs.
