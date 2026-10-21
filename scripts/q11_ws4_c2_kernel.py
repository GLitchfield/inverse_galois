"""q11 — WS4 C_2-kernel construction, proof of concept (top = C_12 = Q(zeta_13)).

K = F(sqrt(alpha)) with F = Q(zeta_13) (degree 12, Galois group C_12). Varying alpha
chooses the kernel A <= C_2^12: rational alpha -> tiny (diagonal) kernel; non-rational
alpha with varied conjugate square-classes -> larger kernel. We build each degree-24
K, read its local fingerprint (subfields should include 12 and 2; group changes with
alpha), and submit for Magma's authoritative 24Tt — demonstrating the construction +
kernel control end-to-end.

Run: uv run python scripts/q11_ws4_c2_kernel.py   (SUBMITS to the live API)
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

import requests

from igp import gp, sair, submission, verify

PHI13 = [1] * 13  # Phi_13 = 1 + y + ... + y^12  (Q(zeta_13), C_12)
ALPHAS = ["2", "3", "6", "y+1", "y-2", "y^2-2", "2*y+3"]
REALIZED = Path(__file__).resolve().parents[1] / "data" / "targets" / "realized.csv"


def main() -> None:
    cands = []  # (alpha, line, fingerprint)
    for a in ALPHAS:
        try:
            coeffs = gp.quadratic_ext(PHI13, a)
        except gp.CASError as e:
            print(f"alpha={a}: gp error {e}")
            continue
        if len(coeffs) != 25:
            print(f"alpha={a}: degree {len(coeffs)-1} (alpha square in F?) - skip")
            continue
        fp = verify.local_fingerprint(coeffs)
        if not fp["irreducible"]:
            print(f"alpha={a}: reducible - skip")
            continue
        line = submission.poly_line(coeffs)
        cands.append((a, line, fp))
        print(f"alpha={a:8s}: A24={fp['in_a24']} subfields={fp['subfield_degrees']} "
              f"#cycle-types={len(fp['cycle_types'])}")

    if not cands:
        return
    sess = requests.Session()
    sess.headers.update({"Authorization": f"Bearer {sair.api_key()}",
                         "Accept": "application/json", "User-Agent": "igp/0.0.1"})
    url = f"{sair.BASE}/competitions/igp24/submissions"
    desc = "WS4 C_2-kernel POC: Q(zeta_13)(sqrt(alpha)), top C_12."
    body = {"payload": {"polynomials": [c[1] for c in cands]}, "meta": {"description": desc}}
    j = sess.post(url, json=body, timeout=300).json()
    if not j.get("ok"):
        print("submit error:", json.dumps(j)[:400])
        return
    sid = j["data"]["submissionId"]
    item = None
    for _ in range(12):
        time.sleep(15)
        me = sess.get(f"{sair.BASE}/competitions/igp24/submissions/me?limit=100", timeout=60).json()
        item = next(x for x in me["data"]["items"] if x["submissionId"] == sid)
        if not item["payload"].get("queuedPolynomials"):
            break
    print("\nMagma labels (kernel control: distinct alpha -> distinct group):")
    with REALIZED.open("a", newline="") as fh:
        w = csv.writer(fh)
        for v in (item or {}).get("verifiedPolynomials", []):
            a, line, _ = cands[v["polynomialIndex"]]
            w.writerow([v["label"], v["t"], v["r"], v.get("scoreable"), v["inBaseline"],
                        f"WS4-C2 zeta13 sqrt({a})", line])
            print(f"  alpha={a:8s} -> {v['label']} r={v['r']} inBaseline={v['inBaseline']}")
        for fpoly in (item or {}).get("failedPolynomials", []):
            print(f"  idx{fpoly['polynomialIndex']} FAILED: {fpoly['reason']}")
    Path("data/raw/sair_submission_q11.json").write_text(json.dumps(item or {}, indent=2))


if __name__ == "__main__":
    main()
