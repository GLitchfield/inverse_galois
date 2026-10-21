# Test 0062 — gen12 totally-positive DETERMINISTIC r=24 producer (dive #31 build)

Family: `gen12treal` / minblk=2 breadth. Build of the top **Ready** backlog item (dive #31).

## Question
Turn gen12_treal's *stochastic* ~33%-r=24 `general_c2` build into a **deterministic r=24** producer
for the single biggest open slice of the board — the ~10,105 open `r=24` minblk=2 pairs (91% of the
open board, test 0058) — and enqueue a validation batch of concrete r=24 candidates.

## Recipe (dive #31, VERIFIED)
For `K = F(√α)` over a **totally-real** deg-12 base `F` (r₁=12), a real place `v` of `F` splits in
`K` iff `α >_v 0`, so `r(K) = 2·#{v : α >_v 0}` and **r=24 ⟺ α totally positive**. `general_c2`
takes whatever sign the product-ideal generator `g = bnfisprincipal(bnf,∏p_j)[2]` happens to have
(~33% r=24 by luck). The fix (Cohen's unit sign-lattice solve, VERIFIED in `/tmp/nt4.gp`):

```
sg = apply(x->(1-x)/2, nfeltsign(bnf,g))~;      \\ F2 target signs, len r1=12
MF = Mat(apply(x->(1-x)/2, bnfsignunit(bnf)));   \\ r1 x (r1+r2-1) unit-sign matrix / F2
e  = matsolvemod(MF, 2, sg);                      \\ t_INT 0 => narrowly non-principal => SKIP
u  = ∏ fu[k]^e[k];  al = g*u;                      \\ nfeltsign(bnf,al) all +1  => α ≫ 0 => r=24
```

Over an **h⁺=1** base the solve is ALWAYS solvable ⇒ every `(w,q)` yields guaranteed r=24; over
h⁺>1 the per-α `matsolvemod` returning 0 skips the narrowly-non-principal classes (still all-r=24,
lower yield). Note `class_number=1` ⇏ h⁺=1; h⁺ must be computed (`bnfnarrow`).

## What was built
- **`src/igp/gp.py`**: added `general_c2_totpos(f_coeffs, w, q)` (general_c2 + the sign-fix; returns
  `[]` on NOTSPLIT / NONPRINCIPAL / **NOTPOS** / SIGNFAIL / DEGENERATE) and `narrow_class_number`.
- **`scripts/gen12_totpos_producer.py`**: reusable producer. Walks totally-real deg-12 class-number-1
  LMFDB bases (disc-ordered cursor), gates **h⁺==1** (`narrow_class_number`), finds completely-split
  primes, builds r=24 polys via `general_c2_totpos`, HARD-gates (deg-24 irreducible ∧ `polsturm`==24 ∧
  `scoreable_disc` non-blank), shape-open-gates via the gen12 atlas (skip known-dead shapes), and
  enqueues survivors as `ready` tagged `gen12treal:totpos:...` @128 (feeds the existing atlas).

## Verify gate (PARI-only, dive #31 reproducer)
`gp -q < /tmp/nt4.gp` on 12T1/q=71 printed `p1..p3 → FIXED r=24`, `p4 sign-fix UNSOLVABLE` — exactly
as specified (the h⁺=2 obstruction flagged before any build).

## Result — validation batch
Live run `--max-enqueue 12 --max-builds 40 --n-primes 2 --per-group 3 --per-q-cap 2`:
**12 candidates / 12 tags enqueued** (`ready`, coeffs = 25-int ascending lists, @128) over **5
distinct base-fields** (12T222, 12T134, 12T260, 12T18) across 6 split primes. Every candidate:
- deg-24 **irreducible**, `polsturm == 24` (r=24 confirmed by the deterministic sign-fix);
- disc fully **<10⁶-smooth** (max prime factor = the split prime `q` ≤ 44927) ⇒ guaranteed scoreable,
  no grader blank;
- **minblk=2** by construction (K ⊃ the deg-12 subfield F ⇒ 12 blocks of size 2).

h⁺-gating worked live: same galois-label fields with different narrow class number were correctly
split (a 12T260 field with h⁺=1 built; other 12T260/12T134 fields with h⁺=2/4 were skipped).

## Scope / honesty
This is a **breadth** producer: it lands *some* open (t,24) minblk=2 group per build, open-gated at
the **shape** level via the atlas. It does NOT target a fixed 24Tt — the sign-fixing unit `u∉F*²`
changes α's square class, so the exact group is re-learned from **SAIR's Magma label** (the
authoritative gate downstream). Per-poly exact-group density-labeling is not done (no GAP dist for
arbitrary target groups) — consistent with gen12_treal's established posture (structural local gate +
SAIR ground truth). Rationale for budget-safety: every candidate is a valid minblk=2 r=24 field, and
r=24 minblk=2 is the biggest open bucket (10,105 open pairs, 91% of the board).
