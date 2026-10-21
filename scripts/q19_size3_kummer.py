"""q19 — size-3 (C_3-block) cyclotomic Kummer construction (item C, size-k axis).

The second dominant frontier shape, 8x3 (test 0004): m=8 blocks of size k=3, cyclic C_3
block group. K = Q(zeta_15)(alpha^{1/3}); zeta_3 lives in Q(zeta_15) (3 | 15), so the
radical extension is a clean cyclic Kummer C_3. Q(zeta_15) has degree 8 (= the 8 blocks),
top (Z/15)* = C_2 x C_4, h=1; split prime q=31.

Unlike k=2, the C_3 block carries a cyclotomic twist (complex conjugation inverts zeta_3),
so the kernel is a *twisted* F_3[H]-module; the exact a-priori predictor is deferred. This
script validates the CONSTRUCTION: every output is a degree-24 field with an 8x3 block
structure (degree-8 subfield), and Magma assigns the 24Tt label.

Rerunnable: first run constructs + submits; reruns collect + report Magma labels.
Run: uv run python scripts/q19_size3_kummer.py
"""

from __future__ import annotations

import json
from pathlib import Path

from igp import db, engine, gp, submission

REC = Path(__file__).resolve().parents[1] / "data/processed/q19_records.json"
N, Q, K = 15, 31, 3
PATTERNS = [
    [1, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0],
    [1, 0, 1, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0],
    [2, 1, 0, 0, 0, 0, 0, 0],
]


def build():
    rec, cands = {}, []
    for w in PATTERNS:
        co = gp.cyclotomic_kummer(w, N, Q, K)
        if len(co) != 25 or co[-1] != 1:
            print(f"  SKIP w={w} (degenerate)")
            continue
        subs = gp.subfield_degrees(co)
        if 8 not in subs:
            print(f"  SKIP w={w} (not 8x3: subs={subs})")
            continue
        line = submission.poly_line(co)
        src = f"zeta15:{''.join(map(str, w))}"
        rec[line] = {"source": src}
        cands.append((line, f"C-kummer3:{src}"))
        print(f"  {src}: 8x3 ok, subs={subs}")
    REC.parent.mkdir(parents=True, exist_ok=True)
    REC.write_text(json.dumps(rec, indent=2))
    return cands


def report():
    if not REC.exists():
        return
    rec = json.loads(REC.read_text())
    cache = db.cache_load()
    print("\n  Magma labels (8x3 degree-24 groups):")
    for line, info in rec.items():
        res = cache.get(line) or {}
        lab = res.get("label") or "(pending)"
        r = res.get("r")
        print(f"    {info['source']:>16}: {lab}" + (f"  r={r}" if r is not None else ""))


def main():
    print("collect (drain pending):", engine.collect())
    print("build:")
    cands = build()
    sid = engine.submit(cands, description="q19 size-3 cyclotomic Kummer (8x3, zeta_15)")
    print(f"submitted: {sid or '(nothing new)'}")
    print("collect:", engine.collect())
    report()


if __name__ == "__main__":
    main()
