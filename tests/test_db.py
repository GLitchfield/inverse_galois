from igp import db


def test_db_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "REALIZED", tmp_path / "realized.csv")
    monkeypatch.setattr(db, "CACHE", tmp_path / "cache.json")
    monkeypatch.setattr(db, "PENDING", tmp_path / "pending.json")

    # pending log
    db.pending_add("sub_1", [["1,0,1", "srcA"]])
    assert "sub_1" in db.pending_load()
    db.pending_remove("sub_1")
    assert db.pending_load() == {}

    # cache
    db.cache_update({"1,0,1": {"label": "24T2"}})
    assert db.cache_load()["1,0,1"]["label"] == "24T2"

    # realized: dedup by coeffs line
    row = {"label": "24T2", "t": "1", "r": "0", "scoreable": "False",
           "in_baseline": "True", "field_disc": "5", "source": "x", "coeffs": "1,0,1"}
    db.record_realized([row])
    db.record_realized([row])
    assert len(db.load_realized()) == 1

    # submitted_lines unions realized + cache + pending
    db.pending_add("sub_2", [["9,9,9", "srcB"]])
    assert {"1,0,1", "9,9,9"} <= db.submitted_lines()

    # coverage keeps the smaller field_disc per (t, r)
    db.record_realized([{**row, "field_disc": "3", "coeffs": "2,0,2"}])
    cov = db.coverage()
    assert cov[("1", "0")]["coeffs"] == "2,0,2"


_BASE = {"label": "24T2", "t": "2", "r": "0", "scoreable": "true", "in_baseline": "false",
         "disc_source": "", "source": "x", "coeffs": "1,2,1"}


def test_record_realized_fills_blanks(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "REALIZED", tmp_path / "realized.csv")
    db.record_realized([{**_BASE, "field_disc": ""}])          # first: blank disc
    n = db.record_realized([{**_BASE, "field_disc": "999"}])   # later: richer, same coeffs line
    rows = db.load_realized()
    assert n == 0 and len(rows) == 1        # merged, not a new line
    assert rows[0]["field_disc"] == "999"   # blank got filled


def test_record_realized_keeps_existing_nonblank(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "REALIZED", tmp_path / "realized.csv")
    db.record_realized([{**_BASE, "field_disc": "100"}])
    db.record_realized([{**_BASE, "field_disc": "200"}])       # same line
    rows = db.load_realized()
    assert len(rows) == 1 and rows[0]["field_disc"] == "100"   # merge fills blanks only
