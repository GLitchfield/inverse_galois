# Board pre-filter for the general_c2_TWIST engine (dive #49): which 24Tt can a dim-11 landing
# over the block top H = 12Tj possibly BE?  Only the dim-11 (mu = 1, one-relation) submodules are
# reachable by the mixed split-pair divisor, so we skip the full submodule lattice and enumerate
# just those, with ALL complement classes (the split one plus the twists = the payload).
#
# Usage: gap -q -b -c 'TOP:=210;' scripts/mb2_twist_prefilter.g
#   PRE|<24Tt>|<order>     one per (dim-11 submodule, complement class)

Pre := function(j)
    local H, W, base, flip, M, B, K, v, i, G, t, f, Q, Bq, comps, C, seen;
    H := TransitiveGroup(12, j);
    W := WreathProduct(SymmetricGroup(2), H);
    flip := List([1..12], i -> Image(Embedding(W, i), (1,2)));
    base := Group(flip);
    M := PermutationGModule(H, GF(2));
    seen := [];
    for B in Filtered(MTX.BasesSubmodules(M), b -> Length(b) = 11) do
        K := Group(List(B, v -> Product(Filtered([1..12], i -> IsOne(v[i])), i -> flip[i])));
        f := NaturalHomomorphismByNormalSubgroup(W, K);
        Q := Image(f);
        Bq := Image(f, base);
        comps := ComplementClassesRepresentatives(Q, Bq);
        for C in comps do
            G := PreImage(f, C);
            if Size(G) <> Size(H) * 2^11 then continue; fi;
            if not IsTransitive(G, [1..24]) then continue; fi;
            t := TransitiveIdentification(G);
            if t in seen then continue; fi;
            Add(seen, t);
            Print("PRE|", t, "|", Size(G), "\n");
        od;
    od;
end;;

Pre(TOP);
QUIT;
