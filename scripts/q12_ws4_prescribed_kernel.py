"""q12 — WS4 step 2: hit a PRESCRIBED kernel deliberately (top C_12 = Q(zeta_13)).

GAP predicts the 24Tt for each canonical kernel over top C_12 (diagonal / augmentation
/ full). We then construct alpha to realize each and CONFIRM locally (verify.confirm_label,
no submission):
  - diagonal  (24T2)     <- rational alpha
  - full      (24T14744) <- generic non-unit alpha
  - augmentation (24T...) <- alpha with N(alpha) a square AND no other square-relations;
    search norm-square candidates (1-zeta^a)(1-zeta^b) (each has norm 13, product 13^2).

Run: uv run python scripts/q12_ws4_prescribed_kernel.py   (local only; no submit)

CAVEAT (test 0006): the local confirm_label CAN false-positive — it "confirmed" the
augmentation candidates as 24T12727, but Magma says 24T2456 (the two share parity,
subfields, and cycle types). Intermediate-kernel claims must be Magma-checked until
the identifier gets a resolvent upgrade. The norm-square recipe here is also
degenerate (13 totally ramified in Q(zeta_13) -> all (1-zeta^k) associate -> unit-
class -> 24T2456, not the augmentation). See docs/tests/0006.
"""

from __future__ import annotations

from igp import gap, gp, verify

PHI13 = [1] * 13


def try_alpha(alpha: str, target_t: int) -> str:
    try:
        coeffs = gp.quadratic_ext(PHI13, alpha)
    except gp.CASError as e:
        return f"gp error: {e}"
    if len(coeffs) != 25:
        return f"degree {len(coeffs)-1} (alpha square in F) - skip"
    fp = verify.local_fingerprint(coeffs)
    ok, checks = verify.confirm_label(coeffs, target_t, fingerprint=fp)
    return (f"24T{target_t}: confirm={ok} {checks}  "
            f"(#cyc={len(fp['cycle_types'])}, A24={fp['in_a24']})")


def main() -> None:
    pred = gap.c2_kernel_labels(1, 12)  # top = C_12
    print("GAP-predicted labels over top C_12:", pred)
    aug_t = int(pred["augmentation"][3:])

    print("\ndiagonal (rational alpha):")
    print("  alpha=2  ->", try_alpha("2", 2))
    print("full (generic alpha):")
    print("  alpha=y-2 ->", try_alpha("y-2", 14744))
    print(f"\naugmentation target {pred['augmentation']} via norm-square alpha:")
    for a, b in [(1, 2), (1, 3), (1, 5), (2, 3), (1, 4), (3, 5)]:
        alpha = f"(1-y^{a})*(1-y^{b})"
        print(f"  alpha={alpha:18s} ->", try_alpha(alpha, aug_t))


if __name__ == "__main__":
    main()
