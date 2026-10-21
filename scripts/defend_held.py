"""Defend held pairs: rank our held scoreable (t,r) by RECOVERABLE score-loss and (optionally)
enqueue the worst as high-priority disc-min targets.

Per held pair the score is `weight * ratio` with `weight = 2^(1-k)` (k=teamCount, baseline-capped
at 0.5) and `ratio = log(minDisc)/log(ourDisc) <= 1` (1.0 = we hold the global-min field disc). A
pair where a rival's field disc beats ours has ratio<1; lowering our disc to the current min
recovers `weight*(1-ratio)`. This ranks by that recoverable loss so defense is targeted, not blind.

NOTE the scoring disc is the FIELD disc (nfdisc), invariant under polredabs -- so a "smaller model"
means a genuinely SMALLER FIELD (different base/prime), not a reduced representative of the same one.

Usage:
  python scripts/defend_held.py                 # diagnose: ranked loss + totals + family buckets
  python scripts/defend_held.py --enqueue 200   # push the top-N behind pairs as defend: disc-min targets
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from igp import baseline, db  # noqa: E402
from igp import searchstore as store  # noqa: E402

PROG = ROOT / "data" / "processed" / "progress.json"


def load() -> list[dict]:
    prog = json.load(open(PROG))
    rows = db.load_realized()
    # our smallest field disc per held scoreable pair, keep provenance (source) of that best model
    best: dict = {}
    for r in rows:
        if str(r.get("scoreable")).lower() != "true":
            continue
        fd = r.get("field_disc")
        if not (fd and fd.lstrip("-").isdigit()):
            continue
        key, d = (r["t"], r["r"]), abs(int(fd))
        if key not in best or d < best[key]["ourDisc"]:
            best[key] = {"ourDisc": d, "source": r.get("source", "")}

    out = []
    for (t, r), b in best.items():
        e = prog.get(f"{t},{r}", {})
        md = e.get("minDisc")
        k = max(e.get("teamCount", 1), 1)
        d = b["ourDisc"]
        if not (md and str(md).isdigit()) or d <= 1:
            continue
        md = int(md)
        ratio = math.log(md) / math.log(d)
        weight = 2 ** (1 - k)
        if baseline.is_baseline(t, r):
            weight = min(weight, 0.5)
        loss = weight * (1 - ratio)
        out.append({"t": t, "r": r, "k": k, "ourDisc": d, "minDisc": md,
                    "ratio": ratio, "weight": weight, "loss": loss,
                    "source": b["source"], "we_hold_min": md >= d})
    return out


def family(src: str) -> str:
    s = str(src)
    for tag in ("mb2", "mb4", "mb8", "mb12", "gen12", "compose", "lift", "tsig", "sigfill",
                "discmin", "size4", "size3", "harden", "g6x4", "g8x3", "lit", "daemon"):
        if tag in s:
            return tag
    return s.split(":")[0][:10] if s else "?"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enqueue", type=int, default=0, help="push top-N behind pairs as defend: targets")
    ap.add_argument("--min-loss", type=float, default=0.02, help="only enqueue pairs with loss >= this")
    args = ap.parse_args()

    data = load()
    behind = [d for d in data if not d["we_hold_min"]]
    behind.sort(key=lambda d: -d["loss"])
    total_loss = sum(d["loss"] for d in behind)

    print(f"=== DEFENSE: {len(data)} held scoreable pairs; {len(behind)} behind on disc ===")
    print(f"  total RECOVERABLE score if we matched every rival's min disc: {total_loss:.1f}")
    print(f"  (cumulative loss in the top 50 / 200 / 500 pairs:", end=" ")
    for n in (50, 200, 500):
        print(f"{sum(d['loss'] for d in behind[:n]):.1f}", end="  ")
    print(")")

    print("\n  by teamCount k (weight 2^(1-k)):")
    byk = collections.Counter()
    lossk: dict = collections.defaultdict(float)
    for d in behind:
        byk[d["k"]] += 1
        lossk[d["k"]] += d["loss"]
    for k in sorted(byk):
        print(f"    k={k}: {byk[k]:5d} pairs, recoverable {lossk[k]:6.1f}  (weight {2**(1-k):.3f})")

    print("\n  by producer family (where our current best model came from):")
    fam = collections.Counter()
    lossf: dict = collections.defaultdict(float)
    for d in behind:
        f = family(d["source"])
        fam[f] += 1
        lossf[f] += d["loss"]
    for f, _ in sorted(lossf.items(), key=lambda x: -x[1])[:12]:
        print(f"    {f:10s}: {fam[f]:5d} pairs, recoverable {lossf[f]:6.1f}")

    print("\n  TOP 30 pairs by recoverable loss (t, r, k, ratio, loss, our->min disc digits, family):")
    for d in behind[:30]:
        od, mdg = len(str(d["ourDisc"])), len(str(d["minDisc"]))
        print(f"    24T{d['t']:>5} r{d['r']:>2} k={d['k']} ratio={d['ratio']:.3f} "
              f"loss={d['loss']:.3f} disc {od}d->{mdg}d  {family(d['source'])}")

    if args.enqueue:
        store.init()
        n = added = 0
        for d in behind:
            if d["loss"] < args.min_loss:
                break
            n += 1
            if n > args.enqueue:
                break
            tag = f"defend:{d['t']}.{d['r']}"
            payload = {"t": d["t"], "r": d["r"], "target_disc": d["minDisc"],
                       "our_disc": d["ourDisc"], "seed_source": d["source"]}
            if not store.has_target(tag) and store.enqueue("defend", payload, target=tag):
                added += 1
        store.set_priority_prefix("defend:", 150.0)  # above lit:* new (130) -- defense is cheap+high-value
        print(f"\n  enqueued {added} defend: targets (priority 150) for the disc-min searchers")


if __name__ == "__main__":
    main()
