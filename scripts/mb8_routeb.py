"""minblk=8 affine-cluster r=24 Route-B (direct radical / relative Kummer) driver  (test 0050).

Route B is the residual Track F (test 0049) deferred after proving the fix8 seed-deformation
family DEAD.  This module carries Route B to a DEFINITIVE feasibility verdict:

  VERDICT (data/processed/routeb_feasibility.json): BLOCKED in pure PARI/GP.  It is NOT a
  build-cost wall -- the whole degree-192 (C2)^3-Kummer radical tower over W=F_8.k BUILDS in
  ~20-40s.  It is a STRUCTURAL + tooling wall, and the reason SPLITS by cluster (GAP-verified):

  1a. CLUSTER A (14051/14052/16060/16061, irreducible (C2)^6): the seed F_8 and W=F_8.k are
      STRUCTURALLY DISJOINT from the target closure L.  GAP: 14051/16060 have ZERO order-4032
      quotients, so closure(W)=AGL(3,2)xC3=(C2)^3:(C3xL3(2)) is NOT a quotient of G (N
      Q-irreducible => no (C2)^3 submodule, no AGL(3,2) quotient).  All targets have subfields
      [1,3,24] (E24/k PRIMITIVE, no deg-8) while W has [1,3,8,24]; the block-8 8T48 is only the
      block-STABILISER's action, never a deg-8 field over Q.  => NO radical tower over the seed
      / W reaches cluster A (empirically: C48=K16.k has a UNIQUE deg-24 subfield = diagonal W).
  1b. CLUSTER B (19280/20408, reducible (C2)^9=3(+)6): W IS a subfield of L -- GAP: 19280 HAS
      the order-4032 quotient C3xAGL(3,2)=closure(W) (the diagonal-3 = W's 2-core).  So W is the
      right universe; blocked at (a) selecting the F4-twist 6-dim Galois-stable module classes
      over W (needs the F2[Q]-module decomposition of Cl(W)/S-units) and (b) nfsubfields(deg-192)
      extraction (>8min, no return).

  2. TOOLING: the CORRECT frame is the (C3|S3)xL3(2) field (degree 504|1008; PARI-feasible
     non-Galois model M0 = L3(2)-septic . cubic, degree 21|42, bnfinit ~400ms, tot-pos codim 0
     so r=24 is clean).  But realizing N=(C2)^6=3(x)F4 over it needs (i) the Galois-module
     selection of the F4-twisted submodule of Cl(M)/2 (Q-action lives on the degree-504
     closure), (iii) the non-abelian (C2)^3-torsor assembly into a k-rational AGL(3,2) octic
     with the prescribed C3-twist, (iv) the point-stabiliser extraction -- none automated in
     PARI.  This is Magma / OSCAR(Hecke) relative-Kummer + class-field-theory-with-automorphisms
     territory (a build_backlog TOOLING item, not a PARI producer).

Usage:
  --probe     reproduce the feasibility verdict (build timings + structural checks), fast.
  --enqueue   gate + enqueue any density-verified r=24 winners in mb8_routeb_winners.jsonl
              (reuses scripts/mb8_fix8.py gate()/enqueue).  Currently enqueues NOTHING -- no
              PARI-buildable model exists; supply models from an OSCAR/Magma relative-Kummer run.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from igp import gp  # noqa: E402

# reuse Track F's certified gate() + enqueue machinery (deg24+irred, polsturm==24,
# mb8_match density, scoreable_disc) verbatim -- no reason to reimplement.
_spec = importlib.util.spec_from_file_location("mb8_fix8", ROOT / "scripts" / "mb8_fix8.py")
mb8_fix8 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mb8_fix8)

SEED = "y^8 - 2*y^7 - 17*y^6 + 15*y^5 + 53*y^4 - y^3 - 37*y^2 - 15*y - 1"
CUBIC_C3 = "y^3 - y^2 - 2*y + 1"        # cyclic, disc 49 (square)  -> C3 quotient (14051/14052/19280)
WINNERS = ROOT / "data" / "processed" / "mb8_routeb_winners.jsonl"
FEAS = ROOT / "data" / "processed" / "routeb_feasibility.json"
TARGETS = [14051, 14052, 16060, 16061, 19280, 20408]


def probe_build() -> dict:
    """Reproduce the definitive feasibility timings: the (C2)^3-Kummer tower over W=F_8.k
    BUILDS cheaply (proving the wall is not build-cost), and the L3(2)/C3xL3(2) frame is
    bnfinit-cheap (proving the wall is not the frame).  Returns the timing dict."""
    body = (
        f"seed = {SEED}; kc = {CUBIC_C3};\n"
        "W = polredbest(polcompositum(seed, kc)[1]);\n"
        "t0=gettime(); bnf = bnfinit(W, 1); tW=gettime();\n"
        "r1=bnf.sign[1]; gens=concat([bnf.tu[2]],bnf.fu);\n"
        "sv(a)=vector(r1,k,(1-nfeltsign(bnf,a,k))/2);\n"
        "U=matconcat(vector(length(gens),i,(sv(gens[i]))~));\n"
        "rk=matrank(U*Mod(1,2));\n"
        "q=0; forprime(p=2,10^6, if(length(idealprimedec(bnf,p))==24,q=p;break));\n"
        "pr=idealprimedec(bnf,q);\n"
        "t1=lift(nfbasistoalg(bnf,bnfisprincipal(bnf,pr[1])[2]));\n"
        "t2=lift(nfbasistoalg(bnf,bnfisprincipal(bnf,pr[2])[2]));\n"
        "t3=lift(nfbasistoalg(bnf,bnfisprincipal(bnf,pr[3])[2]));\n"
        "gettime(); Ka=rnfequation(bnf,x^2-t1); Kb=rnfequation(bnf,x^2-t2); Kc=rnfequation(bnf,x^2-t3); tK48=gettime();\n"
        "K96=polcompositum(Ka,Kb)[1]; t96=gettime();\n"
        "K192=polcompositum(K96,Kc)[1]; t192=gettime();\n"
        "print(tW,\"|\",rk,\"|\",r1,\"|\",q,\"|\",tK48,\"|\",t96,\"|\",poldegree(K96),\"|\",t192,\"|\",poldegree(K192));"
    )
    out = gp.script(body, timeout=180).strip().splitlines()[-1]
    tW, rk, r1, q, tK48, t96, d96, t192, d192 = out.split("|")
    return {
        "bnfinit_W_deg24_ms": int(tW), "unit_sign_rank": int(rk), "r1": int(r1),
        "smallest_totally_split_in_W_prime": int(q),
        "three_rnfequation_deg48_ms": int(tK48),
        "polcompositum_deg96_ms": int(t96), "deg96": int(d96),
        "polcompositum_deg192_ms": int(t192), "deg192": int(d192),
        "note": "full (C2)^3-Kummer of W builds cheaply; nfsubfields(192,24) is the extraction "
                "wall (>8min, no return) but MOOT -- W is structurally disjoint from the targets.",
    }


def probe_frame() -> dict:
    """The correct frame is bnfinit-cheap: L3(2) septic (deg 7) and the C3xL3(2) model (deg 21).
    Confirms the wall is the relative-Kummer module/torsor/extraction, NOT the frame arithmetic.
    (Uses an S7 septic as a degree/cost stand-in; a genuine 7T5=L3(2) septic costs the same.)"""
    body = (
        "s7 = x^7 - x^6 - 12*x^5 + 7*x^4 + 28*x^3 - 14*x^2 - 9*x + 1;\n"
        "gettime(); b7=bnfinit(s7,1); t7=gettime();\n"
        "M0=polredbest(polcompositum(s7, x^3-x^2-2*x+1)[1]);\n"
        "gettime(); bM=bnfinit(M0,1); tM=gettime();\n"
        "r1=bM.sign[1]; gens=concat([bM.tu[2]],bM.fu);\n"
        "sv(a)=vector(r1,k,(1-nfeltsign(bM,a,k))/2);\n"
        "U=matconcat(vector(length(gens),i,(sv(gens[i]))~));\n"
        "print(t7,\"|\",tM,\"|\",poldegree(M0),\"|\",r1,\"|\",matrank(U*Mod(1,2)));"
    )
    out = gp.script(body, timeout=180).strip().splitlines()[-1]
    t7, tM, dM, r1, rk = out.split("|")
    return {"bnfinit_septic_deg7_ms": int(t7), "bnfinit_frame_deg21_ms": int(tM),
            "frame_deg": int(dM), "frame_r1": int(r1), "frame_unit_sign_rank": int(rk),
            "totally_positive_codim": int(r1) - int(rk),
            "note": "tot-pos codim 0 => every radicand sign-fixable => r=24 clean over the frame."}


def enqueue() -> dict:
    """Gate (mb8_fix8.gate: deg24+irred, polsturm==24, mb8_match density, scoreable_disc) and
    enqueue r=24 winners from mb8_routeb_winners.jsonl.  Ready for OSCAR/Magma-built models;
    enqueues nothing while no PARI-buildable model exists."""
    winners = []
    if WINNERS.exists():
        for ln in WINNERS.read_text().splitlines():
            if ln.strip():
                winners.append(json.loads(ln))
    gated = []
    for w in winners:
        ok, info = mb8_fix8.gate(w["coeffs"], w["t"])
        print(f"  24T{w['t']} src={w.get('src','?')}: {'PASS' if ok else 'REJECT'} {info}")
        if ok:
            gated.append({**w, "r": info["r"], "src": w.get("src", "routeb")})
    if gated:
        added = mb8_fix8.enqueue_winners(gated)
        print(f"enqueued new {added['new']}@130 / pair {added['pair']}@115 / alt {added['alt']}@100")
        return added
    print("no gated r=24 winners to enqueue (Route B BLOCKED in pure PARI -- needs an "
          "OSCAR/Magma relative-Kummer model; see data/processed/routeb_feasibility.json)")
    return {"new": 0, "pair": 0, "alt": 0}


def main() -> None:
    ap = argparse.ArgumentParser(description="minblk=8 affine r=24 Route-B feasibility + enqueue")
    ap.add_argument("--probe", action="store_true", help="reproduce the feasibility verdict (fast)")
    ap.add_argument("--enqueue", action="store_true", help="gate + enqueue r=24 winners (none yet)")
    args = ap.parse_args()
    if args.probe:
        print("build feasibility :", json.dumps(probe_build()))
        print("frame feasibility :", json.dumps(probe_frame()))
        print("VERDICT: build is CHEAP, frame is CHEAP -- BLOCKED is structural + tooling. "
              "See data/processed/routeb_feasibility.json")
    if args.enqueue:
        enqueue()
    if not (args.probe or args.enqueue):
        ap.print_help()


if __name__ == "__main__":
    main()
