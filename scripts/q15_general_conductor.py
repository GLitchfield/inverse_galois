"""q15 — general-conductor C_2 constructor + aligned prediction (item C, step 1).

Generalizes the deliberate C_2-kernel constructor beyond the cyclic C_12 (Q(zeta_13))
slice to ANY cyclotomic top via ``gp.cyclotomic_c2`` (enumerate the units of n as the
Galois action). The group PREDICTION uses ``gap.kernel_label_perms`` fed the SAME
(Z/n)* action (``gp.cyclotomic_top_perms``), so intermediate kernels align between
predict and construct. Magma is ground truth: this test checks predict == Magma label.

- Q(zeta_13) (top 12T1=C_12, sorted-units action): cross-check the generalized path
  reproduces the known family.
- Q(zeta_21) (top 12T2=C_2 x C_6): a NEW abelian top — full + two intermediate kernels.

Rerunnable: first run constructs + submits (async); reruns collect and compare.
Run: uv run python scripts/q15_general_conductor.py
"""

from __future__ import annotations

import json
from pathlib import Path

from igp import db, engine, gap, gp, submission

PRED = Path(__file__).resolve().parents[1] / "data/processed/q15_predictions.json"

CASES = [
    ("zeta13", 13, 53, [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
    ("zeta13", 13, 53, [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]),
    ("zeta21", 21, 43, [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # full
    ("zeta21", 21, 43, [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # intermediate
    ("zeta21", 21, 43, [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]),  # intermediate
]


def build():
    preds = {}
    cands = []
    for tag, n, q, w in CASES:
        perms = gp.cyclotomic_top_perms(n)
        pred = gap.kernel_label_perms(w, perms)
        co = gp.cyclotomic_c2(w, n, q)
        if len(co) != 25 or co[-1] != 1:
            print(f"  SKIP {tag} w={w[:4]} (bad poly deg={len(co) - 1})")
            continue
        line = submission.poly_line(co)
        preds[line] = {"predict": pred, "source": f"{tag}:w={''.join(map(str, w))}"}
        cands.append((line, f"C-gen:{tag}:{pred}"))
        print(f"  {tag} w={w[:4]}.. predict={pred}")
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
        res = cache.get(line)
        got = (res or {}).get("label") or "(pending)"
        mark = "OK " if got == info["predict"] else ("??" if got == "(pending)" else "XX")
        print(f"    [{mark}] predict={info['predict']:>10}  magma={got:>10}  {info['source']}")


def main():
    print("collect (drain pending):", engine.collect())
    print("build + predict:")
    cands = build()
    sid = engine.submit(cands, description="q15 general-conductor C_2 (zeta13/zeta21)")
    print(f"submitted: {sid or '(nothing new — already in flight/verified)'}")
    print("collect:", engine.collect())
    compare()


if __name__ == "__main__":
    main()
