"""Search engine: robust submit/collect over the SAIR API + durable stores.

Decouples submission from result-collection (the synchronous-poll approach broke on
verifier backlog): ``submit`` posts a deduped batch and logs it to the pending store;
``collect`` reconciles pending submissions against the server whenever results are
ready, recording verified polynomials (with their coeffs) into the cache + coverage DB.
Idempotent and resumable across runs.
"""

from __future__ import annotations

import json

from . import db, sair


def _fail_reason(v: dict) -> str:
    """Best-effort rejection reason from a failedPolynomials entry -- defensive across schema keys
    (the exact field name is not pinned in the docs, so capture whatever SAIR sends, not a guess).
    """
    for k in ("reason", "rejectReason", "failureReason", "error", "message", "verdict", "status"):
        if v.get(k):
            return str(v[k])[:80]
    r = v.get("reasons") or v.get("errors")
    if r:
        return str(r[0] if isinstance(r, list) and r else r)[:80]
    extra = {k: val for k, val in v.items()
             if k not in ("polynomialIndex", "polynomial", "coeffs", "line")}
    return json.dumps(extra)[:80] if extra else "unknown"


def submit_batch(items: list[tuple[str, str]], description: str = "search batch",
                 cap: int = 1000) -> tuple[str | None, set[str], set[str]]:
    """Submit new (line, source) candidates in ONE POST (<=cap; server limit is 1000/submission).

    Dedups vs everything seen. Returns ``(submission_id, posted, known)``: ``posted`` = lines
    actually sent (pending-tracked), ``known`` = lines dropped as already verified/in flight.
    A line in NEITHER set exceeded ``cap`` and was NOT sent -- the caller must requeue it, never
    mark it submitted. (A silent ``[:100]`` truncation here while searchd marked the whole batch
    submitted dropped ~85% of built candidates between 2026-06-29 and 2026-07-01.)
    """
    prior = db.submitted_lines()
    seen: set[str] = set()
    uniq: list[tuple[str, str]] = []
    known: set[str] = set()
    for line, source in items:
        if line in prior:
            known.add(line)
        elif line not in seen:
            seen.add(line)
            uniq.append((line, source))
    if not uniq:
        return None, set(), known
    uniq = uniq[:cap]
    data = sair.submit("igp24", [line for line, _ in uniq], description=description)
    sid = data["submissionId"]
    db.pending_add(sid, [[line, source] for line, source in uniq])
    db.log_sid(sid)  # append-only sid ledger -> complete future re-sync (survives pending_remove)
    return sid, {line for line, _ in uniq}, known


def submit(items: list[tuple[str, str]], description: str = "search batch") -> str | None:
    """One-shot wrapper around ``submit_batch``: returns the submission id (None if nothing new)."""
    sid, _, _ = submit_batch(items, description)
    return sid


def collect() -> dict:
    """Reconcile pending submissions with the server; record finished ones. Resumable."""
    pending = db.pending_load()
    if not pending:
        return {"collected": 0, "still_pending": 0, "new_rows": 0}
    # Early-stop pagination: fetch newest-first only until every pending sid is seen. The full
    # history re-fetch was 27s/cycle at 1,126 submissions (and growing ~150/day); pending sids are
    # always recent, so this is ~1 page.
    need = set(pending)
    subs: dict = {}
    for it in sair.iter_submissions("igp24"):
        subs[it["submissionId"]] = it
        need.discard(it["submissionId"])
        if not need:
            break
    # Pagination caps at offset 300 (server-side 503 past page 12); any pending sid buried under
    # >300 newer submissions never appears above, so fetch the stragglers directly by id (not
    # offset-capped). Without this they strand forever (the 07-04/07-06 zombie batches).
    for sid in list(need):
        try:
            subs[sid] = sair.submission_by_id(sid)
        except sair.SairError:
            pass  # transient (503/timeout) -> leave pending, retry next cycle
    cache_new: dict = {}
    rows: list[dict] = []
    reason_counts: dict = {}
    collected = failed = 0
    for sid, items in list(pending.items()):
        it = subs.get(sid)
        if it is None or it.get("payload", {}).get("queuedPolynomials"):
            continue  # unknown yet, or still verifying — leave pending
        for v in it.get("verifiedPolynomials", []):
            line, source = items[v["polynomialIndex"]]
            res = {
                "label": v["label"], "t": v["t"], "r": v["r"],
                "in_baseline": v["inBaseline"], "scoreable": v.get("scoreable"),
                # mixed-disc results can be scoreable with no numeric field disc; keep disc_source
                "field_disc": v.get("fieldDiscAbs") or v.get("scoringDiscAbs") or "",
                "disc_source": v.get("discSource") or "",
            }
            cache_new[line] = res
            rows.append({**res, "source": source, "coeffs": line})
        for v in it.get("failedPolynomials", []):  # record failures + WHY (rejection reason)
            idx = v.get("polynomialIndex")
            if idx is None or idx >= len(items):
                continue
            reason = _fail_reason(v)
            src = items[idx][1]
            fam = src.split(":")[1] if src.count(":") >= 1 else src[:14]  # producer family
            key = f"{fam}|{reason}"
            reason_counts[key] = reason_counts.get(key, 0) + 1
            cache_new[items[idx][0]] = {"label": None, "failed": True, "reason": reason}
            failed += 1
        db.pending_remove(sid)
        collected += 1
    if cache_new:
        db.cache_update(cache_new)
    if rows:
        db.record_realized(rows)
    # collect_failed: we HAD pending sids to collect but iter_submissions returned nothing -> the
    # /submissions/me endpoint 503'd on page 1. The caller uses this to stop pending (which is then
    # a lie -- it includes results SAIR verified but we could not pull) from gating the daemon.
    if reason_counts:  # persist a running per-(producer, reason) tally for producer diagnostics
        try:
            from . import searchstore as store
            agg = store.get_kv("failed_reasons", {}) or {}
            for k, n in reason_counts.items():
                agg[k] = agg.get(k, 0) + n
            store.set_kv("failed_reasons", agg)
        except Exception:
            pass
    return {"collected": collected, "failed": failed,
            "still_pending": len(db.pending_load()), "new_rows": len(rows),
            "reasons": reason_counts,
            "collect_failed": (not subs and bool(pending))}
