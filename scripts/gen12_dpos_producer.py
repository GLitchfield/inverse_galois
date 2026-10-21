"""gen12 delta>0 TOTALLY-POSITIVE producer -- open sub-wreath breadth (dive #39, test 00NN).

Dive #39 thesis: the OPEN proper-sub-wreath minblk=2 groups (24T9641/9642/14616/19246/20699 at
r=24) live over delta>0 degree-12 bases (h+ > 1). ``general_c2_totpos`` builds a DETERMINISTIC r=24
field K = F(sqrt(alpha)) with alpha totally positive; over a delta>0 base its per-alpha sign-lattice
solve is solvable only on the NARROWLY-PRINCIPAL classes -> a PROPER F2[H]-submodule -> a
smaller-kernel proper sub-wreath group (the open target), whereas the delta=0 (h+=1) bases the
existing ``gen12_totpos_producer`` keeps land the MAX wreath (the least useful). So this producer
INVERTS that gate: it keeps h+ > 1 bases and skips h+ = 1.

Unlike the blind ``general_c2`` mb2 sweep (test 0061, which only landed 9633 cleanly), this both
forces r=24 (totpos) AND density-gates each candidate against the 7 known GAP distributions
(``mb2ns/gdist.json``), so a candidate is only kept if its Frobenius fingerprint matches the SPECIFIC
open target 24Tt (L1 < 0.35, 0 impossible cycle types) -- not merely a wreath neighbor.

PILOT-first (evidence ladder, project review 2026-07-11): this enqueues a SMALL pilot; SAIR's Magma
label is the authoritative gate. Do not mass-build until an official label confirms a target hit.

Reuses ``poly_dist`` / ``density_label`` / ``_pats`` / ``TARGETS`` from ``mb2ns_producer``.

Usage:
    .venv/bin/python scripts/gen12_dpos_producer.py                 # dry run
    .venv/bin/python scripts/gen12_dpos_producer.py --enqueue --max-enqueue 5
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from igp import baseline, db, gp  # noqa: E402
from igp import lmfdb  # noqa: E402
from igp import searchstore as store  # noqa: E402
from mb2ns_producer import (  # noqa: E402
    GDIST, L1_THRESH, TARGETS, _base_targets, _pats, density_label,
)

PROG = ROOT / "data" / "processed" / "progress.json"


def _open_r24(base_ts, prog, held_pairs):
    """(t,24) among these tops that are teamCount==0, non-baseline, unheld -> genuine sole-1.0."""
    need = set()
    for t in base_ts:
        if 24 not in TARGETS[t]["rs"]:
            continue
        e = prog.get(f"{t},24", {})
        if e.get("teamCount", 9) != 0:
            continue
        if baseline.is_baseline(t, 24) or (t, 24) in held_pairs:
            continue
        need.add((t, 24))
    return need


def dpos_bases(top, lim, hplus_timeout):
    """delta>0 bases of ``top``: totally-real, class_number=1, but h+ > 1 (skip h+ == 1)."""
    raw = lmfdb.fields(12, galois_label=top, max_r2=0, class_number=1, limit=lim)
    out = []
    for coeffs, label, disc, _h in raw:
        try:
            hplus = gp.narrow_class_number(coeffs, timeout=hplus_timeout)
        except Exception:  # noqa: BLE001
            continue
        if hplus == 1:  # delta=0 -> max-wreath only; skip
            continue
        out.append((coeffs, label, disc, hplus))
    return out


def sweep_top(top, gd, need, bases_lim, nq, max_win, max_gate, hplus_timeout):
    base_ts = _base_targets(top)
    winners = []
    n_gate = 0
    for coeffs, label, disc, hplus in dpos_bases(top, bases_lim, hplus_timeout):
        if len(winners) >= max_win or n_gate >= max_gate:
            break
        try:
            qs = gp.split_primes(coeffs, 12, k=nq)
        except Exception:  # noqa: BLE001
            qs = []
        for q in qs:
            if len(winners) >= max_win or n_gate >= max_gate:
                break
            for w in _pats():
                if len(winners) >= max_win or n_gate >= max_gate:
                    break
                try:
                    c = gp.general_c2_totpos(coeffs, w, q)
                except Exception:  # noqa: BLE001
                    c = []
                if not c or len(c) != 25:
                    continue  # not split / narrowly non-principal / degenerate
                try:
                    if gp.real_roots(c) != 24:
                        continue  # totpos should force r=24; guard
                except Exception:  # noqa: BLE001
                    continue
                n_gate += 1
                t, l1, imp, n = density_label(c, gd)
                if t not in base_ts or l1 >= L1_THRESH or imp > 0:
                    continue
                if (t, 24) not in need:
                    continue
                sd = gp.scoreable_disc(c)
                if sd is None:
                    continue  # blank-risk disc
                wtag = "".join(map(str, w))
                src = f"hp{hplus}:d{disc}:q{q}:{wtag}"
                winners.append({"t": t, "r": 24, "coeffs": c, "l1": round(l1, 4),
                                "n": n, "src": src, "top": top, "disc": str(sd)})
                print(f"  WIN 24T{t} r=24 L1={l1:.4f} n={n} imp={imp} [{top} {src}]")
    return winners


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", default=None, help="restrict to one top (12T74/12T183/12T230/12T33)")
    ap.add_argument("--bases", type=int, default=8)
    ap.add_argument("--nq", type=int, default=2)
    ap.add_argument("--max-enqueue", type=int, default=5)
    ap.add_argument("--max-gate", type=int, default=30, help="cap density evals per top")
    ap.add_argument("--hplus-timeout", type=float, default=200.0)
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    raw = json.load(open(GDIST))
    gd = {str(t): raw[str(t)] for t in TARGETS}
    prog = json.loads(PROG.read_text())
    realized = db.load_realized()
    held_pairs = {(int(r["t"]), int(r["r"])) for r in realized
                  if str(r.get("label", "")).startswith("24T")}
    held_groups = {t for (t, _r) in held_pairs}

    # tops with a genuinely-open r=24 target (12T33's 9633.24 is rival-claimed as of build time)
    tops = [args.top] if args.top else ["12T74", "12T183", "12T230"]
    winners = []
    for top in tops:
        base_ts = _base_targets(top)
        need = _open_r24(base_ts, prog, held_pairs)
        print(f"# {top} -> targets {base_ts}  open r24 need {sorted(need)}")
        if not need:
            print(f"  (no open r24 target over {top}; skip)")
            continue
        winners += sweep_top(top, gd, need, args.bases, args.nq,
                             args.max_enqueue - len(winners), args.max_gate,
                             args.hplus_timeout)
        if len(winners) >= args.max_enqueue:
            break

    print(f"\ngen12_dpos: {len(winners)} density-gated r=24 winners")
    pairs = sorted({(w["t"], w["r"]) for w in winners})
    print(f"  distinct open pairs landed: {len(pairs)} -> {pairs}")

    if args.enqueue and winners:
        store.init()
        tiers = {"new": 130.0, "pair": 115.0, "alt": 100.0}
        added = {"new": 0, "pair": 0, "alt": 0}
        for w in winners[:args.max_enqueue]:
            t, r = w["t"], w["r"]
            tier = "alt" if (t, r) in held_pairs else ("pair" if t in held_groups else "new")
            tag = f"lit:gtp{tier}:{t}.{r}:{w['src']}"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": w["coeffs"]}, target=tag):
                added[tier] += 1
        for tier, pri in tiers.items():
            store.set_priority_prefix(f"lit:gtp{tier}", pri)
        print(f"  enqueued new {added['new']} @130, pair {added['pair']} @115, "
              f"alt {added['alt']} @100")


if __name__ == "__main__":
    main()
