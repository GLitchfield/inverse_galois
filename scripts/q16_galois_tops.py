"""q16 — C_2-kernel over general GALOIS degree-12 tops (item C, step 2).

Step 1 (q15) reached the two abelian order-12 tops (C_12, C_2xC_6) via cyclotomic
fields. Step 2 reaches the NON-abelian order-12 tops by taking the base field F to be
any Galois degree-12 field and using its automorphisms (``nfgaloisconj``) directly:

- ``gp.galois_c2(f, w, q)``: alpha = prod_{w_a=1} sigma_a(pi), pi a generator of a prime
  above a completely-split q; K = F(sqrt alpha). Works for any Galois F with h(F)=1.
- ``gp.galois_action_perms(f)``: the regular action of Gal(F/Q) on its autos, so the
  GROUP prediction (``gap.kernel_label_perms``) shares the construction's action.

Fields built here (both Galois, degree 12, h=1):
- A_4 (= 12T4): splitting field of the A_4 quartic x^4 + 8x + 12 (split prime q=71).
- D_6 = C_2 x S_3 (= 12T3): compositum of Q(zeta of x^3-2 splitting) and Q(sqrt 5) (q=31).

Rerunnable: first run constructs + submits; reruns collect and compare predict vs Magma.
Run: uv run python scripts/q16_galois_tops.py
"""

from __future__ import annotations

import json
from pathlib import Path

from igp import db, engine, gap, gp, submission

PRED = Path(__file__).resolve().parents[1] / "data/processed/q16_predictions.json"

# (tag, gp expression for the Galois degree-12 defining poly, split prime)
FIELDS = [
    ("A4", "polredbest(nfsplitting(x^4+8*x+12))", 71),
    ("D6", "polredbest(polcompositum(nfsplitting(x^3-2), x^2-5)[1])", 31),
]
WS = {
    "full": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "pair": [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "skip": [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
}


def build():
    preds, cands = {}, []
    for tag, expr, q in FIELDS:
        coeffs = [int(x) for x in gp.script(f"print(Vec({expr}));").strip("[]").split(",")][::-1]
        perms = gp.galois_action_perms(coeffs)
        for wname, w in WS.items():
            pred = gap.kernel_label_perms(w, perms)
            co = gp.galois_c2(coeffs, w, q)
            if len(co) != 25 or co[-1] != 1:
                print(f"  SKIP {tag}/{wname} (bad poly)")
                continue
            line = submission.poly_line(co)
            preds[line] = {"predict": pred, "source": f"{tag}:{wname}"}
            cands.append((line, f"C-gal:{tag}:{wname}:{pred}"))
            print(f"  {tag}/{wname}: predict={pred}")
    PRED.parent.mkdir(parents=True, exist_ok=True)
    PRED.write_text(json.dumps(preds, indent=2))
    return cands


def compare():
    if not PRED.exists():
        return
    preds = json.loads(PRED.read_text())
    cache = db.cache_load()
    print("\n  predict vs Magma:")
    for line, info in preds.items():
        got = (cache.get(line) or {}).get("label") or "(pending)"
        mark = "OK " if got == info["predict"] else ("??" if got == "(pending)" else "XX")
        print(f"    [{mark}] predict={info['predict']:>10}  magma={got:>10}  {info['source']}")


def main():
    print("collect (drain pending):", engine.collect())
    print("build + predict:")
    cands = build()
    sid = engine.submit(cands, description="q16 general Galois tops A4/D6 (C_2-kernel)")
    print(f"submitted: {sid or '(nothing new)'}")
    print("collect:", engine.collect())
    compare()


if __name__ == "__main__":
    main()
