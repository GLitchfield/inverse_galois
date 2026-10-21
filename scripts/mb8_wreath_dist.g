# Full-wreath cycle-type distributions for the density labeler (test 0045).
# 24916 = AGL(3,2) wr C3, 24922 = AGL(3,2) wr S3 -- the groups the DIRECT Malle-Thm-6.1
# octic-over-cubic resultant actually lands (NOT the twisted 19280/20408, see 0045).
# Emits `data/targets/mb8/dist_<t>.txt` (order line + one "cycletype size" line per class).
for t in [24916, 24922] do
  G := TransitiveGroup(24, t);
  cc := ConjugacyClasses(G);
  Print("== 24T", t, " order ", Size(G), " nclasses ", Length(cc), "\n");
  for c in cc do
    ct := List(Orbits(Group(Representative(c)), [1..24]), Length);
    Sort(ct);
    Print(JoinStringsWithSeparator(List(ct, String), ","), " ", Size(c), "\n");
  od;
od;
Print("DONE\n");
QUIT;
