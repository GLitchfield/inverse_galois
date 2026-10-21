"""Block-structure reachability map for degree-24 (test 0040).

Which 24Tt are reachable by which imprimitive tower shape, and where the OPEN (teamCount==0,
non-baseline, unrealized) coverage sits. A group with minimal block size a (b=24/a blocks) is a
subgroup of S_a wr S_b -> buildable as a degree-a relative kernel over a degree-b base field. Our
dominant machinery (C2/V4/C3 kernels over degree-12 bases) makes ONLY the minblk=2 shape, so every
minblk>=3 group is its structural blind spot.

For the non-solvable tail the wreath embedding pins the possible non-abelian composition factors: a
minblk=a group's simple factor lives in S_a or S_(24/a), so it is one of A5/A6 (a or b = 6),
PSL(2,7)/A7/A8 (=8), M11/M12/PSL(2,11)/A_k (=12). All have known low-degree rigid realizations.

Reads: data/targets/block_structure_deg24.csv (minblk, committed) + transitive_groups_deg24.csv +
realized.csv (committed) + data/processed/progress.json (live teamCount; strata counts are exact
without it, open counts need it). Run: uv run python scripts/analyze_block_structure.py
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from igp import baseline, db

ROOT = Path(__file__).resolve().parents[1]
SHAPE = {0: "primitive", 2: "12x2 deg12base x C2", 3: "8x3 octic x cubic",
         4: "6x4 sextic x quartic", 6: "4x6 quartic x sextic", 8: "3x8 cubic x octic",
         12: "2x12 quad x deg12"}


def main() -> None:
    minblk = {int(r["t"]): int(r["minblk"])
              for r in csv.DictReader((ROOT / "data/targets/block_structure_deg24.csv").open())}
    meta = {int(r["t"]): r
            for r in csv.DictReader((ROOT / "data/targets/transitive_groups_deg24.csv").open())}
    rows = db.load_realized()
    realized_t = {int(r["t"]) for r in rows if r.get("label", "").startswith("24T")}
    held = {(int(r["t"]), int(r["r"])) for r in rows if r.get("label", "").startswith("24T")}
    try:
        prog = json.loads((ROOT / "data/processed/progress.json").read_text())
    except Exception:
        prog = {}

    def tc(t, r):
        return prog.get(f"{t},{r}", {}).get("teamCount", 1)

    def solvable(t):
        return str(meta.get(t, {}).get("solvable", "")).lower() == "true"

    opensig: dict = {}  # group -> [open r's]: valid, teamCount==0, non-baseline, unheld
    for t, r in ((int(a), int(b)) for a, b in baseline.valid_pairs()):
        if (t, r) not in held and tc(t, r) == 0 and not baseline.is_baseline(t, r):
            opensig.setdefault(t, []).append(r)

    def row(*c):
        print(f"{c[0]:>6} {c[1]:<22} {c[2]:>6} {c[3]:>6} {c[4]:>6} {c[5]:>7} {c[6]:>9}")

    row("minblk", "shape", "#grp", "realiz", "openG", "openSig", "solv")
    tot_g = tot_s = 0
    for a in [0, 2, 3, 4, 6, 8, 12]:
        grp = [t for t, m in minblk.items() if m == a]
        real = sum(1 for t in grp if t in realized_t)
        opg = [t for t in grp if t not in realized_t and t in opensig]
        sigs = sum(len(opensig[t]) for t in opg)
        sv = sum(1 for t in opg if solvable(t))
        if a >= 3:
            tot_g += len(opg)
            tot_s += sigs
        row(a, SHAPE[a], len(grp), real, len(opg), sigs, f"{sv}/{len(opg)}")
    print(f"\nminblk>=3 blind spot: {tot_g} open groups, {tot_s} open (t,r) signatures")

    ns = [t for t, m in minblk.items() if m >= 3 and t not in realized_t
          and t in opensig and not solvable(t)]
    tractable = sum(1 for t in ns if t in meta and int(meta[t]["order"]) < 10**8)
    print(f"non-solvable tail: {len(ns)} open groups, {sum(len(opensig[t]) for t in ns)} sigs; "
          f"by minblk {dict(sorted(Counter(minblk[t] for t in ns).items()))}; "
          f"order<1e8 (tractable) {tractable}")


if __name__ == "__main__":
    main()
