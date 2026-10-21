for t in [14051, 16060, 19280, 20408] do
  G := TransitiveGroup(24, t);
  # 3 blocks of 8
  B := First(AllBlocks(G), b -> Size(b) = 8);
  BS := Orbit(G, B, OnSets);
  Print("==== 24T", t, "  #blocks(size8)=", Length(BS), "\n");
  # action on ONE block of 8 by its setwise stabilizer
  stab := Stabilizer(G, BS[1], OnSets);
  act := Action(stab, BS[1]);
  Print("     block-8 action = 8T", TransitiveIdentification(act),
        "  |img|=", Size(act), "  desc=", StructureDescription(act), "\n");
  # point stabilizer (index 24)
  ps := Stabilizer(G, 1);
  Print("     point stab order=", Size(ps), " (index ", Index(G,ps), ")  desc=",
        StructureDescription(ps), "\n");
od;
Print("DONE\n");
QUIT;
