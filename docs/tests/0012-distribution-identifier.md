# 0012 — Distribution-likelihood identifier: separating same-invariant groups (item B)

**Family:** infra / verify · **Date:** 2026-06-26 · **Modules:** `igp/verify.py`
(`identify`), `igp/gap.py` (`cycle_type_distributions`), `scripts/q17_identifier.py`

## Question

`confirm_label` (test 0003/0006) can't separate groups that share parity + subfield
degrees + cycle-type *set* — it false-positived 24T2456 as 24T12727. Can a cheap offline
upgrade separate such collisions (and serve as a pre-Magma confirmer to save API calls)?

## Method

The bug was **set containment** ("observed cycle types ⊆ candidate's set"). 24T2456's
cycle-type set is a *subset* of 24T12727's (2456 has no 8-cycles; 12727 has `4,4,8,8` at
frequency 0.125), so a 2456 polynomial passes 12727's containment test.

Fix — match the cycle-type **distribution**, not the set (`verify.identify`):
- Sample Frobenius cycle types over many good primes (`IDENT_PRIMES` = primes < 2000 ≈ 300);
  by Chebotarev the empirical frequencies approximate the group's class distribution.
- For each candidate `G`, log-likelihood `Σ_ct n(ct)·log(p_G(ct))`, `p_G(ct) =
  (#elements of G with cycle type ct)/|G|` (from `gap.cycle_type_distributions`). An
  observed `ct` impossible in `G` (`p_G=0`) → likelihood `−∞` (**hard exclusion**).
- Return the MLE label + a separation **margin** (gap to runner-up; `∞` if runner-up
  hard-excluded). Statistical, not a proof — Magma stays authoritative.

## Result

Confusion matrix over 5 Magma-confirmed polynomials (~300 primes, ~2 s each):

| true | identified | margin (nats) |
|---|---|---|
| 24T2456 | **24T2456** | 168.5 |
| 24T12727 | **24T12727** | ∞ (2456 hard-excluded) |
| 24T2568 | **24T2568** | 165.3 |
| 24T2595 | **24T2595** | 297.5 |
| 24T14747 | **24T14747** | ∞ |

**5/5 correct.** The decisive case is **24T2456 → 24T2456 (margin 168)**: since 2456's
cycle-type set ⊆ 12727's, *no* hard exclusion is possible — only the distribution
likelihood separates them, and it does so by 168 nats. The reverse (24T12727) hard-excludes
2456 outright (the polynomial produces 8-cycles impossible in 2456).

## Learnings

- **The collision that broke `confirm_label` is resolved.** Distribution-likelihood is the
  right upgrade: it subsumes set containment (impossible type ⇒ −∞) *and* separates
  subset-collisions that containment never could.
- Cheap and fast (~2 s/poly, pure local PARI-free factoring) → a strong **offline
  pre-confirmer**: pre-rank a construction's label before spending a Magma call, cutting API
  load (the real bottleneck, test 0009).
- **Limits:** statistical (rare classes need enough primes; a tiny margin = low confidence),
  and **cannot** separate genuinely cycle-type-equivalent (Gassmann) groups — those need a
  true resolvent (orbit lengths on `k`-subsets). None appeared among the tested collisions.
  Candidate narrowing is still by parity + subfields (`identify` takes an explicit shortlist).
