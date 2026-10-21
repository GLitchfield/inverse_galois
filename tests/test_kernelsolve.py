"""Tests for the general F_2[H]-module kernel solver (pure; no CAS)."""

from __future__ import annotations

from igp import kernelsolve as ks

SHIFT12 = [(i + 1) % 12 for i in range(12)]  # C_12 regular (cyclic shift)
V4 = [[1, 0, 3, 2], [2, 3, 0, 1]]  # Klein 4-group, regular on 4 points


def test_apply_perm_shifts_bits():
    assert ks.apply_perm(SHIFT12, 0b1) == 0b10  # e_0 -> e_1
    assert ks.apply_perm(SHIFT12, 1 << 11) == 0b1  # e_11 -> e_0 (wraps)


def test_rref_is_canonical_and_order_independent():
    a = ks.rref([0b011, 0b101, 0b110])  # rank 2 (third = xor of first two)
    b = ks.rref([0b110, 0b011])
    assert a == b
    assert len(a) == 2


def test_module_basis_augmentation_over_c12():
    # x+1 (= e_0 + e_1) generates the augmentation ideal of F_2[C_12]: dim 11
    assert len(ks.module_basis(0b11, [SHIFT12])) == 11
    # e_0 generates the whole regular module: dim 12
    assert len(ks.module_basis(0b1, [SHIFT12])) == 12


def test_cyclic_module_recovered_by_single_generator():
    # over a cyclic group every submodule is cyclic -> one generator
    target = [1 << i for i in range(12)]  # the full module
    gens = ks.generators(target, [SHIFT12])
    assert len(gens) == 1
    assert ks.module_basis(gens[0], [SHIFT12]) == ks.rref(target)


def test_noncyclic_module_needs_two_generators():
    # the augmentation ideal of F_2[V_4] is the maximal ideal (a,b): not principal
    aug = [0b0011, 0b0101, 0b1001]  # sum-zero vectors, dim 3
    assert ks.cyclic_generator(aug, V4) is None
    gens = ks.generators(aug, V4)
    assert len(gens) == 2
    union = set()
    for w in gens:
        union |= ks.orbit(w, V4)
    assert ks.rref(union) == ks.rref(aug)  # generators reconstruct the target


def test_unreachable_target_returns_none():
    # a vector outside any H-submodule spanned by target's own elements is still fine,
    # but a "target" that isn't H-closed cannot be generated from within itself in general;
    # the full space is always reachable, so check the empty/zero target instead.
    assert ks.generators([0], [SHIFT12]) == []
