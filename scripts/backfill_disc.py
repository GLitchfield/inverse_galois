"""Backfill blank field_disc for scoreable realized rows via local PARI/GP nfdisc (review / 0031).

~97 scoreable rows had blank field_disc (older schema + the old setdefault never updating). Now that
record_realized merges, compute the field disc locally and fill the blanks. Skips rows flagged
disc_source=mixed_disc (the API genuinely has no numeric disc there). Pause the daemon first so it
isn't writing realized.csv concurrently.

Run: uv run python scripts/backfill_disc.py
"""

from __future__ import annotations

from igp import db, gp


def main() -> None:
    blanks = [r for r in db.load_realized()
              if str(r.get("scoreable")).lower() == "true"
              and not r.get("field_disc") and r.get("coeffs")
              and str(r.get("disc_source", "")) != "mixed_disc"]
    print(f"backfilling {len(blanks)} blank-disc scoreable rows via nfdisc...", flush=True)
    updates, fails = [], 0
    for i, r in enumerate(blanks):
        try:
            d = gp.nfdisc([int(x) for x in r["coeffs"].split(",")])
        except Exception as e:
            fails += 1
            print(f"  [{i}] {r['label']} nfdisc failed: {str(e)[:50]}", flush=True)
            continue
        updates.append({**r, "field_disc": str(abs(int(d))), "disc_source": "field"})
    if updates:
        db.record_realized(updates)  # merge fills the blanks
    print(f"done: filled {len(updates)}, failed {fails}", flush=True)


if __name__ == "__main__":
    main()
