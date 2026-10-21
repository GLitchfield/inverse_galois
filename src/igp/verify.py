"""Verification loop interface: cheap local pre-filter -> authoritative checks.

The IGP24 verify/score path (confirmed; see docs/competition_rules.md) is split:
  - Magma decides the math: irreducible + degree-24 + the transitive 24Tt label
    (and the real-root count r).
  - PARI/GP ``nfdisc`` computes the official SCORING discriminant (field disc,
    60 s/poly, with a mixed-discriminant fallback).

This module wires the *local* pre-filter (``polys``, runs anywhere) to those two
authoritative backends. The backends are not yet available in this environment
(no PARI/GP, no Magma, and the SAIR MAGMA API endpoint/auth are pending the
``/api`` docs), so they raise ``NotImplementedError`` with a clear message
rather than fabricating a result. ``local_prefilter`` is fully functional now.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from sympy import primerange

from . import gap, gp, polys

# A wider prime set than the local pre-filter's: rare-but-discriminating cycle types
# (e.g. an 8-cycle present in one candidate at frequency ~0.1) need enough samples to
# show up and separate same-cycle-type-set groups.
IDENT_PRIMES: list[int] = list(primerange(3, 2000))


@dataclass
class LocalReport:
    """Result of the cheap, local, network-free pre-filter."""

    degree: int
    irreducible: bool
    poly_disc: int
    disc_is_square: bool          # Gal <= A_24 ?
    num_real_roots: int           # the signature coordinate r
    cycle_fingerprint: dict[tuple[int, ...], int] = field(default_factory=dict)

    @property
    def passes(self) -> bool:
        """Minimal admissibility: an irreducible degree-24 polynomial."""
        return self.degree == 24 and self.irreducible


@dataclass
class Verdict:
    """Authoritative result (from Magma + PARI nfdisc)."""

    t: int | None            # 24Tt index
    r: int | None            # real-root count
    field_disc: int | None   # official scoring discriminant (nfdisc / mixed)
    disc_source: str | None  # 'exact_nfdisc' | 'mixed_disc'
    poly_disc: int
    source: str              # which backend produced the label


def local_prefilter(coeffs, *, ascending: bool = True, primes=polys.DEFAULT_PRIMES) -> LocalReport:
    """Run the cheap local checks on a candidate (no CAS, no network)."""
    p = polys.poly_from_coeffs(coeffs, ascending=ascending)
    disc = polys.poly_discriminant(p)
    return LocalReport(
        degree=p.degree(),
        irreducible=polys.is_irreducible(p),
        poly_disc=disc,
        disc_is_square=polys.is_perfect_square(disc),
        num_real_roots=polys.num_real_roots(p),
        cycle_fingerprint=dict(polys.frobenius_cycle_types(p, primes=primes)),
    )


def pari_nfdisc(coeffs, *, ascending: bool = True, timeout: float = 70.0) -> int:
    """Official scoring discriminant via PARI/GP ``nfdisc`` (system ``gp``)."""
    return gp.nfdisc(coeffs, ascending=ascending, timeout=timeout)


def local_fingerprint(coeffs, *, ascending: bool = True, primes=polys.DEFAULT_PRIMES) -> dict:
    """Local invariants of a candidate: parity (=> A_24?), proper subfield degrees
    (block structure), and the set of observed Frobenius cycle types. (WS-INFRA-A.)
    """
    p = polys.poly_from_coeffs(coeffs, ascending=ascending)
    return {
        "degree": p.degree(),
        "irreducible": polys.is_irreducible(p),
        "in_a24": polys.is_perfect_square(polys.poly_discriminant(p)),
        "subfield_degrees": gp.subfield_degrees(coeffs, ascending=ascending),
        "cycle_types": set(polys.frobenius_cycle_types(p, primes=primes)),
    }


def _s24_skip(cycle_types, in_a24: bool) -> bool:
    """Decision rule for `likely_negligible_s24` (pure, so it's unit-testable).

    A cycle of prime length in {13,17,19} forces primitivity (those lengths are coprime to every
    block size dividing 24) AND excludes the degree-24 Mathieu/projective primitives (|M_24|,
    |PSL(2,23)|, |PGL(2,23)| are not divisible by 13/17/19) -- leaving only A_24 or S_24 (Jordan).
    Square discriminant => A_24 (rare, valuable -> keep); otherwise S_24 -> skip. Lengths 11 and 23
    are deliberately NOT triggers, since M_24 / PSL(2,23) realize those cycles.
    """
    has_big = any(L in (13, 17, 19) for ct in cycle_types for L in ct)
    return has_big and not in_a24


def likely_negligible_s24(coeffs, *, ascending: bool = True, primes=polys.DEFAULT_PRIMES) -> bool:
    """True if Frobenius cycle types force the group to be S_24 (negligible score), so the daemon
    can skip it and spend verifier budget on imprimitive / rare groups. Safe: never skips A_24
    (square disc) or the Mathieu/projective primitives. Avoids the gp subfield call in
    `local_fingerprint` (this runs in the daemon hot loop)."""
    p = polys.poly_from_coeffs(coeffs, ascending=ascending)
    cts = set(polys.frobenius_cycle_types(p, primes=primes))
    if not any(L in (13, 17, 19) for ct in cts for L in ct):
        return False  # short-circuit: skip the discriminant computation in the common case
    return _s24_skip(cts, polys.is_perfect_square(polys.poly_discriminant(p)))


def likely_negligible_s24_fast(coeffs, *, ascending: bool = True) -> bool:
    """gp-backed `likely_negligible_s24` (same decision, ~20x faster and subprocess-parallel);
    falls back to the sympy path on any gp hiccup. Runs in the daemon's worker threads."""
    try:
        from . import gp as _gp
        has_big, disc_square = _gp.s24_probe(coeffs, ascending=ascending)
        return has_big and not disc_square
    except Exception:
        return likely_negligible_s24(coeffs, ascending=ascending)


def confirm_label(coeffs, t, *, ascending: bool = True, fingerprint: dict | None = None):
    """Is a candidate consistent with being 24Tt? Local check (no Magma).

    Compares parity, the proper-subfield-degree set, and Frobenius cycle types
    against 24Tt's GAP invariants. Returns ``(ok, checks)``. ``ok`` True = consistent
    (strong evidence, not a proof — distinct groups can share these invariants);
    any False = the polynomial is NOT 24Tt.
    """
    fp = fingerprint or local_fingerprint(coeffs, ascending=ascending)
    gi = gap.group_invariants(t)
    checks = {
        "parity": fp["in_a24"] == gi["in_an"],
        "subfields": set(fp["subfield_degrees"]) == set(gi["subfield_degrees"]),
        "cycle_types_subset": fp["cycle_types"] <= gi["cycle_types"],
    }
    return all(checks.values()), checks


def identify(coeffs, candidates, *, ascending: bool = True, primes=IDENT_PRIMES, dists=None):
    """Rank candidate 24Tt labels for a polynomial by Chebotarev cycle-type likelihood.

    The resolvent-lite upgrade to ``confirm_label``: instead of the too-weak "observed
    cycle types ⊆ candidate's set" (which let 24T2456 pass as 24T12727, test 0006), match
    the observed cycle-type *distribution* to each candidate's expected distribution.

    For candidate G, log-likelihood = Σ_ct n(ct)·log(p_G(ct)) where n(ct) = #good primes
    giving factorization pattern ``ct`` and p_G(ct) = (#elements of G with that cycle
    type)/|G|. Any observed ``ct`` impossible in G (p_G=0) sets the likelihood to -inf
    (hard exclusion). Returns the MLE label, the full ranking, and a separation ``margin``
    (log-likelihood gap to the runner-up; ``inf`` if the runner-up was hard-excluded).

    Statistical, not a proof — Magma remains authoritative — but it cleanly separates the
    same-invariant collisions and is a strong offline pre-confirmer (saves API calls).
    """
    p = polys.poly_from_coeffs(coeffs, ascending=ascending)
    obs = polys.frobenius_cycle_types(p, primes=primes)
    n_eff = sum(obs.values())
    dists = dists or gap.cycle_type_distributions(list(candidates))
    ranked = []
    for t in candidates:
        order = dists[t]["order"]
        dist = dists[t]["dist"]
        loglik = 0.0
        impossible = []
        for ct, n in obs.items():
            cnt = dist.get(ct, 0)
            if cnt == 0:
                impossible.append(ct)
                loglik = -math.inf
            elif loglik != -math.inf:
                loglik += n * math.log(cnt / order)
        ranked.append({"t": t, "loglik": loglik, "impossible": impossible})
    ranked.sort(key=lambda r: r["loglik"], reverse=True)
    top = ranked[0]
    best = top["t"] if top["loglik"] != -math.inf else None
    margin = math.inf
    if len(ranked) > 1 and ranked[1]["loglik"] != -math.inf:
        margin = top["loglik"] - ranked[1]["loglik"]
    return {"best": best, "margin": margin, "ranked": ranked,
            "observed": dict(obs), "n_primes": n_eff}


def magma_verify(coeffs, *, ascending: bool = True) -> Verdict:
    """Authoritative 24Tt label + r via Magma. [pending SAIR MAGMA API / local Magma]

    Requires Magma. Use the SAIR free MAGMA API (endpoint/auth pending the
    ``/api`` docs) or a local Magma license.
    """
    raise NotImplementedError(
        "magma_verify needs Magma. Wire up the SAIR MAGMA API (see docs/harness_notes.md) "
        "or a local Magma; it returns the authoritative transitive 24Tt label and r."
    )
