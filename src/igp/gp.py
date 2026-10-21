"""PARI/GP backend (shell-out to the ``gp`` binary).

PARI/GP is a system dependency (`pari-gp`); we call the ``gp`` CLI rather than
linking ``cypari2`` so the project keeps a single uv-managed Python env. This
provides the field-theoretic operations sympy lacks — most importantly
``nfdisc``, the **official scoring discriminant** (the competition runs
``nfdisc`` with a 60 s/poly timeout and a mixed-disc fallback; see
docs/competition_rules.md).

Polynomials are passed as integer coefficient lists; ``ascending=True`` means
``coeffs[i]`` multiplies ``z**i``.
"""

from __future__ import annotations

import shutil
import subprocess

GP_BIN = shutil.which("gp") or "/usr/bin/gp"


class CASError(RuntimeError):
    """A computer-algebra backend (gp) failed, timed out, or is missing."""


def available() -> bool:
    return shutil.which("gp") is not None


def _run_gp(body: str, timeout: float = 70.0) -> str:
    script = "default(parisizemax, 2*10^9);\n" + body + "\n"
    try:
        proc = subprocess.run(
            [GP_BIN, "-q"], input=script, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as e:
        raise CASError(f"gp not found at {GP_BIN!r}; install pari-gp") from e
    except subprocess.TimeoutExpired as e:
        raise CASError(f"gp timed out after {timeout}s") from e
    out = proc.stdout.strip()
    if proc.returncode != 0 or "***" in proc.stdout:  # gp reports errors with "*** at..."
        raise CASError(f"gp error: {(proc.stderr or proc.stdout).strip()[:400]}")
    return out


def _poly(coeffs, ascending: bool) -> str:
    cs = [int(c) for c in coeffs]
    if ascending:
        cs = cs[::-1]  # PARI Pol() takes coefficients highest-degree first
    return f"Pol({cs})"


def nfdisc(coeffs, *, ascending: bool = True, timeout: float = 70.0) -> int:
    """Absolute discriminant of the number field defined by the polynomial.

    This is the official IGP24 *scoring* discriminant (for the exact path).
    Requires a monic irreducible integer polynomial.
    """
    return int(_run_gp(f"print(nfdisc({_poly(coeffs, ascending)}))", timeout))


def scoreable_disc(coeffs, *, ascending: bool = True, budget: int = 55,
                   smooth_bound: int = 10**6) -> int | None:
    """Predict whether SAIR's scoring ``nfdisc`` (60 s bounded) will certify this poly.

    Returns the absolute field discriminant if ``nfdisc`` computes it within ``budget``
    seconds (=> the grader can too => the poly SCORES), else ``None``.

    NOTE (2026-07-05, unresolved): this uses nfdisc-completion. It is NOT confirmed to
    match SAIR's grader — the 18440 trophy recorded scoreable=False/blank-disc while
    22336 scored, yet BOTH compute discs locally in <0.02 s. A poldisc-smoothness
    variant was tried and rejected 22336 (which scored), so that is wrong too. The
    18440 blank may be collection lag (row captured before SAIR finished scoring; never
    re-fetched due to pending_remove) rather than genuine non-scoreability. Treat this
    as a best-effort filter until the mechanism is pinned down by re-fetching SAIR.
    """
    _ = smooth_bound  # reserved; poldisc-smoothness variant rejected (it failed 22336)
    try:
        out = _run_gp(f"print(nfdisc({_poly(coeffs, ascending)}))", timeout=budget).strip()
    except CASError:
        return None
    try:
        return int(out)
    except ValueError:
        return None


def poldisc(coeffs, *, ascending: bool = True, timeout: float = 70.0) -> int:
    """Polynomial discriminant (differs from nfdisc by the index squared)."""
    return int(_run_gp(f"print(poldisc({_poly(coeffs, ascending)}))", timeout))


def real_roots(coeffs, *, ascending: bool = True, timeout: float = 30.0) -> int:
    """Number of real roots r (the IGP24 signature coordinate), via PARI polsturm — fast + exact.
    Lets us pick a construction's signature `r` BEFORE submitting (to target a specific `(t,r)`)."""
    return int(_run_gp(f"print(polsturm({_poly(coeffs, ascending)}))", timeout).strip())


def polredbest(coeffs, *, ascending: bool = True, timeout: float = 70.0) -> list[int]:
    """A small-coefficient polynomial defining the same field (ascending coeffs)."""
    out = _run_gp(f"print(Vec(polredbest({_poly(coeffs, ascending)})))", timeout)
    vals = [int(x) for x in out.strip("[]").split(",")]
    return vals[::-1]  # back to ascending


def _parse_vec(out: str) -> list[int]:
    return [int(x) for x in out.strip("[]").split(",")][::-1]  # PARI Vec is descending -> ascending


def script(body: str, *, timeout: float = 300.0) -> str:
    """Run an ad-hoc gp script and return its printed output (research escape hatch)."""
    return _run_gp(body, timeout)


def c2_split_construct(w, n: int = 13, q: int = 53, prim_root: int = 2,
                       timeout: float = 300.0) -> list[int]:
    """Build K = Q(zeta_n)(sqrt(alpha)) realizing the C_2-kernel from pattern `w`.

    `alpha = prod_j sigma^j(pi)^{w_j}` where pi generates a prime above the split prime
    `q` (= 1 mod n), and sigma: zeta -> zeta^prim_root generates Gal. The realized
    kernel = the H-submodule generated by `w` (its valuation pattern). Returns the
    absolute degree-2*(n-1) coefficients (ascending). The construction side of A→w→α.
    """
    idx = [j for j, wj in enumerate(w) if wj]
    if not idx:
        raise ValueError("w = 0 gives a degenerate (square) alpha")
    terms = "*".join(f"Mod(subst(lift(p0),'y,'y^{pow(prim_root, j, n)}),F)" for j in idx)
    body = (
        f"F=polcyclo({n},'y); bnf=bnfinit(F);\n"
        f"p0=nfbasistoalg(bnf, bnfisprincipal(bnf, idealprimedec(bnf,{q})[1])[2]);\n"
        f"al=lift({terms});\n"
        # polredbest reduces coeffs: faster verify + smaller disc
        "print(Vec(polredbest(rnfequation(F,'x^2 - al))))"
    )
    return [int(x) for x in _run_gp(body, timeout).strip("[]").split(",")][::-1]


def quadratic_ext(f_coeffs, alpha: str, *, timeout: float = 180.0) -> list[int]:
    """Absolute defining polynomial (ascending coeffs) of F(sqrt(alpha)).

    ``f_coeffs`` (ascending) defines the base field F in variable ``y``; ``alpha`` is
    a gp expression in ``y`` (e.g. ``"2"``, ``"y+1"``, ``"y^2-2"``). Returns the
    degree-2*deg(F) absolute polynomial via PARI ``rnfequation`` (or a shorter list
    if ``alpha`` is a square in F, i.e. degenerate). The WS4 C_2-kernel step.
    """
    cs = [int(c) for c in f_coeffs][::-1]  # descending for Pol(...,'y)
    out = _run_gp(f"print(Vec(rnfequation(Pol({cs},'y), 'x^2 - ({alpha}))))", timeout)
    return [int(x) for x in out.strip("[]").split(",")][::-1]


def cyclotomic_top_perms(n: int) -> list[list[int]]:
    """The top action ``cyclotomic_c2`` uses, as 0-indexed permutations on the units of n.

    Gal(Q(zeta_n)/Q) = (Z/n)* acts on the sorted units (= the blocks) by multiplication;
    each unit ``u`` gives a permutation ``pos[a] -> pos[u*a mod n]``. Returns one perm per
    unit (a generating set, redundant but exact). Feed to ``gap.kernel_label_perms`` so the
    group prediction shares the field construction's action — the alignment for intermediate
    kernels.
    """
    from math import gcd

    units = [a for a in range(1, n) if gcd(a, n) == 1]
    pos = {u: i for i, u in enumerate(units)}
    return [[pos[(u * a) % n] for a in units] for u in units]


def cyclotomic_c2_multi(n: int, pairs, *, timeout: float = 400.0) -> list[int]:
    """Multi-prime cyclotomic C_2-kernel: realizes a non-cyclic kernel `<H·w_i : i>`.

    ``pairs`` = ``[(q_1, w_1), …]`` with distinct split primes ``q_i ≡ 1 (mod n)``; each
    contributes generator ``w_i`` to the kernel via ``alpha = prod_i prod_{w_i[a]=1}
    sigma_a(pi_i)``. Returns the degree-2*phi(n) field (ascending). Pairs with
    ``gap.kernel_labels_multigen`` for the full submodule lattice over a cyclotomic top.
    """
    from math import gcd

    units = [a for a in range(1, n) if gcd(a, n) == 1]
    setup = [f"F=polcyclo({n},'y); bnf=bnfinit(F);"]
    terms = []
    for k, (q, w) in enumerate(pairs):
        idx = [units[j] for j, wj in enumerate(w) if wj]
        if not idx:
            continue
        setup.append(f"p{k}=nfbasistoalg(bnf, bnfisprincipal(bnf, idealprimedec(bnf,{q})[1])[2]);")
        terms.append("*".join(f"Mod(subst(lift(p{k}),'y,'y^{a}),F)" for a in idx))
    if not terms:
        raise ValueError("all-zero kernel")
    body = "\n".join(setup) + (
        f"\nal=lift({'*'.join(terms)});\nprint(Vec(polredbest(rnfequation(F,'x^2 - al))))"
    )
    return [int(x) for x in _run_gp(body, timeout).strip("[]").split(",")][::-1]


def galois_c2_multi(f_coeffs, pairs, *, timeout: float = 400.0) -> list[int]:
    """Multi-prime C_2-kernel over a Galois base: realizes a non-cyclic kernel `<H·w_i : i>`.

    ``f_coeffs`` defines a Galois base (h=1); ``pairs`` = ``[(q_i, w_i)]`` with distinct
    completely-split primes. ``alpha = prod_i prod_{w_i[a]=1} sigma_a(pi_i)``. Returns the
    degree-24 field (ascending). Multi-generator analogue of ``galois_c2``.
    """
    cs = [int(c) for c in f_coeffs][::-1]
    setup = [f"f=Pol({cs},'y);bnf=bnfinit(f);cj=nfgaloisconj(f);"]
    terms = []
    for k, (q, w) in enumerate(pairs):
        idx = [j + 1 for j, wj in enumerate(w) if wj]
        if not idx:
            continue
        setup.append(f"pi{k}=lift(nfbasistoalg(bnf,bnfisprincipal(bnf,idealprimedec(bnf,{q})[1])[2]));")
        terms.append("*".join(f"Mod(subst(pi{k},'y,cj[{a}]),f)" for a in idx))
    if not terms:
        raise ValueError("all-zero kernel")
    body = "\n".join(setup) + (
        f"\nal=lift({'*'.join(terms)});\nprint(Vec(polredbest(rnfequation(f,'x^2 - al))))"
    )
    return [int(x) for x in _run_gp(body, timeout).strip("[]").split(",")][::-1]


def cyclotomic_c2(w, n: int, q: int, *, timeout: float = 300.0) -> list[int]:
    """C_2-kernel construction over Q(zeta_n) for ANY conductor (not just cyclic Gal).

    Enumerates the Galois automorphisms as zeta -> zeta^a over the units a of n (sorted),
    so `w` is a 0/1 pattern indexed by those units; alpha = prod_{w_a=1} sigma_a(pi) for
    pi a generator of a prime above the split prime `q` (= 1 mod n). Generalizes
    ``c2_split_construct`` (which assumed a cyclic group via a primitive root) to abelian
    tops like Q(zeta_21) = C_2 x C_6. Returns the degree-2*phi(n) coeffs (ascending).
    """
    from math import gcd

    units = [a for a in range(1, n) if gcd(a, n) == 1]
    if len(w) != len(units):
        raise ValueError(f"w has length {len(w)}, expected phi({n})={len(units)}")
    idx = [units[j] for j, wj in enumerate(w) if wj]
    if not idx:
        raise ValueError("w = 0 gives a degenerate (square) alpha")
    terms = "*".join(f"Mod(subst(lift(p0),'y,'y^{a}),F)" for a in idx)
    body = (
        f"F=polcyclo({n},'y); bnf=bnfinit(F);\n"
        f"p0=nfbasistoalg(bnf, bnfisprincipal(bnf, idealprimedec(bnf,{q})[1])[2]);\n"
        f"al=lift({terms});\n"
        "print(Vec(polredbest(rnfequation(F,'x^2 - al))))"
    )
    return [int(x) for x in _run_gp(body, timeout).strip("[]").split(",")][::-1]


def split_primes(f_coeffs, ndeg: int, k: int = 1, hi: int = 20000,
                 *, timeout: float = 120.0) -> list[int]:
    """First ``k`` primes splitting completely in the degree-``ndeg`` field (idealprimedec==ndeg).

    Uses ``nfinit`` (not ``bnfinit``) — much faster for large-disc / non-Galois bases where we only
    need prime splitting, not the class group.
    """
    cs = [int(c) for c in f_coeffs][::-1]
    out = _run_gp(
        f"nf=nfinit(Pol({cs},'y));n=0;"
        f"for(q=2,{hi},if(isprime(q)&&#idealprimedec(nf,q)=={ndeg},print(q);n++;"
        f"if(n>={k},break)));",
        timeout)
    return [int(x) for x in out.split()]


def galois_action_perms(f_coeffs, *, timeout: float = 300.0) -> list[list[int]]:
    """Regular action of Gal(F/Q) on its 12 automorphisms, as 0-indexed perms.

    ``f_coeffs`` (ascending) must define a GALOIS number field F. With autos
    ``sigma_1..sigma_n = nfgaloisconj(f)`` (a fixed order), the primes above a split q are
    ``p_b = sigma_b(p_1)``, and ``sigma_a`` sends ``p_b -> p_c`` with ``sigma_c = sigma_a o
    sigma_b`` — left regular multiplication. Returns ``perm_a`` (one per auto) so that the
    valuation-vector action matches ``galois_c2``'s construction, for ``gap.kernel_label_perms``.
    """
    cs = [int(c) for c in f_coeffs][::-1]
    body = (
        f"f=Pol({cs},'y);cj=nfgaloisconj(f);n=#cj;\n"
        "cm=vector(n,c,Mod(cj[c],f));\n"
        "cp(a,b)=my(h=Mod(subst(cj[a],'y,cj[b]),f));for(c=1,n,if(cm[c]==h,return(c)));\n"
        "print(vector(n,a,vector(n,b,cp(a,b))));"
    )
    out = _run_gp(body, timeout)
    rows = out.strip("[]").split("], [")
    return [[int(x) - 1 for x in r.strip("[]").split(",")] for r in rows]


def galois_c2(f_coeffs, w, q: int, *, timeout: float = 300.0) -> list[int]:
    """C_2-kernel construction over an arbitrary GALOIS degree-12 base field F.

    ``f_coeffs`` (ascending) defines F (Galois, ideally h(F)=1); ``q`` splits completely in
    F. With pi a generator of one prime above q and autos ``sigma_a = nfgaloisconj(f)``,
    builds ``alpha = prod_{w_a=1} sigma_a(pi)`` and returns K = F(sqrt(alpha)) (degree 24,
    ascending). Pairs with ``galois_action_perms`` for prediction: realizes arbitrary
    order-12 tops (D_6, A_4, Dic_3, ...) in their regular action, not just cyclotomic ones.
    """
    idx = [j + 1 for j, wj in enumerate(w) if wj]
    if not idx:
        raise ValueError("w = 0 gives a degenerate (square) alpha")
    cs = [int(c) for c in f_coeffs][::-1]
    terms = "*".join(f"Mod(subst(pil,'y,cj[{a}]),f)" for a in idx)
    body = (
        f"f=Pol({cs},'y);bnf=bnfinit(f);cj=nfgaloisconj(f);\n"
        f"pi=nfbasistoalg(bnf,bnfisprincipal(bnf,idealprimedec(bnf,{q})[1])[2]);\n"
        "pil=lift(pi);\n"
        f"al=lift({terms});\n"
        "print(Vec(polredbest(rnfequation(f,'x^2 - al))));"
    )
    return [int(x) for x in _run_gp(body, timeout).strip("[]").split(",")][::-1]


def abelian_kernel(base_coeffs, n: int, *, hi_modulus: int = 80, smooth_bound: int = 10**6,
                   timeout: float = 300.0) -> tuple[list[int], int] | None:
    """CLASS-FIELD-THEORY kernel: a degree-``n`` CYCLIC (C_n) abelian extension of the base field F
    via RAY CLASS FIELDS (bnrinit + bnrclassfield), giving a deg-24 field (n = 24/deg F). This
    GENERALIZES general_c2 (the n=2 case) to arbitrary C_n over an arbitrary base -- the tractable
    (pure-PARI, no Magma) version of the Klüners-Malle systematic construction, reaching solvable
    groups the C_2-tower structurally can't (task #3/#4). Scans moduli m for a CYCLIC ray class
    group of order divisible by n, takes the C_n quotient's class field, and returns (ascending
    deg-24 coeffs, real-root count) if irreducible + nfdisc-smooth (<smooth_bound), else None."""
    cs = ",".join(str(int(c)) for c in base_coeffs[::-1])  # descending for Pol(...,'y)
    sb = str(smooth_bound)
    # gp parses stdin line-by-line: the whole for-loop must be ONE logical line (no internal \n).
    # A cyclic ray class group with n | order -> its C_n subfield's class field (matdiagonal([n])).
    loop = (
        f"for(m=2,{hi_modulus}, my(b=bnrinit(bnf,m)); my(c=b.cyc); "
        f"if(#c==1 && c[1]%{n}==0, "
        f"my(cf=iferr(bnrclassfield(b,matdiagonal([{n}])),e,0)); "
        "if(cf!=0, my(rel=if(type(cf)==\"t_POL\",cf,cf[1])); my(K=rnfequation(f,rel)); "
        "if(poldegree(K)==24 && polisirreducible(K), my(Kr=polredabs(K)); my(D=abs(nfdisc(Kr))); "
        f"my(fa=factor(D,{sb})); if(fa[#fa~,1]<{sb}, res=[Vec(Kr),polsturm(Kr)]; break)))));"
    )
    body = (f"f=Pol([{cs}],'y);bnf=bnfinit(f);res=0;\n{loop}\n"
            "if(res==0, print(\"NONE\"), print(res[2]); print(res[1]))")
    out = _run_gp(body, timeout).strip()
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines or lines[0].strip() == "NONE":
        return None
    try:
        r = int(lines[0].strip())
        coeffs = [int(x) for x in lines[1].strip("[]").split(",")][::-1]
    except (ValueError, IndexError):
        return None
    return (coeffs, r) if len(coeffs) == 25 else None


def general_c2(f_coeffs, w, q: int, *, timeout: float = 300.0) -> list[int]:
    """C_2-kernel over an ARBITRARY degree-12 base field F (Galois or NOT).

    Unlike ``galois_c2`` (which needs autos via ``nfgaloisconj``, so only Galois F → regular,
    small tops), this uses only the primes of F above a completely-split ``q``: ``alpha =
    prod_{w_j=1} pi_j`` where ``pi_j`` generates the j-th prime (in ``idealprimedec`` order),
    and ``K = F(sqrt alpha)``. Reaches the BIG tops (``12Tj`` with ``|H|>12``) that need a
    non-Galois base — including NON-SOLVABLE tops (A_5, ...), so the degree-24 group is itself
    non-solvable. Uses the PRODUCT ideal's generator, so it handles any class number ``h(F)``
    (not just 1); when ``h>1`` a pattern is realizable only if ``prod p_j`` is principal
    (returns [] otherwise — pick another ``w``). Needs ``q`` split completely (12 deg-1 primes).
    Returns degree-24 coeffs (ascending), or [] if not split / nonprincipal / degenerate.
    """
    idx = [j + 1 for j, x in enumerate(w) if x]
    if not idx:
        raise ValueError("w = 0 gives a degenerate (square) alpha")
    cs = [int(c) for c in f_coeffs][::-1]
    sel = ",".join(f"pr[{j}]" for j in idx)
    # Form the PRODUCT ideal prod p_j and take ITS generator: works for any class number
    # (the product can be principal even when individual primes are not — needed when
    # h(F)>1). NONPRINCIPAL => this pattern isn't realizable over F (pick another w).
    body = (
        f"f=Pol({cs},'y);bnf=bnfinit(f);pr=idealprimedec(bnf,{q});\n"
        "if(#pr!=12,print(\"NOTSPLIT\"); quit);\n"
        f"sel=[{sel}];Jd=sel[1];for(k=2,#sel,Jd=idealmul(bnf,Jd,sel[k]));\n"
        "pd=bnfisprincipal(bnf,Jd);\n"
        "if(#pd[1]>0 && vecmax(abs(pd[1]))>0, print(\"NONPRINCIPAL\"); quit);\n"
        "al=lift(nfbasistoalg(bnf,pd[2]));\n"
        "r=rnfequation(f,'x^2 - al);\n"
        "print(if(poldegree(r)<24,\"DEGENERATE\",Vec(polredbest(r))));"
    )
    out = _run_gp(body, timeout)
    if any(m in out for m in ("NOTSPLIT", "NONPRINCIPAL", "DEGENERATE")):
        return []
    return [int(x) for x in out.strip("[]").split(",")][::-1]


def general_c2_totpos(f_coeffs, w, q: int, *, timeout: float = 300.0) -> list[int]:
    """``general_c2`` forced to a TOTALLY-POSITIVE generator -> a DETERMINISTIC r=24 field.

    For K = F(sqrt(alpha)) over a totally-real deg-12 base F (r1=12), a real place v of F splits in
    K iff alpha >_v 0, so r(K) = 2*#{v : alpha >_v 0} and r=24 iff alpha is totally positive (dive
    #31, VERIFIED in PARI). ``general_c2`` takes whatever sign the product-ideal generator happens
    to have (~33% r=24 by luck); this post-processes that generator ``g`` to a totally-positive
    ``alpha = g * u`` by solving the unit sign-lattice ``bnfsignunit(bnf) . e = sign(g)`` over F2
    (Cohen's method). If the solve is UNSOLVABLE the ideal class is narrowly non-principal (the
    h+/h obstruction) -> returns [] (like NONPRINCIPAL), flagged before any build. Only valid over
    a TOTALLY-REAL base (needs r2=0 -- the sign vector has length r1). Returns degree-24 coeffs
    (ascending) at guaranteed r=24, or [] if not split / (narrowly) nonprincipal / degenerate.

    Caveat (dive #31): multiplying by the sign-fixing unit u changes alpha's SQUARE CLASS, so K may
    land a NEIGHBOR 24Tt vs plain ``general_c2`` on the same (base, w, q) -- fine for a breadth
    r=24 producer (open-gated post-hoc), NOT for a fixed-group target.
    """
    idx = [j + 1 for j, x in enumerate(w) if x]
    if not idx:
        raise ValueError("w = 0 gives a degenerate (square) alpha")
    cs = [int(c) for c in f_coeffs][::-1]
    sel = ",".join(f"pr[{j}]" for j in idx)
    body = (
        f"f=Pol({cs},'y);bnf=bnfinit(f,1);pr=idealprimedec(bnf,{q});\n"
        "if(#pr!=12,print(\"NOTSPLIT\"); quit);\n"
        f"sel=[{sel}];Jd=sel[1];for(k=2,#sel,Jd=idealmul(bnf,Jd,sel[k]));\n"
        "pd=bnfisprincipal(bnf,Jd);\n"
        "if(#pd[1]>0 && vecmax(abs(pd[1]))>0, print(\"NONPRINCIPAL\"); quit);\n"
        "g=nfbasistoalg(bnf,pd[2]);\n"
        "sg=apply(x->(1-x)/2, nfeltsign(bnf,g))~;\n"
        "MF=Mat(apply(x->(1-x)/2, bnfsignunit(bnf)));\n"
        "e=matsolvemod(MF,2,sg);\n"
        "if(type(e)==\"t_INT\" && e==0, print(\"NOTPOS\"); quit);\n"
        "fu=bnf.fu;u=1;for(k=1,#fu,if(lift(e[k]),u=u*nfbasistoalg(bnf,fu[k])));\n"
        "al=g*u;\n"
        "if(vecsum(apply(x->(1-x)/2, nfeltsign(bnf,al)))!=0, print(\"SIGNFAIL\"); quit);\n"
        "r=rnfequation(f,'x^2 - lift(al));\n"
        "print(if(poldegree(r)<24,\"DEGENERATE\",Vec(polredbest(r))));"
    )
    out = _run_gp(body, timeout)
    if any(m in out for m in ("NOTSPLIT", "NONPRINCIPAL", "NOTPOS", "SIGNFAIL", "DEGENERATE")):
        return []
    return [int(x) for x in out.strip("[]").split(",")][::-1]


def narrow_class_number(f_coeffs, *, timeout: float = 200.0) -> int:
    """Narrow (totally-positive) class number h+ of the field F=Q[y]/(f_coeffs). h+=1 <=> every
    principal ideal has a totally-positive generator <=> ``general_c2_totpos`` is solvable for EVERY
    (w, q) on this base (dive #31). LMFDB class_number=1 does NOT imply h+=1; this computes it."""
    cs = [int(c) for c in f_coeffs][::-1]
    out = _run_gp(f"print(bnfnarrow(bnfinit(Pol({cs},'y)))[1]);", timeout)
    return int(out.strip())


def nflist_fields(name: str, disc_lo: int, disc_hi: int, *, limit: int = 20,
                  timeout: float = 120.0) -> list[tuple[list[int], int]]:
    """Number fields whose Galois-closure group is ``name`` (PARI nflist naming: C4, V4, A4, C6, D6,
    C3, ...) with |disc| in [disc_lo, disc_hi]. Returns up to ``limit`` [([ascending coeffs], |field
    disc|), ...] -- the disc lets a caller enforce COPRIME factors (linear disjointness ⇒ the
    compositum is the full direct product, not a collapsed fiber product). ``limit`` caps how many
    fields get an nfdisc (the slow step) so this stays fast enough for the feed. nflist is ms.
    """
    body = (f'v=iferr(nflist("{name}",[{disc_lo},{disc_hi}]),e,[]);'
            f'v=vecextract(v,Vecsmall([1..min(#v,{int(limit)})]));'
            'for(i=1,#v,print(abs(nfdisc(v[i])),":",Vec(v[i])))')
    out = _run_gp(body, timeout)
    fields = []
    for line in out.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        dpart, cpart = line.split(":", 1)
        cpart = cpart.strip()
        if cpart.startswith("[") and "," in cpart and dpart.strip().lstrip("-").isdigit():
            try:
                coeffs = [int(x) for x in cpart.strip("[]").split(",")][::-1]
                fields.append((coeffs, abs(int(dpart.strip()))))
            except ValueError:
                pass
    return fields


def compositum24(f4: list[int], f6: list[int], *, smooth_bound: int = 10**6,
                 timeout: float = 30.0) -> tuple[list[int], int] | None:
    """Compositum of two coprime-disc small fields -> a deg-24 field (when linearly disjoint), the
    product-action group's field. Returns (ascending coeffs of polredabs, real-root count) if it is
    deg-24 + irreducible + nfdisc-smooth (no prime factor > smooth_bound -> always scoreable, no
    grader blank), else None (not disjoint, or a rough disc)."""
    a = ",".join(str(c) for c in f4[::-1])
    b = ",".join(str(c) for c in f6[::-1])
    body = (
        f"f=Pol([{a}]);g=Pol([{b}]);C=polcompositum(f,g);h=0;\n"
        "for(i=1,#C,if(poldegree(C[i])==24 && polisirreducible(C[i]),h=C[i]));\n"
        "if(h==0,print(\"NONE\"),H=polredabs(h);D=abs(nfdisc(H));"
        f"fa=factor(D,{smooth_bound});bad=0;"
        f"for(i=1,matsize(fa)[1],if(fa[i,1]>{smooth_bound},bad=1));"
        "if(bad,print(\"ROUGH\"),print(polsturm(H));print(Vec(H))))"
    )
    out = _run_gp(body, timeout).strip()
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines or lines[0].strip() in ("NONE", "ROUGH"):
        return None
    try:
        r = int(lines[0].strip())
        coeffs = [int(x) for x in lines[1].strip("[]").split(",")][::-1]
    except (ValueError, IndexError):
        return None
    return (coeffs, r) if len(coeffs) == 25 else None


def smooth_or_reduce(coeffs, *, bound: int = 100000, ascending: bool = True,
                     timeout: float = 60.0) -> list[int]:
    """The L1 smoothness gate (task #15, tripwire fired 2026-07-04): if poldisc has a cofactor
    the grader's bounded factorization can't clear, try polredabs for a smoother model; keep
    whichever is smooth (or the original -- a mixed-disc claim still claims the pair, so this
    never drops). ~ms when already smooth (the common case)."""
    cs = [int(c) for c in coeffs]
    dsc = cs[::-1] if ascending else cs
    body = (
        f"f=Pol({dsc});D=abs(poldisc(f));fa=factor(D,{bound});cof=1;\n"
        f"for(i=1,matsize(fa)[1],if(fa[i,1]>{bound},cof*=fa[i,1]^fa[i,2]));\n"
        f"if(cof==1,print(\"SMOOTH\"), g=polredabs(f);D2=abs(poldisc(g));fa2=factor(D2,{bound});"
        f"cof2=1;for(i=1,matsize(fa2)[1],if(fa2[i,1]>{bound},cof2*=fa2[i,1]^fa2[i,2]));"
        "if(cof2<cof,print(Vec(g)),print(\"KEEP\")));"
    )
    try:
        out = _run_gp(body, timeout)
    except CASError:
        return list(coeffs)
    if "SMOOTH" in out or "KEEP" in out:
        return list(coeffs)
    vals = [int(x) for x in out.strip("[]").split(",")][::-1]
    return vals if len(vals) == len(cs) else list(coeffs)


def s24_probe(coeffs, *, ascending: bool = True, timeout: float = 60.0) -> tuple[bool, bool]:
    """(has_13_17_19_cycle, disc_is_square) for the S24-skip filter, via factormod shape at the
    good primes in (3,200) -- the C-speed replacement for the sympy path (203ms serial -> ~10ms
    in the already-parallel worker subprocess). Semantics match polys.frobenius_cycle_types +
    is_perfect_square exactly; raises on gp failure (caller falls back to sympy)."""
    cs = [int(c) for c in coeffs]
    if ascending:
        cs = cs[::-1]
    body = (
        f"f=Pol({cs});d=poldisc(f);lc=pollead(f);big=0;\n"
        "forprime(q=3,199, if(d%q!=0 && lc%q!=0,"
        " fa=factormod(f,q,1); for(i=1,matsize(fa)[1],"
        " if(fa[i,1]==13||fa[i,1]==17||fa[i,1]==19, big=1))));\n"
        "print(big,\" \",issquare(d));"
    )
    out = _run_gp(body, timeout).split()
    return out[0] == "1", out[1] == "1"


def orbit_lift(f_coeffs, sel, *, timeout: float = 400.0) -> list[int]:
    """Orbit-sign lift: K24 = K12(sqrt delta), delta = product of selected factor discs of P12
    over its own field K12 (2026-07-02 lift-map dive). sqrt(disc g_i) lives in the Galois CLOSURE
    of K12, so the lift is closure-preserving: Gal(K24) has the SAME order as the closure group
    (the coset action on G/ker(orbit-sign char)) — reaches 491 24Tt (660 lifts) from the 301 12T
    base labels, ~384 of them groups we don't hold. ``sel`` = 1-based indices into the NON-LINEAR
    factors (degree-sorted); invalid indices => []. Returns ascending deg-24 coeffs or []."""
    if not sel:
        raise ValueError("empty selection")
    cs = [int(c) for c in f_coeffs][::-1]
    idx = ",".join(str(int(i)) for i in sel)
    body = (
        f"f=Pol({cs},'y);nf=nfinit(f);fa=nffactor(nf,subst(f,'y,'x));\n"
        "L=[];for(i=1,matsize(fa)[1],if(poldegree(fa[i,1])>1,L=concat(L,[fa[i,1]])));\n"
        f"sel=[{idx}];if(#L==0||vecmax(sel)>#L,print(\"NOSEL\");quit);\n"
        "dl=1;for(k=1,#sel,dl=dl*poldisc(L[sel[k]]));\n"
        "r=rnfequation(f,'x^2 - lift(dl));\n"
        "print(if(poldegree(r)<24,\"DEGENERATE\",Vec(polredbest(r))));"
    )
    out = _run_gp(body, timeout)
    if any(m in out for m in ("NOSEL", "DEGENERATE")):
        return []
    return [int(x) for x in out.strip("[]").split(",")][::-1]


def composition(inner_coeffs, outer_coeffs, *, timeout: float = 400.0) -> list[int]:
    """h(x) = f(g(x)): the degree-24 composition of outer f (deg a) with inner g (deg b), ab=24.

    Roots of h = g-preimages of f's roots => a blocks of size b, Gal(h) <= Gal(g) wr Gal(f)
    (research log 2026-06-24, arXiv 2306.14386) — the ONLY cheap route to the minblk in {6,8,12}
    strata (4x6/3x8/2x12), incl. the near-S24 titans (S12 wr C2 = order 2.29e17 = 24T24996/97)
    via a quadratic outer over a generic S12/A12 inner. No bnfinit — just substitution.
    Coeffs ascending; returns [] if the composition is reducible/degenerate."""
    ic = [int(c) for c in inner_coeffs][::-1]
    oc = [int(c) for c in outer_coeffs][::-1]
    body = (
        f"g=Pol({ic},'x);f=Pol({oc},'y);h=subst(f,'y,g);\n"
        "if(poldegree(h)!=24||!polisirreducible(h),print(\"DEGENERATE\"),"
        "print(Vec(polredbest(h))));"
    )
    out = _run_gp(body, timeout)
    if "DEGENERATE" in out:
        return []
    return [int(x) for x in out.strip("[]").split(",")][::-1]


def _general_radical(f_coeffs, w, q: int, kernel_poly: str, timeout: float) -> list[int]:
    """Shared driver: alpha = generator of the product of the w-selected primes above a
    completely-split q (exactly ``general_c2``'s alpha), then ``rnfequation(f, kernel)``.
    Base degree inferred from the coeffs; q must split completely (deg-many deg-1 primes).
    Returns ascending degree-24 coeffs, or [] (not split / nonprincipal / degenerate)."""
    idx = [j + 1 for j, x in enumerate(w) if x]
    if not idx:
        raise ValueError("w = 0 gives a degenerate alpha")
    cs = [int(c) for c in f_coeffs][::-1]
    deg = len(cs) - 1
    sel = ",".join(f"pr[{j}]" for j in idx)
    body = (
        f"f=Pol({cs},'y);bnf=bnfinit(f);pr=idealprimedec(bnf,{q});\n"
        f"if(#pr!={deg},print(\"NOTSPLIT\"); quit);\n"
        f"sel=[{sel}];Jd=sel[1];for(k=2,#sel,Jd=idealmul(bnf,Jd,sel[k]));\n"
        "pd=bnfisprincipal(bnf,Jd);\n"
        "if(#pd[1]>0 && vecmax(abs(pd[1]))>0, print(\"NONPRINCIPAL\"); quit);\n"
        "al=lift(nfbasistoalg(bnf,pd[2]));\n"
        f"r=rnfequation(f,{kernel_poly});\n"
        "print(if(poldegree(r)<24,\"DEGENERATE\",Vec(polredbest(r))));"
    )
    out = _run_gp(body, timeout)
    if any(m in out for m in ("NOTSPLIT", "NONPRINCIPAL", "DEGENERATE")):
        return []
    return [int(x) for x in out.strip("[]").split(",")][::-1]


def general_cubic(f_coeffs, w, q: int, *, timeout: float = 400.0) -> list[int]:
    """Non-Galois cubic kernel over an arbitrary degree-8 base: K = F(cbrt(alpha)).

    x^3 - alpha is generically non-Galois over F (zeta_3 not in F, alpha not a cube) => an
    S3-type size-3 block — the kernel the 2026-07-02 GAP screen shows 606 open minblk=3
    groups (2,728 open sigs) require; the cyclic zeta-Kummer 8x3 producer cannot reach them."""
    return _general_radical(f_coeffs, w, q, "'x^3 - al", timeout)


def general_quartic(f_coeffs, w, q: int, *, timeout: float = 400.0) -> list[int]:
    """Generic quartic kernel over an arbitrary degree-6 base: x^4 + alpha*x + alpha.

    Its resolvent cubic x^3 - 4*alpha*x - alpha^2 is generically irreducible over F => an
    S4-type block (x^4-alpha's resolvent always factors -> only D4-ish; biquadratic -> V4) —
    the kernel 541 open minblk=4 groups (3,706 open sigs) require per the same screen.
    A4-kernel groups (square relative disc) are a later refinement."""
    return _general_radical(f_coeffs, w, q, "'x^4 + al*'x + al", timeout)


def general_biquadratic(f_coeffs, w1, w2, q: int, *, timeout: float = 400.0) -> list[int]:
    """Size-4 (V_4-block) construction over an ARBITRARY degree-m base F (Galois or NOT).

    Generalizes ``biquadratic_c2`` (which needs autos) the way ``general_c2`` generalizes
    ``galois_c2``: ``beta_i`` is the generator of the PRODUCT ideal of the primes selected by
    ``w_i`` above a completely-split ``q`` (so any class number; non-principal => []), and
    ``K`` is the degree-4m compositum of ``F(sqrt b1)``, ``F(sqrt b2)``. For m=6 this builds
    6x4 groups over arbitrary degree-6 tops (6Tj, |H|>6) — the diversity 12x2 lacks. Label via
    Magma (the daemon). Returns ascending coeffs, or [] if degenerate / nonprincipal.
    """
    cs = [int(c) for c in f_coeffs][::-1]
    i1 = [j + 1 for j, x in enumerate(w1) if x]
    i2 = [j + 1 for j, x in enumerate(w2) if x]
    if not i1 or not i2:
        raise ValueError("w1 and w2 must be nonzero")
    s1 = ",".join(f"pr[{j}]" for j in i1)
    s2 = ",".join(f"pr[{j}]" for j in i2)
    body = (
        f"f=Pol({cs},'y);bnf=bnfinit(f);pr=idealprimedec(bnf,{q});\n"
        f"s1=[{s1}];J1=s1[1];for(k=2,#s1,J1=idealmul(bnf,J1,s1[k]));\n"
        f"s2=[{s2}];J2=s2[1];for(k=2,#s2,J2=idealmul(bnf,J2,s2[k]));\n"
        "pd1=bnfisprincipal(bnf,J1);pd2=bnfisprincipal(bnf,J2);\n"
        "if((#pd1[1]>0&&vecmax(abs(pd1[1]))>0)||(#pd2[1]>0&&vecmax(abs(pd2[1]))>0),"
        "print(\"NONPRINC\");quit);\n"
        "b1=lift(nfbasistoalg(bnf,pd1[2]));b2=lift(nfbasistoalg(bnf,pd2[2]));\n"
        "r1=polredbest(rnfequation(f,'x^2-b1));r2=polredbest(rnfequation(f,'x^2-b2));\n"
        "L=polcompositum(r1,r2);K=0;for(i=1,#L,if(poldegree(L[i])==4*poldegree(f),K=L[i]));\n"
        "print(if(K==0,\"DEGEN\",Vec(polredbest(K))));"
    )
    out = _run_gp(body, timeout)
    if "NONPRINC" in out or "DEGEN" in out:
        return []
    return [int(x) for x in out.strip("[]").split(",")][::-1]


def cyclotomic_kummer(w, n: int, q: int, k: int, *, timeout: float = 300.0) -> list[int]:
    """Size-k (cyclic C_k block) Kummer construction K = Q(zeta_n)(alpha^{1/k}).

    Needs zeta_k in Q(zeta_n) (i.e. k | n for k>2) so the radical extension is a clean cyclic
    C_k (Kummer). ``w`` is a length-phi(n) vector of exponents in 0..k-1 indexed by the units
    of n; ``alpha = prod_a sigma_a(pi)^{w_a}`` for pi a generator of a prime above a split q
    (= 1 mod n). Returns the degree k*phi(n) field (ascending), or [] if alpha is a k-th power
    (degenerate). For 24 = m*k: e.g. k=3,n=15 (m=8, the 8x3 frontier shape).
    """
    from math import gcd

    units = [a for a in range(1, n) if gcd(a, n) == 1]
    if len(w) != len(units):
        raise ValueError(f"w has length {len(w)}, expected phi({n})={len(units)}")
    terms = "*".join(
        f"Mod(subst(lift(p0),'y,'y^{a}),F)^{w[j]}" for j, a in enumerate(units) if w[j] % k
    )
    if not terms:
        raise ValueError("w = 0 (mod k) gives a degenerate (k-th power) alpha")
    body = (
        f"F=polcyclo({n},'y); bnf=bnfinit(F);\n"
        f"p0=nfbasistoalg(bnf, bnfisprincipal(bnf, idealprimedec(bnf,{q})[1])[2]);\n"
        f"al=lift({terms});\n"
        f"r=rnfequation(F,'x^{k} - al);\n"
        f"if(poldegree(r)<{k} * poldegree(F),print(\"DEGENERATE\"),print(Vec(polredbest(r))));"
    )
    out = _run_gp(body, timeout)
    if "DEGENERATE" in out:
        return []
    return [int(x) for x in out.strip("[]").split(",")][::-1]


def biquadratic_c2(f_coeffs, w1, w2, q: int, *, timeout: float = 300.0) -> list[int]:
    """Size-4 (V_4-block) construction: K = F(sqrt(beta1), sqrt(beta2)) over Galois F.

    ``f_coeffs`` (ascending) defines a GALOIS base field F of degree m=24/4=6; ``w1``,``w2``
    are 0/1 valuation patterns (length m) selecting two independent square-classes
    ``beta_i = prod_{w_i[a]=1} sigma_a(pi)`` from a completely-split prime q. K is the
    degree-24 compositum of F(sqrt beta1) and F(sqrt beta2) — m blocks of size 4 with a
    Klein-four (C_2 x C_2) block group. Returns ascending coeffs (or [] if degenerate, i.e.
    beta1, beta2 dependent mod squares so [K:F] < 4).
    """
    i1 = [j + 1 for j, x in enumerate(w1) if x]
    i2 = [j + 1 for j, x in enumerate(w2) if x]
    if not i1 or not i2:
        raise ValueError("w1 and w2 must both be nonzero")
    cs = [int(c) for c in f_coeffs][::-1]
    t1 = "*".join(f"Mod(subst(pil,'y,cj[{a}]),f)" for a in i1)
    t2 = "*".join(f"Mod(subst(pil,'y,cj[{a}]),f)" for a in i2)
    body = (
        f"f=Pol({cs},'y);bnf=bnfinit(f);cj=nfgaloisconj(f);\n"
        f"pi=nfbasistoalg(bnf,bnfisprincipal(bnf,idealprimedec(bnf,{q})[1])[2]);pil=lift(pi);\n"
        f"b1=lift({t1});b2=lift({t2});\n"
        "r1=polredbest(rnfequation(f,'x^2-b1));r2=polredbest(rnfequation(f,'x^2-b2));\n"
        "L=polcompositum(r1,r2);K=0;for(i=1,#L,if(poldegree(L[i])==24,K=L[i]));\n"
        "if(K==0,print(\"DEGENERATE\"),print(Vec(polredbest(K))));"
    )
    out = _run_gp(body, timeout)
    if "DEGENERATE" in out:
        return []
    return [int(x) for x in out.strip("[]").split(",")][::-1]


def subfield_degrees(coeffs, *, ascending: bool = True, timeout: float = 180.0) -> list[int]:
    """Degrees of the PROPER subfields of Q[x]/(f) (= block-system sizes [G:U]).

    Via PARI nfsubfields; the local read on imprimitivity / block structure.
    """
    script = f"print([poldegree(u[1]) | u <- nfsubfields({_poly(coeffs, ascending)})])"
    out = _run_gp(script, timeout)
    degs = sorted(int(x) for x in out.strip("[]").split(",") if x.strip())
    return [d for d in degs if 1 < d < 24]


def scan_galois(coeff_lists, *, timeout: float = 300.0) -> dict:
    """Galois group of each candidate (deg <= 11) in ONE gp process.

    Returns {index: (order, name)} for irreducible candidates whose group PARI can
    compute; reducible/erroring ones are omitted. Used to auto-build a palette of
    small fields binned by Galois group.
    """
    arr = ",".join(_poly(c, True) for c in coeff_lists)
    script = (
        f"fs=[{arr}];"
        "for(i=1,#fs, f=fs[i];"
        " if(polisirreducible(f),"
        "  g=iferr(polgalois(f),e,0);"
        '  if(type(g)=="t_VEC", print(i,"|",g[1],"|",g[4],"|",polsturm(f)))))'
    )
    res = {}
    for ln in _run_gp(script, timeout).splitlines():
        if "|" in ln:
            i, order, name, nreal = ln.split("|")
            res[int(i) - 1] = (int(order), name, int(nreal))
    return res


def compositum(factor_lists, *, reduce: bool = False, timeout: float = 300.0):
    """Build a degree-(prod) compositum of the given factor polynomials.

    Each factor is ascending integer coeffs. Returns ``(coeffs_ascending, num_real_roots)``
    of a compositum field (max-degree factor at each fold step; the field has the
    factors as subfields -> imprimitive). ``reduce=True`` applies polredbest (slower).
    """
    pols = ",".join(_poly(c, True) for c in factor_lists)
    red = "m=polredbest(m);" if reduce else ""
    script = (
        f"fs=[{pols}];m=fs[1];"
        "for(k=2,#fs,L=polcompositum(m,fs[k]);m=L[1];"
        "for(i=2,#L,if(poldegree(L[i])>poldegree(m),m=L[i])));"
        f"{red}print(Vec(m));print(polsturm(m))"
    )
    out = _run_gp(script, timeout).splitlines()
    coeffs = [int(x) for x in out[0].strip("[]").split(",")][::-1]
    return coeffs, int(out[1])


def polsubcyclo(n: int, d: int, *, reduce: bool = True, timeout: float = 180.0) -> list[int]:
    """Ascending coeffs of the degree-``d`` abelian subfield of Q(zeta_n).

    Requires exactly one such subfield (true when Gal(Q(zeta_n)/Q) is cyclic, e.g.
    ``n`` prime), else PARI returns a vector and this raises. ``polredabs``-reduced
    by default (canonical small monic polynomial defining the same field).
    """
    expr = f"polsubcyclo({n},{d})"
    if reduce:
        expr = f"polredabs({expr})"
    return _parse_vec(_run_gp(f"print(Vec({expr}))", timeout))
