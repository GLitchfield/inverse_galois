"""minblk=8 octic-over-cubic HARVEST-EXPANDED builder (test 0046).

Builds degree-24 candidates for the 7 PGL(2,7)-block (8T43) HARVEST-EXPANDED targets by
resolvent composition:

    F(X) = Res_y( c(y), f(a, y, X) )

where c(y) is a small-disc cubic of the target's block-3 type (3T2=S3 / 3T1=C3) and
f(a,t,X) is Malle Thm 5.1's PGL(2,7)=8T43 octic specialised at the octic parameter t = y.
Res_y over a cubic gives F = f(a,y1,X)*f(a,y2,X)*f(a,y3,X): three conjugate octic blocks
sitting over the cubic. GENERIC (disjoint) blocks => the FULL WREATH PGL(2,7) wr S3 = 24672
(S3 cubic) / PGL(2,7) wr C3 = 24592 (C3 cubic). The twist subgroups
(24593/24489/24594/24316/24488) are index-2/4/8 correlated-block subgroups and need block
correlation, not the plain disjoint Res -- see build_twist().

Family-sufficiency (scripts/mb8_family_suff.g, test 0046): all 33 open PGL pairs are reachable
by the plain a in {-1,-2} family over a (3,0) cubic (menu {0,2,8} per block); the 6 AGL pairs
(24922/24916) need the fix8 deformation (menu {0,4}) -> owned by the fix8 agent.

Local gates (all mandatory before enqueue): deg==24 & irreducible; polsturm r matches an OPEN
pair; density-consistent (L1 Frobenius cycle-type match, dist_<t>.txt) with the target and NOT
a neighbour; nfdisc computes (scoreable, not blank-only).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from igp import gp  # noqa: E402

MB8 = ROOT / "data" / "targets" / "mb8"

# Block-3 type per target (3T2=S3 non-square-disc cubic; 3T1=C3 always-real cyclic cubic).
CUBIC_TYPE = {24672: "S3", 24592: "C3", 24593: "S3", 24489: "C3",
              24594: "S3", 24316: "C3", 24488: "S3"}
# Open (teamCount==0) real-root menu per target, re-verified vs progress.json (2026-07-07).
OPEN_R = {24672: {8, 10, 12, 16, 18, 24}, 24592: {8, 12, 16, 18, 24},
          24593: {0, 4, 8, 12, 16, 24}, 24489: {0, 8, 12, 16, 24},
          24594: {4, 8, 12, 16, 24}, 24316: {8, 16, 24}, 24488: {8, 16, 24}}
FULL_WREATH = {24672: "S3", 24592: "C3"}   # generic disjoint-block Res lands these
TWIST = {24593, 24489, 24594, 24316, 24488}
# Density comparison pool: the new PGL targets + the sibling twist 24315 (Gassmann neighbour).
DIST_POOL = [24672, 24592, 24593, 24489, 24594, 24316, 24488, 24315]

# Malle Thm 5.1 PGL(2,7)=8T43 octic, parameters a (fixed) and t (= octic param, set to y).
OCTIC_PGL = ("X*(X^7+X^6+14*a*X^5+7*a*X^4+49*a^2*X^3+14*a^2*X^2+49*a^3*X+7*a^3)"
             "+t*(7*X^2+X+1)")


def _gp(script: str, timeout: float = 240.0) -> str:
    out = subprocess.run(["gp", "-q"], input="default(parisizemax,2*10^9);\n" + script,
                         capture_output=True, text=True, timeout=timeout)
    return out.stdout


SMOOTH_BOUND = 10**6   # SAIR's bounded poldisc factorization ceiling (disc scoring succeeds
#                        only if poldisc has no prime factor above this -> nfdisc terminates).


def build(cubic: list[int], a: int) -> dict | None:
    """cubic = ascending coeffs [c0,c1,c2,1]. Returns dict(coeffs, r, deg, smooth, cof_ndig).

    coeffs is the polredabs'd degree-24 field polynomial (ascending). ``smooth`` is True iff the
    POLDISC (not the field disc) factors fully below SMOOTH_BOUND -- the real scoreability gate:
    SAIR marks scoringReason=discriminant_pending and its bounded factorization only terminates
    (=> the pair scores) when poldisc is smooth. The field disc / nfdisc-completes locally even
    when poldisc carries a rough prime, so that gate (gp.scoreable_disc) is INSUFFICIENT."""
    cs = ",".join(str(c) for c in cubic)
    script = (
        f"a={a};\n"
        f"c=Pol(Vecrev([{cs}]),'y);\n"
        f"fp=subst({OCTIC_PGL},X,x);\n"        # octic in x, param t=y
        "fp=subst(fp,t,y);\n"
        "F=polresultant(c,fp,y);\n"
        "if(poldegree(F)!=24||!polisirreducible(F),print(\"BAD\");quit);\n"
        "Fr=polredabs(F);\n"
        f"pd=poldisc(Fr);fa=factor(abs(pd),{SMOOTH_BOUND});"
        "cof=abs(pd);for(i=1,matsize(fa)[1],cof=cof/fa[i,1]^fa[i,2]);\n"
        "print(poldegree(Fr));print(polsturm(Fr));print(#Str(cof));print(Vecrev(Fr));\n")
    out = _gp(script).strip().splitlines()
    if not out or out[0].strip() == "BAD" or len(out) < 4:
        return None
    try:
        deg = int(out[0]); r = int(out[1]); cof_ndig = int(out[2])
        coeffs = [int(x) for x in out[3].strip("[]").split(",")]
    except (ValueError, IndexError):
        return None
    if deg != 24 or len(coeffs) != 25 or coeffs[-1] != 1:
        return None
    return {"coeffs": coeffs, "r": r, "deg": deg, "smooth": cof_ndig == 1, "cof_ndig": cof_ndig}


# ---- density pre-check (Frobenius cycle-type distribution vs dist_<t>.txt) -----------------
def load_gdist(t: int) -> dict | None:
    fn = MB8 / f"dist_{t}.txt"
    if not fn.exists():
        return None
    order = None
    dist: dict = {}
    for ln in fn.read_text().splitlines():
        ln = ln.strip()
        if ln.startswith("order"):
            order = int(ln.split()[1]); continue
        if not ln or " " not in ln:
            continue
        key, cnt = ln.rsplit(" ", 1)
        ct = tuple(int(x) for x in key.split(","))
        dist[ct] = dist.get(ct, 0) + int(cnt)
    return {"order": order, "dist": dist}


GD = {t: g for t in DIST_POOL if (g := load_gdist(t)) is not None}


def poly_dist(coeffs: list[int], hi: int = 6000) -> tuple[dict, int]:
    cs = ",".join(str(c) for c in coeffs[::-1])   # descending for Pol
    body = (f"f=Pol([{cs}]);d=poldisc(f);lc=pollead(f);"
            f"forprime(p=3,{hi}, if(d%p!=0 && lc%p!=0, fa=factormod(f,p); "
            "if(vecmax(fa[,2])==1, print(vecsort(vector(matsize(fa)[1],i,poldegree(fa[i,1])))))));")
    out = _gp(body, timeout=300)
    tally: dict = {}; n = 0
    for ln in out.splitlines():
        ln = ln.strip()
        if not ln.startswith("["):
            continue
        ct = tuple(sorted(int(x) for x in ln.strip("[]").split(",") if x.strip()))
        if sum(ct) != 24:
            continue
        tally[ct] = tally.get(ct, 0) + 1; n += 1
    return tally, n


def density_rank(coeffs: list[int], hi: int = 6000) -> list[tuple]:
    tally, n = poly_dist(coeffs, hi)
    scored = []
    for t, g in GD.items():
        exp = {k: v / g["order"] for k, v in g["dist"].items()}
        obs = {ct: c / n for ct, c in tally.items()}
        keys = set(exp) | set(obs)
        l1 = sum(abs(obs.get(k, 0) - exp.get(k, 0)) for k in keys)
        impossible = sum(tally[ct] for ct in tally if ct not in g["dist"])
        scored.append((l1, t, impossible))
    scored.sort()
    return tally, n, scored


def density_ok(coeffs: list[int], target: int, hi: int = 6000) -> tuple[bool, str]:
    """target must be the best (or tied-best zero-impossible) L1 match with 0 impossible obs."""
    tally, n, scored = density_rank(coeffs, hi)
    if n < 8:
        return False, f"too few good primes ({n})"
    best_l1, best_t, best_imp = scored[0]
    tinfo = next((s for s in scored if s[1] == target), None)
    if tinfo is None:
        return False, "target not in dist pool"
    l1_t, _, imp_t = tinfo
    if imp_t > 0:
        return False, f"{imp_t} obs cycle-types impossible for {target}"
    ok = (best_t == target) or (l1_t - best_l1 < 0.02 and best_imp > 0)
    tag = f"L1[{target}]={l1_t:.3f} best={best_t}(L1={best_l1:.3f},imp={best_imp}) n={n}"
    return ok, tag


# ---- cubic pools ---------------------------------------------------------------------------
def s3_cubics() -> list[list[int]]:
    """Depressed cubics y^3 + p*y + q with disc=-4p^3-27q^2 > 0 (=> 3 real roots) and non-square
    (=> S3). Ascending [q, p, 0, 1]. A spread of root magnitudes to vary per-block real counts."""
    import math
    out = []
    for p in range(-2, -40, -1):
        for q in range(-30, 31):
            disc = -4 * p**3 - 27 * q**2
            if disc <= 0:
                continue
            r = int(math.isqrt(disc))
            if r * r == disc:            # square disc => C3, skip
                continue
            out.append([q, p, 0, 1])
    return out


def c3_cubics() -> list[list[int]]:
    """Shanks' simplest-cubic family y^3 - k*y^2 - (k+3)*y - 1, disc = (k^2+3k+9)^2 (C3, always 3
    real roots). Ascending [-1, -(k+3), -k, 1]. Also the k<0 branch for spread."""
    out = []
    for k in range(-25, 26):
        out.append([-1, -(k + 3), -k, 1])
    return out


def poly_line(coeffs: list[int]) -> str:
    return ",".join(str(c) for c in coeffs)


def sweep(target: int, a_values=(-2, -1), limit_per_r: int = 2, hi: int = 4000,
          density: bool = True) -> dict:
    """Build across the cubic pool x a-values, bucket by r, keep density-consistent candidates
    hitting an OPEN r. Returns {r: [ {coeffs,r,line,disc,cubic,a}, ... ]}."""
    cubics = s3_cubics() if CUBIC_TYPE[target] == "S3" else c3_cubics()
    want = OPEN_R[target]
    found: dict = {r: [] for r in want}
    seen_lines: set = set()
    for cub in cubics:
        for a in a_values:
            if all(len(found[r]) >= limit_per_r for r in want):
                return found
            b = build(cub, a)
            if b is None or b["r"] not in want:
                continue
            r = b["r"]
            if len(found[r]) >= limit_per_r:
                continue
            line = poly_line(b["coeffs"])
            if line in seen_lines:
                continue
            if not b["smooth"]:     # rough poldisc => SAIR disc scoring never terminates (gate #4)
                continue
            disc = gp.scoreable_disc(b["coeffs"], budget=55)
            if density:
                ok, tag = density_ok(b["coeffs"], target, hi=hi)
                if not ok:
                    print(f"    24T{target} r={r} cubic={cub} a={a} DENSITY-REJECT {tag}")
                    continue
            else:
                tag = "density-skipped"
            seen_lines.add(line)
            found[r].append({"coeffs": b["coeffs"], "r": r, "line": line, "disc": disc,
                             "cubic": cub, "a": a, "dens": tag})
            print(f"    24T{target} r={r} cubic={cub} a={a} disc~{disc} [{tag}] KEEP")
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="24672,24592",
                    help="comma list of the 7 PGL targets (full-wreaths 24672,24592 by default)")
    ap.add_argument("--limit-per-r", type=int, default=2)
    ap.add_argument("--a", default="-2,-1")
    ap.add_argument("--no-density", action="store_true")
    ap.add_argument("--hi", type=int, default=4000)
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()
    a_values = tuple(int(x) for x in args.a.split(","))
    targets = [int(x) for x in args.targets.split(",")]

    all_found: dict = {}
    for t in targets:
        if t in TWIST:
            print(f"NOTE 24T{t} is a TWIST target -- plain disjoint Res lands the full wreath, "
                  f"not the twist; needs correlated blocks (build_twist, not implemented). SKIP.")
            continue
        print(f"== sweep 24T{t} ({CUBIC_TYPE[t]}) open r={sorted(OPEN_R[t])} ==")
        found = sweep(t, a_values=a_values, limit_per_r=args.limit_per_r, hi=args.hi,
                      density=not args.no_density)
        all_found[t] = found
        for r in sorted(found):
            print(f"  24T{t} r={r}: {len(found[r])} candidate(s)")

    if args.enqueue:
        from igp import db
        from igp import searchstore as store
        store.init()
        realized = db.load_realized()
        held_pairs = {(str(x["t"]), str(x["r"])) for x in realized
                      if str(x.get("scoreable")).lower() == "true"}
        held_groups = {str(x["t"]) for x in realized
                       if str(x.get("scoreable")).lower() == "true"}
        added = {"new": 0, "pair": 0, "alt": 0}
        for t, found in all_found.items():
            for r, cands in found.items():
                for c in cands:
                    ts, rs = str(t), str(r)
                    tier = ("alt" if (ts, rs) in held_pairs
                            else ("pair" if ts in held_groups else "new"))
                    src = f"a{c['a']}c{'_'.join(str(x) for x in c['cubic'])}"
                    tag = f"lit:mb8{tier}:{ts}.{rs}:{src}"
                    if not store.has_target(tag) and store.enqueue(
                            "ready", {"coeffs": c["coeffs"]}, target=tag):
                        added[tier] += 1
        for tier, pri in {"new": 130.0, "pair": 115.0, "alt": 100.0}.items():
            store.set_priority_prefix(f"lit:mb8{tier}", pri)
        print(f"enqueued new {added['new']}@130 / pair {added['pair']}@115 / alt {added['alt']}@100")


if __name__ == "__main__":
    main()
