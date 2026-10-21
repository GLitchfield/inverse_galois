"""Shape atlas — the empirical (construction shape -> observed 24Tt labels) map.

The pipeline stage that closes the targeting loop (2026-07-04): every verified queue row carries
its provenance tag and its Magma label, so we KNOW which shapes hit which groups — no group-theory
prediction needed (GAP identification of the order-1e17 wreaths times out; Magma already told us).
Producers query it to (a) skip shapes whose reachable groups carry no open value, (b) keep a
per-shape exploration quota for shapes never seen, (c) concentrate on shapes that hit open pairs.

A "shape key" drops the per-candidate variation (base disc, split prime, pattern index) and keeps
what determines the group family, e.g. ``compose:2x12:12T105:o3`` -> ``compose:2x12:12T105``.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

from . import baseline
from . import searchstore as store

_ROOT = Path(__file__).resolve().parents[2]

_DROP = ("d", "q", "p", "s")   # tag segments that vary per candidate: disc, prime, pattern, sel


def shape_key(target: str) -> str:
    parts = (target or "").split(":")
    keep = [parts[0]]
    for seg in parts[1:]:
        if seg and seg[0] in _DROP and seg[1:].lstrip("-").isdigit():
            continue
        keep.append(seg)
    return ":".join(keep)


def observed(prefix: str = "") -> dict:
    """{shape_key: {24Tt_int: count}} over all verified rows (Magma ground truth)."""
    out: dict = defaultdict(lambda: defaultdict(int))
    with sqlite3.connect(store.DB) as c:
        q = "SELECT target, label FROM queue WHERE label IS NOT NULL AND target LIKE ?"
        for tgt, lab in c.execute(q, (prefix + "%",)):
            if lab and lab.startswith("24T"):
                out[shape_key(tgt)][int(lab[3:])] += 1
    return {k: dict(v) for k, v in out.items()}


def erosion_weights(progress: dict) -> dict:
    """{minblk_stratum: survival weight in [0.15, 1]} via a per-stratum scalar Kalman filter over
    the whole progress-snapshot archive.

    State = the stratum's daily claim rate (random walk, process noise Q lets it drift ~5%/day to
    track rival regime changes); each snapshot interval contributes an observation claimed/opens
    scaled to a daily rate, with measurement variance from the BINOMIAL counting statistics — so a
    49-pair stratum's noisy window barely moves the estimate while a 60k-pair stratum's moves it
    decisively (the single-interval point estimate this replaces flapped on small strata). Weight =
    3-day survival at a half-sigma-pessimistic rate. Falls back to {} (all-1.0) without >=1
    archived snapshot."""
    try:
        arch = sorted((_ROOT / "data" / "processed" / "progress_archive").glob("progress_*.json"))
        if not arch:
            return {}
        import re as _re
        import time as _time

        def stamp(f):
            m = _re.search(r"(\d{8})_(\d{4})", f.name)
            return _time.mktime(_time.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M"))

        minblk = {int(a): int(b) for a, b in
                  (ln.split(",") for ln in
                   (_ROOT / "data" / "targets" / "block_structure_deg24.csv")
                   .read_text().splitlines()[1:] if ln)}
        prog_path = _ROOT / "data" / "processed" / "progress.json"
        seq = [(stamp(f), json.loads(f.read_text())) for f in arch[-6:]]
        seq.append((prog_path.stat().st_mtime, progress))
        Q_DAILY = 0.05 ** 2          # rate may drift ~5%/day (regime changes)
        est: dict = {}               # stratum -> [x, P]
        for (t0, old_p), (t1, new_p) in zip(seq, seq[1:]):
            dt_days = max((t1 - t0) / 86400.0, 0.02)
            opens: dict = defaultdict(int)
            claimed: dict = defaultdict(int)
            for k, ov in old_p.items():
                if (ov.get("teamCount") or 0) == 0:
                    st = minblk.get(int(k.split(",")[0]), -1)
                    opens[st] += 1
                    nv = new_p.get(k) or {}
                    if (nv.get("teamCount") or 0) > 0:
                        claimed[st] += 1
            for st, n in opens.items():
                frac = claimed.get(st, 0) / n
                z = frac / dt_days                              # observed daily rate
                r_var = max(frac * (1 - frac), 1e-6) / n / (dt_days ** 2)
                x, pv = est.get(st, (z, 1.0))                   # diffuse prior on first sight
                pv += Q_DAILY * dt_days                         # predict
                gain = pv / (pv + r_var)                        # update
                x += gain * (z - x)
                pv *= (1 - gain)
                est[st] = (x, pv)
        out = {}
        for st, (x, pv) in est.items():
            pess = min(max(x + 0.5 * pv ** 0.5, 0.0), 0.95)     # half-sigma pessimistic rate
            out[st] = max(0.15, (1.0 - pess) ** 3)
        return out
    except Exception:
        return {}


def open_value(progress: dict, held: set) -> dict:
    """{t: erosion-weighted open-or-steal value} — valid, non-baseline, unheld, teamCount<=1,
    each pair discounted by its stratum's measured 3-day survival probability."""
    ew = erosion_weights(progress)
    minblk: dict = {}
    if ew:
        try:
            minblk = {int(a): int(b) for a, b in
                      (ln.split(",") for ln in
                       (_ROOT / "data" / "targets" / "block_structure_deg24.csv")
                       .read_text().splitlines()[1:] if ln)}
        except Exception:
            ew = {}
    val: dict = defaultdict(float)
    for t, r in ((int(a), int(b)) for a, b in baseline.valid_pairs()):
        if (t, r) in held or baseline.is_baseline(t, r):
            continue
        e = progress.get(f"{t},{r}")
        if e is not None and e.get("teamCount", 9) <= 1:
            val[t] += ew.get(minblk.get(t, -1), 1.0) if ew else 1.0
    return dict(val)


def classify(progress: dict, held: set, prefix: str = "") -> dict:
    """Per shape: {'labels': {...}, 'open_pairs': n} — a producer skips shapes with known labels
    and 0 open pairs, explores unknown shapes, and concentrates where open_pairs > 0."""
    obs = observed(prefix)
    val = open_value(progress, held)
    return {k: {"labels": labs, "open_pairs": sum(val.get(t, 0) for t in labs)}
            for k, labs in obs.items()}
