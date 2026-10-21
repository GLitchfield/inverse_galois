# 0073 — The `(a,b)` ORBITAL pre-filter: predict the kernel before you build it

**Family:** MINBLK=2 / twist engines · **Date:** 2026-07-13 · **Ladder:** engine optimization,
regression-tested against test 0072's SAIR-labeled ground truth · **Enqueued: 0 (by design — this
item adds no targets)**

## Question

The weight-2 twist producers (`mb2_twist_sign_producer.py`, `mb2_twist_evenf.py`) build `α` on the
divisor `Id · Q_a · Q_b`, where `Q_a, Q_b` are two of the 12 primes above a completely-split `q`. The
choice of `(a,b)` **moves the block kernel** — tests 0069 and 0072 both watched a pair land the dim-10
sibling instead of the aimed dim-11 one, and paid a full build plus a 5,133-prime fingerprint to find
out. Test 0072 built 3 radicals to gate 2. **Can we predict the landing kernel from `(a,b)` alone?**

Research dive #54 (2026-07-13) says yes, in closed form. This test implements it and regression-tests
it against the one configuration where we have an *authoritative* answer.

## Recipe (dive #54)

Valuation-at-`q` is `H`-equivariant, so the conjugates of `α` carry the vectors `σ(1_{a,b})`:

> `kdim ≥ dim ⟨H·1_{a,b}⟩`, and that span depends ONLY on the `H`-**orbital** of the pair `{a,b}`.

`⟨H·1_{a,b}⟩` is the GF(2) column space of the incidence matrix of the orbital graph `Γ_{a,b}`, whose
rank on `n` vertices with `c` components is `n − c`. Hence

> **`dim ⟨H·1_{a,b}⟩ = 12 − #components(Γ_{a,b})`** — a graph count, no group theory in the hot path.

Computed in **PARI alone** (`scripts/mb2_orbital.py`, `GP_ORBITAL`): one `nffactor` of `f` over `K₀`
per `(base, q)`, then O(1) per pair. Factor index of `f = (x−θ)·∏gₖ` is a base-independent suborbit
label; `dec[i]` is matched to its root `c_i` of `f mod q` by `idealval(K, θ−c, dec[i]) > 0` (**not**
`nfmodpr` — it returns a `t_FFELT` that poisons `polrootsmod`). Because `idealprimedec`'s ordering is
an implementation detail, `ORBDIM` returns its own root vector and callers map their `dec` indices
through `ORBPERM` — the pair label is the **root mod q**, which is intrinsic.

## Result 1 — self-test reproduces dive #54's table exactly (0.07 s)

`mb2_orbital.py --selftest`, base **12T245**, `q = 15569` (test 0072's exact config):

| | value | ground truth |
|---|---|---|
| suborbit degrees | `[1, 2, 3, 3, 3]` | dive #54 ✓ |
| pairing involution | `[1, 2, 5, 4, 3]` (f3 ↔ f5; f2, f4 self-paired) | dive #54 ✓ |
| orbital dims available | **8, 10, 11** | independent GAP census: 8, 10, 11 ✓ |
| `(1,2)` | **10** | test 0072 landed 24T22599, off-target ✓ |
| `(1,3)` | **11** | test 0072 landed **24T23297** (SAIR-labeled) ✓ |
| `(1,4)` | **11** | test 0072 landed **24T23297** (SAIR-labeled) ✓ |

**3/3, zero fitting.** 36 of the 66 pairs are dim-11 on this base.

## Result 2 — the A/B, on the same base, same `d`, same construction; only the filter changed

`mb2_twist_evenf.py --targets 23297 --ncand 4 --per-target 4 --allow-shared`, with and without
`--no-orbital-filter`. Both arms find the same 4 totally-positive `α` budget on the `P_3` repair arm.

| arm | radicals built | on-target (24T23297, kdim 11) | off-target |
|---|---|---|---|
| **filter ON** | 4 | **4** (L1 0.057–0.067, margin 0.84–0.86) | **0** |
| filter OFF (old behaviour) | 4 | 2 | **2** — `(1,2)` and `(1,5)` → 24T22599, kdim 10 |

The on-target rate goes **2/4 → 4/4**; the wasted builds are exactly the pairs the filter predicts as
non-dim-11. The two gated winners reproduce test 0072's SAIR-labeled polynomial (disc **2.3664e68**),
and the filter *additionally* surfaced two fresh dim-11 radicals `(1,7)`, `(1,8)` — more shots per
base, not just fewer wasted ones.

## Correction to dive #54 — the bound is a LOWER bound, and it is sometimes STRICT

Dive #54 reported the criterion as "exact on 3/3". This test adds a fourth data point that is
**strict**: pair `(1,5)`, predicted dim **8**, landed a group of kernel dim **10**. That is expected —
the bound accounts only for the `q`-part of the divisor, while the other primes of `Id` (the odd-`f`
primes over `d`, plus the even-`f` repair prime) contribute further valuation vectors that can inflate
the kernel. Every **predicted-11** pair still landed exactly 11 (**6/6** across tests 0072 + 0073).

Consequence, recorded in the module: the filter is a **build-tax screen, not a proof**. It can in
principle skip a pair that would have inflated *into* the target dim (a false negative), and it does
not certify an accepted pair — **the Frobenius-density gate downstream stays load-bearing.**

## Shipped

- `scripts/mb2_orbital.py` — `GP_ORBITAL` (SUBORB / NCOMPS / ORBDIM / ORBPERM), `orbital_dims()`,
  `good_pairs()`, `--selftest`, and the **reachability guard** `WEIGHT2_UNREACHABLE = {14616, 9641,
  9642}` (dive #54: their dim-6 kernels are *not* the dim-6 orbital module of their top ⇒ no weight-2
  split radical reaches them, at any `(a,b)`, prime or unit twist; **24T20699 is reachable**). Both
  producers now hard-skip those three targets.
- `scripts/mb2_twist_sign_producer.py`, `scripts/mb2_twist_evenf.py` — filter on by default (aiming
  `TKDIM = 11`), `--no-orbital-filter` restores the blind sweep; each `q` reports how many of its 66
  pairs survive.

## Why 0 enqueued

The item adds no targets, and its regression base `(24T23297, r=24)` is already held with the same
disc (2.3664e68) under an official `24T23297` label — re-enqueueing identical models would burn
submission budget for nothing. The payoff is downstream: the **next Ready item** (the 7 fully-open
orbital classes, 14 tc=0 sole-1.0s at r=24) needs exactly this filter, parameterized by target kdim
(`3 components` for the 12T63 class at kdim 9, `2 components` for the six kdim-10 classes).

## Reproduce

```
.venv/bin/python scripts/mb2_orbital.py --selftest
.venv/bin/python scripts/mb2_twist_evenf.py --targets 23297 --ncand 4 --per-target 4 --allow-shared
.venv/bin/python scripts/mb2_twist_evenf.py --targets 23297 --ncand 4 --per-target 4 --allow-shared \
    --no-orbital-filter
```
