# Scope the minblk=8 affine targets: is the elementary-abelian 2-kernel SPLIT over
# the (S3|C3 x L3(2)) top, and what is its F2[Q]-module structure?
# Gates the 28-open-pair affine harvest (agenda 2026-07-06).
LoadPackage("ctbllib");;
targets := [14051, 14052, 16060, 16061, 19280, 20408];;
for t in targets do
  G := TransitiveGroup(24, t);
  N := PCore(G, 2);            # O_2(G) = normal 2-subgroup (the block kernel)
  Q := G / N;
  Print("==== 24T", t, "  |G|=", Size(G), "  |O2(G)|=", Size(N),
        "  elemAb=", IsElementaryAbelian(N), "  |Q|=", Size(Q), "\n");
  Print("     Q struct: ", StructureDescription(Q), "\n");
  # module structure of N as F2[Q]-module via conjugation
  if IsElementaryAbelian(N) then
    d := LogInt(Size(N), 2);
    Print("     N = (C2)^", d, "\n");
    pcgs := Pcgs(N);
    gens := GeneratorsOfGroup(G);
    mats := List(gens, g -> List(pcgs, x ->
              ExponentsOfPcElement(pcgs, x^g)) * One(GF(2)));
    M := GModuleByMats(mats, GF(2));
    cf := MTX.CompositionFactors(M);
    Print("     F2[G]-module N: irreducible=", MTX.IsIrreducible(M),
          "  #constituents=", Length(cf),
          "  dims=", List(cf, c -> c.dimension), "\n");
  fi;
  # SPLIT CHECK: does G split over N?
  cc := ComplementClassesRepresentatives(G, N);
  Print("     SPLIT over O2(G): ", Length(cc) > 0,
        "  (#complement classes=", Length(cc), ")\n");
  Print("\n");
od;
Print("DONE\n");
QUIT;
