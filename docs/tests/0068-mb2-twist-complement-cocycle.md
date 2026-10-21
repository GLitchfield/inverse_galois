# Test 0068 — `general_c2_TWIST`: the complement-cocycle engine, pointed at the OPEN board

**Family:** minblk=2 / `general_c2` radicals over totally-real degree-12 bases
**Date:** 2026-07-13 (headless build loop)
**Backlog item:** `[MINBLK=2] general_c2_TWIST — the COMPLEMENT-COCYCLE engine (dive #49)`
**Code:** `scripts/mb2_twist_producer.py` (build + local gate + enqueue), `scripts/mb2_twist_prefilter.g`
(board pre-filter), on top of dive #49's `scripts/mb2_twist.py` and `scripts/mb2_multi_gdist.g`.

## Question

Test 0067 proved a split-prime radical always lands the **split** sibling of `C₂≀H` (χ = 1, 497/497),
while the open minblk=2 pairs are the **twisted** siblings. Dive #49 identified the dial — χ is the
Galois character of `Q(√N(α))` — and validated a mixed-divisor engine on four demo bases whose
siblings are all CONTESTED. The item's own honest caveat: *"the payoff depends on finding a passing
base over a top that carries a tc=0 twisted sibling"*. **Does such a base exist in the h=1 pool?**

## Setup

1. **Screen** (`mb2_twist.py --screen --limit 400`): a base admits a twist `d` iff every `p | d` has a
   prime of ODD residue degree in `K₀` and `kronecker(d, p) = +1` for all 40 completely-split `p`
   (i.e. `Q(√d) ⊆ M`). **120 of ~400 LMFDB totally-real h=1 degree-12 fields pass, over 48 tops.**
2. **Board pre-filter** (`mb2_twist_prefilter.g`, new): per passing top, enumerate ONLY the dim-11
   submodules of `F₂¹²` and ALL their complement classes → the `24Tt` a dim-11 landing can BE. Cross
   it against a fresh `progress.json` (`teamCount == 0`), `igp.baseline`, and `realized.csv`. Costs
   zero submissions and zero `gp` builds: a top whose dim-11 siblings are all contested is never built.
   Runtime ~90 s for all 48 tops (vs. the full submodule-lattice library, which is minutes/top).
3. **Build + gate + enqueue** (`mb2_twist_producer.py`): mixed divisor `α = gen(P_{q,a}·P_{q,b}·∏_{p|d} P_p)`
   × totally-positive unit twist ⇒ r = 24; 780-prime Frobenius fingerprint; gate L1 < 0.35, runner-up
   margin > 0.15, kdim == 11; then `rnfequation` → `polredbest` → deg-24 irreducible ∧ `polsturm` == 24
   ∧ `gp.scoreable_disc` non-blank; enqueue tier `new` (@130) / `pair` (@115).

## Board census — where the payload actually is

The 48 passing tops carry **151 dim-11 siblings**. Exactly **three** are tc=0, non-baseline AND held by
zero rows (tier `new`): **24T18009** (12T36), **24T18019** (12T38), **24T19336** (12T80). A further
~17 dim-11 siblings have an **open (t, 24) pair** while we hold the group at some other `r` (tier
`pair`) — those score a sole 1.0 just the same, and turned out to be where the engine actually lands.

## Result — 5 candidates enqueued on 2 open pairs

| landing | base | d | pair | tc | L1 (runner-up) | disc | n |
|---|---|---|---|---|---|---|---|
| **24T19241** | 12T76 | 13613 | (19241, 24) | **0** | **0.087–0.105** (0.90–0.92) | 5.73e50 | 3 |
| **24T18461** | 12T49 | 2 | (18461, 24) | **0** | **0.124–0.131** (0.40–0.41) | 6.6e47 / 1.06e49 | 2 |

Both pairs re-verified tc=0 + non-baseline against a `progress.json` refreshed the same day; both
score a **sole 1.0** on any valid disc once Magma confirms the label. All 5 are degree-24 irreducible,
`polsturm` = 24, discriminant fully <10⁶-smooth (no grader blank-risk). Enqueued
`lit:mb2twistpair:{19241,18461}.24:...` @115; the daemon submitted all 5 within minutes.

The 19241 gate is the most decisive fingerprint this family has produced: **L1 = 0.087 against a
runner-up of 0.920** — a 10× margin, not a coin-flip between Gassmann cousins.

**Not built (engine landed elsewhere):** the three tier-`new` targets. Each of 12T36/12T38/12T80 has
exactly ONE reachable `d` in the h=1 pool, and it selects a CONTESTED sibling (12T36 → 24T18008,
12T38 → 24T18017, 12T80 → 24T19335 — all tc ≥ 1, all already held). See Learnings.

## Learnings

1. **The dive-#49 mechanism reaches genuinely open groups — the engine is real, not a demo.** Dive #49
   could only show it on contested siblings. With the board pre-filter to aim it, the same engine
   landed two tc=0 pairs with wide margins on the first pilot.
2. **`d` is a coarse dial, not a free one.** A base admits only the `d` its own ramification supports,
   and each `d` selects exactly one χ, hence one sibling. So per (base, d) you get ONE group — you
   cannot steer toward the sibling you want; you can only enumerate bases and read off where each
   lands. The three tier-`new` targets each had a single reachable `d`, and it pointed at the split-ish
   contested sibling. **Widening the base pool (more fields per top; h > 1, which the item notes is
   legitimate since multiplying the ideal by a square changes neither the norm's square class nor the
   kernel) is the direct way to reach them** — the *directed* version (compute χ for the target group,
   derive the required quadratic subfield of M, then demand that `d`) is the research residual.
3. **`nfeltmul` returns a coordinate vector, not a polynomial.** The first pass reported
   `BUILD-FAIL (degenerate)` on all 16 on-target candidates — a bug in the *poly builder*, not the
   math: `lift(al)` after `nfeltmul` prints `[85,-42,...]~` on the integral basis, and feeding that to
   `subst(·, x, y)` yields a gp error that my `"[" not in out` check misreported as DEGENERATE. Fixed
   with `nfbasistoalg`. **Lesson: a build-stage failure that hits 100% of on-target candidates and 0%
   of anything else is a bug, not a wall** — the density gating was correct throughout.
4. **The `pair` tier is where the score is.** Restricting to groups with zero held rows (the backlog
   item's rule, meant to avoid re-landing the split sibling we already harvest) would have thrown both
   winners away: we hold 19241 and 18461 at other `r`, but their `(t, 24)` pairs are open and worth a
   full sole 1.0 each.

## Reproduce

```
.venv/bin/python scripts/mb2_twist.py --screen --limit 400          # 120 passing bases / 48 tops
for t in 36 38 49 53 67 76 80; do gap -q -b -c "TOP:=$t;" scripts/mb2_twist_prefilter.g; done
.venv/bin/python scripts/mb2_twist_producer.py --limit 400 --bases 12T76,12T49 --pilot 5 --enqueue
```
