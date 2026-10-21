"""gen12 TOTALLY-POSITIVE r=24 producer (dive #31 / test 00NN).

Builds DETERMINISTIC r=24 degree-24 fields for the biggest open slice of the board -- the ~10k open
r=24 minblk=2 pairs. Mechanism (VERIFIED dive #31): K = F(sqrt(alpha)) over a TOTALLY-REAL deg-12
base F has r(K) = 2*#{real places v : alpha >_v 0}, so r=24 iff alpha is totally positive; the
sign-fix unit-lattice solve in ``gp.general_c2_totpos`` forces that. Over an h+=1 base EVERY (w,q)
yields r=24; over h+>1 bases the per-alpha ``matsolvemod`` skips the narrowly-non-principal classes
(still all-r=24, lower yield).

This is a BREADTH producer: it lands *some* open (t,24) minblk=2 group per build (K always has the
deg-12 subfield F => 12 blocks of size 2 => minblk=2, and r is forced to 24), open-gated at the
SHAPE level via the gen12 atlas. It does NOT target a fixed 24Tt -- the sign-fixing unit changes
alpha's square class, so the exact group is re-learned from SAIR's Magma label downstream (that is
the authoritative gate). Enqueues ``ready`` concrete polys tagged ``gen12treal:totpos:...`` so they
feed the existing gen12_treal atlas/accounting.

Local gate (HARD): deg-24 irreducible, polsturm == 24, gp.scoreable_disc non-blank. Reproducible:
    .venv/bin/python scripts/gen12_totpos_producer.py --enqueue --max-enqueue 15
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from igp import atlas, baseline, db, gp, lmfdb  # noqa: E402
from igp import searchstore as store  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PROG = ROOT / "data" / "processed" / "progress.json"

TAG_PREFIX = "gen12treal:totpos"


def _w_patterns():
    from itertools import combinations
    idxs = ([(0,)]
            + list(combinations(range(12), 2))[:14]
            + list(combinations(range(8), 3))[:10]
            + list(combinations(range(6), 4))[:5])
    return [[1 if k in idx else 0 for k in range(12)] for idx in idxs]


def _open_r24_groups(prog: dict, held: set) -> set:
    """t such that (t,24) is teamCount==0, non-baseline (or beats-baseline unknown here => require
    non-baseline), and not already held by us -- a genuine sole-1.0 target at r=24."""
    out = set()
    for key, e in prog.items():
        if "," not in key:
            continue
        t_s, r_s = key.split(",")
        if r_s != "24":
            continue
        t = int(t_s)
        if (t, 24) in held or baseline.is_baseline(t, 24):
            continue
        if e.get("teamCount", 9) == 0:
            out.add(t)
    return out


def _local_gate(coeffs) -> tuple[bool, str]:
    """HARD structural gate: deg-24, irreducible, polsturm == 24. Returns (ok, detail)."""
    cs = ",".join(str(c) for c in coeffs[::-1])
    body = (f"f=Pol([{cs}]);print(poldegree(f),\" \",polisirreducible(f),\" \",polsturm(f))")
    out = gp._run_gp(body, timeout=60).strip()
    try:
        deg, irr, sturm = out.split()
        ok = (int(deg) == 24 and int(irr) == 1 and int(sturm) == 24)
        return ok, f"deg={deg} irr={irr} sturm={sturm}"
    except ValueError:
        return False, f"gate-parse-fail: {out[:40]}"


def run(max_enqueue: int, max_builds: int, hi: int, n_primes: int, per_group: int,
        enqueue: bool, per_q_cap: int = 2) -> dict:
    store.init()
    prog = json.loads(PROG.read_text())
    held = {(int(r["t"]), int(r["r"])) for r in db.load_realized()
            if r.get("label", "").startswith("24T")}
    open24 = _open_r24_groups(prog, held)
    # atlas over both treal + plain gen12 shapes (label knowledge is shared: same base:w map)
    amap = {}
    try:
        amap.update(atlas.classify(prog, held, prefix="gen12:"))
        amap.update(atlas.classify(prog, held, prefix="gen12treal:"))
    except Exception as e:  # noqa: BLE001
        print(f"atlas unavailable ({str(e)[:50]}); shape-gating disabled")

    off = int(store.get_kv("gen12totpos_offset", 0))
    bases = lmfdb.fields(12, max_r2=0, class_number=1, per_group=per_group,
                         limit=max(60, max_builds * 3), offset=off)
    if not bases:
        off = 0
        bases = lmfdb.fields(12, max_r2=0, class_number=1, per_group=per_group,
                             limit=max(60, max_builds * 3))

    pats = _w_patterns()
    enq = 0
    builds = 0
    rows = []
    for coeffs, label, disc, _h in bases:
        if enq >= max_enqueue or builds >= max_builds:
            break
        try:
            hplus = gp.narrow_class_number(coeffs, timeout=200)
        except Exception:  # noqa: BLE001
            continue
        if hplus != 1:
            rows.append({"base": label, "skip": f"h+={hplus}"})
            continue
        try:
            qs = gp.split_primes(coeffs, 12, k=n_primes, hi=hi)
        except Exception:  # noqa: BLE001
            qs = []
        if not qs:
            rows.append({"base": label, "skip": "no-split-prime"})
            continue
        for q in qs:
            if enq >= max_enqueue or builds >= max_builds:
                break
            per_q = 0
            for w in pats:
                if enq >= max_enqueue or builds >= max_builds or per_q >= per_q_cap:
                    break
                wtag = "".join(map(str, w))
                shape = f"gen12treal:{label}:{wtag}"
                info = amap.get(shape) or amap.get(f"gen12:{label}:{wtag}")
                if info is not None:
                    b = sum(info["labels"].values())
                    if info["open_pairs"] == 0 and b >= 8:
                        continue  # known-dead shape
                    # prefer shapes whose reachable labels have (t,24) open
                    r24 = sum(1 for t in info["labels"] if t in open24)
                    if b >= 20 and r24 == 0 and info["open_pairs"] < 0.2:
                        continue
                builds += 1
                try:
                    c = gp.general_c2_totpos(coeffs, w, q, timeout=300)
                except Exception:  # noqa: BLE001
                    continue
                if not c or len(c) != 25:
                    continue
                ok, detail = _local_gate(c)
                if not ok:
                    rows.append({"base": label, "w": wtag, "q": q, "reject": detail})
                    continue
                sd = gp.scoreable_disc(c, ascending=True)
                if sd is None:
                    rows.append({"base": label, "w": wtag, "q": q, "reject": "blank-disc"})
                    continue
                tag = f"{TAG_PREFIX}:{label}:d{disc}:q{q}:{wtag}"
                if store.has_target(tag):
                    continue
                rec = {"base": label, "w": wtag, "q": q, "disc": sd, "coeffs": c, "tag": tag}
                rows.append(rec)
                per_q += 1
                if enqueue:
                    if store.enqueue("ready", {"coeffs": c}, target=tag):
                        enq += 1
                else:
                    enq += 1  # dry-run count
    if enqueue:
        store.set_kv("gen12totpos_offset", off + len(bases))
        store.set_priority_prefix("gen12treal", 128.0)
    return {"enqueued": enq, "builds": builds, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--enqueue", action="store_true")
    ap.add_argument("--max-enqueue", type=int, default=15)
    ap.add_argument("--max-builds", type=int, default=40)
    ap.add_argument("--hi", type=int, default=60000)
    ap.add_argument("--n-primes", type=int, default=2)
    ap.add_argument("--per-group", type=int, default=2)
    ap.add_argument("--per-q-cap", type=int, default=2)
    args = ap.parse_args()
    res = run(args.max_enqueue, args.max_builds, args.hi, args.n_primes, args.per_group,
              args.enqueue, args.per_q_cap)
    for r in res["rows"]:
        print(" ", json.dumps(r if "coeffs" not in r else {**r, "coeffs": "..."}))
    print(f"gen12_totpos: builds={res['builds']} enqueued={res['enqueued']} "
          f"({'LIVE' if args.enqueue else 'DRY'})")


if __name__ == "__main__":
    main()
