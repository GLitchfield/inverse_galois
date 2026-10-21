# 0030 — Cranked raw breadth + minimal-radical disc-min

**Family:** infra / search · **Date:** 2026-06-28 · **Code:** `scripts/search_ctl.py`
(`produce_pentanomials`, `produce_discmin2`), kv knobs

## Question

Acting on 0029 (disc-min has headroom; the verifier has ample headroom): (a) crank raw candidate
breadth now that supply, not the verifier, is the ceiling; (b) attack the behind-on-disc signatures
with a construction that actually lowers field discriminant.

## Method

**Breadth crank.**
- `produce_pentanomials`: a second inexhaustible cursor family, `x²⁴ + a·xⁱ + b·xʲ + c·xᵏ + d`
  (denser than quadrinomials ⇒ more distinct groups; ~75% irreducible). Runs each tick alongside the
  quad buffer.
- Buffer/throughput kv knobs: `quad_target` 2500→**8000**, `quad_max_add`→4000, `max_pending`
  150→**300** (more in flight against the fast verifier).

**Minimal-radical disc-min** (`produce_discmin2`). 0029 showed even our split-prime-radical `discmin`
family is beaten on disc. A C₂ kernel `F(√α)` for small squarefree α (−1, ±2, ±3, …) ramifies far
less than a split-prime radical ⇒ smaller field disc. So: `gp.quadratic_ext(base, α)` over the LMFDB
minimal-disc degree-12 bases (12T1–4), `ready` polys; the engine keeps the min disc per (t,r).

## Result

- **Breadth flows continuously:** queue cranked to ~8000 and stays full between ticks; the daemon
  drains at verifier rate with the S₂₄ filter dropping the junk (2500+ filtered, 2800+ verified).
  Bandit correctly ranks `quad` last (low scoreable-rate-per-sample) so targeted producers build
  first. posts/day rose to ~96.
- **discmin2 generates small-disc kernels:** 68 candidates at **~32-digit discs** vs the ~38–43-digit
  discs we were behind with — structurally smaller, as intended.
- **Coverage (live):** 312→**319 distinct groups**, 255→**263 distinct scoreable sigs** (258 beyond
  the 622 baseline), 5 sole sigs. Still draining (queue ~7–8k), so this undercounts the steady state.
- **Disc-min impact is still landing:** behind-on-disc is **173/202** — not yet down, because the
  discmin2 candidates are still in the queue/verifying and the comparison set grows as more sigs gain
  a leaderboard min. To re-measure after the queue drains: `scripts/analyze_coverage.py`.

## Learnings

- **Cranking breadth is cheap and safe given the filter + bandit:** extra volume that's mostly S₂₄ is
  dropped pre-submit, and the bandit deprioritises the low-yield filler — so raw breadth can't drown
  the high-value producers. But (per 0029) its marginal *distinct-sig* yield is modest; it's a
  steady trickle of new sigs + a wide net, not the main score lever.
- **Minimal-ramification radicals are the right disc-min primitive** for C₂ kernels — small α beats
  split primes on field disc by construction. The open disc-min frontier is the *worst* gaps
  (non-solvable S₅-base, fraction ~0.37), which need genuinely smaller-disc constructions, not
  parameter tweaks — deferred.
- Net: breadth and disc-min both now run continuously in the tick; `analyze_coverage.py` is the
  honest scoreboard to watch (distinct sigs + behind-on-disc), not the per-poly row counts.
