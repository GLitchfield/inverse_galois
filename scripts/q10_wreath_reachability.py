"""q10 — WS1 v1: is the untouched-solvable frontier reachable by our toolkit?

For a sample of untouched solvable groups, classify each via block structure
(gap.wreath_decompose_batch):
  - FULL WREATH on some block system -> reachable by G2 composition (deliberate
    recipe: realize the block group `kTi` and the top group `mTj`, then f(g(x))).
  - no full-wreath system -> a proper-kernel group => deliberate construction /
    embedding problem (WS4) — the genuinely-new-method residual.

Reports the split + which constituent groups the reachable ones need (so we know
which smaller-degree groups to be able to realize).

Run: uv run python scripts/q10_wreath_reachability.py [sample_size]
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

from igp import gap

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    sample_size = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    meta = csv.DictReader(open(ROOT / "data/targets/transitive_groups_deg24.csv"))
    solvable = {int(r["t"]) for r in meta if r["solvable"] == "True"}
    discovered = set()
    for s in csv.DictReader(open(ROOT / "data/targets/signatures_deg24.csv")):
        if s["discovered"] == "True":
            discovered.add(int(s["t"]))
    frontier = sorted(t for t in solvable if t not in discovered)
    # even stride across the (order-sorted t) list to span the order range
    stride = max(1, len(frontier) // sample_size)
    sample = frontier[::stride][:sample_size]
    print(f"untouched-solvable frontier: {len(frontier)} groups; sampling {len(sample)}")

    dec = gap.wreath_decompose_batch(sample)
    g2_reach, needs_kernel = [], []
    constituents = Counter()
    for t in sample:
        systems = dec.get(t, [])
        full = [s for s in systems if s["full_wreath"]]
        if full:
            g2_reach.append(t)
            s = full[0]
            constituents[(s["block"], s["top"])] += 1
        else:
            needs_kernel.append(t)

    n = len(sample)
    pct = lambda x: f"{len(x)}/{n} ({100*len(x)/n:.0f}%)"  # noqa: E731
    print(f"\nfull-wreath (easy G2 recipe suffices): {pct(g2_reach)}")
    print(f"proper kernel (needs deliberate construction / WS4): {pct(needs_kernel)}")

    # WS4 blueprint profile: which block structures + top-action fields dominate the frontier
    shapes, tops = Counter(), Counter()
    for t in sample:
        for s in dec.get(t, []):
            shapes[(s["k"], s["m"])] += 1
            tops[s["top"]] += 1
    print("\nblock-system shapes across the frontier sample (m blocks of size k):")
    for (k, m), c in shapes.most_common(8):
        print(f"  {m} blocks of size {k}: {c}")
    print("\nmost common top-action groups (the degree-m field WS1 builds first):")
    for top, c in tops.most_common(8):
        print(f"  {top}: {c}")
    print("\nsample WS4 targets (proper-kernel, untouched solvable):", needs_kernel[:12])


if __name__ == "__main__":
    main()
