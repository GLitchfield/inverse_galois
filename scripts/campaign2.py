"""campaign2.py — multi-generator routing: the full submodule lattice per top.

Extends campaign.py (cyclic kernels only) to NON-cyclic kernels via multi-prime alpha
(gp.*_c2_multi + gap.kernel_labels_multigen). Enumerates submodules as <H-orbits of a small
generating set> (singles + pairs of low-popcount patterns, deduped by reduced basis), routes
the undiscovered ones, and constructs each with one split prime per generator.

Run: uv run python scripts/campaign2.py [maxconstruct]
"""

from __future__ import annotations

import json
import os
import sys
from itertools import combinations
from pathlib import Path

from igp import engine, gap, gp, submission
from igp import kernelsolve as ks

ROOT = Path(__file__).resolve().parents[1]
# Live per-pair leaderboard state (fetched separately; search_ctl refresh writes this path).
PROG = Path(os.environ.get("IGP_PROGRESS", ROOT / "data" / "processed" / "progress.json"))
MAXCONSTRUCT = int(sys.argv[1]) if len(sys.argv) > 1 else 24


def submodules(perms):
    """{reduced-basis -> minimal generator list} for cyclic + 2-generated submodules.

    Cyclic: varied low-popcount single patterns (popcount 1..3). Non-cyclic: pairs of those
    cyclic generators whose combined orbit-span is a new submodule.
    """
    mods = {}
    cyc = []
    for pc in range(1, 4):
        for idx in combinations(range(12), pc):
            w = [1 if k in idx else 0 for k in range(12)]
            b = ks.module_basis(sum(1 << k for k in idx), perms)
            if b not in mods:
                mods[b] = [w]
                cyc.append((sum(1 << k for k in idx), w, b))
    # non-cyclic: combine pairs of distinct cyclic submodules
    for a in range(len(cyc)):
        for c in range(a + 1, len(cyc)):
            ma, wa, _ = cyc[a]
            mc, wc, _ = cyc[c]
            b = ks.rref(ks.orbit(ma, perms) | ks.orbit(mc, perms))
            if b not in mods:
                mods[b] = [wa, wc]
    return mods


def families():
    fa = "polredbest(nfsplitting(x^4+8*x+12))"
    fd = "polredbest(polcompositum(nfsplitting(x^3-2), x^2-5)[1])"
    a4 = [int(x) for x in gp.script(f"print(Vec({fa}));").strip("[]").split(",")][::-1]
    d6 = [int(x) for x in gp.script(f"print(Vec({fd}));").strip("[]").split(",")][::-1]

    def split_primes(cs, n=2, hi=4000):
        out = gp.script(
            f"f=Pol({cs[::-1]},'y);bnf=bnfinit(f);c=0;"
            f"for(q=2,{hi},if(isprime(q)&&#idealprimedec(bnf,q)==12,print(q);c++;if(c>={n},break)));"
        )
        return [int(x) for x in out.split()][:n]

    return [
        ("C12", gp.cyclotomic_top_perms(13), [53, 79],
         lambda gens, qs: gp.cyclotomic_c2_multi(13, list(zip(qs, gens, strict=False)))),
        ("C2xC6", gp.cyclotomic_top_perms(21), [43, 127],
         lambda gens, qs: gp.cyclotomic_c2_multi(21, list(zip(qs, gens, strict=False)))),
        ("D6", gp.galois_action_perms(d6), split_primes(d6),
         lambda gens, qs: gp.galois_c2_multi(d6, list(zip(qs, gens, strict=False)))),
        ("A4", gp.galois_action_perms(a4), split_primes(a4),
         lambda gens, qs: gp.galois_c2_multi(a4, list(zip(qs, gens, strict=False)))),
    ]


def main():
    if not PROG.exists():
        print("progress.json missing")
        return
    prog = json.loads(PROG.read_text())
    def undiscovered(t):
        return prog.get(f"{t},0", {}).get("teamCount", 1) == 0

    print("collect:", engine.collect())
    routes = {}
    for name, perms, primes, ctor in families():
        mods = submodules(perms)
        gens_list = list(mods.values())
        labels = gap.kernel_labels_multigen(perms, gens_list)
        new = 0
        for gens, lab in zip(gens_list, labels, strict=False):
            if lab not in routes:
                routes[lab] = (name, gens, primes, ctor)
                new += 1
        print(f"  {name}: {len(mods)} submodules -> {len(set(labels))} labels ({new} new)")

    targets = {lab: v for lab, v in routes.items() if undiscovered(lab[3:])}
    print(f"\nreachable labels: {len(routes)}; UNDISCOVERED: {len(targets)}")
    cands = []
    for lab, (name, gens, primes, ctor) in list(targets.items())[:MAXCONSTRUCT]:
        try:
            co = ctor(gens, primes[:len(gens)])
        except Exception as e:
            print(f"  {lab} ({name}): construct failed {str(e)[:40]}")
            continue
        if co and len(co) == 25 and co[-1] == 1:
            cands.append((submission.poly_line(co), f"campaign2:{name}:{lab}"))
            print(f"  built {lab} via {name} ({len(gens)}-gen)")
    sid = engine.submit(cands, description="campaign2: undiscovered via multi-gen kernels")
    print(f"\nconstructed {len(cands)}; submitted: {sid or '(nothing new)'}")
    print("collect:", engine.collect())


if __name__ == "__main__":
    main()
