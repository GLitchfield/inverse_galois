"""MINBLK=2 general_c2_TWIST producer -- the complement-cocycle engine (research dive #49).

`scripts/mb2_twist.py` screens bases and fingerprints the mixed-divisor radical; it stops at the
label. This script closes the loop: it screens, pre-filters each passing base's TOP against the
live board (a top whose dim-11 siblings are all contested / already held is not built at all),
builds the degree-24 field, LOCAL-GATES it, and enqueues.

The construction (dive #49):

    alpha = gen( P_{q,a} . P_{q,b} . prod_{p | d} P_p )   x  totally-positive unit twist

q completely split with an EVEN-weight divisor => the kernel is the dim-11 even-weight submodule;
the odd-residue-degree primes above d supply the norm character chi = Q(sqrt N(alpha)), which is
the complement cocycle that separates the TWISTED siblings from the split one (test 0067 showed a
pure split-prime radical lands the split sibling 497/497). The unit twist makes alpha totally
positive => the degree-24 field is totally real => r = 24 deterministically.

Enqueue gate (all must hold):
  * fingerprint L1 < 0.35 to a specific library group, runner-up margin > 0.15, kernel dim == 11;
  * (t, 24) teamCount == 0 and non-baseline in a FRESH progress.json;
  * zero rows for 24Tt in realized.csv (a landing we already hold is the SPLIT sibling);
  * degree 24, irreducible, polsturm == 24, gp.scoreable_disc non-blank.

Usage:
    .venv/bin/python scripts/mb2_twist_producer.py --limit 400            # screen + report
    .venv/bin/python scripts/mb2_twist_producer.py --bases 12T42 --enqueue
"""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import mb2_twist as tw  # noqa: E402

from igp import gp, lmfdb  # noqa: E402

OUT = ROOT / "data" / "processed" / "mb2twist"
KDIM = 11
MARGIN = 0.15


def held_groups() -> set:
    with open(ROOT / "data" / "targets" / "realized.csv") as fh:
        return {int(row["t"]) for row in csv.DictReader(fh) if row["t"]}


def screen_ds(lab: str, coeffs: list) -> list:
    out = tw.gp_run(tw.SCREEN + f'SCREEN("{lab}", {coeffs});\nquit\n')
    for ln in out.splitlines():
        if ln.startswith("SCREEN|"):
            return json.loads(ln.split("|")[5].replace(" ", "") or "[]")
    return []


def build_poly(coeffs: list, alpha: str, timeout: float = 900.0) -> list:
    """alpha arrives as a coordinate vector on the integral basis (nfeltmul's output form), NOT as
    a polynomial -- nfbasistoalg is what turns it back into an element of K0."""
    cs = ",".join(str(c) for c in coeffs[::-1])
    body = ("default(parisizemax,8*10^9);\n"
            f"f=Pol([{cs}],y); K=nfinit(f); al=lift(nfbasistoalg(K, {alpha}));\n"
            "r=rnfequation(f, x^2 - al);\n"
            "print(if(poldegree(r)<24, \"DEGENERATE\", Vec(polredbest(r))));")
    out = subprocess.run(["gp", "-q"], input=body, capture_output=True, text=True,
                         timeout=timeout).stdout
    if "DEGENERATE" in out or "[" not in out:
        return []
    return [int(x) for x in out.strip().strip("[]").split(",")][::-1]


def local_gate(c: list) -> tuple[bool, str]:
    """degree 24 + irreducible + polsturm == 24 + a scoreable (10^6-smooth) discriminant."""
    if len(c) != 25:
        return False, "degree"
    cs = ",".join(str(x) for x in c[::-1])
    out = subprocess.run(["gp", "-q"], capture_output=True, text=True, timeout=300,
                         input=f"p=Pol([{cs}]);print(poldegree(p),\"|\",polisirreducible(p),"
                               "\"|\",polsturm(p));").stdout.strip()
    deg, irr, rr = out.split("|")
    if int(deg) != 24 or int(irr) != 1:
        return False, "reducible"
    if int(rr) != 24:
        return False, f"r={rr}"
    if gp.scoreable_disc(c) is None:
        return False, "blank-risk disc"
    return True, "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=400, help="LMFDB deg-12 base pull size")
    ap.add_argument("--bases", type=str, default=None, help="comma list, e.g. 12T42,12T23")
    ap.add_argument("--ncand", type=int, default=3, help="radicals built per (base, d)")
    ap.add_argument("--pilot", type=int, default=5, help="max polys built + enqueued")
    ap.add_argument("--enqueue", action="store_true")
    args = ap.parse_args()

    fl = lmfdb.fields(12, max_r2=0, class_number=1, per_group=8, limit=args.limit)
    # several DISTINCT fields share a label; they screen differently (the twist d is a property of
    # the field's ramification, not of H), so every one of them is its own base.
    pool = [(label, list(coeffs)) for coeffs, label, _disc, _h in fl]
    keep = set(args.bases.split(",")) if args.bases else None
    pool = [(lab, cs) for lab, cs in pool if keep is None or lab in keep]
    held = held_groups()
    print(f"bases: {len(pool)} fields, {len({lab for lab, _ in pool})} labels")

    libs, winners, report = {}, [], []
    for lab, cs in pool:
        top = int(lab.split("T")[1])
        ds = screen_ds(lab, cs)
        if not ds:
            report.append(f"{lab}: no reachable d (no twist in the norm square-class group)")
            continue
        if top not in libs:
            libs[top] = tw.library(top)
        cts, dim = libs[top]
        # PRE-FILTER on the board: build only if this top carries a dim-11 sibling whose (t, 24) is
        # OPEN (open_rs = teamCount 0 AND non-baseline). "new" = we hold no row for the group at all
        # (the split sibling is exactly what the blind gen12 harvest already holds), "pair" = we hold
        # the group at another r but this signature is still open -- both score a sole 1.0.
        want = {t: ("pair" if t in held else "new")
                for t, k in dim.items() if k == KDIM and 24 in tw.open_rs(t)}
        report.append(f"{lab}: d={ds} lib={len(dim)} groups, open dim-{KDIM} at r=24: "
                      f"{want or 'NONE'}")
        print(report[-1])
        if not want:
            continue
        for d in ds:
            if len(winners) >= args.pilot:
                break
            code = tw.BUILD + f"NCAND = {args.ncand};\nBUILD({top}, {d}, {cs});\nquit\n"
            tallies, alphas = {}, {}
            for ln in tw.gp_run(code).splitlines():
                f = ln.strip().split("|")
                if f[0] == "FP":
                    tallies.setdefault(f[1], {})[f[2]] = int(f[3])
                elif f[0] == "CAND":
                    alphas[f[1]] = f[3]
            for cid, tally in tallies.items():
                if len(winners) >= args.pilot:
                    break
                best = tw.l1_label(tally, cts)
                l1, t = best[0]
                ok = (l1 < tw.L1_THRESH and best[1][0] - l1 > MARGIN and dim.get(t) == KDIM)
                flag = "GATED" if ok else "-"
                print(f"  {lab} d={d} {cid}: 24T{t} kdim={dim.get(t)} L1={l1:.3f} "
                      f"(next {best[1][0]:.3f}) open_r={tw.open_rs(t)} {flag}")
                if not ok or t not in want:
                    continue
                c = build_poly(cs, alphas[cid])
                if not c:
                    print("    BUILD-FAIL (degenerate)")
                    continue
                good, why = local_gate(c)
                if not good:
                    print(f"    LOCAL-GATE FAIL: {why}")
                    continue
                q, a, b = cid.split("_")
                winners.append({"t": t, "r": 24, "coeffs": c, "l1": round(l1, 4),
                                "tier": want[t], "src": f"base12T{top}:d{d}:q{q}_{a}{b}",
                                "disc": str(gp.scoreable_disc(c))})
                print(f"    WIN 24T{t} r=24 tier={want[t]} L1={l1:.3f} "
                      f"disc={winners[-1]['disc']}")

    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(winners, open(OUT / "winners.json", "w"), indent=1)
    (OUT / "screen_report.txt").write_text("\n".join(report) + "\n")
    print(f"\nmb2_twist_producer: {len(winners)} locally-gated candidates")

    if args.enqueue and winners:
        from igp import searchstore as store
        store.init()
        added = 0
        for w in winners:
            tag = f"lit:mb2twist{w['tier']}:{w['t']}.{w['r']}:{w['src']}"
            if not store.has_target(tag) and store.enqueue(
                    "ready", {"coeffs": w["coeffs"]}, target=tag):
                added += 1
        store.set_priority_prefix("lit:mb2twistnew", 130.0)
        store.set_priority_prefix("lit:mb2twistpair", 115.0)
        print(f"enqueued {added}. SAIR's Magma label is the authoritative gate.")


if __name__ == "__main__":
    main()
