"""Official competition reference data loads + the baseline-beat logic (test 0032)."""

from __future__ import annotations

from igp import baseline


def test_reference_data_counts():
    assert len(baseline.valid_pairs()) == 165836      # authoritative validR
    assert len(baseline.baseline_dbase()) == 622      # frozen LMFDB baseline pairs
    assert len(baseline.nonsolvable_t()) == 807       # non-solvable residual


def test_baseline_membership_and_beat():
    db = baseline.d_base("1", "0")                     # 24T1,0 is a baseline pair
    assert db is not None and db > 0
    assert baseline.is_baseline("1", "0")
    assert baseline.beats_baseline("1", "0", db - 1)  # strict improvement unlocks (0.5)
    assert not baseline.beats_baseline("1", "0", db)  # equal does not
    assert not baseline.beats_baseline("999999", "0", 5)  # non-baseline: nothing to beat


def test_nonsolvable_and_valid_lookup():
    assert "201" in baseline.nonsolvable_t()          # first non-solvable t
    assert ("1", "0") in baseline.valid_pairs()
