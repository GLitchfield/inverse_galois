# 0069 — `general_c2_TWIST` AIMED by the sign character: the dive-#50 shortlist

**Family:** MINBLK=2 / imprimitive tower (`general_c2` + complement-cocycle twist)
**Date:** 2026-07-13 (headless build loop)
**Backlog item:** `[MINBLK=2] general_c2_TWIST, AIMED — the sign-character shortlist (dive #50)`
**Recipe pointers:** `docs/auto_log.md` dives #49 (engine) + #50 (the aim); `scripts/mb2_twist.py`,
`scripts/mb2_twist_producer.py` (the dive-#49 engine, unchanged as the reference)
**Producer (new, reusable):** `scripts/mb2_twist_sign_producer.py`
**Outcome:** `[BUILT: 5 candidates / 5 tc=0 pairs enqueued — PILOT, SAIR labels pending]`

## Question

Dive #49 built the complement-cocycle engine but had to *screen* each base for a reachable norm
class `d`, then accept whatever sibling that `d` happened to aim at. Dive #50 claims the aim is
free: take `χ = χ_sgn` (the sign character of the top `H`, kernel `H ∩ A₁₂`), which cuts out
`Q(√disc K₀) ⊂ M` **unconditionally**, so

    d = core(disc K₀)

is a reachable norm class for every base whose top is not inside `A₁₂`, with no screening, and it
aims at exactly one sibling `G_{χ_sgn}`. Dive #50 turned that into a lookup table of 11
`(target, base, d)` triples. **Does the table build?**

## Setup

- Targets: the 11 dive-#50 triples. All re-verified against `data/processed/progress.json`
  (refreshed 2026-07-13 03:16, 7 min before the build): **all 11 `teamCount == 0`, non-baseline,
  `minimumDiscAbs = None`, and zero rows in `realized.csv`** — genuinely open, sole-1.0 on any
  valid disc.
- Sibling libraries: `scripts/mb2_multi_gdist.g` over each of the 11 tops (submodules × complement
  classes → cycle-type densities). Built fresh; cached to `data/processed/mb2twist/lib<top>.txt`.
  **Structural pre-check passed: every one of the 11 targets is a dim-11 sibling of its stated top**
  (so dive #50's table is at least self-consistent with the module theory).
- Construction: `α = gen(P_{q,a} · P_{q,b} · ∏_{p|d} P_p)`, `q` completely split, `|w|` even, `P_p`
  of odd residue degree; totally-positive unit twist ⇒ `r = 24` deterministically.
- Gate (unchanged from dive #49, plus one addition): 780-prime Frobenius density fingerprint,
  **L1 < 0.35**, **runner-up margin > 0.15**, **kdim == 11**, **and the fingerprinted group must BE
  the intended target** (dive #49's producer accepted any gated open sibling; aiming means the aim
  has to be checked). Then deg-24 / irreducible / `polsturm == 24` / `gp.scoreable_disc` non-blank.

## Two corrections to the handed-off recipe

**(1) The `q` window was too small by two orders of magnitude — this is what "no candidate" meant.**
The engine searched `q ∈ [100, 6000]` for a completely-split prime. Split density is `1/|H|`, and
dive #49's demo tops were *small* (`|H| = 36..72`), so that window always held one. **This
shortlist's tops run to `|H| = 28800`** (12T156→432, 12T167/170/175→648, 12T192→768, 12T207→1152,
12T245→2592, 12T253→3456, 12T274→10368, 12T281→15552, 12T288→28800), where the expected number of
split primes below 6000 is **0.03**. The first run reported "no candidate radical" on 24T23664 —
an *arithmetic* miss, not a structural obstruction; a naive read would have marked the item REFUTED.
The window must scale with `|H|`, and its ceiling is set by **scoreability**: `q` ramifies in
`K/K₀`, so `q` divides the degree-24 disc, so `q < 10^6` (the grader's factorization bound). Search
upward from 100 and take the smallest hits. `polrootsmod(f, q) == 12` is the cheap split test
(`idealprimedec` over ~78k primes is not). With `QMAX = 10^6` every top has ≥ ~2.7 expected split
primes, and all six built targets found one.

**(2) The `h = 2` base needs a principality guard, and it is a correctness bug, not a filter.**
`bnfisprincipal`'s second component is only a generator when the first vanishes. Using it regardless
would have silently built the radical of the **wrong element**. Guarded (skip non-principal
`(q,a,b)`); with `h = 1` bases it is a no-op, since every ideal is principal.

## Result — 5 GATED on-target, on 5 DISTINCT targets, all enqueued

| target | top / \|H\| | d | q | L1 | runner-up | disc (all <10⁶-smooth) |
|---|---|---|---|---|---|---|
| 24T23664 | 12T253 / 3456 | 3 | 52009 | 0.149 | 0.356 | 6.7e61 |
| 24T21904 | 12T192 / 768 | 37 | 31153 | **0.121** | 0.373 | 2.7e57 |
| 24T21572 | 12T167 / 648 | 89 | 2371 | 0.186 | 0.422 | 2.9e50 |
| 24T21376 | 12T156 / 432 | 101 | 3061 | 0.182 | 0.342 | 3.9e64 |
| 24T22401 | 12T207 / 1152 | 1129 | 18457 | 0.140 | 0.457 | 3.8e70 |

All five: deg-24 irreducible, `polsturm == 24`, `scoreable_disc` non-blank. Enqueued
`lit:mb2twsignnew:<t>.24:...` @130 (tier **new** — we hold zero rows for all five groups). The
daemon submitted all five within minutes.

**The gate is doing real work, not rubber-stamping.** Of the radicals fingerprinted, several landed
a *different kernel dimension* than the target and were rejected: 24T23664's first two `(a,b)`
choices landed a **dim-9** kernel (24T22294), and 24T21376's first landed **dim-10** (24T20338).
The `(a,b)` choice moves the kernel; only the even-weight ones reach dim 11.

## The two that did NOT gate — both honest, neither refuting

- **24T21582 / 12T170.** Three radicals landed the target on-target at **kdim 11** (L1
  0.154–0.176) — but the **runner-up was 0.157–0.183**, i.e. margin ≈ 0.00–0.03, far under the 0.15
  bar. **The three dim-11 siblings over 12T170 are not density-separable.** This is the
  family-specific resolution limit test 0067 already flagged ("a density gate's resolution must be
  measured, not assumed"): the fingerprint cannot tell 21580/21581/21582 apart, so a gated enqueue
  here would be a coin-flip we could not audit. Correctly refused.
- **24T23297 / 12T245.** Split primes found (15569, 52291), `h = 1` so principality is free, but
  **no `(q,a,b)` produced a totally-positive α with `core(N(α)) = 5`** — the sign-fix
  `matsolvemod` is unsolvable or the norm lands in the wrong square class. This is the `h⁺ > 1`
  obstruction shape (cf. test 0062's 12T1/q71 p4 case), not a failure of the sign map.

Untouched (pilot cap reached): 24T21593, 24T24334, 24T24157, 24T24492.

## Status on the evidence ladder

**LOCAL-GATED → PILOT (enqueued), NOT yet PILOT-LABELED.** The dive-#49 engine's own SAIR labels
(test 0068's five candidates on 24T19241 / 24T18461) had **still not returned** when this ran, so
*nothing in this family carries an official Magma label yet*. Five distinct targets over five
distinct bases each landing its predicted sign sibling is the strongest local evidence the map
could give — but it is local evidence. **Do not scale the remaining 6 targets until an official
label matches.** If a label comes back as a *sibling* rather than the target, the sign map is
mis-aimed and the item is `[REFUTED]`.

## Reproduce

```
.venv/bin/python scripts/mb2_twist_sign_producer.py --ncand 4 --pilot 5 --per-target 1 --enqueue
```
Sibling library for one top: `gap -q -b -c 'TOP:=253;' scripts/mb2_multi_gdist.g`.
Artifacts: `data/processed/mb2twist/sign_winners.json`, `sign_report.txt`, `lib<top>.txt`.
