"""mb2 non-solvable SPLIT groups: general_c2 single-radical sweep (dive #30 greenlit build).

The 7 non-solvable minblk=2 groups whose kernel has ``dim soc(K)=1`` in GAP are reachable by a
SINGLE sqrt(alpha) over a totally-real degree-12 base -- the exact ``general_c2`` construction.
This walks each target's base top (12T33/74/183/230), pulls totally-real LMFDB bases, sweeps the
gen12 C_2-kernel w-patterns over completely-split primes, and enqueues the density-gated survivors.

Gate (budget-safe; SAIR's Magma label is the authoritative downstream gate):
  1. deg-24 irreducible
  2. polsturm real-root count r in the matched group's OPEN needed-r set
  3. Frobenius cycle-type density (~500 primes) matches ONE of the 7 targets: L1 < THRESH and 0
     impossible cycle types (rules out the C2-wreath collapse / Gassmann neighbor, which show
     imp>0, L1~1.0)
  4. gp.scoreable_disc non-blank (nfdisc completes in budget)

Recipe: docs/build_backlog.md (mb2 non-solvable Ready item) + auto_log dive #30 + gdist from
data/processed/mb2ns/gdist.json (GAP Chebotarev distributions, scripts/mb2ns_gdist.g).

Usage:
    .venv/bin/python scripts/mb2ns_producer.py            # dry run (build + gate, no enqueue)
    .venv/bin/python scripts/mb2ns_producer.py --enqueue  # enqueue survivors for the daemon
    .venv/bin/python scripts/mb2ns_producer.py --top 12T33 --enqueue
"""
import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from igp import gp, lmfdb  # noqa: E402

GDIST = ROOT / "data" / "processed" / "mb2ns" / "gdist.json"

# target 24Tt -> its totally-real deg-12 base top + the OPEN needed-r set (all tc=0, non-baseline,
# unheld as of 2026-07-11; verified in the build run)
TARGETS = {
    9633:  {"base": "12T33",  "rs": {4, 20}},
    9641:  {"base": "12T74",  "rs": {16, 24}},
    9642:  {"base": "12T74",  "rs": {16, 24}},
    14616: {"base": "12T183", "rs": {8, 16, 24}},
    16607: {"base": "12T183", "rs": {16}},
    19246: {"base": "12T230", "rs": {20, 24}},
    20699: {"base": "12T183", "rs": {24}},
}
L1_THRESH = 0.35           # clean match ~0.2; diff group ~1.0
MODELS_PER_PAIR = 2        # stop a pair once we have this many density-gated models


def _base_targets(top):
    return [t for t, v in TARGETS.items() if v["base"] == top]


def _pats():
    """gen12 diverse C_2-kernel patterns (popcount 1..4)."""
    idxs = ([(0,)]
            + list(itertools.combinations(range(12), 2))[:14]
            + list(itertools.combinations(range(8), 3))[:10]
            + list(itertools.combinations(range(6), 4))[:5])
    return [[1 if k in idx else 0 for k in range(12)] for idx in idxs]


def poly_dist(coeffs, hi=4000):
    """Frobenius cycle-type tally over primes < hi."""
    cs = ",".join(map(str, coeffs[::-1]))
    body = (f"f=Pol([{cs}]);d=poldisc(f);lc=pollead(f);"
            f"forprime(p=3,{hi}, if(d%p!=0 && lc%p!=0, fa=factormod(f,p); "
            "if(vecmax(fa[,2])==1, print(vecsort(vector(matsize(fa)[1],i,poldegree(fa[i,1])))))));")
    out = subprocess.run(["gp", "-q"], input="default(parisizemax,2*10^9);\n" + body,
                         capture_output=True, text=True, timeout=180).stdout
    tally = {}
    n = 0
    for ln in out.splitlines():
        ln = ln.strip()
        if not ln.startswith("["):
            continue
        ct = tuple(sorted(int(x) for x in ln.strip("[]").split(",") if x.strip()))
        if sum(ct) != 24:
            continue
        tally[ct] = tally.get(ct, 0) + 1
        n += 1
    return tally, n


def density_label(coeffs, gd):
    """Return (best_t, l1, imp, n) matching the poly against the 7 target distributions."""
    tally, n = poly_dist(coeffs)
    if not n:
        return None, 9.9, 99, 0
    scored = []
    for t, g in gd.items():
        exp = {tuple(int(x) for x in k.split(",")): v / g["order"] for k, v in g["dist"].items()}
        obs = {ct: c / n for ct, c in tally.items()}
        keys = set(exp) | set(obs)
        l1 = sum(abs(obs.get(k, 0) - exp.get(k, 0)) for k in keys)
        imp = sum(1 for ct in tally if ct not in exp)
        scored.append((l1, int(t), imp))
    scored.sort()
    l1, t, imp = scored[0]
    return t, l1, imp, n


def sweep_top(top, gd, bases_lim, nq, need):
    """Build + gate over one base top; return list of winner dicts. ``need`` = set of open (t,r)
    pairs still wanted (mutated as we fill)."""
    base_ts = _base_targets(top)
    bases = lmfdb.fields(12, galois_label=top, max_r2=0, class_number=None, limit=bases_lim)
    winners = []
    filled = {}  # (t,r) -> count
    for base in bases:
        coeffs = base[0]
        bdisc = base[2]
        if all((t, r) not in need or filled.get((t, r), 0) >= MODELS_PER_PAIR
               for t in base_ts for r in TARGETS[t]["rs"]):
            continue
        try:
            qs = gp.split_primes(coeffs, 12, k=nq)
        except Exception:
            continue
        for q in qs:
            for w in _pats():
                # early-out if every pair this base could serve is already filled
                if all(filled.get((t, r), 0) >= MODELS_PER_PAIR
                       for t in base_ts for r in TARGETS[t]["rs"]):
                    break
                try:
                    c = gp.general_c2(coeffs, w, q)
                except Exception:
                    c = []
                if not c or len(c) != 25:
                    continue
                try:
                    r = gp.real_roots(c)
                except Exception:
                    continue
                # only proceed if r could serve some still-wanted pair over this base
                if not any(r in TARGETS[t]["rs"] and (t, r) in need
                           and filled.get((t, r), 0) < MODELS_PER_PAIR for t in base_ts):
                    continue
                t, l1, imp, n = density_label(c, gd)
                if t not in base_ts or l1 >= L1_THRESH or imp > 0:
                    continue
                if r not in TARGETS[t]["rs"] or (t, r) not in need:
                    continue
                if filled.get((t, r), 0) >= MODELS_PER_PAIR:
                    continue
                sd = gp.scoreable_disc(c)
                if sd is None:
                    continue
                wtag = "".join(map(str, w))
                src = f"d{bdisc}:q{q}:{wtag}"
                winners.append({"t": t, "r": r, "coeffs": c, "l1": round(l1, 4),
                                "n": n, "src": src, "top": top, "disc": str(sd)})
                filled[(t, r)] = filled.get((t, r), 0) + 1
                print(f"  WIN 24T{t} r={r} L1={l1:.4f} n={n} [{top} {src}]")
    return winners


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", default=None, help="restrict to one base top (e.g. 12T33)")
    ap.add_argument("--bases", type=int, default=16)
    ap.add_argument("--nq", type=int, default=2)
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    raw = json.load(open(GDIST))
    gd = {str(t): raw[str(t)] for t in TARGETS}

    tops = [args.top] if args.top else ["12T33", "12T74", "12T183", "12T230"]
    need = {(t, r) for t in TARGETS for r in TARGETS[t]["rs"]}
    winners = []
    for top in tops:
        print(f"# {top} -> targets {_base_targets(top)}")
        winners += sweep_top(top, gd, args.bases, args.nq, need)

    print(f"\nmb2ns producer: {len(winners)} density-gated winners")
    pairs = sorted({(w["t"], w["r"]) for w in winners})
    print(f"  distinct open pairs landed: {len(pairs)} -> {pairs}")

    if args.enqueue and winners:
        from igp import db
        from igp import searchstore as store
        store.init()
        realized = db.load_realized()
        held_groups = {int(r["t"]) for r in realized if str(r.get("scoreable")).lower() == "true"}
        held_pairs = {(int(r["t"]), int(r["r"])) for r in realized
                      if str(r.get("scoreable")).lower() == "true"}
        tiers = {"new": 130.0, "pair": 115.0, "alt": 100.0}
        added = {"new": 0, "pair": 0, "alt": 0}
        for w in winners:
            t, r = w["t"], w["r"]
            tier = "alt" if (t, r) in held_pairs else ("pair" if t in held_groups else "new")
            tag = f"lit:mb2ns{tier}:{t}.{r}:{w['src']}"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": w["coeffs"]}, target=tag):
                added[tier] += 1
        for tier, pri in tiers.items():
            store.set_priority_prefix(f"lit:mb2ns{tier}", pri)
        print(f"  enqueued new {added['new']} @130, pair {added['pair']} @115, alt {added['alt']} @100")


if __name__ == "__main__":
    main()
