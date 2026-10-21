"""Durable stores for the search engine.

- ``realized.csv`` (committed): our coverage record — one row per verified polynomial,
  WITH coeffs + provenance (the deliverable; submission.txt rebuilds from it).
- ``verify_cache.json`` (gitignored): poly-line -> Magma result, so we never re-verify.
- ``pending_submissions.json`` (gitignored): submission_id -> [[line, source], …], so a
  submission's results can be collected across runs (decouples submit from poll).

All keyed by the bare coefficient line (the canonical poly string).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REALIZED = ROOT / "data" / "targets" / "realized.csv"
CACHE = ROOT / "data" / "processed" / "verify_cache.json"
PENDING = ROOT / "data" / "processed" / "pending_submissions.json"
FIELDS = ["label", "t", "r", "scoreable", "in_baseline", "field_disc", "disc_source",
          "source", "coeffs"]


_MTIME_CACHE: dict = {}   # path -> (stat_key, parsed) -- see _cached()


def _cached(p: Path, parse):
    """Parse ``p`` once per file change (keyed on mtime_ns+size). The daemon re-read the 131MB
    CSV + 149MB cache 4-5x per cycle (~9s); these files change at most once per cycle, and this
    process is their only writer, so an in-process mtime cache is exact."""
    try:
        st = p.stat()
        key = (st.st_mtime_ns, st.st_size)
    except FileNotFoundError:
        return parse(None)
    hit = _MTIME_CACHE.get(str(p))
    if hit and hit[0] == key:
        return hit[1]
    val = parse(p)
    _MTIME_CACHE[str(p)] = (key, val)
    return val


def _read_json(p: Path, default):
    return json.loads(p.read_text()) if p.exists() else default


def _write_json(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj))


def load_realized() -> list[dict]:
    def parse(p):
        if p is None:
            return []
        with open(p) as fh:
            return list(csv.DictReader(fh))
    return _cached(REALIZED, parse)


def record_realized(rows: list[dict]) -> int:
    """Merge rows into realized.csv (dedup by coeffs line; migrates old schema). Returns #new.

    Later non-blank fields FILL BLANKS in an existing row, so a richer re-verify or a disc backfill
    upgrades it (the old `setdefault` silently dropped such updates -> stale blank field_disc)."""
    existing = {r["coeffs"]: r for r in load_realized() if r.get("coeffs")}
    before = len(existing)
    fresh: list[dict] = []
    upgraded = False
    for r in rows:
        line = r.get("coeffs")
        if not line:
            continue
        norm = {k: ("" if r.get(k) is None else str(r.get(k, ""))) for k in FIELDS}
        cur = existing.get(line)
        if cur is None:
            existing[line] = norm
            fresh.append(norm)
        else:
            for k in FIELDS:  # fill blanks from newer, richer data
                if not cur.get(k) and norm.get(k):
                    cur[k] = norm[k]
                    upgraded = True
    REALIZED.parent.mkdir(parents=True, exist_ok=True)
    header_needed = not REALIZED.exists()
    if upgraded or header_needed:
        # rare path (re-verify upgrades an old row): full rewrite keeps the merge semantics
        with open(REALIZED, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for r in existing.values():
                w.writerow({k: r.get(k, "") for k in FIELDS})
    elif fresh:
        # common path: all-new rows -> append (the 131MB full rewrite cost ~3.1s/cycle)
        with open(REALIZED, "a", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            for r in fresh:
                w.writerow({k: r.get(k, "") for k in FIELDS})
    return len(existing) - before


def cache_load() -> dict:
    return _cached(CACHE, lambda p: json.loads(p.read_text()) if p else {})


def cache_update(d: dict) -> None:
    c = cache_load()
    c.update(d)
    _write_json(CACHE, c)


def pending_load() -> dict:
    return _read_json(PENDING, {})


def pending_add(sid: str, items: list) -> None:
    p = pending_load()
    p[sid] = items
    _write_json(PENDING, p)


def pending_remove(sid: str) -> None:
    p = pending_load()
    p.pop(sid, None)
    _write_json(PENDING, p)


SIDS = ROOT / "data" / "processed" / "submitted_sids.log"


def log_sid(sid: str) -> None:
    """Append-only ledger of EVERY submission id we POST -- survives pending_remove, so a re-sync
    can re-fetch all our submissions by-id (the /me cursor 503s past ~300, losing older sids). SAIR
    scores discs async, so a poly can flip scoreable pending->true after we collect it; without this
    ledger those flips are unreachable (reconcile_accounting's -2,583 stale-flag gap)."""
    try:
        with SIDS.open("a") as f:
            f.write(sid + "\n")
    except OSError:
        pass


def load_sids() -> list[str]:
    """Distinct submission ids from the ledger, oldest-first."""
    if not SIDS.exists():
        return []
    return list(dict.fromkeys(s.strip() for s in SIDS.read_text().splitlines() if s.strip()))


def upgrade_scoreable(updates: dict) -> int:
    """Authoritatively overwrite scoreable/field_disc/disc_source for lines SAIR now reports scored
    (record_realized only FILLS BLANKS, so it can't flip an existing scoreable=false->true).
    ``updates`` = {line: {label,t,r,scoreable,field_disc,disc_source}}. Rewrites realized.csv;
    returns #rows changed."""
    rows = load_realized()
    changed = 0
    for r in rows:
        u = updates.get(r.get("coeffs"))
        if u and str(r.get("scoreable")).lower() != "true":
            r.update({k: str(v) for k, v in u.items() if v is not None})
            changed += 1
    if changed:
        with open(REALIZED, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in FIELDS})
    return changed


def submitted_lines() -> set[str]:
    """Every poly line we've already verified, cached, or have in flight (for dedup)."""
    lines = {r["coeffs"] for r in load_realized() if r.get("coeffs")}
    lines |= set(cache_load())
    for items in pending_load().values():
        lines.update(it[0] for it in items)
    return lines


def coverage() -> dict:
    """Distinct realized (t,r) -> best (smallest field_disc) row."""
    best: dict = {}
    for r in load_realized():
        key = (r.get("t"), r.get("r"))
        fd = r.get("field_disc") or ""
        cur = best.get(key)
        if cur is None:
            best[key] = r
        else:
            cf = cur.get("field_disc") or ""
            if fd and (not cf or int(fd) < int(cf)):
                best[key] = r
    return best
