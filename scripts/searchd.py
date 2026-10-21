"""searchd — the long-running search daemon.

A persistent worker that, every cycle: collects verified results, then (unless paused / over
the rate limit / verifier backed up) claims a batch of queued targets, constructs each,
de-dups, and submits. Producers (separate) fill the queue; this just drains it, 24/7.

Managed via the kv control row in ``searchstore`` (see scripts/search_ctl.py):
  control = {"stop": bool, "pause": bool}
and budget knobs in kv: max_pending, max_posts_day, build_batch, interval.

Construction is dispatched by queue-row ``kind`` over the whole toolkit. State + status live
in ``data/processed/search.db``; verified polynomials land in ``realized.csv`` via the engine.

Run (detached): uv run python scripts/searchd.py   (or via run_in_background)
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

from igp import coverage, db, engine, gp, rank, submission, verify
from igp import searchstore as store

_DATA = Path(store.DB).parent               # data/processed
COVERAGE_LOG = _DATA / "coverage_history.jsonl"
_progress_cache: dict = {"data": {}, "mtime": 0.0}
_last_cov: tuple = ()


def _progress() -> dict:
    """progress.json, cached + reloaded only when its mtime changes (it's ~12MB; the tick refreshes
    it ~every 12h). Used for the sole/est fields of the coverage snapshot."""
    p = _DATA / "progress.json"
    try:
        m = p.stat().st_mtime
        if m != _progress_cache["mtime"]:
            _progress_cache["data"] = json.loads(p.read_text())
            _progress_cache["mtime"] = m
    except Exception:
        pass
    return _progress_cache["data"]


def _log_coverage() -> None:
    """Append a coverage point (groups/scoreable/sole/est + timestamp) to coverage_history.jsonl on
    the distinct metrics change — a fine-grained trajectory the per-commit git reconstruction can't
    give. Fail-safe; never disturbs the cycle."""
    global _last_cov
    try:
        snap = coverage.snapshot(_progress())
        key = (snap["groups"], snap["scoreable"], snap["sole"])
        if key == _last_cov:
            return
        _last_cov = key
        snap["t"] = int(time.time() * 1000)
        with open(COVERAGE_LOG, "a") as fh:
            fh.write(json.dumps(snap) + "\n")
    except Exception:
        pass


def construct(item):
    """Dispatch a queue row to its constructor; return ascending coeffs (or [])."""
    k, p = item["kind"], item["payload"]
    if k == "ready":
        return p["coeffs"]  # pre-built polynomial (e.g. trinomial sweep, Belyi specialization)
    if k == "cyclotomic_c2":
        return gp.cyclotomic_c2(p["w"], p["n"], p["q"])
    if k == "cyclotomic_c2_multi":
        return gp.cyclotomic_c2_multi(p["n"], [tuple(x) for x in p["pairs"]])
    if k == "galois_c2":
        return gp.galois_c2(p["base"], p["w"], p["q"])
    if k == "galois_c2_multi":
        return gp.galois_c2_multi(p["base"], [tuple(x) for x in p["pairs"]])
    if k == "general_c2":
        return gp.general_c2(p["base"], p["w"], p["q"])
    if k == "abelian_kernel":  # C_n ray class field over a deg-(24/n) base (class-field-theory, #3)
        res = gp.abelian_kernel(p["base"], p["n"])
        return res[0] if res else []
    if k == "biquadratic":
        return gp.biquadratic_c2(p["base"], p["w1"], p["w2"], p["q"])
    if k == "general_biquadratic":
        return gp.general_biquadratic(p["base"], p["w1"], p["w2"], p["q"])
    if k == "cyclotomic_kummer":
        return gp.cyclotomic_kummer(p["w"], p["n"], p["q"], p["k"])
    if k == "compositum":  # e.g. 8x3 = deg-8 base x cyclic cubic (built in the parallel pool)
        return gp.compositum([p["base"], p["cubic"]], reduce=True)[0]
    if k == "general_cubic":  # 8x3 S3-kernel: x^3 - alpha over a deg-8 base (test 0041)
        return gp.general_cubic(p["base"], p["w"], p["q"])
    if k == "compose":  # f(g(x)) wreath shapes: 4x6/3x8/2x12 incl. the near-S24 titans
        return gp.composition(p["inner"], p["outer"])
    if k == "lift":  # orbit-sign lift K12(sqrt delta): closure-preserving quadratic (lift-map dive)
        return gp.orbit_lift(p["base"], p["sel"])
    if k == "general_quartic":  # 6x4 S4-kernel: x^4 + alpha*x + alpha over a deg-6 base
        return gp.general_quartic(p["base"], p["w"], p["q"])
    raise ValueError(f"unknown kind {k}")


def _construct_one(item, s24: bool = True):
    """Construct one row's polynomial AND run the S24 filter, both in the worker (each blocks on
    its own gp subprocess -> fully parallel; the filter used to run 211ms/poly SERIALLY on the
    main thread, ~110s of a 212s cycle). Returns (item, coeffs|None, drop). A row requeued after
    a failed POST still carries its built line -> reuse it (it already passed the filter)."""
    if item.get("line"):
        try:
            co = [int(x) for x in item["line"].split(",")]
            if len(co) == 25 and co[-1] == 1:
                return item, co, False
        except Exception:
            pass
    try:
        co = construct(item)
    except Exception as e:
        return item, None, f"exc:{type(e).__name__}"
    if not co:
        return item, None, "empty"
    if not (len(co) == 25 and co[-1] == 1):
        return item, None, "malformed"
    try:
        drop = s24 and verify.likely_negligible_s24_fast(co)
    except Exception:
        drop = False  # filter must never kill a build; fail open (submit)
    if not drop:
        try:  # L1 smoothness gate: prefer a model the grader can factor; never drops (task #15)
            co = gp.smooth_or_reduce(co)
        except Exception:
            pass
    return item, co, drop


def sync_verified():
    """Sync submitted queue rows against the verify cache: verified (has a label) or failed."""
    cache = db.cache_load()
    for qid, line in _submitted_rows():
        res = cache.get(line)
        if not res:
            continue
        if res.get("label"):
            store.mark(qid, "verified", label=res["label"])
        elif res.get("failed"):
            store.mark(qid, "failed", detail="verify-reject")


def _submitted_rows():
    import sqlite3
    with sqlite3.connect(store.DB) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT id,line FROM queue WHERE status='submitted' AND line IS NOT NULL"
        ).fetchall()
    return [(r["id"], r["line"]) for r in rows]


def _posts_today() -> int:
    import time as _t
    day = _t.strftime("%Y-%m-%d", _t.gmtime())
    rec = store.get_kv("posts", {})
    return rec.get(day, 0)


def _bump_posts():
    import time as _t
    day = _t.strftime("%Y-%m-%d", _t.gmtime())
    rec = store.get_kv("posts", {})
    rec[day] = rec.get(day, 0) + 1
    store.set_kv("posts", rec)


def _max_posts_today():
    """Mark today's post budget as exhausted (SAIR returned the daily team limit, now 1000/day) so
    the daemon stops submitting until the next UTC day, without crashing."""
    import time as _t
    day = _t.strftime("%Y-%m-%d", _t.gmtime())
    rec = store.get_kv("posts", {})
    rec[day] = max(rec.get(day, 0), store.get_kv("max_posts_day", 500))
    store.set_kv("posts", rec)


def cycle():
    """One daemon iteration. Returns a short status dict."""
    cfg = store.get_kv("control", {})
    col = {}
    try:
        col = engine.collect()
        sync_verified()
    except Exception as e:  # network / verifier hiccup — keep looping
        col = {"error": str(e)[:80]}
    if col.get("new_rows", 0):
        _log_coverage()  # fine-grained coverage trajectory (only when realized.csv grew)
    built = submitted = 0
    if not cfg.get("pause"):
        max_pending = store.get_kv("max_pending", 40)
        max_posts = store.get_kv("max_posts_day", 500)
        pending = sum(len(v) for v in db.pending_load().values())
        s24 = store.get_kv("s24_filter", True)
        # collect-broken guard (2026-07-07): when /submissions/me 503s, `pending` is a LIE -- it
        # includes results SAIR already verified but we could not pull -- so it must NOT lock the
        # daemon (that gate-lock idled us a whole overnight while the score eroded). Count
        # consecutive collect failures; after 3, ignore the pending gate (max_posts_day still
        # rate-limits) until collect recovers. A single transient 503 (streak 1-2) still gates, so
        # we don't over-relax on a blip; a genuinely backed-up SAIR (collect WORKS, polys queued)
        # keeps streak=0 and gates normally -- exactly the distinction we want.
        pending_high = pending >= max_pending
        streak = (store.get_kv("collect_fail_streak", 0) + 1) if col.get("collect_failed") else 0
        store.set_kv("collect_fail_streak", streak)
        # Second guard, for the INTERMITTENT endpoint (fail/success/fail keeps the streak < 3 while
        # deep-page-stuck old pending never drains): the gate is backpressure, not a hard lock, so
        # must TIME OUT. If pending has sat >= max_pending for GATE_MAX_CYCLES straight, relax
        # regardless of cause (max_posts_day is the real daily ceiling, and the organizers welcome
        # volume). Fast path (streak>=3) unlocks a full 503 in ~1 min; this slow path (~10 min) is
        # the catch-all so no failure pattern can idle the daemon indefinitely again.
        high_cycles = (store.get_kv("gate_high_cycles", 0) + 1) if pending_high else 0
        store.set_kv("gate_high_cycles", high_cycles)
        gated = pending_high and streak < 3 and high_cycles < 30
        if not gated and _posts_today() < max_posts:
            # SAIR raised limits to 1000 polys/POST + 1000 POSTs/day (2026-06-29). Pack each POST to
            # the per-request max; engine.submit dedups vs submitted_lines and the bandit ranks
            # targeted/scoreable first, so volume stays quality-directed (no random flooding).
            submit_target = store.get_kv("submit_target", 1000)  # SAIR allows <=1000 polys/POST
            claim_batch = store.get_kv("claim_batch", store.get_kv("build_batch", 50))
            max_builds = store.get_kv("max_builds_per_post", 2000)  # work cap so a cycle ends
            # Anti-junk: never auto-submit the inexhaustible random enumerators (quad/pent/tri) NOR
            # the 0-value flood producers (compose/g6x4s4/c8x3/nflist) that producer_value.py showed
            # earn ~0 pts at 200-620x duplication (2026-07-11 rebalance) -- the "million random
            # polynomials" the organizers asked us NOT to send. Re-enable any arm by removing it
            # from the `no_submit` kv once producer_value shows it PAYS. Still hand-runnable.
            no_submit = set(store.get_kv(
                "no_submit", ["quad", "pent", "tri", "compose", "g6x4s4", "c8x3", "nflist"]))
            workers = store.get_kv("build_workers", 10)  # parallel gp constructions (24-core box)
            cands = []
            builds = 0
            payload = 0
            full = False  # POST filled (submit_target / 95KB) -> stop, requeue leftovers
            with ThreadPoolExecutor(max_workers=workers) as pool:
                while not full and len(cands) < submit_target and builds < max_builds:
                    batch = store.claim(claim_batch)
                    if not batch:
                        break  # queue exhausted
                    todo = []
                    for item in batch:
                        builds += 1
                        if rank.producer_of(item.get("target")) in no_submit:
                            store.mark(item["id"], "skipped")  # value floor; don't build/submit
                        else:
                            todo.append(item)
                    # Construct the batch concurrently (each blocks on its own gp subprocess).
                    for item, co, drop in pool.map(partial(_construct_one, s24=s24), todo):
                        if full:
                            store.mark(item["id"], "queued")  # POST already full -> not lost
                            continue
                        if co is None:
                            store.mark(item["id"], "failed", detail=drop)  # drop = the reason tag
                            continue
                        if drop:
                            store.mark(item["id"], "filtered")  # forced S_24 => negligible, skip
                            continue
                        line = submission.poly_line(co)
                        if cands and payload + len(line) + 1 > 95000:  # keep POST under 100KB cap
                            store.mark(item["id"], "queued")  # doesn't fit this POST
                            full = True
                            continue
                        store.mark(item["id"], "built", line=line)
                        cands.append((line, f"daemon:{item.get('target')}", item["id"]))
                        payload += len(line) + 1
                        built += 1
                        if len(cands) >= submit_target:
                            full = True
            if cands:
                outcome = None
                try:
                    outcome = engine.submit_batch([(ln, src) for ln, src, _ in cands],
                                                  description="searchd")
                except Exception as e:  # 429 daily-limit / transient: requeue, never crash
                    for _ln, _src, qid in cands:
                        store.mark(qid, "queued")  # not lost; retried next cycle / tomorrow
                    if "TEAM_DAILY_LIMIT" in str(e):
                        _max_posts_today()  # SAIR caps submissions/day; stop until next UTC day
                    print(f"[submit deferred] {str(e)[:90]}", flush=True)
                if outcome is not None:
                    sid, posted, known = outcome
                    if sid:
                        _bump_posts()
                    # Mark ONLY what engine actually sent as submitted; a line it reports as
                    # already-known is a dup; anything else (over-cap) goes back to queued.
                    # Marking the whole batch submitted while engine truncated to 100/POST
                    # silently dropped ~85% of built rows (found 2026-07-01).
                    for ln, _src, qid in cands:
                        if ln in posted:
                            store.mark(qid, "submitted")
                        elif ln in known:
                            store.mark(qid, "dup")
                        else:
                            store.mark(qid, "queued")
                    submitted = len(posted)
    status = {"ts": time.strftime("%H:%M:%S", time.gmtime()), "collect": col,
              "built": built, "submitted": submitted, "gated": gated,
              "queue": store.counts()}
    store.set_kv("status", status)
    return status


def main():
    store.init()
    store.set_kv("control", store.get_kv("control", {}))
    recovered = store.requeue_inflight()  # reclaim work orphaned by a prior stop/crash
    if recovered:
        print(f"recovered {recovered} orphaned in-flight rows -> queued", flush=True)
    interval = store.get_kv("interval", 45)
    print(f"searchd up; interval={interval}s; queue={store.counts()}", flush=True)
    while True:
        if store.get_kv("control", {}).get("stop"):
            print("searchd stopping (control.stop)", flush=True)
            break
        s = cycle()
        print(f"[{s['ts']}] collect={s['collect']} built={s['built']} sub={s['submitted']} "
              f"queue={s['queue']}", flush=True)
        time.sleep(store.get_kv("interval", 45))


if __name__ == "__main__":
    main()
