# 0019 — Signature diversification via totally-real bases (Thread A)

**Family:** construction / signatures · **Date:** 2026-06-26 · **Modules:**
`scripts/q24_signature_diversification.py`, `igp/gp.py`

## Question

We realize each group almost always at `r=0` (complex bases). The scoring is per `(t,r)`, and
112k signatures are undiscovered. Can we hit the *same groups at other `r`* to claim new
signatures?

## Method

Over a **totally real** base `F`, `K = F(√α)` has real-root count `r = 2·#{real places where
α > 0}`. The group is fixed by the valuation pattern (kernel), so the *same* `t` appears at
different `r` as `α`'s real signs change; `α → −α` flips every sign, giving `r ↔ 24−r`.

Base: the degree-12 **totally-real** subfield of `Q(ζ₇₃)` (the order-6 subgroup of `C₇₂`
contains complex conjugation ⇒ its degree-12 fixed field is totally real), `h=1`, split prime
`q=137`. Construct the C_12-top kernel patterns × both signs; read `r` via `polsturm`.

## Result

The C_12-top groups (24T14744, 24T12727, 24T2456, 24T5338, 24T7819, …) — previously realized
only at `r=0` over `Q(ζ₁₃)` — are realized over the real base at **r ∈ {8, 12, 16}**, with the
sign flip confirming `r ↔ 24−r` (16↔8; 12 self-conjugate). **Magma-confirmed: 9 distinct
`(t,r)`, all scoreable** (e.g. 24T14744 r=8/16, 24T12727 r=8/16, 24T2456 r=8/16, 24T5338 r=12,
24T7819 r=8/16).

**But** the leaderboard shows these `(t, r>0)` are still **contested** (teams 3–13) — the
C_12-top family is popular at *every* signature, not just `r=0`. So diversification on popular
groups doesn't yield sole realizers.

## Learnings

- **Signature diversification works and is cheap** — a totally-real base + sign choice gives a
  spread of `r` for the same group (here {8,12,16}; finer sign control via units would fill
  the rest of `0..24`). Reusable (`q24`).
- **Aim it at HARD groups, not popular ones.** The undiscovered analysis (test 0018) shows the
  prize is **10,426 fully-undiscovered solvable groups** (median order 24576) and the 2,228
  undiscovered non-solvable signatures — diversifying *those* (real non-solvable / big-top
  bases) is where sole realizers (1.0) live. The C_12 family is saturated at all `r`.
- Next: real **non-solvable** bases (real A₅/S₅ quintics → totally real resolvent base) to
  hit non-solvable groups at `r>0`, and large-kernel constructions over degree-6 tops to reach
  the order-≈24576 untouched solvable groups.
