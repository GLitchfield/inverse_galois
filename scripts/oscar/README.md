# OSCAR local Galois-group verifier (Phase-0 spike, test 0026)

Exploratory: can we identify a degree-24 polynomial's `24Tt` Galois group **locally** (off the
SAIR-Magma critical path) using the open-source [OSCAR](https://www.oscar-system.org/) stack
(Hecke/GaloisGrp, Fieker–Klüners — the same algorithm family Magma uses)?

**Verdict (see `docs/tests/0026-oscar-local-verifier.md`):** correct, but slow and memory-heavy on
hard groups (tens of minutes; some need >16GB). Not a fast general verifier and does not enable
generative search. Kept as an occasional local cross-check, not a core dependency.

## Setup (one-time)

```bash
curl -fsSL https://install.julialang.org | sh -s -- --yes      # juliaup + Julia
julia -e 'using Pkg; Pkg.add("Oscar")'                         # heavy: pulls GAP/Singular/Nemo/Hecke
```

## Run (under a RAM cap — the box has 31GB, so cap below that + spill to disk)

cgroup v2 (`MemoryMax`) hard-caps **resident** RAM for the run — the kernel reclaims/swaps rather
than letting it grow, so the box is never exhausted. `MemorySwapMax` allows overflow to **disk
swap** (slow, but RAM stays bounded — a heavy run thrashes rather than OOM-kills). The original 16GB
cap (test 0026) OOM-killed 24T7871 because the heavy de-novo needed >16+8GB; with the box's 31GB we
cap at **22GB RAM** (leaves ~9GB for the system + the search daemon) and keep swap as a backstop:

```bash
# de-novo identification (no hints) vs our SAIR labels:
systemd-run --user --scope -p MemoryMax=22G -p MemorySwapMax=8G \
  ~/.juliaup/bin/julia --heap-size-hint=20G scripts/oscar/validate.jl

# seeded "confirm the predicted group" (option C): inject the known group ORDER as a descent filter
systemd-run --user --scope -p MemoryMax=22G -p MemorySwapMax=8G \
  ~/.juliaup/bin/julia --heap-size-hint=20G scripts/oscar/confirm.jl
```

To allow more disk overflow than the existing 8GB swap (so a RAM cap can stay low while the run
spills further to disk), add a swapfile once (needs sudo; `/` has ~786GB free):

```bash
sudo fallocate -l 32G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
# then raise the per-run cap, e.g.  -p MemorySwapMax=32G
```

`MemoryMax`/`MemorySwapMax` are per-run flags — tune both; RAM never exceeds `MemoryMax`.

## Files

- `test_polys.jl` — pinned ground-truth `(24Tt, ascending coeffs)` set used in 0026.
- `extract_test_polys.py` — regenerates a diverse set from `realized.csv` (selection provenance).
- `validate.jl` — de-novo `galois_group`, both coeff orderings (also confirms coeffs are ascending).
- `confirm.jl` — seeded Stauduhar descent: `order(x) >= known_order` filter prunes the sub-lattice.
