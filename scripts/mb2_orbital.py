"""The `(a,b)` ORBITAL pre-filter for the weight-2 split-prime twist engines (research dive #54).

The twist producers (mb2_twist_sign_producer.py, mb2_twist_evenf.py) build alpha on the divisor
`Id * Q_a * Q_b`, where `Q_a`, `Q_b` are two of the 12 primes above a completely-split `q`. Which
`(a,b)` you pick MOVES THE BLOCK KERNEL -- test 0069 and test 0072 both watched a pair land the
dim-10 sibling instead of the aimed dim-11 one, and paid for it with a wasted build plus a wasted
5,133-prime fingerprint (0072 built 3 to gate 2). Dive #54 closed that in closed form:

  valuation-at-q is H-equivariant, so the conjugates of alpha carry the vectors `sigma(1_{a,b})`
  =>  kdim >= dim <H . 1_{a,b}> , and that span depends ONLY on the H-ORBITAL of the pair {a,b}.
  <H . 1_{a,b}> is the GF(2) column space of the incidence matrix of the orbital graph, whose rank
  on n vertices with c components is n - c. Hence

      dim <H . 1_{a,b}>  =  12 - (#connected components of the orbital graph of {a,b})

So: to aim a kernel of dim k, enumerate only the pairs whose orbital graph has `12 - k` components
(k = 11 <=> connected graph).

IT IS A LOWER BOUND, AND THE BOUND IS SOMETIMES STRICT -- test 0073's A/B measured this. Every
predicted-11 pair landed EXACTLY kdim 11 (6/6, across test 0072 and 0073), but pair (1,5) on the
12T245 base, predicted 8, landed a kdim-10 group. That is expected: the bound accounts only for the
q-part of the divisor, and the other primes of `Id` (the odd-f primes over `d`, plus any even-f
repair prime) can contribute further valuation vectors that inflate the kernel. Consequence: the
filter is a BUILD-TAX screen, not a proof -- it can in principle skip a pair that would have
inflated INTO the target dim (a false negative), and it does not by itself certify an accepted
pair. The Frobenius-density gate downstream stays load-bearing.

Computed in PARI alone -- one `nffactor` of f over K0 per (base, q), then O(1) per pair. No GAP, no
bnfinit, no class group. The factor index k of `f = (x - theta) * prod g_k` is a base-independent
suborbit-type label (factor degrees = suborbit lengths); `dec[i]` is matched to its root `c_i` of
`f mod q` by `idealval(K, theta - c, dec[i]) > 0` -- NOT by `nfmodpr`, which returns a t_FFELT that
`lift(lift(.))` does not reduce to a t_INT, after which `polrootsmod` throws `Rg_to_Fl`.

Because PARI's `idealprimedec` ordering is an implementation detail, ORBDIM returns its own root
vector and the caller maps its dec indices through `ORBPERM` -- the pair label is the ROOT mod q,
which is intrinsic, not the index.

Self-test (test 0072's exact ground truth, base 12T245 / d=5 / q=15569):
    .venv/bin/python scripts/mb2_orbital.py --selftest
Ad-hoc:
    .venv/bin/python scripts/mb2_orbital.py --top 245 --q 15569 --kdim 11
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# REACHABILITY GUARD (dive #54's free corollary). The weight-2 split radical reaches EXACTLY the
# orbital modules of its top -- at most rank(H) - 1 of them, one per orbital. So a target whose
# block kernel is not SET-EQUAL to an orbital module is unreachable at weight 2, no matter the
# (a,b), the unit twist or the prime. Dim-match is necessary, NOT sufficient: these three have a
# dim-6 kernel and their top has a dim-6 orbital, but the modules DIFFER (GAP module-equality test,
# dive #54). They need the multi-generator w-engine (scripts/mb2_sweep6.py); do not spend weight-2
# builds on them.
WEIGHT2_UNREACHABLE = {14616: 183, 9641: 74, 9642: 74}

GP_ORBITAL = r"""
{
SUBORB(fac, rts, q, k, base) =
  my(cf = Vec(fac[k]), red, P, rs);
  red = vector(#cf, j, Mod(subst(lift(cf[j]), 'y, rts[base]), q));
  P = Pol(red, 'x);
  rs = Set(lift(polrootsmod(P, q)));
  select(i -> setsearch(rs, rts[i]) > 0, vector(12, i, i));
}
{
NCOMPS(M) =
  my(cp = vector(12, i, i), chg = 1);
  while(chg, chg = 0;
    for(i = 1, 12, for(j = 1, 12,
      if(M[i,j] && cp[i] != cp[j],
        my(m = vecmin([cp[i], cp[j]])); cp[i] = m; cp[j] = m; chg = 1))));
  #Set(Vec(cp));
}
{
ORBDIM(c, q) =
  my(fy = Pol(Vecrev(c), 'y), fx = Pol(Vecrev(c), 'x), K = nfinit(fy), dec, rr0, th, rts,
     g, fac, nf, COL, prt, DIM);
  dec = idealprimedec(K, q);
  if(#dec != 12, return(0));
  rr0 = Vec(lift(polrootsmod(fx, q)));
  th = Mod('y, fy);
  rts = vector(12, i, select(cc -> idealval(K, th - cc, dec[i]) > 0, rr0)[1]);
  g = nffactor(K, fx); fac = g[,1]; nf = #fac;
  COL = matrix(12, 12);
  for(i = 1, 12, for(k = 1, nf,
    my(S = SUBORB(fac, rts, q, k, i)); for(t = 1, #S, COL[i, S[t]] = k)));
  prt = vector(nf, k, if(k == 1, 1,
          my(b = SUBORB(fac, rts, q, k, 1)[1]);
          select(j -> setsearch(Set(SUBORB(fac, rts, q, j, b)), 1) > 0, vector(nf, j, j))[1]));
  DIM = vector(nf);
  for(k = 2, nf,
    my(M = matrix(12, 12, i, j, if(i != j && (COL[i,j] == k || COL[i,j] == prt[k]), 1, 0)));
    DIM[k] = 12 - NCOMPS(M));
  [rts, matrix(12, 12, i, j, if(i == j, 0, DIM[COL[i,j]])),
   apply(x -> poldegree(x), Vec(fac)), prt];
}
{
ORBPERM(K, f, q, dec, rts) =
  my(rr = Vec(lift(polrootsmod(f, q))), th = Mod(variable(f), f));
  vector(12, a,
    my(cc = select(z -> idealval(K, th - z, dec[a]) > 0, rr)[1]);
    select(i -> rts[i] == cc, vector(12, i, i))[1]);
}
"""

PRELUDE = "default(parisizemax, 8*10^9);\n"


def orbital_dims(coeffs: list, q: int, timeout: float = 900.0) -> dict:
    """Predicted block-kernel dim for every prime pair (a,b) above the completely-split q.

    Returns {"dims": {(a,b): dim}, "degs": suborbit lengths, "pairing": the k -> k* involution}.
    """
    cs = ",".join(str(c) for c in coeffs)
    # A gp SCRIPT statement ends at the newline, so the driver has to sit inside a brace block.
    code = (PRELUDE + GP_ORBITAL + "{\n"
            f"my(r = ORBDIM([{cs}], {q}));\n"
            "if(r == 0, print(\"NOTSPLIT\"),\n"
            "  print(\"DEGS|\", r[3]); print(\"PRT|\", r[4]);\n"
            "  for(a = 1, 11, for(b = a + 1, 12,\n"
            "    print(\"PAIR|\", a, \"|\", b, \"|\", r[2][a,b]))));\n"
            "}\nquit\n")
    proc = subprocess.run(["gp", "-q"], input=code, capture_output=True, text=True, timeout=timeout)
    out = proc.stdout
    if "NOTSPLIT" in out:
        raise ValueError(f"q = {q} is not completely split in the base")
    dims, degs, prt = {}, [], []
    for ln in out.splitlines():
        f = ln.strip().split("|")
        if f[0] == "PAIR":
            dims[(int(f[1]), int(f[2]))] = int(f[3])
        elif f[0] == "DEGS":
            degs = [int(x) for x in f[1].strip("[]").split(",")]
        elif f[0] == "PRT":
            prt = [int(x) for x in f[1].strip("[]").split(",")]
    if not dims:
        raise RuntimeError(f"ORBDIM produced no pairs; gp said: {out[:300]} {proc.stderr[:300]}")
    return {"dims": dims, "degs": degs, "pairing": prt}


def good_pairs(coeffs: list, q: int, kdim: int, timeout: float = 900.0) -> list:
    d = orbital_dims(coeffs, q, timeout=timeout)
    return sorted(ab for ab, k in d["dims"].items() if k == kdim)


# test 0072 / dive #54 ground truth: base 12T245 (the 24T23297 base), d = 5, q = 15569.
SELFTEST_COEFFS = [30256, 181536, 408456, 397688, 104715, -72684, -35038, 3912, 2934, -62, -93,
                   0, 1]
SELFTEST_Q = 15569
SELFTEST_EXPECT = {(1, 2): 10, (1, 3): 11, (1, 4): 11}


def selftest() -> int:
    d = orbital_dims(SELFTEST_COEFFS, SELFTEST_Q)
    ok = True
    print(f"base 12T245, q = {SELFTEST_Q}: suborbit degrees {d['degs']}, pairing {d['pairing']}")
    print(f"orbital dims available: {sorted(set(d['dims'].values()))}  (GAP says 8, 10, 11)")
    for ab, want in SELFTEST_EXPECT.items():
        got = d["dims"][ab]
        verdict = "PASS" if got == want else f"FAIL (want {want})"
        if got != want:
            ok = False
        landed = {(1, 2): "24T22599 off-target", (1, 3): "24T23297", (1, 4): "24T23297"}[ab]
        print(f"  (a,b) = {ab}: predicted dim {got} -- test 0072 landed {landed} -- {verdict}")
    n11 = sum(1 for k in d["dims"].values() if k == 11)
    print(f"dim-11 pairs: {n11} of {len(d['dims'])} -- the pre-filter's build-tax saving")
    if sorted(set(d["dims"].values())) != [8, 10, 11]:
        print("FAIL: orbital dim set does not match GAP's (8, 10, 11)")
        ok = False
    print("SELFTEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="reproduce test 0072's ground truth")
    ap.add_argument("--top", type=int, default=None, help="12Tj of a base in the twist SHORTLIST")
    ap.add_argument("--q", type=int, default=None, help="a completely-split prime of that base")
    ap.add_argument("--kdim", type=int, default=11, help="target block-kernel dim")
    args = ap.parse_args()

    if args.selftest or args.top is None:
        sys.exit(selftest())

    sys.path.insert(0, str(ROOT / "scripts"))
    from mb2_twist_sign_producer import SHORTLIST
    cs = next(c for _, top, _, c, _ in SHORTLIST if top == args.top)
    d = orbital_dims(cs, args.q)
    keep = sorted(ab for ab, k in d["dims"].items() if k == args.kdim)
    print(f"12T{args.top}, q={args.q}: suborbit degrees {d['degs']}, pairing {d['pairing']}")
    print(f"dims {sorted(set(d['dims'].values()))}; {len(keep)} of {len(d['dims'])} pairs at "
          f"kdim {args.kdim}")
    print(f"good pairs: {keep[:20]}")


if __name__ == "__main__":
    main()
