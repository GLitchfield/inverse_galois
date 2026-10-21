"""Tests for the search daemon's work store (SQLite); uses a temp DB."""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture()
def store(tmp_path, monkeypatch):
    from igp import searchstore as s
    importlib.reload(s)
    monkeypatch.setattr(s, "DB", tmp_path / "search.db")
    s.init()
    return s


def test_enqueue_claim_mark_lifecycle(store):
    assert store.enqueue("cyclotomic_c2", {"w": [1], "n": 13, "q": 53}, target="24T1")
    assert store.counts() == {"queued": 1}
    batch = store.claim(5)
    assert len(batch) == 1 and batch[0]["payload"]["n"] == 13
    assert store.counts() == {"building": 1}
    store.mark(batch[0]["id"], "submitted", line="1,2,3")
    assert store.counts() == {"submitted": 1}
    assert store.line_status("1,2,3") == "submitted"


def test_target_dedup(store):
    assert store.enqueue("k", {}, target="24T5")
    assert not store.enqueue("k", {}, target="24T5")  # same target -> skipped
    assert store.counts() == {"queued": 1}


def test_kv_roundtrip(store):
    store.set_kv("control", {"pause": True})
    assert store.get_kv("control") == {"pause": True}
    assert store.get_kv("missing", 7) == 7


def test_claim_respects_quota(store):
    for i in range(10):
        store.enqueue("ready", {"coeffs": [i]}, target=f"gen12:a{i}")
    for i in range(10):
        store.enqueue("ready", {"coeffs": [100 + i]}, target=f"tsig:b{i}")
    store.set_priority_prefix("gen12:", 9.0)   # gen12 would dominate a pure-priority claim
    store.set_priority_prefix("tsig:", 1.0)
    store.set_kv("quota", {"gen12:": 0.5, "tsig:": 0.5})
    got = store.claim(8)
    mix = {t.split(":")[0] for t in (r["target"] for r in got)}
    n_tsig = sum(1 for r in got if r["target"].startswith("tsig:"))
    assert mix == {"gen12", "tsig"} and 3 <= n_tsig <= 5   # ~half each despite priority skew


def test_claim_without_quota_is_pure_priority(store):
    store.enqueue("ready", {"coeffs": [1]}, target="gen12:x")
    store.enqueue("ready", {"coeffs": [2]}, target="tsig:y")
    store.set_priority_prefix("tsig:", 5.0)
    got = store.claim(1)
    assert got[0]["target"] == "tsig:y"
