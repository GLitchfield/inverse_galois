"""Build, validate, and score IGP24 submissions.

Authoritative format (docs/competition_rules.md, from the official evaluation doc):
each polynomial is a degree-24 monic integer polynomial written as its **25
coefficients, comma-separated, in ASCENDING powers** ``a_0,a_1,...,a_24`` with
``a_0 != 0`` and ``a_24 == 1`` (monic; non-monic is rejected). Example:
``x^24 + x + 1`` -> ``1,1,0,...,0,1``. In ``submission.txt`` one polynomial per
line, ``#`` lines/trailers are comments; the public API takes the same coefficient
strings as ``{"polynomials": [...]}``. Limits (official, 2026-06-29 raise):
<=1,000 polynomials/submission, <=1,000,000 bytes raw ``submission.txt``.

Scoring per verified ``(24Tt, r)`` pair and team: ``2^(1-k) * log(D0)/log(D)``,
where ``k`` = number of credited teams (LMFDB counts as one for an unlocked
baseline pair), ``D`` = the team's scoring discriminant, ``D0`` = the smallest
among credited teams. Sole non-baseline realizer -> 1.0; beating one baseline
pair -> 0.5. Rarity (the ``2^(1-k)`` factor) dominates; the discriminant is a mild
log-ratio tiebreaker.
"""

from __future__ import annotations

from math import log

DEGREE = 24
NCOEFFS = DEGREE + 1  # 25: a_0 .. a_24
# Official limits (2026-06-29 raise from 100/100KB; confirmed vs the July-9 rules markdown):
MAX_POLYS = 1000  # polynomials per submission
MAX_BYTES = 1_000_000  # raw submission.txt bytes


class SubmissionError(ValueError):
    """A polynomial or submission violates the IGP24 format/limits."""


def validate_coeffs(coeffs) -> list[int]:
    """Check the coefficient rules; return the coeffs as ints (ascending)."""
    cs = [int(c) for c in coeffs]
    if len(cs) != NCOEFFS:
        raise SubmissionError(f"need {NCOEFFS} coefficients a_0..a_{DEGREE}, got {len(cs)}")
    if cs[0] == 0:
        raise SubmissionError("a_0 must be nonzero")
    if cs[-1] != 1:
        raise SubmissionError("a_24 must be 1 (submissions must be monic)")
    return cs


def poly_line(coeffs) -> str:
    """The bare coefficient string ``a_0,a_1,...,a_24`` (ascending), 25 integers.

    No trailing ``#`` comment: the public API rejects any ``polynomials[*]`` string
    that isn't exactly 25 decimal integers ("all coefficients must be decimal
    integers"). Comments are a ``submission.txt``-file affordance only.
    """
    return ",".join(str(c) for c in validate_coeffs(coeffs))


def parse_line(line: str) -> list[int] | None:
    """Parse a submission line to ascending coeffs; ``None`` for blank/comment lines."""
    body = line.split("#", 1)[0].strip()
    if not body:
        return None
    return validate_coeffs([int(x) for x in body.split(",")])


def to_polynomials(items) -> list[str]:
    """Coefficient lists -> API ``polynomials`` strings (bare, <=1,000)."""
    out = [poly_line(c) for c in items]
    if len(out) > MAX_POLYS:
        raise SubmissionError(f"at most {MAX_POLYS} polynomials, got {len(out)}")
    return out


def build_submission_txt(items, *, header: str | None = None) -> str:
    """Assemble a ``submission.txt`` body; enforces the line and byte limits."""
    lines = [f"# {h}" for h in header.splitlines()] if header else []
    lines += to_polynomials(items)
    text = "\n".join(lines) + "\n"
    nbytes = len(text.encode())
    if nbytes > MAX_BYTES:
        raise SubmissionError(f"submission is {nbytes} bytes (> {MAX_BYTES})")
    return text


def score_pair(k: int, disc_abs: int, best_disc_abs: int) -> float:
    """Points for one ``(24Tt, r)`` pair: ``2^(1-k) * log(D0)/log(D)``.

    ``k`` credited teams; ``disc_abs`` = |this team's scoring discriminant D|;
    ``best_disc_abs`` = |smallest D0 among credited teams|.
    """
    D, D0 = abs(int(disc_abs)), abs(int(best_disc_abs))
    if D <= 1 or D0 <= 1:
        raise SubmissionError("need |D| > 1 and |D0| > 1 for the log-ratio")
    return 2.0 ** (1 - k) * (log(D0) / log(D))
