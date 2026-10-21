"""minblk=8 PSL(2,7)-cluster matcher. Assembles a gdist for the 7 targets from GAP
conjugacy-class dist_*.txt files and L1-matches a degree-24 candidate's Frobenius
cycle-type distribution against them. Also usable as: python3 mb8match.py '<asc coeffs>'."""
import json, subprocess, sys, glob, os

# GAP dist_<t>.txt files (committed under data/targets/mb8/); override with IGP_MB8_DIST.
DIR = os.environ.get("IGP_MB8_DIST", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  "..", "data", "targets", "mb8"))
TARGETS = [14051, 14052, 16060, 16061, 19280, 20408, 24315]

def load_gdist():
    gd = {}
    for t in TARGETS:
        fn = f"{DIR}/dist_{t}.txt"
        if not os.path.exists(fn):
            continue
        order = None
        dist = {}
        for ln in open(fn):
            ln = ln.strip()
            if ln.startswith("order"):
                order = int(ln.split()[1]); continue
            if not ln or " " not in ln:
                continue
            key, cnt = ln.rsplit(" ", 1)
            ct = tuple(int(x) for x in key.split(","))
            dist[ct] = dist.get(ct, 0) + int(cnt)   # merge classes w/ same cycle type
        gd[t] = {"order": order, "dist": dist}
    return gd

GD = load_gdist()

def poly_dist(coeffs, hi=6000):
    cs = ",".join(map(str, coeffs[::-1]))  # descending
    body = (f"f=Pol([{cs}]);d=poldisc(f);lc=pollead(f);"
            f"forprime(p=3,{hi}, if(d%p!=0 && lc%p!=0, fa=factormod(f,p); "
            "if(vecmax(fa[,2])==1, print(vecsort(vector(matsize(fa)[1],i,poldegree(fa[i,1])))))));")
    out = subprocess.run(["gp","-q"], input="default(parisizemax,4*10^9);\n"+body,
                         capture_output=True, text=True, timeout=300).stdout
    tally = {}; n = 0
    for ln in out.splitlines():
        ln = ln.strip()
        if not ln.startswith("["):
            continue
        ct = tuple(sorted(int(x) for x in ln.strip("[]").split(",") if x.strip()))
        if sum(ct) != 24:
            continue
        tally[ct] = tally.get(ct, 0) + 1; n += 1
    return tally, n

def l1(tally, n, t):
    g = GD[t]; order = g["order"]; gd = g["dist"]
    exp = {k: v/order for k, v in gd.items()}
    obs = {ct: c/n for ct, c in tally.items()}
    keys = set(exp) | set(obs)
    return sum(abs(obs.get(k,0)-exp.get(k,0)) for k in keys)

def predict(coeffs, hi=6000):
    tally, n = poly_dist(coeffs, hi)
    scored = []
    for t in TARGETS:
        gd = GD[t]["dist"]
        possible = set(gd)
        impossible = sum(tally[ct] for ct in tally if ct not in possible)
        scored.append((l1(tally, n, t), t, GD[t]["order"], impossible))
    scored.sort()
    return tally, n, scored

if __name__ == "__main__":
    coeffs = [int(x) for x in sys.argv[1].replace(" ", "").split(",")]
    tally, n, scored = predict(coeffs, int(sys.argv[2]) if len(sys.argv) > 2 else 6000)
    print(f"n_good_primes={n}")
    obscts = sorted(tally, key=lambda c: -tally[c])
    print("observed cycle types:", [(",".join(map(str,c)), tally[c]) for c in obscts[:14]])
    for dist, t, order, imp in scored:
        flag = f"  <-- {imp} IMPOSSIBLE obs!" if imp > 0 else ""
        print(f"   24T{t:<6} L1={dist:.4f} order={order}{flag}")
