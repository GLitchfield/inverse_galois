# 0049 — minblk=8 fix8 (r=24) unblock: seed-deformation DEAD, Route-B sized S=1/smooth

**Family:** minblk=8 octic-over-cubic affine cluster (14051/14052/16060/16061/19280/20408).
**Date:** 2026-07-07.
**Question:** two coupled things feeding the affine build — (Part 1) size the direct-radical
(Route B) model with three cheap PARI/GAP probes; (Part 2) build the greenlit fix8
seed-deformation family to unblock the r=24 (totally-real) pairs (up to 10 sole-1.0s).

Targets re-verified tc=0 on every pair vs `progress.json`; none in `realized.csv`.
Seed field (bnfinit once): `x^8-2x^7-17x^6+15x^5+53x^4-x^3-37x^2-15x-1` (LMFDB
8.8.410449079569.1, totally-real 8T48=AGL(3,2), field disc `640663^2`, classno 1).

## Part 1 — Route-B sizing probes (all three decisive)

**(a) Diagonal module-generation (`scripts/mb8_routeb_diag.g`).** Does ONE totally-split
prime generate the full 9-dim `3(+)6` kernel of 19280/20408 *including* the C3-trivial
diagonal `(C2)^3`, or is the diagonal separately-sourced (=> S≥2)?
- **Verdict: S=1 for module generation; the diagonal is NOT separately sourced.**
- GAP: 19280/20408 kernel `(C2)^9`, comp-factor dims `[3,6]`, **CYCLIC** (max single-vector
  `F2[G]`-span = 9 of 9). `Fix_C3(N)` = **3** (the diagonal), confirming the `3(+)6`.
  14051/16060 kernel `(C2)^6` **irreducible** (`cfdims [6]`), also cyclic.
- Mechanism: a prime with 8 factors in the degree-8 seed ⟺ Frob=1 (the 8-point AGL action
  is faithful) ⟺ totally split in the closure ⟹ contributes the **regular** `F2[Γ]`-module
  of square-classes, which surjects onto any **cyclic** module. V cyclic ⟹ one totally-split
  prime generates all 9 dims incl. the diagonal. (A non-generic single class *can* miss the
  diagonal — the all-ones seed spanned only 6 of 9 for 19280 — but a generic prime's full
  regular contribution spans all 9.)
- **Correction logged:** my first pass tested `Hom_F2G(Perm24, V)` and got 0 — that used the
  wrong module (24-point permutation `F2[G/point-stab]`, not the regular `F2[G/1]` a
  totally-split prime gives). The correct criterion is **cyclicity**, which holds.
- **Resolves the agenda's module-dim conflict:** 14051 = `(C2)^6` IRREDUCIBLE-6; 19280 =
  `(C2)^9 = 3(+)6`. Confirms the affine-cluster record; the Route-B item's "3-dim(14051) /
  6-dim(19280)" was wrong.

**(b) Sign-fixing (`routeb_1b_v2.gp`).** For the smallest totally-split primes, is a
principal generator reachable to totally-positive by the unit-sign image, or is S≥2 forced?
- **Verdict: S=1 achievable with one well-chosen small totally-split prime.**
- classno 1; unit-sign image **rank(U)=7 of 8** ⟹ totally-positive units mod squares = **dim
  1**; U is a hyperplane (codim 1), so a random square-class is unit-fixable to totally-positive
  with prob 1/2.
- Per prime: q=10853 → 4/8 gens in U (not clean); **q=21557 → 8/8 in U** (its *entire*
  square-class contribution is unit-fixable ⟹ any natural-module class realizable
  totally-positive ⟹ clean S=1); q=30881 → 4/8.
- **Constructive confirmation:** built `theta` = `pi_1(q=21557)·(sign-correcting unit)` with
  `nfeltsign = [+1]×8` (totally positive); `seed(√theta)` = degree-16, `polsturm=16`.
- Empirical: S=1 typical (~half the small split primes clean). S=2 only if forced to the
  smallest prime q=10853 for a class in its non-fixable half.

**(c) Scoreability edge (`probe_1c*.gp`).** Direct split-radical vs the octic-over-cubic Res
family on disc smoothness.
- **Verdict: direct-radical (Route B) is DECISIVELY smoother — prefer it for scoreability.**
- Direct-radical proxy `seed(√theta)` at q=21557: disc bitlen 108, primes **`{2, 21557,
  640663}`**, largest 640663 **< 10^6 ⟹ fully smooth / scoreable**.
- Res-family (Malle Thm 5.1 PGL Res, (24672,24) representative): disc bitlen 287, small primes
  `{2,7,37}` but a **165-bit cofactor with a prime > 10^6 ⟹ blank-risk / non-scoreable**.

## Part 2 — fix8 seed-deformation family: BLOCKED

Deform the seed `f_u(X) = s0(X) + u·g(X)` and fiber over a cubic. Residual: pick g keeping
`f_u` irreducible + 8T48 across a real fix8 interval AND at u=y.

- **Linear pencils are DEAD (`scan_g2.gp`):** 16 low-degree g (`1, x, x², x³, x²−x, x⁴..x⁷,
  …`) × 9–11 sampled u — **every (g,u) gave 40320T50 = S8.** The AGL(3,2) locus is thin; a
  pencil through s0 escapes to S8 generically (Hilbert: generic fiber = generic group).
- **2-seed pencil (`scan_alt.gp`):** `s0 + u·(s1−s0)` with s1 = another totally-real 8T48
  seed — still S8-generic (only the trivial endpoint u=1 = s1 is 8T48).
- **Pure translation:** `Res_y(cubic, s0(X−y))` is **reducible** — the `[1,3,8,24]` diagonal
  collapse (all blocks share the roots θ_j, only shifted).
- Combined with Malle Thm 6.1's known fix4-cap (auto_log 07-07), **no simple parametric fix8
  8T48 family exists.** A fix8 + varying-affine octic *requires* the radical-module
  construction with totally-positive radicands = Route B.

**Nothing enqueued.** The seed-deformation route is dead; the direct-radical Route B (sized
here as S=1 / disc-smooth) needs the relative L3(2)-over-cubic + Chebotarev module build (top
group C3×L3(2) order 504 ⟹ relative, not absolute bnfinit), not completed this session. The 4
mandatory gates (`gate()`) would reject any collapse/wrong-label attempt regardless.

## Build / artifacts

- `data/processed/routeb_probe.json` — all Part-1 verdicts + Part-2 finding (reproducible).
- `scripts/mb8_routeb_diag.g` — Part-1a GAP module/cyclicity/diagonal probe.
- `scripts/mb8_fix8.py` — reusable: `--scan` (reproduces the S8 finding), `--direct-proxy`
  (Route-B smooth-disc demo), `build_res()` (certified octic-over-cubic Res pipeline, reusable
  the instant a valid fix8 8T48 family exists), `gate()` (the 4 mandatory gates), `--enqueue`
  (gated r=24 → lit:mb8new/pair/alt, tiers 130/115/100; enqueues nothing without a family).
- scratchpad: `routeb_1b_v2.gp`, `scan_g2.gp`, `scan_alt.gp`, `probe_1c_dr3.gp`, `probe_1c.gp`.

## Learnings

1. **The r=24 unblock is a RADICAL-MODULE problem, not a family problem.** Every family route
   is walled: naive pencils → S8, Malle Thm 6.1 → fix4-cap, translation → collapse. Route B
   (direct totally-positive radical) is the only path and is now sized: **S=1, disc-smooth.**
2. **Cyclicity, not the permutation module, is the right generation criterion.** A
   totally-split prime gives the *regular* module (Frob=1), which surjects onto any cyclic
   module — so the C3-diagonal comes for free from one prime.
3. **The totally-positive-unit hyperplane (rank 7/8) makes sign-fixing a coin-flip per prime**
   — q=21557 is a clean S=1; the disc stays `640663^(2c)·q^e`, all < 10^6.
