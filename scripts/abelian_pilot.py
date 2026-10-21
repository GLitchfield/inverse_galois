"""PILOT: class-field-theory abelian-kernel producer (the generalization of general_c2).

``gp.abelian_kernel`` builds a deg-24 field as a C_n cyclic RAY CLASS FIELD over a deg-(24/n) base
-- the pure-PARI version of Klüners-Malle systematic construction, reaching solvable minblk=3
(C3/deg8) and minblk=4 (C4/deg6) strata the C2-tower can't. This enqueues a BOUNDED pilot batch
(LOCAL-GATED: deg24 + irreducible + nfdisc-smooth, all enforced inside abelian_kernel) for SAIR to
label. Per the evidence ladder we scale to a wired producer only AFTER PILOT-LABELED (SAIR labels
match a target + the pair is open). Cursored over the disc-ordered mirror (idempotent-ish).

Run: uv run python scripts/abelian_pilot.py [--per N] [--bases M] [--treal]
"""

from __future__ import annotations

import argparse

from igp import gp, lmfdb
from igp import searchstore as store

# (base degree, kernel degree) -> deg-24; validated LOCAL-GATED (C4/deg6 minblk4, C3/deg8 minblk3).
RECIPES = [(6, 4), (8, 3)]


def run(per_recipe: int, bases_per_recipe: int, treal: bool) -> int:
    store.init()
    added = 0
    for deg, n in RECIPES:
        ckey = f"abelian_pilot_{deg}_{n}_off" + ("_tr" if treal else "")
        off = int(store.get_kv(ckey, 0))
        try:
            bases = lmfdb.fields(deg, class_number=None, per_group=2, limit=bases_per_recipe,
                                 offset=off, max_r2=0 if treal else None)
        except Exception as e:  # noqa: BLE001 -- boundary: LMFDB mirror
            print(f"d{deg}c{n}: lmfdb error {e}")
            continue
        got = 0
        for coeffs, label, _disc, _h in bases:
            if got >= per_recipe:
                break
            try:
                res = gp.abelian_kernel(coeffs, n, hi_modulus=60)
            except Exception:  # noqa: BLE001 -- boundary: gp subprocess
                res = None
            if not res:
                continue
            co, r = res
            tr = "tr" if treal else "g"
            tag = f"abelian:d{deg}c{n}{tr}:{label}.r{r}:off{off}i{got}"
            if store.enqueue("ready", {"coeffs": co}, target=tag):
                added += 1
                got += 1
                print(f"  + d{deg}c{n} base={label} r={r} -> {tag}")
        store.set_kv(ckey, off + bases_per_recipe)
    # keep the pilot claimable but not dominant until PILOT-LABELED confirms value
    store.set_priority_prefix("abelian:", 60.0)
    print(f"abelian PILOT: enqueued {added} (treal={treal})")
    return added


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=8, help="candidates to enqueue per recipe")
    ap.add_argument("--bases", type=int, default=40, help="bases to scan per recipe")
    ap.add_argument("--treal", action="store_true", help="totally-real bases (high-r open pairs)")
    a = ap.parse_args()
    run(a.per, a.bases, a.treal)
