"""minblk=4 batch producer -- extend the proven twisted-Kummer A4 engine over the cluster.

The engine (scripts/mb4_sweep.gp, test 0043) built 5 open pairs across 24T18420/19631/22350.
This driver extends it to the rest of the 150-pair minblk=4 cluster: for each target's top
(6T12/14/15/16), it pulls totally-real LMFDB sextic bases and runs the sweep (a degree-18
bnfinit per base -- the cost, so this is a background batch, not a daemon hot-path kind), then
L1-density-labels every emitted candidate (scripts/mb4_match.py) and keeps the OPEN, scoreable,
confidently-labelled hits. Winners are written to data/processed/mb4_winners.jsonl and (with
--enqueue) pushed to the search queue as lit: trophies for the daemon to submit.

Usage:
  python3 scripts/mb4_producer.py --top 6T15 --bases 3 --nq 3        # sweep one top
  python3 scripts/mb4_producer.py --winners-only --enqueue           # label+enqueue prior output
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from igp import baseline, db, gp, lmfdb  # noqa: E402
from igp import searchstore as store  # noqa: E402

# Working dir for sweep params/outputs (was a session scratchpad); override with IGP_SCRATCH.
SCRATCH = Path(os.environ.get("IGP_SCRATCH", ROOT / "data" / "processed" / "scratch"))
_spec = importlib.util.spec_from_file_location("mb4_match", ROOT / "scripts" / "mb4_match.py")
mb4_match = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mb4_match)

# top -> the target 24Tt it can carry (from mb4_match.TOP_TARGETS)
TOP_TARGETS = mb4_match.TOP_TARGETS
WINNERS = ROOT / "data" / "processed" / "mb4_winners.jsonl"
WANT = [0, 4, 8, 12, 16, 24]


def sweep_top(top: str, n_bases: int, nq: int) -> list[str]:
    """Run the gp sweep over n_bases totally-real sextics of `top`; return ksave file paths."""
    try:
        bases = lmfdb.fields(6, galois_label=top, max_r2=0, class_number=None, limit=n_bases)
    except Exception as e:
        print(f"  {top}: LMFDB unavailable ({str(e)[:50]})")
        return []
    outs = []
    for i, (coeffs, _g, disc, _h) in enumerate(bases):
        pref = f"{top.replace('T', 't')}_b{i}"
        params = SCRATCH / f"mb4_params_{pref}.gp"
        spout = SCRATCH / f"mb4_ksave_{pref}.txt"
        spout.write_text("")  # truncate (never rm)
        params.write_text(
            f"BASE={list(coeffs)};\nWANT={WANT};\nPREF=\"{pref}\";\n"
            f"QSTART=1000;\nNQ={nq};\nSPOUT=\"{spout}\";\n")
        print(f"  {top} base#{i} (disc {disc}): bnfinit(deg-18) + sweep ...", flush=True)
        sweep = ROOT / "scripts" / "mb4_sweep.gp"
        try:
            subprocess.run(["gp", "-q"], input=f'PARAMS="{params}";\n\\r {sweep}\n',
                           capture_output=True, text=True, timeout=3600)
        except subprocess.TimeoutExpired:
            print(f"    base#{i}: timed out (>1h) -- skipping")
        if spout.exists() and spout.stat().st_size:
            outs.append(spout)
    return outs


def label_and_collect(ksave_paths: list[Path]) -> list[dict]:
    prog = json.loads((ROOT / "data" / "processed" / "progress.json").read_text())
    held = {(r["t"], r["r"]) for r in db.load_realized()
            if str(r.get("scoreable")).lower() == "true"}
    winners = []
    for path in ksave_paths:
        for line in path.read_text().splitlines():
            if "KASC=" not in line:
                continue
            co = [int(x) for x in line.split("KASC=")[1].strip().strip("[]").split(",")]
            if len(co) != 25 or co[-1] != 1:
                continue
            tally, n = mb4_match.poly_dist(co, hi=3000)
            scores = sorted((mb4_match.l1(tally, n, t), t) for t in mb4_match.GD)
            l1, t = scores[0]
            margin = scores[1][0] - l1
            if l1 >= 0.25 or margin <= 0.05:
                continue
            r = gp.real_roots(co)
            is_open = (prog.get(f"{t},{r}") or {}).get("teamCount", 9) == 0 \
                and (str(t), str(r)) not in held and not baseline.is_baseline(t, r)
            if not is_open or not gp.scoreable_disc(co, budget=50):
                continue
            winners.append({"t": t, "r": r, "l1": round(l1, 3), "margin": round(margin, 3),
                            "coeffs": co, "src": path.stem})
    return winners


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", help="single 6Tj top to sweep (default: all four)")
    ap.add_argument("--bases", type=int, default=3)
    ap.add_argument("--nq", type=int, default=3)
    ap.add_argument("--winners-only", action="store_true",
                    help="skip sweep; label existing ksave files")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    if args.winners_only:
        ksaves = list(SCRATCH.glob("mb4_ksave_*.txt"))
    else:
        tops = [args.top] if args.top else ["6T12", "6T14", "6T15", "6T16"]
        ksaves = []
        for top in tops:
            ksaves += sweep_top(top, args.bases, args.nq)

    winners = label_and_collect(ksaves)
    with WINNERS.open("a") as f:
        for w in winners:
            f.write(json.dumps(w) + "\n")
    print(f"mb4 producer: {len(winners)} OPEN scoreable winners")
    seen = set()
    for w in winners:
        key = (w["t"], w["r"])
        print(f"  24T{w['t']} r={w['r']} L1={w['l1']} (margin {w['margin']}) [{w['src']}]"
              + ("  DUP-pair" if key in seen else ""))
        seen.add(key)

    if args.enqueue and winners:
        store.init()
        realized = db.load_realized()
        held_groups = {r["t"] for r in realized if str(r.get("scoreable")).lower() == "true"}
        held_pairs = {(r["t"], r["r"]) for r in realized if str(r.get("scoreable")).lower() == "true"}
        # NEW GROUP first (climbs rank), then new pair of a held group, then alternate model
        tiers = {"new": 130.0, "pair": 115.0, "alt": 100.0}
        added = {"new": 0, "pair": 0, "alt": 0}
        for w in winners:
            t, r = str(w["t"]), str(w["r"])
            tier = "alt" if (t, r) in held_pairs else ("pair" if t in held_groups else "new")
            tag = f"lit:mb4{tier}:{t}.{r}:{w['src']}"
            if not store.has_target(tag) and store.enqueue("ready", {"coeffs": w["coeffs"]},
                                                           target=tag):
                added[tier] += 1
        for tier, pri in tiers.items():
            store.set_priority_prefix(f"lit:mb4{tier}", pri)
        print(f"  enqueued new-group {added['new']} @130, new-pair {added['pair']} @115, "
              f"alt {added['alt']} @100")


if __name__ == "__main__":
    main()
