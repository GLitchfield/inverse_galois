"""minblk=8 24315 OUTER-TWIST producer via conic-parametrized Kida-Suzuki Res.

SOLVED 2026-07-08 (auto_log dive): the OUTER twist 24T24315 = PGL(2,7) wr S3's
sign-correlated subgroup { (g1,g2,g3;pi) : eps(gi)=sgn(pi) } is reachable by a PLAIN
rational Res once the block octic's PGL/PSL marker is tied to disc(c) via a genus-0
CONIC (test 0044's "0 hits" was a T=y artifact -- free the parameter and it is genus 0).

Recipe, for each small-disc S3 cubic c(y) (NON-square disc), d = poldisc(c):
  T(y) = -756 y^2 / (7 y^2 + d)                       # Kida-Suzuki conic point in k
  G(y,X) = (7 y^2 + d)(X^8 + X^7 + 7 X^6) + 756 y^2 (X + 1)   # F=X^8+X^7+7X^6-T(X+1) cleared
  R = Res_y(c, G) -> monic (L^(deg-1) subst x/L, strip content) -> polredabs
Gate (local, budget-safe -- SAIR Magma is the authoritative downstream label):
  (1) deg 24 + irreducible
  (2) polsturm real-root count == observed r (record whatever r the base signature yields)
  (3) Frobenius-DENSITY fingerprint best == 24T24315, impossible==0, clear margin
      (rejects 24314 inner sibling / 24672 full wreath / 24593 neighbour) -- reuses the
      density labeller in scripts/mb8_24315.py
  (4) scoreable_disc does not blank-risk (>10^6 prime factor -> grader nfdisc timeout)
then enqueue lit:mb8t315:24315.<r>:conic<cubic-id> for the daemon (tier new @130).

r-menu: base signature drives r. A totally-real S3 cubic (disc>0) tends to higher r;
a complex S3 cubic (disc<0) lower r. Sweep the small-disc S3 cubics of both signatures
+ the two conic branches (general -756y^2/(7y^2+d) and the -108y^2/(y^2+d') alternate).

VERIFIED 2026-07-08: c=y^3-y-1 (d=-23) -> 24T24315 L1~0.10 impossible=0 margin>0.6, r=2.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from mb8_24315 import GD, l1, label, poly_dist  # reuse the density machinery  # noqa: E402

TARGET = 24315


def _gp(body: str, timeout: float = 280.0) -> str:
    script = "default(parisizemax,6*10^9);\n" + body + "\n"
    p = subprocess.run(["gp", "-q"], input=script, capture_output=True, text=True,
                       timeout=timeout)
    if "*** " in p.stdout or "syntax error" in p.stderr or p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout)[:400])
    return p.stdout.strip()


def build(cubic: str, timeout: float = 280.0) -> list[int] | None:
    """Res_y(c, G) -> monic -> polredabs -> ascending 25-int coeff list (leading last)."""
    body = (
        f"c={cubic};d=poldisc(c);"
        "G=(7*y^2+d)*(X^8+X^7+7*X^6)+756*y^2*(X+1);"
        "R=polresultant(c,G,y);R=R/content(R);"
        "reject=(poldegree(R)!=24||!polisirreducible(R));"
        "if(reject,print(\"REJECT\"),"
        "L=pollead(R);Rm=L^(poldegree(R)-1)*subst(R,X,X/L);Rm=Rm/content(Rm);"
        "Ra=polredabs(Rm);print(Vecrev(Ra)))"
    )
    out = _gp(body, timeout).splitlines()[-1].strip()
    if out == "REJECT" or not out.startswith("["):
        return None
    co = [int(x) for x in out.strip("[]").split(",")]
    if len(co) != 25 or co[-1] != 1:
        return None
    return co


def real_roots(coeffs) -> int:
    from igp import gp
    return gp.real_roots(coeffs)


def scoreable(coeffs):
    from igp import gp
    return gp.scoreable_disc(coeffs, budget=50)


def label_24315(coeffs, hi=5000):
    """Return (best_t, best_l1, margin, impossible, n, l1_of_24315)."""
    scored, n = label(coeffs, hi)
    best_l1, best_t, best_imp = scored[0]
    margin = scored[1][0] - best_l1
    l1_315 = next(x for x, t, _ in scored if t == TARGET)
    return best_t, best_l1, margin, best_imp, n, l1_315


def process(cubic: str, cid: str, enqueue: bool, l1_max=0.4, margin_min=0.15,
            dry=False):
    import json
    try:
        co = build(cubic)
    except Exception as e:  # noqa: BLE001 -- external gp boundary
        print(f"[{cubic}] build ERROR: {e}")
        return None
    if co is None:
        print(f"[{cubic}] build REJECT (not irreducible deg-24)")
        return None
    r = real_roots(co)
    best_t, best_l1, margin, imp, n, l1_315 = label_24315(co)
    prog = json.load(open(os.path.join(ROOT, "data", "processed", "progress.json")))
    tc = (prog.get(f"{TARGET},{r}") or {}).get("teamCount", 9)
    sd = scoreable(co)
    print(f"[{cubic}] r={r}  density best=24T{best_t} L1={best_l1:.3f} "
          f"margin={margin:.3f} impossible={imp} (n={n})  L1(24315)={l1_315:.3f}")
    print(f"    (24315,{r}) teamCount={tc}  scoreable_disc={'OK' if sd else 'BLANK'}")
    on_target = best_t == TARGET
    consistent = on_target and imp == 0 and best_l1 <= l1_max and margin >= margin_min
    is_open = tc == 0
    ok = consistent and is_open and bool(sd)
    if not ok:
        print(f"    -> NOT enqueued (on_target={on_target} consistent={consistent} "
              f"open={is_open} scoreable={bool(sd)})")
        return {"coeffs": co, "r": r, "enqueued": False, "best_t": best_t}
    tag = f"lit:mb8t315:{TARGET}.{r}:conic{cid}"
    if dry or not enqueue:
        print(f"    -> would enqueue {tag} (use --enqueue)")
        return {"coeffs": co, "r": r, "enqueued": False, "best_t": best_t, "tag": tag}
    from igp import searchstore as store
    store.init()
    if store.has_target(tag):
        print(f"    -> already enqueued ({tag})")
        return {"coeffs": co, "r": r, "enqueued": False, "best_t": best_t, "tag": tag}
    if store.enqueue("ready", {"coeffs": co}, target=tag):
        store.set_priority_prefix("lit:mb8t315", 130.0)
        print(f"    -> ENQUEUED {tag} @130 (tier new)")
        return {"coeffs": co, "r": r, "enqueued": True, "best_t": best_t, "tag": tag}
    return {"coeffs": co, "r": r, "enqueued": False, "best_t": best_t, "tag": tag}


# small-disc S3 cubics (non-square disc), both signatures; cid used in the enqueue tag.
CUBICS = [
    ("y^3-y-1", "ynm1", -23),        # complex, disc -23 (smallest); r=2 verified
    ("y^3+y-1", "yp1", -31),         # complex, disc -31
    ("y^3-y^2-1", "y2m1", -23),      # complex
    ("y^3+y^2-1", "y2p1", -23),      # complex
    ("y^3-2", "2", -108),            # complex, pure cubic
    ("y^3-y^2+y-2", "cmix", None),   # complex
    ("y^3-4*y-1", "tr4m1", 229),     # totally real, disc 229
    ("y^3-4*y-2", "tr4m2", 236),     # totally real
    ("y^3-5*y-1", "tr5m1", 473),     # totally real
    ("y^3-6*y-2", "tr6m2", 756),     # totally real
    ("y^3-7*y-5", "tr7m5", 1229),    # totally real
    ("y^3-9*y-9", "tr9m9", 3321),    # totally real
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cubic", default=None, help="single cubic in y")
    ap.add_argument("--cid", default="custom")
    ap.add_argument("--sweep", action="store_true", help="run the CUBICS list")
    ap.add_argument("--enqueue", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--l1-max", type=float, default=0.4)
    ap.add_argument("--margin-min", type=float, default=0.15)
    args = ap.parse_args()

    if args.sweep:
        seen_r = {}
        for cubic, cid, _disc in CUBICS:
            if cid is None:
                continue
            res = process(cubic, cid, args.enqueue, args.l1_max, args.margin_min,
                          args.dry)
            if res and res.get("enqueued"):
                seen_r[res["r"]] = seen_r.get(res["r"], 0) + 1
        print(f"\nSWEEP DONE. enqueued by r: {seen_r}")
    else:
        if not args.cubic:
            ap.error("give --cubic or --sweep")
        process(args.cubic, args.cid, args.enqueue, args.l1_max, args.margin_min,
                args.dry)


if __name__ == "__main__":
    main()
