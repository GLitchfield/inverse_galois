"""SAIR public API client — https://api.sair.foundation/api/public/v1.

Auth is ``Authorization: Bearer <key>``; the key is read from
``data/raw/sair_api_key.txt`` (gitignored) or the ``SAIR_API_KEY`` env var.
The project key ('inverse-galois') carries competition.read + competition.write.

Endpoints used: ``/me``, ``/competitions/{id}``, ``/competitions/{id}/labels/progress``
(cursor-paginated; each label has ``allowedR`` = the achievable real-root counts,
plus per-signature ``minimumDiscAbs`` / ``discovered`` — the leaderboard state),
and ``/competitions/{id}/submissions`` for submitting.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import requests

BASE = "https://api.sair.foundation/api/public/v1"
_KEY_FILE = Path(__file__).resolve().parents[2] / "data" / "raw" / "sair_api_key.txt"
_UA = "igp/0.0.1 (inverse_galois research client)"


class SairError(RuntimeError):
    """The SAIR API returned an error or no key is available."""


def api_key() -> str:
    key = os.environ.get("SAIR_API_KEY")
    if key:
        return key.strip()
    if _KEY_FILE.exists():
        return _KEY_FILE.read_text().strip()
    raise SairError(f"no API key: set SAIR_API_KEY or write {_KEY_FILE}")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {"Authorization": f"Bearer {api_key()}", "Accept": "application/json", "User-Agent": _UA}
    )
    return s


def _get(path: str, params: dict | None = None, *, session=None, timeout: float = 60.0) -> dict:
    s = session or _session()
    try:  # a network-level blip must surface as SairError -- callers all fail-soft on that, and an
        # escaping ReadTimeout killed a whole resync_scoreable run (audit 2026-07-14). GET only:
        # `submit` (POST) must NOT be made fail-soft, or a timed-out-but-landed POST gets resent.
        r = s.get(f"{BASE}{path}", params=params, timeout=timeout)
    except requests.RequestException as e:
        raise SairError(f"{path}: {type(e).__name__}") from e
    try:
        body = r.json()
    except ValueError as e:
        raise SairError(f"{path}: non-JSON response (HTTP {r.status_code})") from e
    if not body.get("ok"):
        raise SairError(f"{path}: HTTP {r.status_code} {body.get('error')}")
    return body["data"]


def me() -> dict:
    return _get("/me")


def competition(cid: str = "igp24") -> dict:
    return _get(f"/competitions/{cid}")


def labels_progress(cid: str = "igp24", *, limit: int = 500) -> Iterator[dict]:
    """Yield per-label progress dicts for every group, following the cursor.

    Each dict: ``label, t, allowedR, teamCount, minimumDiscAbs,
    discoveredSignatures, remainingSignatures, signatures[{r, teamCount,
    minimumDiscAbs, discovered}]``.
    """
    s = _session()
    cursor: str | None = None
    while True:
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        data = _get(f"/competitions/{cid}/labels/progress", params, session=s)
        yield from data["labels"]
        cursor = data.get("nextCursor")
        if not cursor:
            break


def my_submissions(cid: str = "igp24", *, limit: int = 25) -> list[dict]:
    """All of our submissions for the competition (cursor-paginated)."""
    return list(iter_submissions(cid, limit=limit))


def iter_submissions(cid: str = "igp24", *, limit: int = 25) -> Iterator[dict]:
    """Yield submissions newest-first, one page at a time (callers can stop early — the pending
    sids are always recent, so ``collect`` usually needs only the first page instead of the whole
    ever-growing history).

    ``limit`` MUST stay small: ``/submissions/me`` returns HTTP 503 at ``limit>=100`` once our
    submission history is large (verified 2026-07-06: limit 1/5/25 OK, 100 -> 503). This is the
    daemon's collect path (``engine.collect``), so 100 here silently broke collect for ~13h. On a
    mid-pagination error we stop gracefully (deep pages 503; the recent pages we already yielded are
    where fresh pending lives) but we LOG it to stderr so a page-1/auth/real failure is never silent
    again."""
    import sys
    s = _session()
    cursor: str | None = None
    page = 0
    while True:
        params: dict = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        try:
            data = _get(f"/competitions/{cid}/submissions/me", params, session=s)
        except SairError as e:
            print(f"iter_submissions stopped at page {page} (cursor={bool(cursor)}): {e}",
                  file=sys.stderr)
            return
        yield from data["items"]
        page += 1
        cursor = data.get("nextCursor")
        if not cursor:
            return


def submission_by_id(sid: str, cid: str = "igp24") -> dict:
    """Fetch ONE submission directly by id, bypassing the cursor pagination.

    ``/submissions/me`` caps cursor pagination at offset 300 (HTTP 503 past page 12@limit25 /
    page 6@limit50 — a fixed OFFSET, confirmed 2026-07-10), so a pending sid buried under >300
    newer submissions is UNREACHABLE by ``iter_submissions`` and its verified results strand
    forever (the 3019-row 07-04 zombie batch + 5 uncollected 07-06 sids w/ ~2560 verified polys).
    This per-id GET is NOT offset-capped and returns the same shape pagination yields (payload,
    verifiedPolynomials, failedPolynomials), so ``engine.collect`` uses it as a fallback for any
    pending sid the newest-first walk didn't reach."""
    return _get(f"/competitions/{cid}/submissions/{sid}")


def download_submission(sid: str, cid: str = "igp24") -> list[str]:
    """The submitted coefficient LINES for a submission (text/plain, one per line, in index order).
    The /submissions/{id} result gives per-poly label/scoreable by polynomialIndex but NOT the line,
    so re-syncing a now-scored poly back into realized.csv (keyed by coeffs) needs this."""
    s = _session()
    try:
        r = s.get(f"{BASE}/competitions/{cid}/submissions/{sid}/download", timeout=60)
    except requests.RequestException as e:
        raise SairError(f"download {sid}: {type(e).__name__}") from e
    if r.status_code != 200:
        raise SairError(f"download {sid}: HTTP {r.status_code}")
    return [ln.strip() for ln in r.text.splitlines() if ln.strip() and not ln.startswith("#")]


def leaderboard(cid: str = "igp24", *, limit: int = 100) -> list[dict]:
    """Official team standings: [{rank, teamId, teamName, teamNumber, score, scoreablePairs}]."""
    return _get(f"/competitions/{cid}/leaderboard", {"limit": limit})["items"]


def submit(cid: str, polynomials: list[str], *, description: str | None = None) -> dict:
    """POST a submission. ``polynomials``: coefficient strings from
    ``submission.to_polynomials`` (<=1000 per submission since 2026-06-29, <=1,000,000 bytes total).

    Confirmed body envelope: ``{"payload": {"polynomials": [...]}, "meta": {...}}``.
    Requires the team to be **enrolled** in the competition (else 403
    ENROLL_REQUIRED). Writes to the live competition (counts against the daily limit).
    """
    s = _session()
    body_obj: dict = {"payload": {"polynomials": list(polynomials)}}
    if description:
        body_obj["meta"] = {"description": description}
    r = s.post(f"{BASE}/competitions/{cid}/submissions", json=body_obj, timeout=180)
    body = r.json()
    if not body.get("ok"):
        raise SairError(f"submit: HTTP {r.status_code} {body.get('error')}")
    return body["data"]
