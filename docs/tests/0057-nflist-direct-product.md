# 0057 — nflist direct-product compositum producer (family: nflist / compositum)

**Question.** Can PARI's `nflist` serve as a signature-controlled base-field factory (task #18) to
feed a *new* deg-24 family the tower producers can't reach — direct products G4 × G6 (task #14) —
with good (small, smooth) discs?

## Setup / recipe

`nflist(G, [lo,hi], s)` returns number fields with Galois-closure group `G`, |disc| in `[lo,hi]`,
`s` complex places — a fast (ms) built-in factory. The compositum of a `nflist` deg-4 field and a
**coprime-disc** deg-6 field is a deg-24 field of the **product-action group** G4 × G6 (linearly
disjoint ⇒ single deg-24 factor of `polcompositum`). The 24Tt is fixed per (G4, G6) pair.

- Group map (verified by structure in GAP, not `polgalois` — PARI's numbering differs):
  C4=4T1, V4=4T2, A4=4T4, C6=6T1, D6=6T3.
- Product-action 24Tt (GAP `TransitiveIdentification` of the direct product on the 24 = 4×6 points):
  C4×C6→24T2, V4×C6→24T3, A4×C6→24T71, C4×D6→24T27, V4×D6→24T30, A4×D6→24T250.
- Producer `produce_nflist` (`scripts/search_ctl.py`) + gp helpers `nflist_fields`, `compositum24`
  (`src/igp/gp.py`). Local gate: deg==24 ∧ irreducible ∧ nfdisc smooth (<10⁶, no grader blank) ∧
  `r=polsturm`; then open-gate on `progress.json` — tier `new` (teamCount==0) or `alt` (held by
  others → tiny disc wins disc-min). Cursored per recipe by disc window (`nflist_<G4><G6>_off`).

## Result

- **Mechanic validated:** A4×D6 compositum → deg-24 irreducible, **nfdisc = 2·37** (largest prime
  37 — tiny, perfectly smooth, always scoreable, strong score ratio). Confirmed across all 6 recipes.
- **Open value:** 24T2 (C4×C6) and 24T3 (V4×C6) are **OPEN (teamCount==0) at r∈{0,24}** and unheld
  by us → 4 clean open-1.0 targets. The producer enqueued `nflist:C4C6new:2.0` and `2.24` (both
  signatures — the totally-real vs totally-complex factor choice sets r=24 vs r=0).
- **Defense value:** 24T27/30/71/250 are contested (teamCount 15–46); enqueued as `alt` — the tiny
  smooth discs win disc-min on pairs held-but-undercut.
- One `produce_nflist` run enqueued 36 candidates across the 6 families; wired into `TICK_PRODUCERS`
  (runs every feed/tick, atlas/open-gated). SAIR is the authoritative label downstream.
- **SAIR round-trip confirmed the labels:** 24T2 → 24T2 (6/6), 24T3 → 24T3 (6/6). A4×C6 predicted
  24T71 but labeled **24T9** — A4 and C6 both contain C3, so non-coprime factors share that cubic
  subfield and the compositum collapses to the *fiber* product (order 24), not the direct product
  (order 72). **Fix:** `nflist_fields` now returns each field's disc and `produce_nflist` enforces
  `gcd(disc4, disc6)==1` (linear disjointness ⇒ the full product group). The open-pair recipes
  (C4×C6, V4×C6) never collide (no shared C3) — they were already correct.

## Learnings

- `nflist` is a genuine fresh-runway source with **disc + signature + group control** = good polys by
  construction, unlike the large-disc tower feed. Its abundant supply is small degree (deg-3/4), which
  the compositum split turns into deg-24.
- **Correctness trap caught in validation:** PARI `polgalois` group numbering ≠ GAP `TransitiveGroup`
  numbering (it returned C4=V4=A4=4T1); always fix the transitive ID by *structure* in GAP.
- deg-4×deg-6 with nflist-supported groups yields only 6 base groups (small, mostly contested).
