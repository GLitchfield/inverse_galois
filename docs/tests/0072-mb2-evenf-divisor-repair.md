# 0072 — The EVEN-`f` DIVISOR REPAIR: unblocking a narrow-class-obstructed sign-twist base

**Family:** MINBLK=2 / `general_c2_TWIST` (dives #49–#53; tests 0068–0071)
**Date:** 2026-07-13
**Backlog item:** "[MINBLK=2] NARROW-CLASS PRE-SCREEN + EVEN-`f` REPAIR for the sign-character twist
engine (research dive #52)"
**Outcome:** `[BUILT: 2 candidates / 1 pair — (24T23297, 24) SAIR-LABELED, a DISC-UNDERCUT; the item's
other 5 targets were already spent; Part 1 (the pre-screen) is REFUTED and NOT shipped]`

> **OFFICIAL LABELS LANDED DURING THE RUN, AND THEY MATCH.** Both enqueued candidates were submitted by
> the daemon and came back from SAIR's Magma with the label **`24T23297`** at **r = 24** — the aimed
> sibling, first try. The even-`f` divisor repair is therefore **SAIR-VALIDATED**, not merely
> LOCAL-GATED: ladder position `PILOT-LABELED`. The density fingerprint's verdict (kdim 11, the aimed
> sibling, margin 0.85) is confirmed by the authoritative gate.

## Question

Dive #52 found that the sign-character twist producer's totally-positive-α step succeeds **iff
`[Id] = 0` in the narrow class group `Cl⁺(K₀)`**, where `Id` is the product of the odd-`f` primes above
the primes dividing `d = core(disc K₀)`. On a base where `[Id] ≠ 0` the producer silently finds nothing
— which is exactly what test 0069 recorded as "24T23297 / 12T245 is sign-lattice-BLOCKED".

Dive #52 proposed a repair, and this test asks whether it works and whether it is *safe*:

> `core(N(α))` sees only the **odd** part of the norm valuations, so a prime `P` of **even residue
> degree** has `N(P) = p^even` = a perfect square and can be multiplied into the divisor **without
> changing `d`** — hence without changing the aimed character `χ = Q(√d)` or the aimed sibling `G_χ` —
> **while shifting `[Id]` in `Cl⁺`.**

The repair provably preserves `d` and `χ`. It is **not** proven to preserve the `C₂¹²` **block kernel**,
and the kernel is what actually pins the sibling. That was dive #52's stated open GATE:

> *Does the even-`f` repair prime perturb the block kernel?*

## Setup

Producer: **`scripts/mb2_twist_evenf.py`** (new, reusable, `--enqueue`). Same build as
`mb2_twist_sign_producer.py` (dive #50) with the divisor repaired, plus a **control arm**:

```
Id_repaired = (prod_{p | d} P_p^{odd f}) · P_repair ,   f(P_repair) even
```

The repair arms are enumerated automatically as **every even-`f` prime above a prime already dividing
`disc K₀`** — so the repair prime is *already* in the degree-24 discriminant and **scoreability is
untouched** (no new prime enters). Arm `none` (no repair) runs **first**, as a control, so the
obstruction is *observed* rather than assumed.

Base (from the dive-#50 shortlist): **24T23297 / 12T245**, `d = 5`, `h = 1`.
Verified on-box before building: `disc K₀ = 2⁸·3¹⁴·5⁹·29²·31²·61²`, `core = 5` ✓, and the narrow
sign-lattice rank **δ = 1** (so `h⁺ = 2` — the obstruction is real). There is exactly **one** prime
above 5 (`f = 3`, odd), so dive #52's repair option (i) — *re-choose the odd-`f` prime* — is
**impossible on this base**; option (ii), the even-`f` multiplier, is the only route.

Gate (unchanged from test 0070): kernel dim == 11, target = top match, `L1 < 0.35`,
**witness-exclusion** margin > 0.15 at `FPMAX = 50000` (5,133 primes); then deg-24 ∧ irreducible ∧
`polsturm == 24` ∧ `gp.scoreable_disc` non-blank.

## Result — the repair works, and it does NOT move the kernel

Seven even-`f` repair candidates were found above `disc K₀` (two above 2 with `f=4`, one above 3 with
`f=2, e=6`, two above 31, two above 61). Split primes: `q ∈ {15569, 52291}`.

| arm | totally-positive α with `core(N) = 5` |
|---|---|
| **CONTROL (no repair)** | **0** ← reproduces the shipped producer's failure |
| repair `P₂` (idx 1, `f=4`) | 0 |
| repair `P₂` (idx 2, `f=4`) | 0 |
| **repair `P₃` (`f=2`, `e=6`)** | **3** |

So the obstruction is confirmed *by observation*, and **not every even-`f` prime lifts it** — only one
in the complementary narrow class does. The winner is exactly the fixer dive #52 predicted (the unique
prime above 3), at exactly the split prime it predicted (`q = 15569`).

Fingerprint of the three α at `q = 15569` (5,133 primes):

| `(a,b)` | lands | kernel dim | L1 | margin | rivals witness-killed | verdict |
|---|---|---|---|---|---|---|
| (1,2) | 24T22599 | 10 | 0.057 | 0.198 | 41 / 43 | REJECT (off-target) |
| **(1,3)** | **24T23297** | **11** | **0.064** | **0.852** | **42 / 43** | **GATED** |
| **(1,4)** | **24T23297** | **11** | **0.065** | **0.845** | **42 / 43** | **GATED** |

**The GATE question is answered: the even-`f` repair prime does not perturb the block kernel.** Two of
three radicals land the *aimed* sibling at `kdim = 11` with a decisive margin (0.85, only the full
wreath surviving witness exclusion). The (1,2) landing at `kdim = 10` is the **known `(a,b)` effect** —
test 0069 saw the same kernel wobble across `(a,b)` on bases with *no* repair at all (24T23664 → dim-9,
24T21376 → dim-10) — so it is not attributable to the repair. Dive #52's predicted pair (1,3) is one of
the two winners.

Both winners: deg-24, irreducible, `polsturm = 24`, **`nfisisom`-DISTINCT** (two independent shots at
the label, not a duplicate), field disc **2.366e68**, factoring over **{2, 3, 5, 29, 31, 61, 15569}** —
**fully smooth, max prime 15569 ≪ 10⁶**. The repair prime 3 was already in `disc K₀`, so as designed
**no new prime entered the disc**.

## The targets: the item was almost entirely spent before this build

Step-3 re-verification against a `progress.json` 31 minutes old rewrote the item:

| target | `teamCount` | our rows @ r=24 | status |
|---|---|---|---|
| 24T21904 | 2 | 2 (labeled) | held, **shared** |
| 24T21376 | 2 | 2 (labeled) | held, **shared** |
| 24T22401 | 2 | 2 (labeled) | held, **shared** |
| 24T24334 | 1 | 2 (labeled) | held, **sole** |
| 24T24492 | 0 | 2 (labeled) | held; tc=0 is **submission lag** |
| **24T23297** | **1** | **0** | **RIVAL holds it** |

Five of the six targets are already built and officially labeled — **without any repair**, exactly as
dive #53 predicted (the "no `q`/`(a,b)` can rescue `[Id] ≠ 0`" law holds only for a *rational* genus
character). The only target the repair was ever needed for is 23297, the genuinely rational, `q`-immune
base — and a rival took it.

**Two corrections to the record, both surfaced by this re-verification:**

1. **Test 0071's "24T24492 BLOCKED (12T288 has no completely-split prime below 300,000)" is wrong.**
   We *hold* `(24492, 24)`, officially labeled `24T24492`, built by that very producer at
   **`q = 420419`** (provenance `lit:mb2twsignnew:24492.24:base12T288:d10351121:q420419_1{4,5}`). The
   split-prime window was fine; the run just reported the block before the wider sweep landed.
2. **`(24492, 24)` is an uncollected sole-1.0, and it is *not* blank-risky.** Its rows carry
   `scoreable=False` with an empty disc, which reads like the disc-growth blank test 0069 warned about
   — but both polys' `gp.scoreable_disc` returns **1.3496e80 in 0.0 s** locally, and `d = 10351121 =
   11 · 941011` with `disc K₀ = 5⁶·11⁵·941011³` — every prime **under 10⁶**. So the blank is
   `discriminant_pending` (async SAIR disc scoring), not a failure: `teamCount = 0` here means *nobody
   is credited yet*, and it should resolve to a sole 1.0 on its own. **No build needed.**

## The enqueue: a deliberate, documented deviation (disc-undercut)

`(23297, 24)` is rival-claimed (`teamCount = 1`, we hold zero rows). The headless build gate's default
is **skip rival-claimed pairs** — that rule exists so a 0.5 never displaces a sole-1.0. I enqueued
anyway, and the reason is arithmetic:

> **The rival's discriminant on this pair is 2,474 digits. Ours is 69.**

Under `2^(1-k)·log(D0)/log(D)`:

| | now | after we join |
|---|---|---|
| us | 0 | **0.500** (`k=2`, `D0 = D_ours`) |
| rival | 1.000 (sole) | **0.014** |

A **+0.500 / −0.986 swing** — the largest per-pair swing on the board — for **2 polynomials out of a
1000/day budget**. Disc-undercut is also the repo's *current* official strategy (commit `6f787f1`,
2026-07-13: "the official slide is disc-undercut, not coverage"), which post-dates the skip-rival
default. The deviation is gated behind an explicit `--allow-shared` flag, not the producer's default.

Enqueued `lit:mb2twistfixnew:23297.24:base12T245:d5:rep3-1:q15569_1{3,4}` @130. **Both were submitted
and OFFICIALLY LABELED `24T23297` (r=24) by SAIR's Magma within the run** — the aimed sibling, first
try, on the authoritative gate. `(23297, 24)` is now realized by us at a 69-digit disc against the
rival's 2,474-digit one.

## Part 1 of the item (the narrow-class PRE-SCREEN) is REFUTED and was NOT shipped

The item asked for a `bnrisprincipal` bail-out before the `q`-loop, calling it "a pure saving with no
risk", and supplied a DEAD list: *23297, 21904, 21376, 22401, 24334, 24492*.

**Four of those six are now HELD with official Magma labels** (21904, 21376, 22401, 24334 — plus 24492).
Shipping the bail-out as specified would be a **false-negative generator** that refuses builds which
demonstrably succeed. This is dive #53's correction confirmed at the build: the `[Id] ≠ 0` law is only
`q`- and `(a,b)`-immune when the narrow character is a **rational genus character** (~10% of obstructed
bases, census N=322). The narrow-class computation remains useful as a **diagnostic** (it correctly
predicts *which* `(q, a, b)` works), never as a **skip**.

## Learnings

- **The repair is SAIR-VALIDATED on its first pilot** — both candidates returned the official Magma
  label `24T23297`, matching the aim. The `d = core(disc K₀)` sign map plus an even-`f` repair prime is
  now a labeled, not merely gated, construction.
- **The even-`f` divisor repair is real, safe, and cheap.** It lifts the `h⁺ > 1` sign obstruction
  without touching `d`, `χ`, the block kernel, or scoreability. It is now a reusable capability
  (`scripts/mb2_twist_evenf.py`) for the ~10% of sign-twist bases that are genuinely `q`-immune.
- **Not every even-`f` prime works** — only one in the complementary narrow class. Enumerate the arms
  and let the `matsolvemod` + `core(N)` gate pick; don't compute the class and trust it.
- **Run the control arm.** The no-repair arm returning 0 is what turns "the repair worked" from an
  assumption into an observation, for free.
- **A "BLOCKED" verdict in a prior test is a claim, not a fact — re-verify it.** Test 0071 called
  24492 blocked; it had in fact already built it. A stale block cost nothing here, but it was one
  refresh away from being mistaken for a real wall.
- **`scoreable=False` + blank disc ≠ blank-risk.** Check `gp.scoreable_disc` locally before believing
  a poly failed the grader — on 24492 it returns a clean smooth disc instantly, so the blank was async
  lag and the pair is an uncollected sole-1.0, not a rebuild target.

## Reproduce

```
.venv/bin/python scripts/mb2_twist_evenf.py --targets 23297                    # dry run (control + arms)
.venv/bin/python scripts/mb2_twist_evenf.py --targets 23297 --allow-shared --enqueue
```
Artifacts: `data/processed/mb2twist/evenf_winners.json`, `evenf_report.txt`.
