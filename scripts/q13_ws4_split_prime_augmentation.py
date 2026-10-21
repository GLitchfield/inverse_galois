"""q13 — WS4 (a): reach the AUGMENTATION kernel via a split prime (top C_12).

In F = Q(zeta_13), the prime q = 53 (= 1 mod 13) splits completely into 12 primes,
permuted as a 12-cycle by sigma: zeta -> zeta^2 (2 is a primitive root mod 13).
Let pi generate one prime above 53 (h(F)=1, so principal); set

    alpha = pi * sigma(pi).

Each conjugate sigma^i(alpha) then has 53-valuation pattern e_i + e_{i+1}; the only
F_2-relation among the conjugate square-classes is the all-ones vector (since
N(alpha) = 53^2 is a square), so the kernel is the augmentation (sum-zero, dim 11)
=> predicted 24T12727. Build K = F(sqrt(alpha)) and confirm with Magma.

Run: uv run python scripts/q13_ws4_split_prime_augmentation.py   (SUBMITS)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from igp import gp, sair, submission, verify

GP_BODY = r"""
F = polcyclo(13, 'y);
bnf = bnfinit(F);
P = idealprimedec(bnf, 53)[1];
g = nfbasistoalg(bnf, bnfisprincipal(bnf, P)[2]);
sg = Mod(subst(lift(g), 'y, 'y^2), F);
al = lift(g * sg);
print(Vec(rnfequation(F, 'x^2 - al)))
"""


def main() -> None:
    out = gp.script(GP_BODY, timeout=300)
    coeffs = [int(x) for x in out.strip("[]").split(",")][::-1]  # ascending
    if len(coeffs) != 25:
        print(f"got degree {len(coeffs)-1}, expected 24 — aborting")
        return
    fp = verify.local_fingerprint(coeffs)
    print(f"built K = Q(zeta_13)(sqrt(pi*sigma(pi))): degree 24, "
          f"A24={fp['in_a24']} subfields={fp['subfield_degrees']} #cyc={len(fp['cycle_types'])}")
    line = submission.poly_line(coeffs)

    sess = requests.Session()
    sess.headers.update({"Authorization": f"Bearer {sair.api_key()}",
                         "Accept": "application/json", "User-Agent": "igp/0.0.1"})
    url = f"{sair.BASE}/competitions/igp24/submissions"
    desc = "WS4 split-prime augmentation: Q(z13)(sqrt(pi*sigma(pi))), predict 24T12727."
    body = {"payload": {"polynomials": [line]}, "meta": {"description": desc}}
    j = sess.post(url, json=body, timeout=300).json()
    if not j.get("ok"):
        print("submit error:", json.dumps(j)[:400])
        return
    sid = j["data"]["submissionId"]
    for _ in range(15):
        time.sleep(12)
        me = sess.get(f"{sair.BASE}/competitions/igp24/submissions/me?limit=100", timeout=60).json()
        it = next(x for x in me["data"]["items"] if x["submissionId"] == sid)
        if not it["payload"].get("queuedPolynomials"):
            for v in it.get("verifiedPolynomials", []):
                ok = "MATCH" if v["label"] == "24T12727" else "MISMATCH"
                print(f"Magma: {v['label']} r={v['r']} inBaseline={v['inBaseline']} "
                      f"scoreable={v.get('scoreable')}  vs predicted 24T12727: {ok}")
            for f in it.get("failedPolynomials", []):
                print("FAILED:", f["reason"])
            Path("data/raw/sair_submission_q13.json").write_text(json.dumps(it, indent=2))
            return
    print("still queued; re-poll later")


if __name__ == "__main__":
    main()
