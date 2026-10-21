"""q21 — non-solvable degree-24 via C_2-kernel over a non-solvable-top base (item C).

The big-top unlock (test 0015) made this possible: gp.general_c2 works over ANY degree-12
base, so a base with a NON-SOLVABLE top yields a non-solvable degree-24 group — the first
crack into the 807 non-solvable residual using the existing kernel machinery.

Base: F = the degree-12 A_5 field (top = A_5 on 12 points = cosets of a C_5, the icosahedral
12-vertex action), built as a RESOLVENT of the A_5 quintic x^5 + x^4 - 4x + 4 — a C_5-
invariant of the 5 roots evaluated over the 12 cosets (no degree-60 splitting field needed).
F has h=5, so general_c2's product-ideal path is required.

K = F(sqrt alpha) is degree 24 with a non-solvable Galois group (it surjects onto A_5).
Rerunnable: first run builds the base + constructs + submits; reruns report Magma labels
(and whether each is non-solvable).
Run: uv run python scripts/q21_nonsolvable.py
"""

from __future__ import annotations

import json
from itertools import permutations
from pathlib import Path

from igp import db, engine, gap, gp, submission

QUINTIC = "x^5 + x^4 - 4*x + 4"  # an A_5 quintic (disc = 1088^2)
BASE = Path(__file__).resolve().parents[1] / "data/processed/a5_base.json"
REC = Path(__file__).resolve().parents[1] / "data/processed/q21_records.json"
# h(F)=5: only patterns whose product ideal is principal are realizable (general_c2 skips
# the rest). These five are.
PATTERNS = [
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]


def _coset_reps():
    """12 left-coset reps of C_5 = <(0 1 2 3 4)> in A_5 (even perms of {0..4})."""
    def parity(p):
        seen = [False] * 5
        par = 0
        for i in range(5):
            if not seen[i]:
                j, c = i, 0
                while not seen[j]:
                    seen[j] = True
                    j = p[j]
                    c += 1
                par += c - 1
        return par % 2

    def comp(a, b):
        return tuple(a[b[i]] for i in range(5))

    c5 = (1, 2, 3, 4, 0)
    C5, x = [tuple(range(5))], c5
    while x != tuple(range(5)):
        C5.append(x)
        x = comp(c5, x)
    reps, seen = [], set()
    for g in (p for p in permutations(range(5)) if parity(p) == 0):
        coset = frozenset(comp(g, c) for c in C5)
        if coset not in seen:
            seen.add(coset)
            reps.append(g)
    return reps


def build_base():
    """Build the degree-12 A_5 base field as a C_5-coset resolvent of the quintic.

    theta = sum_i r[s(i)]*r[s(i+1)]^2 (a C_5-invariant, NOT reflection-invariant, so its
    A_5-stabilizer is exactly C_5) evaluated over the 12 cosets => degree-12 irreducible.
    """
    reps = [[i + 1 for i in r] for r in _coset_reps()]  # 1-indexed for gp
    reps_gp = "[" + ",".join("[" + ",".join(map(str, r)) + "]" for r in reps) + "]"
    body = (
        "default(realprecision, 250);\n"
        f"g = {QUINTIC}; r = polroots(g); reps = {reps_gp};\n"
        "th = vector(12, k, my(s=reps[k]); sum(i=1,5, r[s[i]]*r[s[i%5+1]]^2));\n"
        "res = prod(k=1,12, x - th[k]); co = round(real(Vec(res)));\n"
        "Q = polredbest(Polrev(Vecrev(co)));\n"
        "print(Vec(Q));"
    )
    line = next(ln for ln in gp.script(body, timeout=120).splitlines() if ln.startswith("["))
    coeffs = [int(x) for x in line.strip("[]").split(",")][::-1]
    q = find_split_prime(coeffs)
    BASE.parent.mkdir(parents=True, exist_ok=True)
    BASE.write_text(json.dumps({"coeffs": coeffs, "split_prime": q,
                                "top": "A5-on-12", "quintic": QUINTIC}))
    return coeffs


def find_split_prime(f_coeffs, lo=2, hi=4000):
    cs = [int(c) for c in f_coeffs][::-1]
    out = gp.script(
        f"f=Pol({cs},'y);bnf=bnfinit(f);"
        f"for(q={lo},{hi},if(isprime(q)&&#idealprimedec(bnf,q)==12,print(q);break));"
    )
    return int(out.strip()) if out.strip() else None


def build():
    base = json.loads(BASE.read_text())
    f = base["coeffs"]
    q = base.get("split_prime") or find_split_prime(f)
    print(f"  base degree {len(f) - 1}, split prime q={q}")
    rec, cands = {}, []
    for w in PATTERNS:
        co = gp.general_c2(f, w, q)
        if not co or len(co) != 25 or co[-1] != 1:
            print(f"  SKIP w={w} (failed/degenerate)")
            continue
        line = submission.poly_line(co)
        src = f"A5base:{''.join(map(str, w))}"
        rec[line] = {"source": src}
        cands.append((line, f"C-nonsolv:{src}"))
        print(f"  {src}: subs={gp.subfield_degrees(co)}")
    REC.parent.mkdir(parents=True, exist_ok=True)
    REC.write_text(json.dumps(rec, indent=2))
    return cands


def report():
    if not REC.exists():
        return
    rec = json.loads(REC.read_text())
    cache = db.cache_load()
    labels = []
    print("\n  Magma labels:")
    for line, info in rec.items():
        lab = (cache.get(line) or {}).get("label")
        print(f"    {info['source']:>14}: {lab or '(pending)'}")
        if lab:
            labels.append(int(lab[3:]))
    for t in labels:
        gi = gap.transitive_group_info(24, t)
        print(f"    24T{t}: order {gi['order']}  solvable={gi['solvable']}  <-- "
              + ("NON-SOLVABLE" if not gi["solvable"] else "solvable"))


def main():
    print("collect (drain pending):", engine.collect())
    if not BASE.exists():
        print("building A_5 base (resolvent of the quintic)...")
        build_base()
    print("build:")
    cands = build()
    sid = engine.submit(cands, description="q21 non-solvable degree-24 (C_2-kernel over A_5 base)")
    print(f"submitted: {sid or '(nothing new)'}")
    print("collect:", engine.collect())
    report()


if __name__ == "__main__":
    main()
