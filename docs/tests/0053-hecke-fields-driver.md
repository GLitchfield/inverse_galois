# Test 0053 — Hecke.fields driver stood up; 24T4 baseline UNLOCKED, small-solvable band mostly at floor

Family: literature-construction / small-|G| solvable (Hecke constructive-Shafarevich)
Date: 2026-07-07
Status: BUILT (24T4,0) + (24T4,24) enqueued (both beat D_base) / most spike targets BLOCKED [baseline at floor]
Build item: build_backlog "HECKE.FIELDS DRIVER — small-|G| solvable in-envelope sole-1.0s"

## Question

The SPIKE-READY agenda item proposed driving the OSCAR/Hecke `Hecke.fields`
(Sircana/Fieker) constructive enumerator to harvest ~23 open small-|G| solvable
degree-24 pairs (|G|=24/48/72). Two questions: (1) can we stand up a working driver
in the installed Julia/Hecke stack, and (2) are those pairs actually winnable?

## Setup

- Julia 1.12.6 + Hecke 0.39.15 + GAP.jl already installed (`~/.juliaup/bin/julia`).
  `Hecke.fields` lives in the **package extension `GAPExt`** (activates on `using Hecke, GAP`);
  added `GAP` to the v1.12 environment so the extension loads.
- Driver `scripts/oscar/hecke_fields.jl`: for a regular action (|G|==n, the |G|=24 groups)
  the degree-24 field IS its own Galois closure → `Hecke.fields(id, bound)` directly; for
  |G|>n, enumerate the closure tower and extract the degree-n subfield for the conjugacy
  class whose coset action has `TransitiveIdentification == t`. A disc-MIN bound-doubling
  loop (×4) finds the minimal-disc field.
- Python wrapper `scripts/hecke_fields_build.py`: runs the driver, then LOCAL-GATES each
  field — polredabs, deg-24 + irreducible, `polsturm == r`, **Frobenius-density label L1 to
  24Tt** (`gap.cycle_type_distributions`), `gp.scoreable_disc` (no blank-risk), and — because
  every spike target is a BASELINE pair — `baseline.beats_baseline` (nfdisc STRICTLY < D_base;
  a tie never scores, test 0047). Enqueues survivors `lit:hecke<tier>:<t>.<r>:hecke`.

## Two Hecke library bugs (worked around)

Hecke VN62X's own `fields_transitive_group`/`_find_discriminant_bound` (non_normal.jl) is
broken in this version: (a) line 63 `ind = i` indexes the subgroup-CLASS list by the
transitive-group number `i` → out of range (`lC[32]` for a group with <32 subgroup classes);
(b) the Frobenius branch's `root(disc^k, n-1)` throws on a non-perfect power (hit by C24 and
24T32). The driver bypasses both: it treats the enumeration bound as the Galois-closure disc
bound directly and does its own transitive-`t` subfield selection.

## Baseline trap: ALL spike targets are baseline pairs

Re-verifying against `progress.json` + `igp.baseline`: every one of the 20 listed spike
targets (|G|=24/48/72, 24T1/2/3/4/7/32/35/21/23/28/65/81/82/84) has `in_baseline=True`. The
agenda item verified `teamCount==0` but never checked `in_baseline` — the exact omission test
0047 caught for the abelian tail. So each is winnable ONLY by beating D_base.

## Result

| target | path | verdict |
|---|---|---|
| 24T1 r=24 (C24) | Galois | count=0 under unramified_outside=[2,3] (over-constrained; driver-smoke only) |
| **24T4 r=0** | Galois | **WIN — minimal field disc = 3¹⁸·5¹⁸·7²² = 5.778e39 < D_base 6.379e39** |
| **24T4 r=24** | Galois | **WIN — same disc 5.778e39 < D_base 6.379e39** (teamCount=1, disc-improve/unlock) |
| 24T7 r=24 | Galois | count=0 at cap=D_base−1 → **baseline at floor (unwinnable)** |
| 24T32 r{0,8} | non-normal | fix RAN (no crash — validates the workaround); count=0 up to closure disc 2.9e57 → winnability unresolved (min field would need closure enum ~1e72, intractable) |

**24T4 is the win.** The minimal 24T4 (order-24 non-abelian, SL(2,3)-type) field has
discriminant `3¹⁸·5¹⁸·7²²` ≈ 5.778e39, strictly below LMFDB's baseline 6.379e39 for BOTH
signatures it realizes (a totally-real r=24 form and a totally-complex r=0 form, same |disc|).
Local gate on both: deg-24 irreducible, polsturm 24/0, **density L1(24T4) = 0.024 / 0.026 with
0 impossible cycle types** (unambiguously 24T4, not a Gassmann cousin), disc fully smooth
(largest prime 7 ≪ 10⁶ → no blank-risk), `beats_baseline` True. (24T4,0) is teamCount==0 OPEN;
(24T4,24) is teamCount==1.

## Enqueued

- `lit:hecke*:4.0:hecke` (r=0) and `lit:hecke*:4.24:hecke` (r=24), 1 model each, both
  strictly sub-baseline → SAIR labels + disc pending.

## Learnings

- **The Hecke driver works** and is reusable (`scripts/oscar/hecke_fields.jl` +
  `scripts/hecke_fields_build.py`), with the two library bugs worked around. This unblocks
  future small-|G| solvable harvesting.
- **The small-solvable baseline band is mostly at the floor, as expected**: LMFDB's baseline
  for classical small solvable groups was itself built by complete small-disc enumeration
  (often this very machinery), so we usually can only TIE. 24T7 confirms floor; 24T4 is the
  exception where LMFDB's baseline was NOT minimal (we beat it by ~9%).
- **Non-normal (|G|>24) winnability is intractable here**: the closure enumeration a
  sub-baseline field needs (~1e72 closure disc for |G|=48) is far beyond what completes. The
  workaround is validated but the |G|≥48 harvest is not reachable via closure enumeration in
  PARI/Hecke at these disc scales.
