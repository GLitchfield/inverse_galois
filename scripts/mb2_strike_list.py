"""Build the minblk=2 spin-engine strike list (mass-production census, 2026-07-05).

Joins three sources into a ranked strike list for the spin/central-C2 engine:
  1. the GAP screen (mb2_screen.csv: which unrealized minblk=2 solvable groups are
     central-C2 covers of their degree-12 block quotient, split vs non-split),
  2. LMFDB totally-real base supply per needed 12Tj top,
  3. open-pair counts per target (every pair of an unrealized group is tc=0).

Rank: non-split central covers first (split ones are in principle harvest-reachable),
then by (base supply > 0, open pairs desc, group order asc — cheaper verify first).
"""

from __future__ import annotations

import csv
import sys
from collections import Counter

from igp import baseline, lmfdb

# Default: the committed output of scripts/mb2_screen.g (same columns as its mb2_screen.csv).
SCREEN = sys.argv[1] if len(sys.argv) > 1 else "data/targets/mb2_screen_minblk2.csv"
OUT = "data/targets/mb2_strike_list.csv"


def main() -> None:
    rows = list(csv.DictReader(open(SCREEN)))
    # kernel_size 2^k, k>=1: ALL are single-quadratic exts of the deg-12 block field; the
    # kernel RANK = the C2^12-submodule general_c2's w-pattern selects. So every row is a
    # general_c2 target given the right 12Tj base -- centrality only picks the square-class.
    central = [r for r in rows if int(r["kernel_size"]) >= 2]
    print(f"screen rows {len(rows)}; single-quadratic targets kept {len(central)}")

    pairs: dict[int, int] = Counter()
    for a, _b in baseline.valid_pairs():
        pairs[int(a)] += 1

    supply: dict[str, tuple[int, int]] = {}
    for j in sorted({r["top12j"] for r in central}, key=int):
        lab = f"12T{j}"
        try:
            fl = lmfdb.fields(12, galois_label=lab, max_r2=0, class_number=None, limit=200)
            tr = len(fl)
            h1 = sum(1 for (_c, _g, _d, h) in fl if h in (1, "1"))
        except Exception as e:  # LMFDB mirror hiccup: mark unknown, don't drop the top
            print(f"  supply {lab}: ERROR {str(e)[:50]}")
            tr, h1 = -1, -1
        supply[j] = (tr, h1)

    for r in central:
        tr, h1 = supply[r["top12j"]]
        r["tr_bases"] = tr
        r["h1_bases"] = h1
        r["open_pairs"] = pairs.get(int(r["t"]), 0)

    central.sort(key=lambda r: (
        r["split"] != "0",              # non-split first
        (r["tr_bases"] or 0) <= 0,       # supplied tops first
        -r["open_pairs"],
        int(r["order"]),
    ))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["t", "order", "kernel_size", "central", "split",
                                          "top12j", "tr_bases", "h1_bases", "open_pairs"])
        w.writeheader()
        w.writerows(central)
    print(f"strike list -> {OUT} ({len(central)} targets)")
    print("top 15:")
    for r in central[:15]:
        print(f"  24T{r['t']} (ord {r['order']}, split={r['split']}) top 12T{r['top12j']} "
              f"tr_bases={r['tr_bases']} open_pairs={r['open_pairs']}")


if __name__ == "__main__":
    main()
