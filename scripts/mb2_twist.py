"""MINBLK=2 general_c2_TWIST: realize a NONTRIVIAL complement cocycle chi (research dive #49).

Test 0067's blocker: a subgroup of W = C2 wr H with base-intersection K (dim 11) is NOT determined
by K -- it also carries a complement cocycle in H^1(H, F2^12/K) = Hom(H, F2), a quadratic character
chi of H. A radical whose divisor sits on completely-split primes has N(alpha) = +-q1^|w1| q2^|w2|,
so for even weights N(alpha) is +-1 mod squares => chi = 1 => the construction ALWAYS lands the SPLIT
sibling (24T22545 over 12T210, 497/497 landings). The open pairs in these families are open precisely
because they are the TWISTED siblings.

THE DIAL (dive #49, derived + validated end-to-end):

    chi is the Galois character of Q(sqrt(N(alpha))).

Proof sketch: dim K = 11 means the only relation is the all-ones one, i.e. N(alpha) in (M*)^2.
Pick beta_j with beta_j^2 = sigma_j(alpha); then gamma = prod_j beta_j satisfies gamma^2 = N(alpha)
in Q, so gamma lies in M and h(gamma)/gamma = +-1 defines exactly the cocycle chi in Hom(H, F2). So
chi is nontrivial iff N(alpha) = d . square with Q(sqrt d) a (real, since K0 is totally real)
quadratic subfield of the Galois closure M.

CONSEQUENCES:
  * split primes can NEVER twist (they are unramified in M, so their d is not a subfield disc) --
    test 0067's blocker is structural, not a sampling artifact;
  * NECESSARY LOCAL CONDITION on the base: for every p | d, K0 must have a prime above p with ODD
    residue degree f (else v_p(N(alpha)) is always even and d is not in the norm square-class group);
  * the base of test 0067 (12T210) FAILS this: its quadratic subfields come from {5,13,17}, all of
    whose primes have even f -- so its four tc=0 twisted siblings are unreachable FROM THAT BASE.
    The fix is BASE SELECTION, not a new engine.

THE ENGINE -- a MIXED divisor (both dials at once):

    alpha = gen( P_{q,a} . P_{q,b} . prod_{p | d} P_p )        (q completely split, |w| EVEN)

  the split-prime pair supplies the dim-11 kernel (<H.1_w> lies in the even-weight submodule), and
  the odd-f ramified primes supply the norm character chi_d. A PURE ramified radical does NOT work:
  its conjugate divisors coincide heavily => many relations => a tiny kernel (dim 2-3, validated).

VALIDATED (dive #49, LOCAL-GATED, 780-prime Frobenius fingerprint vs the full submodule x complement
library of scripts/mb2_multi_gdist.g), 4 bases / 4 tops, every one landing a dim-11 TWISTED sibling
at r=24 with a clean gate:

    12T42  d=39   -> 24T18031 [twist]  L1=0.12  (runner-up 0.53)
    12T23  d=79   -> 24T16707 [twist]  L1=0.13  (runner-up 0.50)
    12T19  d=5    -> 24T16121 [sgn]    L1=0.08  (runner-up 0.41)
    12T45  d=173  -> 24T18038 [sgn]    L1=0.12  (runner-up 0.30)

Those four tops are small (|H| = 36..72) and their siblings are all CONTESTED (tc >= 1) -- they are
the mechanism demo, not the payload. The payload is to point this at bases whose tops carry tc=0
twisted siblings.

Usage:
    .venv/bin/python scripts/mb2_twist.py --screen              # which bases admit a reachable d
    .venv/bin/python scripts/mb2_twist.py --build 12T42         # build + fingerprint one base
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from igp import baseline, lmfdb  # noqa: E402

L1_THRESH = 0.35
MARGIN = 0.15
# Fingerprint prime bound. 6000 (~780 primes) has an L1 sampling-noise floor of ~0.15, which is
# more than twice the true distance to an index-2 SUBGROUP rival -- the gate was blind there
# (dive #51). 50000 (~5100 primes) is where the witness test below kills such a rival 100% of the
# time in simulation; the cost is seconds of nfmodpr, not a bottleneck.
FP_MAX = 50000
OUT = ROOT / "data" / "processed" / "mb2twist"


def gp_run(code: str, timeout: float = 3000.0) -> str:
    p = subprocess.run(["gp", "-q"], input=code, capture_output=True, text=True, timeout=timeout)
    return p.stdout


SCREEN = r"""
{
SCREEN(lab, c) =
  my(f = Pol(Vecrev(c)), K = nfinit(f), dK = K.disc, ram, odd, split, ds);
  ram = Vec(factor(abs(dK))[,1]);
  odd = select(p -> #select(P -> P.f % 2 == 1, idealprimedec(K, p)) > 0, ram);
  \\ p splits completely in K0  <=>  p splits completely in the Galois closure M, so
  \\ Q(sqrt d) subset M  <=>  kronecker(d, p) = 1 for every such p (Chebotarev: else half fail).
  split = [];
  forprime(p = 3, 30000,
    if(dK % p == 0, next);
    if(#idealprimedec(K, p) == 12, split = concat(split, [p]));
    if(#split >= 40, break));
  ds = [];
  for(m = 1, 2^#odd - 1,
    my(d = 1, ok = 1);
    for(i = 1, #odd, if(bitand(m, 2^(i-1)), d *= odd[i]));
    for(i = 1, #split, if(kronecker(d, split[i]) != 1, ok = 0; break));
    if(ok, ds = concat(ds, [d])));
  \\ fewer than 20 completely-split primes => the subfield test is not decisive; report and skip
  print("SCREEN|", lab, "|", ram, "|", odd, "|", #split, "|", if(#split >= 20, ds, []));
}
"""

BUILD = r"""
{
BUILD(top, d, c) =
  my(f = Pol(Vecrev(c)), K = bnfinit(f, 1), dK = K.disc, SU, S, UNS, Id, pf, n = 0);
  SU = bnfsignunit(K);
  S = matconcat([matrix(12, 11, i, j, (1 - SU[i,j]) / 2), vectorv(12, i, 1)]);
  UNS = concat(K.fu, [-1]);
  pf = factor(d)[,1];
  Id = idealhnf(K, 1);
  for(i = 1, #pf,
    Id = idealmul(K, Id, select(P -> P.f % 2 == 1, idealprimedec(K, pf[i]))[1]));
  forprime(q = 100, 6000,
    if(n >= NCAND, break);
    my(dec = idealprimedec(K, q));
    if(#dec != 12, next);
    for(a = 1, 4, for(b = a + 1, 5,
      if(n >= NCAND, break);
      my(I = idealmul(K, Id, idealmul(K, dec[a], dec[b])), e, al, sg, sol, u);
      e = bnfisprincipal(K, I);
      \\ h=1 bases only: the ideal is principal, so a generator always exists
      al = nfbasistoalg(K, e[2]);
      sg = nfeltsign(K, al);
      \\ totally-positive unit twist => r = 24 (deterministic, not the stochastic 33%)
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
          \\ alpha is a p-unit => the deg-24 cycle type is read off the base decomposition
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


def library(top: int) -> tuple[dict, dict]:
    """Cycle-type densities of every group C2 wr H can land in: submodules x complement classes."""
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / f"lib{top}.txt"
    if not raw.exists():
        p = subprocess.run(
            ["gap", "-q", "-b", "-c", f"TOP:={top};", str(ROOT / "scripts" / "mb2_multi_gdist.g")],
            capture_output=True, text=True, timeout=3600)
        raw.write_text(p.stdout)
    cts, dim = {}, {}
    for ln in raw.read_text().splitlines():
        f = ln.strip().split("|")
        if f[0] == "SUB":
            dim[int(f[1])] = int(f[2])
        elif f[0] == "CT":
            cts.setdefault(int(f[1]), {})
            cts[int(f[1])][f[2]] = cts[int(f[1])].get(f[2], 0) + int(f[3])
    return cts, dim


def l1_label(tally: dict, cts: dict):
    tot = sum(tally.values())
    best = []
    for t, d in cts.items():
        n = sum(d.values())
        keys = set(d) | set(tally)
        best.append((sum(abs(d.get(k, 0) / n - tally.get(k, 0) / tot) for k in keys), t))
    best.sort()
    return best


def witness_exclude(tally: dict, cts: dict) -> tuple[list, dict]:
    """Rivals proved IMPOSSIBLE by an observed cycle type absent from their support.

    If tau is observed at some prime p and tau is not in supp(C), then Frob_p is not in C, hence
    G is not contained in C -- deterministically, from one prime, no density and no margin. This is
    the right tool in the SUBGROUP direction, where a density is arbitrarily weak (dive #51): an
    index-2 subgroup of the target sits at L1 0.066, under any realistic sampling-noise floor, yet
    dies to a single witness prime. Densities remain necessary for SUPERGROUPS, which contain every
    cycle type the target has and so can never be witness-excluded.
    """
    obs = set(tally)
    survivors, killed = [], {}
    for t, d in cts.items():
        w = sorted(obs - set(d))
        if w:
            killed[t] = w[0]
        else:
            survivors.append(t)
    return survivors, killed


def gate(tally: dict, cts: dict) -> tuple[int, float, float, list, dict]:
    """Witness-exclude, then rank the survivors by density. Returns (best, L1, margin, ...)."""
    survivors, killed = witness_exclude(tally, cts)
    ranked = [(l1, t) for l1, t in l1_label(tally, cts) if t in set(survivors)]
    if not ranked:
        return 0, 1.0, 0.0, ranked, killed
    l1, best = ranked[0]
    margin = ranked[1][0] - l1 if len(ranked) > 1 else 1.0
    return best, l1, margin, ranked, killed


def resolution(cts: dict, t: int) -> list:
    """A priori, before any polynomial is built: how close is each rival, and can a witness kill it?

    witness mass = the target's density on cycle types ABSENT from the rival's support = the chance
    a single prime excludes that rival. Mass 0 (a supergroup / a Gassmann twin) => witness-proof, so
    the density must carry it. A gate whose noise floor exceeds the nearest witness-proof rival's L1
    is under-powered and should say so rather than silently refuse.
    """
    tgt = cts[t]
    tot = sum(tgt.values())
    rows = []
    for u, d in cts.items():
        if u == t:
            continue
        n = sum(d.values())
        keys = set(d) | set(tgt)
        l1 = sum(abs(d.get(k, 0) / n - tgt.get(k, 0) / tot) for k in keys)
        mass = sum(v for k, v in tgt.items() if k not in d) / tot
        rows.append((l1, mass, u))
    rows.sort()
    return rows


def open_rs(t: int) -> list:
    prog = json.load(open(ROOT / "data" / "processed" / "progress.json"))
    out = []
    for r in range(0, 25, 2):
        if (str(t), str(r)) not in baseline.valid_pairs():
            continue
        e = prog.get(f"{t},{r}")
        tc = e.get("teamCount") if isinstance(e, dict) else None
        if tc == 0 and not baseline.is_baseline(str(t), str(r)):
            out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--build", type=str, default=None, help="base label, e.g. 12T42")
    ap.add_argument("--resolution", type=int, default=None,
                    help="24Tt: report the library's rivals, their L1 and their witness mass")
    ap.add_argument("--top", type=int, default=None, help="top 12Tj for --resolution")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--ncand", type=int, default=3)
    ap.add_argument("--fpmax", type=int, default=FP_MAX)
    args = ap.parse_args()

    if args.resolution:
        cts, dim = library(args.top)
        print(f"library 12T{args.top}: {len(cts)} groups; target 24T{args.resolution} "
              f"(kdim {dim.get(args.resolution)})")
        for l1, mass, u in resolution(cts, args.resolution)[:8]:
            kill = f"~{1 / mass:.0f} primes" if mass > 0 else "NEVER (witness-proof)"
            print(f"  24T{u:<6d} kdim={str(dim.get(u)):>2s}  L1={l1:.4f}  "
                  f"witness mass={mass:.4f}  {kill}")
        return

    fl = lmfdb.fields(12, max_r2=0, class_number=1, per_group=8, limit=args.limit)
    bases = {}
    for coeffs, label, disc, _h in fl:
        bases.setdefault(label, []).append(list(coeffs))

    if args.screen:
        code = SCREEN + "\n" + "\n".join(
            f'SCREEN("{lab}", {cs});' for lab, css in bases.items() for cs in css) + "\nquit\n"
        for ln in gp_run(code).splitlines():
            if ln.startswith("SCREEN|"):
                _, lab, ram, odd, ns, ds = ln.split("|")
                if ds.strip() not in ("[]", ""):
                    print(f"{lab:9s} ram={ram:22s} odd-f={odd:16s} nsplit={ns:>3s}  d={ds}")
        return

    if args.build:
        lab = args.build
        cs = bases[lab][0]
        top = int(lab.split("T")[1])
        code = SCREEN + f'SCREEN("{lab}", {cs});\nquit\n'
        ds = []
        for ln in gp_run(code).splitlines():
            if ln.startswith("SCREEN|"):
                ds = json.loads(ln.split("|")[5].replace(" ", "") or "[]")
        if not ds:
            print(f"{lab}: no reachable d -- every twist is locally out of the norm group")
            return
        cts, dim = library(top)
        for d in ds:
            code = (BUILD + f"NCAND = {args.ncand};\nFPMAX = {args.fpmax};\n"
                    f"BUILD({top}, {d}, {cs});\nquit\n")
            tallies, alphas = {}, {}
            for ln in gp_run(code).splitlines():
                f = ln.strip().split("|")
                if f[0] == "FP":
                    tallies.setdefault(f[1], {})[f[2]] = int(f[3])
                elif f[0] == "CAND":
                    alphas[f[1]] = f[3]
            for cid, tally in tallies.items():
                t, l1, margin, ranked, killed = gate(tally, cts)
                gated = l1 < L1_THRESH and margin > MARGIN
                print(f"{lab} d={d} {cid}: 24T{t} kdim={dim.get(t)} L1={l1:.3f} "
                      f"margin={margin:.3f} ({len(killed)} rivals witness-killed, "
                      f"{len(ranked) - 1} left)  open_r={open_rs(t)}  "
                      f"{'GATED' if gated else '-'}")


if __name__ == "__main__":
    main()
