# Related work — constructive inverse Galois & degree-24 realization

Annotated bibliography. Entries marked ✓ were surfaced + their relevance confirmed in deep-research
round 1 (`docs/landscape_survey.md`); each note says what it gives us. Grouped by theme. Add DOIs and
new entries as round 2 / Phase 1 proceeds.

## Competition primary sources

- ✓ **Tao, "Third SAIR competition: inverse Galois challenge"** (blog, 2026-06-16) — authoritative
  announcement; verifies the 25,000 / 165,836 / 286 / 622 figures and the scoring sketch verbatim.
  `https://terrytao.wordpress.com/2026/06/16/third-sair-competition-inverse-galois-challenge/`
- ✓ **SAIR IGP24 site** (overview / discoveries / bootstrap JSON) — deadline `2026-08-15T12:00:00Z`,
  `pythonMaxBytes=100000`, `realRootValues=[0,2,…,24]`, the Magma-verify / PARI-`nfdisc`-score split.
  `https://competition.sair.foundation/competitions/igp24/` (403 to automated fetch; via JS bundle).

## Group theory of degree-24 transitive groups

- ✓ **Hulpke, "Constructing transitive permutation groups"** (J. Symbolic Comput. 39(1):1–30, 2005;
  DOI 10.1016/j.jsc.2004.08.002) — the `24Tt` classification + the **recursive imprimitive construction**
  (from smaller divisor-degree transitive groups via block systems / base groups) that motivates M2.
  `https://www.math.colostate.edu/~hulpke/paper/ctg.pdf`
- ✓ **GAP TransGrp library / LMFDB `gg.tnumber`** — the `nTt` labeling (degrees 24–30 from ~v4.3),
  Magma-identical indexing, `TransitiveIdentification` ≤ 30 points. Produces *abstract groups only*, no
  polynomials. `https://www.lmfdb.org/knowledge/show/gg.tnumber`
- ✓ **OEIS A002106** — transitive groups by degree; `a(24)=25000`. `https://oeis.org/A002106`
- ✓ **LMFDB `24T352`** (`C_3 × (C_2 ≀ C_2²)`, order 192, imprimitive, GAP `[192,890]`) — worked example
  of wreath/direct-product decomposition. `https://www.lmfdb.org/GaloisGroup/24T352`

## Databases (coverage to mine — M1)

- ✓ **LMFDB** — degree-24 number fields + Galois DB; the **286/622** baseline; completeness only
  guaranteed for degree `< 20`. `https://www.lmfdb.org/`
- ✓ **Klüners–Malle database** (arXiv math/0102232; `galoisdb.math.upb.de`) — ~100k polynomials, but
  **only up to degree 15**: no degree-24 polynomials directly; source of the *building-block* fields
  (degrees | 24) for M2. `https://arxiv.org/abs/math/0102232`
- **Jones–Roberts** local-fields DB; **Awtrey** degree-24 / composite-degree Galois tables — to confirm
  + annotate in round 2.

## Imprimitive / wreath / tower constructions (M2)

- ✓ **Tower → wreath embedding:** `Gal(L^c/F) ↪ Gal(L^c/K^c) ≀ Gal(K^c/F)` (explicit, constructive) —
  the structural backbone of imprimitive constructions (round-1 arXiv source, to pin the citation).
- ✓ **`C_2 ≀ H` ramification recipe:** tower `L/K/k`, `[L:K]=2`, with an explicit prime-ramification
  criterion guaranteeing `Gal(L/k)=C_2≀H` — a directly usable build (round-1 arXiv source).
- ✓ **Klüners**, wreath-product / field-extension construction notes (Paderborn; bmd2014 slides).
- ✓ **Subfield computation:** principal subfields via `≤ n−1` LLL steps (van Hoeij–Klüners–Novocin
  style) — backs `nfsubfields` for tower decomposition.

## Generic polynomials, rigidity & explicit realizations (M3, M8)

- ✓ **Jensen–Ledet–Yui, *Generic Polynomials: Constructive Aspects of the Inverse Galois Problem***
  (Cambridge) — canonical catalogue of generic/parametric polynomials by group.
- ✓ **Malle–Matzat, *Inverse Galois Theory*** (Springer Monographs, 1999) — the rigidity method,
  rationality criteria, embedding problems; standard reference.
- ✓ **Müller, "A one-parameter family of polynomials with Galois group `M_24` over `Q(t)`"**
  (arXiv 1204.1328) — explicit `Q(t)`-realization of the Mathieu group `M_24` (natural degree-24
  action) via rigidity → a concrete route to one of the hardest targets. `https://arxiv.org/abs/1204.1328`
- ✓ **Malle**, parametric Galois realizations (`pargal.pdf`) — and the finding that rigidity rarely
  gives totally-real specializations (signature control needs ≥ 4 branch points / multi-parameter
  families). `https://agag-malle.math.rptu.de/~malle/download/pargal.pdf`
- **Shafarevich** — every finite solvable group is realizable over `Q` (existential; the constructive
  gap motivates M4). To cite precisely in round 2.

## Galois-group computation & cost (M7)

- ✓ **Fieker–Klüners, "Computation of Galois groups of rational polynomials"** (LMS J. Comput. Math. 17
  (2014) 141–158; arXiv 1211.3588) — first **practical degree-independent** algorithm (Stauduhar +
  better invariants, no transitive-group-classification dependence); the engine behind degree-24
  identification. `https://arxiv.org/abs/1211.3588`
- ✓ **Magma `GaloisGroup` handbook** — no degree limit (Klüners/Geissler/Fieker/Sutherland); identifies
  degree-24 groups "within seconds" → verification is not the bottleneck.
  `http://magma.maths.usyd.edu.au/magma/handbook/text/505`
- ✓ **PARI/GP manual** — `nfdisc` (scoring discriminant), `polredabs`/`polredbest`; `galoisinit` limited
  to **weakly-supersolvable** groups (can't ID generic non-solvable `24Tt`).
  `https://pari.math.u-bordeaux.fr/dochtml/html/General_number_fields.html`
- ✓ **Conrad, "Galois groups via factoring mod p"** — Dedekind's theorem → Frobenius cycle-type
  pre-filter. `https://kconrad.math.uconn.edu/blurbs/gradnumthy/galois-Q-factor-mod-p.pdf`

## Discriminant minimization (M5)

- ✓ Minimum-`|disc|`-by-signature results (e.g. the octic `(2,3)` minimum `4286875`, attained by a
  non-primitive field) — the per-signature minimization IGP24 rewards; targeted Hunter/Pohst/Martinet
  enumeration + LLL + `polredabs`. (Round-1 arXiv source; pin the citation in round 2.)

## 2026-06-30 — Explicit Q(t)/regular realizations of degree-24 groups beyond M24 (igp-research dive)

One research subagent; web dive (arXiv, Malle/Klüners pages, LMFDB). Verdict: **beyond M24 the
literature offers essentially ONE directly-usable degree-24 construction** — the rest bottoms out
below/beside degree 24. The higher-yield move is methodological (coset actions, central extensions),
not finding more published families ("prestige long tail, not a breadth lever").

**The one usable family — Roberts' M12.2** ("Lightly ramified number fields with Galois group
S.M12.A", arXiv:1404.0429, JTNB 28 (2016) 435): explicit polynomial + genus-0 Q(t) families (Covers
A2/C2/D2/E2) for **M12.2 = Aut(M12) = 24T18441** (imprimitive 2x12, non-solvable). Smallest field
(rootdisc ~38.2, τ=53/22): coeffs `1,-11,53,-154,330,-594,1012,-2255,6512,-17710,42768,-89067,154308,
-237699,351252,-483318,623997,-753291,733491,-520641,278586,-104841,15552,2673,81`. The famous
"ramified only at 11" field is 2.M12.2 in degree **48** (out of scope). E2 is never totally real
(no R/Q2 points); totally-real (r=24) needs Covers A2/C2/D2 — pull their equations from the arXiv
**source** (PDF extraction garbles them).

**Dead ends (all cited):** Klüners-Malle "Database for Number Fields" caps at **degree 23**
(galoisdb.math.upb.de — no deg-24 data); their explicit-realization paper is degree ≤15 (JSC 30
(2000) 675); Malle's multi-parameter `pargal` tables are degrees 7-14 (the "24" strings are cycle
shape 2^4, not degree); König's almost-simple Hurwitz polynomials (arXiv:1512.05533) are deg
21/22/31/12/13 (the "24 points / 12 blocks of 2" is a braid/Nielsen object, NOT a Galois group);
Malle's M22/Aut(M22) work is deg 21/22. PSL(2,23)/PGL(2,23): only abstract existence (Zywina,
pi.math.cornell.edu/~zywina/papers/PSL2Galois.pdf; arXiv:2604.27402) — no usable explicit poly.
**No bespoke published Q(t) families exist for individual SOLVABLE 24Tt** — confirms our tower engine
is the right tool for the solvable bulk; don't expect the literature to hand those over.

**Method lever (the real find): small simple groups in their degree-24 COSET action via PARI
resolvents** — a non-normal degree-24 subfield of G's splitting field (`galoissubfields`/`nfsubfields`
/ resolvent). Examples: 24T201/202/203 (S5, SL(2,5)=2.A5), 24T284 (PSL(2,7)). Complementary to our
abelian-kernel towers; reaches obscure non-solvable groups. (Verified open subset below.)

**Verified against progress.json (corrects the subagent on 3 points):** M12.2 r=0 is k=2 (not 1);
**24T18441 r=8 and r=24 are OPEN (k=0)**, sibling **24T18440 r=0/r=24 OPEN**; **M24 24T24680 r=8 and
r=24 are OPEN (k=0)** (we hold only the k=11 r=0); **24T201 r=24 OPEN**; 24T202 r=0 is k=1 (NOT open,
subagent said 0); 24T284 is k=5 (not 2); **PSL(2,23)=24T7817 r0 and PGL(2,23)=24T10255 r0 are k=0
OPEN and we do NOT hold them** (subagent wrongly said we do).

## 2026-06-30 — Rigidity / rationality for non-solvable degree-24 groups (igp-research dive)

One subagent. **Strategic frame:** only 5 degree-24 groups are primitive (PSL(2,23), PGL(2,23), M24,
A24, S24); the other ~802 non-solvable 24Tt are imprimitive towers. Rigidity/Belyi/Hurwitz natively
output groups in their PRIMITIVE action → its degree-24 products are the FAMOUS contested primitives,
not the obscure towers. So rigidity is best repurposed as (i) a signature/disc engine on families we
already hold, and (ii) a targeted weapon AFTER a screen that finds the rare obscure 24Tt with a
rational rigid triple.

**Rigidity criterion (recap):** a tuple of conj classes (C1..Cn) of G (trivial center) is rigid if
the generating product-1 tuples form a single G-orbit (Thompson); if all Ci are RATIONAL classes the
field of definition is Q → regular over Q(t) → over Q by Hilbert. Pure rigidity = 3-branch-point
cover (genus-0 ⇒ a rational φ(x), family φ(x)-t); ≥4 branch points = Hurwitz families needing a
Q-point + genus-0 fiber. (Malle-Matzat *Inverse Galois Theory*; Ranjbar arXiv:1512.08708; Wittenberg
arXiv:2302.13719.)

**Key explicit results (cited):**
- **Bosman: explicit degree-24 PGL(2,23) polynomial, ramified ONLY at 23** — projective mod-23 image
  of the level-1 weight-22 cusp form on P^1(F_23) (24 pts): `x^24-11x^23+46x^22-...` (full 25 coeffs
  in arXiv:0710.1237 Table 4 = Edixhoven-Couveignes book arXiv:math/0605244 ch.7). Companion paper
  arXiv:1109.6879 does PSL2(25/32/49), PGL2(25/27) (degrees 26/33/50/26/28 — not 24); the METHOD
  extends to PSL(2,23)/PGL(2,23) in degree 24.
- **Roberts M12.2 (arXiv:1404.0429)** also yields **2.M12, 2.M12.2** (more non-solvable deg-24/48);
  3-point covers (rigid), genus 0, rootdisc≈38.2, one 2.M12.2 ramified only at 11.
- **M24 (Müller arXiv:1204.1328)** is NOT a rigid triple — 4 branch points, base = positive-rank
  elliptic curve. Don't hunt an M24 rigid triple.
- Computational-rigidity engine (König arXiv:1512.05533; Barth-Wenz arXiv:1703.02848 deg 50-250;
  Belyi-map code Klug-Musty-Schiavone-Voight arXiv:1311.2529) targets large almost-simple groups —
  NONE in degree 24. LMFDB Belyi DB caps at degree 9; galoisdb at 23.

**Verified vs progress.json:** PGL(2,23)=24T10255 (valid r {0,2,24}: r0 & r24 OPEN k=0, r2 k=1) and
PSL(2,23)=24T7817 (r {0,24}, both OPEN k=0) — **we hold NEITHER**. So both primitive groups are
genuinely open, and Bosman gives an explicit PGL(2,23) field. Matzat GAR-realizations only give
existence (which our towers already achieve).
