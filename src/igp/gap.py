"""GAP backend (shell-out to the ``gap`` binary) for degree-24 group metadata.

GAP's transitive-groups library (`transgrp`) holds the full `24Tt` catalogue
(`NrTransitiveGroups(24) == 25000`), the authoritative source for the target
index: per-group order, solvability, primitivity, transitivity, and `A_n`
membership. We shell out to the `gap` CLI (`-q -b`: quiet, no banner) and have
GAP `Print` exactly the fields we want, pipe-separated, then `QUIT`.
"""

from __future__ import annotations

import shutil
import subprocess

from .gp import CASError  # reuse the same backend-error type

GAP_BIN = shutil.which("gap") or "/usr/bin/gap"


def available() -> bool:
    return shutil.which("gap") is not None


def _run_gap(body: str, timeout: float = 600.0) -> str:
    script = body + "\nQUIT;\n"
    try:
        proc = subprocess.run(
            [GAP_BIN, "-q", "-b"], input=script, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as e:
        raise CASError(f"gap not found at {GAP_BIN!r}; install gap") from e
    except subprocess.TimeoutExpired as e:
        raise CASError(f"gap timed out after {timeout}s") from e
    if proc.returncode != 0 or "Error" in proc.stderr:
        raise CASError(f"gap error: {(proc.stderr or proc.stdout).strip()[:400]}")
    return proc.stdout.replace("\\\n", "").strip()  # undo GAP's line-wrap continuations


def num_transitive_groups(n: int = 24) -> int:
    return int(_run_gap(f"Print(NrTransitiveGroups({n}));"))


def _parse_row(line: str, n: int) -> dict:
    t, order, solv, prim, trans, in_an = line.split("|")
    return {
        "n": n,
        "t": int(t),
        "label": f"{n}T{int(t)}",
        "order": int(order),
        "solvable": solv == "true",
        "primitive": prim == "true",
        "transitivity": int(trans),
        "in_an": in_an == "true",  # Gal <= A_n (parity)
    }


def transitive_group_info(n: int, t: int) -> dict:
    body = (
        f"g:=TransitiveGroup({n},{t});;\n"
        f'Print({t},"|",Order(g),"|",IsSolvable(g),"|",IsPrimitive(g,[1..{n}]),'
        f'"|",Transitivity(g,[1..{n}]),"|",IsSubgroup(AlternatingGroup({n}),g));'
    )
    return _parse_row(_run_gap(body), n)


def group_invariants(t: int, n: int = 24, timeout: float = 300.0) -> dict:
    """Local-identifier invariants of nTt: order, A_n membership, proper subfield
    degrees ([G:U] for intermediate U), and the SET of cycle types (partitions of n).

    For confirming a constructed polynomial's group without Magma. Feasible for the
    solvable / moderate-order groups we target; can be slow for huge groups.
    """
    body = (
        "SizeScreen([100000, 100000]);;\n"
        f"g:=TransitiveGroup({n},{t});;\n"
        "s:=Stabilizer(g,1);;\n"
        "degs:=Set(List(IntermediateSubgroups(g,s).subgroups, u->Index(g,u)));;\n"
        f"cyc:=p->SortedList(List(OrbitsDomain(Group(p),[1..{n}]),Length));;\n"
        "cts:=Set(List(ConjugacyClasses(g), c->cyc(Representative(c))));;\n"
        f'Print(Order(g),"|",IsSubgroup(AlternatingGroup({n}),g),"|",'
        'JoinStringsWithSeparator(List(degs,String),","),"|");;\n'
        'for ct in cts do Print(JoinStringsWithSeparator(List(ct,String),","),";"); od;'
    )
    order_s, inan_s, degs_s, cts_s = _run_gap(body, timeout=timeout).split("|")
    cts = {tuple(int(x) for x in part.split(",")) for part in cts_s.split(";") if part.strip()}
    return {
        "t": t,
        "order": int(order_s),
        "in_an": inan_s == "true",
        "subfield_degrees": sorted(int(x) for x in degs_s.split(",") if x.strip()),
        "cycle_types": cts,
    }


def c2_kernel_labels(top_t: int, top_deg: int = 12, timeout: float = 300.0) -> dict:
    """24Tt labels of the C_2-kernel groups over a given top group `top_deg`T`top_t`.

    Builds `C_2 ≀ H` (H = the top) and identifies the three canonical H-submodule
    kernels: diagonal `<(1,…,1)>` (dim 1), augmentation/sum-zero (dim m-1), and full
    (dim m). Lets us PREDICT the 24Tt for a (top, prescribed-kernel) pair, to match
    against a construction. (WS4 step 2.)
    """
    body = (
        f"top:=TransitiveGroup({top_deg},{top_t});;\n"
        "W:=WreathProduct(SymmetricGroup(2),top);;\n"
        f"b:=List([1..{top_deg}], i->Image(Embedding(W,i),(1,2)));;\n"
        f"tg:=GeneratorsOfGroup(Image(Embedding(W,{top_deg + 1}),top));;\n"
        "Gd:=Group(Concatenation(tg,[Product(b)]));;\n"
        f"Ga:=Group(Concatenation(tg,List([2..{top_deg}],i->b[i]*b[1])));;\n"
        'Print(TransitiveIdentification(Gd),"|",TransitiveIdentification(Ga),'
        '"|",TransitiveIdentification(W));'
    )
    d, a, f = _run_gap(body, timeout=timeout).split("|")
    return {"diagonal": f"24T{int(d)}", "augmentation": f"24T{int(a)}", "full": f"24T{int(f)}"}


def kernel_label(w, top_t: int = 1, top_deg: int = 12, timeout: float = 300.0) -> str:
    """24Tt of the C_2-kernel group `A ⋊ H` where `A = <H-shifts of w>`.

    `w` is a 0/1 vector of length `top_deg`; `H = top_deg`T`top_t` acts on the blocks.
    Generalizes `c2_kernel_labels`: predicts the label for the kernel generated by an
    arbitrary valuation pattern `w` — the group side of the A→w→α solver.
    """
    idx = [i + 1 for i, wi in enumerate(w) if wi]
    if not idx:
        raise ValueError("w = 0 gives the trivial kernel (degree 12, not 24)")
    prod = "*".join(f"b[{i}]" for i in idx)
    body = (
        f"top:=TransitiveGroup({top_deg},{top_t});;\n"
        "W:=WreathProduct(SymmetricGroup(2),top);;\n"
        f"b:=List([1..{top_deg}], i->Image(Embedding(W,i),(1,2)));;\n"
        f"tg:=GeneratorsOfGroup(Image(Embedding(W,{top_deg + 1}),top));;\n"
        f"G:=Group(Concatenation(tg,[{prod}]));;\n"
        "Print(TransitiveIdentification(G));"
    )
    return f"24T{int(_run_gap(body, timeout=timeout))}"


def subset2_orbits(t: int, n: int = 24, timeout: float = 300.0) -> list:
    """Orbit lengths of nTt on 2-subsets of [1..n] (the 2-subset resolvent invariant).

    A RIGOROUS separator beyond cycle types: Gassmann-equivalent (same cycle-type-distribution)
    groups can still differ here. This is the cheap GROUP side; the matching POLY side is the
    factorization of the degree-C(n,2) pair resolvent, which needs separability (Tschirnhaus)
    + high precision (the Fieker-Klüners hard core) — see test 0022.
    """
    body = (
        f"g:=TransitiveGroup({n},{t});;\n"
        f"Print(SortedList(List(OrbitsDomain(g,Combinations([1..{n}],2),OnSets),Length)));"
    )
    out = _run_gap(body, timeout=timeout)
    return [int(x) for x in out.strip("[ ]").split(",") if x.strip()]


def cycle_type_distributions(ts, n: int = 24, timeout: float = 600.0) -> dict:
    """Expected Frobenius cycle-type distribution of each nTt (Chebotarev weights).

    For each `t`, returns ``{"order": |G|, "dist": {cycle_type_tuple: total #elements
    with that cycle type}}``. By Chebotarev a Frobenius element equidistributes over `G`,
    so ``count/order`` is the expected frequency of that factorization pattern when
    reducing the polynomial mod good primes. The discriminating upgrade over the
    cycle-type *set*: two groups sharing a set still differ in these weights (and in
    which types are even possible). One GAP process over the whole list.
    """
    tl = "[" + ",".join(map(str, ts)) + "]"
    body = (
        "SizeScreen([100000,100000]);;\n"
        f"cyc:=p->SortedList(List(OrbitsDomain(Group(p),[1..{n}]),Length));;\n"
        f"for t in {tl} do\n"
        f"  g:=TransitiveGroup({n},t);;\n"
        '  Print(t,"|",Order(g),"|");\n'
        "  for c in ConjugacyClasses(g) do\n"
        '    Print(JoinStringsWithSeparator(List(cyc(Representative(c)),String),","),'
        '":",Size(c),";");\n'
        "  od;\n"
        '  Print("@");\n'
        "od;"
    )
    res = {}
    for chunk in _run_gap(body, timeout=timeout).split("@"):
        if "|" not in chunk:
            continue
        tpart, order_s, classes = chunk.split("|", 2)
        dist: dict = {}
        for seg in classes.split(";"):
            if not seg.strip():
                continue
            ct_s, size_s = seg.rsplit(":", 1)
            ct = tuple(int(x) for x in ct_s.split(","))
            dist[ct] = dist.get(ct, 0) + int(size_s)
        res[int(tpart.strip())] = {"order": int(order_s), "dist": dist}
    return res


def kernel_label_perms(w, top_perms, timeout: float = 300.0) -> str:
    """24Tt of `A ⋊ H` where H is given by EXPLICIT permutations and `A = <H-shifts of w>`.

    Unlike ``kernel_label`` (which uses GAP's own `top_deg`T`top_t` action), the caller
    supplies the top action directly as ``top_perms`` — a list of permutations, each a
    0-indexed image list on ``[0..len(w)-1]``. This lets the GROUP prediction use the
    SAME block action as the field construction (e.g. the (Z/n)* multiplication action of
    ``gp.cyclotomic_c2``), so intermediate kernels align between predict and construct.
    """
    m = len(w)
    idx = [i + 1 for i, wi in enumerate(w) if wi]
    if not idx:
        raise ValueError("w = 0 gives the trivial kernel (degree m, not 2m)")
    prod = "*".join(f"b[{i}]" for i in idx)
    perms = ",".join(
        "PermList([" + ",".join(str(p[k] + 1) for k in range(m)) + "])" for p in top_perms
    )
    body = (
        f"top:=Group([{perms}]);;\n"
        "W:=WreathProduct(SymmetricGroup(2),top);;\n"
        f"b:=List([1..{m}], i->Image(Embedding(W,i),(1,2)));;\n"
        f"tg:=GeneratorsOfGroup(Image(Embedding(W,{m + 1}),top));;\n"
        f"G:=Group(Concatenation(tg,[{prod}]));;\n"
        "Print(TransitiveIdentification(G));"
    )
    return f"24T{int(_run_gap(body, timeout=timeout))}"


def kernel_labels_for_top(top_perms, ws, timeout: float = 1200.0) -> dict:
    """Batch: 24Tt of `<H-shifts of w> ⋊ H` for MANY patterns `w`, one GAP process.

    `H` = ``Group(top_perms)`` (explicit perms on ``[0..m-1]``); ``ws`` a list of 0/1 vectors.
    Builds the wreath product once and identifies each kernel group, returning
    ``{tuple(w): "24Tt"}``. The forward map for routing — far faster than per-`w`
    ``kernel_label_perms`` (which spawns a process each call).
    """
    m = len(top_perms[0]) if top_perms else (len(ws[0]) if ws else 0)
    perms = ",".join(
        "PermList([" + ",".join(str(p[k] + 1) for k in range(m)) + "])" for p in top_perms
    )
    prods = []
    for w in ws:
        idx = [i + 1 for i, wi in enumerate(w) if wi]
        prods.append("*".join(f"b[{i}]" for i in idx) if idx else "()")
    arr = "[" + ",".join(prods) + "]"
    body = (
        f"top:=Group([{perms}]);;\n"
        "W:=WreathProduct(SymmetricGroup(2),top);;\n"
        f"b:=List([1..{m}], i->Image(Embedding(W,i),(1,2)));;\n"
        f"tg:=GeneratorsOfGroup(Image(Embedding(W,{m + 1}),top));;\n"
        f"for p in {arr} do\n"
        "  G:=Group(Concatenation(tg,[p]));;\n"
        "  Print(TransitiveIdentification(G),\";\");\n"
        "od;"
    )
    out = _run_gap(body, timeout=timeout)
    labels = [x for x in out.split(";") if x.strip()]
    return {tuple(w): f"24T{int(lab)}" for w, lab in zip(ws, labels, strict=False)}


def kernel_labels_multigen(top_perms, kernels, timeout: float = 1200.0) -> list:
    """Batch labeler for MULTI-generator kernels: 24Tt of `<H·w for w in gens> ⋊ H`.

    ``kernels`` is a list of generator-lists (each a list of 0/1 vectors). Builds the wreath
    product once and identifies each ``Group(tg + [prod_b(w) for w in gens])``. Returns a list
    of labels aligned to ``kernels``. Generalizes ``kernel_labels_for_top`` (1 generator each)
    to the full submodule lattice (non-cyclic kernels via multi-prime alpha).
    """
    m = len(top_perms[0]) if top_perms else 0
    perms = ",".join(
        "PermList([" + ",".join(str(p[k] + 1) for k in range(m)) + "])" for p in top_perms
    )
    groups = []
    for gens in kernels:
        prods = []
        for w in gens:
            idx = [i + 1 for i, wi in enumerate(w) if wi]
            prods.append("*".join(f"b[{i}]" for i in idx) if idx else "()")
        groups.append("[" + ",".join(prods) + "]")
    arr = "[" + ",".join(groups) + "]"
    body = (
        f"top:=Group([{perms}]);;\n"
        "W:=WreathProduct(SymmetricGroup(2),top);;\n"
        f"b:=List([1..{m}], i->Image(Embedding(W,i),(1,2)));;\n"
        f"tg:=GeneratorsOfGroup(Image(Embedding(W,{m + 1}),top));;\n"
        f"for gens in {arr} do\n"
        "  G:=Group(Concatenation(tg,gens));;\n"
        "  Print(TransitiveIdentification(G),\";\");\n"
        "od;"
    )
    out = _run_gap(body, timeout=timeout)
    return [f"24T{int(x)}" for x in out.split(";") if x.strip()]


def biquadratic_label(w1, w2, reg_perms, timeout: float = 300.0) -> str:
    """24Tt of the size-4 V_4-block group from ``gp.biquadratic_c2`` (item C, size-k).

    Models the explicit degree-24 action of ``M ⋊ H`` on points ``(tau, e1, e2)`` (block
    ``tau`` in ``0..m-1``, signs ``e1,e2`` of ``sqrt(beta1),sqrt(beta2)``): the top permutes
    blocks (regular action ``reg_perms``, one perm per block), and the prime-``p`` sign flip
    ``chi_p`` toggles ``e_i`` by ``w_i[tau^{-1}(p)]``. Returns the identified ``24Tt``.

    ``reg_perms`` = the full regular action of ``Gal(F/Q)`` (``gp.galois_action_perms``);
    pass the SAME orientation the construction used so the prediction aligns with Magma.
    """
    m = len(w1)

    def idx(tau, e1, e2):
        return tau * 4 + e1 * 2 + e2

    inv = [[p.index(q) for q in range(m)] for p in reg_perms]  # tau^{-1}
    gens = []
    for h in reg_perms:  # top generators (regular action generates H)
        perm = [0] * 24
        for tau in range(m):
            for e1 in (0, 1):
                for e2 in (0, 1):
                    perm[idx(tau, e1, e2)] = idx(h[tau], e1, e2)
        gens.append(perm)
    for p in range(m):  # kernel generators chi_p (sign flips at prime p)
        perm = [0] * 24
        for tau in range(m):
            tp = inv[tau][p]
            f1, f2 = w1[tp], w2[tp]
            for e1 in (0, 1):
                for e2 in (0, 1):
                    perm[idx(tau, e1, e2)] = idx(tau, e1 ^ f1, e2 ^ f2)
        gens.append(perm)
    glist = ",".join(
        "PermList([" + ",".join(str(x + 1) for x in g) + "])" for g in gens
    )
    body = f"G:=Group([{glist}]);;Print(TransitiveIdentification(G));"
    return f"24T{int(_run_gap(body, timeout=timeout))}"


def biquadratic_labels_batch(reg_perms, pairs, timeout: float = 1200.0) -> dict:
    """Batch of ``biquadratic_label``: 24Tt of the V_4-block group for many ``(w1,w2)`` pairs.

    Builds the same ``M ⋊ H`` 24-point action as ``biquadratic_label`` (top from ``reg_perms``,
    kernel sign-flips from each ``(w1,w2)``) but identifies every pair in one GAP process —
    the forward map for routing biquadratic candidates. Returns ``{(tuple(w1),tuple(w2)): "24Tt"}``.
    """
    m = len(reg_perms[0]) if reg_perms else 0
    inv = [[p.index(q) for q in range(m)] for p in reg_perms]

    def at(tau, e1, e2):
        return tau * 4 + e1 * 2 + e2

    def plist(g):
        return "PermList([" + ",".join(str(x + 1) for x in g) + "])"

    top = []
    for h in reg_perms:
        perm = [0] * 24
        for tau in range(m):
            for e1 in (0, 1):
                for e2 in (0, 1):
                    perm[at(tau, e1, e2)] = at(h[tau], e1, e2)
        top.append(perm)
    top_str = ",".join(plist(g) for g in top)

    groups = []
    for w1, w2 in pairs:
        kg = []
        for p in range(m):
            perm = [0] * 24
            for tau in range(m):
                tp = inv[tau][p]
                f1, f2 = w1[tp], w2[tp]
                for e1 in (0, 1):
                    for e2 in (0, 1):
                        perm[at(tau, e1, e2)] = at(tau, e1 ^ f1, e2 ^ f2)
            kg.append(perm)
        groups.append(f"Group([{top_str},{','.join(plist(g) for g in kg)}])")
    arr = "[" + ",".join(groups) + "]"
    body = f"for G in {arr} do Print(TransitiveIdentification(G),\";\"); od;"
    out = _run_gap(body, timeout=timeout)
    labels = [x for x in out.split(";") if x.strip()]
    return {(tuple(w1), tuple(w2)): f"24T{int(lab)}"
            for (w1, w2), lab in zip(pairs, labels, strict=False)}


def wreath_decompose_batch(ts, n: int = 24, timeout: float = 1200.0) -> dict:
    """For each nTt in ``ts``, classify every block system as full-wreath or not.

    Per block system returns (block size k, #blocks m, block-action group `kTi`,
    top-action group `mTj`, full_wreath = is `G` the *full* wreath `K ≀ H` on that
    system, i.e. `|G| = |K|^m·|H|`). full_wreath ⇒ reachable by G2 composition with
    constituents realizing `K` (deg k) and `H` (deg m); none full ⇒ a proper-kernel
    group needing deliberate construction (WS4). One GAP process over the whole list.
    """
    tl = "[" + ",".join(map(str, ts)) + "]"
    body = (
        "SizeScreen([100000,100000]);;\n"
        f"for t in {tl} do\n"
        f"  g:=TransitiveGroup({n},t);;\n"
        '  Print(t,":");\n'
        "  for B in AllBlocks(g) do\n"
        f"    k:=Size(B);; m:={n}/k;;\n"
        "    sys:=Orbit(g,B,OnSets);;\n"
        "    Htop:=Action(g,sys,OnSets);;\n"
        "    Kblk:=Action(Stabilizer(g,B,OnSets),B,OnPoints);;\n"
        "    full:=Order(g)=Order(Kblk)^m*Order(Htop);;\n"
        '    Print(k,",",m,",",TransitiveIdentification(Kblk),",",'
        'TransitiveIdentification(Htop),",",full,";");\n'
        "  od;\n"
        '  Print("@");\n'
        "od;"
    )
    res = {}
    for chunk in _run_gap(body, timeout=timeout).split("@"):
        if ":" not in chunk:
            continue
        tpart, segs = chunk.split(":", 1)
        systems = []
        for seg in segs.split(";"):
            if not seg.strip():
                continue
            k, m, ki, tj, full = seg.split(",")
            systems.append({"k": int(k), "m": int(m), "block": f"{k}T{int(ki)}",
                            "top": f"{m}T{int(tj)}", "full_wreath": full == "true"})
        res[int(tpart.strip())] = systems
    return res


def all_transitive_group_info(n: int = 24, timeout: float = 1800.0):
    """Metadata for every nTt group, in one GAP process. Returns a list of dicts.

    A_n is built once and reused across the loop. For n=24 this enumerates all
    25,000 groups; expect minutes, not seconds.
    """
    body = (
        f"A:=AlternatingGroup({n});;\n"
        f"for t in [1..NrTransitiveGroups({n})] do\n"
        f"  g:=TransitiveGroup({n},t);;\n"
        f'  Print(t,"|",Order(g),"|",IsSolvable(g),"|",IsPrimitive(g,[1..{n}]),'
        f'"|",Transitivity(g,[1..{n}]),"|",IsSubgroup(A,g),"\\n");\n'
        f"od;"
    )
    out = _run_gap(body, timeout=timeout)
    return [_parse_row(line, n) for line in out.splitlines() if "|" in line]
