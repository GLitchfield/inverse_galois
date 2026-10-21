\\ Is every narrow-class character of our deg-12 totally-real bases a RATIONAL GENUS character?
\\ Research dive #53 (follows dive #52: on 12T245 the nontrivial narrow character was kronecker(-3,.)).
\\
\\ For a totally-real K0 with h = 1, Cl+(K0) = {+-1}^12 / sign(units) is ELEMENTARY ABELIAN 2, of rank
\\   delta = 12 - rk_F2(sign matrix of the units + (-1)).
\\ Its characters <-> quadratic extensions of K0 unramified at all FINITE primes (infinity is free).
\\ A character is RATIONAL (genus) iff that extension is K0(sqrt m) for some m in Q  <=>  it is the
\\ extended genus field of Froehlich/Ishida.  Then chi(P) = kronecker(m, p)^f_P is pure arithmetic on
\\ disc K0 -- no bnfinit, no bnrinit.
\\
\\ g = dim_F2 of the group of rational classes m (mod Q*^2) giving an unramified-at-finite ext,
\\     MINUS the ones that are already squares in K0 (they give the trivial character).
\\ ALL narrow characters rational  <=>  g == delta.
\\
\\ Exactness note: for ODD p, K0(sqrt m)/K0 is unramified at p  <=>  v_P(m) = e_P * v_p(m) is even for
\\ every P | p, so supp(m) must consist of ramified p with ALL e_P even.  p = 2 is decided by
\\ rnfconductor (which is the authority for every candidate anyway).

read(BASEFILE);   \\ defines BASES = [[tag, coeffs...], ...]

{
for(bi = 1, #BASES,
  my(B = BASES[bi], tag = B[1], c = B[2], f = Pol(Vecrev(c), 'y));
  my(t0 = getabstime());
  my(K = bnfinit(f, 1));
  my(h = K.no, dK = K.disc);
  \\ delta: rank of the F2 sign lattice of units (bnfsignunit) together with -1 (always a unit).
  my(SU = bnfsignunit(K));
  my(M = matconcat([matrix(12, #SU[1,], i, j, (1 - SU[i,j]) / 2), vectorv(12, i, 1)]));
  my(rk = matrank(Mod(M, 2)));
  my(delta = 12 - rk);
  my(fa = factor(abs(dK)), ps = fa[,1]~);
  \\ candidate support: ramified p with all e_P even  (odd p exact; keep 2 always, rnfconductor rules)
  my(supp = List());
  for(i = 1, #ps,
    my(p = ps[i], dec = idealprimedec(K, p), alleven = 1);
    for(j = 1, #dec, if(dec[j].e % 2 == 1, alleven = 0; break));
    if(p == 2 || alleven, listput(supp, p)));
  supp = Vec(supp);
  \\ enumerate m = +- prod(subset of supp), test unramified-at-finite via rnfconductor
  my(unram = List(), sqin = List(), n = #supp);
  for(s = 0, 2^n - 1,
    for(sg = 0, 1,
      my(m = if(sg, -1, 1));
      for(i = 1, n, if(bitand(s, 1 << (i-1)), m *= supp[i]));
      if(m == 1, next);
      if(#nfroots(K, x^2 - m) > 0, listput(sqin, m); next);
      my(cf = rnfconductor(K, x^2 - m));
      if(idealnorm(K, cf[1]) == 1, listput(unram, m))));
  \\ W = <unram, sqin> in Q*/Q*^2 ; g = dim W - dim <sqin>
  my(U = Vec(unram), S = Vec(sqin));
  my(gdim = 0);
  \\ dims via F2 exponent vectors over the primes of supp plus the sign coordinate
  my(vec(m) = my(v = vectorv(n + 1)); v[n+1] = if(m < 0, Mod(1,2), Mod(0,2));
     for(i = 1, n, v[i] = Mod(if(abs(m) % supp[i] == 0, 1, 0), 2)); v);
  my(dimof(L) = if(#L == 0, 0, matrank(matconcat(vector(#L, i, vec(L[i]))))));
  my(dW = dimof(concat(U, S)), dS = dimof(S));
  gdim = dW - dS;
  print("BASE|", tag, "|h=", h, "|delta=", delta, "|g=", gdim,
        "|rational=", if(gdim == delta, 1, 0),
        "|supp=", supp, "|unram=", U, "|sqinK0=", S,
        "|disc=", dK, "|secs=", (getabstime() - t0) / 1000.0);
);
}
quit;
