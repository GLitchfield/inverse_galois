"""engine.submit_batch: dedup + cap accounting (regression for the silent [:100] drop)."""

from igp import engine


def test_submit_batch_reports_posted_known_and_overcap(monkeypatch):
    sent = {}
    monkeypatch.setattr(engine.db, "submitted_lines", lambda: {"known_line"})
    monkeypatch.setattr(engine.db, "pending_add",
                        lambda sid, items: sent.__setitem__("pending", items))

    def fake_post(cid, polys, description=None):
        sent["polys"] = list(polys)
        return {"submissionId": "sub_test"}

    monkeypatch.setattr(engine.sair, "submit", fake_post)
    items = [("known_line", "old")] + [(f"l{i}", "s") for i in range(1500)] + [("l0", "dup_again")]
    sid, posted, known = engine.submit_batch(items, cap=1000)
    assert sid == "sub_test"
    assert known == {"known_line"}
    assert len(posted) == 1000 and len(sent["polys"]) == 1000 and len(sent["pending"]) == 1000
    assert "l0" in posted and "l999" in posted
    # over-cap lines are in NEITHER set -> caller must requeue them, not mark submitted
    assert "l1000" not in posted and "l1000" not in known


def test_collect_recovers_sid_buried_past_pagination(monkeypatch):
    # A pending sid that pagination never yields (buried past the offset-300 cap) must still be
    # collected via the by-id fallback, not stranded forever (the 07-04/07-06 zombie batches).
    sid = "sub_buried"
    monkeypatch.setattr(engine.db, "pending_load", lambda: {sid: [("coeff_line", "prov")]})
    monkeypatch.setattr(engine.sair, "iter_submissions", lambda *a, **k: iter(()))
    by_id_calls = []

    def fake_by_id(s, cid="igp24"):
        by_id_calls.append(s)
        return {"submissionId": s, "payload": {},
                "verifiedPolynomials": [{"polynomialIndex": 0, "label": "24T5", "t": 5, "r": 0,
                                         "inBaseline": False, "scoreable": True,
                                         "fieldDiscAbs": "12345", "discSource": "exact_nfdisc"}],
                "failedPolynomials": []}

    monkeypatch.setattr(engine.sair, "submission_by_id", fake_by_id)
    recorded = {}
    monkeypatch.setattr(engine.db, "cache_update", lambda d: recorded.update(cache=d))
    monkeypatch.setattr(engine.db, "record_realized",
                        lambda rows: recorded.setdefault("rows", rows))
    removed = []
    monkeypatch.setattr(engine.db, "pending_remove", removed.append)

    out = engine.collect()
    assert by_id_calls == [sid]
    assert out["collected"] == 1 and out["new_rows"] == 1 and out["collect_failed"] is False
    assert removed == [sid]
    assert recorded["rows"][0]["coeffs"] == "coeff_line" and recorded["rows"][0]["t"] == 5


def test_submit_batch_all_known_posts_nothing(monkeypatch):
    called = []
    monkeypatch.setattr(engine.db, "submitted_lines", lambda: {"x", "y"})
    monkeypatch.setattr(engine.sair, "submit", lambda *a, **k: called.append(1))
    sid, posted, known = engine.submit_batch([("x", "s"), ("y", "s")])
    assert sid is None and posted == set() and known == {"x", "y"}
    assert not called
    assert engine.submit([("x", "s")]) is None
