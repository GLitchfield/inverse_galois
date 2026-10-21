# mb2_kummer_module.g -- research dive #46 (2026-07-12), reproducer.
#
# For a minblk=2 base top H = 12Tj and a target 24Tt, compute which split-prime subsets w
# realize the target's block kernel as the CLEAN Kummer module, and the residual-unit fields
# that control inflation toward the full wreath.
#
# Formalism (validated below, do not "simplify"):
#   q splits completely in K0 <=> completely in M (H faithful transitive).
#   M-primes <-> sigma in H; the K0-prime under P_sigma has index 1^sigma;
#   the conjugate alpha_j = sigma(alpha) has index 1^(sigma^-1)  (LEFT cosets, hence the inverse).
#   alpha with divisor 1_w  =>  D_w = sum_{sigma: 1^sigma in w} e_sigma  in F2[H].
#   Phi_w = the 12 x |H| matrix with rows sigma_j . D_w.
#   Kernel of the realized 24Tt = COLUMN SPACE of Phi_w in F2^12  (= N_val^perp).
#   Relations N_val = left-nullspace of Phi_w; for S in N_val the residual u_S = prod_{j in S} alpha_j
#   is a UNIT of F_S = M^Stab_H(S), and the realized kernel exceeds the clean dim by the rank of the
#   residual map into O_M*/(O_M*)^2 (inflation is upward only).
#
# VALIDATION GATES (both must print true; an indexing error breaks them):
#   * every column space is H-stable,
#   * the column space equals GAP's own block kernel of TransitiveGroup(24,t).
#
# Run: gap -q -b scripts/mb2_kummer_module.g

F := GF(2);;
TOPJ := 74;;               # base top 12Tj
TARGETS := [9641, 9642];;  # 24Tt whose block kernel we want to hit

H  := TransitiveGroup(12, TOPJ);;
elts := AsList(H);; n := Size(H);;
cosidx := List(elts, g -> 1^g);;
reps := List([1..12], j -> First(elts, g -> j^g = 1));;

PhiRows := function(w)
  local Dv, i, rows, j, g, vec, pos;
  Dv := List([1..n], i -> cosidx[i] in w);
  rows := [];
  for j in [1..12] do
    g := reps[j];
    vec := List([1..n], i -> 0*Z(2));
    for i in [1..n] do
      if Dv[i] then pos := Position(elts, g * elts[i]); vec[pos] := Z(2)^0; fi;
    od;
    rows[j] := vec;
  od;
  return rows;
end;;

CleanModule := function(w)          # the kernel the build lands with NO unit inflation
  local cols;
  cols := TransposedMat(PhiRows(w));
  return VectorSpace(F, Filtered(cols, v -> v <> Zero(v)), Zero(cols[1]));
end;;

IsHStable := function(V)
  return ForAll(GeneratorsOfGroup(H), g ->
           ForAll(BasisVectors(Basis(V)), v -> Permuted(v, g) in V));
end;;

BlockKernel := function(t)          # block kernel of 24Tt as a subspace of F2^12, in H's labeling
  local G, b2, bl, hom, HG, K, vecs, g, v, i, c;
  G := TransitiveGroup(24, t);
  b2 := First(AllBlocks(G), b -> Length(b) = 2);
  bl := Orbit(G, b2, OnSets);
  hom := ActionHomomorphism(G, bl, OnSets);
  HG := Image(hom); K := Kernel(hom);
  vecs := [];
  for g in AsList(K) do
    v := List([1..12], i -> 0*Z(2));
    # kernel elements PRESERVE each block setwise; the vector records the swap INSIDE each block
    for i in [1..12] do if bl[i][1]^g <> bl[i][1] then v[i] := Z(2)^0; fi; od;
    Add(vecs, v);
  od;
  vecs := Filtered(vecs, v -> v <> Zero(v));
  c := RepresentativeAction(SymmetricGroup(12), HG, H);
  return VectorSpace(F, List(vecs, v -> Permuted(v, c)), Zero(vecs[1]));
end;;

allw := List([1..4095], k -> Filtered([1..12], i -> QuoInt(k, 2^(i-1)) mod 2 = 1));;
mods := List(allw, CleanModule);;

Print("### base top 12T", TOPJ, "  |H|=", n, "  H1=", StructureDescription(Stabilizer(H,1)), "\n");
Print("VALIDATION all clean modules H-stable: ", ForAll(mods, IsHStable), "\n");
Print("clean-module dim tally over all 4095 w: ",
      Collected(List(mods, Dimension)), "\n\n");

for t in TARGETS do
  K := BlockKernel(t);
  hits := Filtered([1..4095], i -> mods[i] = K);
  Print("24T", t, ": block-kernel dim ", Dimension(K),
        "   VALIDATION kernel is a clean module: ", Length(hits) > 0, "\n");
  Print("   #w realizing it: ", Length(hits), " of 4095   sizes: ",
        Collected(List(hits, i -> Length(allw[i]))), "\n");
  if Length(hits) > 0 then
    w := allw[hits[1]];
    Print("   sample w=", w, "  residual-unit fields (inflation surface):\n");
    for b in NullspaceMat(ImmutableMatrix(F, PhiRows(w))) do
      S := Filtered([1..12], k -> b[k] <> 0*Z(2));
      St := Stabilizer(H, S, OnSets);
      r2 := Number(AbelianInvariants(St), x -> x mod 2 = 0);
      Print("     S=", S, " [F_S:Q]=", n/Size(St), " |Stab|=", Size(St),
            " 2rank=", r2, " => quad exts of F_S inside M: ", 2^r2 - 1, "\n");
    od;
  fi;
  Print("\n");
od;
QUIT;
