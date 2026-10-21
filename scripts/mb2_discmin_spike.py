"""DISC-MIN DEFENSE spike (2026-07-13): can we match a rival's disc on held minblk=2 pairs?

Finding: we hold the disc-min on only 562 of ~22,555 pairs; a rival beats our disc on 22,029
(~118 pts recoverable). Our disc-behind pairs are gen12 (general_c2 over NON-Galois deg-12 bases)
built with LARGE split primes + NON-minimal bases. Since disc(K) ~ disc(K0)^2 * q^|w|, the lever is
smallest-disc base of the SAME 12Tj label + smallest completely-split prime + smallest subset w.

The catch is group-preservation (the 24Tt depends on alpha's square class), so we can't just swap
q. This spike, per held pair, uses our held poly's Frobenius cycle-type distribution as the
REFERENCE (a known-good realization -> no GAP labeling), then re-sweeps (smallest base, small q,
small w), keeps only deg-24/irred/polsturm==r candidates whose distribution L1-matches the
reference, and reports the SMALLEST disc vs ours vs the rival minDisc. Proof = several beat ours.

Run: uv run python scripts/mb2_discmin_spike.py
"""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mb2ns_producer import poly_dist  # noqa: E402  -- reuse the Frobenius tally

from igp import coverage, gp, lmfdb  # noqa: E402

PROG = json.loads((Path(__file__).resolve().parents[1]
                   / "data/processed/progress.json").read_text())


def l1(a: dict, b: dict) -> float:
    keys = set(a) | set(b)
    na, nb = sum(a.values()) or 1, sum(b.values()) or 1
    return sum(abs(a.get(k, 0) / na - b.get(k, 0) / nb) for k in keys)


def base_label_of(src: str) -> str | None:
    # daemon:gen12:12T148:d...:q...:w  -> 12T148
    for p in src.split(":"):
        if p.startswith("12T"):
            return p
    return None


def digits(n) -> int:
    return len(str(abs(int(n)))) if n else 0


# a spread of disc-behind held pairs (t, r) from the diagnostic
TARGETS = [("13862", "4"), ("8937", "4"), ("15714", "4"), ("3333", "0"), ("15746", "0")]


def spike_pair(t: str, r: str) -> dict:
    best = coverage.best_by_pair()
    b = best.get((t, r))
    if not b or not b.get("line"):   # best_by_pair records key the poly as "line"
        return {"pair": f"{t},{r}", "skip": "no held poly"}
    our_disc = abs(int(b["disc"])) if b.get("disc") else None
    lab = base_label_of(str(b.get("source", "")))
    md = PROG.get(f"{t},{r}", {}).get("minDisc")
    rival_dig = digits(md)
    ref, _ = poly_dist([int(x) for x in b["line"].split(",")])   # reference distribution

    if not lab:
        return {"pair": f"{t},{r}", "skip": f"no base label in {b.get('source', '')[:30]}"}
    try:
        bases = lmfdb.fields(12, galois_label=lab, class_number=None, limit=3)
    except Exception as e:  # noqa: BLE001
        return {"pair": f"{t},{r}", "skip": f"lmfdb {e}"}

    rr = int(r)
    matches = []
    for base_co, _l, _bdisc, _h in bases[:1]:         # smallest-disc base of the same 12Tj
        try:
            qs = gp.split_primes(base_co, 12, k=4, hi=4000)   # SMALL split primes
        except Exception:  # noqa: BLE001
            qs = []
        for q in qs[:3]:
            for size in (2, 4, 6):                     # small subsets first (smaller disc)
                for w_idx in list(combinations(range(12), size))[:18]:
                    w = [1 if i in w_idx else 0 for i in range(12)]
                    try:
                        co = gp.general_c2(base_co, w, q)
                    except Exception:  # noqa: BLE001
                        co = []
                    if not co or len(co) != 25:
                        continue
                    try:
                        if gp.real_roots(co) != rr:
                            continue
                    except Exception:  # noqa: BLE001
                        continue
                    d = gp.scoreable_disc(co)
                    if d is None or (our_disc and abs(d) >= our_disc):
                        continue                        # must improve on our current disc
                    cand, _ = poly_dist(co)
                    if l1(cand, ref) < 0.30:            # same group as our known-good poly
                        matches.append((digits(d), abs(d), co, l1(cand, ref), q, size))
        if matches:
            break                                       # smallest base already gave hits
    matches.sort()
    out = {"pair": f"24T{t},{r}", "base": lab, "our_dig": digits(our_disc),
           "rival_dig": rival_dig, "n_match": len(matches)}
    if matches:
        best_dig, _absd, _co, l1v, q, size = matches[0]
        out["best_dig"] = best_dig
        out["beats_rival"] = best_dig <= rival_dig
        out["via"] = f"q{q} |w|{size} L1={l1v:.3f}"
    return out


def main():
    print(f"{'pair':>14} {'base':>8} {'ourD':>5} {'rivalD':>7} {'bestD':>6} {'beats?':>7} via")
    for t, r in TARGETS:
        o = spike_pair(t, r)
        if o.get("skip"):
            print(f"{o['pair']:>14}  SKIP {o['skip']}")
            continue
        bd = o.get("best_dig", "-")
        beats = o.get("beats_rival", "-")
        via = o.get("via", "(no match)")
        print(f"{o['pair']:>14} {o['base']:>8} {o['our_dig']:>5} {o['rival_dig']:>7} "
              f"{str(bd):>6} {str(beats):>7} {via}")


if __name__ == "__main__":
    main()
