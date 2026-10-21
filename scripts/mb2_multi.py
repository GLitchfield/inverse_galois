"""MINBLK=2 general_c2_multi: the TWO-PRIME radical (research dive #48).

Dive #46's validated column-space law says a single-radical `general_c2` over a completely-split
prime q realizes the block kernel <H . 1_w>, a CYCLIC F2[H]-submodule of F2^12 -- so targets whose
kernel needs 2 module generators (mu(K)=2) are provably out of reach. Dive #48's derivation: let
alpha's divisor be supported on TWO completely-split primes q1, q2,

    alpha = gen( prod_{j in w1} P_j^(q1) . prod_{j in w2} P_j^(q2) ),

still ONE radical, so K0(sqrt(alpha)) is still degree 24 -- only the ramified primes change. The
realized kernel becomes <H . 1_w1> + <H . 1_w2>, which reaches the mu=2 targets. The residual-unit
relation count is 12 - dim K regardless of the number of primes, so the dim-11 / one-relation
targets are the cheapest on the board (~4.6% end-to-end yield per random candidate vs ~0.05% for
the 9641/9642 sweep of test 0066).

WHAT THIS BUILD ESTABLISHED (test 0067) -- the law holds, but it does NOT reach dive #48's targets:

  1. CONFIRMED: two split primes DO reach dim-11 (mu=2) kernels. 194 of 288 fingerprinted
     candidates land a dim-11 kernel -- provably impossible for a single radical. The column-space
     law's kernel half is real.
  2. REFUTED (the targeting premise): the dim-11 kernel does NOT determine the group. The six
     siblings 24T22543..22548 share that one kernel and differ by a complement twist -- a cocycle
     in H^1(H, F2^12/K) = Hom(H, F2), i.e. a quadratic character chi of H. Dive #48 censused
     KERNELS (mu(K)) and never modelled the twist, so it listed 22544/22548 as reachable.
     For a radical whose divisor is supported on completely-split primes, N(alpha) = +-q1^|w1| .
     q2^|w2| times a unit norm (+-1), so mod squares N(alpha) is +-1 whenever |w1|,|w2| are even --
     chi is FORCED TRIVIAL, and the construction always lands the SPLIT complement, 24T22545.
     Empirically: 194/194 dim-11 landings were 22545, across 288 DISTINCT square classes (every
     unit twist), i.e. the twist is not a dial. Odd |w| makes N(alpha) = +-q1 mod squares, which is
     no quadratic subfield of the closure of K0 (q1 is unramified there) -- so chi cannot exist and
     the group escapes the family entirely: 0 of those candidates even pass the allowed-cycle-type
     screen. Both halves of the norm argument confirmed.
  => 22543/22544/22547/22548 are unreachable by ANY split-prime radical, single- or multi-prime,
     under any unit twist. Reaching them needs a divisor supported on a prime that ramifies in a
     real quadratic subfield of the closure of K0 (pushed to research_agenda).

So this script gates on what the engine DEMONSTRABLY lands, minus what we already hold (see
`gate_set`). Corroboration that the fingerprint is right: its landings (22545, 21610, 21612, 21613,
20576, 23274) are exactly groups our gen12 harvest already realized -- and 22545's teamCount=1 is
US, not a rival.

Label library (scripts/mb2_multi_gdist.g): every group this construction can land in is a subgroup
of C2 wr H with base-intersection an H-submodule K of F2^12 AND a complement twist, so the library
enumerates submodules x complement classes. The six dim-11 siblings' pairwise cycle-type L1
distances are >= 0.48, so an L1 < 0.35 gate identifies the SPECIFIC group (unlike the 9641/9642
Gassmann pair of test 0066, which no local invariant separates).

Cheap exact fingerprint (as test 0066): for p unramified in K0 with p not in {q1,q2}, alpha is a
p-unit, so the degree-24 cycle type at p is read off the base decomposition alone -- each prime
P|p of residue degree f contributes (f,f) if alpha is a square mod P, else (2f). No rnfequation
needed to label a candidate; that runs only on density-gated survivors.

Usage:
    .venv/bin/python scripts/mb2_multi.py --pairs 200                    # dry run
    .venv/bin/python scripts/mb2_multi.py --pairs 200 --pilot 3 --enqueue
"""
import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from igp import gp  # noqa: E402

# 12T210, totally real, h=1 (LMFDB; the exact gen12_totpos input) -- ascending coefficients.
K0 = [-16, 124, 159, -1913, 1181, 1901, -1050, -610, 304, 70, -33, -2, 1]
TOP = 210
OUT = ROOT / "data" / "processed" / "mb2multi"
RAW = OUT / "raw210.txt"          # gap -q -b -c 'TOP:=210;' scripts/mb2_multi_gdist.g > RAW
LIB = OUT / "lib210.json"         # parsed from RAW by _build_lib()
L1_THRESH = 0.35


def held_ts() -> set:
    """Groups we already have a realized row for (tier: a fresh group is worth more)."""
    import csv
    return {int(str(row["t"]).replace("24T", ""))
            for row in csv.DictReader(open(ROOT / "data" / "targets" / "realized.csv"))
            if str(row.get("t", "")).replace("24T", "").isdigit()}


def open_rs(t: int) -> list:
    """r with (t,r) a sole-1.0 target: achievable, non-baseline, nobody credited (teamCount==0)."""
    from igp import baseline
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


def gate_set(lib: dict) -> dict:
    """The engine's payable targets: library groups we hold ZERO rows for, with an open r.

    NOT the dive-#48 dim-11 shortlist. That shortlist (22543/22544/22547/22548) is provably
    unreachable here -- see the module docstring -- so gating on it would enqueue nothing. We
    gate instead on what this construction demonstrably lands, minus what we already hold."""
    held = held_ts()
    return {t: open_rs(t) for t in lib if t not in held and open_rs(t)}


def _build_lib():
    """Parse the GAP dump (SUB|t|dim|masks|order and CT|t|cycletype|classsize) into lib210.json."""
    dist, dims = {}, {}
    for ln in open(RAW):
        p = ln.strip().split("|")
        if p[0] == "SUB":
            dims[int(p[1])] = int(p[2])
        elif p[0] == "CT":
            d = dist.setdefault(int(p[1]), {})
            d[p[2]] = d.get(p[2], 0) + int(p[3])
    LIB.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"dims": dims, "dist": {str(t): d for t, d in dist.items()}}, open(LIB, "w"))


def _lib():
    if not LIB.exists():
        _build_lib()
    raw = json.load(open(LIB))
    dist = {int(t): {tuple(int(x) for x in k.split(",")): v for k, v in d.items()}
            for t, d in raw["dist"].items()}
    return ({t: {k: v / sum(d.values()) for k, v in d.items()} for t, d in dist.items()},
            {int(t): d for t, d in raw["dims"].items()})


def pair_list(npairs: int, weights=((4, 6), (6, 6), (6, 8))):
    """Deterministic blind (w1, w2) sample. The census says ~9.3% of pairs generate the dim-11
    kernel and the mode weights are 4/6/8; the idealprimedec labelling is non-canonical, so we
    SWEEP rather than align (aligning is what killed tests 0038/0051/0052)."""
    pairs = []
    for a, b in weights:
        s1 = list(itertools.combinations(range(1, 13), a))
        s2 = list(itertools.combinations(range(1, 13), b))
        n = npairs // len(weights)
        for i in range(n):
            pairs.append((list(s1[(i * 7) % len(s1)]), list(s2[(i * 13 + 5) % len(s2)])))
    return pairs


def sweep_gp(pairs, ntwist: int, gate: dict, qmax: int = 60000, dens_hi: int = 3000,
             timeout: float = 10800.0):
    """One amortized bnfinit; for each (w1,w2) form the two-prime product ideal and fingerprint
    the radical under `ntwist` unit twists.

    The twist sweep is NOT optional. This base has h = h+ = 1, so every totally positive unit is a
    square: the totally-positive alpha (the free-r=24 route of test 0062/0066) is UNIQUE mod
    squares, which pins the field -- and empirically it always lands the SPLIT complement 24T22545
    (rival-claimed, tc=1). The six dim-11 siblings 22543..22548 share one kernel and differ only by
    a cocycle twist in H^1(H, F2^12/K), which is visible only in alpha's square class. So reaching
    the OPEN siblings requires a non-square unit twist -- which also moves the signature r off 24
    (fine: these targets are open at many r, gated per-candidate below)."""
    lib, dims = _lib()
    allowed = sorted({k for t in gate for k in lib[t]})
    al_lit = str([list(c) for c in allowed]).replace(" ", "")
    pl_lit = str([[w1, w2] for w1, w2 in pairs]).replace(" ", "")
    cs = ",".join(str(c) for c in K0[::-1])
    L = [
        "default(parisizemax, 12*10^9);",
        f"AL=Map(); ALLOWED={al_lit}; for(i=1,#ALLOWED, mapput(AL, ALLOWED[i], 1));",
        f"PAIRS={pl_lit}; NT={ntwist};",
        f"K0=Pol([{cs}]); bnf=bnfinit(K0,1); fu=bnf.fu;",
        "print(\"H|\", bnf.no, \"|\", bnf.sign);",
        f"QS=List(); forprime(q=5, {qmax}, if(#QS>=2, break()); "
        "if(#idealprimedec(bnf,q)==12, listput(QS,q)));",
        "q1=QS[1]; q2=QS[2]; print(\"QS|\", q1, \",\", q2);",
        "pr1=idealprimedec(bnf,q1); pr2=idealprimedec(bnf,q2);",
        "twist(g,x) = my(a=g); for(k=1,11, if(bitand(x,2^(k-1)), a=a*nfbasistoalg(bnf,fu[k]))); "
        "if(bitand(x,2^11), a=-a); a;",
        "PLIST=List(); "
        f"forprime(p=3,{dens_hi}, if(p!=q1 && p!=q2 && Mod(bnf.disc,p)!=0, listput(PLIST,p)));",
        "PD=vector(#PLIST,i,idealprimedec(bnf,PLIST[i]));",
        "ctype(al) = my(tally=Map(), n=0); for(i=1,#PLIST, my(P=PD[i], ct=List(), bad=0); "
        "for(j=1,#P, my(pf=nfmodpr(bnf,al,P[j]), f=P[j].f); if(pf==0, bad=1; break()); "
        "if(issquare(pf), listput(ct,f); listput(ct,f), listput(ct,2*f))); "
        "if(!bad, my(key=vecsort(Vec(ct))); if(!mapisdefined(AL,key), return(0)); "
        "mapput(tally,key,if(mapisdefined(tally,key),mapget(tally,key),0)+1); n++)); [tally,n];",
        "for(k=1,#PAIRS, my(w1=PAIRS[k][1], w2=PAIRS[k][2], Jd=pr1[w1[1]]); "
        "for(j=2,#w1, Jd=idealmul(bnf,Jd,pr1[w1[j]])); "
        "for(j=1,#w2, Jd=idealmul(bnf,Jd,pr2[w2[j]])); "
        "my(pd=bnfisprincipal(bnf,Jd), g=nfbasistoalg(bnf,pd[2])); "
        "for(ti=0, NT-1, my(x=(ti*1235+7)%4096, al=twist(g,x), sv=nfeltsign(bnf,al), "
        "rr=24-2*sum(i=1,12,(1-sv[i])/2), res=ctype(al)); "
        "if(type(res)==\"t_INT\", next()); "
        "print(\"HIT|\", k, \"|\", x, \"|\", rr, \"|\", res[2], \"|\", lift(al), "
        "\"|\", Mat(res[1]))));",
        "print(\"DONE\");",
    ]
    out = subprocess.run(["gp", "-q"], input="\n".join(L), capture_output=True, text=True,
                         timeout=timeout).stdout
    hits, qs, meta = [], [], {}
    for ln in out.splitlines():
        if ln.startswith("H|"):
            meta["bnf"] = ln[2:]
        if ln.startswith("QS|"):
            qs = [int(x) for x in ln[3:].split(",")]
        if not ln.startswith("HIT|"):
            continue
        _, k, x, r, n, alpha, tally = ln.split("|")
        i = int(k) - 1
        hits.append({"w1": pairs[i][0], "w2": pairs[i][1], "twist": int(x), "r": int(r),
                     "n": int(n), "alpha": alpha.strip(),
                     "tally": _parse_tally(tally.strip())})
    if "DONE" not in out:
        print("WARNING: gp sweep did not reach DONE", file=sys.stderr)
    return qs, hits, meta


def _parse_tally(mat: str) -> dict:
    tally = {}
    for row in mat.strip()[1:-1].split(";"):
        row = row.strip()
        if not row:
            continue
        key, cnt = row.rsplit(",", 1)
        tally[tuple(int(x) for x in key.strip().strip("[]").split(","))] = int(cnt)
    return tally


def l1_label(tally: dict, lib: dict):
    n = sum(tally.values())
    obs = {k: v / n for k, v in tally.items()}
    scored = sorted((sum(abs(obs.get(k, 0) - exp.get(k, 0)) for k in set(exp) | set(obs)), t)
                    for t, exp in lib.items())
    return scored[0][1], scored[0][0]


def build_poly(alpha: str, timeout: float = 900.0):
    cs = ",".join(str(c) for c in K0[::-1])
    body = (f"f=Pol([{cs}],y); al=subst({alpha}, x, y);\n"
            "r=rnfequation(f, x^2 - al);\n"
            "print(if(poldegree(r)<24, \"DEGENERATE\", Vec(polredbest(r))));")
    out = subprocess.run(["gp", "-q"], input="default(parisizemax,8*10^9);\n" + body,
                         capture_output=True, text=True, timeout=timeout).stdout
    if "DEGENERATE" in out or "[" not in out:
        return []
    return [int(x) for x in out.strip().strip("[]").split(",")][::-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=180, help="number of blind (w1,w2) pairs to sweep")
    ap.add_argument("--twists", type=int, default=64, help="unit twists per pair (square classes)")
    ap.add_argument("--pilot", type=int, default=3, help="max candidates to build+enqueue")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    lib, dims = _lib()
    gate = gate_set(lib)
    print("gate (library groups we hold ZERO rows for, with an open r): "
          + ", ".join(f"24T{t}(dim{dims.get(t)}) r={rs}" for t, rs in sorted(gate.items())))
    pairs = pair_list(args.pairs)
    qs, hits, meta = sweep_gp(pairs, args.twists, gate)
    print(f"base 12T{TOP}: bnf(h,sign)={meta.get('bnf')}  split primes q1,q2 = {qs}")
    print(f"swept {len(pairs)} pairs x {args.twists} twists; cycle-type-consistent: {len(hits)}")

    seen, gated, tally_t = set(), [], {}
    for h in hits:
        if h["alpha"] in seen:
            continue
        seen.add(h["alpha"])
        t, l1 = l1_label(h["tally"], lib)
        h["best_t"], h["l1"], h["dim"] = t, round(l1, 4), dims.get(t)
        if l1 < L1_THRESH:
            tally_t[t] = tally_t.get(t, 0) + 1
        if l1 < L1_THRESH and h["r"] in gate.get(t, []):
            gated.append(h)
    print(f"distinct alphas: {len(seen)}")
    print("L1-confident landings by group: "
          + ", ".join(f"24T{t}(dim{dims.get(t)}):{n}" for t, n in sorted(tally_t.items())))
    print(f"gated onto an unheld group at an OPEN r: {len(gated)}")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump([{k: v for k, v in h.items() if k != "tally"} for h in hits],
              open(OUT / "hits.json", "w"), indent=1)

    gated.sort(key=lambda h: h["l1"])
    winners = []
    for h in gated:
        if len(winners) >= args.pilot:
            break
        c = build_poly(h["alpha"])
        if not c or len(c) != 25:
            print(f"  BUILD-FAIL w1={h['w1']} w2={h['w2']}")
            continue
        rr = gp.real_roots(c)
        if rr != h["r"]:
            print(f"  R-MISMATCH want {h['r']} got {rr}")
            continue
        sd = gp.scoreable_disc(c)
        if sd is None:
            print(f"  BLANK-RISK disc w1={h['w1']} w2={h['w2']} r={rr}")
            continue
        wtag = "".join(str(x) for x in h["w1"]) + "-" + "".join(str(x) for x in h["w2"])
        winners.append({"t": h["best_t"], "r": rr, "coeffs": c, "l1": h["l1"],
                        "src": f"q{qs[0]}-{qs[1]}:w{wtag}:x{h['twist']}", "disc": str(sd)})
        print(f"  WIN 24T{h['best_t']} r={rr} L1={h['l1']} disc={sd}")

    print(f"\nmb2_multi: {len(winners)} locally-gated candidates")
    json.dump(winners, open(OUT / "winners.json", "w"), indent=1)

    if args.enqueue and winners:
        from igp import searchstore as store
        store.init()
        added = 0
        for w in winners:
            tag = f"lit:mb2multinew:{w['t']}.{w['r']}:{w['src']}"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": w["coeffs"]}, target=tag):
                added += 1
        store.set_priority_prefix("lit:mb2multinew", 130.0)
        print(f"enqueued {added} (tier new; none of 22543/22544/22547/22548 held). "
              "SAIR's Magma label is the arbiter of the two-prime column-space law.")


if __name__ == "__main__":
    main()
