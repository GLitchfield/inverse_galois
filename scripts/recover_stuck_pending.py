"""Recover pending submissions that engine.collect() can't reach.

collect() paginates /submissions/me newest-first and early-stops once every pending sid is seen.
When old pending sids never appear in the first ~2 pages, pagination walks deep and hits the
documented page-2+ HTTP 503, so those sids stay pending forever. Because searchd's build/submit
gate counts POLYNOMIALS across pending submissions (gated = sum(len(v)) >= max_pending), a handful
of stuck submissions (~360 polys each) can push the daemon over the threshold and freeze the whole
pipeline (built=0 sub=0), even though the submissions are already verified server-side.

This fetches each pending sid DIRECTLY by id (GET /submissions/{sid}, which works), then applies the
identical recording logic as engine.collect (verified -> realized rows + cache; failed -> cache;
remove from pending). Submissions still verifying (queuedPolynomials non-empty) are left pending.

Reproducible: `python scripts/recover_stuck_pending.py`. Idempotent (record_realized merges).
"""

from __future__ import annotations

import time

from igp import db, sair


def recover() -> dict:
    pending = db.pending_load()
    if not pending:
        return {"recovered": 0, "new_rows": 0, "failed": 0, "still_pending": 0}
    cache_new: dict = {}
    rows: list[dict] = []
    recovered = failed = 0
    for sid, items in list(pending.items()):
        try:
            it = sair._get(f"/competitions/igp24/submissions/{sid}")
        except Exception as e:  # leave pending on a transient fetch error
            print(f"  {sid}: fetch error {type(e).__name__} {str(e)[:80]}")
            continue
        if it.get("payload", {}).get("queuedPolynomials"):
            continue  # still verifying -> leave pending
        for v in it.get("verifiedPolynomials", []):
            line, source = items[v["polynomialIndex"]]
            res = {
                "label": v["label"], "t": v["t"], "r": v["r"],
                "in_baseline": v["inBaseline"], "scoreable": v.get("scoreable"),
                "field_disc": v.get("fieldDiscAbs") or v.get("scoringDiscAbs") or "",
                "disc_source": v.get("discSource") or "",
            }
            cache_new[line] = res
            rows.append({**res, "source": source, "coeffs": line})
        for v in it.get("failedPolynomials", []):
            idx = v.get("polynomialIndex")
            if idx is None or idx >= len(items):
                continue
            cache_new[items[idx][0]] = {"label": None, "failed": True}
            failed += 1
        db.pending_remove(sid)
        recovered += 1
        time.sleep(0.3)
    if cache_new:
        db.cache_update(cache_new)
    if rows:
        db.record_realized(rows)
    return {"recovered": recovered, "new_rows": len(rows), "failed": failed,
            "still_pending": len(db.pending_load())}


if __name__ == "__main__":
    print(recover())
