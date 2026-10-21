# Competition rules — IGP24 (Inverse Galois Problem, degree 24)

> Confirmed 2026-06-24 by deep-research round 1 (`docs/landscape_survey.md`): the central figures and
> mechanics were verified 3-0 across primary sources — Tao's announcement, the SAIR site's overview /
> discoveries pages + embedded bootstrap JSON, the LMFDB, Hulpke's classification, and OEIS A002106.
> **Access caveat:** `competition.sair.foundation` returned HTTP 403 to automated fetches; figures
> were triangulated from Tao's blog, the site's JS bundle, and LMFDB/Hulpke/OEIS rather than read off
> the live HTML. Items under **Still open** are not yet confirmed. Source URLs at the bottom.

## The problem

The **inverse Galois problem** asks whether every finite group is the Galois group of an extension of
`Q`. IGP24 is the constructive, competitive **degree-24** instance: for each transitive permutation
group `G ≤ S_24`, exhibit an **irreducible degree-24 polynomial `P(z) ∈ Z[z]`** whose Galois group
(of its splitting field, as a transitive subgroup of `S_24`) is `G`.

## The 25,000 groups

- The transitive permutation groups on 24 points are classified and labeled `24Tt`, `t = 1..25000`
  (Hulpke's `nTt` convention; `24T1 = C_24` minimal, `24T25000 = S_24` maximal; T-number weakly
  increasing by order). The count **25,000** is confirmed (Hulpke; OEIS A002106(24)=25000).
- **Exactly 5 of the 25,000 are primitive.** Since `24 = 2³·3`, the other **~24,995 (~99.98%) are
  imprimitive** with block systems of size 2, 3, 4, 6, 8, 12 — and Hulpke's classification *builds*
  them recursively from transitive groups of smaller divisor degrees via block/wreath structure.
  **This makes imprimitive / wreath / subfield constructions the natural workhorse for coverage.**
- **24,193 are solvable; 807 are non-solvable.** By **Shafarevich**, every finite solvable group is a
  Galois group over `Q` — so the solvable bulk is realizable *in principle*. But the theorem is
  **existential, not a catalog of small explicit polynomials**: bridging that constructive gap (with
  *small discriminant*) is the competition.

## Signatures `(t, r)`

- Scored per **signature pair `(t, r)`**: `t` = group index; `r` = **number of real roots**, which is
  **even** (`r ∈ {0, 2, 4, …, 24}`, 13 values) because complex roots of a real polynomial come in
  conjugate pairs and `deg = 24`.
- **165,836** achievable `(t,r)` pairs in total (the backend's `validR` counts over all 25,000 groups
  sum to 165,836). Not every `r` is achievable for every `t`. **The per-group reachable-`r` list is
  NOT yet confirmed** (a specific per-`r` breakdown was *refuted* in verification) — get it from the
  SAIR backend `validR` data.

## Verification & scoring — a two-system split (confirmed)

This is the operationally critical detail, and it differs from a naive "smallest discriminant" read:

- **Magma is the mathematical verifier.** A polynomial counts only if **Magma** confirms it is
  **irreducible of degree 24** and computes a **transitive degree-24 Galois group label** (`24Tt`) and
  the **real-root count `r`**. Magma locates the group "within seconds" (degree-24 identification uses
  the degree-independent Fieker–Klüners/Stauduhar algorithm — see `docs/landscape_survey.md`).
- **PARI/GP computes the official *scoring* discriminant.** For each scoreable `(t,r)` pair the
  evaluator computes the **absolute number-field discriminant via PARI/GP `nfdisc`** with a **60-second
  timeout per polynomial**. If any `nfdisc` in the pair times out or fails, the **entire pair** is
  scored with a documented **"mixed discriminant" (prime bound 100000)**. (`disc_source` ∈
  `{exact_nfdisc, mixed_disc}`.) → **The ranking quantity is the field discriminant, not the
  polynomial discriminant.**
- **Exact scoring formula** (per verified `(24Tt, r)` pair, per team): a credited team gets
  **`2^(1-k) · log(D0)/log(D)`** points, where `k` = number of credited teams for the pair, `D` =
  that team's scoring discriminant, `D0` = the smallest `D` among credited teams. Consequences:
  **sole realizer of a non-baseline pair → `k=1`, `D=D0` → 1.0 point**; **beating one baseline pair →
  `k=2` (LMFDB counts as a team) → 0.5**. The `2^(1-k)` factor (rarity) **dominates**; the `log` ratio
  (smaller discriminant) is a mild tiebreaker. ⇒ **breadth-first on rare/open pairs beats grinding
  discriminants.** Per team+pair only the smallest-`D` row is kept; each team is credited ≤ once/pair.
- **Scoreable pair** = a verified pair **outside** the frozen LMFDB baseline (mixed-disc fallback
  allowed), **or** a **baseline pair unlocked by an exact `nfdisc` strictly < `D_base`** (the baseline's
  smallest exact nfdisc for that pair; mixed disc does **not** unlock baseline pairs). Baseline = 286
  groups / 622 signatures. **Per-pair baseline membership is learned per-poly from the submission
  response (`inBaseline`), AND the frozen baseline is now vendored** from the official
  `SAIRcompetition/IGP24-public` (via `scripts/fetch_competition_package.py` →
  `data/targets/baseline_signatures.csv`, `t,r,D_base`; query with `igp.baseline`). The package's
  `competition.yaml` confirms the `2^(1-k)·log(D0)/log(D)` scoring, the nfdisc→mixed-disc rule, and the
  100/day cap. [Reconciled + vendored 2026-06-28, test 0032.]
- **Daily limits:** ≤ 5 submissions/day per team, rising to 100/day once the team has ≥ 5 distinct
  scoreable pairs credited. Within one submission, if several polys verify to the same `(t,r)`, only the
  **first** (file order) counts — so submit one (smallest-disc) poly per expected `(t,r)`.

**Empirical update (2026-06-29) — limits raised 10×, and the verification bottleneck is disc
factorization (competition Zulip; announced by organizer Andrew Sutherland).**
- **Limits: 1000 polynomials/submission and 1000 submissions/day** (was 100/100). "In principle you
  can now submit multiple solutions for every `(t,r)` pair every day." Caveat: organizers ask
  contestants **not to "submit a million random polynomials"** and reserve the right to reduce the
  limit — so keep submissions deduped + coverage-directed. File-size (byte) limit: **unconfirmed**
  (asked on Zulip; no answer given). Our daemon self-caps at `max_posts_day=500`, packs to
  `submit_target=1000`, keeps a 95 KB payload guard, and dedups vs `submitted_lines`.
- **Bottleneck = discriminant factorization, not Galois group.** The verifier trial-divides the poly
  discriminant up to `10^6` then spends a **bounded 60 s** trying to factor the rest; "in most cases
  the bulk of submission processing time is spent in this bounded factoring attempt, not computing the
  Galois group." Implication for us: a poly whose disc has a **large prime factor > 10^6** risks the
  60 s timeout → the mixed-disc fallback (which **cannot unlock baseline**). So disc *smoothness /
  factorability* — not just field-disc magnitude — is a scoring-relevant quality signal.
- **Comment field (`#`):** organizers suggest listing known ramified primes > 10^6 there, but note a
  prime list is insufficient without a **completeness proof**, and this phase asks for no proofs (LLM
  submissions are untrusted). So the comment is advisory only — **not used for scoring now**; may
  matter in Phase 2 (Buchmann–Lenstra maximal-order check when ramified primes are known).

## Submission (confirmed via the public API, 2026-06-24)

Submissions go through the **SAIR public API** — `https://api.sair.foundation/api/public/v1`,
`Authorization: Bearer <key>` — **not** a file upload. `POST /competitions/igp24/submissions` with
content matching `submissionSpec` (kind `igp24-polynomial`):

- `{"polynomials": [<string>, …]}` — an **array of polynomial strings**, **1–1000 items**
  (raised from 100 on 2026-06-29; see update below), total **≤ 100,000 bytes** (request body
  ≤ 131,072) *unless that too was raised — unconfirmed*. Optional `meta.description` (≤ 500 chars).
- **Each string = the 25 integer coefficients, comma-separated, in ASCENDING powers** `a_0,a_1,…,a_24`,
  with **`a_0 ≠ 0`** and **`a_24 = 1` (monic — non-monic is rejected)**. Example `x^24 + x + 1` →
  `1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1`. (In the `submission.txt` form, `#` lines/trailers
  are comments and never affect scoring; claimed labels/discriminants in comments are ignored —
  official values are computed by the verifier.) Implemented in `src/igp/submission.py`.
- Window: **2026-06-15T10:00:00Z → 2026-08-15T12:00:00Z**. **POST body (confirmed):**
  `{"payload": {"polynomials": [...]}, "meta": {"description": ...}}` to
  `/competitions/igp24/submissions`. Requires the **team to be enrolled** (`permission.teamRole:
  activeMember`); otherwise 403 `ENROLL_REQUIRED`.

### API surface (the `inverse-galois` key has competition.read + competition.write)

- `GET /me` — key scopes / owner.
- `GET /competitions/igp24` — config incl. `submissionSpec`, window, limits.
- `GET /competitions/igp24/labels/progress` — cursor-paginated (`?limit=500`, `?cursor=`); per group:
  **`allowedR`** (achievable `r`, i.e. the validR), and per-signature **`minimumDiscAbs`** (the disc to
  beat), `teamCount`, `discovered`. The authoritative target + leaderboard map (snapshot in
  `data/targets/signatures_deg24.csv`).
- `POST /competitions/igp24/submissions`, `GET …/submissions/me`.

Docs live at `https://docs.sair.foundation/docs` (React SPA: `authentication`, `reference/submission-spec`,
`endpoints/competitions/igp24`, …).

## Allowed methods

Unrestricted: computational algebra (Magma, PARI/GP, SageMath, GAP), public databases (LMFDB and
others), papers/preprints, code search, **LLMs and agents**, and collaboration (Zulip). A "black box"
challenge — results over methodology.

## Timeline & structure

- Submissions opened **2026-06-15**; **Stage-1 deadline 2026-08-15T12:00:00Z** (noon UTC).
- **Stage 2** = later focus on the hardest groups (more conceptual/collaborative). Dates/rules TBD.

## Organizers

Terence Tao (UCLA), John Jones (ASU), Jen Paulhus, David Roe (MIT), Andrew Sutherland (MIT) — with the
**LMFDB**.

## Still open

1. **Enrollment:** submitting requires the team to be **enrolled** in IGP24 (`permission.teamRole:
   activeMember`); an un-enrolled key gets HTTP 403 `ENROLL_REQUIRED`. Enroll on the SAIR site (consent
   action) before the first submit. (POST envelope is **confirmed**: `{"payload":{"polynomials":[…]},"meta":{…}}`.)
2. Whether the official **Magma** path is reachable other than via a scored submission (no igp24 playground).
3. Stage-2 details; prizes (not found in the announcement); team/solo rules.

Resolved 2026-06-24 (were open): the submission **format** (25 ascending integer coeffs, monic, `a_0≠0`,
`a_24=1`; example `x^24+x+1` → `1,1,0,…,0,1`) and mechanism (API POST `{polynomials:[…]}`, ≤100, ≤100 KB);
the **exact scoring formula** `2^(1-k)·log D0/log D` + scoreable-pair rules + daily limits (5→100/day);
the per-group **`allowedR`** = validR (165,836 total, exact match); the live coverage map (47,727
signatures / 13,459 groups; each open signature's `minimumDiscAbs`); API auth (`Bearer`); the
25,000-group classification (24,193 / 807 / 5, from GAP). Source: the official IGP24 evaluation doc
(saved page), competition_rules above.

## Sources

- Tao announcement: `https://terrytao.wordpress.com/2026/06/16/third-sair-competition-inverse-galois-challenge/`
- Overview: `https://competition.sair.foundation/competitions/igp24/overview`
- Discoveries / backend JSON: `https://competition.sair.foundation/competitions/igp24/discoveries`
- API docs: `https://competition.sair.foundation/competitions/igp24/api`
- Evaluation setup: `https://competition.sair.foundation/competitions/igp24/evaluation-setup`
- Hulpke, *Constructing transitive permutation groups* (J. Symbolic Comput. 39(1):1–30, 2005): `https://www.math.colostate.edu/~hulpke/paper/ctg.pdf`
- LMFDB: `https://www.lmfdb.org/` (T-number `gg.tnumber`; degree-24 completeness; `24T352` example)
- OEIS A002106 (transitive groups by degree): `https://oeis.org/A002106`
