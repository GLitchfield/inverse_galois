# 0028 — Inexhaustible candidate generation + safe S₂₄ filter (juicing the bottleneck)

**Family:** infra / search · **Date:** 2026-06-28 · **Code:** `scripts/search_ctl.py`
(`produce_quadrinomials`, `_quad_stream`), `src/igp/verify.py` (`likely_negligible_s24`,
`_s24_skip`), `scripts/searchd.py` (filter before submit)

## Question

The diagnosed bottleneck (0027 + status review): a *fast pipeline starved by finite producers* —
every producer is a bounded family that the daemon drains in hours, then the queue goes dry. Turn
supply from one-shot batches into a continuous stream, and protect the (shared, free-tier) verifier
budget so a broad flood doesn't drown in generic S₂₄.

## Method

- **Inexhaustible generator** (`produce_quadrinomials`): a deterministic small-coeff-first stream of
  `x²⁴ + a·xⁱ + b·xʲ + c` (genuine quadrinomials), walked by a **kv cursor** so successive runs
  yield NEW irreducible candidates forever. Self-regulating: tops the queue up to a `target` (1200)
  and runs **last** in the tick, so targeted high-yield producers fill first and quadrinomials
  absorb the remaining verifier capacity. `ready` polys (Magma labels).
- **Safe S₂₄ skip** (`verify.likely_negligible_s24`): a Frobenius cycle of prime length ∈ {13,17,19}
  forces a **primitive, non-Mathieu** degree-24 group (those lengths are coprime to every block size
  dividing 24, and don't divide |M₂₄|, |PSL(2,23)|, |PGL(2,23)|) ⇒ A₂₄ or S₂₄ (Jordan). Square
  disc ⇒ A₂₄ (rare, keep); else S₂₄ (negligible) ⇒ daemon marks `filtered`, never submits. Provably
  never discards a valuable group. Applied in the daemon before submit (fail-open: a filter
  exception submits rather than crashing).

## Result

- **Generator works and is inexhaustible:** 0 → 1200 queued in two runs, cursor non-repeating
  (0→2385→2951→4153 across runs, all new).
- **The verifier is NOT the bottleneck.** Feeding it 1200 candidates, the queue's `verified` count
  rose ~668 → ~1868 well within the session — far above the ~330/day we'd inferred while
  *supply-limited*. So supply really was the only ceiling; the verifier has ample headroom.
- **Coverage jump:** scoreable signatures **613 → 1067** (+454, blowing past the LMFDB baseline of
  622 to ~1.7×), groups 294 → 304, sole 14 → 15. The `quad` producer alone: n=1200, 454 scoreable,
  **3 sole realizers** (rare groups from the broad sweep, as expected).
- **Filter is safe + bites hard:** in production the daemon filtered **588 of 800** queued
  quadrinomials (~73%) as S₂₄, submitting only the ~212 valuable ones — most sparse degree-24 polys
  are generic S₂₄, so ~¾ of verifier budget is saved. 0/6 sampled realized groups flagged. Pure
  `_s24_skip` rule unit-tested (13/17/19 ⇒ skip unless square disc; 11/23 never skip). 31 tests green.

## Learnings

- **Supply was the whole bottleneck; flood hard.** The verifier (SAIR Magma) is fast and
  high-capacity — we only ever saw ~330/day because we kept starving it. Continuous top-up keeps it
  busy and coverage climbing.
- **Broad search is mostly S₂₄, so the filter is essential, not optional.** Without it ~60%+ of a
  flood is wasted on negligible-score generic groups (and spams a shared free-tier API). The
  Jordan + Mathieu-order argument gives a *rigorous, zero-false-positive* skip.
- **A kv cursor over a deterministic stream** is the clean way to get inexhaustible + reproducible +
  non-repeating generation — no randomness, full provenance from the target string.
- Next: the same cursor pattern generalises to other inexhaustible families (pentanomials,
  Tschirnhaus perturbations); and the verifier headroom means we can raise the queue target.
