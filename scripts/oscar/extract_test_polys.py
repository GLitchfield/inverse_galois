"""Select diverse ground-truth degree-24 polynomials for the OSCAR verifier spike (test 0026).

Picks distinct-label rows from data/targets/realized.csv (preferring scoreable ones, whose 24Tt
came from SAIR-Magma verification), spread evenly across t, and emits a Julia data file:

    const POLYS = [("24Tt", [c0, c1, ..., c24]), ...]   # coeffs ascending

Usage:  uv run python scripts/oscar/extract_test_polys.py [N] > scripts/oscar/test_polys.jl

The committed scripts/oscar/test_polys.jl is the *pinned* set actually used in 0026 (realized.csv
grows, so re-running yields a different spread; the pinned file keeps the test reproducible).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REALIZED = Path(__file__).resolve().parents[2] / "data" / "targets" / "realized.csv"


def main(n: int = 12) -> None:
    rows = [r for r in csv.DictReader(REALIZED.open())
            if r.get("coeffs") and r.get("label", "").startswith("24T")]
    seen: dict[str, dict] = {}
    for r in rows:  # prefer a scoreable representative per label
        lab = r["label"]
        if lab not in seen or str(r.get("scoreable")).lower() == "true":
            seen[lab] = r
    items = sorted(seen.values(), key=lambda r: int(r["label"][3:]))
    pick = items[:: max(1, len(items) // n)][:n]
    print("const POLYS = [")
    for r in pick:
        coeffs = ",".join(str(int(x.strip())) for x in r["coeffs"].split(","))
        print(f'  ("{r["label"]}", [{coeffs}]),')
    print("]")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
