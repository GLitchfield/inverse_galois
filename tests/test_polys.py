import sympy

from igp import polys, verify

# z^24 - 2: irreducible (Eisenstein at 2); two real roots (+- 2^(1/24)).
Z24_MINUS_2 = [-2] + [0] * 23 + [1]  # ascending: c0=-2, ..., c24=1
# 35th cyclotomic polynomial has degree phi(35)=24; irreducible; no real roots.
PHI35 = sympy.Poly(sympy.cyclotomic_poly(35, polys.z), polys.z)


def test_irreducibility():
    assert polys.is_irreducible(polys.poly_from_coeffs(Z24_MINUS_2))
    assert polys.is_irreducible(PHI35)
    # z^24 - 1 factors.
    assert not polys.is_irreducible(polys.poly_from_coeffs([-1] + [0] * 23 + [1]))


def test_real_root_counts():
    assert polys.num_real_roots(polys.poly_from_coeffs(Z24_MINUS_2)) == 2
    assert polys.num_real_roots(PHI35) == 0  # all roots are non-real roots of unity


def test_signature_sums_to_degree():
    for p in (polys.poly_from_coeffs(Z24_MINUS_2), PHI35):
        r, s = polys.signature(p)
        assert r + 2 * s == p.degree() == 24


def test_perfect_square_helper():
    assert polys.is_perfect_square(0)
    assert polys.is_perfect_square(144)
    assert not polys.is_perfect_square(145)
    assert not polys.is_perfect_square(-4)


def test_frobenius_fingerprint_is_consistent():
    p = polys.poly_from_coeffs(Z24_MINUS_2)
    fp = polys.frobenius_cycle_types(p, primes=list(sympy.primerange(5, 80)))
    assert sum(fp.values()) > 0
    # every cycle type must partition the degree (24)
    for degs, count in fp.items():
        assert sum(degs) == 24
        assert count >= 1


def test_local_prefilter_report():
    rep = verify.local_prefilter(Z24_MINUS_2)
    assert rep.degree == 24
    assert rep.irreducible
    assert rep.num_real_roots == 2
    assert rep.passes
    assert isinstance(rep.disc_is_square, bool)
    assert all(sum(k) == 24 for k in rep.cycle_fingerprint)
