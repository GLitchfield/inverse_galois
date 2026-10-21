# Test 0076 — 24T18009 on the sextic-derived 12T36 base: the wall breaks, but the AIM was wrong

**Family:** MINBLK=2 / `general_c2_TWIST` (sign-character engine)
**Date:** 2026-07-14
**Backlog item:** "[MINBLK=2] 24T18009 (5 tc=0 sole-1.0s) on a NEW δ=0 12T36 base — the dive-#58 wall is BROKEN"
**Recipe pointer:** `docs/auto_log.md` dive #59 (the base factory) + dive #50 (the sign-character aim);
producer `scripts/mb2_twist_sign_producer.py`, new d-finder `scripts/mb2_chi_d_base.py`.

## Question

Dive #58 proved 24T18009 unbuildable on *every* 12T36 base we had — but LMFDB holds only **2**
totally-real 12T36 fields in total, and both are the dead ones (the wall was the data source, not the
mathematics). Dive #59 built a fresh 12T36 base from a 6T13 sextic and claimed it lands in the free
case. Does the twist engine now reach **24T18009**, and at what `d`?

## Targets

`24T18009` at `r ∈ {8, 12, 16, 20, 24}` — re-verified against `data/processed/progress.json`
(refreshed 2026-07-14 02:42, ~5 h old): **all five `teamCount = 0`, `minDisc = None`, non-baseline**
(`igp.baseline.is_baseline` False), and **zero rows held** in `realized.csv`. Five sole-1.0 pairs.
The engine builds a totally-positive α, so it aims at **r = 24**.

## The base (independently re-verified, not taken on faith)

Ascending coeffs
`[6264469, 1670201, -3640611, -770897, 773737, 117664, -78270, -8027, 4036, 253, -102, -3, 1]`.

| check | value |
|---|---|
| degree / irreducible / `polsturm` | 12 / yes / **12** (totally real) |
| `nfsplitting` degree | **72** |
| `#nfsubfields` | **5** (the 12T36 subfield-degree fingerprint) |
| field disc | 13757459396482553140625, `core` = **3881** |
| `h`, `Cl` | 3, `[3]` |
| `h⁺`, `Cl⁺`, δ | 3, `[3]`, **δ = 0 ⇒ OK-NARROW** (the sign gate is vacuous) |

`scripts/mb2_narrow_screen.py --targets 18009` returns **OK-NARROW** on this base and reproduces
**DEAD-NARROW** (δ = 1, `nmixed = 0`) on the old LMFDB base — dive #58's wall confirmed, and broken.

## The headline: the item's aim was WRONG, and the mandatory gate caught it

The backlog item said to build with **`d = core(disc K₀) = 3881`**, reasoning that dive #50's rule
makes the aimed sibling a function of the top alone, "which is still 12T36 ⇒ it should still aim at
18009 — but verify, don't assume." **Verifying refuted it.**

`scripts/mb2_twist_sign.g` on 12T36 prints `SGN|36|18008`: the **sign character aims at 24T18008**,
the *contested* sibling — not 18009. 12T36 has **three** index-2 subgroups (`mb2_chi_table.g`):

| χ | sibling | d on this base |
|---|---|---|
| 1 | **24T18009** | **5** |
| 2 | 24T18007 | 19405 |
| 3 | 24T18008 (= sign) | 3881 = core(disc K₀) |

24T18009 is the sibling of a *different* character, so its `d` is not the free one and had to be
solved for. LMFDB has no such base, so dive #51's d-finder (`mb2_chi_d.py`, LMFDB-only input) could
not be pointed at it — hence the new **`scripts/mb2_chi_d_base.py`**, the same Frobenius/homomorphism
method taking an arbitrary `(top, base)` on the command line. It pins **d = 5** for χ₁ from **438
decisive Frobenius equations with a unique surviving candidate**, and the homomorphism law
cross-checks it: `d₁ · d₃ = 5 · 3881 = 19405 = d₂`, no contradictions. Both 5 and 3881 have an odd-`f`
prime in K₀ ⇒ reachable.

**Had the item been built as written, it would have produced 24T18008 — a contested group, ~0 score.**

## Build

`scripts/mb2_twist_sign_producer.py --targets 18009 --ncand 4 --nq 12 --per-target 2 --pilot 2
--enqueue`, with the base added to `SHORTLIST` as `(18009, 36, 5, <coeffs>, 3)`. No engine change.

12 completely-split primes found (619 … 11959); the dive-#54 orbital pre-filter kept 36 of 66 `(a,b)`
pairs at kdim 11 on the first prime, `q = 619`. `h = 3` makes principality a real constraint, but the
producer's `bnfisprincipal` guard handles it and the very first prime yielded gated radicals.

| candidate | lands | kdim | L1 | margin | rivals witness-killed |
|---|---|---|---|---|---|
| `q619_1_2` | **24T18009** | 11 | 0.052 | 0.778 | 41 of 43 |
| `q619_1_4` | **24T18009** | 11 | 0.045 | 0.779 | 41 of 43 |

Both **on-target**, decisively (the nearest rival, 24T9761, sits at L1 0.510).

## Local gate — both pass

Degree 24, irreducible, **`polsturm` = 24** (= target r), `nfisisom` = 0 ⇒ **two distinct fields**
(two independent shots at the label, not a duplicate). Field disc
`1.5209e59`, factoring as **{2, 5, 619, 3881}** — every prime is four orders of magnitude below the
grader's 10⁶ `nfdisc` bound, so **no blank-risk**.

## Result — SAIR-LABELED WITHIN THE RUN, both on target

**2 candidates / 1 tc=0 pair enqueued** — `(24T18009, r = 24)`, tier **new** (@130), tags
`lit:mb2twsignnew:18009.24:base12T36:d5:q619_1{2,4}`. The daemon submitted both within the run and
**both came back from SAIR's Magma as `24T18009`, r = 24, `scoreable = True`**, each carrying our own
`field_disc = 1.5209e59`. The aim is therefore **`PILOT-LABELED`, not merely locally gated**: a sole
1.0 on a pair we held zero rows for, and the first 24T18009 anywhere in `realized.csv`.

That label is also the authoritative confirmation that **d = 5 was the right character and d = 3881
would have been the wrong one** — the density fingerprint's kdim-11 / 18009 verdict is now backed by
the official gate, on a base that dive #58 had written off entirely.


## Learnings

1. **"The aim is a function of the top alone" is true but was applied to the wrong character.** The
   sign character's `d = core(disc K₀)` is *free*, which is exactly why it is seductive — and on 12T36
   it aims at the contested sibling. The free `d` and the *wanted* `d` are different questions. Gate #2
   of the item ("recompute, don't assume") is the only reason this build is on-target.
2. **The dive-#58 wall really was a database artifact.** A base outside LMFDB, built by dive #59's
   sextic factory, lands δ = 0 and gates on its *first* split prime. LMFDB's degree-12 table is a
   Klüners–Malle sample; "not in LMFDB" is not "does not exist."
3. **`h > 1` is not a blocker for this engine** — h = 3 here, and the principality guard simply skips
   the non-principal divisors. The narrow rank δ, not `h`, is what kills a base.
4. **The d-finder needed to accept a non-LMFDB base.** `mb2_chi_d_base.py` closes that gap and is the
   reusable half of dive #59's base factory: any new sextic-derived base can now be aimed.

## Reproduce

```
gap -q -b -c 'JS:=[36];;'   scripts/mb2_twist_sign.g          # -> SGN|36|18008  (the sign sibling)
gap -q -b -c 'TOPS:=[36];;' scripts/mb2_chi_table.g > /tmp/chitab36.txt
.venv/bin/python scripts/mb2_chi_d_base.py --top 36 --chitab /tmp/chitab36.txt \
    --coeffs '[6264469, 1670201, -3640611, -770897, 773737, 117664, -78270, -8027, 4036, 253, -102, -3, 1]'
.venv/bin/python scripts/mb2_narrow_screen.py --targets 18009
.venv/bin/python scripts/mb2_twist_sign_producer.py --targets 18009 --ncand 4 --nq 12 \
    --per-target 2 --pilot 2 --enqueue
```
