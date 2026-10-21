# Frobenius cycle-type distribution (degree-24 permutation rep) for the PGL(2,7) minblk=8
# HARVEST-EXPANDED targets, for the local density pre-check (scripts/mb8_match.py). Emits, per
# target, a dist_<t>.txt: "order <|G|>" then one "<sorted,cycle,lengths> <classSize>" line per
# conjugacy class. AGL wreaths (24916/24922) are excluded here: |G|>=7e9 (fix8 agent owns them).
targets := [24672, 24592, 24593, 24489, 24594, 24316, 24488];;
dir := "data/targets/mb8";;
for t in targets do
  G := TransitiveGroup(24, t);
  cc := ConjugacyClasses(G);
  out := OutputTextFile(Concatenation(dir, "/dist_", String(t), ".txt"), false);
  SetPrintFormattingStatus(out, false);
  AppendTo(out, "order ", Size(G), "\n");
  for c in cc do
    g := Representative(c);
    cyc := ShallowCopy(CycleLengths(g, [1..24]));
    Sort(cyc);
    AppendTo(out, JoinStringsWithSeparator(List(cyc, String), ","), " ", Size(c), "\n");
  od;
  CloseStream(out);
  Print("done ", t, " |G|=", Size(G), " nclasses=", Length(cc), "\n");
od;
Print("DONE\n");
QUIT;
