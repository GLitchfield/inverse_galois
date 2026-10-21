# 0003 — Local Galois identifier (WS-INFRA-A), validated vs Magma

**Family:** infra / methods · **Date:** 2026-06-24 · **Scripts:** `src/igp/{gp,gap,verify}.py`,
`scripts/q09_validate_identifier.py`

## Question

Can we confirm a degree-24 polynomial's `24Tt` **locally** (no Magma submission), well enough to verify
deliberate constructions before submitting?

## Method

`verify.confirm_label(coeffs, t)` compares three local invariants against 24Tt's GAP invariants:
- **parity** — `disc(f)` a perfect square ⇔ `Gal ≤ A_24` (`polys`).
- **subfield-degree set** — proper subfields via PARI `nfsubfields` = block-system indices `[G:U]`
  (`gp.subfield_degrees`) vs GAP `IntermediateSubgroups`.
- **Frobenius cycle types** — observed factor-degree partitions mod good primes (`polys`) must be a
  subset of 24Tt's cycle-type set (GAP `ConjugacyClasses`).

GAP invariants are feasible for moderate-order groups (huge wreaths choke `ConjugacyClasses`) — which
is fine: those moderate orders are the solvable mid-order *frontier* we target.

## Result (`q09`, 12 labels of order ≤ 5000, ground-truth = Magma labels in `realized.csv`)

- **Confirmed the true label: 12/12** (no false negatives — the identifier never rejects a correct
  construction).
- **Rejected a wrong label: 9/12.** The 3 non-rejections are groups sharing *all three* invariants
  (e.g. `24T71/254/250/679` all have subfields `[2,3,4,6,8,12]`, even parity, compatible cycle types).

## Learnings

- A **sound confirmer**: parity + subfield structure + cycle-type containment catch gross errors
  (wrong block structure, wrong parity, impossible cycle type). For WS1 (we know the target *by
  construction*) this is exactly the needed pre-submission check.
- **Not a separator** for groups that share block structure + parity + cycle indices — these need finer
  invariants (resolvents / relative resolvents). That's the documented next refinement of WS-INFRA-A.
- Net: we can now **target → construct → confirm offline → submit** for moderate-order groups, instead
  of relying on the submission to discover the label. Enables WS1.
