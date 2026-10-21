# minblk=8 module comparison (test 0052): the load-bearing fact that the "wreath" 24916
# (direct-Res builds this) has an IRREDUCIBLE 9-dim kernel with THREE independent L3(2)
# (Q=(PSL(3,2)^3):C3), while the twist 19280 has a SINGLE SHARED L3(2) (Q=C3xL3(2)) with the
# REDUCIBLE kernel (C2)^9 = [3,6] = V (+) V(x)F4.  This is WHY the twist needs a genuine tensor
# module (not a product-of-radicands) and direct-Res gives the wreath.  See docs/tests/0052.
for t in [24916, 19280, 24314, 24315] do
  G := TransitiveGroup(24, t);
  N := PCore(G, 2);
  Q := G / N;
  Print("==== 24T", t, "  |G|=", Size(G), "  |O2|=", Size(N), " (2^", LogInt(Size(N),2), ")",
        "  |Q|=", Size(Q), " Q=", StructureDescription(Q), "\n");
  if IsElementaryAbelian(N) and Size(N)>1 then
    pcgs := Pcgs(N);
    gens := GeneratorsOfGroup(G);
    mats := List(gens, g -> List(pcgs, z -> ExponentsOfPcElement(pcgs, z^g)) * One(GF(2)));
    M := GModuleByMats(mats, GF(2));
    cf := MTX.CompositionFactors(M);
    Print("     module dims=", List(cf, c -> c.dimension), " irred=", MTX.IsIrreducible(M), "\n");
  else
    Print("     O2 not elem-abelian or trivial\n");
  fi;
od;
Print("DONE\n"); QUIT;
