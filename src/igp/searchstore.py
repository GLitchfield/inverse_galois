"""SQLite-backed work store for the long-running search daemon.

A persistent queue of construction *targets* (kind + JSON payload) plus a key/value table
for daemon status/config. Decouples WHAT to build (producers enqueue) from the daemon that
builds + submits + collects. SQLite (stdlib) is concurrency-safe, so the daemon writes while
management commands / the agent read.

Status lifecycle of a queue row: queued -> building -> submitted -> verified | failed | dup.
The authoritative coverage record stays ``realized.csv`` (via ``db``/``engine``); this store
is the daemon's operational state (gitignored under data/processed).
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data" / "processed" / "search.db"


def _conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    return c


def init():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS queue("
            "id INTEGER PRIMARY KEY, kind TEXT, payload TEXT, target TEXT, "
            "status TEXT DEFAULT 'queued', label TEXT, line TEXT, "
            "created REAL, updated REAL)"
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_status ON queue(status)")
        try:  # failure-taxonomy column (2026-07-04); no-op when it already exists
            c.execute("ALTER TABLE queue ADD COLUMN detail TEXT")
        except Exception:
            pass
        c.execute("CREATE INDEX IF NOT EXISTS idx_queue_target ON queue(target)")
        try:  # priority: bandit (producer) + surrogate (per-row) value; claim highest first
            c.execute("ALTER TABLE queue ADD COLUMN priority REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # already added
        c.execute("CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT)")


def enqueue(kind: str, payload: dict, target: str | None = None) -> bool:
    """Add a target. ``target`` (e.g. predicted label) dedups against existing queue rows."""
    now = time.time()
    with _conn() as c:
        if target is not None:
            row = c.execute("SELECT 1 FROM queue WHERE target=? LIMIT 1", (target,)).fetchone()
            if row:
                return False
        c.execute(
            "INSERT INTO queue(kind,payload,target,created,updated) VALUES(?,?,?,?,?)",
            (kind, json.dumps(payload), target, now, now),
        )
    return True


def claim(n: int) -> list[dict]:
    """Atomically move up to ``n`` queued rows to 'building' and return them.

    Portfolio allocation (2026-07-04): when the tick has written kv ``quota`` =
    {target-prefix: share}, slots are split by share (largest remainder) with each bucket taking
    its own highest-priority rows, remainder filled by global priority — so no producer can
    silently dominate the mix (the 91%-gen12 queue) and every active family keeps a floor. The
    prefix LIKE rides the queue(target) index. No kv -> legacy pure-priority behavior."""
    quota = get_kv("quota") or {}
    with _conn() as c:
        rows = []
        if quota:
            seen: set = set()
            shares = [(pre, max(sh, 0.0)) for pre, sh in quota.items()]
            total = sum(sh for _, sh in shares) or 1.0
            for pre, sh in sorted(shares, key=lambda x: -x[1]):
                k = int(round(n * sh / total))
                if k <= 0:
                    continue
                for r in c.execute(
                        "SELECT * FROM queue WHERE status='queued' AND target LIKE ? "
                        "ORDER BY priority DESC, id LIMIT ?", (pre + "%", k)):
                    if r["id"] not in seen:
                        seen.add(r["id"])
                        rows.append(r)
            if len(rows) < n:
                for r in c.execute(
                        "SELECT * FROM queue WHERE status='queued' "
                        "ORDER BY priority DESC, id LIMIT ?", (n,)):
                    if r["id"] not in seen and len(rows) < n:
                        seen.add(r["id"])
                        rows.append(r)
        else:
            rows = c.execute(
                "SELECT * FROM queue WHERE status='queued' ORDER BY priority DESC, id LIMIT ?",
                (n,)
            ).fetchall()
        ids = [r["id"] for r in rows]
        if ids:
            placeholders = ",".join("?" * len(ids))
            c.execute(
                f"UPDATE queue SET status='building',updated=? WHERE id IN ({placeholders})",
                [time.time(), *ids],
            )
    return [{**dict(r), "payload": json.loads(r["payload"])} for r in rows]


def mark(qid: int, status: str, *, label: str | None = None, line: str | None = None,
         detail: str | None = None):
    with _conn() as c:
        c.execute(
            "UPDATE queue SET status=?,label=COALESCE(?,label),line=COALESCE(?,line),"
            "detail=COALESCE(?,detail),updated=? WHERE id=?",
            (status, label, line, detail, time.time(), qid),
        )


def failure_taxonomy() -> list[tuple]:
    """[(kind, detail, n)] over failed rows — the self-repair substrate (2026-07-04)."""
    with _conn() as c:
        return c.execute(
            "SELECT kind, COALESCE(detail,'(untagged)'), COUNT(*) FROM queue "
            "WHERE status='failed' GROUP BY kind, detail ORDER BY 3 DESC"
        ).fetchall()


def line_status(line: str) -> str | None:
    with _conn() as c:
        r = c.execute("SELECT status FROM queue WHERE line=? LIMIT 1", (line,)).fetchone()
    return r["status"] if r else None


def has_target(target: str) -> bool:
    """True if any queue row (any status) already has this target — cheap pre-dedup so callers can
    skip expensive construction work for already-enqueued targets."""
    with _conn() as c:
        row = c.execute("SELECT 1 FROM queue WHERE target=? LIMIT 1", (target,)).fetchone()
    return row is not None


def set_priority_prefix(prefix: str, value: float):
    """Set priority on QUEUED rows whose target starts with ``prefix`` (bandit, per-producer)."""
    with _conn() as c:
        c.execute("UPDATE queue SET priority=? WHERE status='queued' AND target LIKE ?",
                  (value, prefix + "%"))


def set_priority_rows(updates: list[tuple]):
    """Bulk per-row priority updates [(id, priority), ...] (surrogate refinement)."""
    with _conn() as c:
        c.executemany("UPDATE queue SET priority=? WHERE id=?",
                      [(v, qid) for qid, v in updates])


def queued_rows() -> list[dict]:
    """All queued rows (id, kind, payload, target) — for scoring/ranking."""
    with _conn() as c:
        rows = c.execute(
            "SELECT id,kind,payload,target FROM queue WHERE status='queued'").fetchall()
    return [{"id": r["id"], "kind": r["kind"], "payload": json.loads(r["payload"]),
             "target": r["target"]} for r in rows]


def requeue_inflight() -> int:
    """Reset orphaned in-flight rows ('building' or 'built') back to 'queued'. Both are transient:
    'building' = claimed, not yet constructed; 'built' = constructed with a line, awaiting the batch
    POST. A stop/crash mid-cycle orphans them (claim() takes only 'queued') so work is lost. Call on
    startup. engine.submit dedups, so re-submitting a 'built' line that did go out is harmless."""
    with _conn() as c:
        return c.execute("UPDATE queue SET status='queued',updated=? "
                         "WHERE status IN ('building','built')", (time.time(),)).rowcount


def verified_rows() -> list[dict]:
    """All verified rows with their construction (payload) + label — surrogate training data."""
    with _conn() as c:
        rows = c.execute("SELECT kind,payload,target,label,line FROM queue "
                         "WHERE status='verified' AND label IS NOT NULL").fetchall()
    return [{"kind": r["kind"], "payload": json.loads(r["payload"]), "target": r["target"],
             "label": r["label"], "line": r["line"]} for r in rows]


def counts() -> dict:
    with _conn() as c:
        rows = c.execute("SELECT status,COUNT(*) n FROM queue GROUP BY status").fetchall()
    return {r["status"]: r["n"] for r in rows}


_JOURNAL_SKIP = {"status", "posts", "tsig_last"}   # per-cycle noise, not configuration


def set_kv(key: str, value):
    with _conn() as c:
        if key not in _JOURNAL_SKIP:
            try:  # config journal (2026-07-04): correlate score-velocity eras with tuning eras
                old = c.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
                oldv = json.loads(old["value"]) if old else None
                if oldv != value:
                    jp = Path(DB).parent / "config_journal.jsonl"
                    with open(jp, "a") as fh:
                        fh.write(json.dumps({"ts": int(time.time()), "key": key,
                                             "old": oldv, "new": value}) + "\n")
            except Exception:
                pass
        c.execute("INSERT OR REPLACE INTO kv VALUES(?,?)", (key, json.dumps(value)))


def get_kv(key: str, default=None):
    with _conn() as c:
        r = c.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
    return json.loads(r["value"]) if r else default
