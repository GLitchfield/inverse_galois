"""q06 — G2 wreath sweep: composition f(g(x)) -> Gal(g) wr Gal(f).

f(g(x)) (outer f deg b, inner g deg a) is irreducible of degree a*b with the
imprimitive wreath group Gal(g) wr Gal(f) (b blocks of size a) -- larger than the
compositum's direct-product action, reliably non-baseline, and cheap (pure
substitution). We cross degree splits a*b=24 over a palette of small fields, plus a
few iterated towers, and submit one batch. Magma returns the labels.

Run: uv run python scripts/q06_g2_wreath.py   (SUBMITS to the live API)
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import requests
import sympy

from igp import polys as P
from igp import sair, submission

PAL = {
    2: {"C2": [-2, 0, 1]},
    3: {"C3": [-1, -3, 0, 1], "S3": [-1, -1, 0, 1]},
    4: {"C4": [1, 1, 1, 1, 1], "V4": [1, 0, 0, 0, 1], "D4": [-2, 0, 0, 0, 1],
        "A4": [12, 8, 0, 0, 1], "S4": [-1, -1, 0, 0, 1]},
    6: {"C6": [1, 1, 1, 1, 1, 1, 1], "S6": [-1, -1, 0, 0, 0, 0, 1]},
    8: {"S8": [-1, -1, 0, 0, 0, 0, 0, 0, 1]},
    12: {"S12": [-1, -1] + [0] * 10 + [1]},
}
SPLITS = [(2, 12), (3, 8), (4, 6), (6, 4), (8, 3), (12, 2)]  # (inner deg a, outer deg b)
REALIZED = Path(__file__).resolve().parents[1] / "data" / "targets" / "realized.csv"


def comp(inner, outer):
    """outer(inner(x)) -> ascending int coeffs."""
    x = P.z
    gi = sum(c * x**i for i, c in enumerate(inner))
    fo = sum(c * x**i for i, c in enumerate(outer))
    p = sympy.Poly(sympy.expand(fo.subs(x, gi)), x)
    return [int(c) for c in p.all_coeffs()[::-1]]


def candidate(coeffs, source):
    if len(coeffs) != 25:
        return None
    try:
        return (source, submission.poly_line(coeffs))
    except submission.SubmissionError:
        return None


def build():
    out, seen = [], set()
    for a, b in SPLITS:
        for gn, g in PAL[a].items():
            for fn, f in PAL[b].items():
                c = candidate(comp(g, f), f"{fn}wr{gn}")
                if c and c[1] not in seen:
                    seen.add(c[1])
                    out.append(c)
    # a few iterated towers (deg 2*3*4 = 24)
    for fn, f in PAL[4].items():
        c = candidate(comp(comp(PAL[2]["C2"], PAL[3]["S3"]), f), f"{fn}wrS3wrC2")
        if c and c[1] not in seen:
            seen.add(c[1])
            out.append(c)
    return out


def main() -> None:
    cands = build()
    print(f"built {len(cands)} wreath candidates")
    sess = requests.Session()
    sess.headers.update({"Authorization": f"Bearer {sair.api_key()}",
                         "Accept": "application/json", "User-Agent": "igp/0.0.1"})
    url = f"{sair.BASE}/competitions/igp24/submissions"
    desc = "G2 wreath sweep: f(g(x)) -> Gal(g) wr Gal(f), imprimitive degree-24."
    body = {"payload": {"polynomials": [c[1] for c in cands]}, "meta": {"description": desc}}
    j = sess.post(url, json=body, timeout=300).json()
    if not j.get("ok"):
        print("submit error:", json.dumps(j)[:400])
        Path("data/raw/q06_lines.json").write_text(json.dumps([c[1] for c in cands]))
        return
    sid = j["data"]["submissionId"]
    print("submitted", sid)
    item = None
    for _ in range(10):
        time.sleep(15)
        me = sess.get(f"{sair.BASE}/competitions/igp24/submissions/me?limit=100", timeout=60).json()
        item = next(x for x in me["data"]["items"] if x["submissionId"] == sid)
        if not item["payload"].get("queuedPolynomials"):
            break
    nb = 0
    with REALIZED.open("a", newline="") as fh:
        w = csv.writer(fh)
        for v in (item or {}).get("verifiedPolynomials", []):
            src, line = cands[v["polynomialIndex"]]
            w.writerow([v["label"], v["t"], v["r"], v.get("scoreable"), v["inBaseline"], src, line])
            nb += 0 if v["inBaseline"] else 1
    nver = len((item or {}).get("verifiedPolynomials", []))
    nfail = len((item or {}).get("failedPolynomials", []))
    print(f"verified={nver} non_baseline={nb} failed={nfail}")
    Path("data/raw/sair_submission_q06.json").write_text(json.dumps(item or {}, indent=2))


if __name__ == "__main__":
    main()
