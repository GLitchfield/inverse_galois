# 0002 — Where is the frontier? Coverage × group structure

**Family:** analysis / strategy · **Date:** 2026-06-24 · **Script:** `scripts/q08_coverage_analysis.py`

## Question

Based on which groups are already solved, where should method development focus?

## Setup

Join the live participant-coverage snapshot (`data/targets/signatures_deg24.csv`: per-`(t,r)`
`discovered`, `team_count`) with group structure (`transitive_groups_deg24.csv`: order, solvable,
primitive, transitivity, in-A_24). A group is "touched" if any of its signatures is participant-
discovered. (Snapshot; participant-only, baseline not subtracted — small effect.)

## Result

- **Overall:** 13,459/25,000 groups touched (54%); 47,727/165,836 signatures (29%).
- **Coverage runs OPPOSITE to difficulty:** non-solvable **76%** (616/807), primitive **4/5**, but
  solvable only **53%** (12,843/24,193). The "hard" exotic groups are mostly done; the solvable bulk isn't.
- **By order:** ≤100 → 92%; **1000–10⁴ → 49%** (least covered); 10⁴–10⁶ → 51%; ≥10⁶ → 58%.
- **Frontier:** 11,541 untouched groups = **11,350 solvable + 191 non-solvable.** ~98% solvable.
- **Saturation of solved groups (max teams/signature):** 7,278 have 1 team, 4,974 have 2–5, 1,187 have
  6–20, 20 have 21+. The easy groups are crowded.
- The single untouched **primitive** group is the **2-transitive** one (likely `PSL(2,23)`).

## Learnings

- **The frontier is the solvable imprimitive bulk, especially mid/large order — not the non-solvable /
  primitive groups** (those have known generic/wreath/family constructions others already used).
- Our G1/G2 harvesting lands on the same easy, crowded groups everyone gets (high `k`, low value). The
  open, high-value territory is the **specific** solvable imprimitive groups that simple
  full-wreath/direct-product constructions miss → **deliberate construction (WS1) + embedding problems
  (WS4)** is where method development has leverage.
- WS5 (rigidity) becomes a *targeted* track (the lone untouched primitive group), not the bulk play.

Reprioritizes `docs/phase_2_plan.md`: lead with WS-INFRA-A (identifier) + WS1/WS4 for solvable
imprimitive groups.
