"""minblk=8 AFFINE CLUSTER builder -- Route A (Malle Thm 6.1 AGL(3,2) octic over a cubic).

VALIDATION-FIRST FINDING (test 0045, 2026-07-07). The greenlit recipe
``deg24 = Res_y(c(y), f_AGL(a,y,X))`` (specialize the Malle Thm 6.1 AGL(3,2)=8T48 octic
family at t = a cubic generator) does **NOT** build the six twisted affine targets. The
direct resultant lands the FULL WREATH:

    C3 cubic  ->  AGL(3,2) wr C3 = 24T24916  (|G| = 7,283,146,752)
    S3 cubic  ->  AGL(3,2) wr S3 = 24T24922  (|G| = 14,566,293,504)

confirmed three independent ways: GAP group order, order-9 Frobenius (cycle type 3,3,9,9
at ~12% of primes -- IMPOSSIBLE in the twisted targets, whose max element order is 21),
and density L1 (candidate matches 24916/24922 at L1~=0.2 with ZERO impossible cycle types,
vs >1.0 with hundreds of impossibles for every 14051/14052/16060/16061/19280/20408).

The twisted targets have the three PSL(3,2) linear parts COLLAPSED to one diagonal
(kernel (C2)^6 for 14051/14052/16060/16061, (C2)^9=3(+)6 for 19280/20408). That diagonal
correlation is NOT produced by the generic (disjoint-conjugate-block) resultant; it needs
the Route-B construction (a shared-L3(2) relative Kummer over the cubic -- a degree-168
class-group build, out of PARI's reach here). So the mandatory density gate below REFUSES
to enqueue any Route-A candidate as a twisted target: for those six targets this producer
correctly emits nothing.

The module is still a usable Route-A builder for the full wreaths (should the reachable
open pairs -- 24916/24922 r{16,20,24} -- ever be wanted) and a reusable density-gate /
labeler harness for a future Route-B build.

Usage:
    python scripts/mb8_affine.py --target 24916 --cubic C3 --a-lo -6 --a-hi 6
    python scripts/mb8_affine.py --target 19280 --cubic C3 --a-lo -6 --a-hi 6   # emits nothing (Route-B-blocked)
    ... add --enqueue to push density-consistent candidates to the daemon queue.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from igp import gp  # noqa: E402

DIST_DIR = ROOT / "data" / "targets" / "mb8"
# every 24T we can distinguish a Route-A candidate against (twisted cluster + full wreaths)
TARGETS = [14051, 14052, 16060, 16061, 19280, 20408, 24315, 24916, 24922]

# Malle, "Multi-parameter polynomials with given Galois group" (pargal.pdf), Thm 6.1:
# genus/2-param AGL(3,2)=8T48 octic family. Certified 8T48 locally at (a,t)=(1,1).
FAMILY = "X^4*(X^2 + a*X + 2*a)*(X-2)^2 + 't*((a-5)*(X^2+X) - 2*a - 2)*(X-1)^2"

CUBICS = {
    "C3": "y^3 - y^2 - 2*y + 1",      # cyclic, disc 49 (square) -> top C3 -> full wreath 24916
    "S3": "y^3 - y^2 - 3*y + 1",      # totally-real S3, disc 148 (non-square) -> 24922
    "S3cx": "y^3 - y - 1",            # complex S3, disc -23
}


# ---- density labeler (self-contained; reads data/targets/mb8/dist_<t>.txt) -----------

def load_gdist() -> dict:
    gd = {}
    for t in TARGETS:
        fn = DIST_DIR / f"dist_{t}.txt"
        if not fn.exists():
            continue
        order, dist = None, {}
        for ln in fn.read_text().splitlines():
            ln = ln.strip()
            if ln.startswith("order"):
                order = int(ln.split()[1])
                continue
            if not ln or " " not in ln:
                continue
            key, cnt = ln.rsplit(" ", 1)
            try:
                ct = tuple(int(x) for x in key.split(","))
            except ValueError:
                continue
            dist[ct] = dist.get(ct, 0) + int(cnt)
        gd[t] = {"order": order, "dist": dist}
    return gd


GD = load_gdist()


def poly_dist(coeffs_asc: list[int], hi: int = 6000) -> tuple[dict, int]:
    """Frobenius cycle-type tally over unramified primes p<hi (squarefree factorizations)."""
    cs = ",".join(map(str, coeffs_asc[::-1]))  # descending for Pol
    body = (f"f=Pol([{cs}]);d=poldisc(f);lc=pollead(f);"
            f"forprime(p=3,{hi}, if(d%p!=0 && lc%p!=0, fa=factormod(f,p); "
            "if(vecmax(fa[,2])==1, print(vecsort(vector(matsize(fa)[1],i,poldegree(fa[i,1])))))));")
    out = subprocess.run(["gp", "-q"], input="default(parisizemax,4*10^9);\n" + body,
                         capture_output=True, text=True, timeout=300).stdout
    tally, n = {}, 0
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


def label(coeffs_asc: list[int], hi: int = 6000):
    """Return (best_t, sorted_scores) where scores = [(L1, t, impossible_obs), ...]."""
    tally, n = poly_dist(coeffs_asc, hi)
    scored = []
    for t in TARGETS:
        gd = GD[t]["dist"]
        order = GD[t]["order"]
        exp = {k: v / order for k, v in gd.items()}
        obs = {ct: c / n for ct, c in tally.items()}
        keys = set(exp) | set(obs)
        l1 = sum(abs(obs.get(k, 0) - exp.get(k, 0)) for k in keys)
        impossible = sum(tally[ct] for ct in tally if ct not in gd)
        scored.append((l1, t, impossible))
    scored.sort()
    return (scored[0][1] if scored else None), scored, n


# ---- Route-A build --------------------------------------------------------------------

def build(cubic: str, a) -> tuple[list[int], int] | None:
    """deg-24 Res_y(c(y), f(a,y,X)), polredbest'd. Returns (ascending coeffs, r) or None."""
    body = (
        "default(parisizemax,6*10^9);\n"
        f"fT(a) = {FAMILY};\n"
        f"c = {cubic};\n"
        f"R = polresultant(c, subst(fT({a}),'t,y), y);\n"
        "if(R==0, print(\"DEGEN\"), R=R/content(R);"
        "if(poldegree(R)!=24 || !polisirreducible(R), print(\"BAD\"),"
        "rb=polredbest(R); print(polsturm(rb)); print(Vec(rb))));"
    )
    out = gp.script(body, timeout=240)
    lines = [ln.strip() for ln in out.splitlines() if ln.strip() and "Warning" not in ln]
    if not lines or lines[0] in ("DEGEN", "BAD"):
        return None
    try:
        r = int(lines[0])
        desc = [int(x) for x in lines[1].strip("[]").split(",")]
    except (ValueError, IndexError):
        return None
    if len(desc) != 25:
        return None
    return desc[::-1], r  # ascending


# ---- gate + drive ---------------------------------------------------------------------

def gate(coeffs_asc, target_t: int, target_r: int, hi: int = 6000):
    """Mandatory local gates. Returns (ok, verdict_dict)."""
    v = {"deg": len(coeffs_asc) - 1, "irred": True}  # build() only returns irreducible deg-24
    v["r"] = target_r
    best_t, scored, n = label(coeffs_asc, hi)
    v["density_best"] = best_t
    v["density_L1"] = round(scored[0][0], 4)
    v["density_impossible"] = next(imp for l1, t, imp in scored if t == target_t)
    v["n_primes"] = n
    sd = gp.scoreable_disc(coeffs_asc)
    v["scoreable_disc"] = sd
    ok = (v["deg"] == 24
          and best_t == target_t
          and v["density_impossible"] == 0
          and sd is not None)
    return ok, v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, required=True)
    ap.add_argument("--cubic", choices=list(CUBICS), default="C3")
    ap.add_argument("--a-lo", type=int, default=-6)
    ap.add_argument("--a-hi", type=int, default=6)
    ap.add_argument("--r", type=int, default=None, help="only keep candidates with this r (else any)")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    winners = []  # (coeffs_asc, r, verdict)
    for a in range(args.a_lo, args.a_hi + 1):
        res = build(CUBICS[args.cubic], a)
        if res is None:
            print(f"a={a}: degenerate/reducible -- skip")
            continue
        coeffs, r = res
        if args.r is not None and r != args.r:
            print(f"a={a}: r={r} != target r={args.r} -- skip")
            continue
        ok, v = gate(coeffs, args.target, r)
        tag = "PASS" if ok else "REJECT"
        print(f"a={a}: r={r} density_best=24T{v['density_best']} "
              f"L1={v['density_L1']} impossible={v['density_impossible']} "
              f"sd={'ok' if v['scoreable_disc'] else 'BLANK'} -> {tag}")
        if ok:
            winners.append((coeffs, r, v))

    print(f"\n{len(winners)} density-consistent candidate(s) for 24T{args.target}")
    if not winners:
        print("(none -- expected for the twisted targets: Route A builds the full wreath, "
              "not the diagonal-collapsed twist; those need Route B.)")
        return

    if args.enqueue:
        sys.path.insert(0, str(ROOT / "src"))
        from igp import searchstore as store, db
        store.init()
        realized = db.load_realized()
        held_groups = {r["t"] for r in realized if str(r.get("scoreable")).lower() == "true"}
        held_pairs = {(r["t"], r["r"]) for r in realized if str(r.get("scoreable")).lower() == "true"}
        tiers = {"new": 130.0, "pair": 115.0, "alt": 100.0}
        added = {"new": 0, "pair": 0, "alt": 0}
        for coeffs, r, _v in winners:
            t, rs = str(args.target), str(r)
            tier = "alt" if (t, rs) in held_pairs else ("pair" if t in held_groups else "new")
            line = ",".join(map(str, coeffs))
            src = f"{args.cubic}a"
            tag = f"lit:mb8{tier}:{t}.{rs}:{src}"
            if not store.has_target(tag) and store.enqueue("ready", {"coeffs": line}, target=tag):
                added[tier] += 1
        for tier, pri in tiers.items():
            store.set_priority_prefix(f"lit:mb8{tier}", pri)
        print(f"enqueued new {added['new']}@130 pair {added['pair']}@115 alt {added['alt']}@100")


if __name__ == "__main__":
    main()
