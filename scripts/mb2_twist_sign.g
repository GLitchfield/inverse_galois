# Which dim-11 sibling does the SIGN character of the block top select? (research dive #50)
#
# Q(sqrt(disc K0)) is the fixed field of H \cap A12, i.e. the quadratic subfield of the closure M
# cut out by the SIGN character chi_sgn of H.  It is therefore a *free* reachable d for every base
# whose top is NOT inside A12 -- no search, no screen: d = core(disc K0) is always a subfield disc.
# This prints the sibling it aims at:  G_sgn = { (v;h) : Sum v = chi_sgn(h) }.
#
# Usage: gap -q -b -c 'JS:=[12,16,24];;' scripts/mb2_twist_sign.g
#   SGN|<j>|<24Tt>            the sign-character sibling (only if H is not inside A12)
#   SGN|<j>|inA12             H <= A12 => disc is a square => no free d

Sgn := function(j)
    local H, W, proj, S2, f, G, imgs;
    H := TransitiveGroup(12, j);
    if IsSubgroup(AlternatingGroup(12), H) then
        Print("SGN|", j, "|inA12\n"); return;
    fi;
    W := WreathProduct(SymmetricGroup(2), H);
    proj := Projection(W);
    S2 := Group((1,2));
    imgs := List(GeneratorsOfGroup(W), function(g)
        local b;
        b := 0;
        if SignPerm(g) = -1 then b := 1; fi;
        if SignPerm(Image(proj, g)) = -1 then b := (b + 1) mod 2; fi;
        if b = 0 then return (); else return (1,2); fi;
    end);
    f := GroupHomomorphismByImages(W, S2, GeneratorsOfGroup(W), imgs);
    G := Kernel(f);
    Print("SGN|", j, "|", TransitiveIdentification(G), "\n");
end;;

for J in JS do Sgn(J); od;
QUIT;
