"""search.py — deliberate search driver (engine A + target->recipe routing).

Loop: collect pending -> route frontier targets to a construction recipe -> construct
-> submit (engine, deduped + pending-logged) -> collect -> report. Resumable.

Routing (C_12-top, 12x2-block slice): the kernel is an ideal of
F_2[x]/(x^12-1) = (x+1)^4 (x^2+x+1)^4, so there are only 25 ideals. Enumerate
g = (x+1)^a (x^2+x+1)^b -> pattern w -> GAP label (forward map) => a {label: w}
table. Intersect with the untouched-solvable frontier and construct the matches via
gp.c2_split_construct (the A->w->alpha solver). This is exact deliberate routing for
that slice; broader slices await item C (non-abelian tops, size-k blocks).

Run: uv run python scripts/search.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import sympy

from igp import db, engine, gap, gp, submission

ROOT = Path(__file__).resolve().parents[1]
X = sympy.symbols("x")
MAX_CONSTRUCT = 8  # per run (demo cap)


def ideal_w(a: int, b: int):
    g = sympy.Poly((X + 1) ** a * (X**2 + X + 1) ** b, X, modulus=2)
    c = [int(t) % 2 for t in g.all_coeffs()[::-1]]  # ascending
    if len(c) > 12 or not any(c):
        return None
    return c + [0] * (12 - len(c))


def c12_routing_table() -> dict:
    """{24Tt label -> valuation pattern w} for the C_12-top, 12x2-block family."""
    tab = {}
    for a in range(5):
        for b in range(5):
            w = ideal_w(a, b)
            if w is None:
                continue
            tab.setdefault(gap.kernel_label(w, 1, 12), w)
    return tab


def untouched_solvable() -> set[str]:
    solv = {r["t"] for r in csv.DictReader(open(ROOT / "data/targets/transitive_groups_deg24.csv"))
            if r["solvable"] == "True"}
    disc = {s["t"] for s in csv.DictReader(open(ROOT / "data/targets/signatures_deg24.csv"))
            if s["discovered"] == "True"}
    return solv - disc


def main() -> None:
    print("collect (drain pending):", engine.collect())

    table = c12_routing_table()
    print(f"C_12-top routing table: {len(table)} distinct labels reachable")
    frontier = untouched_solvable()
    routable = {lab: w for lab, w in table.items() if lab[3:] in frontier}
    print(f"routable untouched targets: {len(routable)}  {sorted(routable)}")

    cands = []
    for lab, w in list(routable.items())[:MAX_CONSTRUCT]:
        coeffs = gp.c2_split_construct(w)
        if len(coeffs) == 25:
            cands.append((submission.poly_line(coeffs), f"route:{lab}"))
    sid = engine.submit(cands, description="deliberate C_12-top routing")
    print(f"constructed {len(cands)}; submitted: {sid or '(nothing new)'}")

    print("collect:", engine.collect())
    cov = db.coverage()
    nb = sum(1 for r in cov.values() if str(r.get("in_baseline")).lower() == "false")
    print(f"coverage DB: {len(cov)} (t,r), {nb} non-baseline; pending {len(db.pending_load())}")


if __name__ == "__main__":
    main()
