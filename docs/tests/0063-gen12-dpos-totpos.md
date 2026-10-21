# Test 0063 — gen12 δ>0 totally-positive producer (dive #39 build): δ>0 bases still land the wreath

**Family:** MINBLK=2 / gen12 / non-solvable sub-wreaths
**Date:** 2026-07-12
**Outcome:** [BLOCKED] δ>0 totpos builds land the C₂-wreath/overgroup, not the proper open sub-wreaths — 24 builds, 0 clean target landings. 0 enqueued.

## Question

Dive #39 (auto_log 2026-07-12) hypothesized that the OPEN proper-sub-wreath minblk=2 groups
(24T9641/9642 top 12T74; 24T14616/20699 top 12T183; 24T19246 top 12T230, all at r=24) live over
**δ>0** degree-12 bases (narrow class number h⁺>1). The mechanism: α totally-positive ⇔ real places
split ⇔ r=24, and δ>0 injects 2-torsion so the narrowly-principal square-classes form a PROPER
F₂[H]-submodule ⇒ a smaller-kernel proper sub-wreath. The existing `gen12_totpos_producer.py` keeps
only h⁺=1 (δ=0) bases, which land the MAX wreath (least useful). Does INVERTING that gate — build
`general_c2_totpos` over δ>0 (h⁺>1) bases — land the open sub-wreaths?

## Setup

- New reusable producer `scripts/gen12_dpos_producer.py`: queries `lmfdb.fields(12, galois_label=top,
  max_r2=0, class_number=1)` per top, keeps **h⁺>1** bases (`gp.narrow_class_number`), builds
  `gp.general_c2_totpos(base, w, q)` (deterministic r=24) over completely-split primes × gen12
  C₂-kernel w-patterns (popcount 1–4).
- **Local gate** reuses the test-0061 density fingerprint (`scripts/mb2ns_producer.density_label`
  against `data/processed/mb2ns/gdist.json`, the 7 GAP Chebotarev distributions): keep iff the best
  match is the base's own target 24Tt with **L1 < 0.35 AND 0 impossible cycle types (imp=0)**, plus
  deg-24 irreducible, polsturm==24, `gp.scoreable_disc` non-blank.
- Targets re-verified OPEN in `data/processed/progress.json` (mtime 2026-07-12 02:36): 9641.24,
  9642.24, 14616.24, 19246.24 tc=0 non-baseline unheld (tier new); 20699.24 tc=0 group-held (tier
  pair). **9633.24 is now tc=1 (rival-claimed)** → dropped; 12T33 has no open r=24 target.

## Result

δ>0 bases are abundant exactly as dive #39 claimed — 12T74: h⁺∈{4,8,2}; 12T183: h⁺∈{1,2}; 12T230:
h⁺∈{8,8,16,8}. The totpos builds fire and force r=24. But the density fingerprints are decisive:

| landed group | # builds | min L1 | imp at min |
|---|---|---|---|
| 24T9641 (target neighbor) | 10 | 0.432 | 6 |
| 24T20699 (wreath/overgroup) | 14 | 0.528 | 2 |

**24 δ>0-base builds across all three tops → 0 clean target landings.** EVERY build has imp≥2
impossible cycle types, the density signature of the C₂-wreath/overgroup, not the proper subgroup (a
clean 24T9641 would be L1≈0.2, imp=0, as 24T9633 was in test 0061). The min L1 to any target (9641 at
0.432, imp=6) is well outside the gate. The density gate — a genuine G-invariant that cleanly
separated subgroup↔wreath in test 0061 — rejects all 24. **0 enqueued** (enqueuing wreath-collapse
polys would burn the daily submission budget on the wrong group; the density fingerprint already
labels them as the wreath, no SAIR call needed).

## Learnings

- **Dive #39's hypothesis is REFUTED at the local-gate stage.** δ>0 bases DO inject 2-torsion, but the
  totpos sign-fix generator (multiply by a sign-fixing unit u to force α totally positive) lands in
  the WREATH's square-class, not the narrow-class-selected proper submodule's. This is the same
  wreath-collapse test 0061's blind `general_c2` sweep hit over 12T74/183/230 — the totpos determinism
  changes r (→24) but not the square-class that fixes the group.
- The residual is exactly what the recipe's DEAD branch predicted: reaching the proper sub-wreaths
  needs **Mode (b) — a DIRECTED narrow discrete-log** that picks the target submodule's square-class,
  not the blind sign-fix unit.
- The local density gate saved a full SAIR pilot: the fingerprint is authoritative enough to call the
  collapse (imp≥2 on every build) without spending submission budget.

## Reproducer

```
.venv/bin/python scripts/gen12_dpos_producer.py --bases 6 --nq 2 --max-enqueue 5   # 0 winners
```

Recipe pointer: docs/build_backlog.md (MINBLK=2 gen12_totpos δ>0 item) + auto_log dive #39
(2026-07-12); density gate `scripts/mb2ns_producer.py` + `data/processed/mb2ns/gdist.json`; totpos
primitive `src/igp/gp.py:general_c2_totpos`.
