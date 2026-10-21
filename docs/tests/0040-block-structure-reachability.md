# 0040 — Block-structure reachability map (tower shape ↔ 24Tt), and where the open targets sit

**Family:** coverage / construction-strategy. **Date:** 2026-07-01.
**Question:** which degree-24 transitive groups are reachable by which imprimitive *tower shape*, and
where do the OPEN (`teamCount==0`, non-baseline, unrealized) targets concentrate? In particular: what
is the structural blind spot of our dominant machinery (C2/V4/C3 kernels over degree-12 bases)?

## Method

`AllBlocks(TransitiveGroup(24,t))` for all `t=1..25000` (GAP, ~15s) → **minimal block size** `minblk`
per group (`scripts/gap/minblk_deg24.g` → `data/targets/block_structure_deg24.csv`). A group with
minimal block size `a` (`b=24/a` blocks) is a subgroup of `S_a ≀ S_b`, hence buildable as a
**degree-`a` relative kernel over a degree-`b` base field**. Cross-tabbed against `realized.csv`
(realized), `progress.json` (teamCount), `transitive_groups_deg24.csv` (order/solvable) by
`scripts/analyze_block_structure.py`. Strata counts are exact; open counts are a live snapshot (they
drift as the daemon realizes groups + the leaderboard moves).

## Result (snapshot 2026-07-01)

| minblk `a` | shape (base×kernel) | #groups | realized | open groups | open sigs | solvable |
|---|---|---|---|---|---|---|
| 0 primitive | — | 5 | 4 | 1 (A24) | 5 | 0 |
| 2 | 12×2 (deg-12 × C2) | 20,733 | 2,492 | 14,045 | 67,129 | 13,775 |
| 3 | 8×3 (octic × cubic) | 3,222 | 35 | 623 | 2,772 | 604 |
| 4 | 6×4 (sextic × quartic) | 866 | 11 | 747 | 4,989 | 700 |
| 6 | 4×6 (quartic × sextic) | 110 | 5 | 69 | 294 | 0 |
| 8 | 3×8 (cubic × octic) | 53 | 2 | 49 | 249 | 25 |
| 12 | 2×12 (quad × deg-12) | 11 | 1 | 10 | 41 | 0 |

- **The C2-workhorse blind spot.** Our dominant machinery makes ONLY the `minblk=2` shape (12 blocks
  of 2). A group has a size-2 block **iff** `minblk=2`, so the **4,262 groups with `minblk≥3` are
  structurally unreachable that way** — `~1,498` of them open ⇒ **`~8,345` open `(t,r)` signatures**
  (the scoring unit; ~5.6× the group count). Multiple block systems mean many `minblk∈{3,4}` groups
  also admit larger blocks, so alternate tower routes exist — the cliff is specific to the size-2
  default, not inaccessibility.
- **93% of the opportunity is two solvable pools.** `minblk=3` (8×3) + `minblk=4` (6×4) = ~1,370 open
  groups / ~7,760 open sigs, overwhelmingly solvable, mid-order (many at order 1,152–1,728). `minblk=4`
  alone is the single biggest lever (~5,000 sigs); `produce_size4*` exists but has realized only 11/866
  → barely exploited.
- **The non-solvable tail is small and structurally pinned.** 169 open groups / ~806 sigs, by minblk
  `{3:19, 4:47, 6:69, 8:24, 12:10}`; 64 are order `<1e8` (tractable), the rest astronomical-disc. By
  the `S_a ≀ S_b` embedding the non-abelian composition factor must live in `S_a` or `S_{24/a}`, so it
  is one of **A5/A6** (a size-6 present), **PSL(2,7)/A7/A8** (size-8), **M11/M12/PSL(2,11)** (size-12) —
  all with known low-degree *rigid* realizations. `minblk=12` (10 groups) contains the M12.2 siblings
  24T18439/18440/18441 → directly served by the Roberts-cover agenda item.

## Learnings

1. "We're plateauing" resolves into a concrete map: **~8,300 open signatures behind two buildable
   tower shapes** (8×3, 6×4) we do not yet exploit, plus a small non-solvable tail.
2. Biggest single lever = **expand the 6×4 (`minblk=4`) producer** (more sextic bases + quartic kernel
   patterns): ~5,000 open sigs, 700+ solvable groups, only 11 realized.
3. `minblk=3` S3-cubic subset = task #13 (non-Galois radical cubic). Direct-product subset = task #14.
4. Non-solvable tail: not hopeless — reach it by a tower whose base/kernel realizes a small rigid
   simple (A5/A6/PSL(2,7)/M12). Connects to the Roberts M12.2 covers + the coset-action / rigidity
   agenda items. Deprioritized vs the solvable pools (7% of the opportunity) but tractable for the
   64 small-order ones.

## Reproducibility

`gap -q -b scripts/gap/minblk_deg24.g` (regenerates the CSV) → `uv run python
scripts/analyze_block_structure.py`. Committed: the block CSV + both scripts. Extends the
2026-07-01 headless "imprimitive/block-structure systematics" dive (`docs/auto_log.md`) with the
signature-level counts + the non-solvable-tail factor analysis.
