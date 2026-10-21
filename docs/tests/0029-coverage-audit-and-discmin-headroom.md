# 0029 — Coverage audit + disc-min headroom (the honest scoring picture)

**Family:** analysis / scoring · **Date:** 2026-06-28 · **Code:** `scripts/analyze_coverage.py`,
`scripts/dashboard/app.py` (metric fix)

## Question

Lever from the status review: now that the verifier is cheap, is **disc-minimisation** on signatures
we already cover the higher marginal lever than more breadth? Measure it. (And audit the headline
metrics, which felt high.)

## Method

`scripts/analyze_coverage.py` over `realized.csv` + `progress.json`: distinct (t,r) signatures vs
per-poly rows, beyond-baseline count, currently-sole count, and — for each scoreable signature with
both our `field_disc` and a leaderboard `minDisc` — the disc fraction `log(minDisc)/log(ourDisc)`
(1.0 ⇒ we hold the global min; <1 ⇒ a team beats our disc).

## Result

**Metric correction (important):** the dashboard's "scoreable" was counting **rows**, not distinct
signatures — and there are ~6 polys per signature, so it overcounted ~6×. The honest picture:

| metric | us | LMFDB baseline |
|---|---|---|
| distinct groups | **312** | 286 |
| distinct scoreable signatures | **255** (of which 244 beyond baseline) | 622 |
| scoreable *rows* (poly DB size) | 1520 | — |
| currently sole signatures (teamCount==0) | **5** | — |

So we're **above baseline on groups but well below on signatures** — our constructions hit many
groups at few real-root counts `r` each, whereas the baseline has ~2.2 sigs/group. And the earlier
"~15 sole realizers" has eroded to **5** as the leaderboard refreshed (other teams caught up).

**Disc-min headroom is real and large:** of 193 scoreable sigs with both numbers, **166 (86%) have a
team beating our disc**; mean disc fraction **0.81** (median 0.81, worst 0.38). So on most covered
sigs we're leaking ~19% of the available disc credit.

## Learnings

- **Distinct (t,r) is the metric that scores; rows are just our poly database.** Dashboard fixed to
  show distinct sigs + a "behind on disc" stat; trajectory recomputed on distinct sigs.
- **The breadth flood is hitting diminishing returns on *distinct* sigs.** 6× row-duplication means
  the quadrinomial sweep is mostly re-covering signatures we already hold. New distinct sigs now come
  slowly from sparse volume.
- **Disc-min is the fresher lever — but it needs small-disc *constructions*, not more sparse flood.**
  Sparse polys (quad/tri) tend to *large* field disc, and `polredabs` only shrinks coefficients, not
  the field disc (the field is fixed). Closing the 166-sig gap means re-realising those groups over
  minimal-disc bases (the `discmin` family), where we have a construction.
- **Net redirection:** continuous *sparse* volume was the right unblock for the dry-queue plateau,
  but it's now low marginal value. The next gains are (a) disc-min on the 166 behind-sigs we can
  construct, and (b) breadth toward *new* sigs via diverse constructions (more `r` per group;
  composita) rather than more sparse polys. Measured, as the lever asked.
