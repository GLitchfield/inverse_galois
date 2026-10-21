"""Hourly watchdog -- deterministic, zero-token, no-input health + progress check.

Runs on a systemd timer (see install below) whether or not a human or an interactive Claude
session is present. Each run appends ONE status line to logs/hourly_watch.log and takes only SAFE,
REVERSIBLE corrective actions (restart the daemon if it died). Anything higher-stakes (blank
trophies, sharp score drops) is FLAGGED in the line with a leading '!!' for human/Claude review on
return -- the watchdog never fires submissions or edits the daemon on its own.

Deliberately NOT an LLM: this is the "check on everything once an hour" that needs no tokens and no
input, complementing the daily audit's deeper (LLM) counter-check.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from igp import db, sair  # noqa: E402
from igp import searchstore as store  # noqa: E402

LOG = ROOT / "logs" / "hourly_watch.log"
TROPHY_T = {"18440", "22336", "13994", "5332", "5334", "2157", "18420", "19631", "22350",
            "21449", "24672"}


def daemon_active() -> bool:
    r = subprocess.run(["systemctl", "--user", "is-active", "igp24-searchd"],
                       capture_output=True, text=True)
    return r.stdout.strip() == "active"


def main() -> None:
    flags: list[str] = []
    parts: list[str] = [time.strftime("%Y-%m-%dT%H:%M:%S")]

    # 1. daemon health -- restart if dead (safe, reversible)
    if not daemon_active():
        subprocess.run(["systemctl", "--user", "restart", "igp24-searchd"],
                       capture_output=True)
        flags.append("!!daemon-was-DEAD-restarted")
    parts.append(f"daemon={'up' if daemon_active() else 'DOWN'}")

    # 1b. daemon PRODUCTIVITY -- 'up' is not enough; a gated/hung daemon is 'up' but idle. This
    # blind spot cost a full overnight (2026-07-06): gate locked (pending stuck > max_pending),
    # sub=0 for ~1168 cycles, but the watchdog only checked liveness and reported daemon=up=OK.
    st = store.get_kv("status", {}) or {}
    stale = st.get("ts") and st["ts"] == store.get_kv("watch_last_ts")
    if st.get("gated"):
        flags.append("!!daemon-GATED(not-submitting)")
    if stale:
        flags.append(f"!!daemon-status-STALE(hung? ts={st.get('ts')})")
    store.set_kv("watch_last_ts", st.get("ts"))
    parts.append(f"dstat=gated:{st.get('gated')},built:{st.get('built')},sub:{st.get('submitted')}")

    # 2. leaderboard (rate-flaky; one call, tolerate failure)
    try:
        lb = sair.leaderboard()
        us = next((i for i in lb if i.get("teamName") == "Team Gavin"), None)
        score = us.get("score", us.get("totalScore", 0)) if us else 0
        rank = us.get("rank") if us else "?"
        pr = rank - 1 if isinstance(rank, int) else 0
        ahead = next((i for i in lb if i.get("rank") == pr), None)
        gap = (ahead.get("score", ahead.get("totalScore", 0)) - score) if ahead else 0
        parts.append(f"rank={rank} score={score:.0f} gap+{gap:.0f}")
        prev = store.get_kv("watch_last_score")
        if prev is not None and score < float(prev) - 15:
            flags.append(f"!!score-drop {float(prev):.0f}->{score:.0f}")
        store.set_kv("watch_last_score", score)
    except Exception as e:
        parts.append(f"lb=ERR({type(e).__name__})")

    # 3. backlog drain
    pend = sum(len(v) for v in db.pending_load().values())
    parts.append(f"pending={pend}")

    # 4. blank-disc trophy detection (scoreable pair with NO scoring model) -- FLAG, don't act
    rows = db.load_realized()
    scoring: dict[tuple, bool] = {}
    for r in rows:
        if r["t"] not in TROPHY_T:
            continue
        k = (r["t"], r["r"])
        has = (str(r.get("scoreable")).lower() == "true"
               and bool((r.get("field_disc") or "").strip()))
        scoring[k] = scoring.get(k, False) or has
    blank = [f"{t}r{rr}" for (t, rr), ok in scoring.items() if not ok]
    if blank:
        flags.append(f"!!trophy-blank[{','.join(blank[:6])}]")
    parts.append(f"trophies_scoring={sum(scoring.values())}/{len(scoring)}")

    # 5. per-producer feed health -- the gen12 blind spot: the main feed silently crashed and stayed
    # dead for DAYS while daemon=up (the whole stack looked healthy). A producer that PROVED it can
    # produce (peak>=50/run) but errored 3x or went silent >=12 ticks is flagged. The tick writes
    # producer_health; here we only read + alert (zero-token).
    ph = store.get_kv("producer_health", {}) or {}
    dead = []
    for name, rec in ph.items():
        short = name.replace("produce_", "").replace("produce", "produce") or name
        if rec.get("err_streak", 0) >= 3:
            dead.append(f"{short}:ERR")
        elif rec.get("max_enq", 0) >= 50 and rec.get("zero_streak", 0) >= 12:
            dead.append(f"{short}:SILENT")
    if dead:
        flags.append(f"!!producer-dead[{','.join(dead[:8])}]")
    live = sum(1 for r in ph.values() if r.get("last_enq", 0) > 0)
    parts.append(f"producers_live={live}/{len(ph)}")

    line = " ".join(parts) + ("  " + " ".join(flags) if flags else "  OK")
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a") as f:
        f.write(line + "\n")
    print(line)


if __name__ == "__main__":
    main()
