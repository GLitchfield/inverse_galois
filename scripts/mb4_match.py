"""Predict the 24Tt of a degree-24 candidate by matching its Frobenius cycle-type
distribution (factorization degrees mod many primes) against GAP Chebotarev distributions."""
import json, os, sys, subprocess

# GAP Chebotarev distributions for the targets (was a session scratchpad); override with IGP_SCRATCH.
_SCRATCH = os.environ.get("IGP_SCRATCH", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      "..", "data", "processed", "scratch"))
GD = json.load(open(os.path.join(_SCRATCH, "gdist.json")))

# top -> list of target t
TOP_TARGETS = {
    "6T12":[18420,19632,21853,24496,24650],
    "6T14":[19630,19631,20713,21852,22784,24596,24729],
    "6T15":[16062,21449,22351,23173,24727],
    "6T16":[17948,22349,22350,23175,24099,24802,24873],
    None: list(map(int, GD.keys())),
}

def poly_dist(coeffs, hi=4000):
    """Tally Frobenius cycle types of the ascending-coeff poly over primes < hi."""
    cs = ",".join(map(str, coeffs[::-1]))  # descending for Pol
    # single-line body: gp -q reads line-by-line, so no embedded newlines inside forprime
    body = (f"f=Pol([{cs}]);d=poldisc(f);lc=pollead(f);"
            f"forprime(p=3,{hi}, if(d%p!=0 && lc%p!=0, fa=factormod(f,p); "
            "if(vecmax(fa[,2])==1, print(vecsort(vector(matsize(fa)[1],i,poldegree(fa[i,1])))))));")
    out = subprocess.run(["gp","-q"], input="default(parisizemax,2*10^9);\n"+body,
                         capture_output=True, text=True, timeout=180).stdout
    tally={}; n=0
    for ln in out.splitlines():
        ln=ln.strip()
        if not ln.startswith("["): continue
        ct=tuple(sorted(int(x) for x in ln.strip("[]").split(",") if x.strip()))
        if sum(ct)!=24: continue
        tally[ct]=tally.get(ct,0)+1; n+=1
    return tally, n

def l1(tally, n, t):
    g=GD[str(t)]; order=g["order"]; gd=g["dist"]
    # normalized expected freq per cycle type
    exp={tuple(int(x) for x in k.split(",")):v/order for k,v in gd.items()}
    obs={ct:c/n for ct,c in tally.items()}
    keys=set(exp)|set(obs)
    return sum(abs(obs.get(k,0)-exp.get(k,0)) for k in keys)

def predict(coeffs, top=None, hi=4000):
    tally,n = poly_dist(coeffs, hi)
    cands = TOP_TARGETS[top]
    # also flag cycle types observed that are IMPOSSIBLE for a candidate (hard filter)
    scored=[]
    for t in cands:
        gd=GD[str(t)]["dist"]
        possible={tuple(int(x) for x in k.split(",")) for k in gd}
        impossible=[ct for ct in tally if ct not in possible]
        scored.append((l1(tally,n,t), t, GD[str(t)]["order"], len(impossible)))
    scored.sort()
    return tally, n, scored

if __name__=="__main__":
    # read batch file: tag|coeffs and optional top from tag prefix
    for ln in open(sys.argv[1]):
        ln=ln.strip()
        if "|" not in ln: continue
        tag,cs=ln.split("|")
        coeffs=[int(x) for x in cs.split(",")]
        top=tag.split("_")[0] if tag.split("_")[0] in TOP_TARGETS else None
        tally,n,scored=predict(coeffs, top)
        print(f"\n### {tag}  (top={top}, {n} good primes)")
        for dist,t,order,imp in scored[:4]:
            flag="  <-- IMPOSSIBLE cycle types!" if imp>0 else ""
            print(f"   24T{t:<6} L1={dist:.4f} order={order} impossible_cts={imp}{flag}")
