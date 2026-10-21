"""Fetch + vendor the official IGP24 public competition package (SAIRcompetition/IGP24-public).

Clones the repo into data/raw/ (gitignored, re-fetchable) and derives the committed canonical
indexes into data/targets/:
  - baseline_signatures.csv  (t, r, D_base)  -- D_base = min exact nfdisc per baseline pair
  - valid_pairs.csv          (label, r)      -- the authoritative 165,836 achievable (24Tt, r)
  - nonsolvable_t.txt        the 807 non-solvable t
Also vendors the official mixed_disc.gp reference. The package confirms our scoring model
(2^(1-k)*log(D0)/log(D); baseline pairs need exact nfdisc < D_base). Run: uv run python <this>.
"""

from __future__ import annotations

import csv
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "igp24_public"
TARGETS = ROOT / "data" / "targets"
REPO = "https://github.com/SAIRcompetition/IGP24-public"


def main() -> None:
    if RAW.exists():
        shutil.rmtree(RAW)
    RAW.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--depth", "1", REPO, str(RAW)], check=True,
                   capture_output=True, text=True)
    comp = RAW / "competition"

    # baseline_signatures.csv: D_base = smallest exact nfdisc per (t, r)
    dbase: dict = {}
    for row in csv.DictReader((comp / "baseline" / "lmfdb_baseline.csv").open()):
        t = row["label"].replace("24T", "")
        d = int(row["nfdisc_abs"])
        dbase[(t, row["r"])] = min(dbase.get((t, row["r"]), d), d)
    with (TARGETS / "baseline_signatures.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["t", "r", "d_base"])
        for (t, r), d in sorted(dbase.items(), key=lambda kv: (int(kv[0][0]), int(kv[0][1]))):
            w.writerow([t, r, d])

    shutil.copy(comp / "baseline" / "valid_pairs.csv", TARGETS / "valid_pairs.csv")
    shutil.copy(comp / "baseline" / "nonsolvable_t.txt", TARGETS / "nonsolvable_t.txt")
    shutil.copy(comp / "tools" / "number_field_discriminant" / "mixed_disc.gp",
                ROOT / "src" / "igp" / "mixed_disc.gp")  # official scoring-disc fallback

    print(f"baseline pairs: {len(dbase)} | derived data/targets/{{baseline_signatures,valid_pairs,"
          f"nonsolvable_t}} + src/igp/mixed_disc.gp; raw clone in data/raw/igp24_public/")


if __name__ == "__main__":
    main()
