"""Drive the Hecke.fields constructive-Shafarevich enumerator (scripts/oscar/hecke_fields.jl)
to realize SOLVABLE degree-24 transitive groups, LOCAL-GATE the fields, and enqueue survivors.

The driver builds fields whose Galois group is EXACTLY the target by construction; the gate here
guards against (a) to_non_normal returning a different transitive type of the same group order,
(b) a wrong real-root count, (c) a blank-risk scoring disc, and -- critically for BASELINE pairs --
(d) a field disc that does not STRICTLY beat D_base (a tie never scores; test 0047).

Reproducibility: a realized poly records provenance src="lit:hecke:<t>.<r>:hecke".

Usage:
  python scripts/hecke_fields_build.py --t 32 --rs 0,8 [--seed 1e24] [--cap auto] \
      [--only-real 0] [--unram ""] [--enqueue]
The default cap is (max over the requested r of D_base(t,r)) - 1 so every returned field beats
baseline. --rs restricts which real-root counts we keep+enqueue (each gated on its own D_base).
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, "src")
from igp import baseline, db, gap, gp  # noqa: E402
from igp import searchstore as store  # noqa: E402

JULIA = os.path.expanduser("~/.juliaup/bin/julia")
DRIVER = "scripts/oscar/hecke_fields.jl"

_DIST_CACHE: dict[int, dict] = {}


def group_dist(t: int) -> dict:
    if t not in _DIST_CACHE:
        _DIST_CACHE.update(gap.cycle_type_distributions([t]))
    return _DIST_CACHE[t]


def run_driver(t: int, cap: int, only_real: int, unram: str, seed: int | None,
               timeout: float = 3000.0) -> list[dict]:
    args = [JULIA, "--startup-file=no", DRIVER, "24", str(t), str(cap),
            str(only_real), unram]
    if seed is not None:
        args.append(str(seed))
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    fields = []
    for ln in proc.stdout.splitlines():
        ln = ln.strip()
        if not ln.startswith("{"):
            continue
        obj = json.loads(ln)
        if "done" in obj:
            continue
        fields.append(obj)
    if proc.returncode != 0 and not fields:
        sys.stderr.write(proc.stderr[-2000:] + "\n")
    return fields


def poly_frobenius_tally(coeffs, hi: int = 4000) -> tuple[dict, int]:
    """Frobenius cycle-type tally of the ascending-coeff poly over unramified primes < hi."""
    cs = ",".join(map(str, coeffs[::-1]))
    body = (f"f=Pol([{cs}]);d=poldisc(f);lc=pollead(f);"
            f"forprime(p=3,{hi}, if(d%p!=0 && lc%p!=0, fa=factormod(f,p); "
            "if(vecmax(fa[,2])==1, print(vecsort(vector(matsize(fa)[1],i,poldegree(fa[i,1])))))));")
    out = subprocess.run(["gp", "-q"], input="default(parisizemax,2*10^9);\n" + body,
                         capture_output=True, text=True, timeout=180).stdout
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


def density_l1(tally: dict, n: int, t: int) -> tuple[float, int]:
    """L1 distance of the observed tally to the Chebotarev distribution of 24Tt, and the
    number of observed cycle types that are IMPOSSIBLE for 24Tt (a hard reject if > 0)."""
    g = group_dist(t)
    order = g["order"]
    exp = {k: v / order for k, v in g["dist"].items()}
    obs = {ct: c / n for ct, c in tally.items()}
    keys = set(exp) | set(obs)
    l1 = sum(abs(obs.get(k, 0) - exp.get(k, 0)) for k in keys)
    impossible = sum(1 for ct in tally if ct not in g["dist"])
    return l1, impossible


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--t", type=int, required=True)
    ap.add_argument("--rs", type=str, default="", help="comma-sep target real-root counts to keep")
    ap.add_argument("--cap", type=str, default="auto")
    ap.add_argument("--seed", type=str, default="")
    ap.add_argument("--only-real", type=int, default=0)
    ap.add_argument("--unram", type=str, default="")
    ap.add_argument("--l1-max", type=float, default=0.10)
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    t = args.t
    want_rs = {int(x) for x in args.rs.split(",") if x.strip()} if args.rs else None

    # cap = (max requested-r D_base) - 1  => every returned field strictly beats baseline.
    if args.cap == "auto":
        rs_for_cap = want_rs or {0, 24}
        dbs = [baseline.d_base(str(t), str(r)) for r in rs_for_cap]
        dbs = [d for d in dbs if d]
        if not dbs:
            print(f"24T{t}: no D_base for requested r -> non-baseline; use explicit --cap")
            return
        cap = max(dbs) - 1
    else:
        cap = int(float(args.cap)) if "e" in args.cap.lower() else int(args.cap)

    seed = None
    if args.seed:
        seed = int(float(args.seed)) if "e" in args.seed.lower() else int(args.seed)

    print(f"24T{t}: running Hecke.fields cap={cap} seed={seed} only_real={args.only_real}")
    fields = run_driver(t, cap, args.only_real, args.unram, seed)
    print(f"  driver returned {len(fields)} raw fields")

    winners = []
    for fobj in fields:
        coeffs = [int(c) for c in fobj["coeffs"]]
        hecke_disc = int(fobj["disc"])
        r_sig = int(fobj["r"])
        if want_rs is not None and r_sig not in want_rs:
            continue
        # polredabs to a small model
        try:
            red = gp.polredbest(coeffs)
        except Exception as e:  # noqa: BLE001
            print(f"    polredbest failed: {e}")
            continue
        # a. degree + irreducible
        deg = len(red) - 1
        if deg != 24:
            print(f"    reject: degree {deg} != 24")
            continue
        irr = gp.script(f"print(polisirreducible(Pol([{','.join(map(str, red[::-1]))}])))").strip()
        if irr not in ("1", "true"):
            print(f"    reject: not irreducible")
            continue
        # b. real-root count
        rr = gp.real_roots(red)
        if want_rs is not None and rr not in want_rs:
            print(f"    reject: polsturm r={rr} not in {want_rs}")
            continue
        # c. density label consistency with 24Tt
        tally, npr = poly_frobenius_tally(red)
        if npr < 60:
            print(f"    reject: too few good primes ({npr})")
            continue
        l1, imp = density_l1(tally, npr, t)
        if imp > 0 or l1 > args.l1_max:
            print(f"    reject: density L1={l1:.4f} impossible={imp} (not 24T{t})")
            continue
        # d. scoreable disc, and STRICT baseline beat
        sdisc = gp.scoreable_disc(red)
        if sdisc is None:
            print(f"    reject: scoreable_disc blank-risk")
            continue
        if not baseline.beats_baseline(str(t), str(rr), sdisc):
            db_r = baseline.d_base(str(t), str(rr))
            print(f"    reject: disc {sdisc} does NOT beat D_base {db_r} for r={rr} (baseline floor)")
            continue
        winners.append({"t": t, "r": rr, "coeffs": red, "disc": sdisc,
                        "hecke_disc": hecke_disc, "l1": round(l1, 4)})
        print(f"    WIN 24T{t} r={rr} disc={sdisc} (< D_base) L1={l1:.4f}")

    print(f"24T{t}: {len(winners)} gated winners")

    if args.enqueue and winners:
        store.init()
        realized = db.load_realized()
        held_groups = {int(rw["t"]) for rw in realized
                       if str(rw.get("scoreable")).lower() == "true"}
        held_pairs = {(int(rw["t"]), int(rw["r"])) for rw in realized
                      if str(rw.get("scoreable")).lower() == "true"}
        tiers = {"new": 130.0, "pair": 115.0, "alt": 100.0}
        added = {"new": 0, "pair": 0, "alt": 0}
        for w in winners:
            key = (w["t"], w["r"])
            tier = "alt" if key in held_pairs else ("pair" if w["t"] in held_groups else "new")
            tag = f"lit:hecke{tier}:{w['t']}.{w['r']}:hecke"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": w["coeffs"]}, target=tag):
                added[tier] += 1
        for tier, pri in tiers.items():
            store.set_priority_prefix(f"lit:hecke{tier}", pri)
        print(f"  enqueued new {added['new']}@130 pair {added['pair']}@115 alt {added['alt']}@100")


if __name__ == "__main__":
    main()
