# Family-sufficiency gate for the 9 NEW minblk=8 octic-over-cubic HARVEST-EXPANDED targets.
# For each target: enumerate identity + involution conjugacy classes, split by how many of the
# 3 octic blocks the class fixes (nfixblk). nfixblk=3 => (3,0)-cubic real structure, record the
# SORTED per-block fixed-point vector [f1,f2,f3]; nfixblk=1 => (1,1)-cubic, record the single
# fixed block's fixed-point count. The OCTIC FAMILY realizes a per-block involution only if its
# fixed-point count is in the family MENU (PGL 8T43 a=-1: {0,2,8}; AGL 8T48 Thm6.1: {0,4}, and 8
# needs the fix8 deformation). An r is FAMILY-REACHABLE by the plain family iff some recorded
# config has sum=r with every per-block entry in the menu.
# Output is machine-parseable: lines "T <t> <block8> <cubic>", "V30 <sum> <f1>,<f2>,<f3>",
# "V11 <f>", terminated by "ENDT".
targets := [
  [24672, "8T43", "S3"], [24592, "8T43", "C3"],
  [24922, "8T48", "S3"], [24916, "8T48", "C3"],
  [24593, "8T43", "S3"], [24489, "8T43", "C3"],
  [24594, "8T43", "S3"], [24316, "8T43", "C3"],
  [24488, "8T43", "S3"],
];;
for spec in targets do
  t := spec[1];
  G := TransitiveGroup(24, t);
  B := First(AllBlocks(G), b -> Size(b) = 8);
  BS := Orbit(G, B, OnSets);
  bact := ActionHomomorphism(G, BS, OnSets);
  Print("T ", t, " ", spec[2], " ", spec[3], "\n");
  for cc in ConjugacyClasses(G) do
    g := Representative(cc);
    if Order(g) <= 2 then
      bg := Image(bact, g);
      nfixblk := 3 - NrMovedPoints(bg);
      if nfixblk = 3 then
        v := List(BS, blk -> Number(blk, p -> p^g = p));
        Sort(v);
        Print("V30 ", Sum(v), " ", v[1], ",", v[2], ",", v[3], "\n");
      elif nfixblk = 1 then
        fb := First(BS, blk -> OnSets(blk, g) = blk);
        Print("V11 ", Number(fb, p -> p^g = p), "\n");
      fi;
    fi;
  od;
  Print("ENDT\n");
od;
Print("DONE\n");
QUIT;
