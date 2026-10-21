"""MINBLK=2 9641/9642: alignment-free size-6 w-sweep over the 12T74 base (dive #46 recipe).

Targets: (24T9641, r in {16,24}) and (24T9642, r in {16,24}) -- all teamCount=0, non-baseline
(re-verified against data/processed/progress.json at build time), and we hold ZERO rows for either
group. Base K0 = [16,0,-512,0,992,0,-664,0,192,0,-24,0,1] (12T74 = S5 on 12 points, totally real,
h=1, Cl+ = [2,2] so delta=2).

Construction (auto_log dive #46): K = K0(sqrt(alpha)), alpha a generator of the product of a size-6
subset w of the 12 primes above a completely-split q, twisted by a unit to fix the signature. GAP
proved exactly 30 of the C(12,6)=924 size-6 subsets have clean Kummer module EXACTLY the 24T9641/9642
dim-6 block kernel, and BOTH the count 30 and the size |w|=6 are labeling-INVARIANT -- so a blind
size-6 sweep contains all 30 regardless of the (non-canonical) idealprimedec ordering. Do not align;
sweep.

Cheap exact fingerprint (the reason a 924 x nq sweep is affordable): for an odd prime p unramified in
K0 and p != q, alpha is a p-unit, so the degree-24 cycle type at p is read off the base decomposition
alone -- each prime P|p of residue degree f contributes (f,f) if alpha is a square mod P, else (2f).
No rnfequation / polredbest needed to label a candidate; those run only on survivors.

Gate:
  1. every observed cycle type lies in the 24T9641 class set (early abort otherwise)
  2. L1 density distance < 0.35 vs the target distribution over ~550 primes, and the best match among
     the 7 mb2ns targets is 9641/9642
  3. deg-24 irreducible, polsturm r == the target r, gp.scoreable_disc non-blank
NOTE: 24T9641 and 24T9642 are a GASSMANN PAIR (identical cycle-type distributions, L1 = 0.0), so the
local fingerprint CANNOT separate them -- it can only certify "order-7680 with this permutation
character". Both are open at both r, so either label scores; SAIR's Magma label is the arbiter of
which. Other dim-6 submodules (214 of 924 w have SOME dim-6 module) may share the character too, so
this is a PILOT: enqueue a few, wait for official labels, scale only on a match.

Usage:
    .venv/bin/python scripts/mb2_sweep6.py --primes 2                 # dry run
    .venv/bin/python scripts/mb2_sweep6.py --primes 2 --pilot 5 --enqueue
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from igp import gp  # noqa: E402

K0 = [16, 0, -512, 0, 992, 0, -664, 0, 192, 0, -24, 0, 1]  # ascending
GDIST = ROOT / "data" / "processed" / "mb2ns" / "gdist.json"
TARGET_TS = (9641, 9642)
L1_THRESH = 0.35
OUT = ROOT / "data" / "processed" / "mb2sweep6"


def _gdist():
    raw = json.load(open(GDIST))
    return {int(t): {tuple(int(x) for x in k.split(",")): v / raw[t]["order"]
                     for k, v in raw[t]["dist"].items()} for t in raw}


def sweep_gp(nprimes: int, dens_hi: int = 4000, timeout: float = 3600.0):
    """Run the whole (q, w, twist) sweep inside one amortized bnfinit. Returns hit dicts."""
    gd = _gdist()
    allowed = sorted(gd[9641])
    al_lit = str([list(c) for c in allowed]).replace(" ", "")
    cs = ",".join(str(c) for c in K0[::-1])
    L = [
        "default(parisizemax, 12*10^9);",
        f"AL=Map(); ALLOWED={al_lit}; for(i=1,#ALLOWED, mapput(AL, ALLOWED[i], 1));",
        f"K0=Pol([{cs}]); bnf=bnfinit(K0,1); fu=bnf.fu;",
        "SU=bnfsignunit(bnf); MF=Mat(concat(apply(x->(1-x)/2,SU), matrix(12,1,i,j,1)));",
        f"QS=List(); forprime(q=5, 200000, if(#QS>={nprimes}, break()); "
        "if(#idealprimedec(bnf,q)==12, listput(QS,q)));",
        "print(\"QS|\", Vec(QS));",
        "twist(g,x) = my(a=g); for(k=1,11, if(lift(x[k]), a=a*nfbasistoalg(bnf,fu[k]))); "
        "if(lift(x[12]), a=-a); a;",
        "W4=List(); forvec(v=vector(4,i,[1,12]), my(t=vector(12,i,0)); for(j=1,4, t[v[j]]=1); "
        "listput(W4,t~), 2);",
        "subs=List(); forvec(v=vector(6,i,[1,12]), listput(subs,v), 2);",
        "ctype(al) = my(tally=Map(), n=0); for(i=1,#PLIST, my(P=PD[i], ct=List(), bad=0); "
        "for(j=1,#P, my(pf=nfmodpr(bnf,al,P[j]), f=P[j].f); if(pf==0, bad=1; break()); "
        "if(issquare(pf), listput(ct,f); listput(ct,f), listput(ct,2*f))); "
        "if(!bad, my(key=vecsort(Vec(ct))); if(!mapisdefined(AL,key), return(0)); "
        "mapput(tally,key,if(mapisdefined(tally,key),mapget(tally,key),0)+1); n++)); [tally,n];",
        "for(qi=1,#QS, q=QS[qi]; pr=idealprimedec(bnf,q); PLIST=List(); "
        f"forprime(p=3,{dens_hi}, if(p!=q && Mod(bnf.disc,p)!=0, listput(PLIST,p))); "
        "PD=vector(#PLIST,i,idealprimedec(bnf,PLIST[i])); "
        "for(k=1,#subs, my(v=subs[k], Jd=pr[v[1]]); for(j=2,6, Jd=idealmul(bnf,Jd,pr[v[j]])); "
        "my(pd=bnfisprincipal(bnf,Jd), g=nfbasistoalg(bnf,pd[2]), "
        "s=apply(x->(1-x)/2, nfeltsign(bnf,g))~, sol24=matsolvemod(MF,2,s,1), targets=List(), "
        "cnt16=0); "
        "if(type(sol24)!=\"t_INT\", my(x0=sol24[1], KB=sol24[2], nk=matsize(KB)[2]); "
        "for(b=0, min(3,2^nk-1), my(x=x0); for(c=1,nk, if(bitand(b,2^(c-1)), x=x+KB[,c])); "
        "listput(targets,[24,lift(Mod(x,2))]))); "
        "for(w=1,#W4, if(cnt16>=3, break()); my(tt=W4[w], sol=matsolvemod(MF,2,lift(Mod(s+tt,2)),1)); "
        "if(type(sol)!=\"t_INT\", my(x0=sol[1], KB=sol[2], nk=matsize(KB)[2]); "
        "for(b=0, min(1,2^nk-1), my(x=x0); for(c=1,nk, if(bitand(b,2^(c-1)), x=x+KB[,c])); "
        "listput(targets,[16,lift(Mod(x,2))])); cnt16++)); "
        "for(ti=1,#targets, my(tg=targets[ti], al=twist(g,tg[2]), sv=nfeltsign(bnf,al), "
        "nneg=sum(i=1,12,(1-sv[i])/2), rr=24-2*nneg); if(rr!=tg[1], next()); "
        "my(res=ctype(al)); if(type(res)==\"t_INT\", next()); "
        "print(\"HIT|\", q, \"|\", v, \"|\", rr, \"|\", res[2], \"|\", lift(al), \"|\", Mat(res[1])))));",
        "print(\"DONE\");",
    ]
    out = subprocess.run(["gp", "-q"], input="\n".join(L), capture_output=True, text=True,
                         timeout=timeout).stdout
    hits, qs = [], []
    for ln in out.splitlines():
        if ln.startswith("QS|"):
            qs = [int(x) for x in ln[3:].strip("[] ").split(",")]
        if not ln.startswith("HIT|"):
            continue
        _, q, w, r, n, alpha, tally = ln.split("|")
        hits.append({"q": int(q), "w": [int(x) for x in w.strip("[] ").split(",")],
                     "r": int(r), "n": int(n), "alpha": alpha.strip(),
                     "tally": _parse_tally(tally.strip())})
    return qs, hits


def _parse_tally(mat: str) -> dict:
    """PARI Mat(Map) prints as [key1, c1; key2, c2; ...] with vector keys."""
    tally = {}
    body = mat.strip()[1:-1]
    for row in body.split(";"):
        row = row.strip()
        if not row:
            continue
        key, cnt = row.rsplit(",", 1)
        ct = tuple(int(x) for x in key.strip().strip("[]").split(","))
        tally[ct] = int(cnt)
    return tally


def l1_label(tally: dict, gd: dict):
    n = sum(tally.values())
    obs = {k: v / n for k, v in tally.items()}
    scored = []
    for t, exp in gd.items():
        keys = set(exp) | set(obs)
        scored.append((sum(abs(obs.get(k, 0) - exp.get(k, 0)) for k in keys), t))
    scored.sort()
    return scored[0][1], scored[0][0]


def build_poly(alpha: str, timeout: float = 600.0):
    """K0(sqrt(alpha)) -> reduced degree-24 coefficients (ascending)."""
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
    ap.add_argument("--primes", type=int, default=2, help="number of completely-split q to sweep")
    ap.add_argument("--pilot", type=int, default=5, help="max candidates to build+enqueue")
    ap.add_argument("--r", type=int, default=None,
                    help="build only this signature r (e.g. 16 -- r=24 already held, test 0066)")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    gd = _gdist()
    qs, hits = sweep_gp(args.primes)
    print(f"split primes swept: {qs}")
    print(f"fingerprint-consistent (no impossible cycle type): {len(hits)} (q,w,twist) hits")

    # dedup identical alphas, then L1-gate
    seen, gated = set(), []
    for h in hits:
        if h["alpha"] in seen:
            continue
        seen.add(h["alpha"])
        t, l1 = l1_label(h["tally"], gd)
        h["best_t"], h["l1"] = t, round(l1, 4)
        if t in TARGET_TS and l1 < L1_THRESH:
            gated.append(h)
    print(f"distinct alphas: {len(seen)}; L1-gated (best in {TARGET_TS}, L1<{L1_THRESH}): "
          f"{len(gated)}")
    gated.sort(key=lambda h: (h["l1"], h["q"]))
    for h in gated[:12]:
        print(f"  q={h['q']} w={h['w']} r={h['r']} L1={h['l1']} best={h['best_t']} n={h['n']}")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump([{k: v for k, v in h.items() if k != "tally"} for h in gated],
              open(OUT / "gated.json", "w"), indent=1)

    if args.r is not None:
        gated = [h for h in gated if h["r"] == args.r]
        print(f"filtered to r={args.r}: {len(gated)} gated candidates")

    winners = []
    for h in gated:
        if len(winners) >= args.pilot:
            break
        c = build_poly(h["alpha"])
        if not c or len(c) != 25:
            print(f"  BUILD-FAIL q={h['q']} w={h['w']}")
            continue
        try:
            rr = gp.real_roots(c)
        except Exception:
            continue
        if rr != h["r"]:
            print(f"  R-MISMATCH q={h['q']} w={h['w']} want {h['r']} got {rr}")
            continue
        sd = gp.scoreable_disc(c)
        if sd is None:
            print(f"  BLANK-RISK disc q={h['q']} w={h['w']} r={rr}")
            continue
        wtag = "".join(str(x) for x in h["w"])
        winners.append({"t": 9641, "r": rr, "coeffs": c, "l1": h["l1"], "q": h["q"],
                        "src": f"q{h['q']}:w{wtag}", "disc": str(sd)})
        print(f"  WIN r={rr} L1={h['l1']} q={h['q']} w={h['w']} disc={sd}")

    print(f"\nmb2_sweep6: {len(winners)} locally-gated candidates")
    json.dump(winners, open(OUT / "winners.json", "w"), indent=1)

    if args.enqueue and winners:
        from igp import searchstore as store
        store.init()
        added = 0
        for w in winners:
            tag = f"lit:mb2sweepnew:{w['t']}.{w['r']}:{w['src']}"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": w["coeffs"]}, target=tag):
                added += 1
        store.set_priority_prefix("lit:mb2sweepnew", 130.0)
        print(f"enqueued {added} (tier new; 24T9641/9642 unheld). "
              "Group is 9641-or-9642 (Gassmann pair) -- SAIR's Magma label decides.")


if __name__ == "__main__":
    main()
