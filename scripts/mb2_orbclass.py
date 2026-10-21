"""MINBLK=2 THE FULLY-OPEN ORBITAL CLASSES: weight-2 split radical, aimed by ORBITAL MODULE (dive #55).

Dive #55 censused every minblk=2 group whose block kernel is SET-EQUAL to an orbital module of its
top -- exactly the kernels a weight-2 split radical can reach (dive #54). A hit aims at the MODULE,
not at a single group: 2-12 sibling groups share each (top, module) and no local invariant chooses
among them before the build. Seven classes are FULLY OPEN (every sibling teamCount=0 at r=24), so
the ambiguity costs nothing there -- whatever lands, scores.

    K = K0(sqrt(alpha)),  alpha = totally-positive generator of  P_{q,a} . P_{q,b}

with K0 a totally-real degree-12 field of the class's top, q completely split, and the pair (a,b)
selected by the dive-#54 orbital pre-filter at the class's kernel dim (9 for the 12T63 class, 10 for
the other six). Totally positive => r = 24 (dive #31), the only signature these 14 pairs still need.

TWO KNOWN, MEASURED RISKS (do not restate them as guarantees):
  * every available base has h+ in {2,4} -- there is no free totally-positive alpha, so the unit
    sign-lattice solve (matsolvemod) FAILS on a fraction of (q,a,b). That is a local, zero-SAIR-cost
    filter: sweep more pairs.
  * the orbital dim is a LOWER bound (test 0073): on 630 labeled gen12 builds the landed kernel
    exceeded the prediction 27% of the time, and at aimed kdim 9-10 only ~61-64% of builds land the
    predicted dim. An off-class landing is EXPECTED, not a refutation -- it is enqueued anyway iff
    the group it actually landed is itself a tc=0 non-baseline pair at r=24.

Gate (all must hold before enqueue): the Frobenius-density fingerprint (witness exclusion + L1 over
~5,100 primes, mb2_twist.gate) lands a group that is tc=0 + non-baseline at r=24; degree-24
irreducible; polsturm == 24; gp.scoreable_disc non-blank.

Usage:
    .venv/bin/python scripts/mb2_orbclass.py --tops 63 --ncand 6            # dry run
    .venv/bin/python scripts/mb2_orbclass.py --pilot 5 --enqueue            # PILOT
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import mb2_orbital as orb  # noqa: E402
import mb2_twist as tw  # noqa: E402
from mb2_twist_sign_producer import build_poly, held_groups, local_gate, still_open  # noqa: E402

from igp import gp, lmfdb  # noqa: E402

OUT = ROOT / "data" / "processed" / "mb2orbclass"
MARGIN = 0.15

# (top 12Tj, kernel dim of the orbital module, the sibling groups sharing it -- all tc=0 at r=24
# except 19768, which is tc=1 and therefore never enqueued). Dive #55's census.
CLASSES = [
    (63, 9, [14957, 14958, 14959, 14960]),
    (154, 10, [19768, 19769, 19770, 19771]),
    (107, 10, [18527, 18528]),
    (106, 10, [18525, 18526]),
    (58, 10, [16758]),
    (69, 10, [16759]),
    (126, 10, [19373]),
]

# Weight-2 split radical with a totally-positive generator. The divisor is P_{q,a} . P_{q,b}, so the
# complement cocycle is trivial (dive #48) and the kernel is the orbital module of {a,b} (dive #54, a
# LOWER bound). ORBDIM/ORBPERM come from mb2_orbital.GP_ORBITAL.
#
# REPAIR ARMS (test 0072, SAIR-validated on 24T23297). Every base of these seven classes has h+ in
# {2, 4}, and the plain weight-2 divisor's narrow class is (measured, 12T126: 0 of 96 pairs) usually
# not trivial, so the unit sign-lattice solve has NO solution and r=24 is unreachable. An even-f
# prime P above a prime already dividing disc K0 moves the divisor's narrow class while adding NO
# new prime to the degree-24 disc (scoreability untouched). The control arm (no repair) runs FIRST,
# so its failure is measured, not assumed. The repair is not proven to preserve the block kernel --
# the Frobenius-density gate downstream is what certifies where the radical actually landed.
BUILD_ORB = r"""
{
BUILD(top, c) =
  my(f = Pol(Vecrev(c)), K = bnfinit(f, 1), dK = K.disc, df, SU, S, UNS, reps, qs, n = 0);
  SU = bnfsignunit(K);
  S = matconcat([matrix(12, #SU[1,], i, j, (1 - SU[i,j]) / 2), vectorv(12, i, 1)]);
  UNS = concat(K.fu, [-1]);
  print("HPLUS|", bnfnarrow(K)[1]);
  reps = [[0, 0]];
  my(dp = factor(dK)[,1]);
  if(!NOREP,
    for(i = 1, #dp,
      my(dec = idealprimedec(K, dp[i]));
      for(j = 1, #dec,
        if(dec[j].f % 2 == 0, reps = concat(reps, [[dp[i], j]])))));
  print("REPS|", #reps - 1);
  df = poldisc(f);
  qs = [];
  forprime(q = 100, QMAX,
    if(df % q == 0, next);
    if(#polrootsmod(f, q) == 12, qs = concat(qs, [q]); if(#qs >= NQ, break)));
  print("SPLITQ|", qs);
  for(qi = 1, #qs,
    if(n >= NCAND, break);
    my(q = qs[qi], dec = idealprimedec(K, q), od, DM, pm, npair = 0, nprin = 0, npos = 0);
    od = ORBDIM(c, q);
    if(od == 0, next);
    pm = ORBPERM(K, f, q, dec, od[1]);
    DM = od[2];
    for(ri = 1, #reps, for(a = 1, 11, for(b = a + 1, 12,
      if(n >= NCAND, break);
      if(DM[pm[a], pm[b]] != TKDIM, next);
      npair++;
      my(rp = reps[ri], rtag = "none", I = idealmul(K, dec[a], dec[b]), e, al, sg, sol, u);
      if(rp[1] != 0,
        I = idealmul(K, I, idealprimedec(K, rp[1])[rp[2]]);
        rtag = Str(rp[1], "-", rp[2]));
      e = bnfisprincipal(K, I);
      if(#select(x -> x != 0, Vec(e[1])) > 0, next);
      nprin++;
      al = nfbasistoalg(K, e[2]);
      sg = nfeltsign(K, al);
      \\ h+ > 1 on every base here: the sign class need not be in the image of the unit sign map,
      \\ so this solve genuinely fails for some (q,a,b). Local filter, zero SAIR cost.
      sol = matsolvemod(S, 2, vectorv(12, i, if(sg[i] < 0, 1, 0)));
      if(sol == 0, next);
      u = 1;
      for(i = 1, #UNS, if(lift(sol[i]) % 2 == 1, u = nfeltmul(K, u, UNS[i])));
      al = nfeltmul(K, al, u);
      if(vecmin(nfeltsign(K, al)) < 0, next);
      npos++;
      n++;
      my(t = Map(), tot = 0, nrm = nfeltnorm(K, al), id = Str(q, "_", a, "_", b, "_", rtag));
      forprime(p = 3, FPMAX,
        if(dK % p == 0 || numerator(nrm) % p == 0, next);
        my(de = idealprimedec(K, p), ct = List(), bad = 0);
        for(i = 1, #de,
          my(P = de[i], mp = nfmodprinit(K, P), im = nfmodpr(K, al, mp));
          if(im == 0, bad = 1; break);
          if(issquare(im), listput(ct, P.f); listput(ct, P.f), listput(ct, 2 * P.f)));
        if(bad, next);
        my(s = vecsort(Vec(ct)), key = "");
        for(i = 1, #s, key = concat(key, Str(s[i])); if(i < #s, key = concat(key, ",")));
        mapput(t, key, if(mapisdefined(t, key), mapget(t, key), 0) + 1);
        tot++);
      my(ks = Vec(t));
      for(i = 1, #ks, print("FP|", id, "|", ks[i], "|", mapget(t, ks[i])));
      print("CAND|", id, "|", tot, "|", lift(al));
    )));
    print("ORBQ|", q, "|", npair, "|", nprin, "|", npos);
  );
}
"""


def bases(top: int, nbases: int) -> list:
    return [list(c) for c, _lab, _d, _h in
            lmfdb.fields(12, galois_label=f"12T{top}", class_number=1, max_r2=0, limit=nbases)]


def run_class(top: int, kdim: int, sibs: list, args, held: dict, winners: list, report: list):
    cts, dim = tw.library(top)
    inclass = [t for t in sibs if dim.get(t) == kdim]
    print(f"\n=== 12T{top} class kdim={kdim}: siblings {sibs}; library says kdim "
          f"{ {t: dim.get(t) for t in sibs} }; {len(cts)} groups in library")
    if not inclass:
        report.append(f"12T{top}: library disagrees with the census (no sibling at kdim {kdim})")
        print("  " + report[-1])
        return

    for cs in bases(top, args.nbases):
        if len(winners) >= args.pilot:
            return
        code = (orb.PRELUDE + orb.GP_ORBITAL + BUILD_ORB +
                f"NCAND = {args.ncand};\nNQ = {args.nq};\nFPMAX = {args.fpmax};\n"
                f"TKDIM = {kdim};\nQMAX = {args.qmax};\nNOREP = {1 if args.no_repair else 0};\n"
                f"BUILD({top}, {cs});\nquit\n")
        out = tw.gp_run(code, timeout=args.timeout)
        tallies, alphas = {}, {}
        for ln in out.splitlines():
            f = ln.strip().split("|")
            if f[0] == "FP":
                tallies.setdefault(f[1], {})[f[2]] = int(f[3])
            elif f[0] == "CAND":
                alphas[f[1]] = f[3]
            elif f[0] == "HPLUS":
                print(f"  h+ = {f[1]}")
            elif f[0] == "REPS":
                print(f"  even-f repair arms available: {f[1]}")
            elif f[0] == "SPLITQ":
                print(f"  split primes: {f[1]}")
            elif f[0] == "ORBQ":
                print(f"  q={f[1]}: {f[2]} (pair, arm) tried at kdim {kdim}, {f[3]} principal, "
                      f"{f[4]} totally-positive")
        if not tallies:
            report.append(f"12T{top}: no totally-positive weight-2 radical at kdim {kdim} on this "
                          f"base (h+ obstruction or no split q < {args.qmax})")
            print("  " + report[-1])
            continue

        got = 0
        for cid, tally in tallies.items():
            if got >= args.per_target or len(winners) >= args.pilot:
                break
            lt, l1, margin, ranked, killed = tw.gate(tally, cts)
            open_now = still_open(lt)
            ok = open_now and l1 < tw.L1_THRESH and margin > MARGIN
            print(f"  {cid}: lands 24T{lt} kdim={dim.get(lt)} L1={l1:.3f} margin={margin:.3f} "
                  f"[{len(killed)} killed, {len(ranked) - 1} survive] "
                  f"{'in-class' if lt in sibs else 'OFF-CLASS'} "
                  f"{'open' if open_now else 'NOT-OPEN'} {'GATED' if ok else 'REJECT'}")
            if not ok:
                continue
            c = build_poly(cs, alphas[cid])
            if not c:
                print("    BUILD-FAIL (degenerate)")
                continue
            good, why = local_gate(c)
            if not good:
                print(f"    LOCAL-GATE FAIL: {why}")
                continue
            q, a, b, rtag = cid.split("_")
            winners.append({"t": lt, "r": 24, "coeffs": c, "l1": round(l1, 4),
                            "margin": round(margin, 4), "kdim": dim.get(lt),
                            "tier": "pair" if lt in held else "new", "in_class": lt in sibs,
                            "src": f"base12T{top}:q{q}_{a}{b}:rep{rtag}",
                            "disc": str(gp.scoreable_disc(c))})
            got += 1
            print(f"    WIN 24T{lt} r=24 tier={winners[-1]['tier']} disc={winners[-1]['disc']}")
        if got:
            return
    if not any(w["src"].startswith(f"base12T{top}:") for w in winners):
        report.append(f"12T{top}: {len(inclass)} in-class targets, 0 gated candidates")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tops", type=str, default=None, help="comma list of 12Tj, else all 7 classes")
    ap.add_argument("--ncand", type=int, default=3, help="radicals fingerprinted per base")
    ap.add_argument("--nq", type=int, default=2, help="completely-split primes to collect")
    ap.add_argument("--qmax", type=int, default=10**6, help="q ramifies => under the grader's bound")
    ap.add_argument("--nbases", type=int, default=2, help="LMFDB bases per top (both are h=1)")
    ap.add_argument("--fpmax", type=int, default=tw.FP_MAX)
    ap.add_argument("--no-repair", action="store_true",
                    help="control arm only. The even-f repair arms consume the --ncand budget before "
                         "the q sweep gets deep (test 0075: on 12T69 every candidate at q=691,839 was "
                         "a repair arm, and the repair prime inflated the kernel to dim 11)")
    ap.add_argument("--per-target", type=int, default=1, help="max enqueued per base")
    ap.add_argument("--pilot", type=int, default=5, help="max enqueued in total (PILOT discipline)")
    ap.add_argument("--timeout", type=float, default=6000.0)
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    keep = {int(x) for x in args.tops.split(",")} if args.tops else None
    held = held_groups()
    winners, report = [], []
    for top, kdim, sibs in CLASSES:
        if keep is not None and top not in keep:
            continue
        if len(winners) >= args.pilot:
            report.append(f"12T{top}: skipped, pilot cap {args.pilot} reached")
            continue
        run_class(top, kdim, sibs, args, held, winners, report)

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(winners, open(OUT / "winners.json", "w"), indent=1)
    (OUT / "report.txt").write_text("\n".join(report) + "\n")
    print(f"\nmb2_orbclass: {len(winners)} locally-gated candidates on "
          f"{len({w['t'] for w in winners})} groups")
    for r in report:
        print("  -", r)

    if args.enqueue and winners:
        from igp import searchstore as store
        store.init()
        added = 0
        for w in winners:
            tag = f"lit:orbclass{w['tier']}:{w['t']}.{w['r']}:{w['src']}"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": w["coeffs"]}, target=tag):
                added += 1
        store.set_priority_prefix("lit:orbclassnew", 130.0)
        store.set_priority_prefix("lit:orbclasspair", 115.0)
        print(f"enqueued {added}. SAIR's Magma label is the authoritative gate.")


if __name__ == "__main__":
    main()
