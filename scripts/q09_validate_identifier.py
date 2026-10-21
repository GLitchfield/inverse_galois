"""q09 — validate the local Galois identifier (WS-INFRA-A) against Magma ground truth.

Our realized.csv pairs polynomials with Magma's authoritative 24Tt label. Run the
local identifier (verify.confirm_label) on a sample and check: (a) it CONFIRMS the
true label, and (b) it REJECTS a wrong label. GAP invariants are feasible for
moderate-order groups, so we sample order <= 5000 (the solvable mid-order frontier).

Run: uv run python scripts/q09_validate_identifier.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from igp import verify

ROOT = Path(__file__).resolve().parents[1]
MAX_ORDER = 5000
SAMPLE = 12


def main() -> None:
    order = {int(r["t"]): int(r["order"])
             for r in csv.DictReader(open(ROOT / "data/targets/transitive_groups_deg24.csv"))}
    seen, cands = set(), []
    for r in csv.DictReader(open(ROOT / "data/targets/realized.csv")):
        t = int(r["t"])
        if t in seen or order.get(t, 10**9) > MAX_ORDER:
            continue
        seen.add(t)
        cands.append((t, r["label"], [int(x) for x in r["coeffs"].split(",")]))
    cands = cands[:SAMPLE]
    print(f"validating {len(cands)} moderate-order labels (order <= {MAX_ORDER})\n")

    confirmed = rejected = 0
    for i, (t, label, coeffs) in enumerate(cands):
        fp = verify.local_fingerprint(coeffs)
        ok, checks = verify.confirm_label(coeffs, t, fingerprint=fp)
        wrong_t = cands[(i + 1) % len(cands)][0]  # a different label
        ok_w, _ = verify.confirm_label(coeffs, wrong_t, fingerprint=fp)
        confirmed += ok
        rejected += not ok_w
        verdict = "reject" if not ok_w else "ACCEPT!"
        flag = "" if ok and not ok_w else "  <-- shares invariants"
        print(f"{label:>8}: confirm={ok}  wrong-24T{wrong_t}:{verdict}  "
              f"A24={fp['in_a24']} subfields={fp['subfield_degrees']}{flag}")
    n = len(cands)
    print(f"\nconfirmed true label: {confirmed}/{n} | rejected wrong label: {rejected}/{n}")


if __name__ == "__main__":
    main()
