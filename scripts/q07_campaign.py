"""q07 — scaled G2 wreath campaign with an auto-discovered palette.

(1) Build a palette of small fields binned by Galois group (gp.scan_galois over
small poly families, deg 3/4/6/8; cached). (2) Generate G2 wreath candidates
f(g(x)) over all degree splits a*b=24 x the palette (pure sympy, fast). (3) Dedup
vs already-submitted lines in realized.csv. (4) Batch-submit in chunks of 100
(stops cleanly at the daily cap), poll labels, append realized.csv.

Re-runnable: each run submits the next chunks of fresh candidates.
Run: uv run python scripts/q07_campaign.py [max_chunks]
"""

from __future__ import annotations

import csv
import json
import sys
import time
from itertools import product
from pathlib import Path

import requests
import sympy

from igp import gp, sair, submission
from igp import polys as P

ROOT = Path(__file__).resolve().parents[1]
REALIZED = ROOT / "data" / "targets" / "realized.csv"
PAL_CACHE = ROOT / "data" / "processed" / "palette.json"

SEEDS = {  # ensure these groups are always present
    2: {"C2": [-2, 0, 1]},
    3: {"C3": [-1, -3, 0, 1], "S3": [-1, -1, 0, 1]},
    4: {"S4": [-1, -1, 0, 0, 1]},
    6: {"S6": [-1, -1, 0, 0, 0, 0, 1]},
    8: {"S8": [-1, -1, 0, 0, 0, 0, 0, 0, 1]},
    12: {"S12": [-1, -1] + [0] * 10 + [1]},
}
SPLITS = [(2, 12), (3, 8), (4, 6), (6, 4), (8, 3), (12, 2)]  # (inner a, outer b)


def mono(d, terms):
    c = [0] * (d + 1)
    c[d] = 1
    for p, v in terms.items():
        c[p] = v
    return c


def scan_families():
    fam = {3: [], 4: [], 6: [], 8: []}
    R = range(-3, 4)
    for a in R:
        for b in R:
            if b == 0:
                continue
            for d in fam:
                fam[d].append(mono(d, {1: a, 0: b}))
    for a in R:
        for b in R:
            if b == 0:
                continue
            fam[6].append(mono(6, {2: a, 0: b}))
            fam[6].append(mono(6, {4: a, 0: b}))
            fam[8].append(mono(8, {2: a, 0: b}))
            fam[8].append(mono(8, {4: a, 0: b}))
    for a in range(-2, 3):
        for b in range(-2, 3):
            for c in (-1, 1):
                fam[4].append(mono(4, {2: a, 1: b, 0: c}))
                fam[6].append(mono(6, {3: a, 1: b, 0: c}))
                fam[8].append(mono(8, {4: a, 2: b, 0: c}))
    return fam


def build_palette():
    if PAL_CACHE.exists():
        raw = json.loads(PAL_CACHE.read_text())
        return {int(d): v for d, v in raw.items()}
    pal = {d: dict(s) for d, s in SEEDS.items()}
    for d, fam in scan_families().items():
        groups = gp.scan_galois(fam)
        for idx, (_order, name, nreal) in groups.items():
            coeffs = fam[idx]
            key = f"{name}/r{nreal}"  # bin by (group, signature) -> signature-fill
            cur = pal[d].get(key)
            if cur is None or sum(map(abs, coeffs)) < sum(map(abs, cur)):
                pal[d][key] = coeffs
    # degree-12 constituents via compositum of smaller palette fields (new (2,12)/(12,2) family)
    for parts in [(2, 6), (3, 4)]:
        for combo in product(*[list(pal.get(d, {}).items()) for d in parts]):
            try:
                coeffs, _ = gp.compositum([c for _, c in combo])
            except gp.CASError:
                continue
            if len(coeffs) == 13:  # degree 12
                pal[12]["+".join(n for n, _ in combo)] = coeffs
    PAL_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PAL_CACHE.write_text(json.dumps({str(d): v for d, v in pal.items()}))
    return pal


def comp(inner, outer):
    x = P.z
    gi = sum(c * x**i for i, c in enumerate(inner))
    fo = sum(c * x**i for i, c in enumerate(outer))
    p = sympy.Poly(sympy.expand(fo.subs(x, gi)), x)
    return [int(c) for c in p.all_coeffs()[::-1]]


def gen_candidates(pal):
    out, seen = [], set()
    for a, b in SPLITS:
        for (gn, g), (fn, f) in product(pal.get(a, {}).items(), pal.get(b, {}).items()):
            try:
                coeffs = comp(g, f)
            except Exception:
                continue
            if len(coeffs) != 25:
                continue
            try:
                line = submission.poly_line(coeffs)
            except submission.SubmissionError:
                continue
            if len(line) <= 30000 and line not in seen:
                seen.add(line)
                out.append((f"{fn}wr{gn}", line))
    # G1: compositum (direct-product action) — one rep per group (sig-variants are a G2 lever)
    bygroup = {d: {} for d in pal}
    for d, ents in pal.items():
        for name, c in ents.items():
            bygroup[d].setdefault(name.split("/")[0], c)
    for part in [(4, 6), (3, 8), (2, 3, 4)]:
        for combo in product(*[list(bygroup.get(d, {}).items()) for d in part]):
            try:
                coeffs, _ = gp.compositum([c for _, c in combo])
            except gp.CASError:
                continue
            if len(coeffs) != 25:
                continue
            try:
                line = submission.poly_line(coeffs)
            except submission.SubmissionError:
                continue
            if len(line) <= 30000 and line not in seen:
                seen.add(line)
                out.append(("G1:" + "+".join(n for n, _ in combo), line))
    return out


def already_submitted():
    if not REALIZED.exists():
        return set()
    return {r["coeffs"] for r in csv.DictReader(open(REALIZED))}


def main() -> None:
    max_chunks = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    pal = build_palette()
    print("palette groups:", {d: len(v) for d, v in pal.items()})
    cands = gen_candidates(pal)
    done = already_submitted()
    fresh = [c for c in cands if c[1] not in done]
    print(f"candidates: {len(cands)} total, {len(fresh)} fresh")

    sess = requests.Session()
    sess.headers.update({"Authorization": f"Bearer {sair.api_key()}",
                         "Accept": "application/json", "User-Agent": "igp/0.0.1"})
    url = f"{sair.BASE}/competitions/igp24/submissions"
    total_nb = 0
    for ci in range(max_chunks):
        chunk = fresh[ci * 100:(ci + 1) * 100]
        if not chunk:
            break
        body = {"payload": {"polynomials": [c[1] for c in chunk]},
                "meta": {"description": "G2 wreath campaign chunk."}}
        j = sess.post(url, json=body, timeout=300).json()
        if not j.get("ok"):
            print(f"chunk {ci}: stop ({j.get('error', {}).get('code')})")
            break
        sid = j["data"]["submissionId"]
        item = None
        for _ in range(12):
            time.sleep(15)
            me = sess.get(f"{sair.BASE}/competitions/igp24/submissions/me?limit=100",
                          timeout=60).json()
            item = next(x for x in me["data"]["items"] if x["submissionId"] == sid)
            if not item["payload"].get("queuedPolynomials"):
                break
        with REALIZED.open("a", newline="") as fh:
            w = csv.writer(fh)
            for v in (item or {}).get("verifiedPolynomials", []):
                src, line = chunk[v["polynomialIndex"]]
                w.writerow([v["label"], v["t"], v["r"], v.get("scoreable"),
                            v["inBaseline"], src, line])
                total_nb += 0 if v["inBaseline"] else 1
        nver = len((item or {}).get("verifiedPolynomials", []))
        print(f"chunk {ci}: submitted {len(chunk)}, verified {nver}")
    print(f"non-baseline this run: {total_nb}")


if __name__ == "__main__":
    main()
