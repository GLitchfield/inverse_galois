"""PGL-wreath Tier-A builder (test 0056): the four missing r-values of the two full
PGL(2,7) wreaths, via the EXISTING Malle-octic-over-cubic Res pipeline (scripts/mb8_harvest).

    F(X) = Res_y( c(y), f_Malle(a, y, X) )   -- three conjugate 8T43 octic blocks over c.

The deg-24 real-root count r = sum over the 3 REAL cubic roots of the per-block octic real count,
which is a step function of the root value t (block window map, empirically):

        block real count W_a(t) = 8  for t in a bounded window   (a=-1:[0,3], a=-2:[-2,33], a=-3:[-6,124])
                                  0  for t >= a one-sided threshold (a=-1:16, a=-2:99, a=-3:299)
                                  2  otherwise

So a 0-block needs ONE large positive root; the 0-region is one-sided (t -> -inf gives 2). Hence:

  (24672,10) = (8,2,0)  S3 cubic: one root in-window, one mid/neg, one large.        BUILDABLE
  (24672,16) = (8,8,0)  S3 cubic: two roots in-window, one large.                     BUILDABLE
  (24592,16) = (8,8,0)  C3 cubic: two roots in-window, one large (Shanks large k).    BUILDABLE
  (24592,8)  = (8,0,0)  C3 cubic: needs TWO large roots -> two roots near +inf.        BLOCKED.
      A real cyclic cubic's Galois generator is a real Mobius map of order 3 (no real fixed
      points) = a projective 120-degree rotation, so at most ONE real root can sit near +inf.
      Two 0-blocks are therefore geometrically unreachable over any C3 base. (Numerically
      confirmed: 0 hits across Shanks k in [-5,320] x a in {-1,-2,-3}.)

Targets all VERIFIED teamCount==0 OPEN, non-baseline (score on any valid disc). Local gate reuses
mb8_harvest: deg-24 irreducible, polsturm r == target, poldisc smooth (<10^6, disc-scoreable), and
a Frobenius-DENSITY label check vs the 24672/24592 twins + the 24315/24314 Gassmann neighbours.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import mb8_harvest as M  # noqa: E402  (build / density_ok / poly_line primitives)

# (target, r) -> the octic block pattern we steer to; all a<0 (a>0 gives no 8-block).
TIER_A = [(24672, 10), (24672, 16), (24592, 16)]
BLOCKED = {(24592, 8): "two 0-blocks need two roots near +inf; impossible over a real C3 cubic"}


def _isqrt_square(n: int) -> bool:
    import math
    if n <= 0:
        return False
    s = math.isqrt(n)
    return s * s == n


def _cubic_disc(cub: list[int]) -> int:
    # cub ascending [c0,c1,c2,1]; standard cubic discriminant.
    b0, b1, b2, _ = cub
    return (18 * b2 * b1 * b0 - 4 * b2**3 * b0 + b2**2 * b1**2
            - 4 * b1**3 - 27 * b0**2)


def s3_general_cubics() -> list[list[int]]:
    """General (non-depressed) integer S3 cubics y^3+b2 y^2+b1 y+b0 with one large positive root
    and two small roots, to steer the (8,2,0)/(8,8,0) block patterns. Built near integer root
    triples {small, small_or_neg, big} then perturbed a couple units to force irreducible + S3
    (disc>0 non-square). a=-1 windows: 8-block for a root in [0,3], 0-block for a root >=16."""
    out: list[list[int]] = []
    seen: set = set()

    def add(roots: tuple[int, int, int]) -> None:
        p, q, r = roots
        b2, b1, b0 = -(p + q + r), p * q + p * r + q * r, -p * q * r
        for db0 in range(-2, 3):
            for db1 in range(-2, 3):
                cub = [b0 + db0, b1 + db1, b2, 1]
                key = tuple(cub)
                if key in seen:
                    continue
                d = _cubic_disc(cub)
                if d <= 0 or _isqrt_square(d):   # need 3 real roots (disc>0) and S3 (non-square)
                    continue
                seen.add(key)
                out.append(cub)

    for big in range(16, 34):
        for w1 in (0, 1, 2, 3):                  # (8,8,0): two window roots + big
            for w2 in (0, 1, 2, 3):
                add((w1, w2, big))
        for w in (0, 1, 2, 3):                   # (8,2,0): one window, one neg (->2), one big
            for neg in (-1, -2, -3, -5, -8):
                add((w, neg, big))
    return out


def c3_shanks_cubics() -> list[list[int]]:
    """Shanks simplest cubics y^3 - k y^2 - (k+3) y - 1 (cyclic C3, totally real) at large k:
    roots ~ {-1, ~0, k+1}. The two small roots land the a=-2 8-window [-2,33]; the large root
    >= 99 is the 0-block -> pattern (8,8,0) = r=16. Ascending [-1,-(k+3),-k,1]."""
    return [[-1, -(k + 3), -k, 1] for k in range(96, 140)]


def candidate_configs(target: int, r: int):
    """Yield (cubic, a) configs to try for this (target, r)."""
    if target == 24672:
        for cub in s3_general_cubics():
            yield cub, -1
    elif target == 24592:
        for cub in c3_shanks_cubics():
            yield cub, -2


def sweep(target: int, r: int, limit: int, hi: int, density: bool) -> list[dict]:
    found: list[dict] = []
    seen_lines: set = set()
    for cub, a in candidate_configs(target, r):
        if len(found) >= limit:
            break
        b = M.build(cub, a)
        if b is None or b["r"] != r:
            continue
        if not b["smooth"]:            # rough poldisc -> SAIR disc scoring never terminates
            continue
        line = M.poly_line(b["coeffs"])
        if line in seen_lines:
            continue
        if density:
            ok, tag = M.density_ok(b["coeffs"], target, hi=hi)
            if not ok:
                print(f"    24T{target} r={r} cub={cub} a={a} DENSITY-REJECT {tag}")
                continue
        else:
            tag = "density-skipped"
        disc = M.gp.scoreable_disc(b["coeffs"], budget=55)
        seen_lines.add(line)
        found.append({"coeffs": b["coeffs"], "r": r, "line": line, "disc": disc,
                      "cubic": cub, "a": a, "dens": tag})
        print(f"    24T{target} r={r} cub={cub} a={a} disc~{disc} [{tag}] KEEP")
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=3, help="candidates per pair")
    ap.add_argument("--hi", type=int, default=6000, help="density prime bound")
    ap.add_argument("--no-density", action="store_true")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    for (t, r), why in BLOCKED.items():
        print(f"BLOCKED (24T{t}, r={r}): {why}")

    results: dict = {}
    for t, r in TIER_A:
        print(f"== sweep 24T{t} r={r} ==")
        results[(t, r)] = sweep(t, r, args.limit, args.hi, not args.no_density)
        print(f"  24T{t} r={r}: {len(results[(t, r)])} candidate(s)")

    if args.enqueue:
        from igp import db
        from igp import searchstore as store
        store.init()
        realized = db.load_realized()
        held_groups = {str(x["t"]) for x in realized}   # present in realized.csv => group held
        held_pairs = {(str(x["t"]), str(x["r"])) for x in realized
                      if str(x.get("scoreable")).lower() == "true"}
        added = {"new": 0, "pair": 0, "alt": 0}
        for (t, r), cands in results.items():
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
