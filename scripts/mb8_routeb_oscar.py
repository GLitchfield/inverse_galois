"""Thin driver for the OSCAR relative-Kummer engine  (test 0052).

Runs scripts/oscar/mb8_routeb.jl, parses its ``MODEL:<t> <r> <25 ascending ints>`` lines,
and feeds each model through scripts/mb8_routeb.py's gate/enqueue (mb8_fix8.gate: deg24+irred,
polsturm==24, mb8_match density vs Gassmann/wreath, scoreable_disc -> lit:mb8new/pair/alt tiers
130/115/100).

TURNKEY but currently emits/enqueues NOTHING: the engine walls at spec-step (i) module-selection
(the F2[C3xL3(2)]-module decomposition needs the degree-168 L3(2)-closure, which does not build in
Hecke in 900s -- see data/processed/oscar_routeb_probe.json / docs/tests/0052).  The moment a
Magma (or future-Hecke) module-selection makes the engine emit a MODEL line, this driver gates +
enqueues it with no further changes.

Usage:
  python scripts/mb8_routeb_oscar.py            # run the engine, gate+enqueue any emitted models
  python scripts/mb8_routeb_oscar.py --dry-run  # run the engine, gate only (no enqueue)
  python scripts/mb8_routeb_oscar.py --models-file FILE  # skip the engine; read MODEL lines from FILE
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JULIA = Path.home() / ".juliaup" / "bin" / "julia"
ENGINE = ROOT / "scripts" / "oscar" / "mb8_routeb.jl"

_spec = importlib.util.spec_from_file_location("mb8_routeb", ROOT / "scripts" / "mb8_routeb.py")
mb8_routeb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mb8_routeb)
mb8_fix8 = mb8_routeb.mb8_fix8  # the certified gate()/enqueue_winners()

# 19280 = C3 top ; 20408 = S3 top.  src tag distinguishes provenance in the queue.
SRC = "oscar_relkummer"


def run_engine(timeout: float = 1200.0) -> str:
    """Run the OSCAR engine, return its stdout (MODEL lines + ladder verdict)."""
    if not JULIA.exists():
        raise RuntimeError(f"julia not found at {JULIA}")
    proc = subprocess.run([str(JULIA), str(ENGINE)], capture_output=True, text=True, timeout=timeout)
    return proc.stdout


def parse_models(text: str) -> list[dict]:
    """Parse ``MODEL:<t> <r> <c0,c1,...,c24>`` lines into gate-ready winner dicts.

    coeffs are stored as a LIST of 25 ASCENDING ints (a comma-STRING would die as `malformed`
    downstream); enqueue formatting to the 25-comma queue payload is done by enqueue_winners()."""
    winners = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln.startswith("MODEL:"):
            continue
        head, coeffstr = ln[len("MODEL:"):].rsplit(" ", 1)
        t, r = head.split()
        coeffs = [int(c) for c in coeffstr.split(",")]
        if len(coeffs) != 25:
            print(f"  SKIP malformed model (len {len(coeffs)} != 25): {ln[:60]}")
            continue
        winners.append({"t": int(t), "r": int(r), "coeffs": coeffs, "src": SRC})
    return winners


def gate_and_enqueue(winners: list[dict], *, dry_run: bool) -> dict:
    gated = []
    for w in winners:
        ok, info = mb8_fix8.gate(w["coeffs"], w["t"])
        print(f"  24T{w['t']} r{w['r']} src={w['src']}: {'PASS' if ok else 'REJECT'} {info}")
        if ok:
            gated.append({**w, "r": info["r"]})
    if not gated:
        print("no gated models to enqueue.")
        return {"new": 0, "pair": 0, "alt": 0}
    if dry_run:
        print(f"[dry-run] {len(gated)} model(s) would enqueue (lit:mb8new/pair/alt @ 130/115/100)")
        return {"new": 0, "pair": 0, "alt": 0}
    added = mb8_fix8.enqueue_winners(gated)  # tiers + set_priority_prefix lit:mb8new=130
    print(f"enqueued new {added['new']}@130 / pair {added['pair']}@115 / alt {added['alt']}@100")
    return added


def main() -> None:
    ap = argparse.ArgumentParser(description="OSCAR relative-Kummer engine driver (test 0052)")
    ap.add_argument("--dry-run", action="store_true", help="gate only, do not enqueue")
    ap.add_argument("--models-file", type=str, default=None,
                    help="read MODEL lines from FILE instead of running the engine")
    ap.add_argument("--timeout", type=float, default=1200.0, help="engine wall-clock budget (s)")
    args = ap.parse_args()

    if args.models_file:
        text = Path(args.models_file).read_text()
    else:
        print(f"running OSCAR engine: {ENGINE}")
        text = run_engine(timeout=args.timeout)
        # surface the ladder verdict / wall lines for the operator
        for ln in text.splitlines():
            if ln.startswith(("[CKPT]", "[WALL]", "===")):
                print("  " + ln)

    winners = parse_models(text)
    print(f"parsed {len(winners)} candidate model(s) from engine output")
    if not winners:
        print("engine emitted 0 models (walls at step (i) module-selection; "
              "see data/processed/oscar_routeb_probe.json). Nothing to enqueue.")
        return
    gate_and_enqueue(winners, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
