"""Pure-Python polynomial primitives for IGP24 candidate pre-filtering.

These need neither a computer-algebra system nor network access: they run on
sympy and provide the *cheap local* checks (arsenal method M7) that narrow or
reject a candidate before spending an authoritative verification (Magma, via the
SAIR API) or the official scoring discriminant (PARI/GP ``nfdisc``).

Here (cheap, local, exact):
  - irreducibility over Q
  - the integer polynomial discriminant + its square class (-> Gal <= A_24?)
  - the number of real roots (the signature coordinate ``r``)
  - a Frobenius cycle-type fingerprint from factorization mod good primes

NOT here (need a CAS / the official path; see ``verify.py``):
  - the field discriminant ``nfdisc`` (the SCORING quantity)  -> PARI/GP
  - the authoritative 24Tt Galois label                       -> Magma (SAIR API)

Candidates are assumed monic with integer coefficients (the standard form for a
polynomial defining a degree-24 field); the Frobenius method via Dedekind's
theorem requires the leading coefficient to be coprime to the sampled prime,
which is automatic for monic input.
"""

from __future__ import annotations

from collections import Counter
from math import isqrt

import sympy
from sympy import Poly, Symbol, primerange

z = Symbol("z")

# Small good primes for the Frobenius fingerprint (primes dividing the
# discriminant or the leading coefficient are skipped at use time).
DEFAULT_PRIMES: list[int] = list(primerange(3, 200))


def poly_from_coeffs(coeffs, *, ascending: bool = True) -> Poly:
    """Build a sympy ``Poly`` in ``z`` from integer coefficients.

    ``ascending=True``  -> ``coeffs[i]`` multiplies ``z**i`` (c0 + c1 z + ...).
    The IGP24 ``submission.txt`` coefficient order is not yet confirmed (see
    docs/competition_rules.md), so the convention is explicit, not guessed.
    """
    cs = [int(c) for c in coeffs]
    if not ascending:
        cs = cs[::-1]
    expr = sum(c * z**i for i, c in enumerate(cs))
    return Poly(expr, z)


def is_irreducible(p: Poly) -> bool:
    """Irreducibility over Q."""
    return p.is_irreducible


def poly_discriminant(p: Poly) -> int:
    """Discriminant of the polynomial (an integer for integer ``p``).

    This is the *polynomial* discriminant, not the field discriminant ``nfdisc``
    used for scoring; they differ by the square of the index [O_K : Z[theta]].
    """
    return int(sympy.discriminant(p.as_expr(), z))


def is_perfect_square(n: int) -> bool:
    if n < 0:
        return False
    r = isqrt(n)
    return r * r == n


def in_alternating_group(p: Poly) -> bool:
    """Whether Gal(p) <= A_n, i.e. disc(p) is a square in Q.

    For monic separable integer ``p`` this is exactly: disc(p) is a perfect
    square integer. Cheap necessary condition on the 24Tt label (every group is
    either inside A_24 or not), so it prunes the candidate group set for free.
    """
    return is_perfect_square(poly_discriminant(p))


def num_real_roots(p: Poly) -> int:
    """Number of real roots (the signature coordinate ``r``).

    For irreducible ``p`` the roots are simple; uses exact real-root isolation.
    """
    return len(sympy.real_roots(p.as_expr(), z))


def signature(p: Poly) -> tuple[int, int]:
    """(r, s): r real roots and s complex-conjugate pairs, r + 2s = deg."""
    r = num_real_roots(p)
    return r, (p.degree() - r) // 2


def frobenius_cycle_types(p: Poly, primes=DEFAULT_PRIMES) -> Counter:
    """Multiset of Frobenius cycle types from factoring ``p`` mod good primes.

    Dedekind: for a prime ``q`` not dividing disc(p) (and coprime to the leading
    coefficient), the multiset of degrees of the irreducible factors of ``p mod
    q`` is the cycle type of a Frobenius element of Gal(p) on the roots. Sampling
    many ``q`` approximates the group's cycle-type distribution (Chebotarev) -- a
    cheap fingerprint to narrow / rule out the 24Tt before an authoritative call.

    Returns a ``Counter`` mapping a sorted tuple of factor degrees (summing to
    deg p) to how many sampled primes produced it.
    """
    disc = poly_discriminant(p)
    lead = int(p.LC())
    out: Counter = Counter()
    for q in primes:
        if disc % q == 0 or lead % q == 0:
            continue  # ramified / bad reduction: Dedekind does not apply
        factors = Poly(p.as_expr(), z, modulus=q).factor_list()[1]
        degs = tuple(sorted(f.degree() for f, _mult in factors))
        out[degs] += 1
    return out
