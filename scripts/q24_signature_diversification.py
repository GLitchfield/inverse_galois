"""q24 — signature diversification via totally-real base fields.

Most of our constructions use complex bases (cyclotomic / resolvent), giving r=0 only. Over a
TOTALLY REAL base F, K = F(sqrt alpha) has real-root count r = 2 * #{real places where
alpha > 0}, so the SAME group (same kernel/valuation pattern) appears at many r — and
alpha -> -alpha flips every sign, giving r <-> 24-r. This is how to reach undiscovered
(t, r>0) signatures of groups we can build.

Base: the degree-12 totally-real subfield of Q(zeta_73) (a real C_12 field; the order-6
subgroup of C_72 contains complex conjugation, so the degree-12 fixed field is totally real),
h=1, split prime q=137.

Demonstrated: the C_12-top kernel family, realized at r in {8,12,16} (vs r=0 from Q(zeta_13)).
Run: uv run python scripts/q24_signature_diversification.py
"""

from __future__ import annotations

import json
from pathlib import Path

from igp import engine, gap, gp, submission

REC = Path(__file__).resolve().parents[1] / "data/processed/q24_records.json"
Q = 137
PATTERNS = [
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
]


def construct(cs, reg_w, q, sign):
    """K = F(sqrt(sign*alpha)) for pattern reg_w; returns (num_real_roots r, coeffs)."""
    idx = [j + 1 for j, x in enumerate(reg_w) if x]
    terms = "*".join(f"Mod(subst(pil,'y,cj[{a}]),f)" for a in idx)
    body = (
        f"f=Pol({cs},'y);bnf=bnfinit(f);cj=nfgaloisconj(f);\n"
        f"pi=nfbasistoalg(bnf,bnfisprincipal(bnf,idealprimedec(bnf,{q})[1])[2]);pil=lift(pi);\n"
        f"al=lift({terms})*({sign});\n"
        "K=polredbest(rnfequation(f,'x^2 - al));\n"
        "print(polsturm(K));print(Vec(K));"
    )
    out = gp.script(body, timeout=300).replace("\\\n", "")
    lines = [ln for ln in out.splitlines() if ln.strip()]
    return int(lines[0]), [int(x) for x in lines[-1].strip("[]").split(",")][::-1]


def build():
    base = gp.polsubcyclo(73, 12)
    cs = base[::-1]
    reg = gp.galois_action_perms(base)
    rec, cands = {}, []
    for w in PATTERNS:
        lab = gap.kernel_label_perms(w, reg)
        for sign in (1, -1):
            r, co = construct(cs, w, Q, sign)
            if len(co) != 25 or co[-1] != 1:
                continue
            line = submission.poly_line(co)
            src = f"realC12:{lab}:r{r}"
            rec[line] = {"label": lab, "r": r, "source": src}
            cands.append((line, f"sigdiv:{src}"))
            print(f"  {lab} sign{sign}: r={r}")
    REC.parent.mkdir(parents=True, exist_ok=True)
    REC.write_text(json.dumps(rec, indent=2))
    return cands


def main():
    print("collect (drain pending):", engine.collect())
    cands = build()
    rs = sorted({(v["label"], v["r"]) for v in json.loads(REC.read_text()).values()})
    print(f"realized {len(rs)} distinct (t,r); r values: {sorted({r for _, r in rs})}")
    sid = engine.submit(cands, description="signature diversification (real C12 base)")
    print(f"submitted: {sid or '(nothing new)'}")
    print("collect:", engine.collect())


if __name__ == "__main__":
    main()
