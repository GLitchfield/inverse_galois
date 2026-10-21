"""q17 — distribution-likelihood identifier vs same-invariant collisions (item B).

Validates ``verify.identify`` (the resolvent-lite upgrade): rank candidate 24Tt labels
for a polynomial by Chebotarev cycle-type *distribution* likelihood, hard-excluding any
candidate that can't produce an observed cycle type. This separates the collisions that
broke ``confirm_label`` (set containment), notably 24T2456 vs 24T12727 where the former's
cycle-type set is a SUBSET of the latter's (so only the distribution can tell them apart).

Pulls Magma-confirmed polynomials from realized.csv and runs the confusion matrix.
Run: uv run python scripts/q17_identifier.py
"""

from __future__ import annotations

from igp import db, gap, verify

LABELS = [2456, 12727, 2568, 2595, 14747]


def main():
    rows = db.load_realized()
    known = {}
    for r in rows:
        t = int(r["t"]) if r.get("t") else None
        if t in LABELS and t not in known and r.get("coeffs"):
            known[t] = [int(x) for x in r["coeffs"].split(",")]
    missing = [t for t in LABELS if t not in known]
    if missing:
        print(f"missing confirmed polys for {missing}; run the constructors first")
        return

    dists = gap.cycle_type_distributions(LABELS)
    print("true \\ identified (margin in nats; inf = rival hard-excluded)")
    allok = True
    for t in LABELS:
        res = verify.identify(known[t], LABELS, dists=dists)
        ok = res["best"] == t
        allok &= ok
        m = res["margin"]
        print(f"  24T{t:<6} -> 24T{res['best']:<6} "
              f"margin={'inf' if m == float('inf') else round(m, 1):>8}  "
              f"{'OK' if ok else 'WRONG'}  ({res['n_primes']} primes)")
    print("\nALL CORRECT" if allok else "\nSOME WRONG")


if __name__ == "__main__":
    main()
