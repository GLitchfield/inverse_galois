"""Generate the compact best-by-pair table (project review 2026-07-11).

realized.csv is the append-only provenance log (~1.5M rows / 296MB, ~49 rows per scoreable
signature). This materializes ONE best model per (t,r) -> data/processed/best_by_pair.csv, so
ranking / submission / score analysis load ~24k rows instead of churning the 296MB CSV. The raw log
stays the source of truth + provenance; regenerate this after a batch of new results.

Run: uv run python scripts/build_best_by_pair.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from igp import coverage  # noqa: E402


def main() -> None:
    best = coverage.best_by_pair()
    n = coverage.write_cache(best)
    ex = sum(1 for b in best.values() if b["exact"])
    print(f"best_by_pair: {n} pairs ({ex} exact / {n - ex} mixed) -> {coverage.BEST_CACHE}")


if __name__ == "__main__":
    main()
