"""Pin d_N for EVERY quadratic character of a top, on an ARBITRARY base (not just an LMFDB one).

`mb2_chi_d.py` runs dive #51's Frobenius d-finder over bases pulled from LMFDB. Dive #59's base
factory builds bases that are NOT in LMFDB (LMFDB's degree-12 table is a Kluners-Malle sample, not
an enumeration -- it holds only 2 totally-real 12T36 fields and both are dead for the twist engine),
so the d-finder has to accept a base on the command line. Same mathematics, different input.

WHY THIS EXISTS (the trap it caught, 2026-07-14). The 12T36 build item assumed the sign character's
free d = core(disc K0) aims at 24T18009 "because the aim is a function of the top alone". The aim IS
a function of the top -- but the SIGN character of 12T36 aims at 24T18008, not 18009. 18009 is the
sibling of a DIFFERENT index-2 subgroup, so its d is not core(disc K0) and must be solved for.

METHOD (dive #51, unchanged): d_N is supported on the primes ramifying in K0 and is positive (K0
totally real => M totally real), so there are <= 2^omega - 1 candidates. Each prime p with a
DECISIVE cycle type (all H-classes of that type share one chi value) gives one equation
kronecker(d_N, p) = (-1)^chi(type), and Hom(H,F2) -> Q*/(Q*)^2 being a homomorphism cross-checks
and pins the rest.

REACHABILITY, per (base, d): the engine builds alpha on prod_{p | d} P_p times a completely-split
pair and needs core(N(alpha)) = d, so every p | d must have a prime of K0 above it with ODD residue
degree f.

Usage:
    gap -q -b -c 'TOPS:=[36];;' scripts/mb2_chi_table.g > /tmp/chitab36.txt
    .venv/bin/python scripts/mb2_chi_d_base.py --top 36 --chitab /tmp/chitab36.txt \
        --coeffs '[6264469, 1670201, ..., 1]'          # ASCENDING
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import mb2_chi_d as cd  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, required=True)
    ap.add_argument("--coeffs", type=str, required=True, help="ASCENDING degree-12 base coeffs")
    ap.add_argument("--chitab", type=str, default=str(cd.CHITAB))
    ap.add_argument("--pbound", type=int, default=4000)
    args = ap.parse_args()

    cd.CHITAB = Path(args.chitab)
    tab = cd.chi_table()
    if args.top not in tab:
        sys.exit(f"12T{args.top} absent from {args.chitab} "
                 f"(run mb2_chi_table.g with TOPS:=[{args.top}])")
    chis = tab[args.top]

    cs = json.loads(args.coeffs)
    out = cd.gp(f"PBOUND = {args.pbound};\n" + cd.FROB + f'FROB("b", {cs});\nquit\n')
    ram, oddf, cts, dK = [], {}, {}, None
    for ln in out.splitlines():
        f = ln.strip().split("|")
        if f[0] == "RAM":
            ram.append(int(f[2]))
            oddf[int(f[2])] = int(f[3]) == 1
        elif f[0] == "CT":
            cts[int(f[2])] = f[3]
        elif f[0] == "DONE":
            dK = int(f[2])
    if not ram:
        sys.exit(f"no ramified primes parsed from gp:\n{out}")

    cand = cd.squarefree_ds(sorted(ram), 2 in ram)
    print(f"12T{args.top} base disc = {dK}")
    print(f"  ramified: {sorted(ram)}  odd-f: {{{', '.join(f'{p}:{oddf[p]}' for p in sorted(ram))}}}")
    print(f"  core(disc) = {cd.core(abs(dK))}   d-candidates: {len(cand)}   "
          f"unramified primes sampled: {len(cts)}")

    surv, nq = {}, {}
    for i, e in chis.items():
        eqs = [(p, e["dec"][c]) for p, c in cts.items() if c in e["dec"]]
        nq[i] = len(eqs)
        surv[i] = [d for d in cand
                   if all(cd.kron(d, p) == (1 if ch == 0 else -1) for p, ch in eqs if d % p != 0)]
    dmap, bad = cd.resolve(chis, surv)
    for a, b, c, da, db, dc, prod in bad:
        print(f"  !! homomorphism CONTRADICTION chi{a}.chi{b}=chi{c}: {da}*{db} -> {prod} != {dc}")

    print(f"\n{'chi':<5}{'24Tt':<8}{'d_N':<14}{'#eqs':<6}{'#surv':<7}reachable (every p|d has odd-f)")
    for i in sorted(chis):
        d = dmap[i]
        reach = bool(d) and all(oddf.get(p, False) for p in ram if d % p == 0)
        print(f"{i:<5}{chis[i]['t']:<8}{str(d or '-'):<14}{nq[i]:<6}{len(surv[i]):<7}{reach}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
