from igp import coverage


def _row(t, r, sc, disc, ds, line):
    return {"t": t, "r": r, "scoreable": sc, "field_disc": disc, "disc_source": ds,
            "coeffs": line, "label": f"24T{t}"}


def test_best_by_pair_prefers_exact_then_smallest():
    # 24T24999 (near S24) is non-baseline, so the baseline-D_base guard is a no-op here.
    rows = [
        _row("24999", "0", "true", "1000", "exact_nfdisc", "A"),   # exact, disc 1000
        _row("24999", "0", "true", "10", "mixed_disc", "B"),        # mixed, smaller disc
        _row("24999", "0", "true", "2000", "exact_nfdisc", "C"),    # exact, larger disc
    ]
    best = coverage.best_by_pair(rows)
    assert best[("24999", "0")]["line"] == "A"   # exact wins over smaller-disc mixed
    assert best[("24999", "0")]["exact"] is True


def test_best_by_pair_skips_non_scoreable_and_blank_disc():
    rows = [
        _row("24999", "0", "false", "1000", "exact_nfdisc", "A"),   # not scoreable
        _row("24999", "2", "true", "", "", "B"),                    # blank disc
    ]
    assert coverage.best_by_pair(rows) == {}
