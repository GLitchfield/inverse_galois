# Test 0077 — 24T18007, the second sibling of the 12T36 base: the odd-`f` prime is a CHOICE

**Family:** MINBLK=2 / `general_c2_TWIST`, sign-character shortlist
**Date:** 2026-07-14
**Backlog item:** "24T18007 at r=24 — the SECOND sibling of the SAIR-validated 12T36 base" (research
dive #61)
**Producer:** `scripts/mb2_twist_sign_producer.py` (SHORTLIST entry + `CHOOSEID`)

## Question

Test 0076 built and SAIR-labeled `(24T18009, r=24)` on the sextic-derived 12T36 base. That base has
three index-2 characters; χ2 aims at **24T18007**, a group whose r=24 pair is `teamCount = 0` and
non-baseline. Does the same engine, same base, reach it at `d = 19405`?

## Setup

Target `(24T18007, r=24)` re-verified against `data/processed/progress.json` (refreshed 2026-07-14
04:47): `teamCount = 0`, `minDisc = None`, `is_baseline = False` ⇒ a genuinely open sole-1.0 that
scores on any valid disc.

**Correction to the item's premise (step-3 re-verify).** The item claimed 24T18007 has **zero rows**
in `realized.csv`. It does not: we hold **48 officially-labeled `24T18007` rows, all at `r = 2`**
(a contested pair, tc=7). The *group* is held; the *pair* `(18007, 24)` is not. So the enqueue tier
is **`pair`** (@115), not `new` (@130). The producer computes the tier from `realized.csv` itself, so
it got this right regardless of the item's text.

`d` was **re-derived, not assumed** — the gate that saved test 0076. `mb2_chi_d_base.py` on this base
reproduces dive #61 exactly:

| χ | 24Tt | d_N | #eqs | #surv | reachable |
|---|---|---|---|---|---|
| 1 | 18009 | 5 | 438 | 1 | yes |
| 2 | **18007** | **19405** | 438 | 1 | yes |
| 3 | 18008 | 3881 (= core(disc K₀), the SIGN character) | 547 | 1 | yes |

## Result: BUILT — but only after fixing a real producer bug

**The first run produced ZERO candidates**, and the reason was structural, not a sampling gap.
Instrumenting the divisor arithmetic directly (rather than trusting "no candidate" as a verdict):

- `Cl(K₀) = Z/3`.
- `Id = P₅ · P₃₈₈₁` as the producer chose it has class **[2] ≠ 0**.
- **Every prime above every completely-split `q` is principal** (checked at 6 split primes, all 12
  primes each, all class [0]).

So `[Id · P_a · P_b] = [Id] ≠ 0` for **every `q` and every `(a,b)`** — no principal even-weight
divisor exists at *any* parameter. That is dive #52's `[Id] ≠ 0` law, and no amount of `--nq` /
`--abmax` widening can touch it.

**The bug: the producer picked the odd-`f` prime by INDEX (`od[1]`), not by CLASS.** `p | d` can have
several primes of odd residue degree, and they sit in **different ideal classes**. Every one of them
gives `v_p(N(Id))` odd ⇒ `core(N) = d` holds for all of them — but only some make `[Id]` trivial.
Above 3881 this base has five odd-`f` primes:

| P | f | e | class |
|---|---|---|---|
| P1 | 1 | 2 | [2] ← `od[1]`, what the producer took |
| P2 | 1 | 2 | [1] |
| P3 | 1 | 1 | [2] |
| P4 | 1 | 1 | [1] |
| **P5** | **3** | 2 | **[0]** |

`P5` has odd `f` **and** trivial class. Both primes above 5 are already principal. Picking `(P₅^{(5)},
P5^{(3881)})` makes `Id` principal while keeping both `v_p(N(Id))` odd ⇒ `core(N(Id)) = 5 · 3881 =
19405` still holds.

This is dive #52's **"option (i): re-choose the odd-`f` prime"** — which was *impossible* on 12T245
(a unique odd-`f` prime above 5, which is why test 0072 had to invent the even-`f` repair) and is
very much *possible* here. Shipped as `CHOOSEID` in `BUILD_SIGN`: search the product of the per-`p`
odd-`f` lists for a trivial-class `Id`; fall back to `od[1]` only when none is principal (on a base
whose split primes are *not* all principal, the `(a,b)` sweep can still cancel `[Id]`, so the old
behaviour stays available). **h=1 bases are unaffected** (everything is principal), and 18009's `d=5`
already had both primes above 5 in class [0] ⇒ **no regression on the SAIR-labeled test-0076 build.**

**With the fix, the target builds on the FIRST split prime (`q = 619`), 2 for 2:**

| cand | lands | kdim | L1 | margin | rivals killed |
|---|---|---|---|---|---|
| `q619_1_2` | **24T18007** | 11 | 0.050 | 0.727 | 41 of 43 |
| `q619_1_4` | **24T18007** | 11 | 0.049 | 0.728 | 41 of 43 |

Both: degree 24, irreducible, `polsturm = 24`, **`nfisisom`-DISTINCT** (two independent shots at the
label, not a duplicate), field disc `8.890e69` over **{2, 5, 619, 3881}** — every prime four orders of
magnitude under the grader's 10⁶ `nfdisc` bound ⇒ **no blank-risk** (the item's disc-growth worry from
`d = 19405` ramifying more than `d = 5` did not materialise: the disc *value* grew, the prime *set*
did not).

Enqueued `lit:mb2twsignpair:18007.24:base12T36:d19405:q619_1{2,4}` @115, both verified in the queue as
well-formed 25-int ascending lists.

## The label landed IN-RUN, and it matches

Both candidates came back from SAIR's Magma **officially labeled `24T18007`, r = 24** — the aimed
sibling, first try ⇒ χ2's `d = 19405` is **SAIR-validated** and this build is `PILOT-LABELED`. The
`(18007, 24)` pair goes from `teamCount = 0` (nobody credited) to ours, and it is the **first
`(18007, 24)` row anywhere in `realized.csv`** (our other 48 `24T18007` rows are all the contested
`r = 2`).

Both rows show `scoreable = False` with a blank `field_disc` on the fresh poll. That is
**`discriminant_pending`** (the disc is scored asynchronously after Magma returns the label), **not a
rejection** — the same correction test 0072 had to make about `(24492, 24)`. `gp.scoreable_disc`
returns `8.890e69` locally in ~0 s and every prime of the disc is under 10⁶, so there is no
factorization timeout for the grader to hit.

Two independent (non-isomorphic) fields at the same disc means two shots at the same pair; the
smaller-disc hunt is a separate, later concern (the pair is open, so any valid disc already scores).

## Learnings

1. **"No candidate radical" is a hypothesis, not a verdict.** The producer's own failure message
   blamed the `q < 10⁶` window ("no principal even-weight divisor under q < 1000000"), which reads as
   *search harder*. The truth was that the search space was empty by construction, and one
   `bnfisprincipal` on `Id` would have said so. A negative result from a producer deserves the same
   instrumentation as a positive one.
2. **The odd-`f` prime above `p | d` is a free parameter the engine was silently spending.** Any odd-`f`
   choice satisfies the `core(N) = d` requirement — that is the only constraint the recipe ever stated
   — so the class was never considered, and `od[1]` was as good as a coin flip. On an `h > 1` base
   that coin flip decides whether the target is buildable **at all**.
3. **The even-`f` repair (test 0072) is the SECOND-choice tool.** It buys the class at the cost of
   inflating the kernel (test 0075). Re-choosing the odd-`f` prime buys the same class for **free** —
   no new prime enters the disc, no kernel perturbation. Try option (i) before option (ii); 12T245 was
   the unlucky base where option (i) didn't exist, and that made the expensive tool look like the
   default.

## Reproduce

```
gap -q -b -c 'TOPS:=[36];;' scripts/mb2_chi_table.g > /tmp/chitab36.txt
.venv/bin/python scripts/mb2_chi_d_base.py --top 36 --chitab /tmp/chitab36.txt \
    --coeffs '[6264469, 1670201, -3640611, -770897, 773737, 117664, -78270, -8027, 4036, 253, -102, -3, 1]'
.venv/bin/python scripts/mb2_twist_sign_producer.py --targets 18007 --ncand 4 --nq 12 \
    --per-target 2 --pilot 2 --enqueue
```
