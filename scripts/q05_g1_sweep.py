"""q05 — G1 compositum sweep (group-diverse), batched submit, record coverage.

Distinct 24Tt come from distinct CONSTITUENT GROUPS (not distinct fields): we cross
a palette of small fields of known group at each degree with the degree-partitions
of 24, build composita (product-action imprimitive groups), and submit the batch.
Magma returns the authoritative labels; we record realized (t,r) -> data/targets/realized.csv.

Run: uv run python scripts/q05_g1_sweep.py   (SUBMITS to the live API)
"""

from __future__ import annotations

import csv
import json
import time
from itertools import product
from pathlib import Path

import requests

from igp import gp, sair, submission

# palette: degree -> [(group, ascending coeffs)] of small irreducible fields
PALETTE = {
    2: [("C2", [-2, 0, 1])],
    3: [("C3", [-1, -3, 0, 1]), ("S3", [-1, -1, 0, 1])],
    4: [("C4", [1, 1, 1, 1, 1]), ("V4", [1, 0, 0, 0, 1]), ("D4", [-2, 0, 0, 0, 1]),
        ("A4", [12, 8, 0, 0, 1]), ("S4", [-1, -1, 0, 0, 1])],
    6: [("C6", [1, 1, 1, 1, 1, 1, 1]), ("S6", [-1, -1, 0, 0, 0, 0, 1])],
    8: [("S8", [-1, -1, 0, 0, 0, 0, 0, 0, 1])],
}
PARTITIONS = [(4, 6), (2, 3, 4), (3, 8)]
REALIZED = Path(__file__).resolve().parents[1] / "data" / "targets" / "realized.csv"


def build_batch():
    cands = []  # (source, coeffs, r)
    for part in PARTITIONS:
        for combo in product(*[PALETTE[d] for d in part]):
            src = "+".join(g for g, _ in combo)
            try:
                coeffs, r = gp.compositum([c for _, c in combo])
            except gp.CASError:
                continue
            if len(coeffs) != 25:
                continue
            line = submission.poly_line(coeffs)
            if len(line) <= 20000:
                cands.append((f"{'x'.join(map(str, part))} {src}", line, r))
    return cands


def main() -> None:
    cands = build_batch()
    print(f"built {len(cands)} candidates")
    if not cands:
        return
    sess = requests.Session()
    sess.headers.update({"Authorization": f"Bearer {sair.api_key()}",
                         "Accept": "application/json", "User-Agent": "igp/0.0.1"})
    url = f"{sair.BASE}/competitions/igp24/submissions"
    desc = "G1 compositum sweep: product-action imprimitive degree-24 groups."
    body = {"payload": {"polynomials": [c[1] for c in cands]}, "meta": {"description": desc}}
    j = sess.post(url, json=body, timeout=300).json()
    if not j.get("ok"):
        print("submit error:", json.dumps(j)[:400])
        return
    sid = j["data"]["submissionId"]
    print("submitted", sid)

    item = None
    for _ in range(12):
        time.sleep(18)
        me = sess.get(f"{sair.BASE}/competitions/igp24/submissions/me", timeout=60).json()
        item = next(x for x in me["data"]["items"] if x["submissionId"] == sid)
        vs = item.get("verifiedPolynomials", [])
        if vs and all(v.get("scoringStatus") not in (None, "pending") for v in vs) \
                and not item["payload"].get("queuedPolynomials"):
            break

    new = REALIZED if REALIZED.exists() else None
    with REALIZED.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new is None:
            w.writerow(["label", "t", "r", "scoreable", "in_baseline", "source", "coeffs"])
        nscore = 0
        for v in (item or {}).get("verifiedPolynomials", []):
            src, line, _ = cands[v["polynomialIndex"]]
            w.writerow([v["label"], v["t"], v["r"], v.get("scoreable"), v["inBaseline"], src, line])
            nscore += 1 if v.get("scoreable") else 0
            print(f"  {v['label']} r={v['r']} scoreable={v.get('scoreable')} "
                  f"inBaseline={v['inBaseline']} [{src}]")
        nver = len((item or {}).get("verifiedPolynomials", []))
        nfail = len((item or {}).get("failedPolynomials", []))
        print(f"\nverified={nver} scoreable(now)={nscore} failed={nfail}")
    raw = Path(__file__).resolve().parents[1] / "data" / "raw" / "sair_submission_q05.json"
    json.dump(item, open(raw, "w"), indent=2)


if __name__ == "__main__":
    main()
