"""q18 — size-4 (V_4-block) biquadratic construction, with prediction (item C, size-k).

First construction off the size-2 axis: m=6 blocks of size k=4 (the dominant frontier
shape). K = F(sqrt beta1, sqrt beta2) over a Galois degree-6 base F; beta1, beta2 are two
independent square-classes from a completely-split prime, giving a Klein-four (C_2 x C_2)
block group. Reuses the autos machinery (no zeta_k needed).

- ``gp.biquadratic_c2(f, w1, w2, q)``: the degree-24 compositum of F(sqrt b1), F(sqrt b2).
- ``gap.biquadratic_label(w1, w2, reg_perms)``: predict 24Tt from the explicit degree-24
  action of M ⋊ H on (block, sign1, sign2), aligned to the construction's regular action.

Base: F = Q(zeta_7) (C_6 = 6T1, h=1), split prime q=29.
Rerunnable: first run constructs + submits; reruns collect + compare predict vs Magma.
Run: uv run python scripts/q18_size4_biquadratic.py
"""

from __future__ import annotations

import json
from pathlib import Path

from igp import db, engine, gap, gp, submission, verify

PRED = Path(__file__).resolve().parents[1] / "data/processed/q18_predictions.json"
Q = 29
PAIRS = [
    ([1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0]),
    ([1, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0]),
    ([1, 0, 1, 0, 0, 0], [0, 1, 0, 1, 0, 0]),
]


def build():
    f6 = [int(x) for x in gp.script("print(Vec(polcyclo(7)));").strip("[]").split(",")][::-1]
    reg = gp.galois_action_perms(f6)
    preds, cands = {}, []
    for w1, w2 in PAIRS:
        pred = gap.biquadratic_label(w1, w2, reg)
        co = gp.biquadratic_c2(f6, w1, w2, Q)
        if len(co) != 25 or co[-1] != 1:
            print(f"  SKIP {w1}/{w2} (degenerate)")
            continue
        line = submission.poly_line(co)
        src = f"C6:{''.join(map(str, w1))}/{''.join(map(str, w2))}"
        preds[line] = {"predict": pred, "source": src}
        cands.append((line, f"C-biquad:{src}:{pred}"))
        print(f"  {src}: predict={pred}  subs={gp.subfield_degrees(co)}")
    PRED.parent.mkdir(parents=True, exist_ok=True)
    PRED.write_text(json.dumps(preds, indent=2))
    return cands


def compare():
    """Two-stage labeling: biquadratic_label gives the abstract group; identify (the item-B
    cycle-type identifier) resolves the exact degree-24 rep. Magma is ground truth.

    biquadratic_label can land on a sibling 24Tt (same abstract group, different permutation
    rep — a branch/cocycle subtlety of the hand action), so we show BOTH it and the identify
    resolution. The candidate pool for identify here is the labels seen this run (in practice:
    the abstract-group siblings with the right block structure)."""
    if not PRED.exists():
        return
    preds = json.loads(PRED.read_text())
    cache = db.cache_load()
    pool = {int(info["predict"][3:]) for info in preds.values()}
    for line in preds:
        lab = (cache.get(line) or {}).get("label")
        if lab:
            pool.add(int(lab[3:]))
    dists = gap.cycle_type_distributions(sorted(pool))
    print("\n  biquad_label (abstract group) -> identify (exact rep) vs Magma:")
    for line, info in preds.items():
        magma = (cache.get(line) or {}).get("label")
        if not magma:
            print(f"    [??] {info['source']}: predict={info['predict']} (Magma pending)")
            continue
        best = verify.identify([int(x) for x in line.split(",")], sorted(pool), dists=dists)["best"]
        mark = "OK " if f"24T{best}" == magma else "XX "
        print(f"    [{mark}] {info['source']}: biquad_label={info['predict']:>8} "
              f"identify=24T{best:<6} magma={magma}")


def main():
    print("collect (drain pending):", engine.collect())
    print("build + predict:")
    cands = build()
    sid = engine.submit(cands, description="q18 size-4 biquadratic V4 blocks (C_6 top)")
    print(f"submitted: {sid or '(nothing new)'}")
    print("collect:", engine.collect())
    compare()


if __name__ == "__main__":
    main()
