"""Read-only dashboard for the IGP24 search.

Five panels, all from data we already keep: coverage trajectory (reconstructed from git history of
realized.csv), the live queue pipeline, the producer/bandit leaderboard, sole realizers, and
throughput. Stdlib http.server only (zero new deps).

Run:  uv run python scripts/dashboard/app.py [--port 5057]
Then open http://localhost:5057
"""

from __future__ import annotations

import argparse
import csv
import getpass
import io
import json
import math
import sqlite3
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from igp import baseline, db, rank
from igp import searchstore as store

ROOT = Path(__file__).resolve().parents[2]
HTML = Path(__file__).resolve().parent / "index.html"
HISTORY_CACHE = ROOT / "data" / "processed" / "coverage_history.json"


def _progress() -> dict:
    try:
        return json.loads((ROOT / "data" / "processed" / "progress.json").read_text())
    except Exception:
        return {}


_REALIZED_CACHE: dict = {"mtime": 0.0, "rows": []}


def _realized() -> list[dict]:
    """realized.csv parsed once per file change (131MB; a fresh parse per 30s poll burned ~28% of
    a core)."""
    try:
        m = db.REALIZED.stat().st_mtime
        if m != _REALIZED_CACHE["mtime"]:
            _REALIZED_CACHE["rows"] = db.load_realized()
            _REALIZED_CACHE["mtime"] = m
        return _REALIZED_CACHE["rows"]
    except Exception:
        return []


def _labels(rows: list[dict]) -> set:
    return {r["label"] for r in rows if r.get("label", "").startswith("24T")}


def _scoreable_sigs(rows: list[dict]) -> set:
    return {(r["t"], r["r"]) for r in rows
            if str(r.get("scoreable")).lower() == "true" and r.get("label", "").startswith("24T")}


def _true_1pt(prog: dict, rows: list[dict]) -> set:
    # true 1.0 held: scoreable, non-baseline (baseline caps at 0.5), no other team
    return {(r["t"], r["r"]) for r in rows
            if str(r.get("scoreable")).lower() == "true" and r.get("label", "").startswith("24T")
            and not baseline.is_baseline(r["t"], r["r"])
            and prog.get(f"{r['t']},{r['r']}", {}).get("teamCount", 1) == 0}


def _open_sigfill(prog: dict, rows: list[dict]) -> int:
    # valid, non-baseline, teamCount==0 r's missing for a group we ALREADY realize (sig-fill 1.0s)
    ours = {(r["t"], r["r"]) for r in rows if r.get("label", "").startswith("24T")}
    groups = {r["t"] for r in rows if r.get("label", "").startswith("24T")}
    return sum(1 for (t, rr) in baseline.valid_pairs()
               if t in groups and (t, rr) not in ours and not baseline.is_baseline(t, rr)
               and prog.get(f"{t},{rr}", {}).get("teamCount", 1) == 0)


def _disc_headroom(prog: dict, rows: list[dict]) -> dict:
    # among scoreable sigs with both our disc and a leaderboard min, how many a team beats us on
    our: dict = {}
    for r in rows:
        if str(r.get("scoreable")).lower() == "true" and r.get("field_disc"):
            k = (r["t"], r["r"])
            our[k] = min(our.get(k, int(r["field_disc"])), int(r["field_disc"]))
    behind = total = 0
    for (t, rr), d in our.items():
        md = prog.get(f"{t},{rr}", {}).get("minDisc")
        if not md or d <= 1:
            continue
        total += 1
        behind += math.log(int(md)) / math.log(d) < 0.999
    return {"behind": behind, "total": total}


def summary(prog: dict, rows: list[dict]) -> dict:
    st = store.get_kv("status", {}) or {}
    ctrl = store.get_kv("control", {}) or {}
    daemon = "paused" if ctrl.get("pause") else ("stopped" if ctrl.get("stop") else "running")
    dh = _disc_headroom(prog, rows)
    return {"groups": len(_labels(rows)),
            "scoreable_sigs": len(_scoreable_sigs(rows)),  # DISTINCT (t,r), the scoring metric
            "scoreable_rows": sum(1 for r in rows if str(r.get("scoreable")).lower() == "true"),
            "true_1pt": len(_true_1pt(prog, rows)), "open_sigfill": _open_sigfill(prog, rows),
            "disc_behind": dh["behind"], "disc_total": dh["total"],
            "daemon": daemon, "last_cycle": st.get("ts", "?"),
            "queued": store.counts().get("queued", 0)}


def producers_panel(prog: dict) -> list[dict]:
    stats = rank.producer_stats(prog)
    weights = rank.bandit_weights(stats)
    out = []
    for p in sorted(weights, key=lambda x: -weights[x]):
        s = stats.get(p, {})
        out.append({"name": p, "n": s.get("n", 0), "scoreable": s.get("scoreable", 0),
                    "sole": s.get("sole", 0), "weight": round(weights[p], 3)})
    return out


def soles_panel(prog: dict, rows: list[dict]) -> list[dict]:
    disc: dict = {}
    for r in rows:
        if r.get("label", "").startswith("24T") and r.get("field_disc"):
            k = (r["t"], r["r"])
            d = abs(int(r["field_disc"]))
            disc[k] = min(disc.get(k, d), d)
    prod: dict = {}
    for vr in store.verified_rows():
        if vr.get("label"):
            prod.setdefault(vr["label"], rank.producer_of(vr["target"]))
    out = [{"label": f"24T{t}", "r": rr, "producer": prod.get(f"24T{t}", "manual"),
            "disc_digits": len(str(disc[(t, rr)])) if (t, rr) in disc else None}
           for (t, rr) in _true_1pt(prog, rows)]
    return sorted(out, key=lambda x: (int(x["label"][3:]), int(x["r"])))


def throughput_panel() -> dict:
    posts = store.get_kv("posts", {}) or {}
    ver: dict = {}
    try:
        with sqlite3.connect(store.DB) as c:
            q = "SELECT updated FROM queue WHERE status='verified' AND updated IS NOT NULL"
            for (ts,) in c.execute(q):
                day = time.strftime("%Y-%m-%d", time.gmtime(ts))
                ver[day] = ver.get(day, 0) + 1
    except Exception:
        pass
    return {"posts": [{"day": d, "n": n} for d, n in sorted(posts.items())],
            "verified": [{"day": d, "n": n} for d, n in sorted(ver.items())]}


def trajectory_panel() -> list[dict]:
    """Coverage over time, reconstructed from git history of realized.csv (cached by commit sha)."""
    cache: dict = {}
    if HISTORY_CACHE.exists():
        try:
            cache = json.loads(HISTORY_CACHE.read_text())
        except Exception:
            cache = {}
    try:
        log = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%H %ct", "--",
                              "data/targets/realized.csv"],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return []
    out, changed = [], False
    for line in log.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ct = parts
        if sha not in cache:
            try:
                content = subprocess.run(["git", "-C", str(ROOT), "show",
                                          f"{sha}:data/targets/realized.csv"],
                                         capture_output=True, text=True, timeout=30).stdout
                rows = list(csv.DictReader(io.StringIO(content)))
                labels = {r["label"] for r in rows if r.get("label", "").startswith("24T")}
                sc = len({(r["t"], r["r"]) for r in rows  # DISTINCT scoreable sigs, not rows
                          if str(r.get("scoreable")).lower() == "true"
                          and r.get("label", "").startswith("24T")})
                cache[sha] = {"t": int(ct) * 1000, "groups": len(labels), "scoreable": sc}
                changed = True
            except Exception:
                continue
        out.append(cache[sha])
    if changed:
        try:
            HISTORY_CACHE.write_text(json.dumps(cache))
        except Exception:
            pass
    # merge the daemon's live per-cycle coverage log (fine-grained: groups/scoreable/sole/est) with
    # the per-commit git reconstruction (the long-term past) -> one continuous trajectory.
    live = ROOT / "data" / "processed" / "coverage_history.jsonl"
    if live.exists():
        try:
            for line in live.read_text().splitlines():
                if line.strip():
                    out.append(json.loads(line))
        except Exception:
            pass
    return sorted(out, key=lambda x: x["t"])


# (unit-name, kind, spends-Claude-tokens?, one-line description) -- the whole autonomous stack.
SERVICES = [
    ("searchd",   "service", False, "search daemon -- builds candidates & submits to SAIR"),
    ("tick",      "timer",   False, "producers refill the queue (every 15 min)"),
    ("watch",     "timer",   False, "deterministic health watchdog (zero Claude tokens)"),
    ("dashboard", "service", False, "this dashboard"),
    ("research",  "timer",   True,  "Claude research dive (~2h * Opus * high)"),
    ("build",     "timer",   True,  "Claude build runner (every 3h * Opus * high)"),
    ("audit",     "timer",   True,  "Claude self-audit (daily 08:17 * Opus * high)"),
]


def _sysctl(unit: str, props: list[str]) -> dict:
    try:
        out = subprocess.run(["systemctl", "--user", "show", unit, *[f"-p{p}" for p in props]],
                             capture_output=True, text=True, timeout=5).stdout
        return dict(ln.split("=", 1) for ln in out.splitlines() if "=" in ln)
    except Exception:
        return {}


def _proc_uptime(pid: str) -> int | None:
    try:
        out = subprocess.run(["ps", "-o", "etimes=", "-p", str(pid)],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        return int(out) if out.isdigit() else None
    except Exception:
        return None


def _reltime(human: str) -> dict | None:
    """systemctl stamps like 'Fri 2026-07-10 10:41:00 EDT' -> {at, rel_s}. Drop the tz abbrev and
    parse the rest as naive-local: the dashboard runs in the same tz so the delta is correct, and
    strptime can't parse %Z reliably."""
    human = (human or "").strip()
    if not human:
        return None
    try:
        from datetime import datetime
        parts = human.split()
        core = " ".join(parts[1:3]) if len(parts) >= 3 else human
        dt = datetime.strptime(core, "%Y-%m-%d %H:%M:%S")
        return {"at": dt.strftime("%b %d %H:%M"), "rel_s": int(time.time() - dt.timestamp())}
    except Exception:
        return {"at": human, "rel_s": None}


def system_panel() -> dict:
    """Live state of the whole autonomous stack -- services + timers + Claude processes + boot info.
    All read-only shell-outs, each wrapped so a systemd/ps hiccup degrades to 'unknown'."""
    services = []
    for name, kind, claude, blurb in SERVICES:
        svc = _sysctl(f"igp24-{name}.service",
                      ["ActiveState", "SubState", "MainPID"])
        pid = svc.get("MainPID", "0")
        running = svc.get("ActiveState") == "active" and svc.get("SubState") in ("running", "start")
        entry = {"name": name, "kind": kind, "claude": claude, "blurb": blurb,
                 "state": svc.get("SubState", "?"), "running": running,
                 "uptime_s": _proc_uptime(pid) if running and pid not in ("", "0") else None}
        if kind == "timer":
            tmr = _sysctl(f"igp24-{name}.timer",
                          ["LastTriggerUSec", "NextElapseUSecRealtime", "ActiveState"])
            entry["timer_active"] = tmr.get("ActiveState") == "active"
            entry["last"] = _reltime(tmr.get("LastTriggerUSec", ""))
            entry["next"] = _reltime(tmr.get("NextElapseUSecRealtime", ""))
        services.append(entry)

    procs = []
    try:
        out = subprocess.run(["ps", "-eo", "pid,etimes,rss,args"],
                             capture_output=True, text=True, timeout=5).stdout
        for line in out.splitlines():
            p = line.split(None, 3)
            if len(p) < 4:
                continue
            pid, et, rss, args = p
            cmd0 = args.split()[0] if args.split() else ""
            if not (cmd0 == "claude" or cmd0.endswith("/claude")):
                continue
            if "claude -p" in args or "-p" in args.split()[1:2]:
                kind = ("research" if "RESEARCH runner" in args else
                        "build" if "BUILD runner" in args else
                        "audit" if ("AUDIT" in args or "self-audit" in args) else "headless")
                label, is_claude = f"{kind} loop (headless)", True
            else:
                label, is_claude = "interactive session", True
            procs.append({"pid": pid, "elapsed_s": int(et) if et.isdigit() else None,
                          "rss_mb": int(rss) // 1024 if rss.isdigit() else None,
                          "label": label, "claude": is_claude})
    except Exception:
        pass

    boot = None
    try:
        for ln in Path("/proc/stat").read_text().splitlines():
            if ln.startswith("btime"):
                boot = int(ln.split()[1])
    except Exception:
        pass
    lg = _sysctl_str(["loginctl", "show-user", getpass.getuser(), "-p", "Linger"])
    linger = "Linger=yes" in lg

    # per-producer feed health -- the gen12 blind spot (a silent/crashing producer). The tick writes
    # producer_health; a producer that PROVED capacity (peak>=50/run) but errored 3x or went silent
    # >=12 ticks is flagged dead.
    ph = store.get_kv("producer_health", {}) or {}
    live = silent = errored = 0
    dead = []
    for name, rec in ph.items():
        short = name.replace("produce_", "") or name
        if rec.get("err_streak", 0) >= 3:
            errored += 1
            dead.append({"name": short, "why": "error",
                         "detail": (rec.get("last_error") or "")[:50]})
        elif rec.get("max_enq", 0) >= 50 and rec.get("zero_streak", 0) >= 12:
            silent += 1
            zs, mx = rec.get("zero_streak"), rec.get("max_enq")
            dead.append({"name": short, "why": "silent", "detail": f"{zs} ticks, peak {mx}/run"})
        elif rec.get("last_enq", 0) > 0:
            live += 1
    prod_health = {"live": live, "silent": silent, "error": errored, "total": len(ph), "dead": dead}

    return {"services": services, "claude_procs": procs, "producer_health": prod_health,
            "boot_epoch": boot, "boot_rel_s": (int(time.time() - boot) if boot else None),
            "linger": linger,
            "note": "auto-start on boot via systemd user linger (no manual start needed)."}


def _sysctl_str(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return ""


def gather() -> dict:
    prog, rows = _progress(), _realized()
    s = summary(prog, rows)
    traj = trajectory_panel()
    # append a live point so the chart connects to current (uncommitted) coverage
    traj.append({"t": int(time.time() * 1000), "groups": s["groups"],
                 "scoreable": s["scoreable_sigs"]})
    return {
        "summary": s,
        "trajectory": traj,
        "queue": store.counts(),
        "producers": producers_panel(prog),
        "soles": soles_panel(prog, rows),
        "throughput": throughput_panel(),
        "system": system_panel(),
        "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }


_GATHER_CACHE: dict = {"t": 0.0, "body": b""}
_GATHER_TTL = 20.0   # gather() parses a 195MB CSV + 723k queue rows (~10-28s); the browser polls
#                      every 30s and old builds piled up faster than they finished -> 22GB leak +
#                      hang. Cache the computed JSON: compute at most once per TTL regardless of
#                      request volume, decoupling compute-rate from request-rate.


def cached_gather() -> bytes:
    now = time.time()
    if now - _GATHER_CACHE["t"] > _GATHER_TTL or not _GATHER_CACHE["body"]:
        _GATHER_CACHE["body"] = json.dumps(gather()).encode()
        _GATHER_CACHE["t"] = now
    return _GATHER_CACHE["body"]


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: bytes, ctype: str):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/data"):
            self._send(cached_gather(), "application/json")
        elif self.path == "/" or self.path.startswith("/index"):
            self._send(HTML.read_bytes(), "text/html; charset=utf-8")
        else:
            self.send_error(404)

    def log_message(self, *_):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5057)
    args = ap.parse_args()
    store.init()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"dashboard: http://localhost:{args.port}  (Ctrl-C to stop)", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
