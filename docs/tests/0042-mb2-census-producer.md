# 0042 — minblk=2 mass-production census → targeted-base producer (mb2)

**Family:** imprimitive / C2-kernel towers (targeted).
**Date:** 2026-07-05 (evening).
**Question:** the Zulip-decoded famous-41 aside, how many groups has *nobody* realized, and are
they reachable by machinery we already have?

## Setup

1. Census over `progress.json` + `valid_pairs`: a group is *unrealized-open* if **every** valid
   `(t,r)` has `teamCount==0` and we hold no row. Result: **1,576 groups / 9,905 open pairs**
   (1,556 solvable + 20 non-solvable; 1,142 solvable at minblk=2).
2. GAP screen (`scripts/mb2_screen.g`) over the 1,142: block action on the size-2 system, kernel
   size, centrality, `TransitiveIdentification` of the degree-12 top.
   Output committed: `data/targets/mb2_screen_minblk2.csv`.
3. Strike-list builder (`scripts/mb2_strike_list.py`): joins the screen with LMFDB totally-real
   base supply per top + open-pair counts; ranks (supplied, open pairs desc, order asc).
   Output committed: `data/targets/mb2_strike_list.csv`.
4. Producer `produce_mb2` (in `scripts/search_ctl.py`, tick-registered, quota `mb2:` 14%):
   walks the strike list's distinct tops (cursor `mb2_top_off`), pulls up to 3 totally-real
   bases/top (fallback: any signature), sweeps the gen12 w-patterns × 2 split primes through the
   existing `general_c2` construction; atlas-tagged `mb2:12Tj:...` with the gen12 dry-gate.

## Results

- Kernel-size distribution of the 1,140 screened: ks 8..2048 dominate (rank 3–11); **only one
  strict central-C2** (24T2778). The spin-engine framing was wrong for this stratum — but all
  1,139 are single-quadratic extensions over their deg-12 top, i.e. **`general_c2` targets**:
  kernel rank = the C2^12-submodule the w-pattern selects. The reason harvest missed them is
  **aim, not machinery**: gen12 walks LMFDB by smallest disc and never targeted these tops.
- Supply is complete: **all 1,139 targets sit over 144 distinct tops, every one with LMFDB
  fields** (2–8 totally-real each on sampled tops); 6,943 open pairs carried.
- First live tick: **1,830 constructions enqueued across 16 tops, 34 usable bases**; daemon
  building immediately. SAIR was 522-down at build time, so labels/hit-rate pending its recovery.

## Learnings

- **Check the kernel rank before reaching for the spin engine** — centrality is the exception
  (1/1,140), not the rule; the mass lane was the existing engine pointed correctly.
- The census unit that matters is *unrealized-open groups* (multi-pair sole claims), not open
  pairs: 1,576 groups nobody holds is a larger, quieter frontier than the contested famous 41.
- Reproduce: `scripts/mb2_screen.g` (GAP) → `scripts/mb2_strike_list.py` →
  `search_ctl produce-mb2`.
