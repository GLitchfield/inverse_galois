# 0017 — M24 (Mathieu), a PRIMITIVE degree-24 group, via Müller's Q(t)-family

**Family:** construction / primitive · **Date:** 2026-06-26 · **Modules:** `igp/gp.py`,
`scripts/q22_m24_primitive.py` · **External:** Müller, arXiv:1204.1328

## Question

The 5 primitive degree-24 groups (24T7817 PSL(2,23), 24T10255 PGL(2,23), **24T24680 M24**,
24T24999 A24, 24T25000 S24) have **no block system**, so the kernel-over-base machinery (tests
0010–0016) cannot touch them. Can we realize one — the Mathieu group **M24**?

## Method

Not de-novo construction — M24 needs an explicit family. Peter Müller's one-parameter family
(arXiv:1204.1328; data file `Papers/m24.sage`) is

    F_s(X) = (t − A_s(X))² + (1 + X²)·B_s(X)²,   Galois group M24 over Q(t)  (s ≠ 1).

Pipeline: take `s = 0` (a concrete member; A_0 deg 12, B_0 deg 10, embedded in q22 with
credit), specialize `t = 0` (not a branch point — `dis(0,0) ≠ 0`), giving a degree-24 `F(X)`
with leading coeff `2^44`. Monicize via `g(Y) = L^{23}·F(Y/L)` (huge but exact), then
`polredbest` → a small defining polynomial of the **same field** (same M24 closure). Verify on
Magma.

## Result

**24T24680 = M24 — Magma-confirmed, scoreable, non-baseline.** Both the raw monic `g` (4038-char
coeffs, ~316 digits) and the `polredbest` version verified as M24:

```
clean M24 poly (ascending a0..a24, 332 chars):
24856216304325362944, -10897577707247959040, 5255658192536042240, -2084897024849335296,
647106313478930592, -194330496057009600, 49072757202892304, -11617496986046880,
2447252012829953, -470648891645344, 83991847381640, -13220334412960, 2011932105948,
-262286382880, 34976811480, -3773261792, 462889030, -40465376, 4667960, -286176,
37052, -1440, 216, 0, 1
```

`r = 0` (totally complex), field disc ≈ `2.49×10^180` (huge — M24 fields are highly ramified;
`polredbest` shrinks the *polynomial*, not the field disc).

## Learnings

- **First primitive degree-24 group realized.** Primitive groups are a different regime: no
  construction engine of ours reaches them; the lever is an explicit published Q(t)-family +
  specialization. The reusable operation is **fetch family → specialize (s,t) avoiding branch
  points → monicize → polredbest → verify**.
- `polredbest` is essential and was the only slow step (the `2^44`-leading monic blows
  coefficients to ~300 digits; reduction brings them to ~20).
- **Remaining primitives:** `A24`/`S24` are trivial (a random degree-24 poly is S24; square
  discriminant gives A24). `PSL(2,23)` / `PGL(2,23)` (24T7817 / 24T10255) act on P¹(F₂₃) and
  should come from the Belyi-map literature (e.g. arXiv:1703.02848) — the next primitive targets.
- Combined with tests 0010–0016, we have now touched **every category**: solvable imprimitive,
  non-solvable imprimitive, and a primitive sporadic group.
