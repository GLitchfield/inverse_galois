"""DISC-MIN DEFENSE producer (2026-07-13): shrink our disc on held minblk=2 pairs we're behind on.

REFUTED BY SAIR (2026-07-13) -- DO NOT DEPLOY as-is. The smaller-disc candidates this produces land
NEIGHBORING groups, not the targets (24T13862,4 -> SAIR 24T18770/17391; 15714,4 -> 18891; 3333,0 ->
7935): the 24Tt is pinned to the specific base field's Kummer module, and the local Frobenius
fingerprint (L1<0.30 vs our held poly) can't separate 24T13862 from 24T18770. So it does NOT recover
disc on the target pairs -- same low-trust-signal trap as tests 0044/0045/0051-0054. The amortized
gp machinery below is sound + fast; the missing piece is a SAIR-in-the-loop group-preservation gate
(PILOT each (base,w,q), persist only SAIR-confirmed-target triples). Kept for that salvage; the
disc-undercut DIAGNOSIS stands, this DEFENSE does not. See docs/commentary.md 2026-07-13.


We hold the disc-min on only 562 of ~22,555 scoreable pairs; a rival beats our disc on 22,029, and
per-pair score is 2^(1-k)*log(minDisc)/log(ourDisc), so our ~2x-larger discs collect ~half the
points. The disc-behind pairs are gen12 (general_c2 over non-Galois deg-12 bases) built with LARGE
split primes and NON-minimal bases; disc(K) ~ disc(K0)^2 * q^|w|, so re-building over the smallest-
disc base of the SAME 12Tj label with the smallest completely-split prime and smallest subset w
shrinks the disc. Group-preservation is enforced by matching the candidate's Frobenius cycle-type
distribution to OUR OWN held poly (a known-good realization -> no GAP labeling). Every improvement
helps (best_by_pair keeps the smallest disc); pairs with a small module + small split prime can beat
the rival outright (spike: 24T3333,0 66->32), dim-6 pairs only narrow the gap (13862,4 65->55).

Bounded per run (each pair is a ~1-2 min sweep); processes the top-gain disc-behind pairs first,
cursored. Run: uv run python scripts/mb2_discmin.py [--pairs N] [--enqueue]
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from mb2_sweep6 import _parse_tally  # noqa: E402  -- PARI Mat(Map) parser
from mb2ns_producer import poly_dist  # noqa: E402

from igp import coverage, gp, lmfdb  # noqa: E402
from igp import searchstore as store  # noqa: E402

PROG = json.loads((ROOT / "data/processed/progress.json").read_text())
L1_THRESH = 0.30


def _l1(a: dict, b: dict) -> float:
    keys = set(a) | set(b)
    na, nb = sum(a.values()) or 1, sum(b.values()) or 1
    return sum(abs(a.get(k, 0) / na - b.get(k, 0) / nb) for k in keys)


def _base_label(src: str) -> str | None:
    for p in src.split(":"):
        if p.startswith("12T"):
            return p
    return None


def _digits(n) -> int:
    return len(str(abs(int(n)))) if n else 0


def disc_behind(limit: int) -> list:
    """Held minblk=2 (gen12) pairs where a rival has a smaller disc, sorted by recoverable score."""
    best = coverage.best_by_pair()
    out = []
    for (t, r), b in best.items():
        if not b.get("line") or not b.get("disc"):
            continue
        lab = _base_label(str(b.get("source", "")))
        if not lab or "gen12" not in str(b.get("source", "")):
            continue  # this producer only re-sweeps the general_c2 family
        p = PROG.get(f"{t},{r}", {})
        md = p.get("minDisc")
        our = abs(int(b["disc"]))
        if not md or int(md) <= 0 or our <= int(md) * 1.0000001 or our <= 1:
            continue
        k = p.get("teamCount", 1) or 1
        gain = 2 ** (1 - k) * (1 - math.log(int(md)) / math.log(our))
        out.append((gain, t, r, lab, our, int(md), b["line"]))
    out.sort(reverse=True)
    return out[:limit]


def _sweep_gp(base_coeffs: list, target_r: int, nq: int, dens_hi: int, per_size: int,
              timeout: float) -> list:
    """AMORTIZED sweep: one bnfinit + one prime-decomposition, per-candidate work is only
    nfmodpr+issquare (the Dedekind cycle type of K0(sqrt al) at p, no field build). Sweeps size-
    2/4/6 subsets w over nq completely-split primes, keeps those whose NATURAL generator gives
    r==target_r, and prints (q, w, r, n, alpha, cycle-type tally). Returns hit dicts."""
    cs = ",".join(str(int(c)) for c in base_coeffs[::-1])
    # NEWLINE-join (not ""): each piece must be its own line, else the one-line ctype(al)=... def
    # swallows the sweep loop as its body and nothing executes.
    L = "\n".join([
        "default(parisizemax,10*10^9);",
        f"K0=Pol([{cs}]);bnf=bnfinit(K0,1);",
        f"QS=List();forprime(q=5,50000,if(#QS>={nq},break());"
        "if(#idealprimedec(bnf,q)==12,listput(QS,q)));print(\"QS|\",Vec(QS));",
        "ctype(al)=my(t=Map(),n=0);for(i=1,#PD,my(P=PD[i],ct=List(),bad=0);"
        "for(j=1,#P,my(pf=nfmodpr(bnf,al,P[j]),ff=P[j].f);if(pf==0,bad=1;break());"
        "if(issquare(pf),listput(ct,ff);listput(ct,ff),listput(ct,2*ff)));"
        "if(!bad,my(key=vecsort(Vec(ct)));mapput(t,key,if(mapisdefined(t,key),mapget(t,key),0)+1);"
        "n++));[t,n];",
        "SIZES=[2,4,6];",
        "for(qi=1,#QS,q=QS[qi];pr=idealprimedec(bnf,q);PLIST=List();"
        f"forprime(p=3,{dens_hi},if(p!=q&&Mod(bnf.disc,p)!=0,listput(PLIST,p)));"
        "PD=vector(#PLIST,i,idealprimedec(bnf,PLIST[i]));"
        "for(sz=1,#SIZES,my(k=SIZES[sz],cnt=0);"
        f"forvec(v=vector(k,i,[1,12]),if(cnt>={per_size},break());"
        "my(Jd=pr[v[1]]);for(j=2,k,Jd=idealmul(bnf,Jd,pr[v[j]]));"
        "my(pd=bnfisprincipal(bnf,Jd));"
        "if(#pd[1]==0||vecmax(abs(pd[1]))==0,"
        # r(K0(sqrt al)) = 2 * #{real places v of K0 : al >_v 0}; #sv = r1 (NOT always 12)
        "my(al=nfbasistoalg(bnf,pd[2]),sv=nfeltsign(bnf,al),rr=2*sum(i=1,#sv,(1+sv[i])/2));"
        f"if(rr=={target_r},my(res=ctype(al));if(type(res)!=\"t_INT\","
        "print(\"HIT|\",q,\"|\",Vec(v),\"|\",rr,\"|\",res[2],\"|\",lift(al),\"|\",Mat(res[1]));"
        "cnt++)))"
        ",2)));print(\"DONE\");",
    ])
    try:  # trailing newline is REQUIRED: gp never executes an unterminated final line
        out = subprocess.run(["gp", "-q"], input=L + "\n", capture_output=True, text=True,
                             timeout=timeout).stdout
    except Exception:  # noqa: BLE001
        return []
    hits = []
    for ln in out.splitlines():
        if not ln.startswith("HIT|"):
            continue
        _, q, w, rr, n, alpha, tally = ln.split("|")
        hits.append({"q": int(q), "w": w.strip(), "r": int(rr), "alpha": alpha.strip(),
                     "tally": _parse_tally(tally.strip())})
    return hits


def _build_poly(base_coeffs: list, alpha: str, timeout: float = 300.0) -> list:
    """K0(sqrt alpha) -> reduced deg-24 coeffs (ascending); only run on fingerprint survivors."""
    cs = ",".join(str(int(c)) for c in base_coeffs[::-1])
    # statements on SEPARATE lines (a one-line body breaks the parse, like the ctype def)
    body = (f"default(parisizemax,8*10^9);\nf=Pol([{cs}],y);\nal=subst({alpha},x,y);\n"
            "r=rnfequation(f, x^2 - al);\n"
            "print(if(poldegree(r)<24,\"DEG\",Vec(polredbest(r))));\n")
    try:
        out = subprocess.run(["gp", "-q"], input=body,
                             capture_output=True, text=True, timeout=timeout).stdout
    except Exception:  # noqa: BLE001
        return []
    if "DEG" in out or "[" not in out:
        return []
    return [int(x) for x in out.strip().strip("[]").split(",")][::-1]


def resweep(t: str, r: str, lab: str, our_disc: int, our_line: str,
            nq: int = 3, per_size: int = 160) -> dict | None:
    """Smaller-disc, group-matching realization of (t,r) via the AMORTIZED sweep. Fingerprints all
    candidates in one gp process, builds + nfdiscs only the group-matches, keeps the smallest."""
    ref, _ = poly_dist([int(x) for x in our_line.split(",")], hi=1500)
    try:
        base = lmfdb.fields(12, galois_label=lab, class_number=None, limit=1)[0][0]
    except Exception:  # noqa: BLE001
        return None
    hits = _sweep_gp(base, int(r), nq, 1500, per_size, timeout=1800.0)
    # build group-matches SMALLEST-|w| first: disc ~ disc(K0)^2 * q^|w|, so fewer primes in the
    # radical => smaller disc (the spike's win came from |w|=2). Tie-break on fingerprint quality.
    matches = sorted((h for h in hits if _l1(h["tally"], ref) < L1_THRESH),
                     key=lambda h: (h["w"].count(",") + 1, _l1(h["tally"], ref)))
    best = None
    for h in matches[:12]:
        co = _build_poly(base, h["alpha"])
        if not co or len(co) != 25:
            continue
        try:
            if gp.real_roots(co) != int(r):
                continue
        except Exception:  # noqa: BLE001
            continue
        d = gp.scoreable_disc(co)
        if d is None or abs(d) >= our_disc:
            continue
        if best is None or abs(d) < best[1]:
            best = (co, abs(d))
    return {"coeffs": best[0], "disc": best[1]} if best else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", type=int, default=8, help="disc-behind pairs to re-sweep this run")
    ap.add_argument("--per-size", type=int, default=160, help="subsets per size (small=faster)")
    ap.add_argument("--nq", type=int, default=3, help="split primes per pair")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    cur = int(store.get_kv("discmin_mb2_cursor", 0)) if args.enqueue else 0
    cands = disc_behind(cur + args.pairs)[cur:cur + args.pairs]
    print(f"{'pair':>13} {'base':>8} {'ourD':>5} {'rivalD':>7} {'newD':>5} {'gain':>6}")
    added = 0
    if args.enqueue:
        store.init()
    for gain, t, r, lab, our, md, line in cands:
        res = resweep(t, r, lab, our, line, nq=args.nq, per_size=args.per_size)
        newd = _digits(res["disc"]) if res else "-"
        print(f"{'24T'+t+','+r:>13} {lab:>8} {_digits(our):>5} {_digits(md):>7} "
              f"{str(newd):>5} {gain:>6.3f}")
        if res and args.enqueue:
            tag = f"discmin2:{t}.{r}:mb2:{_digits(res['disc'])}d"
            if store.enqueue("ready", {"coeffs": res["coeffs"]}, target=tag):
                added += 1
    if args.enqueue:
        store.set_kv("discmin_mb2_cursor", cur + args.pairs)
        store.set_priority_prefix("discmin2", 135.0)  # defense: reclaiming score we already earned
        print(f"enqueued {added} disc-min improvements; cursor -> {cur + args.pairs}")


if __name__ == "__main__":
    main()
