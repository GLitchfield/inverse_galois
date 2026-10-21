"""Backfill blank field_disc on scoreable realized rows.

A row is written scoreable-but-blank-disc when SAIR verifies the label but its
response carries no numeric disc at collect time (disc pending, or a mixed-disc
fallback that later resolves) AND we `pending_remove` the submission so it is
never re-fetched. The scoring disc is `nfdisc`, so we recompute it locally under
a time budget matching the grader's: `scoreable_disc` fills the disc iff `nfdisc`
completes in-budget -- which is exactly the condition under which SAIR itself
scores the poly exactly. Rows whose disc genuinely times out stay blank (SAIR
mixed-discs them too), so this never records an optimistic disc.

Reproducible: reads `realized.csv`, upgrades in place via the merge path (which
upgrades blanks, never downgrades). Idempotent.
"""

from __future__ import annotations

import argparse

from igp import db, gp


def blank_scoreable_rows(rows: list[dict]) -> list[dict]:
    return [
        r for r in rows
        if str(r.get("scoreable")).lower() == "true"
        and not (r.get("field_disc") or "").strip()
        and (r.get("coeffs") or "").strip()
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=55, help="per-poly nfdisc seconds")
    ap.add_argument("--limit", type=int, default=0, help="max rows (0 = all)")
    args = ap.parse_args()

    rows = db.load_realized()
    blanks = blank_scoreable_rows(rows)
    # one poly per distinct coeff line is enough; the merge propagates to duplicates
    seen: dict[str, dict] = {}
    for r in blanks:
        seen.setdefault(r["coeffs"], r)
    todo = list(seen.values())
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(blanks)} blank-disc scoreable rows, {len(todo)} distinct polys to compute")

    filled, timed_out = 0, 0
    upgrades: list[dict] = []
    for i, r in enumerate(todo, 1):
        coeffs = [int(x) for x in r["coeffs"].split(",")]
        try:
            d = gp.scoreable_disc(coeffs, budget=args.budget)
        except gp.CASError:
            d = None
        if d is None:
            timed_out += 1
            continue
        upgrades.append({**r, "field_disc": str(abs(d)),
                         "disc_source": r.get("disc_source") or "local_nfdisc"})
        filled += 1
        print(f"  [{i}/{len(todo)}] {r['label']} r{r['r']}: filled ({abs(d).bit_length()} bits)")

    if upgrades:
        db.record_realized(upgrades)
    print(f"done: {filled} filled, {timed_out} genuinely time out (SAIR mixed-discs these too)")


if __name__ == "__main__":
    main()
