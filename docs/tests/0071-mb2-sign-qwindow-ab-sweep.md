# Test 0071 — sign-character twist: the wide `q`-window + 66-pair `(a,b)` sweep (family: MINBLK=2)

**Question.** Dive #52 declared six sign-character targets DEAD on a narrow-class argument; dive #53
refuted that for the *non-rational* bases and claimed the three survivors (21593 / 24157 / 24334) were
merely **under-searched** — a `q`-window and an `(a,b)`-window artifact, not an obstruction. Build them.

**Setup.** `scripts/mb2_twist_sign_producer.py` (test 0069/0070 engine), two parameter changes:
the hardcoded `(a,b)` loop `a<=4, b<=5` (10 of the 66 prime pairs above a split `q`) becomes
`--abmax` (default 12 ⇒ all 66); `--qmax` exercised at 300000. Everything else identical — same
`d = core(disc K0)` sign aim, same witness-exclusion fingerprint gate at `FPMAX` (kernel dim == 11,
witness cycle types, ~5,000 primes).

Command:
```
.venv/bin/python scripts/mb2_twist_sign_producer.py \
    --targets 21593,24157,24334,24492 --abmax 12 --ncand 3 --nq 2 --qmax 300000 \
    --per-target 1 --pilot 5 --enqueue
```

**Step-3 re-verify.** All four targets `teamCount == 0`, non-baseline, **zero rows** in `realized.csv`
at `r=24` against `data/processed/progress.json` (07:41, 1.7 h old).

## The gate that was actually blocking: it had already cleared

The backlog carried this family as "SAIR labels pending — nothing in it is validated". That is **stale**.
Every candidate tests 0069 and 0070 enqueued has since returned an **official Magma label, and every
one matches the target it aimed at — 7 rows / 6 distinct groups, 6-for-6:**

| target | base | d | q | official label |
|---|---|---|---|---|
| 24T23664 | 12T253 | 3 | 52009 | `24T23664` |
| 24T21904 | 12T192 | 37 | 31153 | `24T21904` |
| 24T21572 | 12T167 | 89 | 2371 | `24T21572` |
| 24T21376 | 12T156 | 101 | 3061 | `24T21376` |
| 24T22401 | 12T207 | 1129 | 18457 | `24T22401` |
| 24T21582 | 12T170 | 5 | 4079 | `24T21582` (×2) |

The label column is SAIR's independent answer, not a copy of our aim — across `realized.csv`, 2,746 rows
carry a label that *disagrees* with the target in their provenance tag. So the **sign map
`d = core(disc K0)` ⇒ the sibling `G_chi_sgn` is SAIR-VALIDATED**, and the family moves from
`LOCAL-GATED` to `PILOT-LABELED`. This also clears the label gate on the backlog's separate scale-up item.

## Result — 3 of 4 built, gated, enqueued

| target | base | d | split q | (a,b) | kernel dim | L1 | margin | rivals witness-killed | field disc |
|---|---|---|---|---|---|---|---|---|---|
| **24T21593** | 12T175 | 19567 | 5273 | (1,2) | 11 | **0.053** | 0.825 | 10 of 11 | 2.06e59 |
| **24T24334** | 12T281 | 5077 | 52103 | (1,3) | 11 | **0.109** | 0.740 | 16 of 17 | 1.53e68 |
| **24T24157** | 12T274 | 97296769 | 51749 | (1,2) | 11 | **0.118** | 0.444 | 96 of 97 | 6.01e57 |

All three: degree 24, irreducible, `polsturm == 24`, `gp.scoreable_disc` non-blank. Enqueued
`lit:mb2twsignnew:<t>.24:base12T<top>:d<d>:q<q>_<a><b>` @130, tier **new** (zero rows held for any of
the three groups). The daemon picked all three up within the run.

**24T24492 — BLOCKED, and not for the reason the item guessed.** The item flagged its `h = 2` principality
guard as the risk. The actual wall is upstream of that: **12T288 has no completely-split prime below
300,000 at all** (`polrootsmod(f, q) == 12` never fires). A completely-split prime has density `1/|H|`,
and this top is large enough that the expected count in the window is fractional. The `q` ceiling is set
by scoreability (`q` divides the degree-24 disc, so `q < 10^6`), which leaves only ~3x more window to
search — worth one attempt, but the odds are set by `1/|H|`, not by anything we can dial.

## Two honest corrections to the item's own premise

1. **The 66-pair `(a,b)` widening did not bind.** The winning pairs are (1,2), (1,3), (1,2) — all three
   sit *inside* the old `a<=4, b<=5` window. The widening is still correct to keep (it costs nothing and
   the narrow classes of the 12 primes above `q` genuinely differ on a non-rational base), but it is not
   what unlocked these targets.
2. **The `q`-window widening bound for two of the three, but the shipped default already had it.** 24157
   (q=51749) and 24334 (q=52103) both need a `q` far above dive #50's original `q < 6000` window — but
   `--qmax` had already been raised to `10^6` by test 0069. What was actually holding these three back was
   neither window: it was the **PILOT cap** (tests 0069/0070 deliberately stopped at 5 enqueued, pending a
   label) plus dive #52's **incorrect DEAD verdict on 24334**.

So the real finding is #3: **dive #52's narrow-class DEAD list is refuted at the build, not just on
paper.** 24T24334 was listed "DEAD — no `q` and no `(a,b)` can rescue `[Id] != 0`". It built on the first
split prime, at pair (1,3), with a totally-positive alpha of `core(N(alpha)) = 5077`, and the fingerprint
lands 24T24334 at kernel dim 11 with 16 of 17 rivals witness-killed. Dive #53's diagnosis was right: the
"no `q` can rescue it" law holds only when the narrow character is a **rational** genus character, which
12T281 is not.

## Ladder status

`PILOT-LABELED` for the family (6/6 official label matches on the prior batch); these three specific
candidates are `LOCAL-GATED` and awaiting their own SAIR labels. Three tc=0 non-baseline `(t, 24)` pairs
are in flight, each a sole-1.0 if the label matches.

Reproducer: the command above; `scripts/mb2_twist_sign_producer.py`; census `scripts/mb2_genus_census.gp`.
Recipe: `docs/auto_log.md` 2026-07-13 dive #53.
