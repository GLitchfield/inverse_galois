# 0050 — minblk=8 affine cluster r=24 Route-B (direct radical): BLOCKED, structural + tooling

**Family:** minblk=8 octic-over-cubic affine cluster (14051/14052/16060/16061/19280/20408), r=24 slice.
**Date:** 2026-07-07. **Depends on:** 0049 (Route-B sizing; fix8 seed-deformation DEAD),
0045 (Route-A direct-Res = wreath 24916/24922, not the twists).
**Question:** Track F sized Route B (direct totally-positive radical) as S=1 / disc-smooth and
deferred the build. Can it be carried out in **pure PARI/GP**, reusing the certified 8T48 seed
octic + a totally-real cubic, to enqueue a density-verified r=24 model for at least one target?

**Verdict: BLOCKED in pure PARI/GP**, and the reason **splits by cluster** (GAP-verified — do not
over-generalize). It is not a build-cost wall (the whole degree-192 radical tower builds in ~20–40 s);
it is a **STRUCTURAL** wall for cluster A + a **module-selection/extraction** wall for cluster B,
both landing on the same **TOOLING** need (Galois-module class field theory PARI doesn't automate).
Needs OSCAR/Magma. **Nothing enqueued** (no density-verifiable model). All 6 (t,24) re-verified
teamCount==0 (OPEN); none in `realized.csv`.

- **Cluster A — 14051/14052/16060/16061 (irreducible (C2)^6):** the seed `F_8` and `W=F_8·k` are
  **structurally disjoint** from the target closure `L` — no radical tower over them can reach these.
- **Cluster B — 19280/20408 (reducible (C2)^9 = 3⊕6):** `W` **IS** a subfield of `L` (the diagonal-3
  is `W`'s 2-core), so `W` is the right universe; blocked at module-selection + degree-192 extraction.

## Group structure (GAP, definitive)

All SPLIT extensions `N:Q` (`scripts/mb8_affine_kernel_scope.g`, `mb8_block_action.g`):

| t | \|G\| | Q | N | block-8 action | point-stab | subfields |
|---|------|---|---|---|---|---|
| 14051/14052 | 32256 | C3×PSL(3,2) | (C2)^6 irred (3⊗F4) | 8T48=AGL(3,2) | AGL(3,2) | [1,3,24] |
| 16060/16061 | 64512 | S3×PSL(3,2) | (C2)^6 irred | 8T48 | AGL(3,2):C2 | [1,3,24] |
| 19280 | 258048 | C3×PSL(3,2) | (C2)^9 = 3⊕6 | 8T48 | (C2)^3:AGL(3,2) | [1,3,24] |
| 20408 | 516096 | S3×PSL(3,2) | (C2)^9 = 6⊕3 | 8T48 | (C2)^4:AGL(3,2) | [1,3,24] |

## Why the PARI-feasible radical routes fail — split by cluster (GAP-verified)

The only bases PARI can `bnfinit` cheaply are the seed octic **F_8** (8T48, deg 8) and the
compositum **W = F_8·k** (deg 24, subfields `[1,3,8,24]`). All 6 targets have subfields `[1,3,24]`
(`data/targets/mb8/mb8_subfields.txt`): `E24/k` is a **primitive** octic (no degree-8 subfield),
and the block-of-8 `8T48` is only the **block-stabiliser** (index 3) action, never a degree-8 field
over Q. From there the two clusters **diverge** — this is where my first-pass "disjoint from *every*
target" claim was too strong and had to be corrected:

**Cluster A (14051/14052/16060/16061, irreducible (C2)^6) — structurally disjoint (airtight):**
- GAP: 24T14051 and 24T16060 have **ZERO** normal `K` with `|G/K| = 4032`, so
  `closure(W) = AGL(3,2)×C3 = (C2)^3:(C3×L3(2))` is **not a quotient of `G`** ⇒ `W ⊄ L`.
- GAP: 24T14051 has **0** normal `(C2)^3` in `O2(G)` and **no** `AGL(3,2)` (order-1344) quotient
  (`N` Q-irreducible ⇒ no `(C2)^3` submodule).
- Empirical: `C48 = K16·k` (`K16 = F_8(√θ)`, θ the 0049 totally-positive S-unit at q=21557) has a
  **UNIQUE** degree-24 subfield = the diagonal `W`. ⇒ **no radical tower over the seed / W** reaches
  cluster A; the full **L3(2)-frame relative Kummer** is required.

**Cluster B (19280/20408, reducible (C2)^9 = 3⊕6) — W ⊂ L, but module + extraction wall:**
- GAP: 24T19280 has **exactly one** order-4032 quotient = `C3 × ((C2)^3:PSL(3,2)) = C3 × AGL(3,2) =
  closure(W)` (its `O2` = the irreducible diagonal-3). So **`W` IS a subfield of `L(19280)`** — the
  diagonal-3 summand of the kernel is exactly `W`'s 2-core. (20408 is the S3 analog,
  `closure(W)=AGL(3,2)×S3` order 8064; kernel `6⊕3` also carries the diagonal.)
- So `W` is the *right* universe here. But `E24 ∩ W = k` (W's subfields `{1,3,8,24}` have no
  degree-6/12), so `E24` sits in a **degree-192** intermediate of `W(√(6-dim F-module))`. Blocked at
  **(a)** selecting the F4-twist **6-dim** Galois-stable module classes over `W` (needs the
  `F2[Q]`-module decomposition of `Cl(W)/S-units`), and **(b)** extracting `E24` — `nfsubfields(deg
  192)` **did not return in > 8 min**.

## The wall is NOT build-cost, and NOT the frame (`scripts/mb8_routeb.py --probe`)

| step | cost |
|---|---|
| bnfinit(W, deg 24 = F_8·k) | ~0.4 s, classno 1, unit-sign rank 21/24 |
| 3× rnfequation `x²−θ` (deg 48) | ~0.1 s |
| polcompositum → deg 96 | ~3 s (coef 134 bit) |
| polcompositum → deg 192 (full (C2)^3-Kummer of W) | **~20–40 s — BUILDS** |
| nfsubfields(deg 192, 24) | **> 8 min, no return — the extraction wall (moot for cluster A, real for cluster B)** |
| bnfinit(L3(2) septic, deg 7) | ~0.005 s, classno 1 |
| bnfinit(C3×L3(2) frame model, deg 21 = septic·k) | ~0.5 s, classno 1, **tot-pos codim 0** |

The correct **frame** `M = (C3\|S3)×L3(2)` field (deg 504\|1008; PARI-feasible non-Galois model
`M0 = L3(2)-septic · cubic`, deg 21\|42) is bnfinit-cheap, and its **totally-positive codim is 0**
⇒ every radicand is sign-fixable ⇒ **r=24 is clean** (the one Route-B step that *is* PARI-native).

## What is missing (TOOLING spec → build_backlog)

Realizing `N = (C2)^6 = 3⊗F4` (irred) / `(C2)^9 = 3 ⊕ 3⊗F4` over the frame needs, per step:
- **(i) module selection** — pick the 6-dim F4-twisted `F2[Q]`-submodule of `Cl(M)/2` (+ S-units)
  as square-classes. The `Q=C3×L3(2)` action lives on the **degree-504 closure**, not on the
  degree-21 `M0`; PARI gives the class group but **not its Galois-module decomposition**.
- **(ii) totally-positive** — sign-fix radicands. *PARI-feasible* (codim 0, above).
- **(iii) torsor assembly** — build the AGL(3,2) octic over `k` as the `(C2)^3`-torsor with the
  prescribed C3-twist = assemble the L3(2)-conjugate radicals into a **k-rational** octic. `W/k` is
  **not Galois**, so PARI has no handle on the conjugation; this is a non-abelian torsor over a
  Galois-module datum.
- **(iv) extraction** — reduce the `(C2)^k:Q` group+module datum to the degree-24 **point-stabiliser**
  field `E24`.

**Tooling:** Magma (class field theory with automorphisms / `AbelianExtension` carrying the Q-module
map, `GaloisRepresentations`, subfield-from-subgroup) or OSCAR/Hecke (`ray_class_field` with a map
respecting the Galois action, norm-group selection of the F4-twisted submodule, `absolute_field` +
group-theoretic point-stab). ⇒ a **deg-24 OSCAR/Magma relative-Kummer engine** build_backlog item,
not a PARI producer. Once such an engine emits 25-coeff models, `scripts/mb8_routeb.py --enqueue`
gates (deg24+irred, polsturm==24, mb8_match density vs Gassmann/wreath, scoreable_disc) and enqueues
them (`lit:mb8new/pair/alt`, tiers 130/115/100) — turnkey.

## Build / artifacts

- `scripts/mb8_routeb.py` — driver: `--probe` (reproduces this verdict's timings + structural
  checks), `--enqueue` (reuses `mb8_fix8.gate()`/`enqueue_winners()`; enqueues nothing until an
  OSCAR/Magma model exists). Reuses the 0049 gate + theta machinery.
- `scripts/mb8_routeb_quotient.g` — the load-bearing GAP check: is `closure(W)=AGL(3,2)×(C3|S3)`
  a quotient of each `G` (⇔ `W ⊂ L`)? Splits cluster A (0 quotients) from B (1 quotient).
- `scripts/mb8_affine_kernel_scope.g`, `scripts/mb8_block_action.g` — kernel-module dims/split +
  block/point-stab structure (committed).
- `data/processed/routeb_feasibility.json` — the reproducible verdict (structure + timings + spec).
- scratchpad (one-shot exploration; durable timings via `mb8_routeb.py --probe`): `rb_explore.gp`,
  `rb_sub24.gp` (C48 unique-subfield), `rb_wtwist.gp`, `rb_deg192*.gp`, `rb_wall.gp` (deg-192 build
  timings), `rb_frame.gp` (frame feasibility).

## Learnings

1. **The blocker is not one thing — it splits by kernel-module type, and the first-pass "disjoint
   from every target" was too strong.** Cluster A (irreducible (C2)^6): seed/W are genuinely the
   wrong universe (`closure(W)=AGL(3,2)×C3` is *not* a quotient — GAP: 0 order-4032 quotients).
   Cluster B (reducible (C2)^9=3⊕6): `W` **is** a subfield of `L` (the diagonal-3 = `W`'s 2-core;
   GAP: `C3×AGL(3,2)` is a genuine quotient of 19280), so the block there is module-selection +
   degree-192 extraction, not disjointness. Verifying the group-theory before generalizing caught
   the over-claim.
2. **PARI build cost was never the wall** — the full degree-192 Kummer tower builds in <1 min; the
   walls are (A) structural disjointness / (B) `nfsubfields(192)` (>8 min, no return) **plus** the
   missing Galois-module decomposition of the class group needed to *select* the F4-twist module.
3. **The correct frame is cheap and r=24 is free over it** (deg-7/deg-21 bnfinit ~ms; tot-pos codim
   0). The residual is the relative-Kummer *module selection + torsor assembly + point-stab
   extraction* — a clean, well-scoped OSCAR/Magma tooling task, the honest deferral point. Cluster B
   (19280/20408) is the nearer-term OSCAR target since `W` already sits inside `L`.
