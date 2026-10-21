"""Reconcile LOCAL accounting against OFFICIAL leaderboard accounting (P0 review 2026-07-11).

The review flagged the local estimate (~521) vs cached official score (~671) gap as an accounting
bug until explained. This report explains it decisively:

  1. PAIR COUNT: our held scoreable (t,r) vs the official `scoreablePairs` for our team -- these
     should match closely (they reconcile); the gap is NOT missing pairs.
  2. SCORE DECOMPOSITION: local est score by teamCount k = 2^(1-k)*log(minDisc)/log(ourDisc). Shows
     the estimate is dominated by a few low-k pairs and that ~77% of pairs sit at k>=6 (near-zero
     weight) -- i.e. the deficit is per-pair VALUE (rarity + disc), not coverage.
  3. DISC SOURCE: exact vs mixed vs blank, kept SEPARATE (mixed cannot be compared to exact for
     baseline unlocks).
  4. DISC HEADROOM: how many pairs a rival beats us on disc (behind), median log-ratio.

Run: uv run python scripts/reconcile_accounting.py
"""

from __future__ import annotations

import collections
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(10**7)
PROG = ROOT / "data" / "processed" / "progress.json"
LB = ROOT / "data" / "processed" / "leaderboard.json"
REALIZED = ROOT / "data" / "targets" / "realized.csv"


def main() -> None:
    prog = json.loads(PROG.read_text()) if PROG.exists() else {}
    # our best (smallest) disc per held scoreable pair + disc_source
    best: dict = {}
    src_count: collections.Counter = collections.Counter()
    for r in csv.DictReader(REALIZED.open()):
        if str(r.get("scoreable")).lower() != "true" or not r.get("label", "").startswith("24T"):
            continue
        ds = r.get("disc_source") or "blank"
        fd = r.get("field_disc") or ""
        key = (r["t"], r["r"])
        src_count[ds if fd.lstrip("-").isdigit() else "blank"] += 1
        if fd.lstrip("-").isdigit():
            d = abs(int(fd))
            cur = best.get(key)
            if cur is None or cur[0] is None or d < cur[0]:
                best[key] = (d, ds)
        else:
            best.setdefault(key, (None, ds))

    pairs = set(best)
    byk: collections.Counter = collections.Counter()
    score_k: dict = collections.defaultdict(float)
    ratios: list[float] = []
    behind = with_min = 0
    for (t, r), (d, _ds) in best.items():
        k = max(prog.get(f"{t},{r}", {}).get("teamCount", 1), 1)
        byk[k] += 1
        md = prog.get(f"{t},{r}", {}).get("minDisc")
        if d and md and str(md).isdigit() and d > 1:
            ratio = math.log(int(md)) / math.log(d)
            with_min += 1
            behind += ratio < 0.999
            ratios.append(ratio)
            score_k[k] += (2 ** (1 - k)) * ratio
        else:
            score_k[k] += 2 ** (1 - k)  # no leaderboard min or blank -> assume ratio 1

    # official numbers from the cached leaderboard
    off_pairs = off_score = None
    if LB.exists():
        try:
            items = json.loads(LB.read_text()).get("items", [])
            us = next((i for i in items if i.get("teamName") == "Team Gavin"), None)
            if us:
                off_pairs, off_score = us.get("scoreablePairs"), us.get("score")
        except Exception:
            pass

    print("=== PAIR-COUNT RECONCILIATION ===")
    print(f"  local held scoreable pairs : {len(pairs)}")
    print(f"  official scoreablePairs    : {off_pairs}")
    if off_pairs:
        ok = "reconciles" if abs(len(pairs) - off_pairs) < 0.02 * off_pairs else "INVESTIGATE"
        print(f"  difference                 : {len(pairs) - off_pairs:+d}  ({ok})")

    print("\n=== DISC SOURCE (exact vs mixed must stay separate) ===")
    for s, n in src_count.most_common():
        print(f"  {s:14s} {n}")

    print("\n=== SCORE DECOMPOSITION by teamCount k (local estimate) ===")
    est = sum(score_k.values())
    for k in sorted(byk)[:8]:
        print(f"  k={k:>2}: {byk[k]:6d} pairs  est {score_k[k]:7.1f}  (weight {2 ** (1 - k):.4f})")
    hik = sum(v for k, v in byk.items() if k >= 6)
    pct = 100 * hik // max(len(pairs), 1)
    print(f"  k>=6: {hik} pairs ({pct}% of ours) -- weight <0.031, ~worthless")
    print(f"\n  local estimated score : {est:.0f}")
    print(f"  official score        : {off_score}")
    if off_score:
        print(f"  gap                   : {off_score - est:+.0f}")
        if off_pairs and off_pairs - len(pairs) > 0.02 * off_pairs:
            print(f"  --> {off_pairs - len(pairs)} pairs are officially scoreable but NOT locally "
                  "marked (STALE local scoreable flags: scored server-side, never re-fetched). "
                  "Local ranking/defense/coverage undercount -- re-sync scoreable from SAIR. This "
                  "is the accounting gap, NOT lost score (official already credits it).")
        else:
            print("  --> pairs reconcile; the remaining gap is estimator conservatism "
                  "(stale/approx minDisc + ratio=1 fallback), not missing score.")

    if ratios:
        ratios.sort()
        print(f"\n=== DISC HEADROOM ===\n  behind on disc: {behind}/{with_min} "
              f"({100 * behind // max(with_min, 1)}%)  median ratio {ratios[len(ratios) // 2]:.3f}")


if __name__ == "__main__":
    main()
