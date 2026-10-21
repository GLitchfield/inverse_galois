# Route-B (test 0050) load-bearing check: is closure(W) = closure(F_8) x closure(k) =
# AGL(3,2) x (C3|S3) a QUOTIENT of each affine-cluster target G?  (<=> is W=F_8.k a subfield
# of the target Galois closure L, i.e. is the seed/W radical universe the RIGHT one?)
#
# Splits the verdict:
#   CLUSTER A (14051/14052/16060/16061, kernel (C2)^6 IRREDUCIBLE): NO such quotient
#     => W is DISJOINT from L => seed/W radicals CANNOT reach the target.
#   CLUSTER B (19280/20408, kernel (C2)^9 = 3 (+) 6): closure(W) IS a quotient (the diagonal-3
#     = W's 2-core) => W IS a subfield of L => right universe, blocked only at module-select +
#     extraction (see docs/tests/0050-mb8-routeb-r24.md).
#
# C3-cubic targets => |closure(W)| = |AGL(3,2)| * 3 = 4032 ; S3-cubic => * 6 = 8064.
checkQuot := function(t, ordCW)
  local G, cand, K, Q, O2, msg;
  G := TransitiveGroup(24, t);
  cand := Filtered(NormalSubgroups(G), K -> Size(G)/Size(K) = ordCW);
  Print("24T", t, "  |G|=", Size(G), "  #quotients of order ", ordCW, ": ", Length(cand), "\n");
  for K in cand do
    Q := G/K;
    O2 := PCore(Q, 2);
    Print("     G/K = ", StructureDescription(Q), "  |O2|=", Size(O2),
          "  O2-elemAb=", IsElementaryAbelian(O2), "\n");
  od;
  if Length(cand) = 0 then
    Print("     => closure(W) NOT a quotient => W NOT in L (cluster A, structurally disjoint)\n");
  else
    Print("     => closure(W) IS a quotient => W IS a subfield of L (cluster B)\n");
  fi;
end;;
# C3 top (cubic disc square): closure(W) order 4032
checkQuot(14051, 4032);;
checkQuot(14052, 4032);;
checkQuot(19280, 4032);;
# S3 top (cubic disc non-square): closure(W) order 8064
checkQuot(16060, 8064);;
checkQuot(16061, 8064);;
checkQuot(20408, 8064);;
Print("DONE\n");
QUIT;
