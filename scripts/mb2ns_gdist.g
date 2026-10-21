ts := [9633,9641,9642,14616,16607,19246,20699];
out := OutputTextFile("data/processed/mb2ns/gdist.json", false);
SetPrintFormattingStatus(out, false);
AppendTo(out, "{\n");
for i in [1..Length(ts)] do
  t := ts[i];
  G := TransitiveGroup(24, t);
  ord := Size(G);
  ccs := ConjugacyClasses(G);
  d := rec();
  distpairs := [];
  for c in ccs do
    rep := Representative(c);
    cl := SortedList(CycleLengths(rep, [1..24]));
    key := JoinStringsWithSeparator(List(cl, String), ",");
    sz := Size(c);
    if IsBound(d.(key)) then d.(key) := d.(key) + sz; else d.(key) := sz; fi;
  od;
  AppendTo(out, "\"", String(t), "\": {\"order\": ", String(ord), ", \"dist\": {");
  keys := RecNames(d);
  for j in [1..Length(keys)] do
    AppendTo(out, "\"", keys[j], "\": ", String(d.(keys[j])));
    if j < Length(keys) then AppendTo(out, ", "); fi;
  od;
  AppendTo(out, "}}");
  if i < Length(ts) then AppendTo(out, ",\n"); else AppendTo(out, "\n"); fi;
od;
AppendTo(out, "}\n");
CloseStream(out);
QUIT;
