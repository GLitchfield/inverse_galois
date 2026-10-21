"""Coverage + disc-min audit — the honest scoring picture (test 0029).

Two things the per-row counters hide:
  1. The competition scores DISTINCT (t,r) signatures; realized.csv has many polys per signature, so
     "scoreable rows" badly overcounts "scoreable signatures".
  2. For signatures we already cover, score also depends on discriminant smallness vs the
     leaderboard min -- a signature we "have" can still leak points to a team with a smaller disc.

Run: uv run python scripts/analyze_coverage.py
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path

from igp import baseline

ROOT = Path(__file__).resolve().parents[1]
BASELINE_SIGS, BASELINE_GROUPS = 622, 286


def main() -> None:
    rows = list(csv.DictReader((ROOT / "data/targets/realized.csv").open()))
    prog = json.loads((ROOT / "data/processed/progress.json").read_text())

    def tc(t, r):
        return prog.get(f"{t},{r}", {}).get("teamCount", 1)

    groups = {r["t"] for r in rows if r["label"].startswith("24T")}
    realized_sigs = {(r["t"], r["r"]) for r in rows if r["label"].startswith("24T")}
    sc_rows = [r for r in rows if str(r["scoreable"]).lower() == "true"]
    sc_sigs = {(r["t"], r["r"]) for r in sc_rows}
    nonbaseline = {s for s in sc_sigs if not baseline.is_baseline(*s)}      # 1.0-eligible
    unlocks = sc_sigs - nonbaseline                                         # baseline beaten (0.5)

    # our smallest field disc per scoreable sig (disc ratio + estimated score)
    our: dict = {}
    for r in sc_rows:
        fd = r.get("field_disc")
        if fd and fd.lstrip("-").isdigit():
            key, d = (r["t"], r["r"]), abs(int(fd))
            our[key] = min(our.get(key, d), d)

    # SOLE 1.0s: we hold it AND teamCount<=1 (1 = us alone; 0 = submitted, not yet leaderboard-
    # counted). teamCount==0 means NOBODY is credited => an OPEN target, not a held 1.0 -- the old
    # "teamCount==0 held" metric measured submission LAG, which refreshes to teamCount==1 once we
    # are counted (test 0039: it read 41->0 overnight from a progress refresh). sole = k<=1.
    sole = {s for s in nonbaseline if tc(*s) <= 1}
    # estimated total score: sum 2^(1-k)*log(D0)/log(D) over held scoreable, baseline-capped at 0.5
    est = 0.0
    for s in sc_sigs:
        e = prog.get(f"{s[0]},{s[1]}", {})
        k = max(e.get("teamCount", 1), 1)
        md, d, ratio = e.get("minDisc"), our.get(s), 1.0
        if md and str(md).isdigit() and d and d > 1:
            ratio = math.log(int(md)) / math.log(d)
        sc = (2 ** (1 - k)) * ratio
        est += min(sc, 0.5 * ratio) if baseline.is_baseline(*s) else sc

    print("=== COVERAGE (distinct (t,r), the metric that scores) ===")
    print(f"  realized rows ................ {len(rows)}")
    print(f"  distinct groups .............. {len(groups)}  (baseline {BASELINE_GROUPS})")
    print(f"  scoreable signatures ......... {len(sc_sigs)}  [{len(sc_rows)} polys]")
    print(f"    non-baseline (1.0-eligible). {len(nonbaseline)}")
    print(f"    baseline unlocks (0.5) ..... {len(unlocks)}")
    print(f"  SOLE 1.0 held (non-baseline, teamCount<=1 = us alone): {len(sole)}")
    print(f"  ESTIMATED TOTAL SCORE (sum 2^(1-k)*logD0/logD, baseline-capped): {est:.1f}")

    # Tripwire: disc_source is the grader's report ('exact_nfdisc'|'mixed_disc'). 0 mixed => our
    # discs certify exact, so the absent pre-submit smoothness gate (task #15) costs nothing now.
    # If this ever exceeds 0 (a new producer emitting worse-conditioned polys), build the gate.
    mixed = sum(1 for r in rows if r.get("disc_source") == "mixed_disc")
    flag = "  <== REGRESSION: build the pre-submit smoothness gate (task #15)" if mixed else ""
    print(f"  grader mixed_disc fallbacks .. {mixed}{flag}  (0 = every disc certified exact)")

    # OPEN 1.0 targets: valid, non-baseline, NOBODY credited yet (teamCount==0), not ours
    open_1 = {(t, r) for (t, r) in baseline.valid_pairs()
              if (t, r) not in realized_sigs and not baseline.is_baseline(t, r) and tc(t, r) == 0}
    sigfill = {(t, r) for (t, r) in open_1 if t in groups}  # group already reached -> sig-fill
    print("\n=== OPEN 1.0 TARGETS (valid, non-baseline, nobody holds yet, not ours) ===")
    print(f"  total open 1.0 pairs ......... {len(open_1)}")
    print(f"  ...sig-fill reachable (group we already realize): {len(sigfill)}")
    fracs, behind = [], 0
    for (t, r), d in our.items():
        md = prog.get(f"{t},{r}", {}).get("minDisc")
        if not md or d <= 1:
            continue
        fr = math.log(int(md)) / math.log(d)  # <=1; 1.0 means we hold the global min
        fracs.append(fr)
        behind += fr < 0.999
    print("\n=== DISC-MIN HEADROOM (scoreable signatures) ===")
    print(f"  signatures with our disc + a leaderboard min: {len(fracs)}")
    print(f"  disc fraction log(minDisc)/log(ourDisc): mean {statistics.mean(fracs):.3f}  "
          f"median {statistics.median(fracs):.3f}  worst {min(fracs):.3f}")
    print(f"  someone beats our disc (headroom) ........ {behind}/{len(fracs)}")
    print(f"  we hold the min .......................... {len(fracs) - behind}/{len(fracs)}")

    lb_file = ROOT / "data/processed/leaderboard.json"
    if lb_file.exists():
        lb = json.loads(lb_file.read_text())
        name = "Team Gavin"
        items = lb.get("items", [])
        us = next((i for i in items if i.get("teamName") == name), None)
        if us:
            print("\n=== OFFICIAL LEADERBOARD (fetched by the tick) ===")
            cal = est / max(us["score"], 1)
            print(f"  rank {us['rank']} | official {us['score']:.1f} | {us['scoreablePairs']} "
                  f"pairs | our estimate {est:.1f} (x{cal:.2f} vs official)")
            for i in items:
                if abs(i["rank"] - us["rank"]) <= 2 and i["rank"] != us["rank"]:
                    d = i["score"] - us["score"]
                    print(f"  rank {i['rank']:>2} {(i.get('teamName') or i['teamNumber'])[:24]:<24}"
                          f" {i['score']:>9.1f}  ({'+' if d >= 0 else ''}{d:.1f})")



if __name__ == "__main__":
    main()
