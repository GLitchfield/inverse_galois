# Cycle-type density library for the two-prime radical (general_c2_multi), over a block top H=12Tj.
#
# Dive #48's column-space law: the realized block kernel of K0(sqrt(alpha)) is colspace(Phi) =
# sum_i <H . 1_{w_i}>, an H-submodule K of the F2 permutation module F2^12. So every group the
# construction can land in sits inside W = C2 wr H with base-intersection K and full projection
# to H. Those are NOT just the split C2^K : H -- the complement can be twisted by a cocycle in
# H^1(H, F2^12/K), and that twist is exactly what separates the sibling labels (over 12T210 the
# split dim-11 group is 24T22545, while our targets 22544/22548 are the twisted ones). So for
# each submodule K we enumerate ALL complement classes of base/K in W/K and pull them back.
# The result is the exact candidate set -- the right library to L1-discriminate the target from
# its neighbours (block collapses, Gassmann cousins, sibling twists).
#
# Usage: gap -q -b -c 'TOP:=210;' scripts/mb2_multi_gdist.g
#   SUB|<24Tt>|<dim>|<basis bitmasks>|<order>     one per (submodule, complement class)
#   CT|<24Tt>|<cycle type>|<class size>           one per conjugacy class

Library := function(j)
    local H, W, base, flip, M, subs, B, K, v, i, c, G, t, k, mask, key, f, Q, Bq, comps, C, seen;
    H := TransitiveGroup(12, j);
    W := WreathProduct(SymmetricGroup(2), H);
    flip := List([1..12], i -> Image(Embedding(W, i), (1,2)));
    base := Group(flip);
    M := PermutationGModule(H, GF(2));
    subs := MTX.BasesSubmodules(M);
    Print("NSUB|", Length(subs), "\n");
    seen := [];
    for B in subs do
        k := Length(B);
        if k = 0 then continue; fi;
        K := Group(List(B, v -> Product(Filtered([1..12], i -> IsOne(v[i])), i -> flip[i])));
        mask := JoinStringsWithSeparator(
                    List(B, v -> String(Sum([1..12], i -> Int(v[i]) * 2^(i-1)))), ",");
        f := NaturalHomomorphismByNormalSubgroup(W, K);
        Q := Image(f);
        Bq := Image(f, base);
        comps := ComplementClassesRepresentatives(Q, Bq);
        Print("NCOMP|", k, "|", Length(comps), "\n");
        for C in comps do
            G := PreImage(f, C);
            if Size(G) <> Size(H) * 2^k then Print("SKIP|", k, "|order\n"); continue; fi;
            if not IsTransitive(G, [1..24]) then continue; fi;
            t := TransitiveIdentification(G);
            if t in seen then continue; fi;
            Add(seen, t);
            Print("SUB|", t, "|", k, "|", mask, "|", Size(G), "\n");
            for c in ConjugacyClasses(G) do
                key := JoinStringsWithSeparator(
                           List(SortedList(CycleLengths(Representative(c), [1..24])), String), ",");
                Print("CT|", t, "|", key, "|", Size(c), "\n");
            od;
        od;
    od;
end;;

Library(TOP);
QUIT;
