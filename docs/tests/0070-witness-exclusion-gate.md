# 0070 — WITNESS EXCLUSION: the fingerprint gate was using the wrong tool in the subgroup direction

**Family:** MINBLK=2 / `general_c2_TWIST` (sign-character aim)
**Date:** 2026-07-13
**Recipe:** research dive #51 (`docs/auto_log.md`, 2026-07-13); build_backlog Ready item 1
**Code:** `scripts/mb2_twist.py` (gate), `scripts/mb2_twist_sign_producer.py` (producer)
**Status:** LOCAL-GATED → PILOT (2 candidates enqueued, SAIR labels pending)
**Resolution (recorded in test 0071):** both candidates later returned official Magma labels `24T21582`, the aimed group.

## Question

Test 0069 built 24T21582 over 12T170 three times, each landing a dim-11 kernel, and **refused** every
one: L1 ≈ 0.154–0.176 to the target but a runner-up at 0.157–0.183, i.e. a margin of ≈ 0.00–0.03
against a 0.15 bar. It recorded the cause as "the three dim-11 siblings are not density-separable".
Dive #51 refuted that (the siblings are pairwise L1 = 0.94–1.00 apart — the *most* separable objects in
the library) and re-diagnosed the blind spot as **24T20545, a dim-10 index-2 SUBGROUP at true L1 =
0.0663**, under the 780-prime gate's ≈ 0.15 sampling-noise floor. Does the proposed fix — raise the
prime budget and replace the blanket margin bar with **witness exclusion** — make the gate decisive,
and does the refused build then pass?

## Setup

Three changes, all mechanical (no new theory):

1. **Prime budget.** The fingerprint loop `forprime(p = 3, 6000, ...)` (783 primes) → parameterized
   `FPMAX`, default **50000** (5,133 primes). Dive #51's Monte-Carlo puts the witness kill of 24T20545
   at 49% at N=780 and 100% at N≈5,000. (Dive #51 wrote "250000 ≈ 5,000 primes"; π(250000) = 22,044.
   The prime *count* is the operative quantity, so the bound is set at 50000.)
2. **Witness exclusion** (`mb2_twist.witness_exclude`). If a cycle type τ is observed at some prime and
   τ ∉ supp(C), then Frob_p ∉ C, so **G ⊄ C** — deterministically, from one prime, no margin. Rivals
   are killed by witness; the density/margin test then runs **only over the survivors**, which are
   exactly the witness-proof rivals (supergroups, and any Gassmann twin). This is the classical
   division of labour our gate had backwards: *witnesses kill subgroups, densities kill supergroups.*
3. **Self-reported resolution** (`mb2_twist.resolution`, `--resolution T --top J`). Per library rival:
   true L1 to the target and **witness mass** (the target's density on cycle types absent from the
   rival's support = the per-prime chance of excluding it). Computable before any polynomial is built.

Off-target landings that are themselves open pairs are now enqueueable (`--accept-open`): the daemon
records the label SAIR returns, not the one we aimed at (`searchd.py:143`), so the local gate is a
submission-economy filter, not a correctness gate.

## Result

**A priori resolution of lib170** (`--resolution 21582 --top 170`) reproduces dive #51's table exactly:

| rival | kdim | L1 to 21582 | witness mass | primes to kill |
|---|---|---|---|---|
| 24T20545 | 10 | **0.0663** | 0.0010 | ~1024 |
| 24T20544 | 10 | 0.2811 | 0.0417 | ~24 |
| 24T19545 | 9 | 0.3765 | 0.1177 | ~8 |
| 24T22530 (full wreath) | 12 | 0.9436 | **0.0000** | **NEVER — witness-proof** |
| 24T21581 (sibling) | 11 | 0.9436 | 0.1104 | ~9 |

The **only** witness-proof rival over 12T170 is the full wreath, at L1 0.944 — where the density is
decisive by three orders of magnitude. The gate has no blind spot left.

**The refused build passes.** `mb2_twist_sign_producer.py --targets 21582 --accept-open --ncand 3
--per-target 3` over base 12T170, d = 5, split primes [4079, 26759]:

| radical (q_a_b) | lands | kdim | L1 | margin | rivals witness-killed | verdict |
|---|---|---|---|---|---|---|
| 4079_1_2 | **24T21582** | 11 | 0.057 | **0.902** | 24 of 25 | GATED |
| 4079_1_3 | **24T21582** | 11 | 0.050 | **0.908** | 24 of 25 | GATED |
| 4079_1_4 | 24T20544 | 10 | 0.048 | 0.254 | 23 of 25 | REJECT (off-target, not open at r=24) |

Observed L1-to-target 0.050–0.057 lands on dive #51's simulated E[L1] = 0.058 at N = 5,000 — the model
was not fitted to it. 24T20545 is witness-killed in both gated candidates; the surviving rival is the
full wreath, hence the 0.90 margin where test 0069 saw 0.03. The margin didn't improve because the
polynomial changed — the same construction, the same base, the same `d` — it improved because the gate
stopped asking a density to do a witness's job.

Both gated candidates: deg-24 irreducible, `polsturm` = 24, and a **fully smooth field disc**
2.625e54 = 2^a·3^b·5^c·101·4079 (max prime 4079 ≪ 10⁶, so no grader-blank risk). `nfisisom` says they
are **not isomorphic** — two distinct fields with the same disc, i.e. two independent shots at the
label, not a duplicate.

**Enqueued:** 2 candidates, 1 pair — `(24T21582, r=24)`, tier **new** (zero rows held), tags
`lit:mb2twsignnew:21582.24:base12T170:d5:q4079_1{2,3}` @130. `(24T21582, 24)` re-verified `teamCount=0`
+ non-baseline against `progress.json` (2026-07-13 05:25). Daemon submitted both within minutes.

## Learnings

- **The refusal in test 0069 was real, but its diagnosis was inverted, and the inverted diagnosis was
  load-bearing.** It had been written into the backlog as "24T21582 is density-BLOCKED" — a permanent
  wall on a target that needed nothing but more primes and the right test. A gate that cannot state
  its own resolution will keep producing walls that are really budgets.
- **Witnesses kill subgroups; densities kill supergroups.** A subgroup shares half the target's
  elements, so its density is arbitrarily close — but unless it is Gassmann-equivalent, some cycle type
  of the target is absent from it, and one prime realizing that type excludes it with certainty. A
  supergroup contains every cycle type, so witness mass is 0 and only a density can touch it. Our old
  "L1 + blanket margin" used the density tool in the direction where it has essentially no power.
- **The Gassmann case is the only real wall** (identical cycle-type distribution ⇒ witness mass 0 both
  ways ⇒ no prime budget separates them) — test 0066's 9641/9642/9643 triple. It is now *distinguishable
  from an under-sampling wall* before a build starts: witness mass 0 in both directions is Gassmann;
  witness mass > 0 with a bad margin is a budget.
- **The 0.15 margin bar was calibrated against far-away rivals** and silently became an
  under-sampling detector. Replacing it with per-rival exclusion removes the calibration entirely.
- Ladder status: **PILOT, not PRODUCER.** Nothing in the twist family carries an official Magma label
  yet (test 0068's five and test 0069's five are all still `label=None`). The gate being decisive is
  not the sign map being validated.

## Reproduce

```
.venv/bin/python scripts/mb2_twist.py --resolution 21582 --top 170
.venv/bin/python scripts/mb2_twist_sign_producer.py --targets 21582 --accept-open \
    --ncand 3 --per-target 3 --pilot 5 --enqueue
```
