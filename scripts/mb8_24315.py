"""minblk=8 octic-over-cubic producer (24315 track / PSL(2,7)^3 cluster).

Builds degree-24 candidates as Res_y(c(y), f(a,y,X)) where f is Malle pargal.pdf
Thm 5.1's genus-0 PGL(2,7)=8T43 octic family (parameter t=y lives in a cubic k) and
c(y) is a small-disc cubic. polredabs, then gate:
  (1) deg 24 + irreducible
  (2) polsturm real-root count == target r
  (3) Frobenius-density fingerprint consistent with an OPEN minblk=8 label (density,
      not cycle-type-set: distinguishes 24315 twist vs 24672 full-wreath vs Gassmann
      neighbours / the [1,3,8,24] diagonal collapse)
  (4) scoreable_disc does not blank-risk
then enqueue for the daemon to submit (authoritative Magma label from SAIR).

EMPIRICAL (2026-07-07, test 0044): the GENERIC S3-cubic Res lands the FULL WREATH
24T24672 = PGL(2,7) wr S3 = (PSL(2,7)^3):(C2xS4), NOT the twist 24T24315. Descent to
24315 requires the three blocks' PGL/PSL quadratic characters to be tied to the cubic's
quadratic resolvent, i.e. g(y)*disc(c) in (k*)^2 where g = squarefree part of disc_X(f)
= 108 t^3 - 14057 t^2 + 330400 t + 740608 (for a=-2). That is a positive-genus Diophantine
condition (the necessary norm condition Res(c,g)*disc(c) must be a perfect integer square) --
measured 0 hits over ~8500 cubics + ~17000 1-param-curve points -> NOT blind-sweepable; needs
an explicit 2-descent / disc-correlation parametrization (open, see test 0044).

The density labeller enqueues whatever OPEN mb8 target a build actually lands (so generic
builds harvest 24672's open r-menu), and flags a build as a 24315 candidate only when its
fingerprint matches 24315 (no 16-/24-cycles) with a clear margin.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(ROOT, "data", "targets", "mb8")
sys.path.insert(0, os.path.join(ROOT, "src"))

# Malle Thm 5.1 PGL(2,7)=8T43 octic, parameter t=y; a in Q (a=-2 totally-real branch).
OCTIC = ("X*(X^7+X^6+14*a*X^5+7*a*X^4+49*a^2*X^3+14*a^2*X^2+49*a^3*X+7*a^3)"
         "+y*(7*X^2+X+1)")
# squarefree part of disc_X(f) at a=-2 (the octic's PGL/PSL quadratic character).
G_CHAR = "108*y^3-14057*y^2+330400*y+740608"


def _gp(body: str, timeout: float = 280.0) -> str:
    script = "default(parisizemax,6*10^9);\n" + body + "\n"
    p = subprocess.run(["gp", "-q"], input=script, capture_output=True, text=True,
                       timeout=timeout)
    if "*** " in p.stdout or p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout)[:400])
    return p.stdout.strip()


def build(cubic: str, a: int = -2, timeout: float = 280.0) -> list[int] | None:
    """Res_y(c(y), f(a,y,X)) -> polredabs -> ascending 25-int coeff list (leading last)."""
    octic = OCTIC.replace("a", f"({a})")
    body = (f"c={cubic};a={a};"
            f"f={octic};"
            f"R=polresultant(c,f,y);R=R/content(R);"
            f"if(poldegree(R)!=24||!polisirreducible(R),print(\"REJECT\"),"
            f"Rr=polredabs(R);print(Vecrev(Rr)))")
    out = _gp(body, timeout).splitlines()[-1].strip()
    if out == "REJECT" or not out.startswith("["):
        return None
    co = [int(x) for x in out.strip("[]").split(",")]
    if len(co) != 25 or co[-1] != 1:
        return None
    return co


# --- density fingerprint (reuses mb8_match logic; globs data/targets/mb8/dist_*.txt) ---
def load_gdist() -> dict:
    gd = {}
    for fn in glob.glob(f"{DIST_DIR}/dist_*.txt"):
        t = int(re.search(r"dist_(\d+)\.txt", fn).group(1))
        order, dist = None, {}
        for ln in open(fn):
            ln = ln.strip()
            if ln.startswith("order"):
                order = int(ln.split()[1]); continue
            if not ln or " " not in ln:
                continue
            key, cnt = ln.rsplit(" ", 1)
            if not re.fullmatch(r"[0-9,]+", key):
                continue
            ct = tuple(int(x) for x in key.split(","))
            dist[ct] = dist.get(ct, 0) + int(cnt)
        gd[t] = {"order": order, "dist": dist}
    return gd


GD = load_gdist()


def poly_dist(coeffs, hi=5000):
    cs = ",".join(map(str, coeffs[::-1]))
    body = (f"f=Pol([{cs}]);d=poldisc(f);lc=pollead(f);"
            f"forprime(p=3,{hi},if(d%p!=0&&lc%p!=0,fa=factormod(f,p);"
            "if(vecmax(fa[,2])==1,print(vecsort(vector(matsize(fa)[1],i,poldegree(fa[i,1])))))));")
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
        tally[ct] = tally.get(ct, 0) + 1; n += 1
    return tally, n


def l1(tally, n, t):
    g = GD[t]
    exp = {k: v / g["order"] for k, v in g["dist"].items()}
    obs = {ct: c / n for ct, c in tally.items()}
    return sum(abs(obs.get(k, 0) - exp.get(k, 0)) for k in set(exp) | set(obs))


def label(coeffs, hi=5000):
    tally, n = poly_dist(coeffs, hi)
    scored = []
    for t in sorted(GD):
        imp = sum(tally[ct] for ct in tally if ct not in set(GD[t]["dist"]))
        scored.append((l1(tally, n, t), t, imp))
    scored.sort()
    return scored, n


def correlation(cubic: str, a: int = -2) -> str:
    """Predict the wreath twist from the octic character's square class in k=Q[y]/cubic.
    g(y)*disc square -> 24315 (PGL-twist); g(y) square -> 24314 (plain); disc square (C3)
    -> 24055/24592; else -> 24672 (full wreath). Uses matsize rows (NOT #nffactor=cols)."""
    body = (f"c={cubic};d=poldisc(c);K=nfinit(c);gy=Mod({G_CHAR},c);"
            f"r1=matsize(nffactor(K,x^2-gy))[1];r2=matsize(nffactor(K,x^2-gy*d))[1];"
            f"print(issquare(d),\" \",(r1==2),\" \",(r2==2))")
    ds, gsq, gdsq = _gp(body, 120).split()
    ds, gsq, gdsq = ds == "1", gsq == "1", gdsq == "1"
    if ds:
        return "24055/24592 (C3 base)"
    if gsq:
        return "24314 (plain PSL wreath)"
    if gdsq:
        return "24315 (PGL-TWIST)"
    return "24672 (full wreath)"


def real_roots(coeffs) -> int:
    from igp import gp
    return gp.real_roots(coeffs)


def scoreable(coeffs):
    from igp import gp
    return gp.scoreable_disc(coeffs, budget=50)


OPEN_MB8 = {14051, 14052, 16060, 16061, 19280, 20408, 24315, 24316, 24488,
            24489, 24592, 24593, 24594, 24672, 24916, 24922}


def process(cubic: str, a: int, enqueue: bool, l1_max=0.4, margin_min=0.15):
    import json
    co = build(cubic, a)
    if co is None:
        print(f"[{cubic} a={a}] build REJECT (not irreducible deg-24)")
        return
    r = real_roots(co)
    twist = correlation(cubic, a)
    scored, n = label(co)
    best_l1, best_t, best_imp = scored[0]
    margin = scored[1][0] - best_l1
    prog = json.load(open(os.path.join(ROOT, "data", "processed", "progress.json")))
    tc = (prog.get(f"{best_t},{r}") or {}).get("teamCount", 9)
    sd = scoreable(co)
    print(f"[{cubic} a={a}] r={r} predict-twist={twist}")
    print(f"    density best=24T{best_t} L1={best_l1:.3f} margin={margin:.3f} "
          f"impossible={best_imp} (n={n})")
    print(f"    (24T{best_t},{r}) teamCount={tc}  scoreable_disc={'OK' if sd else 'BLANK'}")
    consistent = best_imp == 0 and best_l1 <= l1_max and margin >= margin_min
    is_open = tc == 0 and best_t in OPEN_MB8
    if not (consistent and is_open and sd):
        print(f"    -> NOT enqueued (consistent={consistent} open={is_open} scoreable={bool(sd)})")
        return
    if not enqueue:
        print(f"    -> would enqueue 24T{best_t} r={r} (use --enqueue)")
        return
    from igp import db, searchstore as store
    store.init()
    realized = db.load_realized()
    held = {rr["t"] for rr in realized if str(rr.get("scoreable")).lower() == "true"}
    tier = "pair" if str(best_t) in held else "new"
    src = f"c{re.sub(r'[^0-9a-z]', '', cubic.replace('*', '').replace('^', ''))}_a{a}"
    tag = f"lit:mb8new:{best_t}.{r}:{src}"
    if store.has_target(tag):
        print(f"    -> already enqueued ({tag})")
        return
    if store.enqueue("ready", {"coeffs": co}, target=tag):
        store.set_priority_prefix("lit:mb8new", 130.0)
        print(f"    -> ENQUEUED {tag} @130 (tier {tier})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cubic", default="y^3-y-1")
    ap.add_argument("--a", type=int, default=-2)
    ap.add_argument("--enqueue", action="store_true")
    ap.add_argument("--l1-max", type=float, default=0.4)
    ap.add_argument("--margin-min", type=float, default=0.15)
    args = ap.parse_args()
    process(args.cubic, args.a, args.enqueue, args.l1_max, args.margin_min)


if __name__ == "__main__":
    main()
