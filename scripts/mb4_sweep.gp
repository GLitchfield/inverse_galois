\\ minblk=4 twisted-Kummer A4 sweep -- generalized from the proven R_qsweep driver
\\ (2026-07-06, test 0043). Reads params from a gp file assigning BASE/WANT/PREF/QSTART/NQ/SPOUT,
\\ computes the degree-18 bnf fresh (cache it per base upstream -- bnfinit(deg-18) is the cost),
\\ sweeps the C(6,3) block-triple x coset selection (the module-control parameter), and writes
\\ every candidate whose real-root count is in WANT to SPOUT as "t=<tag> r=<r> KASC=<coeffs>".
\\ The block-triple tag (e.g. 236) IS the submodule selector proven to hit specific 24Tt.
default(parisizemax, 8*10^9);
read(PARAMS);   \\ defines BASE (sextic, ascending), WANT (r list), PREF, QSTART, NQ, SPOUT
rel = 'x^3 - 3*'x - 1;
nfF = nfinit(Pol(Vecrev(BASE), 'z));
rnf = rnfinit(nfF, rel);
bnf = bnfinit(rnf.polabs);   \\ degree-18 absolute field -- the expensive step
onef = Mod(1, nfF.pol);

findqfrom(lo) = {
  my(qq = 0);
  forprime(p = lo, 300000,
    if(#idealprimedec(bnf, p) == 18,
      my(pdt = idealprimedec(bnf, p), ap = 1);
      for(jj = 1, 18, my(pc = bnfisprincipal(bnf, pdt[jj]));
        if(#pc[1] > 0 && vecmax(abs(pc[1])) > 0, ap = 0; break));
      if(ap, qq = p; break)));
  qq;
};

buildJ(J) = {
  my(wabs = 1, tprod = 1, i);
  for(i = 1, #J, wabs = wabs * gens[J[i]] * Nup[J[i]]; tprod = tprod * Nlist[J[i]]^2);
  my(wr = rnfeltabstorel(rnf, wabs));
  my(cp = rnfcharpoly(nfF, rel, wr, 'y));
  my(s1 = -polcoef(cp, 2), s2 = polcoef(cp, 1));
  my(S1 = nfbasistoalg(nfF, nfalgtobasis(nfF, s1)),
     S2 = nfbasistoalg(nfF, nfalgtobasis(nfF, s2)),
     T  = nfbasistoalg(nfF, nfalgtobasis(nfF, tprod)));
  'x^4 - 2*S1*'x^2 - 8*T*'x + (S1^2 - 4*S2);
};

qlo = QSTART;
{for(qi = 1, NQ,
  q = findqfrom(qlo); if(q == 0, print("NO_MORE_Q"); break); qlo = q + 1;
  pd = idealprimedec(bnf, q);
  gens  = vector(18, j, nfbasistoalg(bnf, bnfisprincipal(bnf, pd[j])[2]));
  Nlist = vector(18, j, my(wr = rnfeltabstorel(rnf, gens[j]));
                        my(cp = rnfcharpoly(nfF, rel, wr, 'y)); -polcoef(cp, 0));
  Nup   = vector(18, j, rnfeltup(rnf, Nlist[j]));
  Pf = idealprimedec(nfF, q);
  blockOf = vector(18, j, my(bi = 0); for(i = 1, 6, if(nfeltval(nfF, Nlist[j], Pf[i]) > 0, bi = i)); bi);
  thetaM = rnfeltreltoabs(rnf, Mod('x, rel));
  rootsq = lift(polrootsmod('x^3 - 3*'x - 1, q));
  cidx = vector(18, j, my(ci = -1); for(k = 1, 3, if(nfeltval(bnf, thetaM - rootsq[k], pd[j]) > 0, ci = k - 1; break)); ci);
  bc = matrix(6, 3); for(j = 1, 18, if(blockOf[j] > 0 && cidx[j] >= 0, bc[blockOf[j], cidx[j] + 1] = j));
  for(b1 = 1, 4, for(b2 = b1 + 1, 5, for(b3 = b2 + 1, 6,
    my(J = [bc[b1, 1], bc[b2, 2], bc[b3, 3]]);
    if(vecmin(J) == 0, next);
    my(g = buildJ(J), K = rnfequation(nfF, g));
    my(r = if(polisirreducible(K), polsturm(K), -1));
    my(tag = concat(concat(Str(b1), Str(b2)), Str(b3)));
    if(vecsearch(vecsort(WANT), r),
      write(SPOUT, concat(concat(concat("t=", tag), concat(" r=", Str(r))), concat(" KASC=", Str(Vecrev(polredbest(K)))))));
  )));
  \\ 2-block J -> the SMALLER (dim-6) submodule: the construction-variety lever for the
  \\ unreached dim-6 cluster groups 16062/17948 (3-block gives dim-10; 2 generators give dim-6).
  \\ Sweep the second block's coset (c2) since a 2-subset has a free coset degree of freedom.
  for(b1 = 1, 5, for(b2 = b1 + 1, 6, for(c2 = 1, 3,
    my(J = [bc[b1, 1], bc[b2, c2]]);
    if(vecmin(J) == 0, next);
    my(g = buildJ(J), K = rnfequation(nfF, g));
    my(r = if(polisirreducible(K), polsturm(K), -1));
    my(tag = concat("2", concat(concat(Str(b1), Str(b2)), Str(c2))));
    if(vecsearch(vecsort(WANT), r),
      write(SPOUT, concat(concat(concat("t=", tag), concat(" r=", Str(r))), concat(" KASC=", Str(Vecrev(polredbest(K)))))));
  )));
);}
print("DONE_MB4_SWEEP");
