# Test 0059 — PGL-wreath Tier-A: the four missing r-values of the full PGL(2,7) wreaths

**Family:** mb8 (minblk=8 octic-over-cubic, PGL(2,7)=8T43). **Date:** 2026-07-10.
**Producer:** `scripts/mb8_tierA.py` (reuses `scripts/mb8_harvest.py` build/density primitives).
**Backlog item:** build_backlog "PGL-WREATH Tier A" (top Ready).

## Goal

Land the four missing signatures of the two full PGL(2,7) wreaths, all VERIFIED `teamCount==0`
OPEN and non-baseline (`is_baseline=False` → score on any valid disc, sole-1.0 each):

- (24672,10), (24672,16) — 24672 = PGL(2,7)≀S3 (block-3 action S3)
- (24592,8),  (24592,16) — 24592 = PGL(2,7)≀C3 (block-3 action C3)

The construction (already SAIR-validated for these groups in test 0046) is the Malle Thm-5.1 octic
over a cubic base:

    F(X) = Res_y( c(y), f_Malle(a, y, X) ),   f_Malle = Thm-5.1 PGL(2,7)=8T43 octic, param t=y.

Three conjugate octic blocks over the 3 cubic roots; S3 cubic → 24672, C3 cubic → 24592.

## Setup — the block-window map (the r-lever)

The deg-24 real-root count `r` = Σ over the 3 REAL cubic roots of the per-block octic real count.
Mapping the octic's `polsturm` as a function of the real parameter `t` (integer scan `t∈[-2000,2000]`)
gives a step function `W_a(t)` with only three values {0,2,8}:

| a  | 8-block window (W=8) | 0-block threshold (W=0, one-sided) | else |
|----|----------------------|------------------------------------|------|
| −1 | t∈[0,3]              | t≥16                               | W=2  |
| −2 | t∈[−2,33]            | t≥99                               | W=2  |
| −3 | t∈[−6,124]           | t≥299                              | W=2  |

a>0 gives no 8-block at all. **Crucially the 0-region is ONE-SIDED** (large positive t only;
t→−∞ gives W=2). So each 0-block costs exactly one large positive cubic root. Hence:

- (24672,10) = block pattern (8,2,0): one window root, one mid/neg (→2), one large. **BUILDABLE** (S3).
- (24672,16) = (8,8,0): two window roots + one large. **BUILDABLE** (S3, non-depressed cubic).
- (24592,16) = (8,8,0): two window roots + one large. **BUILDABLE** (C3, Shanks large-k).
- (24592,8)  = (8,0,0): needs **TWO** large positive roots. **BLOCKED**.

### Why (24592,8) is geometrically impossible over any C3 cubic

24592 forces a **cyclic** (C3) cubic base. A totally-real cyclic cubic's Galois generator is a real
Möbius map of order 3 with no real fixed points — a projective 120° rotation of RP¹. The three real
roots are one orbit of that rotation, so **at most one** can lie near the projective point +∞
(the 0-region). Two 0-blocks (two roots ≥ threshold near +∞) are therefore unreachable.
Numerically confirmed: 0 hits for r=8 across Shanks `k∈[-5,320] × a∈{-1,-2,-3}` (and 0 across the
root-window analytic scan). This is not a search gap — it is a property of the construction × the
C3 root geometry.

## Result

Built via `mb8_tierA.py --limit 3 --hi 6000`, local gate = deg-24 irreducible + `polsturm`==r +
smooth poldisc (<10⁶, disc-scoreable) + Frobenius-density label check (`density_ok`, ~780 good
primes, DIST_POOL = the 24672/24592 twins + twists 24593/24489/24594/24316/24488 + Gassmann
neighbour 24315). Every candidate's best density match was the intended group with **0 impossible
cycle-types** — the gate cleanly separates 24672 (S3 top) from 24592 (C3 top):

| pair        | models | density (best_t, L1, impossible) | enqueue tag                    |
|-------------|--------|----------------------------------|--------------------------------|
| (24672,10)  | 3      | 24672, L1 0.28–0.29, imp 0       | `lit:mb8pair:24672.10:*` @115  |
| (24672,16)  | 3      | 24672, L1 0.25–0.27, imp 0       | `lit:mb8pair:24672.16:*` @115  |
| (24592,16)  | 3      | 24592, L1 0.19–0.25, imp 0       | `lit:mb8pair:24592.16:*` @115  |
| (24592,8)   | 0      | BLOCKED (geometric, see above)   | —                              |

**9 candidates / 3 pairs enqueued** (tier "pair": both groups already present in `realized.csv`),
coeffs stored as ascending 25-int lists (test-0046 malformed-string trap avoided). SAIR Magma labels
pending at build time — the construction shape is already SAIR-confirmed for both groups (test 0046),
so no fresh validation-first wait was needed; these are new r-values of the same shape.

## Learnings

- The octic block-window map is the exact r-lever for the whole mb8 family: r decomposes as a sum
  of per-block {0,2,8} counts, and the 0-block is one-sided. This both *builds* the S3 targets and
  *proves* the C3 (8,0,0) target unreachable.
- **Non-depressed** integer cubics (with a y² term) are required to place two window roots + one
  large root; `mb8_harvest.s3_cubics` (depressed, root-sum 0) structurally can't → why the earlier
  full-pool sweep found none of these r-values.
- (24592,8) is the first mb8 target BLOCKED by base-field *geometry* rather than the deg-192
  module wall (Route B) or fix8-death — a distinct failure class worth recording.

## Outcome

`[PARTIAL: 3 pairs (24672 r{10,16} + 24592 r16) enqueued / (24592,8) geometrically BLOCKED]`
