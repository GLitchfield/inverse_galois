"""q14 — WS4 exact A->w->alpha solver (top C_12): predict, construct, confirm.

The realized C_2-kernel is A = <H-shifts of w> (the ideal (w(x)) in F_2[x]/(x^12-1)),
so a single 0/1 pattern w is the knob. For several w we:
  (1) PREDICT the 24Tt of A x| C_12 from the group side (gap.kernel_label), and
  (2) CONSTRUCT K = Q(zeta_13)(sqrt(prod sigma^j(pi)^{w_j})) (gp.c2_split_construct),
  (3) CONFIRM with Magma that the constructed label == the prediction.
Given a target kernel A, w is just a generator of A — so this is the solver, exact.

Run: uv run python scripts/q14_ws4_kernel_solver.py   (SUBMITS the batch)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

from igp import gap, gp, sair, submission

W = {
    "single->full":  [1] + [0] * 11,
    "pair->aug":     [1, 1] + [0] * 10,
    "triple":        [1, 1, 1] + [0] * 9,
    "all->diag":     [1] * 12,
}


def main() -> None:
    print("GAP predictions (w -> label of <H-shifts of w> x| C_12):")
    preds = {}
    for name, w in W.items():
        preds[name] = gap.kernel_label(w, 1, 12)
        print(f"  {name:14s}: {preds[name]}")

    print("\nconstructing K = Q(zeta_13)(sqrt(alpha(w))) ...")
    cands = []
    for name, w in W.items():
        coeffs = gp.c2_split_construct(w)
        if len(coeffs) != 25:
            print(f"  {name}: degree {len(coeffs)-1} - skip")
            continue
        cands.append((name, submission.poly_line(coeffs)))

    sess = requests.Session()
    sess.headers.update({"Authorization": f"Bearer {sair.api_key()}",
                         "Accept": "application/json", "User-Agent": "igp/0.0.1"})
    url = f"{sair.BASE}/competitions/igp24/submissions"
    desc = "WS4 A->w->alpha solver: Q(z13)(sqrt(alpha(w))), various kernels."
    body = {"payload": {"polynomials": [c[1] for c in cands]}, "meta": {"description": desc}}
    j = sess.post(url, json=body, timeout=300).json()
    if not j.get("ok"):
        print("submit error:", json.dumps(j)[:400])
        return
    sid = j["data"]["submissionId"]
    item = None
    for _ in range(15):
        time.sleep(12)
        me = sess.get(f"{sair.BASE}/competitions/igp24/submissions/me?limit=100", timeout=60).json()
        item = next(x for x in me["data"]["items"] if x["submissionId"] == sid)
        if not item["payload"].get("queuedPolynomials"):
            break
    print("\nMagma vs GAP-prediction:")
    n_match = 0
    for v in (item or {}).get("verifiedPolynomials", []):
        name = cands[v["polynomialIndex"]][0]
        pred = preds[name]
        ok = v["label"] == pred
        n_match += ok
        print(f"  {name:14s}: Magma {v['label']:9s} pred {pred:9s} {'MATCH' if ok else 'MISMATCH'}")
    for f in (item or {}).get("failedPolynomials", []):
        print(f"  idx{f['polynomialIndex']} FAILED: {f['reason']}")
    print(f"\n{n_match}/{len(cands)} predictions confirmed by Magma")
    Path("data/raw/sair_submission_q14.json").write_text(json.dumps(item or {}, indent=2))


if __name__ == "__main__":
    main()
