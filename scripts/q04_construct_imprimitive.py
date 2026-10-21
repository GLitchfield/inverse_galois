"""q04 — first non-baseline batch: imprimitive degree-24 fields via compositum.

Each candidate is a compositum of smaller irreducible fields, so it has proper
subfields (=> imprimitive) and a moderate/large product-action group LMFDB almost
certainly lacks (=> likely non-baseline = 1.0 each). The construction guarantees an
irreducible degree-24 integer polynomial; Magma returns the authoritative 24Tt.
Submits the whole batch in ONE POST and reports label / inBaseline / score per poly.

Run: uv run python scripts/q04_construct_imprimitive.py   (SUBMITS to the live API)
"""

from __future__ import annotations

import json
import time

import requests

from igp import gp, sair, submission

# ascending integer coeffs of the factor polynomials (all irreducible)
X2_2, X2_3, X2_5 = [-2, 0, 1], [-3, 0, 1], [-5, 0, 1]
X3 = [-1, -1, 0, 1]                       # x^3 - x - 1  (S_3)
X4 = [-1, -1, 0, 0, 1]                    # x^4 - x - 1  (S_4)
X6 = [-1, -1, 0, 0, 0, 0, 1]             # x^6 - x - 1  (S_6)
X8 = [-1, -1, 0, 0, 0, 0, 0, 0, 1]       # x^8 - x - 1  (S_8)

BATCH = {
    "2x3x4  (~C2xS3xS4)": [X2_2, X3, X4],
    "4x6    (~S4xS6)": [X4, X6],
    "3x8    (~S3xS8)": [X3, X8],
    "2x2x2x3(~C2^3xS3)": [X2_2, X2_3, X2_5, X3],
}


def main() -> None:
    cands = []  # (name, line, r)
    for name, factors in BATCH.items():
        try:
            coeffs, r = gp.compositum(factors)
        except gp.CASError as e:
            print(f"skip {name}: {e}")
            continue
        if len(coeffs) != 25:
            print(f"skip {name}: degree {len(coeffs) - 1}")
            continue
        line = submission.poly_line(coeffs)
        if len(line) > 20000:
            print(f"skip {name}: line too big ({len(line)} bytes)")
            continue
        cands.append((name, line, r))
        print(f"built {name}: deg 24, r={r}, {len(line)} bytes")

    if not cands:
        print("no candidates")
        return

    sess = requests.Session()
    sess.headers.update({"Authorization": f"Bearer {sair.api_key()}",
                         "Accept": "application/json", "User-Agent": "igp/0.0.1"})
    url = f"{sair.BASE}/competitions/igp24/submissions"
    desc = "Imprimitive degree-24 fields via compositum of smaller fields."
    body = {"payload": {"polynomials": [c[1] for c in cands]}, "meta": {"description": desc}}
    j = sess.post(url, json=body, timeout=300).json()
    if not j.get("ok"):
        print("submit error:", json.dumps(j)[:500])
        return
    sid = j["data"]["submissionId"]
    print(f"\nsubmitted {sid}: queued {len(j['data']['payload'].get('queuedPolynomials', []))}")

    for _ in range(10):
        time.sleep(8)
        me = sess.get(f"{sair.BASE}/competitions/igp24/submissions/me", timeout=60).json()
        item = next(x for x in me["data"]["items"] if x["submissionId"] == sid)
        if item["payload"].get("queuedPolynomials"):
            continue
        json.dump(item, open("data/raw/sair_submission_q04.json", "w"), indent=2)
        print("\nRESULTS:")
        for v in item.get("verifiedPolynomials", []):
            i = v["polynomialIndex"]
            print(f"  [{cands[i][0]}] {v['label']} r={v['r']} inBaseline={v['inBaseline']} "
                  f"scoreable={v.get('scoreable')} status={v.get('scoringStatus')} "
                  f"reason={v.get('scoringReason')}")
        for f in item.get("failedPolynomials", []):
            print(f"  [{cands[f['polynomialIndex']][0]}] FAILED: {f['reason']}")
        return
    print("still queued after polling; check /submissions/me later")


if __name__ == "__main__":
    main()
