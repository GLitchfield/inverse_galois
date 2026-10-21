# Route-B Part 1(a): does ONE totally-split prime arithmetically generate the FULL
# (C2)^9 kernel of 19280/20408 -- INCLUDING the C3-trivial diagonal (C2)^3 -- or does
# the diagonal need a separately-sourced square-class (=> S>=2 for the direct-Res targets)?
#
# Model: a prime q totally split in K24 has its 24 prime-ideal square-classes permuted
# transitively by G on the 24 points, so [P_1] generates the whole 24-point PERMUTATION
# module Perm24 = F2^24 as an F2[G]-module.  The kernel V=(C2)^9 is realized arithmetically
# only insofar as it is a QUOTIENT of Perm24 (the map [prime] -> radical square-class).
# So the decisive test: is V a quotient of Perm24, and does the surjection hit the diagonal?
LoadPackage("ctbllib");;
targets := [19280, 20408, 14051, 16060];;   # 19280/20408 = full (C2)^9; 14051/16060 = collapsed 6
for t in targets do
  G := TransitiveGroup(24, t);
  N := PCore(G, 2);
  d := LogInt(Size(N), 2);
  pcgs := Pcgs(N);
  gens := GeneratorsOfGroup(G);
  mats := List(gens, g -> List(pcgs, x -> ExponentsOfPcElement(pcgs, x^g)) * One(GF(2)));
  M := GModuleByMats(mats, GF(2));
  cf := MTX.CompositionFactors(M);
  Print("==== 24T", t, "  |G|=", Size(G), "  N=(C2)^", d,
        "  irred=", MTX.IsIrreducible(M), "  cfdims=", List(cf, c -> c.dimension), "\n");

  # cyclicity: spin a nonzero vector, is its F2[G]-span the whole module?
  seed := List([1..d], i -> Z(2)^0);       # the all-ones vector as a generic seed
  sp := MTX.SpinnedBasis(seed, mats, GF(2));
  Print("     cyclic? span(all-ones seed) dim = ", Length(sp), " of ", d, "\n");
  # try a few more seeds to confirm generic cyclicity
  maxspan := Length(sp);
  for it in [1..8] do
    v := List([1..d], i -> Random(GF(2)));
    if not IsZero(v) then
      s2 := Length(MTX.SpinnedBasis(v, mats, GF(2)));
      if s2 > maxspan then maxspan := s2; fi;
    fi;
  od;
  Print("     max single-vector span over 9 seeds = ", maxspan, " of ", d,
        "   (== d => V is CYCLIC)\n");

  # C3-diagonal: the subspace of N fixed by a top-C3 element (block 3-cycle).
  # Find an order-3 element of G whose block action is a 3-cycle => acts as the C3 on blocks.
  B := First(AllBlocks(G), b -> Size(b) = 8);;
  BS := Orbit(G, B, OnSets);;
  bact := ActionHomomorphism(G, BS, OnSets);;
  c3 := fail;
  for cc in ConjugacyClasses(G) do
    g := Representative(cc);
    if Order(g) = 3 and NrMovedPoints(Image(bact, g)) = 3 then c3 := g; break; fi;
  od;
  if c3 <> fail then
    cm := List(pcgs, x -> ExponentsOfPcElement(pcgs, x^c3)) * One(GF(2));
    # Fix space of cm acting on N = kernel of (cm - I)
    fixdim := d - RankMat(cm - cm^0);
    Print("     C3-block element found; dim Fix_C3(N) (the diagonal) = ", fixdim, "\n");
  else
    Print("     no block-3-cycle order-3 element found\n");
  fi;

  # THE decisive arithmetic test: is V a QUOTIENT of the 24-point permutation module?
  Perm := PermutationGModule(G, GF(2));;
  homs := MTX.BasisModuleHomomorphisms(Perm, M);;
  Print("     dim Hom_F2G(Perm24, V) = ", Length(homs), "\n");
  best := 0;
  for h in homs do
    r := RankMat(h);
    if r > best then best := r; fi;
  od;
  Print("     max rank of a Perm24 -> V homomorphism = ", best, " of ", d,
        "   (== d => Perm24 SURJECTS onto V, incl the diagonal => ONE split prime suffices)\n\n");
od;
Print("DONE-1a\n");
QUIT;
