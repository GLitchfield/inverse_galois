# The chi-TABLE: for every block top H = 12Tj and every index-2 subgroup N <= H, tabulate
# chi_N on CYCLE TYPES of the degree-12 action (research dive #51, generalizing dive #50's
# sign character to an ARBITRARY quadratic character of H).
#
# WHY cycle types: for a prime p unramified in K0, the factorization pattern of the defining
# polynomial mod p gives the cycle type of Frob_p in the degree-12 action -- and nothing more
# (the class itself is not observable cheaply).  chi_N is a class function, so a cycle type
# PINS chi(Frob_p) exactly when all H-classes with that cycle type share one chi value: call
# such a type DECISIVE.  Every decisive prime then gives one equation
#     kronecker(d_N, p) = (-1)^chi(cycletype(p))
# on the unknown quadratic subfield disc d_N of the Galois closure M, and d_N is supported on
# the primes ramifying in K0 -- so a handful of decisive primes pins d_N by brute force.
#
# Usage: gap -q -b -c 'LO:=1;; HI:=301;;' scripts/mb2_chi_table.g
#   TOP|<j>|<|H|>|<#index-2 subgroups>
#   SIB|<j>|<idx>|<24Tt>            the dim-11 twisted sibling selected by chi_idx
#   CHIV|<j>|<idx>|<bits>          chi on GeneratorsOfGroup(H) -- the F2-vector of the character
#   CLS|<j>|<idx>|<cycletype>|<chi 0/1>|<class size>     ONE ROW PER CONJUGACY CLASS
#     cycletype = ascending cycle lengths on 12 points, "-"-joined (e.g. "1-1-2-2-3-3")
#
# Decisiveness is aggregated downstream (scripts/mb2_chi_d.py), NOT here: an earlier version of this
# script aggregated in GAP with NewDictionary("x", true) keyed on the cycle-type STRING, and GAP hash
# dictionaries require IMMUTABLE keys -- mutable-string keys silently dropped classes (12T23: the
# class sizes summed to 35, not |H| = 48), which marked genuinely AMBIGUOUS cycle types as decisive
# and produced d_N answers that disagreed with ~13% of the Frobenius equations.  Emit raw rows.

CT := function(g)
    local s, i, str;
    s := SortedList(CycleLengths(g, [1 .. 12]));
    str := "";
    for i in [1 .. Length(s)] do
        str := Concatenation(str, String(s[i]));
        if i < Length(s) then str := Concatenation(str, "-"); fi;
    od;
    return str;
end;;

Sibling := function(H, N)
    local W, proj, S2, imgs, f, G;
    W := WreathProduct(SymmetricGroup(2), H);
    proj := Projection(W);
    S2 := Group((1, 2));
    imgs := List(GeneratorsOfGroup(W), function(g)
        local b;
        b := 0;
        if SignPerm(g) = -1 then b := 1; fi;
        if not (Image(proj, g) in N) then b := (b + 1) mod 2; fi;
        if b = 0 then return (); else return (1, 2); fi;
    end);
    f := GroupHomomorphismByImages(W, S2, GeneratorsOfGroup(W), imgs);
    if f = fail then return fail; fi;
    G := Kernel(f);
    if Size(G) <> Size(H) * 2 ^ 11 then return fail; fi;
    if not IsTransitive(G, [1 .. 24]) then return fail; fi;
    return TransitiveIdentification(G);
end;;

Table := function(j)
    local H, subs, ccl, i, N, t, c, rep, ch, gens, k;
    H := TransitiveGroup(12, j);
    subs := Filtered(List(ConjugacyClassesSubgroups(H), Representative),
                     N -> Index(H, N) = 2 and IsNormal(H, N));
    Print("TOP|", j, "|", Size(H), "|", Length(subs), "\n");
    if Length(subs) = 0 then return; fi;
    ccl := ConjugacyClasses(H);
    for i in [1 .. Length(subs)] do
        N := subs[i];
        t := Sibling(H, N);
        if t = fail then continue; fi;
        Print("SIB|", j, "|", i, "|", t, "\n");
        # chi as a VECTOR on a fixed generating set: Hom(H,F2) is an F2-space, and d_N is a
        # HOMOMORPHISM chi -> Q*/(Q*)^2, so chi_a + chi_b = chi_c forces d_a . d_b = d_c mod squares.
        # That pins the d of a chi with too few decisive cycle types, and cross-checks the rest.
        Print("CHIV|", j, "|", i, "|");
        gens := GeneratorsOfGroup(H);
        for k in [1 .. Length(gens)] do
            if gens[k] in N then Print("0"); else Print("1"); fi;
        od;
        Print("\n");
        for c in ccl do
            rep := Representative(c);
            if rep in N then ch := 0; else ch := 1; fi;
            Print("CLS|", j, "|", i, "|", CT(rep), "|", ch, "|", Size(c), "\n");
        od;
    od;
end;;

for J in TOPS do
    Table(J);
od;
QUIT;
