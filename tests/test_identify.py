"""Tests for the distribution-likelihood identifier (verify.identify).

Uses x^2+1 (group C_2: splits when p = 1 mod 4, inert when p = 3 mod 4) with explicit
candidate distributions, so the ranking logic is exercised without GAP/Magma.
"""

from __future__ import annotations

import math

from igp import verify

X2P1 = [1, 0, 1]  # x^2 + 1, ascending
PRIMES = [3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]


def test_observes_both_cycle_types():
    res = verify.identify(
        X2P1, [1],
        primes=PRIMES,
        dists={1: {"order": 2, "dist": {(1, 1): 1, (2,): 1}}},
    )
    obs = res["observed"]
    assert (1, 1) in obs and (2,) in obs  # both split and inert occur


def test_hard_excludes_candidate_missing_a_cycle_type():
    # candidate B has no inert (2,) pattern -> impossible -> -inf; A is C_2 and fits
    dists = {
        10: {"order": 2, "dist": {(1, 1): 1, (2,): 1}},   # true C_2
        20: {"order": 1, "dist": {(1, 1): 1}},            # cannot produce (2,)
    }
    res = verify.identify(X2P1, [10, 20], primes=PRIMES, dists=dists)
    assert res["best"] == 10
    assert res["margin"] == math.inf
    excluded = next(r for r in res["ranked"] if r["t"] == 20)
    assert excluded["loglik"] == -math.inf
    assert (2,) in excluded["impossible"]


def test_prefers_better_frequency_match_when_both_possible():
    # both candidates can produce both types, but A's frequencies match C_2 (~50/50)
    # far better than B's lopsided weights -> A wins with a finite positive margin
    dists = {
        1: {"order": 2, "dist": {(1, 1): 1, (2,): 1}},       # 50/50
        2: {"order": 100, "dist": {(1, 1): 99, (2,): 1}},    # 99/1
    }
    res = verify.identify(X2P1, [1, 2], primes=PRIMES, dists=dists)
    assert res["best"] == 1
    assert 0 < res["margin"] < math.inf


def test_s24_skip_rule():
    # a 13/17/19-cycle forces primitive non-Mathieu => A_24/S_24; non-square disc => S_24 => skip
    assert verify._s24_skip({(13, 11)}, False) is True
    assert verify._s24_skip({(1, 4, 19)}, False) is True
    # ...but a square discriminant means A_24 (rare, valuable) => keep
    assert verify._s24_skip({(13, 11)}, True) is False
    # 11- and 23-cycles are realized by M_24 / PSL(2,23) => never skip on them
    assert verify._s24_skip({(1, 23)}, False) is False
    assert verify._s24_skip({(2, 11, 11)}, False) is False
    # imprimitive-compatible cycle types (no big prime cycle) => keep
    assert verify._s24_skip({(2, 4, 6, 12), (3, 3, 18)}, False) is False
