"""Coverage snapshot — the distinct-(t,r) scoring metrics from realized.csv.

Shared by the daemon's per-cycle coverage logger and (potentially) the scoreboard. Reports the
units that actually score: distinct groups, distinct scoreable signatures, SOLE 1.0s (held &
non-baseline & teamCount<=1 = us alone), and an estimated total score (sum 2^(1-k)*logD0/logD,
baseline-capped). ``progress`` (parsed progress.json) is needed for sole + est; else those are None.
When the tick's leaderboard snapshot is fresh (<2h), the OFFICIAL score + rank ride along too.
"""
from __future__ import annotations

import csv
import json
import math
import time
from pathlib import Path

from . import baseline, db

BEST_CACHE = Path(__file__).resolve().parents[2] / "data" / "processed" / "best_by_pair.csv"
BEST_FIELDS = ["t", "r", "label", "scoring_disc", "disc_source", "exact", "source", "coeffs"]


def snapshot(progress: dict | None = None) -> dict:
    rows = db.load_realized()
    groups = {r["t"] for r in rows if r.get("label", "").startswith("24T")}
    best: dict = {}   # (t,r) -> smallest field disc
    sc_sigs: set = set()
    for r in rows:
        if str(r.get("scoreable")).lower() != "true" or not r.get("label", "").startswith("24T"):
            continue
        key = (r["t"], r["r"])
        sc_sigs.add(key)
        fd = r.get("field_disc")
        if fd and str(fd).lstrip("-").isdigit():
            d = abs(int(fd))
            best[key] = min(best.get(key, d), d)
    snap = {"groups": len(groups), "scoreable": len(sc_sigs), "sole": None, "est": None}
    _official(snap)
    if not progress:
        return snap
    sole = 0
    est = 0.0
    for s in sc_sigs:
        e = progress.get(f"{s[0]},{s[1]}", {})
        k = max(e.get("teamCount", 1), 1)
        md, d, ratio = e.get("minDisc"), best.get(s), 1.0
        if md and str(md).isdigit() and d and d > 1:
            ratio = math.log(int(md)) / math.log(d)
        sc = (2 ** (1 - k)) * ratio
        is_base = baseline.is_baseline(*s)
        est += min(sc, 0.5 * ratio) if is_base else sc
        if not is_base and e.get("teamCount", 1) <= 1:
            sole += 1
    snap["sole"] = sole
    snap["est"] = round(est, 1)
    return snap


def _official(snap: dict) -> None:
    """Attach the official score + rank from the tick-cached leaderboard when fresh (<2h)."""
    try:
        lb = Path(__file__).resolve().parents[2] / "data" / "processed" / "leaderboard.json"
        d = json.loads(lb.read_text())
        if time.time() - d.get("t", 0) < 7200:
            us = next((i for i in d.get("items", []) if i.get("teamName") == "Team Gavin"), None)
            if us:
                snap["official"] = round(us["score"], 1)
                snap["rank"] = us["rank"]
    except Exception:
        pass


def exp_score(t: str, r: str, disc: int | None, prog: dict) -> float:
    """Expected points for one (t,r): 2^(1-k)*log(minDisc)/log(ourDisc), baseline-capped at 0.5."""
    e = prog.get(f"{t},{r}", {})
    k = e.get("teamCount", 0) or 0
    md = e.get("minDisc")
    factor = 1.0
    if md and str(md).isdigit() and disc and disc > 1:
        factor = math.log(int(md)) / math.log(disc)
    score = (2 ** (1 - k)) * factor
    if baseline.is_baseline(t, r):
        score = min(score, 0.5 * factor)
    return score


def best_by_pair(rows=None) -> dict:
    """The ONE canonical 'best submittable model per (t,r)' selection, used by submission builder,
    reconciliation, and the producer-value report (project review 2026-07-11). Prefer
    disc_source=exact_nfdisc over mixed; among same exactness, smallest scoring disc. Baseline pairs
    require an exact nfdisc strictly < D_base (mixed can't unlock them). Returns
    {(t,r): {disc, label, line, source, disc_source, exact}}."""
    if rows is None:
        rows = db.load_realized()
    best: dict = {}
    for row in rows:
        if str(row.get("scoreable")).lower() != "true" or not row.get("coeffs"):
            continue
        fd = row.get("field_disc") or ""
        if not fd.lstrip("-").isdigit():
            continue
        t, r, d = row["t"], row["r"], abs(int(fd))
        exact = (row.get("disc_source") or "") == "exact_nfdisc"
        if baseline.is_baseline(t, r) and not (exact and baseline.beats_baseline(t, r, d)):
            continue
        cand = {"disc": d, "label": row.get("label", f"24T{t}"), "line": row["coeffs"],
                "source": row.get("source", ""), "disc_source": row.get("disc_source") or "",
                "exact": exact}
        cur = best.get((t, r))
        if cur is None or (cand["exact"], -cand["disc"]) > (cur["exact"], -cur["disc"]):
            best[(t, r)] = cand
    return best


def write_cache(best: dict | None = None, path: Path = BEST_CACHE) -> int:
    """Materialize the compact best-by-pair table to CSV (~24k rows vs realized.csv's ~1.5M)."""
    if best is None:
        best = best_by_pair()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=BEST_FIELDS)
        w.writeheader()
        for (t, r), b in sorted(best.items(), key=lambda kv: (int(kv[0][0]), int(kv[0][1]))):
            w.writerow({"t": t, "r": r, "label": b["label"], "scoring_disc": b["disc"],
                        "disc_source": b["disc_source"], "exact": b["exact"],
                        "source": b["source"], "coeffs": b["line"]})
    return len(best)


def load_cache(path: Path = BEST_CACHE) -> list[dict]:
    """Load the compact table (fast). Empty list if not yet generated (call write_cache)."""
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh))
