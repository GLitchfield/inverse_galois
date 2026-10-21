"""MINBLK=2 general_c2_TWIST, AIMED by the SIGN character (research dive #50).

Dive #49 built the engine: a mixed divisor on a completely-split prime pair (even weight) plus the
odd-residue-degree primes above a square-free `d` realizes a dim-11 block kernel whose complement
cocycle is the norm character chi = Q(sqrt N(alpha)). Dive #49 then had to SCREEN each base for a
`d` in the norm square-class group, and took whatever sibling that `d` happened to aim at.

Dive #50 removes the screen. Take chi = chi_sgn, the SIGN character of the top H (kernel H n A12).
It cuts out Q(sqrt disc K0), which is a subfield of the Galois closure M unconditionally -- so

    d = core(disc K0)

is a reachable norm class for EVERY base whose top is not inside A12, with no screening, and it
aims at exactly ONE sibling: G_{chi_sgn}. Base selection becomes a lookup, and the (target, base, d)
table below is that lookup, computed by scripts/mb2_twist_sign.g + scripts/mb2_chi_d.py.

The odd-f necessary condition is automatic for this d: p | core(disc) => v_p(disc) is odd => some
prime above p has odd residue degree.

PILOT DISCIPLINE. The dive-#49 engine's own SAIR labels (test 0068) had not returned when this was
written, so the sign-character AIM is LOCAL-GATED, not SAIR-validated. Default caps build at one
candidate per target and five in total, spread across DISTINCT targets -- five different bases each
landing its predicted sign sibling validates the map. Scale only after official labels match.
(2026-07-13: SAIR-validated 19/19 across 10 targets -- scaled; chi_d.csv extends the shortlist.)

Enqueue gate (all must hold):
  * the fingerprinted group IS the intended target (not merely some gated dim-11 sibling);
  * L1 < 0.35, runner-up margin > 0.15, kernel dim == 11 (780-prime Frobenius fingerprint);
  * degree 24, irreducible, polsturm == 24, gp.scoreable_disc non-blank.

Usage:
    .venv/bin/python scripts/mb2_twist_sign_producer.py                    # dry run, report only
    .venv/bin/python scripts/mb2_twist_sign_producer.py --enqueue
    .venv/bin/python scripts/mb2_twist_sign_producer.py --targets 23664,21582 --enqueue
"""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import mb2_orbital as orb  # noqa: E402
import mb2_twist as tw  # noqa: E402

from igp import baseline, gp  # noqa: E402

OUT = ROOT / "data" / "processed" / "mb2twist"
KDIM = 11
MARGIN = 0.15

# (target 24Tt, top 12Tj, d = core(disc K0), base coeffs ascending, class number)
# Ordered by d: the small-d bases ramify at small primes, so their degree-24 discs stay smooth.
SHORTLIST = [
    (23664, 253, 3, [-33683, -39232, 48128, 88600, 24783, -19216, -9552, 1400, 1123, -32, -56, 0, 1], 1),  # noqa: E501
    (21582, 170, 5, [-9595, -6060, 22725, 22920, -6999, -15300, -3707, 1830, 774, -60, -48, 0, 1], 1),  # noqa: E501
    (23297, 245, 5, [30256, 181536, 408456, 397688, 104715, -72684, -35038, 3912, 2934, -62, -93, 0, 1], 1),  # noqa: E501
    # Dive #59's sextic-derived 12T36 base (NOT in LMFDB, which holds only 2 totally-real 12T36
    # fields and both are narrow-DEAD). h = 3 but delta = 0 => the sign gate is vacuous. Its d is
    # NOT core(disc K0) = 3881: that is the SIGN character, which aims at the contested 24T18008.
    # 24T18009 is the sibling of a different index-2 subgroup, and mb2_chi_d_base.py pins its
    # d = 5 (438 decisive Frobenius equations, unique survivor; 5 * 3881 = 19405 = d(chi2) checks
    # the homomorphism law).
    (18009, 36, 5, [6264469, 1670201, -3640611, -770897, 773737, 117664, -78270, -8027, 4036, 253, -102, -3, 1], 3),  # noqa: E501
    # The SECOND index-2 character of that same base: chi2 -> 24T18007 at d = 19405 = 5 * 3881
    # (mb2_chi_d_base.py, 438 decisive equations, unique survivor, both factors odd-f => reachable).
    (18007, 36, 19405, [6264469, 1670201, -3640611, -770897, 773737, 117664, -78270, -8027, 4036, 253, -102, -3, 1], 3),  # noqa: E501
    (21904, 192, 37, [-604, 4128, -3488, -8904, 9140, 4584, -4692, -1056, 850, 120, -52, -4, 1], 1),  # noqa: E501
    (21572, 167, 89, [-1, -10, -20, 28, 79, -25, -102, 9, 56, -1, -13, 0, 1], 1),
    (21376, 156, 101, [13520, -40560, -30420, 94900, 71565, -21060, -19381, 1674, 1926, -46, -78, 0, 1], 1),  # noqa: E501
    (22401, 207, 1129, [-1144611, -1715912, 720580, 1875888, 400382, -286760, -90918, 13424, 5717, -168, -130, 0, 1], 1),  # noqa: E501
    (24334, 281, 5077, [-24, -144, 540, 1034, -1062, -2448, -691, 666, 333, -36, -33, 0, 1], 1),  # noqa: E501
    (21593, 175, 19567, [1, 2, -15, -16, 78, 16, -121, -2, 66, 0, -14, 0, 1], 1),
    (24492, 288, 10351121, [4725369, 15062247, 15376778, 5644029, -383104, -745649, -109038, 27019, 6836, -296, -141, 0, 1], 2),  # noqa: E501
    (24157, 274, 97296769, [-1, 7, -1, -49, 40, 90, -71, -67, 43, 20, -11, -2, 1], 1),
]


def _chi_d_entries():
    """Extend the shortlist from chi_d.csv (mb2_chi_d.py, dive #51's general-chi d-finder): every
    BUILD-READY row (d pinned + reachable + h<=2) whose target isn't already in the static list.
    The engine is SAIR-validated 19/19 on the static entries; these are new aims of the SAME
    mechanism. Sorted by d (small d ramifies small -> smoother deg-24 disc)."""
    path = OUT / "chi_d.csv"
    if not path.exists():
        return []
    have = {t for t, *_ in SHORTLIST}
    rows = []
    with open(path) as fh:
        for row in csv.DictReader(fh):
            try:
                t, d = int(row["t"]), int(row["d"] or 0)
                h = int(row["h"] or 0)
            except ValueError:
                continue
            if (t in have or not d or not int(row["reachable"] or 0)
                    or int(row["contradiction"] or 0) or h > 2):
                continue
            have.add(t)
            rows.append((t, int(row["top"]), d, json.loads(row["coeffs"]), h))
    rows.sort(key=lambda e: e[2])
    return rows

# Dive #49's BUILD, with two changes forced by this shortlist's bases.
#
# (1) q-RANGE. A completely-split prime has density 1/|H|, and dive #49's demo tops were small
#     (|H| = 36..72) so its q < 6000 window always held one. These tops run to |H| = 28800, where
#     the expected count below 6000 is 0.03 -- the engine reports "no candidate" for a reason that
#     is arithmetic, not structural. The window has to scale as |H|, and its ceiling is set by
#     SCOREABILITY: q ramifies in K/K0, so q divides the degree-24 disc, so q must stay under the
#     grader's 10^6 factorization bound. Search from small q up and take the first hits (smallest q
#     = smallest disc).
# (2) PRINCIPALITY. With a non-trivial class group the mixed divisor need not be principal, and
#     bnfisprincipal's second component is only a generator when the first vanishes -- using it
#     regardless would silently build a radical of the WRONG element.
# (3) THE ODD-f PRIME IS A CHOICE, NOT A LOOKUP (test 0077). p | d can have SEVERAL primes of odd
#     residue degree, and they sit in DIFFERENT ideal classes. Any of them gives v_p(N(Id)) odd, so
#     core(N) = d holds for all of them -- but only some make [Id] trivial. Taking od[1] blindly
#     wedged 24T18007: [Id] = [2] in Cl = Z/3, every prime above a completely-split q is principal,
#     so [Id . P_a . P_b] = [Id] != 0 for EVERY q and EVERY (a,b) -- no principal radical exists at
#     any parameter. The 5th prime above 3881 has f = 3 AND class [0]. So pick the odd-f primes by
#     CLASS (search the product of the per-p odd-f lists for a trivial-class Id), and only fall back
#     to od[1] when no choice is principal -- there the (a,b) sweep can still cancel [Id] on a base
#     whose split primes are non-principal. h = 1 bases are unaffected (everything is principal).
BUILD_SIGN = r"""
{
CHOOSEID(K, pf) =
  my(ls = vector(#pf), cnt, tot, Idc);
  for(i = 1, #pf,
    ls[i] = select(P -> P.f % 2 == 1, idealprimedec(K, pf[i]));
    if(#ls[i] == 0, print("NOODD|", pf[i]); return(0)));
  cnt = vector(#pf, i, #ls[i]);
  tot = prod(i = 1, #pf, cnt[i]);
  for(k = 0, tot - 1,
    my(m = k, idx = vector(#pf));
    Idc = idealhnf(K, 1);
    for(i = 1, #pf, idx[i] = m % cnt[i] + 1; m = m \ cnt[i]);
    for(i = 1, #pf, Idc = idealmul(K, Idc, ls[i][idx[i]]));
    if(#select(x -> x != 0, Vec(bnfisprincipal(K, Idc)[1])) == 0,
      print("IDPICK|", idx, "|principal"); return(Idc)));
  Idc = idealhnf(K, 1);
  for(i = 1, #pf, Idc = idealmul(K, Idc, ls[i][1]));
  print("IDPICK|first|class ", Vec(bnfisprincipal(K, Idc)[1]));
  Idc;
}
{
BUILD(top, d, c) =
  my(f = Pol(Vecrev(c)), K = bnfinit(f, 1), dK = K.disc, df, SU, S, UNS, Id, pf, qs, n = 0);
  SU = bnfsignunit(K);
  S = matconcat([matrix(12, 11, i, j, (1 - SU[i,j]) / 2), vectorv(12, i, 1)]);
  UNS = concat(K.fu, [-1]);
  pf = factor(d)[,1];
  Id = CHOOSEID(K, pf);
  if(Id == 0, return());
  \\ q splits completely <=> f has 12 distinct roots mod q; polrootsmod is far cheaper than
  \\ idealprimedec, and q | poldisc is excluded so q cannot divide the index either.
  df = poldisc(f);
  qs = [];
  forprime(q = 100, QMAX,
    if(df % q == 0, next);
    if(#polrootsmod(f, q) == 12, qs = concat(qs, [q]); if(#qs >= NQ, break)));
  print("SPLITQ|", qs);
  for(qi = 1, #qs,
    if(n >= NCAND, break);
    my(q = qs[qi], dec = idealprimedec(K, q), od = 0, DM = 0, pm = 0);
    \\ dive #54: kdim(a,b) = 12 - #components of the orbital graph of {a,b}. Skip the pairs that
    \\ cannot reach the aimed kernel dim instead of paying a build + a 5,133-prime fingerprint to
    \\ watch them land the wrong sibling.
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
      n++;
      my(t = Map(), tot = 0, nrm = nfeltnorm(K, al), id = Str(q, "_", a, "_", b));
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
}
"""

PRELUDE = "default(parisizemax, 8*10^9);\n"


def held_groups() -> dict:
    counts: dict = {}
    with open(ROOT / "data" / "targets" / "realized.csv") as fh:
        for row in csv.DictReader(fh):
            if row["t"]:
                counts[int(row["t"])] = counts.get(int(row["t"]), 0) + 1
    return counts


def still_open(t: int, r: int = 24) -> bool:
    """teamCount == 0 AND non-baseline: a genuinely open pair scores on any valid disc."""
    prog = json.load(open(ROOT / "data" / "processed" / "progress.json"))
    e = prog.get(f"{t},{r}")
    tc = e.get("teamCount") if isinstance(e, dict) else None
    return tc == 0 and not baseline.is_baseline(str(t), str(r))


def build_poly(coeffs: list, alpha: str, timeout: float = 1800.0) -> list:
    """alpha arrives as a coordinate vector on the integral basis, not a polynomial (test 0068)."""
    cs = ",".join(str(c) for c in coeffs[::-1])
    body = (PRELUDE +
            f"f=Pol([{cs}],y); K=nfinit(f); al=lift(nfbasistoalg(K, {alpha}));\n"
            "r=rnfequation(f, x^2 - al);\n"
            "print(if(poldegree(r)<24, \"DEGENERATE\", Vec(polredbest(r))));")
    out = subprocess.run(["gp", "-q"], input=body, capture_output=True, text=True,
                         timeout=timeout).stdout
    if "DEGENERATE" in out or "[" not in out:
        return []
    return [int(x) for x in out.strip().strip("[]").split(",")][::-1]


def local_gate(c: list) -> tuple[bool, str]:
    if len(c) != 25:
        return False, "degree"
    cs = ",".join(str(x) for x in c[::-1])
    out = subprocess.run(["gp", "-q"], capture_output=True, text=True, timeout=600,
                         input=f"p=Pol([{cs}]);print(poldegree(p),\"|\",polisirreducible(p),"
                               "\"|\",polsturm(p));").stdout.strip()
    deg, irr, rr = out.split("|")
    if int(deg) != 24 or int(irr) != 1:
        return False, "reducible"
    if int(rr) != 24:
        return False, f"r={rr}"
    if gp.scoreable_disc(c) is None:
        return False, "blank-risk disc"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", type=str, default=None, help="comma list of 24Tt, else all")
    ap.add_argument("--ncand", type=int, default=3, help="radicals fingerprinted per target")
    ap.add_argument("--nq", type=int, default=2, help="completely-split primes to collect")
    ap.add_argument("--qmax", type=int, default=10**6,
                    help="q ramifies in the disc, so it must stay under the grader's 10^6 bound")
    ap.add_argument("--fpmax", type=int, default=tw.FP_MAX,
                    help="fingerprint prime bound; 6000 is under-powered vs subgroup rivals")
    ap.add_argument("--abmax", type=int, default=12,
                    help="sweep the (a,b) prime pair over dec[1..abmax]; on a non-rational base "
                         "12 primes above q carry DIFFERENT narrow classes, so the pair choice is "
                         "what zeroes [Id] -- the old a<=4,b<=5 window saw only 10 of the 66 pairs")
    ap.add_argument("--no-orbital-filter", action="store_true",
                    help="disable the dive-#54 (a,b) pre-filter and enumerate pairs blind (the old "
                         "behaviour: ~3x the builds, and a thin-margin off-target landing risk)")
    ap.add_argument("--accept-open", action="store_true",
                    help="enqueue an OFF-TARGET landing too, if the witness gate is decisive and "
                         "the group it lands is itself a tc=0 non-baseline pair at r=24")
    ap.add_argument("--timeout", type=float, default=6000.0)
    ap.add_argument("--per-target", type=int, default=1, help="max enqueued per target")
    ap.add_argument("--pilot", type=int, default=5, help="max enqueued in total")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    keep = {int(x) for x in args.targets.split(",")} if args.targets else None
    held = held_groups()
    winners, report = [], []

    shortlist = SHORTLIST + _chi_d_entries()
    for t, top, d, cs, h in shortlist:
        if keep is not None and t not in keep:
            continue
        if len(winners) >= args.pilot:
            report.append(f"24T{t}: skipped, pilot cap {args.pilot} reached")
            continue
        if not still_open(t):
            report.append(f"24T{t}: SKIP -- no longer tc=0 / non-baseline at r=24 (rival claim)")
            print(report[-1])
            continue
        if t in orb.WEIGHT2_UNREACHABLE:
            report.append(f"24T{t}: SKIP -- kernel is NOT an orbital module of 12T{top}, so no "
                          f"weight-2 split radical reaches it (dive #54); use mb2_sweep6.py")
            print(report[-1])
            continue

        cts, dim = tw.library(top)
        if dim.get(t) != KDIM:
            report.append(f"24T{t}: SKIP -- not a dim-{KDIM} sibling of 12T{top} (lib says "
                          f"{dim.get(t)})")
            print(report[-1])
            continue
        tier = "pair" if t in held else "new"
        print(f"\n=== 24T{t} over 12T{top}, d={d}, h={h}, tier={tier} "
              f"({len(dim)} siblings, {sum(1 for k in dim.values() if k == KDIM)} at dim 11)")
        for l1r, mass, u in tw.resolution(cts, t)[:3]:
            kill = f"~{1 / mass:.0f} primes" if mass > 0 else "NEVER (witness-proof)"
            print(f"  rival 24T{u} kdim={dim.get(u)}: L1={l1r:.3f} witness mass={mass:.4f} "
                  f"-> {kill}")

        tkdim = 0 if args.no_orbital_filter else KDIM
        code = (PRELUDE + orb.GP_ORBITAL + BUILD_SIGN + f"NCAND = {args.ncand};\nNQ = {args.nq};\n"
                f"FPMAX = {args.fpmax};\nABMAX = {args.abmax};\nTKDIM = {tkdim};\n"
                f"QMAX = {args.qmax};\nBUILD({top}, {d}, {cs});\nquit\n")
        out = tw.gp_run(code, timeout=args.timeout)
        tallies, alphas, qs = {}, {}, "?"
        for ln in out.splitlines():
            f = ln.strip().split("|")
            if f[0] == "FP":
                tallies.setdefault(f[1], {})[f[2]] = int(f[3])
            elif f[0] == "CAND":
                alphas[f[1]] = f[3]
            elif f[0] == "ORBQ":
                print(f"  orbital pre-filter q={f[1]}: {f[2]} of 66 pairs at kdim {tkdim}")
            elif f[0] == "SPLITQ":
                qs = f[1]
                print(f"  split primes: {qs}")
            elif f[0] == "NOODD":
                report.append(f"24T{t}: BUILD-BLOCK -- no odd-f prime above {f[1]} | d")
                print(report[-1])
        if not tallies:
            report.append(f"24T{t}: no candidate radical (split q={qs}; no principal even-weight "
                          f"divisor with core(N) = {d} under q < {args.qmax})")
            print(report[-1])
            continue

        got = 0
        for cid, tally in tallies.items():
            if got >= args.per_target or len(winners) >= args.pilot:
                break
            lt, l1, margin, ranked, killed = tw.gate(tally, cts)
            on_target = lt == t
            # A landing that is not the aimed sibling is still a WIN if it is itself an open pair:
            # the daemon records the label SAIR returns, not the one we aimed at.
            accept = on_target or (args.accept_open and still_open(lt))
            ok = accept and l1 < tw.L1_THRESH and margin > MARGIN
            print(f"  {cid}: lands 24T{lt} kdim={dim.get(lt)} L1={l1:.3f} margin={margin:.3f} "
                  f"[{len(killed)} rivals witness-killed, {len(ranked) - 1} survive] "
                  f"{'GATED' if ok else 'REJECT'}"
                  f"{'' if on_target else ' [OFF-TARGET' + (', OPEN]' if accept else ']')}")
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
            q, a, b = cid.split("_")
            wtier = "pair" if lt in held else "new"
            winners.append({"t": lt, "r": 24, "coeffs": c, "l1": round(l1, 4),
                            "margin": round(margin, 4), "tier": wtier,
                            "src": f"base12T{top}:d{d}:q{q}_{a}{b}",
                            "disc": str(gp.scoreable_disc(c))})
            got += 1
            print(f"    WIN 24T{lt} r=24 tier={wtier} L1={l1:.3f} disc={winners[-1]['disc']}")
        if got == 0:
            report.append(f"24T{t}: {len(tallies)} radicals built, none gated on-target")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(winners, open(OUT / "sign_winners.json", "w"), indent=1)
    (OUT / "sign_report.txt").write_text("\n".join(report) + "\n")
    print(f"\nmb2_twist_sign_producer: {len(winners)} locally-gated candidates on "
          f"{len({w['t'] for w in winners})} targets")

    if args.enqueue and winners:
        from igp import searchstore as store
        store.init()
        added = 0
        for w in winners:
            tag = f"lit:mb2twsign{w['tier']}:{w['t']}.{w['r']}:{w['src']}"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": w["coeffs"]}, target=tag):
                added += 1
        store.set_priority_prefix("lit:mb2twsignnew", 130.0)
        store.set_priority_prefix("lit:mb2twsignpair", 115.0)
        print(f"enqueued {added}. SAIR's Magma label is the authoritative gate.")


if __name__ == "__main__":
    main()
