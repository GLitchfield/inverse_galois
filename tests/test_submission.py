import pytest

from igp import submission as sub

# x^24 + x + 1 -> a_0=1, a_1=1, a_2..a_23=0, a_24=1
X24_X_1 = [1, 1] + [0] * 22 + [1]
X24_X_1_LINE = "1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1"


def test_poly_line_matches_official_example():
    assert sub.poly_line(X24_X_1) == X24_X_1_LINE
    assert len(X24_X_1) == sub.NCOEFFS == 25


def test_parse_round_trip_and_comments():
    assert sub.parse_line(X24_X_1_LINE) == X24_X_1
    assert sub.parse_line("# just a comment") is None
    assert sub.parse_line("   ") is None
    assert sub.parse_line(X24_X_1_LINE + "  # 24T1 expected") == X24_X_1


def test_coefficient_rules_rejected():
    with pytest.raises(sub.SubmissionError):  # non-monic
        sub.poly_line([1, 1] + [0] * 22 + [2])
    with pytest.raises(sub.SubmissionError):  # a_0 == 0
        sub.poly_line([0, 1] + [0] * 22 + [1])
    with pytest.raises(sub.SubmissionError):  # wrong length
        sub.poly_line([1, 1, 1])


def test_limits():
    assert sub.build_submission_txt([X24_X_1], header="x^24 + x + 1").endswith(X24_X_1_LINE + "\n")
    with pytest.raises(sub.SubmissionError):
        sub.to_polynomials([X24_X_1] * (sub.MAX_POLYS + 1))


def test_api_strings_are_bare():
    # the API rejects anything but 25 decimal integers — no comments allowed
    assert all("#" not in s for s in sub.to_polynomials([X24_X_1, X24_X_1]))


def test_official_limits_current():
    """P0 review 2026-07-11: the official 2026-06-29 raise, confirmed vs the July-9 rules."""
    assert sub.MAX_POLYS == 1000
    assert sub.MAX_BYTES == 1_000_000


def test_mixed_disc_is_official_form():
    """July-9 official: mixed discriminant = nfdisc([f,100000]). Guard against drift back to the old
    product-of-local-nfdisc form (P0 review 2026-07-11)."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "src" / "igp" / "mixed_disc.gp").read_text()
    assert "nfdisc([f,B])" in "".join(src.split())  # the official form
    assert "small_nf_disc" not in src               # the old product-form implementation is gone


def test_score_formula():
    D = 10**40
    assert sub.score_pair(1, D, D) == pytest.approx(1.0)      # sole non-baseline realizer
    assert sub.score_pair(2, D, D) == pytest.approx(0.5)      # beat one baseline pair
    # smaller discriminant -> more points; larger k -> fewer points
    assert sub.score_pair(1, 10**50, 10**40) < 1.0
    assert sub.score_pair(3, D, D) < sub.score_pair(2, D, D)
