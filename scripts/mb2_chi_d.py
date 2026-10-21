"""The chi-TABLE d-FINDER: recover d_N for a GENERAL index-2 subgroup N <= H, at ANY |H|.

Research dive #51 (continues dive #50, which got a free d for the SIGN character only).

THE PROBLEM.  general_c2_TWIST lands the dim-11 sibling G_chi = {(v;h) : Sum v = chi(h)} where chi
is the Galois character of Q(sqrt(N(alpha))) (dive #49).  To AIM at a specific open sibling we must
know, for its index-2 subgroup N = ker chi, the integer d_N with Q(sqrt d_N) = M^N -- a quadratic
subfield of the Galois CLOSURE M, not of K0, so PARI cannot just read it off nfsubfields(K0).

Dive #49's screen guessed d by testing kronecker(d, q) = 1 on COMPLETELY-SPLIT primes q.  That is
blind for large |H|: completely-split primes have density 1/|H|, so above |H| ~ 500 there are
essentially none below 30000 and the screen returns the empty set -- which dive #50 showed is an
ARTIFACT, not a refutation.  The open board lives exactly at those large tops.

THE FIX -- two classical facts, no split primes needed:
  (1) RAMIFICATION (Elsenhans-Kluners, arXiv:1907.13383: "the ramified primes of the subfield can be
      computed efficiently"; a prime ramifies in M iff it ramifies in K0, M being the compositum of
      the conjugates of K0).  So supp(d_N) subset rad(disc K0), and d_N > 0 (K0 totally real =>
      M totally real).  If 2 is unramified, d_N = 1 mod 4.  That is <= 2^omega - 1 candidates.
  (2) FROBENIUS / CHEBOTAREV.  For p unramified in K0 the residue degrees of the primes above p ARE
      the cycle type of Frob_p in the degree-12 action.  chi_N is a class function, so a cycle type
      PINS chi(Frob_p) whenever every H-class with that type shares one chi value (a DECISIVE type;
      tabulated by scripts/mb2_chi_table.g).  Each decisive prime gives one linear equation
          kronecker(d_N, p) = (-1)^chi(cycletype(p)),
      and a few dozen of them cut the candidate set down to the single true d_N.
  Both halves are cheap at ANY |H| -- decisive types have constant density, unlike the 1/|H| of a
  completely-split prime.  This is the FIRST HONEST census of which open twisted siblings are
  reachable and which are not.

REACHABILITY (the dive-#49 necessary condition, applied to the d we now know): the engine builds
alpha on a divisor prod_{p | d} P_p times a completely-split pair, and needs core(N(alpha)) = d, so
every p | d must have a prime of K0 above it with ODD residue degree f.  A d that fails this is a
real wall FOR THAT BASE (try another base of the same top).

Usage:
    gap -q -b -c 'TOPS:=[12,16,...];;' scripts/mb2_chi_table.g > /tmp/chitab_out.txt
    .venv/bin/python scripts/mb2_chi_d.py --bases-per-top 6
"""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from igp import baseline, lmfdb  # noqa: E402

OUT = ROOT / "data" / "processed" / "mb2twist"
CHITAB = Path("/tmp/chitab_out.txt")

# ramified primes, their odd-f status, and the cycle type of Frob_p for p < PBOUND
FROB = r"""
{
FROB(lab, c) =
  my(f = Pol(Vecrev(c)), K = nfinit(f), dK = K.disc, ram, s);
  ram = Vec(factor(abs(dK))[,1]);
  for(i = 1, #ram,
    my(p = ram[i], oddf = 0);
    if(#select(P -> P.f % 2 == 1, idealprimedec(K, p)) > 0, oddf = 1);
    print("RAM|", lab, "|", p, "|", oddf));
  forprime(p = 3, PBOUND,
    if(dK % p == 0, next);
    my(de = idealprimedec(K, p), fs = vecsort(apply(P -> P.f, de)), key = "");
    for(i = 1, #fs, key = concat(key, Str(fs[i])); if(i < #fs, key = concat(key, "-")));
    print("CT|", lab, "|", p, "|", key));
  print("DONE|", lab, "|", dK);
}
"""


def gp(code, timeout=1800):
    p = subprocess.run(["gp", "-q"], input=code, capture_output=True, text=True, timeout=timeout)
    return p.stdout


def kron(d, p):
    """Kronecker symbol (d|p) for odd prime p not dividing d."""
    a = d % p
    r = pow(a, (p - 1) // 2, p)
    return 1 if r == 1 else -1


def chi_table():
    """{top: {idx: {'t': 24Tt, 'dec': {cycletype: chi}}}} -- DECISIVE cycle types only.

    A cycle type is decisive for chi_N iff every H-class carrying it has the same chi value.
    Aggregated here (not in GAP) and checksummed: the class sizes of each chi must sum to |H|,
    which is what caught the mutable-key dictionary bug in the first version of mb2_chi_table.g.
    """
    order, raw, sib, vec = {}, {}, {}, {}
    for ln in CHITAB.read_text().splitlines():
        f = ln.strip().split("|")
        if f[0] == "TOP":
            order[int(f[1])] = int(f[2])
        elif f[0] == "SIB":
            sib[(int(f[1]), int(f[2]))] = int(f[3])
        elif f[0] == "CHIV":
            vec[(int(f[1]), int(f[2]))] = f[3]
        elif f[0] == "CLS":
            j, i, ct, chv, sz = int(f[1]), int(f[2]), f[3], int(f[4]), int(f[5])
            raw.setdefault((j, i), []).append((ct, chv, sz))
    tab = {}
    for (j, i), cls in raw.items():
        tot = sum(sz for _, _, sz in cls)
        if tot != order.get(j):
            print(f"WARN 12T{j} chi{i}: class sizes sum to {tot}, |H| = {order.get(j)} -- SKIPPED")
            continue
        vals = {}
        for ct, chv, _ in cls:
            vals.setdefault(ct, set()).add(chv)
        dec = {ct: v.pop() for ct, v in vals.items() if len(v) == 1}
        tab.setdefault(j, {})[i] = {"t": sib[(j, i)], "dec": dec, "ntypes": len(vals),
                                    "vec": vec.get((j, i), "")}
    return tab


def core(n):
    d, p = 1, 2
    while p * p <= n:
        e = 0
        while n % p == 0:
            n //= p
            e += 1
        if e % 2:
            d *= p
        p += 1
    return d * n


def resolve(chis, surv):
    """chi -> d is a HOMOMORPHISM Hom(H,F2) -> Q*/(Q*)^2: chi_a + chi_b = chi_c => d_a.d_b = d_c.

    Use it to (1) pin a chi whose Frobenius equations left several survivors, and (2) cross-check
    the ones that were already unique.  Returns {idx: d or None} plus a list of contradictions.
    """
    byvec = {chis[i]["vec"]: i for i in chis}
    d = {i: (surv[i][0] if len(surv[i]) == 1 else None) for i in chis}
    bad = []
    for _ in range(3):
        for a in chis:
            for b in chis:
                if a >= b or d[a] is None or d[b] is None:
                    continue
                va, vb = chis[a]["vec"], chis[b]["vec"]
                vc = "".join(str(int(x) ^ int(y)) for x, y in zip(va, vb))
                c = byvec.get(vc)
                if c is None:
                    continue
                prod = core(d[a] * d[b])
                if d[c] is None:
                    if prod in surv[c] or not surv[c]:
                        d[c] = prod
                elif d[c] != prod:
                    bad.append((a, b, c, d[a], d[b], d[c], prod))
    return d, bad


def open_board():
    prog = json.load(open(ROOT / "data" / "processed" / "progress.json"))
    held = set()
    for row in csv.DictReader(open(ROOT / "data" / "targets" / "realized.csv")):
        if row["t"]:
            held.add(int(row["t"]))
    vp = baseline.valid_pairs()

    def rs(t):
        out = []
        for r in range(0, 25, 2):
            if (str(t), str(r)) not in vp:
                continue
            e = prog.get(f"{t},{r}")
            tc = e.get("teamCount") if isinstance(e, dict) else None
            if tc == 0 and not baseline.is_baseline(str(t), str(r)):
                out.append(r)
        return out
    return rs, held


def squarefree_ds(ram, two_ram):
    ds = []
    for m in range(1, 1 << len(ram)):
        d = 1
        for i, p in enumerate(ram):
            if m >> i & 1:
                d *= p
        if not two_ram and d % 4 != 1:
            continue        # disc would be 4d => 2 ramifies in M => 2 ramifies in K0
        ds.append(d)
    return ds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bases-per-top", type=int, default=6)
    ap.add_argument("--pbound", type=int, default=2000)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    tab = chi_table()
    rs, held = open_board()

    # open dim-11 twisted siblings, indexed by (top, chi index)
    tgt = {}
    for j, idxs in tab.items():
        for i, e in idxs.items():
            t = e["t"]
            o = rs(t)
            if o and t not in held:
                tgt.setdefault(j, []).append((i, t, o))
    ngroups = len({t for v in tgt.values() for _, t, _ in v})
    npairs = sum(len(o) for v in tgt.values() for _, _, o in v)
    print(f"chi-table: {len(tab)} tops;  OPEN twisted siblings: {ngroups} groups / "
          f"{npairs} tc=0 pairs over {len(tgt)} tops")

    rows = []
    for j in sorted(tgt):
        try:
            fields = lmfdb.fields(12, galois_label=f"12T{j}", class_number=None, max_r2=0,
                                  limit=args.bases_per_top)
        except Exception as exc:                       # LMFDB mirror is an external boundary
            print(f"12T{j}: lmfdb error {exc}")
            continue
        for coeffs, _lab, fdisc, h in fields:
            cs = list(coeffs)
            code = (f"PBOUND = {args.pbound};\n" + FROB
                    + f'FROB("b", {cs});\nquit\n')
            try:
                out = gp(code)
            except Exception as exc:
                print(f"12T{j} {cs}: gp error {exc}")
                continue
            ram, oddf, cts = [], {}, {}
            for ln in out.splitlines():
                f = ln.strip().split("|")
                if f[0] == "RAM":
                    ram.append(int(f[2]))
                    oddf[int(f[2])] = int(f[3]) == 1
                elif f[0] == "CT":
                    cts[int(f[2])] = f[3]
            if not ram:
                continue
            cand = squarefree_ds(sorted(ram), 2 in ram)
            # solve EVERY chi of this top (not just the open ones) -- the non-open siblings are
            # what make the homomorphism law usable to pin the ambiguous ones
            surv, nq = {}, {}
            for i, e in tab[j].items():
                dec = e["dec"]
                eqs = [(p, dec[c]) for p, c in cts.items() if c in dec]
                nq[i] = len(eqs)
                surv[i] = [d for d in cand
                           if all(kron(d, p) == (1 if ch == 0 else -1)
                                  for p, ch in eqs if d % p != 0)]
            dmap, bad = resolve(tab[j], surv)
            for a, b, c, da, db, dc, prod in bad:
                print(f"  !! 12T{j} homomorphism CONTRADICTION chi{a}.chi{b}=chi{c}: "
                      f"{da}*{db} -> {prod} != {dc}")
            for i, t, o in tgt[j]:
                d = dmap[i]
                reach = bool(d) and all(oddf.get(p, False) for p in ram if d % p == 0)
                rows.append({"top": j, "chi": i, "t": t, "open_r": json.dumps(o),
                             "coeffs": json.dumps(cs), "h": h, "fdisc": fdisc,
                             "ram": json.dumps(sorted(ram)), "neqs": nq[i],
                             "ncand": len(cand), "nsurv": len(surv[i]),
                             "d": d or "", "reachable": int(reach),
                             "contradiction": int(bool(bad))})
            print(f"12T{j} h={h} ram={sorted(ram)} -> "
                  + " ".join(f"24T{t}:d={dmap[i]}{'*' if dmap[i] and all(oddf.get(p, False) for p in ram if dmap[i] % p == 0) else ''}"
                             for i, t, _ in tgt[j]))

    with open(OUT / "chi_d.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print("\n=== SUMMARY ===")
    tried = {r["t"] for r in rows}
    pinned = {r["t"] for r in rows if r["d"]}
    contra = {r["top"] for r in rows if r["contradiction"]}
    reach1 = [r for r in rows if r["reachable"] and r["h"] == 1]     # engine needs a principal ideal
    reachH = {r["t"] for r in rows if r["reachable"]} - {r["t"] for r in reach1}
    g1 = {r["t"] for r in reach1}
    print(f"open twisted siblings with a base tried: {len(tried)} / {ngroups} groups")
    print(f"d_N pinned (Frobenius + homomorphism law): {len(pinned)} groups"
          f"{'  [CONTRADICTIONS at tops ' + str(sorted(contra)) + ']' if contra else '  [no contradictions]'}")
    print(f"BUILD-READY (d pinned, every p|d has an odd-f prime, h=1): {len(g1)} groups")
    pr = sum(len(json.loads(r["open_r"])) for r in {r["t"]: r for r in reach1}.values())
    print(f"  -> {pr} tc=0 open pairs with a passing (base, d)")
    print(f"reachable but h>1 (engine needs a principal-ideal search): {len(reachH)} groups")
    print(f"NO passing (base, d) among the bases tried: {len(tried - g1 - reachH)} groups"
          "  [the honest negative census: d is pinned but some p|d has only even-f primes]")
    seen = set()
    for r in sorted(reach1, key=lambda x: x["t"]):
        if r["t"] in seen:
            continue
        seen.add(r["t"])
        print(f"  24T{r['t']:<6} r={json.loads(r['open_r'])}  base 12T{r['top']} h=1 "
              f"d={r['d']}  coeffs={r['coeffs']}")


if __name__ == "__main__":
    main()
