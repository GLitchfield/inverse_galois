# 0052 — OSCAR/Hecke relative-Kummer + Galois-module CFT for the minblk=8 cluster-B twist

**Family:** minblk=8 octic-over-cubic affine cluster, cluster B (19280/20408), r=any slice.
**Date:** 2026-07-07. **Depends on:** 0050 (Route-B BLOCKED in PARI; the 4-step OSCAR spec),
0049 (fix8 seed-deformation DEAD), 0045 (direct-Res = wreath 24916/24922, not the twists).
**Question:** Can OSCAR/Hecke (the relative-Kummer + class-field-theory-with-automorphisms stack
PARI lacks) break the four test-0050 walls and emit an irreducible degree-24 model that locally
labels **24T19280 = (C2)^9:(C3×L3(2))** (kernel (C2)^9 = 3⊕6 = V⊗F2[C3])?

**Verdict: PARTIAL, then BLOCKED at the SAME essential MODULE wall as PARI.** OSCAR/Hecke does
the tractable abelian arithmetic over the degree-21 non-Galois frame model `M0 = S7·k`
(class_group, ray_class_group, induced C3-action) — realizing spec-step **(ii) totally-positive**
— but **walls at spec-step (i) module-selection**: resolving the F4-twisted 6-dim
`F2[C3×L3(2)]`-submodule needs the **L3(2)-action**, which lives on the **degree-168 L3(2)-closure**.
`normal_closure(S7)→deg168` **did not return in 900s**; `automorphism_group(M0)=C3` only (the L3(2)
is invisible on the non-Galois M0). Steps (iii) torsor-assembly and (iv) extraction are moot.
**Nothing enqueued** (no density-verifiable model). (19280,r) and (20408,r) re-verified tc=0 OPEN
for all r∈{0,4,8,12,16,24} vs `progress.json`; none in `realized.csv`.

## The load-bearing new structural fact (GAP, `modcmp.g`)

| t | \|G\| | Q | O2 = (C2)^9 module |
|---|------|---|---|
| **24T19280** (twist) | 258048 | **C3 × PSL(3,2)** (SINGLE shared L3(2)) | **[3, 6] reducible** = V ⊕ V⊗F4 |
| 24T24916 (wreath, from direct-Res) | 7.28e9 | (PSL(3,2)³):C3 (THREE independent L3(2)) | [9] **irreducible** |

Direct-Res (test 0045) builds the **wreath** because `Res_y(c(y), Malle-AGL-family(a,y,X))` varies
the *whole* octic with y ⇒ three independent L3(2), one per cubic conjugate. The twist 19280 needs
the **same (shared) L3(2)** across all 3 blocks, twisting **only the (C2)³ radicands** by the cubic
⇒ a genuine **tensor** module V⊗F2[C3].

**Why the "just twist by the cubic" shortcuts all fail — the tensor obstruction.** Square-classes
form an **F2-vector space**. Multiplying a septic-class `θ_S` by a cubic-class `μ` gives *sums*
`[θ_S]+[μ]`, whose F2-span is ≤ dim V + dim F2[C3] = 3+3 = **6**, never the **tensor** V⊗F2[C3] of
dim 3·3 = **9**. So no product/quadratic-twist of the seed octic by k realizes the 9-dim kernel
(it lands on a subquotient group, not 19280). Realizing the genuine tensor requires **9 independent
square-classes in the frame field with the prescribed non-product Galois action** = the class /
S-unit group of the degree-168 (L3(2)-closure) or degree-504 (full frame) field.

## Empirical feasibility ladder (OSCAR 1.7.3 / Hecke VN62X; `scripts/oscar/mb8_routeb.jl`)

| step | cost | result |
|---|---|---|
| septic `x^7−7x+3` galois_group | 37.9 s (mostly JIT) | order 168, **id (7,5) = L3(2)** ✓ |
| build M0 = S7·k (non-simple → simple) | 3.4 s | degree 21 |
| **class_group(M0 deg21)** | **82.2 s** | `Z/1` (trivial; confirms PARI classno 1) |
| **automorphism_group(M0/Q)** | 2.1 s | **order 3 (C3 only — L3(2) INVISIBLE)** |
| **normal_closure(S7 → deg168)** | **>900 s, exit 124 (NO RETURN)** | the L3(2)-frame **build wall** |
| ray_class_group(M0, mod 2·21557·640663, +9 real pl, n_quo=2) | 101–167 s | **(Z/2)² (rank 2)** |
| induce_action(C3 on ray class group) | 1.5 s | ok (C3-part of the module ONLY) |

Two independent confirmations that OSCAR cannot select the module: (a) `Aut(M0)=C3` exposes only
the C3-isotypic split (diagonal-vs-F4), **not which V within it** — the L3(2)-resolution needs the
degree-168 closure, which does not build; (b) the mod-2 ray class group at the *seed* modulus is only
**(C2)²**, too small to even contain the needed (C2)³ twist ⇒ the F4-twist ramifies at primes beyond
the seed disc {2,21557,640663}, and **its conductor is unknown without the module**.

## The four spec steps (0050) — OSCAR status

- **(i) module-selection** — **WALLED.** Needs the `F2[C3×L3(2)]`-module decomposition of the
  (ray) class group; Hecke sees only the C3-part over M0; the L3(2)-part needs the degree-168
  closure = does not build in 900s.
- **(ii) totally-positive** — **FEASIBLE** in OSCAR (`ray_class_group` takes the real places; sign
  control native). Matches PARI's tot-pos codim 0 over the frame.
- **(iii) torsor-assembly** — **WALLED** (downstream of (i); the k-rational AGL octic with the
  C3-twist needs the L3(2)-conjugation = the closure).
- **(iv) extraction** — abelian arithmetic + subfield extraction over M0 is feasible
  (`ray_class_field` builds), but **moot** without (i)/(iii), and the correct conductor is unknown.

## Assessment: is Magma the fallback?

**Plausible but uncertain — not turnkey.** Magma's `AbelianExtension`/`RayClassField` natively carry
the automorphism (Galois-module) action for **Galois** bases, and its class-group engine is stronger
than Hecke's — so **if** Magma can build/compute the ray class group of the degree-168 L3(2)-closure
**as an L3(2)-module** (at the edge of feasibility — Magma handles degree ~40–60 routinely, 168 is
beyond typical), it could select the F4-twist submodule and do subfield-from-subgroup extraction.
Alternatively a relative embedding-problem path over M0/k might avoid the full closure. Either way it
is a **research-grade computation**, and the twist's conductor must also be determined. We cannot
test it here (no local Magma; only the SAIR verify API). **No wrong-group / unverified model forced
through the gate.**

## Build / artifacts

- `scripts/oscar/mb8_routeb.jl` — the reproducible engine: builds M0, runs the abelian-arithmetic
  ladder (class_group / ray_class_group / induced C3-action), marks the exact module-selection wall,
  and emits `MODEL:<t> <r> <25 asc ints>` lines (0 currently). `MB8_CLOSURE=1` reproduces the
  degree-168 normal_closure hang.
- `scripts/mb8_routeb_oscar.py` — thin driver: runs the .jl, parses MODEL lines, gates+enqueues via
  `mb8_routeb.py`/`mb8_fix8.gate` (`lit:mb8new/pair/alt` tiers 130/115/100). Turnkey; enqueues 0.
- `data/processed/oscar_routeb_probe.json` — the reproducible verdict + full timing ladder.
- `scripts/mb8_routeb_quotient.g`, `mb8_affine_kernel_scope.g`, `mb8_block_action.g` — the GAP
  structure (from 0050) + `scripts/mb8_module_cmp.g` (the 19280-vs-24916 module comparison above).

## Learnings

1. **The 0050 module wall is real and is the SAME for OSCAR — it is not "PARI gives the class group
   but not the module", it is that NEITHER system can afford the degree-168+ field where the module
   lives.** OSCAR breaks PARI wall (ii) and matches PARI's abelian reach, then stops at the identical
   point.
2. **The obstruction is a genuine tensor, not a twist.** V⊗F2[C3] (dim 9) cannot be manufactured by
   multiplying a septic square-class by a cubic square-class (that gives a dim-≤6 *sum*). This kills
   every cheap product/twist shortcut and pins why direct-Res gives the wreath (independent L3(2))
   while the twist needs a shared-L3(2) tensor module.
3. **A totally-real (r1=7) 7T5 septic is only needed for the r=24 slice; all six (19280,r) sigs are
   OPEN tc=0**, so a validator landing does not require r=24 — the block is upstream (module
   selection), not the signature.
4. **Hecke's relative CFT is genuinely useful but insufficient here**: it computes class/ray-class
   groups of the degree-21 M0 and induces the C3-action, but its normality/stability machinery keys
   on the *base field's* automorphisms (`is_normal_easy` needs `#Aut == degree`; the non-Galois M0
   falls to `is_normal_difficult`), and cannot resolve the L3(2)-module without the closure.
