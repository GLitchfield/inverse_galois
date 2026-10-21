"""Official IGP24 reference data (from SAIRcompetition/IGP24-public; fetch via
scripts/fetch_competition_package.py, committed in data/targets/).

- baseline `(t,r)` -> `D_base`: a baseline pair scores ONLY if our exact nfdisc *strictly* beats
  `D_base` (mixed-disc cannot unlock baseline pairs).
- valid `(t,r)`: the 165,836 achievable signatures (authoritative `validR`).
- nonsolvable `t`: the 807 non-solvable groups (the hard residual, incl. the 5 primitive).

So a true 1.0 target is **valid AND non-baseline AND teamCount==0**; a baseline pair is only worth
pursuing if we can beat its `D_base`.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

TARGETS = Path(__file__).resolve().parents[2] / "data" / "targets"


@lru_cache(maxsize=1)
def baseline_dbase() -> dict:
    """(t, r) -> D_base: the baseline exact-nfdisc threshold a baseline pair must beat."""
    p = TARGETS / "baseline_signatures.csv"
    if not p.exists():
        return {}
    return {(row["t"], row["r"]): int(row["d_base"]) for row in csv.DictReader(p.open())}


@lru_cache(maxsize=1)
def valid_pairs() -> set:
    """The achievable (t, r) signatures (t with the `24T` prefix stripped)."""
    p = TARGETS / "valid_pairs.csv"
    if not p.exists():
        return set()
    return {(row["label"].replace("24T", ""), row["r"]) for row in csv.DictReader(p.open())}


@lru_cache(maxsize=1)
def nonsolvable_t() -> set:
    p = TARGETS / "nonsolvable_t.txt"
    return {ln.strip() for ln in p.read_text().splitlines() if ln.strip()} if p.exists() else set()


def is_baseline(t: str, r: str) -> bool:
    return (str(t), str(r)) in baseline_dbase()


def d_base(t: str, r: str) -> int | None:
    return baseline_dbase().get((str(t), str(r)))


def beats_baseline(t: str, r: str, disc: int) -> bool:
    """True iff `disc` strictly improves D_base for a baseline pair (the 0.5 unlock condition)."""
    db = d_base(t, r)
    return db is not None and disc < db
