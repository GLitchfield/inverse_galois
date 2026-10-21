"""q01 — build the degree-24 transitive-group target index from GAP.

Writes data/targets/transitive_groups_deg24.csv (one row per 24Tt group) and
prints summary counts to validate against the survey figures (24,193 solvable /
807 non-solvable / 5 primitive; landscape_survey.md).

Run: uv run python scripts/q01_build_target_index.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from igp import gap

FIELDS = ["t", "label", "order", "solvable", "primitive", "transitivity", "in_an"]
OUT = Path(__file__).resolve().parents[1] / "data" / "targets" / "transitive_groups_deg24.csv"


def main() -> None:
    rows = gap.all_transitive_group_info(24)
    assert len(rows) == 25000, f"expected 25000 groups, got {len(rows)}"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in FIELDS})

    n_solv = sum(r["solvable"] for r in rows)
    n_prim = sum(r["primitive"] for r in rows)
    n_an = sum(r["in_an"] for r in rows)
    print(f"wrote {len(rows)} rows -> {OUT.relative_to(OUT.parents[2])}")
    print(f"solvable={n_solv}  non-solvable={len(rows) - n_solv}  "
          f"primitive={n_prim}  in_A24={n_an}")


if __name__ == "__main__":
    main()
