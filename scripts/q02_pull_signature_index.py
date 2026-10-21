"""q02 — pull the authoritative (t, r) signature index + leaderboard state from SAIR.

Paginates /competitions/igp24/labels/progress (all 25,000 groups), saves the raw
JSON to data/raw/, and writes data/targets/signatures_deg24.csv (one row per
achievable (t, r) signature: allowedR membership, discovered flag, team count,
current minimum |disc|). Prints coverage summary to validate against the survey
(165,836 achievable signatures; 286/622 baseline).

Run: uv run python scripts/q02_pull_signature_index.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from igp import sair

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "sair_igp24_labels_progress_full.json"
OUT = ROOT / "data" / "targets" / "signatures_deg24.csv"
FIELDS = ["t", "label", "r", "discovered", "team_count", "min_disc_abs"]


def main() -> None:
    labels = list(sair.labels_progress("igp24", limit=500))
    print(f"pulled {len(labels)} labels")

    RAW.write_text(json.dumps(labels))

    rows = []
    for lab in labels:
        t, label = lab["t"], lab["label"]
        sig_by_r = {s["r"]: s for s in lab.get("signatures", [])}
        for r in lab["allowedR"]:
            s = sig_by_r.get(r, {})
            rows.append(
                {
                    "t": t,
                    "label": label,
                    "r": r,
                    "discovered": bool(s.get("discovered", False)),
                    "team_count": s.get("teamCount", 0),
                    "min_disc_abs": s.get("minimumDiscAbs"),
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    n_groups = len(labels)
    n_sigs = len(rows)
    n_disc = sum(r["discovered"] for r in rows)
    n_have_disc = sum(1 for r in rows if r["min_disc_abs"] is not None)
    groups_with_disc = len({r["t"] for r in rows if r["discovered"]})
    groups_with_min = len({r["t"] for r in rows if r["min_disc_abs"] is not None})
    print(f"wrote {n_sigs} signature rows -> {OUT.relative_to(ROOT)}")
    print(f"groups={n_groups}  achievable (t,r)={n_sigs}  (survey says 165,836)")
    print(f"discovered signatures={n_disc} across {groups_with_disc} groups")
    print(f"signatures with a known min |disc|={n_have_disc} across {groups_with_min} groups")


if __name__ == "__main__":
    main()
