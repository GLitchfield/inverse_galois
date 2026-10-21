"""Abelian order-24 baseline-pair builder (24T1=C24, 24T2=C2xC12, 24T3=C2^2xC6).

The 2026-07-06 agenda listed 24T1/2/3 at r in {0,24} as "6 free sole-1.0s buildable NOW"
(abelian => a single cyclotomic-subfield line realizes each, no Magma-gate needed to KNOW the
group). This producer builds all six as their MINIMAL-discriminant abelian model and applies the
real scoreability gate.

FINDING (test 0047): all six are BASELINE pairs (in_baseline=True), not sole-1.0s. A baseline pair
scores ONLY via an exact nfdisc *strictly* < D_base (docs/competition_rules.md; igp.baseline). The
minimal-disc abelian field of each (group, signature) EQUALS D_base exactly -- LMFDB already holds
the global-minimum field for these classical tiny abelian groups -- so the best achievable is a TIE,
which does NOT unlock. Hence none of the six is winnable and the producer enqueues nothing. (The
prior `daemon:lit:abelian:1.24:zeta97` row in realized.csv is the same story: exact nfdisc, but
disc > D_base => scoreable=False.) Kept as a reusable, correctly-gated engine: if a genuinely
strict-beating abelian construction is ever found (or D_base moves), --enqueue will pick it up.

Each construction is a compositum of minimal-conductor cyclic pieces (conductor-discriminant
formula); the piece minima were established by a polsubcyclo enumeration (C3 TR cond7 disc49;
C8 TR cond17; C8 CM cond32 disc 2^31; C4 TR cond15; the CM C2xC12 is Q(zeta_35)).

Usage:
  python3 scripts/abelian_free.py            # build + gate + report (dry run)
  python3 scripts/abelian_free.py --enqueue  # additionally enqueue any STRICT beaters
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from igp import baseline, db, gp  # noqa: E402
from igp import searchstore as store  # noqa: E402
from igp import submission  # noqa: E402

PROGRESS = ROOT / "data" / "processed" / "progress.json"


def _q(m: int) -> list[int]:
    """Ascending coeffs of x^2 - m (the quadratic field Q(sqrt m); m<0 => imaginary)."""
    return [-m, 0, 1]


# Minimal-conductor cyclic building blocks (ascending coeffs), established by a polsubcyclo
# enumeration: C3 real cond7 disc49; C8 CM cond32 disc 2^31; C4 real cond15 disc1125.
C3_7 = [-1, -2, 1, 1]                           # x^3+x^2-2x-1
C8_CM32 = [2, 0, 16, 0, 20, 0, 8, 0, 1]         # x^8+8x^6+20x^4+16x^2+2
C4_TR15 = [1, 4, -4, -1, 1]                     # x^4-x^3-4x^2+4x+1


def _c8tr17() -> list[int]:
    return gp.polsubcyclo(17, 8)                # C8 real, conductor 17


def _zeta35() -> list[int]:
    out = gp.script("print(Vecrev(polredbest(polcyclo(35))));", timeout=120.0)
    return [int(x) for x in out.strip().strip("[]").split(",")]


# Each: minimal-disc model of (24Tt, r) as a compositum of coprime-ish cyclic pieces
# (conductor-discriminant formula). `pieces` is a callable returning the factor list, or a
# direct builder. Every one achieves disc == D_base (the global minimum for that group+signature).
CONSTRUCTIONS = [
    {"t": 1, "r": 24, "src": "C8tr17.C3_7",       "pieces": lambda: [_c8tr17(), C3_7]},
    {"t": 1, "r": 0,  "src": "C8cm32.C3_7",       "pieces": lambda: [C8_CM32, C3_7]},
    {"t": 2, "r": 24, "src": "C4tr15.Qsqrt21.C3_7", "pieces": lambda: [C4_TR15, _q(21), C3_7]},
    {"t": 2, "r": 0,  "src": "Qzeta35",           "direct": _zeta35},
    {"t": 3, "r": 24, "src": "Qsqrt2_3_7.C3_7",   "pieces": lambda: [_q(2), _q(3), _q(7), C3_7]},
    {"t": 3, "r": 0,  "src": "Qi_sqrt3_7.C3_7",   "pieces": lambda: [_q(-1), _q(3), _q(7), C3_7]},
]


def build_field(c: dict) -> list[int]:
    """Return ascending 25-coeff list of the polredbest'd degree-24 abelian field."""
    if "direct" in c:
        return c["direct"]()
    coeffs, _r = gp.compositum(c["pieces"](), reduce=True, timeout=200.0)
    return coeffs


def gate(coeffs: list[int], want_r: int) -> dict:
    """Local gates: degree, irreducibility, real-root count, exact scoring nfdisc, D_base."""
    g: dict = {}
    g["deg_ok"] = len(coeffs) == 25 and coeffs[-1] == 1 and coeffs[0] != 0
    g["irred"] = int(gp.script(f"print(polisirreducible(Pol({[int(c) for c in coeffs][::-1]})))")) == 1
    g["r"] = gp.real_roots(coeffs)
    g["r_ok"] = g["r"] == want_r
    g["disc"] = gp.scoreable_disc(coeffs)          # exact nfdisc if it completes in budget, else None
    g["scoreable_disc_ok"] = g["disc"] is not None
    return g


def load_progress() -> dict:
    try:
        return json.loads(PROGRESS.read_text())
    except Exception:
        return {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enqueue", action="store_true",
                    help="enqueue any construction that STRICTLY beats D_base (real unlock condition)")
    args = ap.parse_args()

    prog = load_progress()
    realized = db.load_realized()
    held_groups = {str(r["t"]) for r in realized if str(r.get("scoreable")).lower() == "true"}
    held_pairs = {(str(r["t"]), str(r["r"])) for r in realized
                  if str(r.get("scoreable")).lower() == "true"}

    if args.enqueue:
        store.init()
    tiers = {"new": 130.0, "pair": 115.0, "alt": 100.0}
    added = {"new": 0, "pair": 0, "alt": 0}
    beaters = 0

    for c in CONSTRUCTIONS:
        t, r, src = c["t"], c["r"], c["src"]
        key = f"{t},{r}"
        tc = (prog.get(key) or {}).get("teamCount")
        claimed = tc is not None and tc > 0
        db_val = baseline.d_base(str(t), str(r))
        try:
            coeffs = build_field(c)
        except Exception as e:
            print(f"24T{t} r={r} [{src}]: BUILD FAILED: {str(e)[:120]}")
            continue
        g = gate(coeffs, r)
        strict_beat = (g["disc"] is not None and db_val is not None and g["disc"] < db_val)
        margin = "n/a" if db_val is None or g["disc"] is None else \
            ("STRICT-BEAT" if g["disc"] < db_val else ("tie" if g["disc"] == db_val else "worse"))
        print(f"24T{t} r={r} [{src}]  tc={tc} claimed={claimed}  baseline={baseline.is_baseline(str(t), str(r))}")
        print(f"    deg_ok={g['deg_ok']} irred={g['irred']} r={g['r']}(want {r}) "
              f"scoreable_disc_ok={g['scoreable_disc_ok']}")
        print(f"    disc={g['disc']}  D_base={db_val}  -> {margin}")

        if not args.enqueue:
            continue
        if claimed:
            print("    SKIP enqueue: pair already claimed (teamCount>0)")
            continue
        if not (g["deg_ok"] and g["irred"] and g["r_ok"] and g["scoreable_disc_ok"]):
            print("    SKIP enqueue: failed a local gate")
            continue
        if baseline.is_baseline(str(t), str(r)) and not strict_beat:
            print("    SKIP enqueue: baseline pair NOT strictly beaten (tie/worse never unlocks)")
            continue
        beaters += 1
        tier = "alt" if (str(t), str(r)) in held_pairs else ("pair" if str(t) in held_groups else "new")
        line = submission.poly_line(coeffs)
        tag = f"lit:abel{tier}:{t}.{r}:{src}"
        if not store.has_target(tag) and store.enqueue("ready", {"coeffs": coeffs}, target=tag):
            added[tier] += 1
            print(f"    ENQUEUED {tag}  line={line[:60]}...")

    if args.enqueue:
        for tier, pri in tiers.items():
            store.set_priority_prefix(f"lit:abel{tier}", pri)
        print(f"\nenqueued: new={added['new']}@130 pair={added['pair']}@115 alt={added['alt']}@100 "
              f"(strict beaters found: {beaters})")
    else:
        print("\n(dry run; pass --enqueue to push STRICT beaters to the queue)")


if __name__ == "__main__":
    main()
