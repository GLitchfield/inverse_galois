"""Re-sync stale local `scoreable` flags from SAIR (P0 review 2026-07-11).

SAIR scores discriminants ASYNC: a poly verifies (accepted, labeled 24Tt/r) with
scoringStatus=pending -> scoreable=false, then flips to scored later. engine.collect records the
false and pending_removes the sid, so the flip is never re-fetched -> local scoreable UNDERCOUNTS
official (reconcile_accounting: local 22,087 vs official 24,670 = -2,583 pairs).

This re-fetches our submissions (recent /me pages, then the sid ledger + current pending by-id), and
for any poly now scored but not yet locally scoreable, downloads its line and authoritatively
upgrades the realized.csv row (record_realized only fills blanks -> use db.upgrade_scoreable).

NOT lost score (official already credits it) -- this un-stales LOCAL ranking/coverage/defense only.
Coverage is bounded: pre-2026-07-11 submissions have no logged sid and /me 503s past ~300,
so an old scored-but-stale pair may be unreachable until the ledger accumulates. Idempotent.

Run: uv run python scripts/resync_scoreable.py [--max N]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from igp import db, sair  # noqa: E402


def _scored(v: dict) -> bool:
    return str(v.get("scoreable")).lower() == "true" or v.get("scoringStatus") == "scored"


def resync(max_subs: int = 400) -> dict:
    """Re-fetch our submissions and authoritatively upgrade any locally-stale scoreable flags.
    Returns a summary dict (also the callable the tick uses). Idempotent; fail-soft on SairError."""
    results: dict = {}
    try:  # recent submissions come with verifiedPolynomials inline (no extra call)
        for it in sair.iter_submissions("igp24"):
            results[it["submissionId"]] = it
            if len(results) >= max_subs:
                break
    except sair.SairError:
        pass
    for sid in list(dict.fromkeys(db.load_sids() + list(db.pending_load()))):
        if sid in results or len(results) >= max_subs:
            continue
        try:
            results[sid] = sair.submission_by_id(sid)
        except sair.SairError:
            continue

    already = {r["coeffs"] for r in db.load_realized()
               if str(r.get("scoreable")).lower() == "true" and r.get("coeffs")}
    updates: dict = {}
    downloaded = 0
    for sid, sub in results.items():
        scored = [v for v in sub.get("verifiedPolynomials", []) if _scored(v)]
        if not scored:
            continue
        try:
            lines = sair.download_submission(sid)
        except sair.SairError:
            continue
        downloaded += 1
        for v in scored:
            idx = v.get("polynomialIndex")
            if idx is None or idx >= len(lines) or lines[idx] in already:
                continue
            updates[lines[idx]] = {
                "label": v.get("label"), "t": v.get("t"), "r": v.get("r"), "scoreable": "true",
                "field_disc": v.get("fieldDiscAbs") or v.get("scoringDiscAbs"),
                "disc_source": v.get("discSource") or "",
            }
    changed = db.upgrade_scoreable(updates) if updates else 0
    return {"fetched": len(results), "downloaded": downloaded,
            "stale": len(updates), "upgraded": changed}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=400, help="cap submissions re-fetched")
    args = ap.parse_args()
    s = resync(args.max)
    print(f"resync: {s['fetched']} submissions fetched, {s['downloaded']} downloaded, "
          f"{s['stale']} scored lines not-yet-local-scoreable, {s['upgraded']} rows upgraded")


if __name__ == "__main__":
    main()
