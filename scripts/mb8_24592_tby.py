"""mb8 (24592,8) via the t=B(y) two-parameter Res (dive #25, test 0060).

test 0059 proved (24592,8)=(8,0,0) is UNREACHABLE with the octic param t=y: over a real
cyclic-C3 base the three cubic roots are one 120-degree-rotation orbit, so at most one can
enter the octic's one-sided 0-region -> two 0-blocks impossible. Dive #25 BREAKS that by
setting the octic parameter to a QUADRATIC in the cubic generator, t = B(y) = b0+b1*y+b2*y^2
(so t in k, the base field): the three per-block params become conjugates of a free base-field
element, Minkowski-dense in R^3, so (8-window, 0-region, 0-region) IS reachable.

    F(X) = Res_y( c(y), f_Malle(a, B(y), X) )     f_Malle = Malle Thm-5.1 8T43 octic.

Reuses the mb8_harvest build primitives (density_ok / poly_line / scoreable_disc), only
swapping the octic-param substitution t=y for t=B(y). Local gate identical to test 0059:
deg-24 irreducible, polsturm==8, poldisc 10^6-smooth (scoreable), Frobenius-density label
consistent with 24592 (not a Gassmann neighbour). Target (24592,8): teamCount==0 OPEN,
non-baseline -> scores a sole-1.0 on any valid disc.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import mb8_harvest as M  # noqa: E402  (density_ok / poly_line / gp / OCTIC_PGL / SMOOTH_BOUND)

TARGET, R = 24592, 8

# (cubic ascending [c0,c1,c2,1], a, B=[b0,b1,b2]) configs dive #25 verified reachable.
# Champion first (fully local-gated in the dive); the rest are robustness / disc-min sweep.
CONFIGS = [
    ([-1, -2, 1, 1], -3, [455, 90, -75]),   # champion: c=y^3+y^2-2y-1 (Q(zeta7)+), a=-3
    ([-1, -2, 1, 1], -3, [65, 106, 162]),
    ([-1, -2, 1, 1], -3, [395, -165, -90]),
    ([-1, -2, 1, 1], -3, [562, 94, -102]),
    ([-1, -2, 1, 1], -3, [76, 124, 199]),
]


def build_tby(cubic: list[int], a: int, B: list[int]) -> dict | None:
    """As mb8_harvest.build but with octic param t = B(y) = b0+b1*y+b2*y^2 (B in base field)."""
    cs = ",".join(str(c) for c in cubic)
    b0, b1, b2 = B
    script = (
        f"a={a};\n"
        f"c=Pol(Vecrev([{cs}]),'y);\n"
        f"B={b0}+({b1})*y+({b2})*y^2;\n"
        f"fp=subst({M.OCTIC_PGL},X,x);\n"        # octic in x, param t
        "fp=subst(fp,t,B);\n"                    # t = B(y)
        "F=polresultant(c,fp,y);\n"
        "if(poldegree(F)!=24||!polisirreducible(F),print(\"BAD\");quit);\n"
        "Fr=polredabs(F);\n"
        f"pd=poldisc(Fr);fa=factor(abs(pd),{M.SMOOTH_BOUND});"
        "cof=abs(pd);for(i=1,matsize(fa)[1],cof=cof/fa[i,1]^fa[i,2]);\n"
        "print(poldegree(Fr));print(polsturm(Fr));print(#Str(cof));print(Vecrev(Fr));\n")
    out = M._gp(script).strip().splitlines()
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


def sweep(limit: int, hi: int, density: bool) -> list[dict]:
    found: list[dict] = []
    seen_lines: set = set()
    for cub, a, B in CONFIGS:
        if len(found) >= limit:
            break
        b = build_tby(cub, a, B)
        if b is None:
            print(f"    cub={cub} a={a} B={B} BUILD-FAIL")
            continue
        if b["r"] != R:
            print(f"    cub={cub} a={a} B={B} r={b['r']}!={R} SKIP")
            continue
        if not b["smooth"]:
            print(f"    cub={cub} a={a} B={B} NOT-SMOOTH (cof_ndig={b['cof_ndig']}) SKIP")
            continue
        line = M.poly_line(b["coeffs"])
        if line in seen_lines:
            continue
        if density:
            ok, tag = M.density_ok(b["coeffs"], TARGET, hi=hi)
            if not ok:
                print(f"    cub={cub} a={a} B={B} DENSITY-REJECT {tag}")
                continue
        else:
            tag = "density-skipped"
        disc = M.gp.scoreable_disc(b["coeffs"], budget=55)
        seen_lines.add(line)
        found.append({"coeffs": b["coeffs"], "r": R, "line": line, "disc": disc,
                      "cubic": cub, "a": a, "B": B, "dens": tag})
        print(f"    cub={cub} a={a} B={B} disc~{disc} [{tag}] KEEP")
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5, help="max candidates to keep")
    ap.add_argument("--hi", type=int, default=6000, help="density prime bound")
    ap.add_argument("--no-density", action="store_true")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    print(f"== build (24T{TARGET}, r={R}) via t=B(y) ==")
    cands = sweep(args.limit, args.hi, not args.no_density)
    print(f"  {len(cands)} candidate(s)")

    if args.enqueue and cands:
        from igp import db
        from igp import searchstore as store
        store.init()
        realized = db.load_realized()
        held_groups = {str(x["t"]) for x in realized}
        held_pairs = {(str(x["t"]), str(x["r"])) for x in realized
                      if str(x.get("scoreable")).lower() == "true"}
        ts, rs = str(TARGET), str(R)
        tier = ("alt" if (ts, rs) in held_pairs
                else ("pair" if ts in held_groups else "new"))
        added = 0
        for c in cands:
            b0, b1, b2 = c["B"]
            src = f"a{c['a']}B{b0}_{b1}_{b2}"
            tag = f"lit:mb8{tier}:{ts}.{rs}:{src}"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": c["coeffs"]}, target=tag):
                added += 1
        for t, pri in {"new": 130.0, "pair": 115.0, "alt": 100.0}.items():
            store.set_priority_prefix(f"lit:mb8{t}", pri)
        print(f"enqueued {added} @ tier={tier}")


if __name__ == "__main__":
    main()
