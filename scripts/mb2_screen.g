LoadPackage("transgrp");;
# Run from the repo root; paths can be preset, e.g. gap -q -c 'MB2_TARGETS:="...";' scripts/mb2_screen.g
if not IsBound(MB2_TARGETS) then MB2_TARGETS := "data/processed/scratch/mb2_targets.txt"; fi;
if not IsBound(MB2_SCREEN_OUT) then MB2_SCREEN_OUT := "data/processed/scratch/mb2_screen.csv"; fi;
targets := List(SplitString(StringFile(MB2_TARGETS), "\n"), Int);;
out := OutputTextFile(MB2_SCREEN_OUT, false);;
SetPrintFormattingStatus(out, false);;
PrintTo(out, "t,order,kernel_size,central,split,top12j\n");
for t in targets do
  G := TransitiveGroup(24, t);
  blocks := Blocks(G, [1..24]);
  if Length(blocks) <> 12 then continue; fi;   # want the size-2 system (12 blocks)
  hom := ActionHomomorphism(G, blocks, OnSets);
  K := Kernel(hom);
  ks := Size(K);
  central := 0; split := -1; topj := 0;
  if ks = 2 and IsSubgroup(Centre(G), K) then
    central := 1;
    if Size(G) < 10000000 then
      if Length(ComplementClassesRepresentatives(G, K)) > 0 then split := 1; else split := 0; fi;
    fi;
  fi;
  topj := TransitiveIdentification(Image(hom));
  AppendTo(out, t, ",", Size(G), ",", ks, ",", central, ",", split, ",", topj, "\n");
od;
CloseStream(out);
Print("DONE\n");
QUIT;
