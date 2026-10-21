"""Build submission.txt batches from realized.csv (the committed deliverable; review / test 0031).

Picks ONE best polynomial per scoreable `(t,r)`, ranks by expected score
`2^(1-teamCount) * log(minDisc)/log(ourDisc)` (highest-value batch first), and writes files at the
OFFICIAL limits (<=1,000 polys / <=1,000,000 bytes, from `igp.submission`) plus a rich manifest.
The daemon submits incrementally; this is the reproducible final artifact + a clean re-submit path.

Selection rules (P0 review 2026-07-11):
- Prefer an EXACT `nfdisc` row (disc_source=exact_nfdisc) over a mixed-disc row; among same
  exactness, smallest scoring disc.
- BASELINE pairs score ONLY with an exact nfdisc strictly below D_base -- a mixed-disc (or a
  non-beating exact) baseline row is dropped (it cannot unlock the pair).

Run: uv run python scripts/build_submission.py
"""

from __future__ import annotations

import json
from pathlib import Path

from igp import baseline, coverage, submission

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "submissions"
PROG = ROOT / "data" / "processed" / "progress.json"
MAX_POLYS, MAX_BYTES = submission.MAX_POLYS, submission.MAX_BYTES  # official: 1,000 / 1,000,000

# selection (exact-vs-mixed, baseline-beats-D_base) + expected_score live in igp.coverage, the ONE
# canonical best-by-pair view shared with reconcile + producer_value (review 2026-07-11).
expected_score = coverage.exp_score


def main() -> None:
    prog = json.loads(PROG.read_text()) if PROG.exists() else {}
    best = coverage.best_by_pair()
    ranked = sorted(best.items(),
                    key=lambda kv: -expected_score(kv[0][0], kv[0][1], kv[1]["disc"], prog))
    OUT.mkdir(exist_ok=True)
    manifest, fileno, batch, nbytes = [], 0, [], 0
    for (t, r), b in ranked:
        line = b["line"]
        if batch and (len(batch) >= MAX_POLYS or nbytes + len(line) + 1 > MAX_BYTES):
            fileno += 1
            (OUT / f"submission_{fileno:03d}.txt").write_text("\n".join(batch) + "\n")
            batch, nbytes = [], 0
        batch.append(line)
        nbytes += len(line) + 1
        manifest.append({"file": fileno + 1, "label": f"24T{t}", "r": r, "source": b["source"],
                         "scoring_disc": str(b["disc"]), "disc_source": b["disc_source"],
                         "exact": b["exact"], "baseline": baseline.is_baseline(t, r),
                         "exp_score": round(expected_score(t, r, b["disc"], prog), 4)})
    if batch:
        fileno += 1
        (OUT / f"submission_{fileno:03d}.txt").write_text("\n".join(batch) + "\n")
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=0))
    ex = sum(1 for m in manifest if m["exact"])
    print(f"built {fileno} file(s), {len(ranked)} sigs ({ex} exact / {len(ranked)-ex} mixed); "
          f"manifest in submissions/ (limits {MAX_POLYS} polys / {MAX_BYTES} bytes)")


if __name__ == "__main__":
    main()
