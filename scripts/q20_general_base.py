"""q20 — C_2-kernel over a general (non-Galois) base field: the BIG-top unlock (item C).

Every prior C_2 construction used a Galois base (autos via nfgaloisconj) and therefore a
REGULAR top: |H| = deg F. The frontier's bigger groups need bigger tops (|H| > deg F), which
only a NON-Galois base provides. ``gp.general_c2`` does exactly that with no autos: alpha =
product of the generators of the primes selected by ``w`` (idealprimedec order), K = F(sqrt
alpha). Reaches tops H = 12Tj with |H| > 12.

Base here: F = Q[x]/(x^12 - 2) — non-Galois (2 autos), Galois closure order 48 (= the top),
h(F)=1, completely-split prime q = 601.

Labeling: the exact a-priori predictor needs H's action aligned to gp's prime ordering (the
Galois closure) — deferred; we predict the ORDER (|A|*|H|, labeling-independent) and confirm
the BIG top via Magma + block structure. Rerunnable.
Run: uv run python scripts/q20_general_base.py
"""

from __future__ import annotations

import json
from pathlib import Path

from igp import db, engine, gap, gp, submission
from igp import kernelsolve as ks

# x^12-2's top: affine maps k -> b*k + a on Z/12, b in (Z/12)*; order 48 = 12T28.
TOP_PERMS = [[(b * k + a) % 12 for k in range(12)] for b in (1, 5, 7, 11) for a in range(12)]
TOP_ORDER = 48

REC = Path(__file__).resolve().parents[1] / "data/processed/q20_records.json"
F = [-2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]  # x^12 - 2 (ascending)
Q = 601
PATTERNS = [
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


def build():
    rec, cands = {}, []
    for w in PATTERNS:
        co = gp.general_c2(F, w, Q)
        if not co or len(co) != 25 or co[-1] != 1:
            print(f"  SKIP w={w} (failed)")
            continue
        subs = gp.subfield_degrees(co)
        line = submission.poly_line(co)
        src = f"x12-2:{''.join(map(str, w))}"
        rec[line] = {"source": src}
        cands.append((line, f"C-gen_c2:{src}"))
        print(f"  {src}: 12x2={12 in subs} subs={subs}")
    REC.parent.mkdir(parents=True, exist_ok=True)
    REC.write_text(json.dumps(rec, indent=2))
    return cands


def predicted_order(src):
    """Labeling-independent order prediction: 2^dim(<H-orbit of w>) * |H| (no alignment needed)."""
    w = [int(c) for c in src.split(":")[-1]]
    wm = sum(wi << i for i, wi in enumerate(w))
    return 2 ** len(ks.module_basis(wm, TOP_PERMS)) * TOP_ORDER


def report():
    if not REC.exists():
        return
    rec = json.loads(REC.read_text())
    cache = db.cache_load()
    print("\n  predicted order -> Magma (big-top 12x2 groups):")
    for line, info in rec.items():
        res = cache.get(line) or {}
        lab = res.get("label")
        pred = predicted_order(info["source"])
        if not lab:
            print(f"    {info['source']:>14}: predicted order {pred} (Magma pending)")
            continue
        t = int(lab[3:])
        o = gap.transitive_group_info(24, t)["order"]
        top = [s["top"] for s in gap.wreath_decompose_batch([t]).get(t, [])
               if s["k"] == 2 and s["m"] == 12]
        mark = "OK" if o == pred else "XX"
        print(f"    {info['source']:>14}: predicted {pred} -> {lab} order {o} top {top} [{mark}]")


def main():
    print("collect (drain pending):", engine.collect())
    print("build:")
    cands = build()
    sid = engine.submit(cands, description="q20 general non-Galois base C_2 (x^12-2, |H|=48)")
    print(f"submitted: {sid or '(nothing new)'}")
    print("collect:", engine.collect())
    report()


if __name__ == "__main__":
    main()
