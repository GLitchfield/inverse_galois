"""Tests for the producer bandit + target->producer mapping (pure; no sklearn/DB)."""

from __future__ import annotations

from igp import rank


def test_producer_of():
    assert rank.producer_of(None) == "exact"
    assert rank.producer_of("24T3039") == "exact"
    assert rank.producer_of("lmfdb6x4:6T11:d100:100000/010000") == "lmfdb6x4"
    assert rank.producer_of("tri:24_1_2_3") == "tri"
    assert rank.producer_of("size3:z15:10000000") == "size3"


def test_producer_of_source():
    assert rank.producer_of_source("daemon:quad:24_1_2_3_4_5") == "quad"
    assert rank.producer_of_source("daemon:lmfdb6x4:6T11:d100:1/0") == "lmfdb6x4"
    assert rank.producer_of_source("C-kummer3:zeta15:10000000") == "manual"  # historical -> one arm
    assert rank.producer_of_source(None) == "exact"


def test_bandit_rewards_distinct_sigs_not_rows():
    # a duplicated flood (many builds, few distinct sigs) must rank BELOW an efficient producer
    # that reaches the same distinct coverage in far fewer builds.
    stats = {
        "flood": {"rows": 1000, "sigs": 10, "sole": 0},
        "efficient": {"rows": 20, "sigs": 10, "sole": 0},
    }
    w = rank.bandit_weights(stats)
    assert w["efficient"] > w["flood"]


def test_bandit_sole_counts_extra():
    a = rank.bandit_weights({"x": {"rows": 20, "sigs": 10, "sole": 0}})["x"]
    b = rank.bandit_weights({"x": {"rows": 20, "sigs": 10, "sole": 5}})["x"]
    assert b > a  # sole (teamCount==0) signatures count extra


def test_bandit_explores_thin_arms():
    stats = {
        "known_low": {"rows": 200, "sigs": 2, "sole": 0},  # well-sampled, low distinct yield
        "thin": {"rows": 2, "sigs": 0, "sole": 0},          # unknown -> exploration bonus
    }
    w = rank.bandit_weights(stats)
    assert w["thin"] > w["known_low"]
