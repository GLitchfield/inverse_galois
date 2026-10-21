# 0026 — OSCAR as a local degree-24 Galois verifier (de-novo + seeded "confirm")

**Family:** infra / verification · **Date:** 2026-06-28 · **Code:** `scripts/oscar/`
(`validate.jl`, `confirm.jl`, `test_polys.jl`, `extract_test_polys.py`)

## Question

Authoritative verification is the SAIR-Magma API (rate-limited, on the critical path). Can we
identify a degree-24 polynomial's `24Tt` group **locally** with the open-source OSCAR stack
(Hecke/GaloisGrp, Fieker–Klüners — Magma's algorithm family), to (a) pre-confirm submissions off
the API budget and (b) potentially enable *generative* search (throw polys, identify locally)? And
since our constructions always *predict* the group, does **seeding that knowledge** (option C) make
the hard cases tractable? All under a hard **16GB physical-RAM** cap (cgroup v2).

## Method

Installed Julia 1.12 + OSCAR. 12 ground-truth polys spread across `t` from `realized.csv` (labels
from SAIR-Magma, so trustworthy). All runs under `systemd-run --user --scope -p MemoryMax=16G
-p MemorySwapMax=8G julia --heap-size-hint=14G`.

- **De-novo** (`validate.jl`): `galois_group(f)` cold, both coeff orderings (also pins our
  convention), compare to known label, time each.
- **Confirm / option C** (`confirm.jl`): replicate the `galois_group` prologue (`find_prime` →
  `GaloisCtx` → `starting_group`) verbatim, then push one extra filter `order(x) >= o_known`
  (`o_known = order(transitive_group(24, t))`) into the descent `GroupFilter`, then call the public
  `descent`. `DescentEnv` applies the filter **before** building each maximal subgroup's resolvent,
  so subgroups smaller than the answer (incl. the answer's own confirming resolvents) are skipped.

## Result

**Correctness: perfect.** Every group OSCAR returned matched the SAIR-Magma label, both de-novo
(5/5 before an OOM) and seeded (4/4). Coeffs confirmed **ascending**.

**De-novo timing is brutally heavy-tailed** (first call includes ~30-40s JIT):

| group | de-novo | note |
|---|---|---|
| 24T2 | 55.7s | incl. JIT |
| 24T163 | 69.1s | |
| 24T577 | 22.5s | |
| 24T1627 | **4419.8s (73.7 min)** | mid-range t, not near S₂₄ |
| 24T5338 | **2111.2s (35.2 min)** | |
| 24T7871 | **OOM** | killed at 15.4GB anon-rss (cgroup OOM-killer; `dmesg` confirms) |

The 16GB cap held exactly — DRAM never exceeded 16GB; the heavy group died instead of eating the box.

**Seeded descent (C): a memory win, a modest speed win.**

| group | de-novo | seeded (C) | Δ |
|---|---|---|---|
| 24T577 | 22.5s | 34.3s | — (easy: nothing to prune; +JIT) |
| 24T1627 | 73.7 min | 52.8 min | −28% |
| 24T5338 | 35.2 min | 31.9 min | −9% |
| 24T7871 | OOM @16GB | **16.0 min, fits** | rescued (swap stayed 0 ⇒ genuinely in DRAM) |

## Learnings

- **OSCAR is a correct local verifier, but not a fast one.** Magma's "seconds" is decades of
  optimization we can't cheaply replicate: some *mid-lattice* (not just giant) degree-24 groups cost
  tens of minutes and >16GB. This independently validates *why* the competition verifies with Magma.
- **C's gain is mostly memory, not speed.** The order-seed prunes resolvents at/below the answer
  level — enough to rescue 24T7871 under 16GB — but the dominant cost is the descent **path** from
  the starting group down (each level's resolvents), which the seed doesn't touch ⇒ only −9–28%.
- **Generative search stays off the table.** An unknown-group poly could land on a 30–70 min / OOM
  case, so local triage of random/sweep output isn't viable. (Corrects the earlier optimistic pitch.)
- **Where it's usable:** *our* pipeline always knows the predicted group, so C-style confirm is the
  right local mode — confirm the easy bulk in seconds under a per-poly timeout, defer the slow tail
  to SAIR. Marginal now (the SAIR cap is 1000/day, so Magma IDs in bulk for free), so kept as a
  cross-check, not wired into the daemon.
- Reproducer committed under `scripts/oscar/` (needs Julia+OSCAR; not a core dep).

## Empirical update (2026-06-29) — the 16GB OOM was a cap artifact; RAM cap raised; GPU N/A

- **The box has 31GB RAM; the 16GB cap was self-imposed.** Re-ran the de-novo case that OOM'd at
  16GB, 24T7871, under `MemoryMax=22G -p MemorySwapMax=8G` (still leaves ~9GB for the system +
  daemon): **`24T7871` correct in 342.6s (5.7 min), peak well under the cap, swap stayed 0.** So that
  OOM was a transient spike tripping the *tight* cap, not a real memory wall — de-novo (not even the
  seeded C mode) completes once given headroom. The README run-commands now use the 22GB cap.
- **Memory fixes the OOM class, not the slow tail.** 24T1627 (73 min) / 24T5338 (35 min) were *not*
  OOM — they're algorithmically deep descents; more RAM doesn't touch their time. So OSCAR is now:
  ~seconds (easy) → ~5 min (moderate, e.g. 24T7871) → 30–70 min (hard tail). Reliable offline, still
  not a hot-path gate.
- **`MemoryMax` (RAM) is kernel-hard, `MemorySwapMax` spills to disk** — so we can bound RAM (box
  never exhausted) and let a pathological case thrash to disk rather than OOM. Add a swapfile for more
  disk overflow (`scripts/oscar/README.md`).
- **No GPU path.** The workload is arbitrary-precision exact arithmetic + symbolic group theory +
  irregular lattice search + p-adic polynomial factorization — none of which maps to a GPU, and none
  of OSCAR's stack (Nemo/Hecke/Flint/GAP/Singular) has a CUDA backend. The OSCAR↔Magma gap is
  algorithmic maturity, not FLOPS. The real acceleration is CPU parallelism *across polynomials*
  (24 threads); the genuinely fast identifier is Magma via the API (free, 1000/day).
