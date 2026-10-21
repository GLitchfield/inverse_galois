"""defend_harden -- GROUP-PRESERVING disc-defense for gen12 SHARED (behind) pairs (2026-07-07).

Context (test 0051): the base-SWAP defense (defend_producer.py) FAILED 0/390 on-target -- rebuilding a
behind pair over a *different* smaller-disc base of the same top lands a DIFFERENT 24Tt, because
idealprimedec's prime ordering is non-canonical across bases, so the w-index picks a different kernel
submodule (test 0038 alignment). The one path that PRESERVES the group is `produce_harden`'s
same-base-smaller-prime rebuild (search_ctl.py): reuse the EXACT base + EXACT w that our held model
was built from, only lower the completely-split prime q. Over one fixed base the Galois action on the
12 primes above any completely-split q is the same abstract G-set, so the same w selects the same
submodule -> the 24Tt is preserved (the split prime is only the disc size + the r-dial, test 0036).

This extends that group-preserving harden from our SOLE 1.0s (what search_ctl.produce_harden covers) to
the gen12 SHARED behind pairs (teamCount k in 2..5) where a rival holds a smaller FIELD disc. Harden
canNOT close a base-disc gap (a rival on a genuinely smaller base wins the base^2 floor) -- it only
recovers the *prime-dominated* slack, i.e. pairs whose held model used a lazy large split prime. So it
targets the small-gap subset and recovers PARTIAL ratio (74d->~55d is a base^2-floored win, not 74->34).

Local gate (budget-safe, does NOT rely on Magma to sort garbage):
  (1) deg-24 irreducible (guaranteed by rnfequation of a field),
  (2) polsturm == target r (the smaller prime can change r; keep only r-matches),
  (3) local nfdisc STRICTLY < our held field disc (never enqueue a model >= ours),
  (4) GROUP PRESERVED: the candidate's Frobenius cycle-type density L1-matches our OWN held model's
      density (both empirical, same sampling -> the fingerprint-noise cancels; same group => small L1).
Survivors enqueue as `ready` at target `defend:<t>.<r>:harden:q<q>`, priority 150.

Usage:
  python scripts/defend_harden.py --limit 15            # validate (no enqueue): per-pair outcome
  python scripts/defend_harden.py --limit 400 --enqueue  # build + enqueue survivors
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import defend_producer  # noqa: E402  (reuse sweep_base: fixed-w general_c2 over a base, bnfinit amortized)
from igp import gp  # noqa: E402
from igp import searchstore as store  # noqa: E402

POOL = ROOT / "data" / "processed" / "defend_harden_pool.json"
CKPT = ROOT / "data" / "processed" / "defend_harden_winners.jsonl"


def build_pool():
    """Regenerate the behind-gen12 pool (base + w + old_q per pair) from realized.csv + the queue.

    A behind pair = a held scoreable gen12 (t,r) where a rival holds a smaller FIELD disc (ratio<1),
    k in 2..5, weight>=0.06. We join its best held-model coeffs to the verified general_c2 queue row
    to recover the exact (base, w, q) it was built from -- the harden rebuild reuses base+w verbatim.
    """
    import sqlite3

    import defend_held
    from igp import db
    data = defend_held.load()
    behind = [d for d in data if not d["we_hold_min"]]
    cand = [d for d in behind if defend_held.family(d["source"]) == "gen12"
            and 2 <= d["k"] <= 5 and d["weight"] >= 0.06]
    best_coeffs: dict = {}
    for r in db.load_realized():
        if str(r.get("scoreable")).lower() != "true":
            continue
        fd = r.get("field_disc", "")
        if not fd.lstrip("-").isdigit():
            continue
        key = (str(r["t"]), str(r["r"]))
        dd = abs(int(fd))
        if key not in best_coeffs or dd < best_coeffs[key][1]:
            best_coeffs[key] = (r["coeffs"], dd)
    info: dict = {}
    for d in cand:
        key = (str(d["t"]), str(d["r"]))
        if key in best_coeffs:
            coeffs = best_coeffs[key][0]
            info[coeffs] = {"t": key[0], "r": key[1], "ourDisc": d["ourDisc"],
                            "minDisc": d["minDisc"], "loss": d["loss"], "k": d["k"],
                            "ratio": d["ratio"], "weight": d["weight"], "line": coeffs}
    recov: dict = {}
    with sqlite3.connect(store.DB) as c:
        c.row_factory = sqlite3.Row
        for row in c.execute("SELECT payload,line FROM queue WHERE status='verified' "
                             "AND line IS NOT NULL AND kind='general_c2'"):
            if row["line"] in info and row["line"] not in recov:
                recov[row["line"]] = json.loads(row["payload"])
    out = []
    for line, payload in recov.items():
        rec = dict(info[line])
        rec["base"], rec["w"], rec["old_q"] = payload.get("base"), payload.get("w"), payload.get("q")
        out.append(rec)
    POOL.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(POOL, "w"))
    return out


def frob_density(coeffs, hi: int = 12000, timeout: float = 240.0):
    """Frobenius cycle-type tally of an ascending-coeff deg-24 poly over unramified primes < hi."""
    cs = ",".join(map(str, coeffs[::-1]))
    body = (f"f=Pol([{cs}]);d=poldisc(f);lc=pollead(f);"
            f"forprime(p=3,{hi}, if(d%p!=0 && lc%p!=0, fa=factormod(f,p);"
            "if(vecmax(fa[,2])==1, print(vecsort(vector(matsize(fa)[1],i,poldegree(fa[i,1])))))));")
    try:
        out = subprocess.run(["gp", "-q"], input="default(parisizemax,4*10^9);\n" + body,
                             capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return {}, 0
    tally: dict = {}
    n = 0
    for ln in out.splitlines():
        ln = ln.strip()
        if not ln.startswith("["):
            continue
        ct = tuple(sorted(int(x) for x in ln.strip("[]").split(",") if x.strip()))
        if sum(ct) != 24:
            continue
        tally[ct] = tally.get(ct, 0) + 1
        n += 1
    return tally, n


def l1(a, na, b, nb):
    pa = {k: v / na for k, v in a.items()}
    pb = {k: v / nb for k, v in b.items()}
    keys = set(pa) | set(pb)
    return sum(abs(pa.get(k, 0) - pb.get(k, 0)) for k in keys)


def harden_pair(rec, *, n_primes: int = 10, hi: int = 20000, per_pair: int = 2,
                l1_max: float = 0.35):
    """Build up to `per_pair` strictly-smaller-disc, GROUP-PRESERVED models for one behind pair."""
    t, r = rec["t"], rec["r"]
    target_r = int(r)
    base, w = rec["base"], rec["w"]
    old_q = int(rec["old_q"]) if rec["old_q"] else 10 ** 9
    our_disc = int(rec["ourDisc"])
    held_coeffs = [int(x) for x in rec["line"].split(",")]
    if not base or not w:
        return {"t": t, "r": r, "status": "no_payload"}
    try:
        primes = [q for q in gp.split_primes(base, 12, k=n_primes, hi=hi) if q < old_q]
    except Exception:
        primes = []
    if not primes:
        return {"t": t, "r": r, "status": "no_smaller_prime", "old_q": old_q}
    cands = [c for c in defend_producer.sweep_base(base, w, primes) if c[1] == target_r]
    cands.sort(key=lambda c: c[0])  # smallest prime first (usually smallest disc)
    smaller = []
    for q, rr, poly in cands:
        try:
            fd = gp.scoreable_disc(poly)
        except Exception:
            fd = None
        if fd is None or not str(fd).lstrip("-").isdigit():
            continue  # blank-risk model: skip (never enqueue a blank-only disc)
        fda = abs(int(fd))
        if fda < our_disc:
            smaller.append((fda, q, poly))
        if len(smaller) >= per_pair * 3:
            break
    if not smaller:
        return {"t": t, "r": r, "status": "no_smaller_disc", "old_q": old_q,
                "n_prime_matches": len(cands)}
    smaller.sort()
    # group-preservation gate: density vs our OWN held model (same group => small L1)
    held_t, held_n = frob_density(held_coeffs)
    if held_n < 300:
        return {"t": t, "r": r, "status": "held_density_failed"}
    winners = []
    for fda, q, poly in smaller:
        ct, n = frob_density(poly)
        if n < 300:
            continue
        d = l1(ct, n, held_t, held_n)
        if d <= l1_max:
            winners.append({"field_disc": fda, "field_dig": len(str(fda)), "q": q,
                            "coeffs": poly, "l1": round(d, 3)})
        if len(winners) >= per_pair:
            break
    if not winners:
        best_l1 = None
        for fda, q, poly in smaller[:2]:
            ct, n = frob_density(poly)
            if n >= 300:
                dd = l1(ct, n, held_t, held_n)
                best_l1 = dd if best_l1 is None else min(best_l1, dd)
        return {"t": t, "r": r, "status": "group_not_preserved", "old_q": old_q,
                "best_l1": None if best_l1 is None else round(best_l1, 3),
                "our_dig": len(str(our_disc)), "smaller_dig": len(str(smaller[0][0]))}
    return {"t": t, "r": r, "top": None, "status": "improved", "old_q": old_q,
            "our_dig": len(str(our_disc)), "winners": winners[:per_pair],
            "loss": rec["loss"], "k": rec["k"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enqueue", action="store_true")
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--per-pair", type=int, default=2)
    ap.add_argument("--l1-max", type=float, default=0.35)
    ap.add_argument("--only", type=str, default="")
    ap.add_argument("--build-pool", action="store_true", help="force-regenerate the behind pool")
    args = ap.parse_args()

    if args.build_pool or not POOL.exists():
        print("building behind-gen12 pool ...", flush=True)
        build_pool()
    pool = json.load(open(POOL))
    pool.sort(key=lambda x: -x["loss"])
    if args.only:
        want = set(args.only.split(","))
        pool = [d for d in pool if f"{d['t']}.{d['r']}" in want]
    pool = pool[:args.limit]

    print(f"=== DEFEND-HARDEN gen12 shared: {len(pool)} behind pairs, enqueue={args.enqueue} ===",
          flush=True)
    if args.enqueue:
        store.init()
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    ck = open(CKPT, "a")
    t0 = time.time()
    status_ct: dict = {}
    improved = enqueued = dig_reduced = 0
    for i, rec in enumerate(pool):
        res = harden_pair(rec, per_pair=args.per_pair, l1_max=args.l1_max)
        status_ct[res["status"]] = status_ct.get(res["status"], 0) + 1
        if res["status"] == "improved":
            improved += 1
            best = res["winners"][0]
            dig_reduced += res["our_dig"] - best["field_dig"]
            print(f"  [{i+1}/{len(pool)}] 24T{res['t']} r{res['r']} k={res['k']} "
                  f"disc {res['our_dig']}d->{best['field_dig']}d q{res['old_q']}->q{best['q']} "
                  f"L1={best['l1']} nwin={len(res['winners'])}", flush=True)
            for wn in res["winners"]:
                ck.write(json.dumps({"t": res["t"], "r": res["r"], **wn}) + "\n")
                ck.flush()
                if args.enqueue:
                    tag = f"defend:{res['t']}.{res['r']}:harden:q{wn['q']}"
                    if store.enqueue("ready", {"coeffs": wn["coeffs"]}, target=tag):
                        enqueued += 1
        else:
            print(f"  [{i+1}/{len(pool)}] 24T{res['t']} r{res['r']} -> {res['status']}"
                  + (f" (best_l1={res.get('best_l1')})" if res["status"] == "group_not_preserved"
                     else ""), flush=True)
    ck.close()
    if args.enqueue and enqueued:
        store.set_priority_prefix("defend:", 150.0)
    print(f"\n=== SUMMARY ===")
    print(f"  attempted:  {len(pool)}")
    print(f"  improved (smaller-disc, group-preserved): {improved}")
    print(f"  disc digits reduced (sum best): {dig_reduced}")
    print(f"  status breakdown: {status_ct}")
    print(f"  enqueued:   {enqueued} defend:harden ready polys (priority 150)")
    print(f"  elapsed:    {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
