# Test 0067 — the TWO-PRIME radical (`general_c2_multi`): the kernel law holds, the targets don't

**Family:** minblk=2 / general_c2 multi-prime radical · **Date:** 2026-07-12 · **Status:**
**LOCAL-GATED, 0 enqueued — dive #48's kernel law CONFIRMED, its target list REFUTED** ·
**Scripts:** `scripts/mb2_multi.py`, `scripts/mb2_multi_gdist.g` · **Recipe:** auto_log dive #48,
build_backlog top-Ready item

## Question

Dive #46 established (and test 0066 cashed in for two sole-1.0s) that a single radical `K₀(√α)` with
α's divisor on a subset `w` of the primes above ONE completely-split prime `q` realizes block kernel
`⟨H·1_w⟩` — a **cyclic** F₂[H]-module. Dive #48 derived the extension: put α's divisor on **two**
split primes,

    α = gen( ∏_{j∈w₁} π_j^(q₁) · ∏_{j∈w₂} π_j^(q₂) ),

still ONE radical (the field stays degree 24 — only the ramified primes change), so the realized
kernel becomes `⟨H·1_{w₁}⟩ + ⟨H·1_{w₂}⟩` and the **µ(K)=2** targets — 99.8% of the open minblk=2
board — come into range. The census priced the dim-11 / one-relation shortlist at **~4.6%
end-to-end yield per random candidate**, ~90× cheaper than the 9641/9642 sweep that already paid.

The law was an explicit **DERIVATION, not a validated result**; its first empirical test is the local
Frobenius fingerprint. Does it hold, and does it land the targets?

**Answer: the law holds and the targets are unreachable — for a reason the census never modelled.**

## Setup

Base `K₀ = [-16,124,159,-1913,1181,1901,-1050,-610,304,70,-33,-2,1]` (12T210, LMFDB, re-verified
fresh in PARI: totally real, `h = 1`, `sign = [12,0]`). Split primes `q₁ = 3761`, `q₂ = 15649`.
Targets from the backlog: `(24T22548, 24T22544, 24T22547, 24T22543)` at r=24 — all re-verified
`teamCount=0`, `is_baseline=False`, **zero rows** in `realized.csv` at build time.

**The label library (`scripts/mb2_multi_gdist.g`) — and the correction it forced.** Every group this
construction can land in is a subgroup of `W = C₂ ≀ H` whose intersection with the base is an
H-submodule `K ⊆ F₂¹²`. My first library enumerated the submodule lattice (14 submodules) and built
the **split** group `C₂^K ⋊ H` for each. The dim-11 submodule came back as **24T22545 — not our
targets.** The reason is the piece dive #48 omitted: a subgroup of `W` with base-intersection `K` and
full projection to `H` is **not** determined by `K`. The complement can be twisted by a cocycle in
`H¹(H, F₂¹²/K)`, and since `dim F₂¹²/K = 1` with trivial H-action, that group is `Hom(H, F₂)` — a
**quadratic character χ of H**. So the library must enumerate *submodules × complement classes*
(`ComplementClassesRepresentatives` of `base/K` in `W/K`, pulled back). Done properly it yields **78
groups**, and the dim-11 submodule alone supports **six** siblings:

| dim-11 sibling | 22543 | 22544 | 22545 | 22546 | 22547 | 22548 |
|---|---|---|---|---|---|---|
| complement | twisted | twisted | **SPLIT** | twisted | twisted | twisted |
| r=24 status | tc=0 | tc=0 | tc=1 (**us**, 90 rows) | tc=1 (us, 20 rows) | tc=0 | tc=0 |

**All four backlog targets are twisted siblings; the split one is the one we already hold.** Their
pairwise cycle-type L1 distances are ≥ 0.481, so an L1 < 0.35 gate against a *specific* dim-11 target
is genuinely discriminating (unlike the 9641/9642 Gassmann pair of test 0066).

Fingerprint as test 0066 (the cheap path): for p unramified in K₀ with p ∉ {q₁,q₂}, α is a p-unit, so
the degree-24 cycle type at p is read off the base decomposition — each prime `P|p` of residue degree
`f` contributes `(f,f)` if α is a square mod P, else `(2f)`. `nfmodpr` + `issquare` over one amortized
`bnfinit`, ~310 ms/candidate, early-abort on the first impossible cycle type; no `rnfequation` needed
to label a candidate.

## Result

**1. The kernel half of the two-prime law is CONFIRMED.** Two split primes do reach dim-11 (µ=2)
kernels — **194 of 288** fingerprinted candidates in the first twist sweep, **497 of 762** in the
main one. A single-radical engine provably cannot reach these (dive #47's cyclicity criterion). The
derivation's central claim is real, and it is the first empirical validation of it.

**2. The targeting premise is REFUTED: the kernel does not determine the group, and the twist is not
a dial.** Every confident dim-11 landing is **24T22545, the split complement — 497/497**, across
**762 distinct square classes** (i.e. every unit twist of every (w₁,w₂) pair). The unit twist moves
the signature `r` freely (r ∈ {4,8,12,16,20} all observed) but **never** moves the complement.

**The mechanism (a norm argument, confirmed on both sides).** χ is the character `σ ↦ λ(v(σ))` where
λ is the H-invariant functional with kernel K; it is cut out by the quadratic field `Q(√N(α))`. For
a divisor supported on completely-split primes, `N(α) = ±q₁^|w₁| · q₂^|w₂|` times a unit norm (±1):

- **|w₁|, |w₂| even** ⇒ `N(α) ≡ ±1` mod squares ⇒ **χ is forced trivial** ⇒ the split complement,
  always. (This test: 497/497.)
- **|w₁| or |w₂| odd** ⇒ `N(α) ≡ ±q₁` mod squares — and `Q(√q₁)` ramifies at q₁, which is *unramified*
  in the closure of K₀, so **no such χ exists**: the group must leave the family entirely. Probe with
  weights (5,6),(5,8),(3,6),(7,6),(5,5): **0 of the candidates even pass the allowed-cycle-type
  screen** — they are not any group in the 78-member library. Confirmed.

⇒ **24T22543/22544/22547/22548 are unreachable by ANY split-prime radical — single- or multi-prime,
under any unit twist.** Adding primes changes the *kernel*; it cannot change the *twist*.

**3. Corroboration that the fingerprint is right.** The engine's confident landings are 22545 (dim
11), 21610/21613 (dim 10), 20576 (dim 9), 21612 — and these are exactly the **split complements** of
their submodules, i.e. precisely the groups our blind `gen12` harvest has already realized (22545: 90
rows, 21610: 155, 21613: 89, 23274: 374). The `teamCount=1` on 22545 is **us**, not a rival. The
construction lands where the fingerprint says it lands.

**4. Gate honesty — the one unheld landing was correctly refused.** `24T21611` (dim 10, zero rows,
open at r ∈ {16,20,24}) appeared once. It was **not** enqueued, for two independent reasons: its
`r = 12` is not an open pair, **and** the dim-10 siblings are *not* density-separable — their pairwise
L1 runs as low as **0.175** (21611↔21612) while observed candidate L1 is 0.15–0.32, so an L1 gate
cannot tell 21611 from 21610/21612. Claiming it would be exactly the "matches a neighbour, not the
target" error that killed tests 0044/0045/0051–0054. **The fingerprint is decisive at dim 11
(siblings ≥ 0.48 apart) and NOT decisive at dim 10.**

**0 candidates enqueued. No SAIR budget burned.**

## Learnings

- **µ(K) prices the kernel, not the group.** Dive #48's census is correct group theory but answers the
  wrong question: it counts F₂[H]-module generators of the block kernel and concludes reachability.
  Reachability also needs the **complement cocycle** `χ ∈ Hom(H, F₂)`, and a split-prime radical has
  `N(α) ≡ ±1` mod squares, which forces `χ = 1`. **A radical construction on split primes reaches
  exactly ONE group per submodule — the split complement — and those are the groups a blind harvest
  already finds.** This re-prices the whole census: the "908 µ=2 groups with r=24 open / ~4.6% yield"
  headline counts mostly *twisted* siblings, which are not addressable this way. The open pairs in
  these families are open *precisely because* they are the twisted ones — the split sibling is what
  a blind harvest (ours included) lands on first.
- **Enumerate submodules × complements, never submodules alone.** The split group `C₂^K ⋊ H` is one of
  up to `|Hom(H,F₂)|` groups sharing the kernel. Building the label library the naive way returned
  24T22545 for a "24T22548" target and would have mislabelled every candidate.
- **A density gate's resolution is family-specific and must be measured, not assumed.** L1 < 0.35 is
  decisive for the dim-11 siblings (min pairwise 0.481) and worthless for the dim-10 siblings (min
  pairwise 0.175). Check the library's internal separation *at the target's dimension* before trusting
  a gate threshold — a single global threshold is not a gate.

## Reproduce

```bash
gap -q -b -c 'TOP:=210;' scripts/mb2_multi_gdist.g > data/processed/mb2multi/raw210.txt
.venv/bin/python scripts/mb2_multi.py --pairs 24 --twists 64          # dry run, 0 gated
```
