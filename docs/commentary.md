# Commentary

Dated log of interpretive discussion — framings, debates, corrections, rejected ideas — that the
numbered tests and research log don't capture. Raw material for any future writeup. Append; don't
delete superseded interpretations. See `CLAUDE.md` → Working memory conventions.

> **Reading note (2026-10-20).** Entries that named other teams or speculated about their methods
> were removed or trimmed for publication, along with one note about a separate project. Paths such
> as `docs/auto_log.md`, `docs/research_agenda.md`, the phase plans, `data/targets/realized.csv` and
> `submissions/` refer to files that are not in this release.

## 2026-06-24 — Project framing

Kicked off the project by studying the sibling `modular_arithmetic_challenge` and mirroring its
conventions. Key realization up front: **IGP24 is a different kind of competition.** The modular
challenge was an ML problem (train a neural net to compute `a·b mod p`, submit a HuggingFace model,
"the core computation must be neural"). IGP24 is a **computational number theory search-and-verify**
problem — find integer polynomials realizing transitive degree-24 Galois groups, verify with
MAGMA/PARI, submit a `≤100 KB` text file — and **methods are explicitly unrestricted** (AI, agents,
databases, collaboration all allowed). So we keep the sibling's *operational scaffolding* (docs
layout, numbered tests, trash/archive discipline, phase plans, provenance discipline) but swap the
stack from torch/wandb to PARI/GP + GAP + LMFDB + the SAIR MAGMA API.

Two framings worth recording before the deep dive:

1. **Coverage vs. quality.** The leaderboard ranks each `(t,r)` by *smallest discriminant*, and
   hard signatures are worth more. So "realize the group at all" and "realize it with a small
   discriminant" are different games. Early coverage (database mining + cheap subfield/resolvent
   extension) is likely the fast win; discriminant minimization and the hard primitive/non-solvable
   groups are where points concentrate. Probably a portfolio, ordered by (coverage × points / cost).

2. **Verification is the scarce resource.** Degree-24 Galois-group identification is nontrivial and
   the SAIR MAGMA API is rate-limited. The architecture should push cheap *local* pre-filters
   (irreducibility, discriminant, factorization mod good primes → Frobenius cycle types, resolvent
   factorizations) as far as possible before spending an authoritative verification call, and cache
   everything. This mirrors the sibling's "budget is a design constraint" stance, but the budget
   here is API calls + CPU, not GPU wall-clock.

Decisions on package name (`igp`), repo name (`inverse_galois`), and visibility (private) taken with
the user up front. Deep-dive landscape research is the explicit next step, to run after setup.

## 2026-06-24 — first submission: pipeline validated, and "discovered ≠ open"

First real submission (two C_24 polynomials for 24T1, r=0 and r=24). Two takeaways:

1. **The whole loop works and our construction is correct.** Magma came back with `24T1, r=24` and
   `24T1, r=0` — exactly what `polsubcyclo(97/73)` should give. Construction-guaranteed groups +
   local checks (cycle-type fingerprint, r) predicted the verifier's answer perfectly. So the
   find→construct→verify→submit machinery is trustworthy.

2. **I misread the coverage signal.** I'd treated `/labels/progress` `discovered=false` as "open for a
   1.0-point win." Wrong: it only means *no participant* has it; it says nothing about the **LMFDB
   baseline**. 24T1 turns out to be a baseline group, so our submission scored 0
   (`lmfdb_baseline_not_improved`) — our large-conductor C_24 fields don't beat `D_base`. The real
   target taxonomy is: **(a) non-baseline + non-discovered → realize it = 1.0** (the prize); **(b)
   baseline pair → only 0.5, and only by beating `D_base` with exact nfdisc**; **(c) already-discovered
   → shared, fractional**. The progress feed doesn't expose baseline membership, so we need the frozen
   `lmfdb_baseline.csv` (622 pairs + `D_base`) to retarget. This reframes the campaign: chase the ~117k
   non-baseline signatures (breadth, since the score's `2^(1-k)` rewards rarity), and treat the 622
   baseline pairs as a separate discriminant-minimization sub-game.

Lesson for picking demos: "looks unclaimed" needed verification against the baseline, not just the
participant feed — exactly the kind of check the user pushed for ("be sure we're up to date"). The
fix was cheap because we validated locally + read the verifier's structured response.

## 2026-06-24 — Landscape survey round 1: what it settled, and a methodology note

Ran the deep-research harness on "an arsenal of construction algorithms" (the user's framing: Stage-1
rewards breadth, so we want a portfolio of polynomial-finding methods). Three things worth recording:

1. **The strategy is now clear at the top level.** ~99.98% of the 25,000 groups are imprimitive, and
   the *classification itself* builds them from smaller fields via blocks/wreaths — so imprimitive/
   wreath/tower constructions (M2 in `arsenal.md`) are the obvious workhorse for coverage, with
   discriminant-minimization (M5) and signature-diversification (M6) as always-on post-processors. The
   807 non-solvable groups (incl. the 5 primitive) are the hard residual / Stage-2, and at least `M_24`
   has an explicit `Q(t)`-family (Müller) to specialize. This matches the user's "arsenal" intuition.

2. **Verification is cheaper than I assumed; *construction* is the hard part.** I had framed the SAIR
   MAGMA API as a scarce, rate-limited resource to ration. Round 1 reframes it: Magma's
   degree-independent `GaloisGroup` (Fieker–Klüners) IDs a degree-24 group in *seconds*, and the real
   scoring quantity is PARI `nfdisc` (the **field** discriminant, not the polynomial discriminant —
   a correction to my first rules draft), with a documented mixed-disc fallback. So the bottleneck is
   finding low-discriminant realizations, not identifying them. (PARI `galoisinit` only handles
   weakly-supersolvable groups, so non-solvable targets do lean on Magma — but it's fast.)

3. **Methodology note on the harness.** The deep-research run is built to *verify falsifiable claims*,
   and it did that superbly for the competition's factual framing (counts, scoring, deadline) and the
   group-classification methodology — all 3-0. But the per-method "arsenal" recipes (which named group
   each method provably reaches, exact commands) are mostly *not* falsifiable one-liners, so they
   survived as sources + open questions rather than verified findings. The harness honestly flagged this
   scope mismatch. Takeaway: round 1 = verified foundation + reading list; **round 2** should be a
   targeted pass that reads the specific sources (Müller, JLY, Hulpke §3, the `C_2≀H` recipe, CFT) and
   writes concrete, tried recipes into `arsenal.md`. Also corrected/retired three refuted claims (a
   per-`r` breakdown, a `baselineR` reconstruction, a live-snapshot solve count) — we rely only on the
   frozen 286/622 baseline.

## 2026-06-26 — Item C step 1: deliberate construction generalizes via a *shared action*

Building the search engine (test 0009) showed the only routable slice (`C_12`-top `12×2`) was
saturated: the easy constructions are everyone's, so frontier value lives in constructions others
*can't* easily make. Item C is the program of building those. Step 1 generalized the C_2-kernel
constructor off its `Q(ζ₁₃)` / cyclic-`C_12` special case to **any cyclotomic top**.

The conceptual crux was **prediction alignment**. A deliberate construction is only deliberate if we
can name the group *before* paying Magma. The old path leaned on a coincidence — ordering the 12
primes by powers of a primitive root made multiplication-by-2 equal a 1-shift, so `gap.kernel_label`'s
`C_12 = 12T1` action matched the field's. For a non-cyclic top (`(Z/21)* = C₂×C₆`) there is no single
shift. The fix is to stop relying on the coincidence: compute the actual `(Z/n)*` block action once
(`cyclotomic_top_perms`) and feed the *same* permutations to both the field construction and the group
prediction (`kernel_label_perms`). Magma's 5/5 agreement — crucially on two *intermediate* `Q(ζ₂₁)`
kernels, which are not action-invariant — confirms the alignment is real, not luck.

Honest scope: this reaches only the two abelian groups of order 12 (`C_12`, `C₂×C₆`), since those are
the only `(Z/n)*` with `φ(n)=12`. So step 1's *new* yield is the `12T2` top family. The frontier-reaching
steps are (2) **general non-abelian tops** — build the degree-12 base field `F` for an arbitrary `12Tj`
(recursively, from our own generators or a known polynomial) and run the C_2 kernel over general `F`
(autos via `nfgaloisconj`, split prime + S-unit generators when `h(F)>1`), and (3) **size-`k` blocks**
(`k=3,4,6`) via `ζ_k`-Kummer, which is where the dominant `6×4`/`8×3` frontier shapes live. The reusable
piece dropped in now is `igp.kernelsolve`: the inverse map `A → w` as plain GF(2) linear algebra for an
arbitrary top, so neither (2) nor (3) is tied to the `C_12` ideal lattice any more.

## 2026-06-26 — Item B: the identifier bug was *containment*, not weak invariants

The test-0006 false positive (24T2456 read as 24T12727) looked like "the local invariants are
too coarse." Looking closer, the invariants were fine — the *comparison* was wrong. `confirm_label`
asked "observed cycle types ⊆ candidate's set," and 24T2456's cycle-type set is literally a **subset**
of 24T12727's (2456 has no 8-cycles; 12727 does). So a true-2456 polynomial trivially satisfies
12727's containment. No amount of extra cheap invariants of the *set* flavour fixes a subset relation.

The fix is to stop comparing sets and compare **distributions**. By Chebotarev the Frobenius cycle
type equidistributes over conjugacy classes, so the empirical frequencies over ~300 primes have a
likelihood under each candidate's class distribution; the impossible-type case (p_G(ct)=0) is just the
−∞ tail of the same formula, so likelihood *subsumes* containment and also separates the subset
collisions containment can't. Empirically 24T2456 beats 24T12727 by 168 nats on a real 2456 poly —
decisive. This is "resolvent-lite": it's statistical, and it provably can't separate genuinely
cycle-type-equivalent (Gassmann) groups, which would need a real k-subset resolvent. But none of our
collisions are Gassmann, so the cheap tool covers the actual cases — and doubles as an offline
pre-confirmer that cuts Magma/API load, which test 0009 identified as the true bottleneck.

Note also: our *deliberate* constructions (tests 0010–0011) predict the label exactly (11/11 vs Magma),
so for those the identifier is a backstop, not the primary path. Its real value is for search-found
candidates (G1/G2 composita) and for trusting results without burning an API call.

## 2026-06-26 — Size-4: the construction is easy, the *exact label* is the hard part

Size-4 (the dominant 6x4 frontier shape) turned out to be easy to CONSTRUCT and surprisingly
subtle to PREDICT. The construction is just two independent square roots over a Galois degree-6
base, K = F(sqrt b1, sqrt b2) — a Klein-four block, all reusing the autos machinery, no zeta_k.
Magma confirms genuine 6x4 groups immediately.

The catch: the a-priori predictor lands on the right ABSTRACT group but the wrong degree-24
permutation rep. 24T1156 and 24T1157 are isomorphic as abstract groups but distinct as transitive
S_24 groups; my hand-built action of M⋊H on (block, sign1, sign2) realizes one, the field realizes
the other. The difference is a sign cocycle / a specific choice of point stabilizer that's painful
to pin down by hand. I spent a while trying variants (tau vs tau^-1, the coset action on
w1-perp ∩ w2-perp) and they all gave the sibling, not the field's rep.

What actually resolved it was item B. The two isomorphic groups have DIFFERENT cycle-type
distributions (different permutation actions => different Frobenius patterns), so verify.identify
picks the field's exact rep from ~300 primes — 3/3 vs Magma. So the deliberate size-4 labeler is a
*pipeline*: biquad_label narrows to the abstract group, identify pins the exact 24Tt. The two
workstreams the user sequenced (C then B) ended up composing — B is what makes C's size-4 exact.

Caveat worth remembering: a Galois base of order 6 caps the group at <=384. The frontier's bigger
6x4 groups need a bigger top on 6 points (a non-Galois 6Tj base, |H|>6), which is the same
"non-Galois base / no autos" wall that also blocks the |H|>12 size-2 tops. That general-base
construction (Frobenius action on the m primes + S-units) is now clearly the single highest-leverage
next build: it unlocks big tops at every block size at once.

## 2026-06-26 — The big-top unlock: non-Galois bases, and what "deliberate" can still mean

The recurring wall across tops AND block sizes was the same: a Galois base field gives only the
REGULAR top (|H| = deg F), so everything maxed out at order-12 tops (and groups <= 49152). The
fix turned out to be almost embarrassingly simple — drop the autos. galois_c2 used nfgaloisconj
to form alpha = prod sigma_a(pi); but you don't need autos at all if you just multiply the
generators of the 12 split primes directly (idealprimedec order). That works for ANY base with
h=1 and a completely-split prime, Galois or not. So general_c2 is shorter than galois_c2 and
reaches the big tops. Over x^12-2 (top 12T28, order 48) we hit 24T18449 of order 196608 — 4x
anything a Galois base could give.

The price of dropping autos is the prediction. With autos I had a canonical regular labeling, so
kernel_label_perms predicted the exact 24Tt (11/11 over tests 0010-0011). Without them, I can't
align H's action to gp's prime ordering without the Galois closure (which is the expensive object
we're trying to avoid). BUT — the thing that's actually labeling-INDEPENDENT is the dimension of
the kernel module, hence the group ORDER: 2^dim<H.w> * |H|. That I can predict exactly and
cheaply (kernelsolve), and it matched Magma 3/3. So "deliberate" degrades gracefully: from
"predict the exact 24Tt" (Galois base) to "predict the order/structure, then let identify pin the
exact rep" (non-Galois base). Item B (the identifier) is again what makes the non-exact case
usable — the same pattern as size-4. The two workstreams keep composing.

Conceptually the matrix is now spanned: tops (regular order-12 + big non-Galois) x block sizes
(2,3,4,6) x kernels (any module). What's left is breadth (sweep many base fields to hit specific
frontier 12Tj/8Tj/6Tj), dropping h(F)=1 via S-units, and — if we want full a-priori exactness for
big tops — building the Galois closure once per base to get the alignment.

## 2026-06-26 — Non-solvable degree-24: the lever is the base field, built by a resolvent

The 807 non-solvable groups were filed as "the hard residual." But the big-top unlock made most
of them fall out for free: general_c2 doesn't care whether the top is solvable, so a degree-12
base with a non-solvable top gives a non-solvable degree-24 group. No new engine — the entire
lever is "get a degree-12 field with the target (non-solvable) top."

The obstacle was building that base. The textbook route — splitting field of an A_5 quintic
(degree 60), then the degree-12 subfield — was too heavy here (nfsplitting on degree 60 ran for
many minutes and the attempts died). The fix was to stop building the splitting field at all and
build the degree-12 field as a RESOLVENT: pick an invariant of the 5 quintic roots whose
A_5-stabilizer is exactly the C_5 (theta = sum r_{s(i)} r_{s(i+1)}^2 — cyclic but not
reflection-symmetric), evaluate it over the 12 cosets, and the 12 values are the roots of the
degree-12 A_5 field. Numerically: roots to 250 digits, product over 12 cosets, round to integers
(error ~1e-240). Cheap, and it sidesteps the whole degree-60 object.

Two debugging notes worth keeping. (1) h(F)=5 here, so the old "product of per-prime generators"
breaks — but forming the product IDEAL and taking its generator works whenever the product is
principal (and the group label only depends on the valuation pattern, not the unit, so this is
strictly more general). A pattern is realizable iff sum of prime-classes = 0 in Cl(F); with h=5
plenty of subsets qualify. (2) `I` is a reserved name in gp (sqrt(-1)) — `I = idealmul(...)`
silently no-ops and you get nonsense. Renamed to Jd.

Caveat for the record: these are non-solvable IMPRIMITIVE groups (12x2 with a non-solvable top).
The genuinely hard primitive degree-24 groups (M_24, PSL(2,23) on the 24 points of P^1(F_23))
have NO block system, so the kernel-over-base trick can't touch them — they remain a separate
problem needing rigidity or explicit Q(t)-families. But "non-solvable" as a blanket category is
no longer a wall.

## 2026-06-26 — M24: primitive groups are a different regime (and our engine doesn't apply)

Realizing M24 closed the last category — but in a way that underlines what our construction
toolkit is and isn't. Everything in tests 0010-0016 builds an imprimitive group: a kernel over a
base field, exploiting a block system. The 5 primitive degree-24 groups have NO block system by
definition, so none of that machinery can touch them. They are realized, if at all, by explicit
one-parameter families from the literature plus a specialization argument (Hilbert irreducibility).

For M24 the family is Müller's (arXiv:1204.1328): F_s(X) = (t - A_s)^2 + (1+X^2) B_s^2, group M24
over Q(t) for rational s != 1. The "method" on our side is operational, not mathematical: fetch
the published family (his m24.sage), pick a rational (s,t) off the branch locus, monicize, and
polredbest down to a submittable polynomial. s=0,t=0 worked first try; Magma said 24T24680. The
only friction was the 2^44 leading coefficient: the honest monic model has ~300-digit coefficients,
and polredbest (the one genuinely slow step) brings them to ~20 digits for the same field. Worth
remembering: polredbest reduces the POLYNOMIAL, not the field discriminant — M24 fields are wildly
ramified (disc ~1e180), so the score comes from M24's rarity, not from a small disc.

So the realistic picture of the primitive five: A24/S24 are free (a random degree-24 polynomial is
S24; force a square discriminant for A24). M24 is done. PSL(2,23) and PGL(2,23) act on P^1(F_23)
and should fall out of the explicit-Belyi-map literature (arXiv:1703.02848 and similar) by the same
fetch-and-specialize recipe. None of these is "our" method — they're operationalizing other
people's families — but they complete the coverage map, and the recipe is now a known quantity.

## 2026-06-27 — Routing campaign: 6 sole realizers, and the non-Galois alignment trap

The routing campaign (invert constructors -> {label:recipe}, intersect the live undiscovered
set, build only the matches) is the right shape and it works: 6 Magma-verified sole realizers
(24T3039/5503/1627/5504 from cyclic kernels; 24T7825/7871 from non-cyclic A_4 kernels via the
multi-prime extension). All were teamCount=0 when built, all scoreable -> ~1.0 each. That's the
first time we've scored on groups nobody else has.

Two honest limits surfaced. First, YIELD PER TOP IS LOW. Even the "obvious" tops are mostly
saturated (e.g. 51/55 size-2 Galois labels already taken); each top contributes only ~1-4 sole
realizers. The binding constraint is the number of exactly-targetable tops, which is just the 4
Galois order-12 groups we have bases for. Scaling means a base LIBRARY, not cleverer kernels.

Second, a real trap: NON-GALOIS A-PRIORI LABELING IS NOT RELIABLE. I'd verified that x^12-2's
affine action (k->b*k+a on Z/12) gave exact labels for the three kernels of test 0015, and
over-generalized: I added 12T28 to the campaign as if exact. It mis-predicted — a kernel routed
as the undiscovered 24T10361 actually constructed 24T18449 (the full, contested kernel). The
affine action coincides with gp's prime ordering for some kernels but not all; only a true
prime<->block alignment (via the Galois closure) or post-construction identify makes non-Galois
targeting trustworthy. Reverted 12T28 from the campaign; the 6 sole realizers are all Galois.
Lesson logged: 3/3 on a spot-check is not a proof of alignment.

## 2026-06-27 (late) — the remaining threads: one win, one deferral, two deep sub-projects

Pushed on all four remaining threads; the honest split:

- **#4 disc-min — WIN, made systematic.** Re-realizing a beatable group over an LMFDB
  minimal-disc base reliably shrinks the field disc (24T2595: 37->34 digits over LMFDB's
  11-digit D_6 field vs our compositum). `produce-discmin` does this for all four order-12
  Galois tops; the engine keeps the min disc per (t,r). The further knob is the GA over split
  prime + kernel weight (the residual 34->26 gap).

- **#5 A_24 — deferred (needs a parametric family).** Brute-searching trinomials for a square
  discriminant is hopeless (disc ~33 digits => square ~1/1e16). The A_5 literature shows the
  way: a PARAMETRIZED trinomial (T^5+5(5a^2-1)T+-4(5a^2-1)) forces a square disc. The n=24
  analog — solving 24^24 b^23 - 23^23 a^24 = square parametrically — is a real Diophantine
  construction, not a search. Scoped, not done. (4/5 primitive stands.)

- **#2 resolvent identifier — confirmed deep.** The 2-subset additive resolvent DEGENERATES for
  our groups universally, not just 24T203: D_6 gave sum 265 vs the true 276 (sum-collisions
  among r_i+r_j). The GROUP side (gap.subset2_orbits) is exact and cheap; the POLY side needs
  Tschirnhaus-for-separability + p-adic precision (PARI float overflows ~300-400 digits) — the
  Fieker-Klüners core, a multi-session build. Marginal value is low (no Gassmann blocker has
  appeared; Chebotarev identify is 5/5).

- **#3 CFT — collapses into #4 for our case.** For C_2-kernels the "minimal conductor" is just
  the smallest split prime, which we already use; combined with LMFDB minimal bases (#4) that IS
  the principled disc-min. The distinctive CFT (ray class fields for abelian targets) is
  low-value (abelian groups are baseline/common), and bnrclassfield is too heavy here. Deferred.

Takeaway: the two deep CAS sub-projects (#2 p-adic resolvent, #3 robust CFT) are real but
low-priority given no blocker and #4 covering disc-min; the concrete remaining win is the
disc-min GA and an explicit A_24 family.

## 2026-06-28 — Self-hosting the verifier (OSCAR spike, test 0026)

- **We CAN identify degree-24 groups locally — and that's exactly why Magma is the verifier.**
  OSCAR (Fieker–Klüners, the open-source sibling of Magma's algorithm) reproduced our SAIR labels
  perfectly, but on *mid-lattice* groups (not just giants) it took **35–74 min** and one **OOM'd
  past 16GB**. Magma's "seconds" is decades of optimization we can't cheaply replicate. The spike's
  real value was negative knowledge: it killed the "self-host the verifier" idea on the merits.

- **Generative search was the prize, and it's off the table.** The pitch was: identify random/sweep
  polys locally, submit only confirmed hits, decouple from the API. But an unknown-group poly can
  land on a 70-min / >16GB case, so triage throughput collapses. Local ID only helps where we
  *already* know the group (our constructive pipeline) — i.e. confirmation, not discovery.

- **Option C taught a precise lesson about the descent.** Seeding the known group *order* as a
  filter (`order(x) >= o_known`) prunes resolvents at/below the answer level — a clean, alignment-free
  hook into the public `descent`. But it only bought −9–28% speed, because the cost lives in the
  descent *path above* the answer, which the seed can't touch. Its surprise payoff was **memory**:
  the pruning rescued 24T7871 from OOM to a 16-min run inside 16GB. So C is a memory lever, not a
  speed lever.

- **Net for strategy:** keep OSCAR as an occasional local cross-check, not a daemon stage — the
  SAIR budget (now 500/day) already covers verification, and the easy groups C could confirm cheaply
  are the ones SAIR verifies cheaply anyway. The honest correction to the earlier "local verifier
  unlocks generative search" framing is logged here.

## 2026-06-28 — The plateau was supply, and the bandit told us twice (test 0027)

- **The throughput debate resolved itself empirically.** We raised max_posts_day 60→500 and
  build_batch 4→50; actual posts were 68 then 1/day. So posting was never the bottleneck — the real
  multiplier was build_batch (fuller POSTs), and the true ceiling is producer SUPPLY. The cap change
  was harmless but beside the point. Lesson: instrument before tuning; the "no cap" instinct was
  right that the cap wasn't doing much, but for the wrong reason.

- **The bandit was diagnostic, not just prescriptive.** Two signals we initially read as noise were
  actually the plan: (a) size3's #1 rank was *mostly the exploration bonus* (n=4) — it was saying
  "this shape is under-sampled, feed it," not "this shape is proven best." (b) Ranking the trinomial
  sweep LAST while that sweep produced 9/14 of our sole realizers exposed a reward bug, not a
  producer to cut. We acted on both: widened 8×3 supply (3 ζ-bases + a compositum generaliser) and
  added a sole-discovery-share term so rate-efficiency stops starving the rare-find engine.

- **"Reliable" vs "finds rare groups" is the core tension.** Targeted towers hit ~100% scoreable
  but 0 sole; the broad trinomial sweep is 61% scoreable but is where ALL our sole realizers live.
  Per-sample efficiency will always rank the sweep low — yet sole realizers (teamCount==0) are the
  top of the scoring formula. Crediting *share of total soles* (undiluted by n) is the cleanest
  realignment; it's tunable (sole_share_weight) if it over- or under-corrects.

- **Compositum as a diversity cheat code.** (deg-8)×C₃ via polcompositum needs no kernel/alignment
  machinery — it's a `ready` poly Magma labels — so every diverse degree-8 field we can sweep becomes
  a new 8×3 group for free. The same trick extends to other (m,k) shapes if 8×3 pays off.

## 2026-06-28 — Juicing the generator: the verifier was never the bottleneck (test 0028)

- **The big reframe: SAIR Magma is fast, supply was the whole story.** We'd inferred ~330
  verifications/day — but that was a *supply-limited* artifact (the queue was dry most of the day).
  Feeding it 1200 candidates, it drained them well within the session (verified ~668→1868). So the
  verifier has large headroom; every time we thought we were throttled, we were just starving it.
  This flips the strategy: **flood hard, continuously.** The cursor-based quadrinomial generator is
  the continuous-supply primitive; we can raise the queue target freely.

- **But a flood is mostly S₂₄ — the filter is the other half of the win.** ~¾ of sparse degree-24
  polys are generic S₂₄ (negligible score). Submitting them wastes the verifier and spams a shared
  free-tier API. The Jordan + Mathieu-order argument gives a *rigorous* skip: a 13/17/19-cycle ⇒
  primitive (coprime to block sizes) and non-Mathieu (those primes don't divide |M₂₄|/|PSL|/|PGL|) ⇒
  A₂₄ or S₂₄; square disc keeps the rare A₂₄. Zero false positives by construction. Live, it dropped
  588/800. So "juice the generator" is really two moves: generate more AND submit less junk.

- **The payoff was immediate and large:** scoreable signatures 613→1067 in one session — past the
  LMFDB baseline (622) to ~1.7×. The broad sweep also coughed up 3 new sole realizers, reaffirming
  that rare groups come from breadth, not from the targeted towers. The genuine frontier beyond
  baseline is finally moving.

- **Open question this raises:** if the verifier is cheap, is *disc-minimisation* now the higher
  marginal lever (improving score on the 1000+ sigs we already cover) versus more breadth? Both are
  unblocked now; worth measuring which converts to more points before the deadline.

## 2026-06-28 — Measuring before cranking: the "1000+ sigs" were ~6x double-counted (test 0029)

- **Self-correction: I'd been quoting row counts as signature coverage.** The dashboard's "scoreable"
  summed realized.csv ROWS; with ~6 polys per (t,r) that overcounted ~6x. Real distinct scoreable
  signatures: **255**, not 1000+. So my "past baseline 1.7x" was wrong — we're at 255 vs the 622
  baseline on *signatures* (though 312 vs 286 on *groups*, and 244 sigs are beyond baseline). Fixed
  the dashboard to count distinct (t,r). Lesson: define the metric as what scores before celebrating.

- **This is exactly why the lever-3 instinct (measure before cranking breadth) paid off.** Had I just
  "gone ahead" and cranked the quad buffer + added pentanomials, I'd have poured effort into
  duplicate rows. The audit shows the sparse flood is now ~6x re-covering held signatures —
  diminishing returns on *distinct* coverage.

- **Disc-min is the fresher lever, with a catch.** 166/193 covered sigs have a team beating our disc
  (~19% credit leaking) — real headroom. BUT disc-min needs small-disc *constructions*: sparse polys
  give large field disc, and polredabs only shrinks coefficients, not the field. So the play is
  re-realising the behind-sigs over LMFDB minimal-disc bases (the discmin family), where we have a
  tower — not more flooding.

- **And the sole edge is perishable.** ~15 → 5 sole as the leaderboard refreshed; competitors are
  realising the same groups. Breadth still matters, but toward *new* signatures (more `r` per group,
  diverse composita), not re-hitting held ones. Net: pivot from "more sparse volume" to
  "disc-min + diverse new sigs."

## 2026-06-28 — Phase 1, a daily cap, and a scoring recalibration (breadth ≫ disc-min)

- **Entered Phase 1 (user-confirmed).** The "is everything documented?" audit + the transition forced
  two corrections, both honest walk-backs of things I'd said earlier this session.

- **The real ceiling is 100 POSTs/day/team, not the verifier.** The daemon *crashed* into a 429
  `TEAM_DAILY_LIMIT`. So "the verifier is unlimited, flood hard" (test 0028) was wrong: the verifier
  is fast, but the submission gate is hard at 100/day. Fixed the daemon to survive it (cap 98 + requeue
  + idle till next UTC day). The game is **value per POST**.

- **The confirmed `2^(1-k)` formula reorders the levers: breadth ≫ disc-min.** A first/undiscovered
  pair (`teamCount==0`) ≈ 1.0; a shared pair caps at ≤0.5 and disc-min only nudges within that. So my
  mid-session disc-min emphasis (0029 → `discmin2`) was **over-weighted** — disc-min is a *secondary*
  post-processor; the dominant Phase-1 lever is covering **undiscovered** pairs fast (before
  competitors claim them). `discmin2` still earns its keep on shared pairs we're credited on.

- **"Could be old?" — the user was right about the numbers.** The 2026-06-24 plan's real estate
  (~47k discovered / ~117k undiscovered) had drifted to **~64k / ~101k** (competitors claiming
  ~4k pairs/day). I verified the *formula* is confirmed (kept) but refreshed the *numbers*. Lesson:
  re-pull leaderboard state before reasoning from a 4-day-old snapshot — the race moves.

- **Net Phase-1 priority:** target `teamCount==0` signatures (the 1.0 wins), spend the 100 POSTs/day on
  the rarest reachable pairs; disc-min + the non-solvable residual are secondary.

## 2026-06-28 — Official package: we hold zero 1.0s; the target is the 299 sig-fill pairs

- The organizers released the canonical package (Tao's post); vendored it. `competition.yaml`
  **confirmed** our reverse-engineered scoring (`2^(1-k)`, nfdisc→mixed-disc, 100/day) — a nice
  validation of the earlier work, and it finally gave us `D_base` + the authoritative `validR`.

- **The honest scoreboard is sobering: we hold ZERO true 1.0 pairs.** Our 263 scoreable = 258
  non-baseline (all SHARED, teamCount≥1 ⇒ ≤0.5 each) + 5 baseline-unlocks (0.5). The "5 sole
  realizers" we'd been tracking are BASELINE pairs we haven't beaten — worth **0**. The bug:
  `teamCount==0` conflated "no participant has it" with "non-baseline." Only non-baseline +
  teamCount==0 is a real ~1.0.

- **But the opportunity is now concrete: 299 sig-fill 1.0s** — groups we ALREADY realize, missing an
  undiscovered valid `r` — deterministic first-claim 1.0s (plus 99,542 open 1.0 in total). So the plan
  crystallizes: convert the 299 (sig-fill toward non-baseline `teamCount==0` missing `r`), then push
  breadth into the 99k. The ranker now rewards true 1.0s and the builder caps baseline, so the
  machinery points the right way.

- **Lesson (now a CLAUDE.md rule):** get the authoritative data before optimizing — we'd been ranking
  and "celebrating sole" against a proxy; the official baseline corrected the whole scoreboard.

## 2026-06-28 — comprehensive review: value per POST, distinct signatures, and data hygiene

- **The largest pipeline leak is POST packing.** The daemon hit the 100 POST/day cap while sending only ~24.9 polys/POST on 2026-06-28, because it claims a fixed batch before S24 filtering and submits the survivors. Under a POST cap, the daemon should accumulate post-filter candidates up to the 100-poly payload limit before spending a POST.

- **The ranker still thinks in rows, while the score thinks in distinct `(t,r)`.** Quad has many scoreable rows but a huge duplicate factor; the sole-reward code also checks `(t,0)` instead of the realized row's actual `r`. The next ranking target is marginal signature value: new `(t,r)`, actual `teamCount==0`, and disc improvement.

- **Signature fill is the clean math lever.** Among groups we already reach, hundreds of allowed missing signatures are still `teamCount==0`; this is more directed than more sparse-polynomial flood. Full writeup: `docs/project_review_2026-06-28.md`.

## 2026-06-29 — first TRUE 1.0s: targeted construction at open signatures

- **We hold 19 true 1.0 signatures (was 0).** The honest scoreboard (test 0032) made the gap precise:
  breadth lands on already-discovered (shared, ≤0.5) pairs; the only pairs worth ~1.0 we can reach are
  open ones (valid, non-baseline, `teamCount==0`). The blocker was that we couldn't know a candidate's
  `(t,r)` until we paid a Magma submission — so we sprayed and hit whatever was nearby.

- **Two local computations removed the blocker.** Over a *Galois* degree-12 base the C_2-kernel group
  is a deterministic function of the kernel pattern (`kernel_label`), and `polsturm` gives the exact
  real-root count. So both coordinates of `(t,r)` are known *before* submitting. `produce_sigfill_targeted`
  builds the open-target set, predicts each pattern's group, computes local `r`, and enqueues only the
  ones that hit an open 1.0. Result: 19 candidates, and Magma confirmed **all 19 at exactly the
  predicted label and `r`** — 19/19, no misses.

- **The lesson is "predict, don't spray."** The prediction is exact, not statistical, so there are no
  false positives — under a 100-POST/day cap that turns every submission into a deliberate 1.0 attempt
  instead of a lottery ticket. This is the first mechanism in the project that *aims* at score rather
  than accumulating coverage and hoping some of it is rare.

- **Honest scope.** 19 came from 10 bases; the method only reaches C_2-extensions of order-12 groups,
  and there are still ~89k open 1.0s. The clear next lever is the same predict-group + local-`r` gate
  wrapped around the other tower families — not more sparse-polynomial flood.

## 2026-06-29 — expanding the targeted gate: where the open 1.0s actually live

- **The gate generalizes; the scarce part is the per-family group predictor.** Extending test 0033 to
  all prediction-capable families confirmed the architecture: local `r` (`polsturm`) and the
  open-target set are family-agnostic, so a new family only needs a local label predictor over a
  Galois base. Added two — multi-generator C₂ kernels (`c2multi`, non-cyclic) and biquadratic V₄
  (`biq`, 4×6) — sharing one gate with the original single-generator `c2`.

- **Yield was lopsided, and that is the interesting result.** `c2multi` found 24T7825 (r12, r16) — a
  group whose kernel is non-cyclic, so single-generator `c2` literally cannot produce it; this is the
  payoff of the richer kernel lattice. But `biq` found **zero** open targets: the V₄-block groups
  reachable over deg-6 bases all sit in the low-T region (24T155–1178) and are already claimed.

- **So open 1.0s are concentrated in the size-2-block (deg-12 base) region.** Where a construction
  family lands in the 24T numbering determines its headroom. The high-T groups (24T5xxx/10xxx) reached
  by 12-block towers are under-explored; the 6-block (size-4) and lower-block regions are saturated.
  This sharpens strategy: invest in deg-12-base families and their kernel structure, not deg-6.

- **The ceiling on per-family predictors points to the general fix.** The compositum families
  (`g6x4`, `size4`, `c8x3`, `size3`) and sparse fillers have no local predictor — each would need its
  own `biquadratic_label`-style model, or we wire a **family-agnostic local degree-24 Galois-group
  identifier** (the OSCAR spike, test 0026: correct but slow). Slow is acceptable for a 6h-throttled
  targeted producer even though it was too slow for the daemon hot path. That is the clean path to
  targeting open 1.0s from *any* construction — the decision is whether the OSCAR latency is worth it.

## 2026-06-29 — limits raised 10x; the bottleneck is disc factorization, not Galois

- **The 100/day cap that shaped our whole pipeline is gone.** Sutherland (Zulip) raised limits to
  **1000 polynomials/submission and 1000 submissions/day** (from 100/100). We built the daemon around
  the 100-POST cap — packing, `_max_posts_today`, bandit triage for scarce POSTs. The scarce resource
  is no longer the API; it's how many *good* candidates our producers make. Retuned the daemon
  (`submit_target=1000`, `max_posts_day=500`) but kept the dedup + bandit ranking, because the
  organizers explicitly asked contestants not to "submit a million random polynomials" — our deduped,
  coverage-directed, targeted-first submission stream is exactly the non-abusive use, and that's the
  real safeguard, not the cap. Did NOT crank to the full 1000/day: 500 is generous headroom over our
  actual output and signals restraint.

- **The strategic reframe:** with throughput unblocked, the targeted-discovery work (tests 0033/0034)
  is now even more central — we can submit many open-1.0 candidates per day rather than rationing
  POSTs between targeted and breadth. Both flow now.

- **The verifier bottleneck is discriminant factorization, not the Galois group** (Sutherland). It
  trial-divides to 10^6 then spends a bounded 60 s on the rest. So a poly whose discriminant carries a
  large prime factor (> 10^6) can time out → the mixed-disc fallback, which *cannot unlock baseline*.
  This elevates disc **smoothness/factorability** from a non-issue to a real quality signal: between
  two polys for the same `(t,r)`, prefer the one whose discriminant factors easily. A Zulip post notes the
  Buchmann–Lenstra maximal-order computation is cheap when ramified primes are known — relevant if we
  ever want a fast *local* field-disc check, and for a Phase-2 proof requirement.

- **Comment-field (`#`) ramified-prime hints are advisory only** this phase (untrusted LLM
  submissions; a prime list without a completeness proof can't be trusted) — so not worth wiring into
  submissions now, but flagged for Phase 2.

## 2026-06-29 — "do the full 1k, just don't submit junk"

- Lifted the daily cap to the true 1000 but added a value gate, because a 10× capacity raise is an
  invitation to flood only if you let it. The data made "junk" concrete: `quad` is 9343 attempts for
  108 distinct sigs (0.01 sig/row) — exactly the random enumeration Sutherland warned against.
- The subtle bug: our per-row priority *blended* the surrogate additively, so a 0.03-value producer's
  rows hit ~1.15 and outranked real producers — the daemon would have submitted junk first. Made the
  surrogate **multiplicative** on producer weight (orders within, doesn't override). Junk now ranks
  last and is denylisted at submission + dropped from auto-production.
- Bonus find while verifying: 1867 rows stuck in `building` — daemon stops for commits had been
  orphaning claims (lost work). Added a startup `requeue_building`. The general lesson: any
  "in-progress" status needs a recovery sweep or restarts leak it.

## 2026-06-29 — the split prime is a free dial on the signature

- Doubled held 1.0s (19 → 41) with no new construction family — just by sweeping the split prime.
  The realization: for a C₂-tower F(√α), the group is fixed by (top, kernel) but the real-root count
  r = 2·#{σ real : σ(α) > 0}, and α's sign pattern depends on which prime above q generates it. So
  one kernel reaches r ∈ {8,12,16} across primes (verified on 24T2595). We'd been taking one prime →
  one r → one signature per group, leaving the other open r unclaimed.
- This reframes targeted discovery: each reachable group isn't one 1.0, it's *all its open (t,r)*, and
  the prime is the cheap way to enumerate them. The same idea will apply as we add families — always
  ask what the free axes are (prime, base, kernel) before adding machinery.
- Process note: the per-run "enqueued N" number looked flat (22 vs 21) and almost masked the win;
  the truth was in cumulative distinct verified (t,r) (19 → 40) and TRUE-1.0-held (19 → 41). Score the
  metric that counts, not the per-run proxy — same lesson as the rows-vs-sigs bug, resurfacing.

## 2026-06-29 — candidate-gen sweep results + the M24 lesson (famous != open)

Big push on "expand candidate generation in all the ways, then research." What worked, and a sharp
lesson.

- **Multi-prime sweep was the standout** (test 0036): the split prime is a free dial on the C_2-tower
  real-root count, so sweeping it harvests every open (t,r) per reachable group. Doubled targeted
  TRUE 1.0s (19->41). Also applied to harvest producers.
- **gen12 (general_c2 over diverse non-Galois deg-12 LMFDB bases)** drove distinct groups 390->457+
  (still climbing) — but as BREADTH (new groups at shared/baseline pairs), not 1.0s. The daemon is
  supply-bound (verification keeps up), and I parallelized construction (10-thread pool).

- **The M24 miss — a real lesson.** Research found the non-solvable gap (we realize ~0 of the hard
  set; towers can't reach primitive groups since a completely-split prime has density 1/|H|) and the
  Malle-Matzat M24/Q(t) family. I built + submitted it expecting a sole-realizer 1.0 ("if sole, score
  1.0"). WRONG: M24 (24T24680,0) has **teamCount=11** — the textbook primitive group everyone
  realizes via the SAME published family. ~0.001 score, and we already held it. I'd even set it to
  top priority; skipped the 121 queued specializations.
  - **Reframe:** the teamCount==0 1.0s live in OBSCURE groups (no published family -> we're first),
    which is exactly what the TARGETED GATE (tsig: predict + gate to teamCount==0) hits. Famous
    groups are contested precisely because they're famous. So the score frontier is *extending the
    targeted gate to more obscure groups*, NOT explicit families for named primitives. Harvest
    (gen12) is for the groups-realized headline, not score.
  - **Process miss:** I didn't check realized.csv (M24 was already there, source "mueller") nor
    teamCount before building/prioritizing. Now a quality rule.

## 2026-06-29 — non-Galois predictor: validated, but the groups are contested (negative result)

Researched the high-ceiling lever (gate gen12 to teamCount==0 by predicting its 24T label).
- **The model is right and the |S|=1 case is cleanly predictable.** G = M⋊H with H=12Tj (LMFDB's
  galois_label); kernel_label(w, top_t=j) predicts the label. Single-prime kernels are alignment-free
  (all singletons H-equivalent) and validated exactly against Magma (24T21859 for base 12T139).
- **But it doesn't matter, because gen12's groups are contested.** 24T21859 has teamCount=18; all 64
  distinct gen12 (t,r) are shared, none open. general_c2-over-deg-12 is what everyone does — the
  "obvious" construction is the contested one, exactly the M24 lesson at family scale. A predictor
  that gates a contested family toward teamCount==0 finds nothing.
- **So I'm NOT building the |S|≥2 alignment solver** (it's the hard part — essentially the Galois
  action on the q-adic roots — and the payoff is ~0 1.0s). Validated-method-pointed-at-contested-
  groups is a trap I've now hit twice; the discipline is to check teamCount FIRST.
- **The real shape of the problem:** open 1.0s are specific (group, r) gaps, not whole construction
  families — whole families get contested. tsig finds them by enumerate-and-gate over Galois tops
  (41 held, a narrow niche). The marginal 1.0s are thin and hard-won; the clearer remaining points
  are disc-min on our low-teamCount held pairs (k=1,2), where shrinking disc approaches a full point.

## 2026-06-29 — disc-min lever: sized it, mostly automatic + alignment-limited

Took the disc-min lever. Sizing: ~4.85 points theoretical (reach the leaderboard min on all 493
headroom pairs), concentrated in k=2 (2.0) and k=3 (1.4); k>=5 is negligible (2^(1-k) tiny).
- **The cheap angles are already covered:** our discs are EXACT (local nfdisc == stored, disc_source
  exact_nfdisc -> no mixed-disc fallback to fix with polredabs), producers polredbest, and
  build_submission already picks min field-disc per (t,r) ranked by 2^(1-k)*log(D0)/log(D).
- **The headroom is real (larger fields) but mostly UNcapturable by us.** The high-gain pairs are
  biquadratic 6x4 over NON-Galois deg-6 bases where we already use minimal bases + the smallest
  split prime; doing better needs a better base with the pattern re-aligned to the same group -- the
  same alignment wall the predictor hit (test 0038).
- **The one alignment-free sliver, taken:** more (w1,w2) PATTERNS over the same base give
  different-disc fields for the same group, so a wider sweep (_BIQ_PAIRS 3-4 -> 8) yields more disc
  samples per (t,r) and the builder keeps the smaller min. Magma labels; no prediction. Modest gain,
  accrues automatically as the harvest runs.
- **Meta:** two proposed levers (non-Galois predictor, targeted disc-min) both bottom out at the same
  alignment wall / "the obvious construction is contested" ceiling. The system is near its
  construction-method ceiling; further 1.0/disc gains are thin and accrue automatically from the
  running harvest + builder.

## 2026-06-30 — morning status: a metric scare that was really a metric bug

The scoreboard read TRUE 1.0 held 41 -> 0 overnight. Heart-stopping, but it was the metric, not the
results: `teamCount==0` means NOBODY is credited (that's the 87k OPEN-target pool), not "we're sole."
A pair sole to us shows `teamCount==1` (verified: all 44 such pairs have minDisc==our disc). The old
"held & teamCount==0" metric was reading the submission LAG -- freshly submitted pairs sit at
teamCount==0 until the leaderboard counts us, then flip to 1; the overnight progress refresh did
exactly that. Fixed analyze_coverage + the bandit (sole = teamCount<=1) and added an ESTIMATED TOTAL
SCORE (lag-robust). Real status: **44 sole 1.0s, ~73 est. points, 621 groups, 734 scoreable sigs** --
overnight harvest added ~164 groups / ~210 sigs. The lesson is the same one in a new guise: know what
a leaderboard field actually counts before you headline a metric on it.

Also: the daemon has drained its queue (structured producers tapped; quad/pent/tri denylisted) and
sits idle between 30-min ticks -- expected steady state now that we're near the construction-method
ceiling. Coverage now accrues slowly from tick refills + the race.

## 2026-06-30 — first igp-research dive (hands-off, one subagent): "beyond M24"

The new research loop fired its first dive (topic: explicit Q(t) realizations of degree-24 groups
beyond M24). Outcome: the literature is a near-dead-end for NEW degree-24 families -- Klüners-Malle DB
stops at degree 23, Malle's tables are deg 7-14, König's Hurwitz polys are deg 21/22/31; the only
directly-usable new construction is Roberts' M12.2 family (arXiv:1404.0429 = 24T18441). The real
takeaway is methodological: **degree-24 coset actions of small simple groups via PARI resolvents**
(complementary to our abelian-kernel towers) and **non-split central-extension embedding problems**
(2.A5, 2.M12) -- both pushed onto the research agenda as method dives.

Verifying the subagent vs progress.json caught 3 errors (it had 24T202 r0 as open when it's k=1; said
we hold PSL/PGL(2,23) when those are k=0 OPEN and unheld). The verified OPEN, actionable targets:
M24 (24T24680) r=8/24 -- via the Müller family we ALREADY run (it only gives r=0 now); M12.2 r=8/24
via Roberts; 24T201 r24 via coset action. The "trust but verify" step paid for itself; the dive's
value was as much in correcting our coverage assumptions as in the new leads. The agenda refilled
itself (popped 1, pushed 2) -- the loop works end-to-end.

## 2026-06-30 — igp-research dive #2 (rigidity): the primitive frontier is open

The rigidity dive's framing is sharp: only 5 deg-24 groups are primitive; rigidity/Belyi natively
output groups in their PRIMITIVE action, so its deg-24 products are exactly those famous primitives,
not the ~802 obscure imprimitive towers. So rigidity is NOT a breadth lever -- BUT verifying vs
progress.json turned up a real prize: **PGL(2,23) (24T10255) and PSL(2,23) (24T7817) are OPEN (k=0)
and we hold neither**, and Bosman has an explicit degree-24 PGL(2,23) polynomial (ramified only at
23, from the level-1 weight-22 cusp form). Two primitive groups, open, with a published construction
-> task #12 (pull the coeffs, verify, submit). The dive also seeded two agenda follow-ups: a GAP
rigid-triple screen of the 807 non-solvable (the obscure-group shortlist) and quantifying the
signature-engine yield of the M12.2/M24 families we already own. The hands-off web access worked this
time (broad WebFetch) -- no approval prompts.

## 2026-07-01 — the silent [:100] submission drop (found via two missing literature polys)

Chasing why Roberts f_C2 (24T18441) and Bosman P16 (24T10255 r2) sat "submitted" for 20h with no
server record turned up a severity-1 pipeline leak, not a SAIR problem: when the organizers raised
the limits 10x (2026-06-29, 1000 polys/POST) and searchd was retuned to pack 1000 per cycle,
`engine.submit` kept its old `uniq = uniq[:100]` truncation -- and searchd marked the ENTIRE built
batch (~650-850 rows/cycle) as "submitted" whenever the POST succeeded. Net effect since the retune:
~85% of built candidates silently discarded (server holds 684 submissions x 100 = ~68k polys vs
~170k queue rows marked submitted), never pending-tracked, never retried, invisible in every counter
we watched (built= and sub= counted marks, not sends). The two priority-100 literature polys were
mid-batch in a mid-cycle claim and fell past the first-100 cutoff -- their loss is what exposed it.

Diagnosis chain worth keeping: queue said submitted; pending_submissions.json was EMPTY (so collect
had reconciled everything it knew about); the polys were in neither the verify-cache nor
realized.csv under their coeff lines; a full label-based scan of all 684 server submissions found
NO t=18441 and no (10255, r=2) anywhere (label search is normalization-independent, so this was
decisive: never received). The 675-marked vs 100-received per-cycle mismatch in the journal then
pointed straight at the truncation.

Fix (deployed after ruff+pytest, daemon restarted): `engine.submit_batch` returns (sid, posted,
known) so the caller knows exactly which lines were sent vs already-known vs over-cap; searchd marks
only `posted` rows submitted, `dup`s the known, and REQUEUES anything unsent; cap raised to the
official 1000/POST (competition_rules.md L100 "1-1000 items"); max_pending raised 40 -> 2000 lines so
full-size POSTs aren't self-blocked (40 was tuned for 100-line POSTs). The two lit rows were reset to
queued at priority 100. Regression test: tests/test_engine.py (over-cap lines must be in NEITHER
returned set -> callers requeue).

Lessons, in the house style: (1) when an external limit changes, grep for EVERY hardcoded echo of the
old limit -- the retune touched searchd but not engine, and the seam between them had no contract
about what "submitted" meant; (2) a status counter that counts MARKS is not a delivery metric --
sub=854 looked healthy while 754 rows evaporated; cross-check against the server's own ledger
(my_submissions is the ground truth); (3) the failure was invisible precisely because volume kept
climbing -- the queue refilled and verified counts grew, so nothing LOOKED broken; the tell was two
specific high-value polys failing to land, which is an argument for occasionally tracing single
items end-to-end rather than only watching aggregates.

## 2026-07-06 — clean no on gen12-sole defense (measured, not assumed)

Priced the proposed defense thread with atlas data: median P(re-hit a sole's group from a
fresh base) = 0.02 (best 0.19, none >=0.2), so one defended pair costs ~200-400 verified
submissions for ~+0.05-0.1 pts — roughly 100x worse verify-budget-to-points than engine
builds (2157: ~150 submissions -> ~4 durable pts). Sharing is unstoppable (defense only
improves our logD term), and erosion losses shrink geometrically (k=2 pays half, k=3 a
quarter). User decision: CLEAN NO — no defense thread, not even the micro-tier; commodity
soles depreciate while all verify budget goes to engine claims. Defense stays: multi-model
on engine pairs only.

## 2026-07-12 — Abelian-kernel construction: the C2→C_n generalization reaches fresh strata

- **`general_c2` was one block (C2) of a whole family.** The kernel `√α` is the `n=2` case of a
  cyclic `C_n` abelian extension. Generalizing it via **ray class fields** (`bnrinit` →
  `bnrclassfield(matdiagonal([n]))`) is the pure-PARI form of the Klüners–Malle systematic
  construction — no Magma required.

- **It opened the minblk=3/4 strata the tower can't touch.** `(deg 8, C3)` = minblk=3, `(deg 6,
  C4)` = minblk=4 — solvable groups the C2-tower structurally misses. Pilot: 22/44 scoreable, 18
  distinct pairs, ~0.41 pairs/build — denser than any saturated harvest producer.

- **Two clean dials.** The kernel `n` picks the block; the base signature is a linear `r` dial
  (totally-real→r=24, mixed→8, complex→0), so one base family covers several `(t,r)` pairs. And the
  label is deterministic per base Galois label → open-gateable. This is a *structural* lever, not a
  disc-min tweak: it manufactures pairs in strata we had no producer for.

- **Discipline held: PILOT before PRODUCER.** Enqueued 12, waited for SAIR labels (5/7 scoreable,
  labels reproduced), THEN promoted to a wired producer — per the evidence ladder, no scaling on an
  unlabelled local fingerprint (the trap of tests 0044/0045/0051–0054).

## 2026-07-12 (update) — Abelian-kernel: works technically, but MEASURED ~0 score value

- **The correction that matters.** The abelian producer's headline "22/44 scoreable, 18 distinct
  pairs, 0.41 pairs/build" was a coverage number. `producer_value.py` (the canonical
  score-per-1000-builds tool) says it earns **0.247 pts total across 38 wins — and 0.243 of that is
  ONE pair** (24T265,24, teamCount=3). Every other win is a heavily-contested group (k≥10, so
  2^(1-k)≈0). The minblk=3/4 strata the generalization reaches are already claimed by many teams.

- **Exactly the trap the quality rules name.** "Score the metric that counts, not a proxy." Distinct
  pairs looked dense and fresh; the score is ~0. I caught myself over-selling it and the tool
  corrected me — the discipline held on the second pass, not the first.

- **What it changes.** The generalization is a real capability (reaches strata the tower can't), but
  it is NOT a score lever — the open score lives in minblk=2 high-r (gen12_treal, 91% of the board),
  not minblk=3/4. abelian dropped to priority 30 (its 10-20s builds must not starve the real lever)
  and kept only as cheap exploration for the rare low-k pair like 24T265. No further investment.

- **Reaching a stratum ≠ earning in it.** The score is gated by teamCount, and the contested strata
  are contested precisely because they're the reachable ones.

## 2026-07-13 — THE SLIDE IS DISC-UNDERCUT, not coverage: we're behind on 97.5% of held pairs

- **The rank-17 story, quantified.** Digging into the overnight official slide (640.7 -> 623.7):
  of ~22,555 pairs we hold scoreable, we are the disc-MIN on only **562**; a rival has a strictly
  smaller disc on **22,029 (97.5%)**. Our discs run **56-82 digits, theirs 32-39** -- roughly 2x.
  Since per-pair score is 2^(1-k)*log(minDisc)/log(ourDisc), a 2x-larger disc collects ~HALF the
  points. Recoverable by matching their disc: **~118 pts** -- dwarfing new-open soles (~1 pt each).

- **We are NOT out-covered; we are out-disc-min'd.** This flips the whole posture. The frontier
  isn't more pairs -- it's SMALLER discs on the pairs we already hold. The rivals at 688-739 aren't
  covering more; they realize the same groups at half the disc.

- **It's our own construction's fault, and it's achievable.** The disc-behind pairs are gen12 builds
  over LARGE split primes (q=11329/18913/39883/52859) and NON-minimal bases -- e.g. 24T13862,4 used
  a 22-digit 12T148 base when a **13-digit** 12T148 field (h=1) exists. general_c2 disc ~
  disc(K0)^2 * (q-stuff), so both levers (smallest-disc base, smallest group-preserving split prime,
  minimal alpha) compound. Matching only TIES the rival (log-ratio -> 1.0), which is enough to
  recover the 2^(1-k) we're currently halving.

- **The catch: group-preservation.** For minblk=2 the group depends on alpha's square class, so a
  disc-min rebuild can't just swap in a smaller q -- it needs the density sweep to confirm it still
  lands the target (t,r). So the defense is a disc-min RE-SWEEP: per held minblk=2 pair, search
  (smallest base, small q, small w) keeping the group, keep the smallest-disc hit. Expensive but the
  single highest-leverage direction on the board -- proposed as the top lever over new-open chasing.

## 2026-07-13 (correction) — the disc-min RE-SWEEP defense is REFUTED by SAIR

- **The mechanism doesn't work; the diagnosis still does.** The disc-undercut finding (behind a
  rival's disc on 97.5% of held pairs, ~118 pts) is real. But the DEFENSE -- re-sweep a held pair
  over the smallest-disc base of the same 12Tj + fingerprint-match to our own held poly -- FAILS:
  SAIR labeled the smaller-disc candidates as NEIGHBORING groups, not the targets (24T13862,4 ->
  24T18770/17391; 15714,4 -> 18891; 3333,0 -> 7935). Our best disc on the targets is unchanged.

- **Root cause: the group is pinned to the specific base field, not the 12Tj label.** Changing to a
  different (smaller-disc) 12T148 field changes the Kummer module -> a different 24Tt. And the local
  Frobenius fingerprint (L1<0.30 vs our held poly) can't tell 24T13862 from 24T18770 -- their
  cycle-type distributions are closer than the threshold. Same low-trust-signal trap as tests
  0044/0045/0051-0054 and yesterday's 9633->17923: fingerprint proximity != same group; only SAIR's
  Magma label is authoritative.

- **The process lesson (mine).** I built the full producer AND the amortized gp optimization on a
  fingerprint SAIR then refuted -- I should have PILOT-checked SAIR labels on ~5 candidates BEFORE
  scaling. The evidence ladder (LOCAL-GATED -> PILOT-LABELED -> PRODUCER) exists precisely to stop
  this; I skipped PILOT-LABELED. The amortized machinery is sound and fast; the group-preservation
  gate is what's missing. A salvage would SAIR-pilot each (base,w,q), persist only the confirmed-
  target triples, and reuse those -- a bigger redesign, deferred.

- **Net: neuter the producer** (not wired into any loop; leave un-deployed) and keep the disc-
  undercut diagnosis as the live strategic finding. Recovering our behind-on-disc pairs needs a
  SAIR-in-the-loop targeted search, not a blind fingerprint re-sweep.

## 2026-07-14 — Project paused: all autonomous runners shut down (user-directed)

- **What was stopped:** every igp24 systemd user unit — searchd (the 24/7 daemon), dashboard, and
  the audit/build/feed/research/tick/watch timers. Stopped and disabled; no igp24 process or timer
  remains.
- **To restart:** `scripts/install_systemd_services.sh` (daemon + dashboard + tick/feed) and
  `scripts/install_headless_loops.sh` (research/audit/build headless Claude loops) re-create
  everything; then `scripts/search_ctl.py refresh` to re-pull live state before producing.
- **Loose ends at the pause:** (1) the last submitted batches' SAIR labels were never collected —
  `scripts/resync_scoreable.py` recovers them on restart; (2) the twist engine's 18007/18009 aims
  (test 0077 class-aware odd-f fix) were queued but their landings were not verified.
- Last observed standing: rank 19, official 597.7 (leaderboard fetch 2026-07-14 13:23 UTC; the last
  coverage snapshot at 13:09 UTC read 598.3), with the disc-undercut diagnosis (a rival's disc is
  smaller on ~97% of our held pairs) as the main strategic finding at the pause. See
  `docs/results.md`.
