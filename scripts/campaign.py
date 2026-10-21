"""campaign.py — route large-kernel constructions at fully-undiscovered groups.

Per test 0018, 10,426 groups are completely undiscovered (sole-realizer = 1.0 each). This
inverts our exact-labeling C_2-kernel families into a {label -> recipe} map, intersects with
the undiscovered (t,0) set, and constructs the matches.

Families (size-2, exact construction<->label correspondence, tests 0010-0011):
  C_12  = Q(zeta_13), q=53     |  C_2xC_6 = Q(zeta_21), q=43   (cyclotomic_c2)
  D_6   = 12T3 Galois, q=31    |  A_4     = 12T4 Galois, q=71   (galois_c2)

For each top: enumerate cyclic kernels (one generator w each; popcount 1..MAXPC), batch-label
via gap.kernel_labels_for_top, keep label->w. Then intersect with undiscovered (t,0), construct
via the family's constructor, and submit (engine dedups + records). Resumable.

Run: uv run python scripts/campaign.py [maxpc] [maxconstruct]
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
MAXPC = int(sys.argv[1]) if len(sys.argv) > 1 else 4
MAXCONSTRUCT = int(sys.argv[2]) if len(sys.argv) > 2 else 24


def families():
    fa = "polredbest(nfsplitting(x^4+8*x+12))"
    fd = "polredbest(polcompositum(nfsplitting(x^3-2), x^2-5)[1])"
    a4 = [int(x) for x in gp.script(f"print(Vec({fa}));").strip("[]").split(",")][::-1]
    d6 = [int(x) for x in gp.script(f"print(Vec({fd}));").strip("[]").split(",")][::-1]
    # Only GALOIS bases give a reliable a-priori label (construction action = nfgaloisconj
    # order = the perms fed here). The non-Galois big top 12T28 (x^12-2) was tried but its
    # affine action aligns to gp's prime order only for some kernels (matched full/pair/skip
    # in test 0015, but mis-predicted 24T10361 -> realized 24T18449), so it is NOT included:
    # non-Galois a-priori targeting needs the true prime<->block alignment (Galois closure).
    return [
        ("C12", gp.cyclotomic_top_perms(13), lambda w: gp.cyclotomic_c2(w, 13, 53)),
        ("C2xC6", gp.cyclotomic_top_perms(21), lambda w: gp.cyclotomic_c2(w, 21, 43)),
        ("D6", gp.galois_action_perms(d6), lambda w: gp.galois_c2(d6, w, 31)),
        ("A4", gp.galois_action_perms(a4), lambda w: gp.galois_c2(a4, w, 71)),
    ]


def cyclic_reps(perms):
    """One generator w per distinct cyclic kernel (lowest popcount), popcount 1..MAXPC."""
    by_kernel = {}
    for pc in range(1, MAXPC + 1):
        for idx in combinations(range(12), pc):
            w = sum(1 << i for i in idx)
            key = ks.module_basis(w, perms)
            by_kernel.setdefault(key, [(i in idx) and 1 or 0 for i in range(12)])
    return list(by_kernel.values())


def main():
    if not PROG.exists():
        print("progress.json missing — fetch leaderboard first")
        return
    prog = json.loads(PROG.read_text())
    def undiscovered(t):
        return prog.get(f"{t},0", {}).get("teamCount", 1) == 0

    print("collect (drain pending):", engine.collect())
    routes = {}  # label -> (family_name, w, constructor)
    for name, perms, ctor in families():
        reps = cyclic_reps(perms)
        labels = gap.kernel_labels_for_top(perms, reps)
        for w in reps:
            lab = labels.get(tuple(w))
            if lab:
                routes.setdefault(lab, (name, w, ctor))
        print(f"  {name}: {len(reps)} cyclic kernels -> {len(set(labels.values()))} labels")

    targets = {lab: v for lab, v in routes.items() if undiscovered(lab[3:])}
    print(f"\nreachable labels: {len(routes)}; UNDISCOVERED (t,0) among them: {len(targets)}")
    if not targets:
        print("none undiscovered in these families (saturated).")
        return

    cands = []
    for lab, (name, w, ctor) in list(targets.items())[:MAXCONSTRUCT]:
        co = ctor(w)
        if co and len(co) == 25 and co[-1] == 1:
            cands.append((submission.poly_line(co), f"campaign:{name}:{lab}"))
            print(f"  built {lab} via {name}")
    sid = engine.submit(cands, description="campaign: undiscovered groups (size-2 kernels)")
    print(f"\nconstructed {len(cands)}; submitted: {sid or '(nothing new)'}")
    print("collect:", engine.collect())


if __name__ == "__main__":
    main()
