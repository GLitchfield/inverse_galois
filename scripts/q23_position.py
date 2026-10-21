"""q23 — leaderboard position analysis: ground disc-min and coverage targeting.

Uses the live per-signature state from sair.labels_progress (teamCount, minimumDiscAbs,
discovered) to classify our realized (t,r):

- sole (teamCount<=1, us): score already maxed (D0 = ours) — disc-min cannot help.
- best (our_disc <= global min): we hold the minimum.
- beatable (our_disc > global min): a smaller realization would raise our score — disc-min
  targets, ranked by the log-disc gap.

Also surfaces UNDISCOVERED signatures (teamCount==0) as the highest-value coverage targets
(sole realizer => score 1.0).

Reads progress.json (fetched separately) + our realized.csv. Run after a fetch.
Run: uv run python scripts/q23_position.py
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

from igp import db

ROOT = Path(__file__).resolve().parents[1]
# Live per-pair leaderboard state (fetched separately; search_ctl refresh writes this path).
PROG = Path(os.environ.get("IGP_PROGRESS", ROOT / "data" / "processed" / "progress.json"))


def analyze(progress: dict):
    cov = db.coverage()  # (t,r) -> best row
    sole = best = beatable = 0
    disc_targets = []
    for (t, r), row in cov.items():
        if not row.get("field_disc"):
            continue
        key = f"{t},{r}"
        info = progress.get(key)
        if not info or info.get("minDisc") is None:
            continue
        ours = abs(int(row["field_disc"]))
        gmin = abs(int(info["minDisc"]))
        tc = info.get("teamCount", 0)
        if tc <= 1:
            sole += 1
        elif ours <= gmin:
            best += 1
        else:
            beatable += 1
            gap = math.log(ours) / math.log(gmin) if gmin > 1 else 1.0
            disc_targets.append((gap, t, r, ours, gmin, tc))
    disc_targets.sort(reverse=True)
    return {"sole": sole, "best": best, "beatable": beatable, "targets": disc_targets}


def main():
    if not PROG.exists():
        print(f"progress not fetched: {PROG} missing")
        return
    progress = json.loads(PROG.read_text())
    print(f"loaded {len(progress)} live signatures")
    res = analyze(progress)
    print("\nour realized signatures vs leaderboard:")
    print(f"  sole realizer (score maxed):        {res['sole']}")
    print(f"  we hold the min disc:               {res['best']}")
    print(f"  beatable (disc-min could help):     {res['beatable']}")
    if res["targets"]:
        print("\ntop disc-min targets (log-disc ratio ours/min, higher=more room):")
        for gap, t, r, ours, gmin, tc in res["targets"][:15]:
            print(f"  24T{t} r={r}: ratio {gap:.3f}  ours={len(str(ours))}d "
                  f"min={len(str(gmin))}d teams={tc}")
    # coverage: count undiscovered signatures (teamCount==0) -> sole=1.0 if we hit them
    undisc = sum(1 for v in progress.values() if v.get("teamCount", 0) == 0)
    print(f"\nundiscovered signatures (coverage targets, sole=1.0): {undisc}")


if __name__ == "__main__":
    main()
