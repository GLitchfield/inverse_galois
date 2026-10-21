# Landscape survey — round 1 (2026-06-24)

Cited synthesis from the first deep-research pass (5 search angles → 25 sources → 113 extracted
claims → 25 adversarially verified, **22 confirmed / 3 refuted**). This is the verified factual
substrate + strategic picture; the actionable per-method catalogue lives in `docs/design/arsenal.md`,
and the annotated bibliography in `docs/related_work.md`. Competition mechanics are in
`docs/competition_rules.md`.

**Scope honesty (carried verbatim from the run):** the verification phase locked down the
**competition framing** and the **group-classification methodology**, and surfaced the right primary
sources for the construction methods — but the detailed *per-method realizability recipes* (which
named `24Tt` each method provably reaches, exact commands, discriminant/signature control) were
**largely not among the surviving verified claims**. Treat round 1 as the foundation + reading list;
the method recipes need a **targeted round 2** (see Open questions).

## Verified factual substrate (high confidence, 3-0 votes)

- **25,000** transitive groups of degree 24 (`24T1=C_24` … `24T25000=S_24`); **5 primitive**, so
  **~24,995 (~99.98%) imprimitive**. **24,193 solvable / 807 non-solvable.**
- **165,836** achievable `(t,r)` signatures (`r` even, 0–24). Aggregate confirmed; **per-group `r`
  reachability NOT confirmed** (a specific per-`r` breakdown was refuted).
- **LMFDB baseline: 286 groups / 622 signatures** (frozen). LMFDB number-field completeness is only
  guaranteed for degree `< 20`, so degree 24 is outside it.
- **Verify/score split:** **Magma** verifies irreducible + degree-24 + `24Tt` label + `r`; **PARI/GP
  `nfdisc`** (60 s/poly; mixed-disc fallback, prime bound 100000) gives the **scoring discriminant**.
  Score `[0,1]` = f(discriminant smallness vs best-known, **rarity**). `submission.txt ≤ 100,000 bytes`,
  25 comma-separated int coeffs/line. Deadline **2026-08-15T12:00:00Z**.
- **Shafarevich:** every finite solvable group is realizable over `Q` — but **existentially**; "not a
  practical catalog of explicit small polynomials." The constructive gap is the whole game.

## Strategic picture

1. **Imprimitive/wreath constructions are the workhorse.** ~99.98% of targets are imprimitive, and
   Hulpke's *classification itself* builds them from smaller divisor-degree transitive groups via block
   systems + base groups "in analogy to wreath products." The number-theory mirror is exact: a tower
   `F ⊆ K ⊆ L` has `Gal(L^c/F)` embedding into the wreath product `Gal(L^c/K^c) ≀ Gal(K^c/F)`
   (constructive, proven). So degree-24 imprimitive groups should be reachable by composing/towering
   fields of degrees dividing 24 (2,3,4,6,8,12) — the cheapest route to broad coverage. Worked example:
   `24T352` = `C_3 × (C_2 ≀ C_2²)`, order 192, imprimitive (GAP `[192,890]`).
2. **The solvable bulk needs *explicit* construction, not just existence.** Shafarevich gives existence;
   small-discriminant explicit polynomials come from class field theory / generic polynomials / towers.
3. **The hard residual = the 807 non-solvable (incl. the 5 primitive) groups.** These are the Stage-2
   targets. Some have explicit `Q(t)`-realizations to specialize — notably **Müller's one-parameter
   family with Galois group `M_24`** (the Mathieu group in its natural degree-24 action) via rigidity.
4. **Databases give a head start but not degree-24 polynomials directly.** The **Klüners–Malle DB**
   (~100k polynomials) only covers transitive groups up to **degree 15** — so it yields NO degree-24
   polynomial directly; it is useful as a source of the *smaller building-block fields* (degrees | 24)
   that feed the imprimitive constructions. LMFDB is the source of the 286/622 baseline + degree-24
   fields beyond it.

## Tooling reality (degree-24 feasibility)

- **Galois-group identification at degree 24 is solved and fast.** Magma's `GaloisGroup` uses the
  **degree-independent Fieker–Klüners algorithm** (a Stauduhar variant with improved invariants, **no
  dependence on the transitive-group classification**, no max degree). Per-degree resolvent
  implementations historically stopped around degree 23 (Geissler 2003); the general algorithm passed
  that. Magma identifies a degree-24 group "within seconds" — so verification is *not* the bottleneck.
- **PARI/GP is limited for non-solvable groups.** `nfgaloisconj`/`galoisinit` only handle
  **weakly-supersolvable** Galois groups (returns 0 otherwise), so PARI can't directly identify generic
  non-solvable `24Tt` (`A_24`, `S_24`, simple/sporadic) — but it *does* compute `nfdisc` (the scoring
  discriminant) and is the project's local workhorse for the solvable bulk + discriminant work.
- **Cheap pre-filter:** Dedekind's theorem — factoring `f` mod good primes `p ∤ disc f` gives an element
  of `Gal` of the corresponding cycle type. Sampling many primes → a Frobenius cycle-type distribution
  that narrows/rules-out the `24Tt` cheaply *before* a Magma call (conserving any API budget).
- **Subfield computation** (for imprimitive/tower work): all principal subfields are computable in
  `≤ n−1` LLL-based linear-algebra steps (van Hoeij–Klüners–Novocin style); useful for `nfsubfields`.
- **Discriminant minimization:** `polredabs`/`polredbest` canonicalize to small coefficients;
  LLL-reduction of the polynomial lattice; targeted small-discriminant field enumeration. Benchmark-type
  results exist (e.g. min `|disc|` octic of signature `(2,3)` is 4286875, achieved by a non-primitive
  field) — the same per-signature minimization IGP24 rewards.

## Signature (`r`) control

The standard rigidity / three-point-branched-cover method **almost never yields totally real
specializations**; controlling the complex-conjugation class (hence `r`) needs covers ramified in
**≥ 4 points**, motivating **multi-parameter (2–4 parameter) families**. So hitting *all* achievable
`r` for a fixed `t` is a real sub-problem, not automatic — relevant because each `(t,r)` scores
separately.

## Refuted / do-not-rely-on

- A specific **per-`r` reachability breakdown** (e.g. "`r=22` reachable for only 376 groups") — refuted.
- A reconstruction of the **622 baseline** as a specific `baselineR` grid — not confirmed.
- A **live-snapshot solve count** ("47,249 signatures across 13,385 groups") — refuted; use only the
  frozen 286/622 baseline.

## Sources (round 1)

Primary: Tao announcement; SAIR overview/discoveries + bootstrap JSON; Hulpke `ctg.pdf` (J. Symbolic
Comput. 39(1):1–30, 2005); LMFDB (`gg.tnumber`, degree-24 completeness, `24T352`, `GaloisGroup` filter);
OEIS A002106; Klüners–Malle DB (arXiv math/0102232; galoisdb.math.upb.de); Fieker–Klüners (arXiv
1211.3588, LMS JCM 17 (2014) 141–158); Magma `GaloisGroup` handbook; PARI/GP manual; Müller, *A
one-parameter family with Galois group M24 over Q(t)* (arXiv 1204.1328); Jensen–Ledet–Yui, *Generic
Polynomials* (Cambridge); Malle–Matzat, *Inverse Galois Theory* (Springer); Malle, parametric
realizations (`pargal.pdf`); Conrad, *Galois groups via factoring mod p*. Full annotations in
`docs/related_work.md`.
