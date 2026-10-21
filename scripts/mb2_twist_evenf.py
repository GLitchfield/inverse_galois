"""MINBLK=2 general_c2_TWIST with the EVEN-f DIVISOR REPAIR (research dive #52, part 2).

THE OBSTRUCTION. The sign-character engine (dive #50, scripts/mb2_twist_sign_producer.py) builds
alpha on the divisor Id * Q_a * Q_b, where Id is the product of odd-residue-degree primes above the
primes dividing d = core(disc K0), and Q_a, Q_b lie over a completely-split q. It then needs alpha
TOTALLY POSITIVE (=> r = 24), which it gets by multiplying in a unit whose sign vector solves
`matsolvemod` over the F2 sign lattice. That solve is possible iff [Id] = 0 in the narrow class group
Cl+(K0). On a base where [Id] != 0 the producer finds nothing -- 24T23297 / 12T245 is the case that
motivated this (test 0069 called it "sign-lattice-BLOCKED").

THE REPAIR. `core(N(alpha))` sees only the ODD part of the norm valuations. A prime P of EVEN residue
degree has N(P) = p^even = a perfect square, so P can be multiplied into the divisor WITHOUT changing
core(N(alpha)) -- hence without changing d, hence without changing the aimed character chi = Q(sqrt d)
or the aimed sibling G_chi -- while it DOES move the class of the divisor in Cl+(K0). Pick an even-f
prime in the complementary narrow class and the sign solve becomes possible.

    Id_repaired = (prod_{p | d} P_p^odd-f) * P_repair,   f(P_repair) even

Preference: P_repair over a prime p | disc K0, so p ALREADY divides the degree-24 discriminant and
scoreability is untouched (no new prime enters the disc). On 12T245 the fixer is the unique prime
above 3 (f = 2, e = 6, and 3^14 || disc K0).

THE GATE (this is why it is a PILOT, not a producer). The repair provably preserves d and chi, but it
is NOT proven to preserve the C2^12 BLOCK KERNEL -- the extra ramified prime enlarges the divisor's
support, and the kernel is what pins the sibling. So the Frobenius-density fingerprint is load-bearing
here, not a formality: it must come back kernel dim == 11 with the TARGET as top match. A different
dim-11 sibling means the repair moved the kernel -- that is a research result (push it back to the
agenda), not a build failure.

The no-repair arm runs as a CONTROL: it should find zero totally-positive alpha, reproducing the
shipped producer's failure on the same base.

Usage:
    .venv/bin/python scripts/mb2_twist_evenf.py --targets 23297            # dry run, report only
    .venv/bin/python scripts/mb2_twist_evenf.py --targets 23297 --enqueue
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
from mb2_twist_sign_producer import (  # noqa: E402
    PRELUDE,
    SHORTLIST,
    build_poly,
    held_groups,
    local_gate,
    still_open,
)

from igp import gp  # noqa: E402

OUT = ROOT / "data" / "processed" / "mb2twist"
KDIM = 11
MARGIN = 0.15

# Same build as dive #50's, with the divisor repaired. Two structural notes:
#   * REPAIR ARM. reps = [0] (control, no repair) followed by every even-f prime above a prime
#     dividing disc K0 -- those add no new prime to the degree-24 disc. The arms are tried in order
#     and the first that yields a totally-positive alpha with core(N) = d wins, so the control runs
#     first and its failure is recorded rather than assumed.
#   * The fingerprint is unchanged and stays valid: for p unramified and p not dividing N(alpha),
#     alpha is a p-unit, so each prime P | p of residue degree f contributes (f,f) if alpha is a
#     square mod P and (2f) otherwise. The repair only adds p = 3 to N(alpha), and p | disc K0 is
#     skipped by the loop anyway.
BUILD_EVENF = r"""
{
BUILD(top, d, c) =
  my(f = Pol(Vecrev(c)), K = bnfinit(f, 1), dK = K.disc, df, SU, S, UNS, base, pf, reps, qs, n = 0);
  SU = bnfsignunit(K);
  S = matconcat([matrix(12, #SU[1,], i, j, (1 - SU[i,j]) / 2), vectorv(12, i, 1)]);
  UNS = concat(K.fu, [-1]);
  pf = factor(d)[,1];
  base = idealhnf(K, 1);
  for(i = 1, #pf,
    my(od = select(P -> P.f % 2 == 1, idealprimedec(K, pf[i])));
    if(#od == 0, print("NOODD|", pf[i]); return());
    base = idealmul(K, base, od[1]));

  \\ repair arms: the control, then every even-f prime over a prime already in disc K0.
  reps = [[0, 0]];
  my(dp = factor(dK)[,1]);
  for(i = 1, #dp,
    my(dec = idealprimedec(K, dp[i]));
    for(j = 1, #dec,
      if(dec[j].f % 2 == 0,
        print("REP|", dp[i], "|", j, "|f=", dec[j].f, "|e=", dec[j].e);
        reps = concat(reps, [[dp[i], j]]))));

  df = poldisc(f);
  qs = [];
  forprime(q = 100, QMAX,
    if(df % q == 0, next);
    if(#polrootsmod(f, q) == 12, qs = concat(qs, [q]); if(#qs >= NQ, break)));
  print("SPLITQ|", qs);

  for(ri = 1, #reps,
    if(n >= NCAND, break);
    my(rp = reps[ri], Id = base, rtag = "none");
    if(rp[1] != 0,
      Id = idealmul(K, Id, idealprimedec(K, rp[1])[rp[2]]);
      rtag = Str(rp[1], "-", rp[2]));
    my(found = 0);
    for(qi = 1, #qs,
      if(n >= NCAND, break);
      my(q = qs[qi], dec = idealprimedec(K, q), od = 0, DM = 0, pm = 0);
      \\ dive #54's (a,b) orbital pre-filter -- see mb2_orbital.py. The repair prime does not move
      \\ the kernel (test 0072), so the aimed dim is still 12 - #components of the orbital graph.
      if(TKDIM > 0,
        od = ORBDIM(c, q);
        if(od == 0, next);
        pm = ORBPERM(K, f, q, dec, od[1]);
        DM = od[2];
        print("ORBQ|", q, "|", sum(a = 1, 11, sum(b = a + 1, 12, DM[pm[a], pm[b]] == TKDIM))));
      for(a = 1, ABMAX - 1, for(b = a + 1, ABMAX,
        if(n >= NCAND, break);
        if(TKDIM > 0 && DM[pm[a], pm[b]] != TKDIM, next);
        my(I = idealmul(K, Id, idealmul(K, dec[a], dec[b])), e, al, sg, sol, u);
        e = bnfisprincipal(K, I);
        if(#select(x -> x != 0, Vec(e[1])) > 0, next);
        al = nfbasistoalg(K, e[2]);
        sg = nfeltsign(K, al);
        sol = matsolvemod(S, 2, vectorv(12, i, if(sg[i] < 0, 1, 0)));
        if(sol == 0, next);
        u = 1;
        for(i = 1, #UNS, if(lift(sol[i]) % 2 == 1, u = nfeltmul(K, u, UNS[i])));
        al = nfeltmul(K, al, u);
        if(vecmin(nfeltsign(K, al)) < 0, next);
        if(core(nfeltnorm(K, al)) != d, next);
        n++; found++;
        my(t = Map(), tot = 0, nrm = nfeltnorm(K, al),
           id = Str(rtag, "_", q, "_", a, "_", b));
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
      ));
    );
    print("ARM|", rtag, "|", found);
  );
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", type=str, default="23297", help="comma list of 24Tt")
    ap.add_argument("--ncand", type=int, default=3, help="radicals fingerprinted per target")
    ap.add_argument("--nq", type=int, default=2)
    ap.add_argument("--qmax", type=int, default=10**6,
                    help="q ramifies in the disc, so it must stay under the grader's 10^6 bound")
    ap.add_argument("--fpmax", type=int, default=tw.FP_MAX)
    ap.add_argument("--abmax", type=int, default=12)
    ap.add_argument("--no-orbital-filter", action="store_true",
                    help="disable the dive-#54 (a,b) pre-filter and enumerate pairs blind")
    ap.add_argument("--timeout", type=float, default=6000.0)
    ap.add_argument("--per-target", type=int, default=2, help="max enqueued per target")
    ap.add_argument("--pilot", type=int, default=5, help="max enqueued in total")
    ap.add_argument("--allow-shared", action="store_true",
                    help="enqueue a pair a rival already holds (a disc-UNDERCUT: k=2 caps us at 0.5, "
                         "but it also collapses the rival's score by log(D_ours)/log(D_theirs))")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    keep = {int(x) for x in args.targets.split(",")}
    held = held_groups()
    winners, report = [], []

    for t, top, d, cs, h in SHORTLIST:
        if t not in keep or len(winners) >= args.pilot:
            continue
        open_now = still_open(t)
        if not open_now and not args.allow_shared:
            report.append(f"24T{t}: SKIP -- not tc=0 / non-baseline at r=24 (rival claim); "
                          f"pass --allow-shared to undercut it")
            print(report[-1])
            continue

        if t in orb.WEIGHT2_UNREACHABLE:
            report.append(f"24T{t}: SKIP -- kernel is not an orbital module of its top, so no "
                          f"weight-2 split radical reaches it (dive #54); use mb2_sweep6.py")
            print(report[-1])
            continue

        cts, dim = tw.library(top)
        if dim.get(t) != KDIM:
            report.append(f"24T{t}: SKIP -- not a dim-{KDIM} sibling of 12T{top}")
            print(report[-1])
            continue

        print(f"\n=== 24T{t} over 12T{top}, d={d}, h={h}, "
              f"{'OPEN tc=0' if open_now else 'SHARED (rival holds it) -- disc-undercut'}")
        for l1r, mass, u in tw.resolution(cts, t)[:3]:
            kill = f"~{1 / mass:.0f} primes" if mass > 0 else "NEVER (witness-proof)"
            print(f"  rival 24T{u} kdim={dim.get(u)}: L1={l1r:.3f} witness mass={mass:.4f} -> {kill}")

        tkdim = 0 if args.no_orbital_filter else KDIM
        code = (PRELUDE + orb.GP_ORBITAL + BUILD_EVENF + f"NCAND = {args.ncand};\nNQ = {args.nq};\n"
                f"FPMAX = {args.fpmax};\nABMAX = {args.abmax};\nTKDIM = {tkdim};\n"
                f"QMAX = {args.qmax};\nBUILD({top}, {d}, {cs});\nquit\n")
        out = tw.gp_run(code, timeout=args.timeout)

        tallies, alphas, arms = {}, {}, {}
        for ln in out.splitlines():
            fl = ln.strip().split("|")
            if fl[0] == "FP":
                tallies.setdefault(fl[1], {})[fl[2]] = int(fl[3])
            elif fl[0] == "CAND":
                alphas[fl[1]] = fl[3]
            elif fl[0] == "ORBQ":
                print(f"  orbital pre-filter q={fl[1]}: {fl[2]} of 66 pairs at kdim {tkdim}")
            elif fl[0] == "ARM":
                arms[fl[1]] = int(fl[2])
            elif fl[0] == "REP":
                print(f"  even-f repair candidate: prime {fl[1]} idx {fl[2]} {fl[3]} {fl[4]}")
            elif fl[0] == "SPLITQ":
                print(f"  split primes: {fl[1]}")
            elif fl[0] == "NOODD":
                report.append(f"24T{t}: BUILD-BLOCK -- no odd-f prime above {fl[1]} | d")
                print(report[-1])
        for rtag, cnt in arms.items():
            tag = "CONTROL (no repair)" if rtag == "none" else f"repair P_{rtag}"
            print(f"  arm {tag}: {cnt} totally-positive alpha with core(N)={d}")
        if arms.get("none", 0) > 0:
            report.append(f"24T{t}: NOTE -- the control arm (no repair) succeeded; the base is not "
                          f"narrow-class obstructed after all")
        if not tallies:
            report.append(f"24T{t}: no candidate radical on ANY repair arm (q < {args.qmax})")
            print(report[-1])
            continue

        got = 0
        for cid, tally in tallies.items():
            if got >= args.per_target or len(winners) >= args.pilot:
                break
            lt, l1, margin, ranked, killed = tw.gate(tally, cts)
            on_target = lt == t
            ok = on_target and l1 < tw.L1_THRESH and margin > MARGIN
            print(f"  {cid}: lands 24T{lt} kdim={dim.get(lt)} L1={l1:.3f} margin={margin:.3f} "
                  f"[{len(killed)} rivals witness-killed, {len(ranked) - 1} survive] "
                  f"{'GATED' if ok else 'REJECT'}{'' if on_target else ' [OFF-TARGET]'}")
            if not on_target:
                # The repair moved the block kernel: d and chi are preserved by construction, so a
                # different sibling means the extra ramified prime perturbed the C2^12 kernel. That
                # is dive #52's open GATE question, answered in the negative -- a research result.
                report.append(f"24T{t}: KERNEL MOVED -- repair arm {cid} lands 24T{lt} "
                              f"(kdim {dim.get(lt)}), not the aimed sibling")
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
            rtag, q, a, b = cid.split("_")
            winners.append({"t": lt, "r": 24, "coeffs": c, "l1": round(l1, 4),
                            "margin": round(margin, 4), "tier": "pair" if lt in held else "new",
                            "src": f"base12T{top}:d{d}:rep{rtag}:q{q}_{a}{b}",
                            "disc": str(gp.scoreable_disc(c))})
            got += 1
            print(f"    WIN 24T{lt} r=24 L1={l1:.3f} disc={winners[-1]['disc']}")
        if got == 0:
            report.append(f"24T{t}: {len(tallies)} radicals built, none gated on-target")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(winners, open(OUT / "evenf_winners.json", "w"), indent=1)
    (OUT / "evenf_report.txt").write_text("\n".join(report) + "\n")
    print(f"\nmb2_twist_evenf: {len(winners)} locally-gated candidates on "
          f"{len({w['t'] for w in winners})} targets")

    if args.enqueue and winners:
        from igp import searchstore as store
        store.init()
        added = 0
        for w in winners:
            tag = f"lit:mb2twistfix{w['tier']}:{w['t']}.{w['r']}:{w['src']}"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": w["coeffs"]}, target=tag):
                added += 1
        store.set_priority_prefix("lit:mb2twistfixnew", 130.0)
        store.set_priority_prefix("lit:mb2twistfixpair", 115.0)
        print(f"enqueued {added}. SAIR's Magma label is the authoritative gate.")


if __name__ == "__main__":
    main()
