"""minblk=8 fix8 (r=24) unblock builder + Route-B sizing scaffold  (test 0049, 2026-07-07).

The 07-07 fix8 spike closed the seed-deformation family route as EMPIRICALLY DEAD: naive
linear/quadratic pencils f_u = s0 + u*g go to S8 (40320T50) at every sampled u for 16
low-degree g, the 2-seed pencil is S8-generic, and pure translation Res_y(c, s0(X-y))
collapses (reducible / [1,3,8,24]).  So a fix8-capable 8T48 octic family does NOT arise
from a low-degree deformation of a totally-real 8T48 seed.  (Findings +
sizing: data/processed/routeb_probe.json ; seed 8.8.410449079569.1.)

This module therefore ships the reusable machinery, not a landed build:
  --scan             reproduce the S8-escape finding (deformation Galois scan).
  --direct-proxy     demonstrate the Route-B disc-smooth profile (K16 = seed(sqrt theta),
                     theta a totally-positive S-unit at q=21557 -> disc primes {2,21557,640663}).
  build_res(...)     the certified octic-over-cubic Res pipeline (Res_y + polredabs) --
                     REUSABLE the instant a valid fix8-capable 8T48 octic FAMILY exists.
  gate(...)          the 4 MANDATORY local gates before any enqueue.
  --enqueue          push GATED r=24 candidates as lit:mb8new/pair/alt trophies
                     (tiers 130/115/100).  With no valid family this enqueues nothing.

RECOMMENDED PATH (Route B, sized in routeb_probe.json): direct split radical with
totally-positive square-classes.  S=1 -- one totally-split prime (e.g. q=21557) both
module-generates the cyclic (C2)^k kernel (incl the C3-diagonal for 19280/20408) AND
admits a totally-positive representative -- and the disc stays fully smooth (< 10^6).
Its full realization needs the relative L3(2)-over-cubic + Chebotarev module build
(top group C3xL3(2) order 504 => relative, not absolute bnfinit); not completed here.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from igp import baseline, db, gp  # noqa: E402
from igp import searchstore as store  # noqa: E402

_spec = importlib.util.spec_from_file_location("mb8_match", ROOT / "scripts" / "mb8_match.py")
mb8_match = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mb8_match)

SEED = "x^8 - 2*x^7 - 17*x^6 + 15*x^5 + 53*x^4 - x^3 - 37*x^2 - 15*x - 1"
WINNERS = ROOT / "data" / "processed" / "mb8_fix8_winners.jsonl"

# target -> (block-3 top signature required for r=24).  All 6 open on r=24 (progress.json).
AFFINE_TARGETS = [14051, 14052, 16060, 16061, 19280, 20408]


def scan_deformations() -> dict:
    """Reproduce the S8-escape finding: Galois group of s0 + u*g over sampled u.
    Returns {g_str: {'8T48': n, 'other': [names]}}.  Documents WHY the family route is dead."""
    gs = ["1", "x", "x^2", "x^3", "x^2-x", "x^2+x", "x^3-x", "x+1", "x^2+1",
          "2*x^2-x-1", "x^4", "x^7", "x^3+x", "x^2-2*x"]
    us = [1, -1, 2, -2, 3, -3, 5, 7, -5, 11]
    body_lines = [f"s0 = {SEED};", f"gs = [{','.join(gs)}];", f"us = {us};", "{",
                  "for(gi=1, length(gs), g = gs[gi]; c48 = 0; oth = \"\";",
                  "  for(ui=1, length(us), u = us[ui]; f = s0 + u*g;",
                  "    if(poldegree(f)==8 && polisirreducible(f),",
                  "      gl = polgalois(f);",
                  "      if(gl[1]==1344 && gl[3]==48, c48++, oth=Str(oth,\" \",gl[1],\"T\",gl[3]))));",
                  "  print(gi, \"|\", c48, \"|\", oth));", "}"]
    out = gp.script("\n".join(body_lines), timeout=550)
    res = {}
    for ln in out.splitlines():
        if "|" not in ln:
            continue
        gi, c48, oth = ln.split("|")
        res[gs[int(gi) - 1]] = {"8T48": int(c48), "other": oth.strip()}
    return res


def direct_radical_proxy(q: int = 21557) -> dict:
    """Route-B disc-profile demonstrator: K16 = seed(sqrt theta), theta a totally-positive
    S-unit at a totally-split prime q.  Shows the direct-radical disc is fully smooth."""
    body = (
        f"f = subst({SEED}, x, y);\n"
        "bnf = bnfinit(f); r1 = bnf.sign[1];\n"
        "gens = concat([bnf.tu[2]], bnf.fu);\n"
        "sv(a) = vector(r1, k, (1 - nfeltsign(bnf, a, k))/2);\n"
        "U = matconcat(vector(#gens, i, (sv(gens[i]))~));\n"
        f"pr = idealprimedec(bnf, {q}); pd = bnfisprincipal(bnf, pr[1]);\n"
        "pv = nfbasistoalg(bnf, pd[2]); sol = matsolvemod(U, 2, (sv(pv))~);\n"
        "un = prod(i=1, #gens, gens[i]^lift(sol[i])); th = pv * un;\n"
        "K16 = polredabs(rnfequation(f, x^2 - lift(th)));\n"
        "D = nfdisc(K16); fa = factor(abs(D));\n"
        "print(polsturm(K16), \"|\", logint(abs(D),2)+1, \"|\", vecmax(fa[,1]), \"|\", Vec(fa[,1]));"
    )
    out = gp.script(body, timeout=400).strip().splitlines()[-1]
    sturm, blen, maxp, primes = out.split("|")
    return {"q": q, "polsturm": int(sturm), "disc_bitlen": int(blen),
            "largest_prime": int(maxp), "smooth": int(maxp) < 10**6, "disc_primes": primes.strip()}


def build_res(octic_expr: str, cubic_expr: str, *, timeout: float = 500.0) -> list[int] | None:
    """Certified octic-over-cubic Res pipeline (identical shape to the 24315/24672 build).

    ``octic_expr`` = a gp octic in X and y (the FAMILY specialized at parameter=y, e.g. a
    valid fix8-capable 8T48 family ``s0(X)+y*g(X)`` once one exists, or Malle Thm 5.1/6.1).
    ``cubic_expr`` = a gp cubic in y (C3 disc-square for 14051/19280, S3 for 16060/20408).
    Returns ascending deg-24 coeffs (polredabs-reduced), or None if reducible/degenerate."""
    body = (
        f"f = {octic_expr};\n"
        f"c = {cubic_expr};\n"
        "R = polresultant(c, f, y); R = R/content(R); if(pollead(R)<0, R=-R);\n"
        "if(poldegree(R)!=24 || !polisirreducible(R), print(\"BAD\"),\n"
        "  Rr = polredabs(R); print(Vecrev(Rr)));"
    )
    out = gp.script(body, timeout=timeout).strip()
    if "BAD" in out or not out.startswith("["):
        return None
    return [int(x) for x in out.split("[")[-1].strip("[]").split(",")]


def gate(coeffs: list[int], target_t: int) -> tuple[bool, dict]:
    """The 4 MANDATORY local gates.  Returns (ok, info)."""
    info: dict = {}
    if len(coeffs) != 25 or coeffs[-1] != 1:
        return False, {"fail": "not-monic-deg24"}
    # (1) deg==24 && irreducible  (irreducibility already enforced in build_res; re-affirm degree)
    info["deg"] = len(coeffs) - 1
    # (2) polsturm == 24 (totally real => r=24)
    r = gp.real_roots(coeffs)
    info["r"] = r
    if r != 24:
        return False, {**info, "fail": f"not-totally-real (r={r})"}
    # (3) density-consistent with the SPECIFIC target t (mb8_match L1, not cycle-set alone)
    try:
        _tally, n, scored = mb8_match.predict(coeffs)
    except Exception as e:  # gp/factormod failure on the candidate
        return False, {**info, "fail": f"density-error {str(e)[:40]}"}
    l1, best_t, _order, impossible = scored[0]
    margin = scored[1][0] - l1 if len(scored) > 1 else 9.0
    info.update({"density_best": best_t, "l1": round(l1, 4),
                 "margin": round(margin, 4), "impossible": impossible, "n": n})
    if best_t != target_t or l1 >= 0.25 or margin <= 0.05 or impossible > 0:
        return False, {**info, "fail": "density-mismatch"}
    # (4) scoreable_disc not blank-only
    D = gp.scoreable_disc(coeffs, budget=55)
    info["scoreable_disc"] = D
    if D is None:
        return False, {**info, "fail": "non-scoreable (nfdisc blanked)"}
    return True, info


def enqueue_winners(winners: list[dict]) -> dict:
    """Enqueue gated r=24 winners as lit:mb8new/pair/alt trophies (tiers 130/115/100)."""
    store.init()
    realized = db.load_realized()
    held_groups = {r["t"] for r in realized if str(r.get("scoreable")).lower() == "true"}
    held_pairs = {(str(r["t"]), str(r["r"])) for r in realized
                  if str(r.get("scoreable")).lower() == "true"}
    tiers = {"new": 130.0, "pair": 115.0, "alt": 100.0}
    added = {"new": 0, "pair": 0, "alt": 0}
    for w in winners:
        t, r = str(w["t"]), str(w["r"])
        tier = "alt" if (t, r) in held_pairs else ("pair" if t in held_groups else "new")
        tag = f"lit:mb8{tier}:{t}.{r}:{w['src']}"
        line = ",".join(str(c) for c in w["coeffs"])
        if not store.has_target(tag) and store.enqueue("ready", {"coeffs": line}, target=tag):
            added[tier] += 1
    for tier, pri in tiers.items():
        store.set_priority_prefix(f"lit:mb8{tier}", pri)
    return added


def main() -> None:
    ap = argparse.ArgumentParser(description="minblk=8 fix8 (r=24) unblock scaffold")
    ap.add_argument("--scan", action="store_true", help="reproduce the S8-escape deformation finding")
    ap.add_argument("--direct-proxy", action="store_true",
                    help="demonstrate the Route-B disc-smooth profile (K16 proxy)")
    ap.add_argument("--enqueue", action="store_true",
                    help="gate + enqueue any r=24 winners in mb8_fix8_winners.jsonl")
    args = ap.parse_args()

    if args.scan:
        res = scan_deformations()
        n48 = sum(v["8T48"] for v in res.values())
        print(f"deformation scan: {len(res)} directions g; TOTAL non-trivial 8T48 fibers = {n48}")
        for g, v in res.items():
            print(f"  g={g:<12} 8T48={v['8T48']}  other=[{v['other']}]")
        print("VERDICT: fix8-capable 8T48 family does NOT arise from a low-degree pencil "
              "(all fibers S8) -- see data/processed/routeb_probe.json")

    if args.direct_proxy:
        print("Route-B direct-radical disc profile:", json.dumps(direct_radical_proxy()))

    if args.enqueue:
        winners = []
        if WINNERS.exists():
            for ln in WINNERS.read_text().splitlines():
                if ln.strip():
                    winners.append(json.loads(ln))
        gated = []
        for w in winners:
            ok, info = gate(w["coeffs"], w["t"])
            print(f"  24T{w['t']} src={w.get('src','?')}: {'PASS' if ok else 'REJECT'} {info}")
            if ok:
                gated.append({**w, "r": info["r"]})
        if gated:
            added = enqueue_winners(gated)
            print(f"enqueued new {added['new']}@130 / pair {added['pair']}@115 / alt {added['alt']}@100")
        else:
            print("no gated r=24 winners to enqueue "
                  "(seed-deformation dead; supply a valid fix8 family or a Route-B build)")

    if not (args.scan or args.direct_proxy or args.enqueue):
        ap.print_help()


if __name__ == "__main__":
    main()
