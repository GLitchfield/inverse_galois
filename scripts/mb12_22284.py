"""24T22284 = (PSL(2,11)^2):C4 reconstruction producer (all four open pairs r in {0,4,12,24}).

Construction (recovered + generalized, test 0048): Mueller/Malle PGL(2,11) degree-12 Q(T)-family
``gtil(T)`` specialized at a real quadratic irrational ``theta = u + v*sqrt(d)`` over the base
field Q(sqrt d). The degree-24 field is ``rnfequation(y^2-2u y+(u^2-v^2 d), gtil(y) mod q)`` --
a degree-12 relative extension of Q(sqrt d) (that quadratic is the ONLY proper subfield, so the
absolute subfield-degree profile is [1,2,24], matching what nfsubfields reports).

Two independent dials:
  * SIGNATURE r: r = prof(u+v*sqrt d) + prof(u-v*sqrt d), where prof(t) = # real roots of the
    degree-12 specialization gtil(t). Empirically prof(t)=2 for t<~0, =12 for t in ~[1,14],
    =0 for t>~15. So both conjugates in [1,14] -> r=24; one in [1,14]+one>15 -> r=12; both<0 -> r=4;
    both>15 -> r=0.
  * GROUP (:C2/:V4/:C4/:D8 = 21362/22283/22284/23095): the C4 top (22284) requires the norm
    N(theta)=u^2-v^2 d to lie in the SAME square class as d, i.e. core(u^2-v^2 d) == core(d).
    (V4=22283 has N a perfect square; the entanglement of the diagonal quadratic with Q(sqrt d)
    is what makes it cyclic-C4 vs V4.) Verified by the degree-24 Frobenius fingerprint:
    22284 is the UNIQUE cluster member with cycle types [24],[2,2,20],[8,8,8] PRESENT and
    [2,2,10,10],[2,22] ABSENT (rules out the Gassmann neighbour 21362 and the siblings 22283/23095).

Each (u,v,d) triple is a fully-specified, reproducible build. The daemon submits to SAIR for the
authoritative Magma 24Tt label (the fingerprint is necessary, not sufficient -- the label is the gate).

Usage:
  python3 scripts/mb12_22284.py                # build + verify all candidates, print table
  python3 scripts/mb12_22284.py --enqueue      # also push verified winners to the search queue
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from igp import db  # noqa: E402
from igp import searchstore as store  # noqa: E402

TARGET_T = 22284
OPEN_R = [0, 4, 12, 24]

# (u, v, d, role): role 'primary' (best scoreable model) or 'backup' (redundant model).
# All d=2 (theta in Q(sqrt 2)); core(u^2-2 v^2) == 2 keeps the C4 top = 22284.
CANDIDATES: dict[int, list[tuple]] = {
    0:  [(26, 7, 2, "primary"), (34, 7, 2, "backup")],
    4:  [(-2, 1, 2, "primary"), (-10, 1, 2, "backup")],
    12: [(10, 5, 2, "primary"), (26, 17, 2, "backup")],   # (10,5,2) == recovered CP_22284r12
    24: [(10, 1, 2, "primary"), (2, 1, 2, "backup")],      # (2,1,2) == recovered SP22284 (slow disc)
}

# Frobenius fingerprint over N_PRIMES good primes; the decisive 22284 signature.
N_PRIMES = 800
DISC_BUDGET = 55  # seconds; nfdisc must complete within the grader's 60s bound to score

GP_FAMILY = r"""
default(parisizemax, 10*10^9);
A = x^3 + x^2 + 1/4*x + 1/22;
B = x^2 + 5/7*x - 1/44;
C = x^4 - 137/110*x^2 - 3/5*x - 623/9680;
D6 = x^6 + 36/143*x^5 - 323/143*x^4 - 6381/3146*x^3 - 9671/25168*x^2 + 5715/138424*x - 7035/553696;
Fq = x^5 + 2*x^4 + 321/550*x^3 - 427/550*x^2 - 2771/9680*x + 401/5324;
Gq = x^2 + 632/693*x - 6914/22869;
Econst = 3^3*5^2*7*11/4;
gtil(TT) = (A^4*(TT+1249) - 364*B*C*D6)*TT - Econst*Fq^2*Gq;
fp22284(P, np) = {
  my(cnt=0, p=1, T=Map(), dd, k);
  while(cnt<np, p=nextprime(p+1); if(Mod(pollead(P)*poldisc(P),p)==0, next);
    my(fa=factormod(P,p)); if(vecmax(fa[,2])>1, next);
    dd=vecsort(vector(#fa~, i, poldegree(fa[i,1]))); k=Str(dd);
    mapput(T,k, if(mapisdefined(T,k),mapget(T,k),0)+1); cnt++);
  my(h24=mapisdefined(T,"[24]"), h2220=mapisdefined(T,"[2, 2, 20]"), h888=mapisdefined(T,"[8, 8, 8]"),
     h1010=mapisdefined(T,"[2, 2, 10, 10]"), h222=mapisdefined(T,"[2, 22]"));
  (h24 && h2220 && h888 && !h1010 && !h222);
}
buildone(u, v, d) = {
  my(q = y^2 - 2*u*y + (u^2 - v^2*d), N = u^2 - v^2*d);
  if(core(abs(N)) != core(abs(d)), print("SKIP core mismatch"); return(0));
  my(relm = lift(Mod(gtil(y)/pollead(gtil(y)), q)));
  my(E = polredbest(rnfequation(q, relm)));
  if(poldegree(E) != 24, print("RES deg=", poldegree(E)); return(0));
  my(r = polsturm(E), ok = polisirreducible(E), fp = fp22284(E, %d));
  my(dz = alarm(%d, nfdisc(E)), sc, dig, mp);
  if(type(dz) == "t_INT", sc = 1; dig = #Str(abs(dz)); mp = vecmax(factor(abs(dz))[,1]),
     sc = 0; dig = 0; mp = 0);
  print("RES ", u, " ", v, " ", d, " ", ok, " ", r, " ", fp, " ", sc, " ", dig, " ", mp);
  print("VEC ", Vec(E));
  1;
}
"""


def _gp_run(body: str, timeout: float) -> str:
    proc = subprocess.run(["gp", "-q"], input=body, capture_output=True, text=True, timeout=timeout)
    return proc.stdout


def build_and_verify() -> list[dict]:
    """Build every candidate over the gtil family; return verified model dicts."""
    calls = "".join(f"buildone({u}, {v}, {d});\n"
                    for r in OPEN_R for (u, v, d, _role) in CANDIDATES[r])
    body = (GP_FAMILY % (N_PRIMES, DISC_BUDGET)) + calls + "quit\n"
    out = _gp_run(body, timeout=len(CANDIDATES) * 8 * 90)
    # roles keyed by (u,v,d)
    roles = {(u, v, d): (r, role)
             for r in OPEN_R for (u, v, d, role) in CANDIDATES[r]}
    models, pending = [], None
    for line in out.splitlines():
        if line.startswith("RES "):
            f = line.split()
            u, v, d = int(f[1]), int(f[2]), int(f[3])
            pending = {
                "u": u, "v": v, "d": d,
                "irred": int(f[4]) == 1, "polsturm": int(f[5]),
                "fp_ok": int(f[6]) == 1, "scoreable": int(f[7]) == 1,
                "disc_digits": int(f[8]), "maxprime": int(f[9]),
            }
            tr = roles.get((u, v, d))
            pending["r_target"], pending["role"] = (tr if tr else (None, "?"))
        elif line.startswith("VEC ") and pending is not None:
            desc = [int(x) for x in line[4:].strip().strip("[]").split(",")]
            pending["coeffs"] = desc[::-1]  # descending (Pol) -> ascending (constant first, monic last)
            models.append(pending)
            pending = None
    return models


def gate(m: dict) -> bool:
    """Mandatory local gates: deg-24 monic irreducible, r matches, fingerprint=22284, disc scores."""
    co = m.get("coeffs")
    return bool(
        co and len(co) == 25 and co[-1] == 1
        and m["irred"] and m["polsturm"] == m["r_target"]
        and m["fp_ok"] and m["scoreable"]
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    models = build_and_verify()
    realized = db.load_realized()
    held_pairs = {(int(r["t"]), int(r["r"])) for r in realized
                  if str(r.get("scoreable")).lower() == "true"}
    held_groups = {int(r["t"]) for r in realized if str(r.get("scoreable")).lower() == "true"}

    print(f"\n24T{TARGET_T} = (PSL(2,11)^2):C4  --  open pairs r in {OPEN_R}")
    print(f"held: group_in_realized={TARGET_T in held_groups}  "
          f"held_pairs={sorted(r for (t, r) in held_pairs if t == TARGET_T)}\n")
    print(f"{'r':>3} {'role':>7} {'u':>4} {'v':>3} {'d':>2} {'irr':>3} {'polsturm':>8} "
          f"{'fp22284':>7} {'score':>5} {'digits':>6} {'maxprime':>14} {'GATE':>5}")
    for r in OPEN_R:
        for m in [x for x in models if x["r_target"] == r]:
            print(f"{r:>3} {m['role']:>7} {m['u']:>4} {m['v']:>3} {m['d']:>2} "
                  f"{int(m['irred']):>3} {m['polsturm']:>8} {int(m['fp_ok']):>7} "
                  f"{int(m['scoreable']):>5} {m['disc_digits']:>6} {m['maxprime']:>14} "
                  f"{'OK' if gate(m) else 'FAIL':>5}")

    winners = [m for m in models if gate(m)]
    print(f"\n{len(winners)} models pass all local gates "
          f"(pairs covered: {sorted({m['r_target'] for m in winners})})")

    if not args.enqueue:
        print("\n(dry run -- pass --enqueue to push to the search queue)")
        return

    store.init()
    tiers = {"new": 130.0, "pair": 115.0, "alt": 100.0}
    added = {"new": 0, "pair": 0, "alt": 0}
    # one primary per pair unlocks the group at high priority; backups ride the alt lane.
    for r in OPEN_R:
        for m in [x for x in winners if x["r_target"] == r]:
            t = TARGET_T
            if (t, r) in held_pairs:
                tier = "alt"
            elif m["role"] == "primary":
                tier = "new" if t not in held_groups else "pair"
            else:
                tier = "alt"
            src = f"u{m['u']}v{m['v']}d{m['d']}"
            tag = f"lit:mb12{tier}:{t}.{r}:{src}"
            if not store.has_target(tag) and store.enqueue("ready", {"coeffs": m["coeffs"]}, target=tag):
                added[tier] += 1
    for tier, pri in tiers.items():
        store.set_priority_prefix(f"lit:mb12{tier}", pri)
    print(f"enqueued: new@130={added['new']}  pair@115={added['pair']}  alt@100={added['alt']}")


if __name__ == "__main__":
    main()
