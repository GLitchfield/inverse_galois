"""q08 — where is the frontier? Cross live coverage with group structure.

Joins data/targets/signatures_deg24.csv (per-(t,r): discovered, team_count — a
snapshot of PARTICIPANT coverage) with transitive_groups_deg24.csv (per-t: order,
solvable, primitive, transitivity, in_A24) to see which structural strata are
saturated vs untouched — i.e., where developing methods has the most leverage.

Run: uv run python scripts/q08_coverage_analysis.py
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    gpath = ROOT / "data/targets/transitive_groups_deg24.csv"
    grp = {int(r["t"]): r for r in csv.DictReader(open(gpath))}
    allowed, solved_sigs, maxteam = (defaultdict(int), defaultdict(int), defaultdict(int))
    for s in csv.DictReader(open(ROOT / "data/targets/signatures_deg24.csv")):
        t = int(s["t"])
        allowed[t] += 1
        if s["discovered"] == "True":
            solved_sigs[t] += 1
        maxteam[t] = max(maxteam[t], int(s["team_count"]))
    ts = sorted(grp)
    solved = {t: solved_sigs[t] > 0 for t in ts}

    def frac(pred):
        tot = [t for t in ts if pred(t)]
        sol = [t for t in tot if solved[t]]
        return len(sol), len(tot)

    print(f"OVERALL: {sum(solved.values())}/{len(ts)} groups have >=1 participant signature")
    print(f"  signatures: {sum(solved_sigs.values())}/{sum(allowed.values())} discovered\n")

    print("by solvability / primitivity (solved groups / total):")
    for name, pred in [
        ("solvable", lambda t: grp[t]["solvable"] == "True"),
        ("non-solvable", lambda t: grp[t]["solvable"] == "False"),
        ("primitive", lambda t: grp[t]["primitive"] == "True"),
        ("in A_24", lambda t: grp[t]["in_an"] == "True"),
    ]:
        s, n = frac(pred)
        print(f"  {name:14s}: {s:5d}/{n:5d}  ({100*s/n:4.0f}%)")

    print("\nby group order (solved / total):")
    bins = [(1, 100), (100, 1000), (1000, 10000), (10000, 10**6), (10**6, 10**40)]
    for lo, hi in bins:
        s, n = frac(lambda t, lo=lo, hi=hi: lo <= int(grp[t]["order"]) < hi)
        if n:
            print(f"  [{lo:>7}, {hi:<9}): {s:5d}/{n:5d}  ({100*s/n:4.0f}%)")

    print("\nby transitivity (solved / total):")
    for k in sorted({int(grp[t]["transitivity"]) for t in ts}):
        s, n = frac(lambda t, k=k: int(grp[t]["transitivity"]) == k)
        print(f"  {k}-transitive: {s:5d}/{n:5d}  ({100*s/n:4.0f}%)")

    print("\nsaturation of SOLVED groups (max #teams on any signature):")
    tc = Counter(maxteam[t] for t in ts if solved[t])
    for band, lo, hi in [("1 team", 1, 2), ("2-5", 2, 6), ("6-20", 6, 21), ("21+", 21, 10**9)]:
        print(f"  {band:6s}: {sum(v for k, v in tc.items() if lo <= k < hi)} groups")

    untouched = [t for t in ts if not solved[t]]
    nonsolv_un = sum(1 for t in untouched if grp[t]["solvable"] == "False")
    print(f"\nFRONTIER: {len(untouched)} untouched groups; "
          f"{nonsolv_un} non-solvable, {len(untouched)-nonsolv_un} solvable")


if __name__ == "__main__":
    main()
