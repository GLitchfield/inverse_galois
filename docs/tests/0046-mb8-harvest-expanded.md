# 0046 — minblk=8 octic-over-cubic HARVEST-EXPANDED build (full-wreaths + family-sufficiency)

Family: mb8 (minblk=8 non-solvable-block octic-over-cubic). Follows the 07-07 harvest census
(auto_log, test 0045). Builds the OPEN full-wreath targets on the certified octic-over-cubic
pipeline and splits the 39 fresh pairs by family-sufficiency.

## Question

The harvest census surfaced 9 NEW open (teamCount==0) targets / 39 fresh sole-1.0 candidate
pairs with the certified octic-over-cubic shape. Before mass-building: (1) does the GENERIC
disjoint-block resultant land the FULL WREATH (as hypothesised) or collapse to a twist /
Gassmann neighbour? (2) which of the 39 pairs are reachable by the plain a-family vs need the
fix8 deformation? (3) build the reachable full-wreath subset.

## Method

Construction `F(X) = Res_y(c(y), f(a,y,X))`: specialise Malle Thm 5.1 PGL(2,7)=8T43 octic
`f(a,t,X)=X*(X^7+X^6+14aX^5+7aX^4+49a^2X^3+14a^2X^2+49a^3X+7a^3)+t*(7X^2+X+1)` at the octic
parameter `t = y` over a small-disc cubic `c(y)` of the target's block-3 type (3T2=S3 /
3T1=C3), then `polredabs`. Res over a cubic = product of 3 conjugate octic blocks. Scripts:
`scripts/mb8_harvest.py` (build + density gate + smooth-poldisc gate + enqueue),
`scripts/mb8_family_suff.g` (per-block involution fixed-point decomposition),
`scripts/mb8_gdist.g` (degree-24 Frobenius cycle-type distributions → `data/targets/mb8/dist_*`).
Authoritative labels via direct SAIR submit + poll. AGL targets via the sibling
`scripts/mb8_affine.py` (Malle Thm 6.1 AGL(3,2)=8T48).

## Result — full-wreath hypothesis CONFIRMED (both PGL)

Direct SAIR/Magma labels on trial builds:

| cubic type | build | SAIR label | r | verdict |
|---|---|---|---|---|
| S3 (3,0), `y^3-4y-1`, a=-2 | Res | **24T24672** | 24 | full wreath PGL(2,7) wr S3 |
| C3 (Shanks `y^3-2y^2-5y-1`), a=-1 | Res | **24T24592** | 12 | full wreath PGL(2,7) wr C3 |
| same C3, a=-2 | Res | **24T24592** | 24 | full wreath (2nd r confirmed) |

The generic disjoint-block Res lands the FULL WREATH — it does NOT collapse to the twist 24315
or a Gassmann neighbour. Local density pre-check corroborates decisively: a 24672 candidate
matches 24672 at L1≈0.27 with **0 impossible cycle types**, while every twist (24315/24593/…)
shows **214–462 impossible observed cycle types** (blocks are independent = full wreath). A C3
candidate flips to 24592 best (L1≈0.20). Steering map pinned: **S3 cubic → 24672, C3 cubic →
24592**, no twist-steering needed for the full wreaths.

## Result — family-sufficiency split of the 39 pairs (mb8_family_suff.g)

Per-block involution fixed-point menu: PGL 8T43 (a in {-1,-2}) = **{0,2,8}**; AGL 8T48 Thm 6.1
= **{0,4}** (8 needs fix8). An r is plain-family reachable iff some block-fixing conjugacy
class has per-block vector summing to r with every entry in the menu.

- **(a) plain-family reachable = 33 pairs = ALL 7 PGL (8T43) targets**, every one via a (3,0)
  cubic (none needs (1,1)):
  - 24672 r{8,10,12,16,18,24} (6) · 24592 r{8,12,16,18,24} (5) · 24593 r{0,4,8,12,16,24} (6) ·
    24489 r{0,8,12,16,24} (5) · 24594 r{4,8,12,16,24} (5) · 24316 r{8,16,24} (3) ·
    24488 r{8,16,24} (3)
- **(b) needs fix8 deformation = 6 pairs = ALL AGL (8T48) targets:**
  - 24922 r{16,20,24} (3) · 24916 r{16,20,24} (3)

AGL confirmed EMPIRICALLY: `mb8_affine.py --target 24922 --cubic S3 --a-lo -10 --a-hi 10`
reaches only **r=8 and r=12, never r≥16** — the {0,4} menu caps a totally-real-cubic build at
4+4+4=12. The AGL open pairs are exactly r{16,20,24}, and r=8/12 are rival-claimed (tc=1). So
the 6 AGL pairs are handed to the **fix8 agent**; no sole-1.0 is reachable there by the plain
family.

## Result — scoreability gate (important correction)

Verified builds return `status=accepted` (label correct) but `scoringStatus=pending`,
`scoringReason=discriminant_pending` — disc scoring runs ASYNC after Magma verification, so an
early poll shows `scoreable=False` (NOT a rejection). The real scoreability predictor is
**POLDISC smoothness**: SAIR's bounded disc factorization terminates (→ the pair scores) only
when the submitted poly's poldisc has no prime factor above ~10^6. `gp.scoreable_disc`
(nfdisc-completes) is INSUFFICIENT — nfdisc completes locally in ms even when poldisc carries a
rough prime (PARI ECM-factors it; SAIR's bounded trial division does not). `mb8_harvest.build`
now gates on `factor(poldisc,10^6)` cofactor == 1. C3 (Shanks, square-disc) cubics are
systematically smooth; S3 cubics are hit-or-miss (swept for smooth hits).

## Enqueued (tier new @130) — 7 of 11 PGL full-wreath pairs

Smooth + density-consistent candidates, 3 per pair (21 rows): **24T24672** r{8,12,18,24} ·
**24T24592** r{12,18,24}. Daemon processed all 21 → **19 submitted, 2 dup**.

**Missing 4 pairs: 24672 r{10,16}, 24592 r{8,16}.** These need mixed per-block real counts
(r=8=8+0+0, r=10=8+2+0, r=16=8+8+0) — a cubic whose 3 real roots land simultaneously in the
octic's totally-real / 2-real / 0-real t-intervals. Three sweeps (~2500 cubic×a builds) hit
r{8,12,18,24} readily but never the mixed 10/16; they need targeted cubic construction with
prescribed root placement (follow-up). Group-theoretically reachable (PGL menu {0,2,8}).

**Enqueue gotcha (fixed):** the daemon `ready` handler returns `payload["coeffs"]` and gates on
`len(co)==25` — so `coeffs` MUST be a **list of ints**, not a comma string (a string fails as
`malformed`). `mb8_harvest.py` passes a list; ad-hoc enqueue scripts must too.

## Learnings

- Generic disjoint-block Res = full wreath, triple-confirmed (label + density + order); twist
  subgroups need correlated blocks (Route B, deferred to the twist/sibling track).
- Family-sufficiency (group menu) ≠ scoreability. Two independent gates: menu decides r-reach,
  poldisc-smoothness decides whether the accepted pair actually scores.
- `scoreable=False` on a fresh poll is pending-lag, not rejection — must re-poll or trust the
  smooth-poldisc predictor.
