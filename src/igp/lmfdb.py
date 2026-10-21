"""LMFDB number-field client (public read-only Postgres mirror — no reCAPTCHA).

The LMFDB web UI and JSON API are reCAPTCHA-walled, but the underlying database is exposed as
a public read-only PostgreSQL mirror (``devmirror.lmfdb.xyz``, user/pass ``lmfdb``). The
``nf_fields`` table gives, per number field: defining polynomial ``coeffs`` (ascending), Galois
group ``galois_label`` (e.g. ``6T11``), ``disc_abs``, and ``class_number`` — exactly the
diverse, small-disc, KNOWN-group base fields the search wants (and degree-12, where local
``polgalois`` can't label).
"""

from __future__ import annotations

MIRRORS = ("devmirror.lmfdb.xyz", "proddb.lmfdb.xyz")


def _connect():
    import psycopg2

    last = None
    for host in MIRRORS:
        try:
            return psycopg2.connect(host=host, port=5432, dbname="lmfdb",
                                    user="lmfdb", password="lmfdb", connect_timeout=20)
        except Exception as e:  # mirror down / network — try the next
            last = e
    raise RuntimeError(f"no LMFDB mirror reachable: {last}")


def fields(degree: int, *, galois_label: str | None = None, class_number: int | None = 1,
           max_disc: int | None = None, max_r2: int | None = None, per_group: int | None = None,
           limit: int = 500, offset: int = 0):
    """Number fields of a degree, smallest |disc| first.

    Returns ``[(coeffs_ascending, galois_label, disc_abs, class_number)]``. ``class_number``
    filters (None = any); ``per_group`` keeps at most that many per ``galois_label`` (diversity);
    ``max_disc`` caps |disc|; ``max_r2`` caps complex places (``max_r2=0`` = totally real, for
    real-root-count / signature control). ``offset`` walks deeper into the (disc-ordered) list —
    a cursor over the full mirror (100k+ fields per degree), so producers aren't stuck re-pulling
    the same smallest-disc few hundred.
    """
    where = [f"degree={int(degree)}"]
    if galois_label is not None:
        where.append("galois_label=%(glab)s")
    if class_number is not None:
        where.append(f"class_number={int(class_number)}")
    if max_disc is not None:
        where.append(f"disc_abs<={int(max_disc)}")
    if max_r2 is not None:
        where.append(f"r2<={int(max_r2)}")
    sql = ("SELECT coeffs, galois_label, disc_abs, class_number FROM nf_fields WHERE "
           + " AND ".join(where) + " ORDER BY disc_abs LIMIT %(lim)s OFFSET %(off)s")
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(sql, {"lim": limit, "glab": galois_label, "off": int(offset)})
        rows = cur.fetchall()
    finally:
        conn.close()
    out, seen = [], {}
    for coeffs, label, disc, h in rows:
        if per_group is not None:
            if seen.get(label, 0) >= per_group:
                continue
            seen[label] = seen.get(label, 0) + 1
        # class_number is NULL for ~1% of the mirror (unknown h); only class_number=None callers
        # (gen12) ever see those rows, and they ignore h -- guard int(None) so the whole page
        # doesn't crash and take the producer down (2026-07-10: this had silently killed gen12).
        out.append(([int(c) for c in coeffs], label, int(disc), int(h) if h is not None else None))
    return out
