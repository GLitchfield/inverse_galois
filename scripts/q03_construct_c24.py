"""q03 — construct C_24 (24T1) candidates for its two open signatures.

24T1 = C_24 is realized as a cyclic subfield of a cyclotomic field (PARI
polsubcyclo): n=97 -> totally real (r=24), n=73 -> totally complex (r=0). The
group is C_24 by Galois theory (subfield of a cyclic cyclotomic extension); we
verify r, irreducibility, A_24 membership (C_24 is odd -> not in A_24), and the
Frobenius cycle-type fingerprint locally, and re-check the live leaderboard so we
don't prepare an already-solved signature.

Run: uv run python scripts/q03_construct_c24.py   (read-only; does NOT submit)
"""

from __future__ import annotations

from igp import gp, sair, submission, verify

CANDIDATES = [(97, 24), (73, 0)]  # (cyclotomic conductor n, expected real-root count r)


def live_24t1() -> dict:
    for lab in sair.labels_progress("igp24", limit=50):
        if lab["t"] == 1:
            return lab
    raise RuntimeError("24T1 not found in label progress")


def main() -> None:
    info = live_24t1()
    live = {s["r"]: s for s in info["signatures"]}
    print("LIVE 24T1 status (refreshed):")
    for r, s in sorted(live.items()):
        print(f"  r={r:>2}: discovered={s['discovered']} teams={s['teamCount']} "
              f"minDisc={s['minimumDiscAbs']}")

    for n, exp_r in CANDIDATES:
        coeffs = gp.polsubcyclo(n, 24)
        rep = verify.local_prefilter(coeffs)
        nf = gp.nfdisc(coeffs)
        r = rep.num_real_roots
        line = submission.poly_line(coeffs)  # bare API string (no comment)
        s = live.get(r, {})
        print(f"\n=== n={n}  ->  24T1, r={r} (expected {exp_r}) ===")
        print(f"  irreducible={rep.irreducible}  in_A24={rep.disc_is_square} (False for C_24)")
        print(f"  field nfdisc = {nf}")
        print(f"  cycle-type fingerprint = {rep.cycle_fingerprint}")
        print(f"  OPEN now? discovered={s.get('discovered')} teams={s.get('teamCount')} "
              f"minDisc={s.get('minimumDiscAbs')}")
        print(f"  submission line ({len(line.split(',')[0:25])} coeffs): {line}")


if __name__ == "__main__":
    main()
