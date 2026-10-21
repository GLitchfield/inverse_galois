"""Marginal score per producer -- by DISTINCT scoreable signature EARNED, not rows (review 2026-07).

The bandit/ranking used row counts, which over-credit a producer that floods dupes (realized.csv is
~49 rows per scoreable signature). This attributes each scoreable pair to the producer whose BEST
model owns it, sums the pair's expected score, and divides by that producer's build cost (its
realized rows) -> score per 1,000 builds + duplicate pressure (rows per owned pair). This is how to
see which producers actually PAY -- the input to rebalancing (e.g. the minblk>=3 lane question).

Run: uv run python scripts/producer_value.py
"""

from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from igp import coverage, db, rank  # noqa: E402

csv.field_size_limit(10**7)
PROG = ROOT / "data" / "processed" / "progress.json"


def main() -> None:
    prog = json.loads(PROG.read_text()) if PROG.exists() else {}
    best = coverage.best_by_pair()  # (t,r) -> best model

    earned: dict = collections.defaultdict(float)
    owned: collections.Counter = collections.Counter()
    for (t, r), b in best.items():
        fam = rank.producer_of_source(b["source"])
        earned[fam] += coverage.exp_score(t, r, b["disc"], prog)
        owned[fam] += 1

    rows_by: collections.Counter = collections.Counter()  # build cost = total realized rows
    for row in db.load_realized():
        if row.get("label", "").startswith("24T"):
            rows_by[rank.producer_of_source(row.get("source", ""))] += 1

    print(f"  {'producer':13} {'owns pairs':>10} {'earned pts':>10} {'rows':>10} "
          f"{'pts/1k builds':>13} {'dupe':>6}")
    print("  " + "-" * 66)
    for fam in sorted(earned, key=lambda f: -earned[f]):
        nrows = rows_by.get(fam, 0)
        per1k = 1000 * earned[fam] / nrows if nrows else 0.0
        dupe = nrows / owned[fam] if owned[fam] else 0.0
        print(f"  {fam:13} {owned[fam]:>10} {earned[fam]:>10.1f} {nrows:>10} "
              f"{per1k:>13.2f} {dupe:>6.0f}")
    print(f"\n  totals: {sum(owned.values())} owned pairs, {sum(earned.values()):.0f} earned pts, "
          f"{sum(rows_by.values())} rows -- pts/1k builds is the lever to rank producers by.")


if __name__ == "__main__":
    main()
