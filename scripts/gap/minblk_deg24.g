# Minimal block size per degree-24 transitive group (24Tt), via AllBlocks -- regenerates
# data/targets/block_structure_deg24.csv (test 0040). minblk=0 => primitive (no nontrivial block).
#
# A group with minimal block size a (b = 24/a blocks) is a subgroup of S_a wr S_b, hence buildable as
# a degree-a relative kernel over a degree-b base field. So minblk fixes the tower shape:
#   2 -> 12x2   3 -> 8x3   4 -> 6x4   6 -> 4x6   8 -> 3x8   12 -> 2x12.
#
# Run from the repo root:  gap -q -b scripts/gap/minblk_deg24.g   (~15s wall)
LoadPackage("transgrp");;
lines := ["t,minblk"];;
for t in [1..25000] do
  b := AllBlocks(TransitiveGroup(24, t));
  if Length(b) = 0 then m := 0; else m := Minimum(List(b, Length)); fi;
  Add(lines, Concatenation(String(t), ",", String(m)));
od;
PrintTo("data/targets/block_structure_deg24.csv", JoinStringsWithSeparator(lines, "\n"));
QUIT;
