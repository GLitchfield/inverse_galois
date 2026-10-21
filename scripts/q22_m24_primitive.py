"""q22 — M24 (Mathieu group), a PRIMITIVE degree-24 group, via Müller's Q(t)-family.

The 5 primitive degree-24 groups have no block system, so the kernel-over-base machinery
can't reach them — they need explicit families. Peter Müller's one-parameter family
(arXiv:1204.1328, file Papers/m24.sage on his homepage) gives

    F_s(X) = (t - A_s(X))^2 + (1 + X^2) B_s(X)^2

with Galois group M24 over Q(t) for every rational s != 1. Specializing s and t to rationals
(avoiding the branch points = roots of the cubic dis(s,t)) yields M24 over Q by Hilbert
irreducibility. We take s = 0, t = 0 (dis(0,0) != 0), monicize (leading coeff is 2^44) and
polredbest to a small defining polynomial of the same field.

A_0, B_0 below are Müller's A_s, B_s specialized at s = 0 (credit: Peter Müller).
Result: 24T24680 = M24, Magma-confirmed (scoreable, non-baseline).
Run: uv run python scripts/q22_m24_primitive.py
"""

from __future__ import annotations

from igp import db, engine, gp, submission

# Müller's A_s, B_s at s = 0 (ascending coeffs a0..a_d in X); 2^44 = leading of F.
A0 = [0, -3462498, -5330757, 30667728, -156060348, 16098816, 46684160, -34062336,
      154443776, 1572864, -72351744, 0, 4194304]
B0 = [224829, -8906760, 71415384, -6865152, -56207872, 48453120, -164757504, -16515072,
      145227776, -1572864, -25165824]


def m24_polynomial():
    """Build the small M24 defining polynomial (ascending coeffs) via polredbest."""
    a = "+".join(f"({c})*X^{i}" for i, c in enumerate(A0) if c)
    b = "+".join(f"({c})*X^{i}" for i, c in enumerate(B0) if c)
    body = (
        f"A0={a}; B0={b}; t0=0;\n"
        "F=(t0-A0)^2+(1+X^2)*B0^2;\n"
        "L=pollead(F); n=poldegree(F);\n"
        "g=L^(n-1)*subst(F,X,X/L);\n"           # monic integer model of the same field
        "print(Vec(polredbest(g)));"
    )
    out = gp.script(body, timeout=600)
    line = next(ln for ln in out.splitlines() if ln.startswith("["))
    return [int(x) for x in line.strip("[]").split(",")][::-1]  # Vec is high->low


def main():
    print("collect (drain pending):", engine.collect())
    coeffs = m24_polynomial()
    print(f"M24 poly: degree {len(coeffs) - 1}, monic={coeffs[-1] == 1}, max digits "
          f"{max(len(str(abs(c))) for c in coeffs)}")
    line = submission.poly_line(coeffs)
    sid = engine.submit([(line, "M24:mueller:s0t0:polredbest")],
                        description="M24 primitive (Mueller family s=0 t=0)")
    print(f"submitted: {sid or '(already in flight/verified)'}")
    print("collect:", engine.collect())
    res = db.cache_load().get(line) or {}
    print(f"label: {res.get('label')}  scoreable: {res.get('scoreable')}")


if __name__ == "__main__":
    main()
