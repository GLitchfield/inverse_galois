"""Adaptive ranking for the search daemon: a producer BANDIT + a per-row SURROGATE.

The daemon claims queued rows by ``priority`` (highest first). This module sets that priority:

- **Bandit (per-producer):** each producer (identified by the target prefix) is an arm; its
  reward is its scoreable/sole rate among verified rows. UCB1 turns rates + counts into a weight
  that favours productive producers while still exploring thin ones.
- **Surrogate (per-row):** a gradient-boosted classifier trained on our verified constructions
  (features: producer, base degree, kernel weight, log prime) predicting P(scoreable); it refines
  priority WITHIN a producer (which base/kernel/prime to build first).

priority = bandit_weight(producer) * (1 + surrogate_score(row)). Computed by the tick (not daemon
loop), so the daemon stays light. Both degrade gracefully (no data / no sklearn => bandit-only,
or uniform).
"""

from __future__ import annotations

import math

from . import baseline, db
from . import searchstore as store

# target-prefix -> producer name (None target = the exact-Galois `produce`, labelled "exact")
PREFIXES = ["spec", "comp", "gen12treal", "gen12", "abelian", "m24", "size4", "g6x4", "lmfdb6x4",
            "tri",
            "discmin", "discmin2", "sigfill", "nflist", "tsig", "size3", "g6x3", "c8x3", "quad",
            "pent", "g8x3s3", "g6x4s4", "lit", "monster", "compose", "lift", "selfc", "harden",
            "mb2", "basemin", "rfill"]


def producer_of(target: str | None) -> str:
    if not target:
        return "exact"
    head = target.split(":", 1)[0]
    if head in PREFIXES:
        return head
    if head.startswith("24T"):
        return "exact"
    return "manual"  # historical / hand-run sources collapse to one arm (not per-construction)


def producer_of_source(source: str | None) -> str:
    """Producer from a realized.csv `source` (daemon rows are `daemon:<target>`; manual rows keep
    their own tag)."""
    if not source:
        return "exact"
    return producer_of(source.split("daemon:", 1)[-1])


def _scoreable_lines() -> set:
    return {r["coeffs"] for r in db.load_realized()
            if str(r.get("scoreable")).lower() == "true" and r.get("coeffs")}


def producer_stats(progress: dict) -> dict:
    """Per-producer marginal-value stats from realized.csv, keyed by the ACTUAL `(t,r)`.

    Rewards DISTINCT `(t,r)` coverage, not duplicate rows: ``rows`` = builds attributed, ``sigs`` =
    distinct scoreable signatures, ``sole`` = distinct signatures whose real `(t,r)` has
    teamCount==0. So a sparse flood that re-hits held signatures is correctly down-weighted vs a
    producer with high distinct-sig yield. (Fixes test 0029/0031: rows != signatures, and the old
    sole check used `(t,0)` regardless of the row's real `r`.)
    """
    acc: dict = {}
    for r in db.load_realized():
        if not r.get("label", "").startswith("24T"):
            continue
        s = acc.setdefault(producer_of_source(r.get("source")),
                           {"rows": 0, "sigs": set(), "sole": set()})
        s["rows"] += 1
        if str(r.get("scoreable")).lower() == "true":
            sig = (r["t"], r["r"])
            s["sigs"].add(sig)
            # sole 1.0: non-baseline (baseline caps at 0.5) AND we're the only team. teamCount<=1
            # (1 = us; 0 = submitted but not yet leaderboard-counted -- the lag). teamCount==0 does
            # NOT mean sole-us: it means nobody is credited (test 0039 fixed the ==0 misread).
            if (progress.get(f"{r['t']},{r['r']}", {}).get("teamCount", 1) <= 1
                    and not baseline.is_baseline(r["t"], r["r"])):
                s["sole"].add(sig)
    return {p: {"rows": s["rows"], "sigs": len(s["sigs"]), "sole": len(s["sole"])}
            for p, s in acc.items()}


def bandit_weights(stats: dict, c: float = 0.7, sole_weight: float = 2.0) -> dict:
    """UCB1 over producers rewarding DISTINCT-`(t,r)` value per build, not rows.

    reward = (distinct scoreable sigs + sole_weight * sole sigs) / rows — a producer that re-hits
    held signatures (high duplication, e.g. the sparse flood) is down-weighted vs one with high
    distinct-sig yield; sole sigs (actual teamCount==0, ~1.0 each) count extra. The UCB explore
    bonus still favours thin/new arms. See docs/tests/0031.
    """
    total = sum(s["rows"] for s in stats.values()) or 1
    out = {}
    for p, s in stats.items():
        rows = max(s["rows"], 1)
        reward = (s["sigs"] + sole_weight * s["sole"]) / rows
        out[p] = reward + c * math.sqrt(math.log(total + 1) / rows)
    return out


def _features(kind: str, payload: dict) -> list:
    """Numeric features for one construction (producer-agnostic)."""
    base = payload.get("base") or []
    deg = (len(base) - 1) if base else payload.get("n", 0)
    w = payload.get("w") or []
    weight = sum(w) if w else (sum(payload.get("w1", [])) + sum(payload.get("w2", [])))
    if "pairs" in payload:
        weight = sum(sum(x[1]) for x in payload["pairs"])
    q = payload.get("q", 0)
    base_mag = math.log(max((abs(c) for c in base), default=1) + 1)  # base-field size proxy
    return [deg, weight, math.log(q + 1), base_mag]


def _disc_by_line() -> dict:
    """{poly line -> log10(|field_disc|)} from realized.csv (disc-surrogate labels)."""
    out = {}
    for r in db.load_realized():
        if r.get("coeffs") and r.get("field_disc"):
            d = abs(int(r["field_disc"]))
            out[r["coeffs"]] = math.log10(d) if d > 1 else 0.0
    return out


def train_disc_surrogate():
    """Regress log10(field disc) on construction features. Returns (model, kinds) or None.

    Smaller predicted disc => more likely to beat the leaderboard min => scoreable; used both as a
    priority bonus and (implicitly) a quality signal. Cheap proxy for the 60s nfdisc.
    """
    try:
        from sklearn.ensemble import GradientBoostingRegressor
    except Exception:
        return None
    disc = _disc_by_line()
    rows = [r for r in store.verified_rows() if r.get("line") in disc]
    if len(rows) < 40:
        return None
    kinds = sorted({r["kind"] for r in rows})
    X = [_features(r["kind"], r["payload"]) + [1 if r["kind"] == k else 0 for k in kinds]
         for r in rows]
    y = [disc[r["line"]] for r in rows]
    model = GradientBoostingRegressor(n_estimators=60, max_depth=3, random_state=0)
    model.fit(X, y)
    return model, kinds, (min(y), max(y))


def train_surrogate(progress: dict):
    """Train P(scoreable) on verified rows. Returns (model, kinds) or None if too little data."""
    try:
        from sklearn.ensemble import GradientBoostingClassifier
    except Exception:
        return None
    sc_lines = _scoreable_lines()
    rows = store.verified_rows()
    if len(rows) < 40:
        return None
    kinds = sorted({r["kind"] for r in rows})
    X, y = [], []
    for r in rows:
        onehot = [1 if r["kind"] == k else 0 for k in kinds]
        X.append(_features(r["kind"], r["payload"]) + onehot)
        y.append(1 if r.get("line") in sc_lines else 0)
    if len(set(y)) < 2:
        return None
    model = GradientBoostingClassifier(n_estimators=60, max_depth=3, random_state=0)
    model.fit(X, y)
    return model, kinds


def apply_ranking(progress: dict) -> dict:
    """Set queue priorities: bandit (per-producer) + surrogate (per-row). Returns a summary."""
    stats = producer_stats(progress)
    weights = bandit_weights(stats)
    base = weights.get("exact", 0.0)
    for p, w in weights.items():
        store.set_priority_prefix("" if p == "exact" else p, w)
    # Portfolio quota (2026-07-04): claim-time shares from bandit weights, CAPPED at 40% so no
    # producer silently dominates the submitted mix, with a 2% exploration floor for every
    # producer that still has queued rows. searchstore.claim consumes this.
    import sqlite3 as _sq
    with _sq.connect(store.DB) as _c:
        quota = {}
        for p_ in PREFIXES:
            nq = _c.execute("SELECT COUNT(*) FROM queue WHERE status='queued' AND target LIKE ?",
                            (p_ + ":%",)).fetchone()[0]
            if nq:
                quota[p_ + ":"] = max(weights.get(p_, 0.0), 0.02)
        if quota and not store.get_kv("quota_locked", False):
            for _ in range(2):  # cap POST-normalization shares at 40% (two passes ~ exact)
                tot = sum(quota.values())
                quota = {k: min(v, 0.4 * tot) for k, v in quota.items()}
            store.set_kv("quota", quota)   # quota_locked keeps a hand-set tilt (SAIR freeze)
    surr = train_surrogate(progress)
    disc = train_disc_surrogate()
    n_scored = 0
    if surr:
        model, kinds = surr
        dmodel = dkinds = dlo = dhi = None
        if disc:
            dmodel, dkinds, (dlo, dhi) = disc
        updates = []
        for row in store.queued_rows():
            f = _features(row["kind"], row["payload"])
            sx = f + [1 if row["kind"] == k else 0 for k in kinds]
            prob = float(model.predict_proba([sx])[0][1])
            w = weights.get(producer_of(row["target"]), base)
            disc_bonus = 0.0
            if dmodel is not None and dhi > dlo:
                dx = f + [1 if row["kind"] == k else 0 for k in dkinds]
                pred = max(dlo, min(dhi, float(dmodel.predict([dx])[0])))
                disc_bonus = 0.5 * (1 - (pred - dlo) / (dhi - dlo))  # smaller disc -> bigger bonus
            # MULTIPLICATIVE: the surrogate refines order WITHIN a producer but cannot lift a
            # near-zero-value producer (e.g. the quad flood, w~0.03) above a real one. Additive
            # blending let the surrogate+disc bonus (~1.2) swamp the bandit signal -> junk outranked
            # structured producers and got claimed first. See docs/tests/0035.
            updates.append((row["id"], w * (1 + prob + disc_bonus)))
        store.set_priority_rows(updates)
        n_scored = len(updates)
    return {"producers": {p: round(w, 3) for p, w in sorted(weights.items(),
            key=lambda kv: -kv[1])}, "surrogate_scored": n_scored,
            "disc_surrogate": disc is not None}
