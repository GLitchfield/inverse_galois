"""Pipeline invariant checker — make the next silent bug loud (2026-07-04).

Generic assertions over the stores; both silent-loss incidents this week (the [:100] submit
truncation, the 243k zombie rows) would have tripped these within a cycle. Run by the daily audit
and on demand: uv run python scripts/check_invariants.py  (exit 1 on violations).
"""

from __future__ import annotations

import json
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

from igp import db
from igp import searchstore as store

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    bad: list[str] = []
    now = time.time()

    with sqlite3.connect(store.DB) as c:
        # I1 (REVISED 2026-07-11): 'submitted' is a TERMINAL queue status -- collect records results
        # into realized.csv via the SEPARATE pending store and never syncs the queue row back to
        # 'verified'. So old 'submitted' rows accumulate forever and are NOT a zombie signal (the
        # old I1 false-alarmed on this; recover_stuck_pending confirmed 0 lost score). The REAL
        # uncollected signal is the PENDING backlog (I3). We keep an informational count only.
        submitted = c.execute("SELECT COUNT(*) FROM queue WHERE status='submitted'").fetchone()[0]
        # I2: 'building' rows older than 2h = daemon crash leftovers
        n = c.execute("SELECT COUNT(*) FROM queue WHERE status='building' AND updated < ?",
                      (now - 2 * 3600,)).fetchone()[0]
        if n:
            bad.append(f"I2: {n} rows stuck in 'building' >2h (orphaned in-flight)")

    # I3: THE real uncollected/zombie tripwire -- pending submissions must collect promptly; a deep
    # backlog means collect is broken and score is genuinely stranded server-side. Run
    # recover_stuck_pending.py to clear.
    stale = {sid: len(v) for sid, v in db.pending_load().items()}
    if len(stale) > 8:
        bad.append(f"I3: {len(stale)} submissions pending, {sum(stale.values())} polys "
                   "(verifier backlog or collect broken -- run recover_stuck_pending.py)")

    # I4: realized.csv — no duplicate coeffs rows (append-mode integrity)
    rows = db.load_realized()
    lines = [r["coeffs"] for r in rows if r.get("coeffs")]
    dup = len(lines) - len(set(lines))
    if dup:
        bad.append(f"I4: {dup} duplicate coeffs rows in realized.csv (append-path corruption)")

    # I5: coverage trajectory must be non-decreasing in groups/scoreable
    hist = ROOT / "data" / "processed" / "coverage_history.jsonl"
    if hist.exists():
        prev_g = prev_s = 0
        drops = 0
        for ln in hist.read_text().splitlines():
            if not ln.strip():
                continue
            p = json.loads(ln)
            if p["groups"] < prev_g or p["scoreable"] < prev_s:
                drops += 1
            prev_g, prev_s = p["groups"], p["scoreable"]
        if drops:
            bad.append(f"I5: coverage trajectory decreased {drops}x (CSV corruption?)")

    # I6: progress.json staleness
    prog = ROOT / "data" / "processed" / "progress.json"
    if prog.exists() and now - prog.stat().st_mtime > 26 * 3600:
        bad.append(f"I6: progress.json is {(now - prog.stat().st_mtime) / 3600:.0f}h stale")

    # I7: grader fallback tripwire (mirrors the scoreboard line)
    mixed = sum(1 for r in rows if r.get("disc_source") == "mixed_disc")
    if mixed:
        bad.append(f"I7: {mixed} mixed_disc rows — build the smoothness gate (task #15)")

    # informational: failure taxonomy snapshot
    tax = Counter()
    for kind, detail, n in store.failure_taxonomy():
        tax[f"{kind}/{detail}"] = n
    top = ", ".join(f"{k}={v}" for k, v in tax.most_common(5))

    if bad:
        print("INVARIANT VIOLATIONS:")
        for b in bad:
            print(f"  {b}")
    else:
        print("all invariants hold")
    print(f"info: {submitted} terminal 'submitted' queue rows (not a zombie signal; see I1 note), "
          f"{len(stale)} pending")
    print(f"failure taxonomy (top): {top}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
