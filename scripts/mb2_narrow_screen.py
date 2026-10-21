"""The NARROW-PARITY screen: one Kronecker symbol decides whether the twist engine can EVER build
on a (base, d) pair (research dive #58).

THE WALL. mb2_twist_sign_producer's BUILD_SIGN needs a TOTALLY POSITIVE generator of the divisor
`Id * Q_a * Q_b`. It gets one iff that divisor is principal in the NARROW sense. Ordinary
principality (h = 1) is NOT enough: with delta = 12 - rank_F2(bnfsignunit) > 0 the narrow class
group Cl+ = (Z/2)^delta is a real obstruction, and when every fundamental unit has norm +1 (the
generic case in even degree) the sign of N(alpha) is a unit-invariant of the ideal.

THE PREDICATE. Write sg(I) in F2^12 for the sign vector of a generator of a principal ideal I, and
V = F2^12 / im(S) for the narrow class group (dim delta). BUILD_SIGN's matsolvemod at (q, a, b)
succeeds iff `Id * Q_a * Q_b` is NARROWLY principal, i.e. iff

        sg(Id) + sg(Q_a) + sg(Q_b)  ==  0  in V.

That is a 66-pair lookup over 13 bnfisprincipal calls -- so the engine's whole q/(a,b) search can be
DECIDED without building a single radical or paying a single Frobenius fingerprint. If no pair
satisfies it at any q, the (base, d) is PROVABLY unbuildable: no q, no (a,b), no unit twist.

WHY A BASE GOES DEAD. sg is a homomorphism to V, so the 12 primes above a completely-split q each
carry a class. When the relevant narrow character is RATIONAL (it factors through the rational prime
-- a genus character), all 12 get the SAME class, hence sg(Q_a) + sg(Q_b) = 0 for EVERY pair and the
split prime is a DEAD dial (dive #52's "DEAD base"; dive #53 measured ~10% of bases rational). Then
buildability hinges entirely on sg(Id), which d fixes -- and d = core(disc K0) is itself forced by
the sign-character aim (dive #50). So on such a base the target is decided before any search.

VERDICTS emitted per (target, base, d):
  OK-NARROW     delta = 0 (h+ = h): the sign gate is vacuous, always buildable
  OK-FEASIBLE   some (q, a, b) satisfies the predicate -- the engine can build here
  DEAD-NARROW   no pair at any sampled q satisfies it -- change the base
  UNKNOWN-*     the screen abstains (no split q sampled; Id or a Q not principal)

`nmixed` counts the sampled q whose 12 primes do NOT all share a class: nmixed = 0 alongside
DEAD-NARROW is the rational-character signature, and is what makes the DEAD verdict structural
rather than merely "unlucky at the q we tried".

Usage:
    .venv/bin/python scripts/mb2_narrow_screen.py                 # whole shortlist + chi_d.csv
    .venv/bin/python scripts/mb2_narrow_screen.py --targets 18009,23297,24494
"""
import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import mb2_twist as tw  # noqa: E402
import mb2_twist_sign_producer as prod  # noqa: E402

OUT = ROOT / "data" / "processed" / "mb2twist"

SCREEN = r"""
\\ The narrow class of a PRINCIPAL ideal I, as a vector in V = F2^12 / im(S): take any generator,
\\ read its sign vector. Returns 0 if I is not principal (the ordinary class already obstructs).
{
NCV(K, I) =
  my(e = bnfisprincipal(K, I), al, sg);
  if(#select(x -> x != 0, Vec(e[1])) > 0, return(0));
  al = nfbasistoalg(K, e[2]); sg = nfeltsign(K, al);
  [vectorv(12, i, if(sg[i] < 0, 1, 0))];
}
{
SCREEN(d, c) =
  my(f = Pol(Vecrev(c), 'y), K = bnfinit(f, 1), SU, S, dl, df, qs, vI, vq, pf, Id, i, j,
     nmixed, nq, hit, allsame, dead);
  SU = bnfsignunit(K);
  S = matconcat([matrix(12, 11, i, j, (1 - SU[i,j]) / 2), vectorv(12, i, 1)]);
  dl = 12 - matrank(Mod(S, 2));
  print("H|", K.clgp.no, "|", dl, "|", bnfnarrow(K).cyc);
  \\ delta = 0 <=> h+ = h: every principal ideal has a totally positive generator, gate is vacuous.
  if(dl == 0, print("V|OK-NARROW|0|0"); return());
  \\ Id = the odd-f primes above the primes of d, exactly as BUILD_SIGN assembles it.
  pf = factor(d)[,1];
  Id = idealhnf(K, 1);
  for(i = 1, #pf,
    my(od = select(P -> P.f % 2 == 1, idealprimedec(K, pf[i])));
    if(#od == 0, print("V|NOODD|0|0"); return());
    Id = idealmul(K, Id, od[1]));
  vI = NCV(K, Id);
  if(vI == 0, print("V|UNKNOWN-IDNONPRIN|0|0"); return());
  \\ BUILD_SIGN succeeds at (q, a, b) <=> Id * Q_a * Q_b is NARROWLY principal
  \\   <=> sg(Id) + sg(Q_a) + sg(Q_b) is in im(S)  (matsolvemod is exactly this test).
  \\ Evaluate it directly on the 13 ideals instead of building a radical to watch it fail.
  df = poldisc(f); nq = 0; dead = 1; nmixed = 0;
  forprime(q = 100, 10^6,
    if(nq >= NQ, break);
    if(df % q == 0, next);
    if(#polrootsmod(f, q) != 12, next);
    my(dec = idealprimedec(K, q), cls = vector(12), bad = 0, feas = 0);
    if(#dec != 12, next);
    for(i = 1, 12,
      my(v = NCV(K, dec[i]));
      if(v == 0, bad = 1; break);
      cls[i] = v[1]);
    if(bad, next);          \\ a prime above q is not principal: outside this screen's h=1 model
    nq++;
    for(i = 1, 11, for(j = i + 1, 12,
      if(matsolvemod(S, 2, (vI[1] + cls[i] + cls[j]) % 2) != 0, feas++)));
    \\ "same class in V", NOT "same sign vector": two primes can have different representatives and
    \\ still be narrowly equivalent. cls[i] ~ cls[1] iff their difference lies in im(S).
    allsame = 1;
    for(i = 2, 12, if(matsolvemod(S, 2, (cls[i] + cls[1]) % 2) == 0, allsame = 0));
    if(!allsame, nmixed++);
    if(feas > 0, dead = 0);
    print("Q|", q, "|feasible_pairs=", feas, "/66|allsame_class=", allsame);
  );
  if(nq == 0, print("V|UNKNOWN-NOQ|0|0"); return());
  print("V|", if(dead, "DEAD-NARROW", "OK-FEASIBLE"), "|", nq, "|", nmixed);
}
"""


def entries():
    rows = [(t, top, d, cs, h) for t, top, d, cs, h in prod.SHORTLIST]
    path = OUT / "chi_d.csv"
    if path.exists():
        with open(path) as fh:
            for row in csv.DictReader(fh):
                try:
                    t, d, h = int(row["t"]), int(row["d"] or 0), int(row["h"] or 0)
                except ValueError:
                    continue
                if d:
                    rows.append((t, int(row["top"]), d, json.loads(row["coeffs"]), h))
    return rows


def screen(d: int, coeffs: list, nq: int, timeout: float) -> dict:
    code = (prod.PRELUDE + SCREEN + f"NQ = {nq};\nSCREEN({d}, {coeffs});\nquit\n")
    out = tw.gp_run(code, timeout=timeout)
    res = {"h": "", "delta": "", "cyc": "", "verdict": "ERROR", "nq": "", "nmixed": "", "q": []}
    for ln in out.splitlines():
        f = ln.strip().split("|")
        if f[0] == "H":
            res["h"], res["delta"], res["cyc"] = f[1], f[2], f[3]
        elif f[0] == "Q":
            res["q"].append((f[1], f[2]))
        elif f[0] == "V":
            res["verdict"], res["nq"], res["nmixed"] = f[1], f[2], f[3]
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", type=str, default=None)
    ap.add_argument("--nq", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=2400.0)
    args = ap.parse_args()

    keep = {int(x) for x in args.targets.split(",")} if args.targets else None
    rows, seen = [], set()
    for t, top, d, cs, _h in entries():
        if keep is not None and t not in keep:
            continue
        if (t, d) in seen:
            continue
        seen.add((t, d))
        r = screen(d, cs, args.nq, args.timeout)
        print(f"24T{t:>5} / 12T{top:<4} d={d:<12} h={r['h']} delta={r['delta']} "
              f"Cl+={r['cyc']:<10} nq={r['nq']:<3} nmixed={r['nmixed']:<3} {r['verdict']}")
        rows.append({"t": t, "top": top, "d": d, "h": r["h"], "delta": r["delta"],
                     "cyc": r["cyc"], "nq": r["nq"], "nmixed": r["nmixed"],
                     "verdict": r["verdict"]})

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "narrow_screen.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    tally: dict = {}
    for r in rows:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    print("\nVERDICTS:", dict(sorted(tally.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
