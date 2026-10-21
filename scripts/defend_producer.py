"""defend_producer -- disc-DEFENSE for gen12-held pairs we're BEHIND on (2026-07-07).

*** OUTCOME (test 0051, do not integrate as-is): the targeted premise FAILED. A smaller FIELD over
the same top at the right r builds fine (705 built, 392 Magma-verified), but the 24Tt is NOT preserved
-- 0/390 verified models hit the intended pair, because idealprimedec's ordering of the 12 primes is
base-dependent, so the same w-index selects a DIFFERENT kernel submodule per base (test 0038 alignment
problem; base-dependent + non-invertible). Net incidental value ~21 disc-improvements + 7 low-value
new pairs on OTHER groups. The reusable parts (source->(top,w) recovery, totally-real r-dial pool,
batched-bnfinit sweep) are sound; the single-w targeting gate is the wrong design. Fix = harvest broad
w + post-hoc Magma filter (fold into produce_selfcomp), NOT this. Kept for reference/repro. ***

Our score slipped (828->824.7) because rivals hold SMALLER FIELD discs on shared pairs. The
diagnosis (scripts/defend_held.py) puts 137 of 150 recoverable points in `gen12`-produced pairs at
teamCount k=2..5, with huge disc gaps (e.g. 24T20054 r12: our field disc 74 digits vs rival 34).

WHY recoverable: gen12 = general_c2 (deg-24 = a C2-kernel over a degree-12 base). The scoring disc is
the FIELD disc (nfdisc), driven mainly by the BASE disc; gen12 took the FIRST base hit (often a large-
disc base at a lazy large split prime). A much SMALLER-disc degree-12 base of the SAME top group 12Tj,
built at the SMALLEST split primes, realizes the same 24Tt with a far smaller field disc. The field
disc is invariant under polredabs, so "smaller model" = a genuinely SMALLER FIELD (smaller base /
smaller ramification), not a reduced representative.

RECOVERY (no queue lookup needed): each held gen12 row's `source` already encodes the top group and
the kernel w-pattern, e.g. `daemon:gen12:12T227:d<basedisc>:q<prime>:110110000000`. We parse the
`12Tj` top + the length-12 binary w, then pull the SMALLEST-disc LMFDB degree-12 bases of that SAME
top (disc-sorted ascending), rebuild general_c2 with the SAME w at the SMALLEST completely-split
primes (the prime is the r-dial, test 0036), polredbest, and GATE hard: irreducible deg-24, polsturm
== target r, and local nfdisc STRICTLY SMALLER than our current field disc for the pair (never enqueue
a model >= ours -- that wastes submission budget). Survivors enqueue as `ready` (pre-built) at target
`defend:<t>.<r>:d24:b<basedisc>`, priority 150 (above lit:new 130). Magma arbitrates the 24Tt label
(same-top same-construction should preserve it; a wrong label merely doesn't score, so it's safe).

Usage:
  python scripts/defend_producer.py                 # dry validation on the top-N behind gen12 pairs
  python scripts/defend_producer.py --enqueue        # build + enqueue the improved models
  python scripts/defend_producer.py --limit 400 --enqueue
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import defend_held  # noqa: E402  (reuse its ranked-loss loader)
from igp import gp, lmfdb  # noqa: E402
from igp import searchstore as store  # noqa: E402

CKPT = ROOT / "data" / "processed" / "defend_winners.jsonl"

TOP_RE = re.compile(r"12T\d+")
# a length-12 binary token not glued to other digits (the kernel w-pattern)
WTAG_RE = re.compile(r"(?<!\d)([01]{12})(?!\d)")


def parse_source(src: str):
    """(top_label, w_list) from a gen12 provenance string, or None if not parseable."""
    if "gen12" not in str(src):
        return None
    mt = TOP_RE.search(src)
    mw = WTAG_RE.search(src)
    if not mt or not mw:
        return None
    return mt.group(0), [int(c) for c in mw.group(1)]


def small_bases(top: str, target_r: int, n_pool: int = 6):
    """Smallest-disc deg-12 LMFDB bases of `top` that can reach `target_r`.

    K = F(sqrt alpha) has r_K = 2*(# real places of F with alpha>0), 0..2*r1 even -- so F needs
    r1 >= target_r/2. We pull the smallest-disc bases meeting that (max_r2=(12-r/2)/2) AND the
    totally-real ones (max_r2=0, which can dial ANY even r via the split prime -- essential for
    high r where the just-enough-real bases can't get all signs positive). Merge, disc-sort.
    """
    need_r1 = target_r // 2
    cap_r2 = (12 - need_r1) // 2
    pool = {}
    try:
        for coeffs, label, disc, h in lmfdb.fields(
                12, galois_label=top, class_number=None, max_r2=cap_r2, limit=n_pool + 4):
            pool[tuple(coeffs)] = (coeffs, disc)
    except Exception:
        pass
    if target_r > 0:  # add totally-real bases (max sign flexibility for high r)
        try:
            for coeffs, label, disc, h in lmfdb.fields(
                    12, galois_label=top, class_number=None, max_r2=0, limit=4):
                pool[tuple(coeffs)] = (coeffs, disc)
        except Exception:
            pass
    out = sorted(pool.values(), key=lambda cd: cd[1])
    return out[:n_pool]


def sweep_base(base_coeffs, w, primes, *, timeout: float = 300.0):
    """Build general_c2(base, w, q) for every q in `primes` in ONE gp process (bnfinit amortized).

    Returns [(q, r, coeffs_ascending)] for the primes that yield a valid degree-24 field (split,
    principal, non-degenerate). nfdisc is deferred to the caller (computed only for r-matches).
    """
    idx = [j + 1 for j, x in enumerate(w) if x]
    if not idx or not primes:
        return []
    cs = [int(c) for c in base_coeffs][::-1]
    # gp's stdin reader parses one statement per line, so the whole for-loop stays on ONE line
    # (newlines inside for(...) trip "unexpected end of file"); bnfinit is amortized across all q.
    loop = (
        f"for(i=1,#Q, q=Q[i]; pr=idealprimedec(bnf,q); "
        "if(#pr==12, Jd=pr[idx[1]]; for(k=2,#idx, Jd=idealmul(bnf,Jd,pr[idx[k]])); "
        "pd=bnfisprincipal(bnf,Jd); "
        "if(!(#pd[1]>0 && vecmax(abs(pd[1]))>0), "
        "al=lift(nfbasistoalg(bnf,pd[2])); rr=rnfequation(f,'x^2-al); "
        "if(poldegree(rr)==24, g=polredbest(rr); print(q,\"|\",polsturm(g),\"|\",Vec(g))))));"
    )
    body = (
        f"f=Pol({cs},'y);bnf=bnfinit(f);\n"
        f"idx={idx};Q={list(map(int, primes))};\n"
        + loop
    )
    try:
        out = gp.script(body, timeout=timeout)
    except Exception:
        return []
    res = []
    for ln in out.splitlines():
        if "|" not in ln:
            continue
        try:
            qs, rs, vec = ln.split("|")
            coeffs = [int(x) for x in vec.strip("[] ").split(",")][::-1]
            if len(coeffs) == 25:
                res.append((int(qs), int(rs), coeffs))
        except Exception:
            continue
    return res


def defend_pair(rec, *, n_bases: int = 6, n_primes: int = 12, hi: int = 60000,
                per_pair: int = 2):
    """Try to build up to `per_pair` strictly-smaller-disc models for one behind pair.

    Returns a dict with the outcome (winners = enqueue-ready coeffs + their field disc).
    """
    t, r = rec["t"], rec["r"]
    target_r = int(r)
    our_disc, min_disc = rec["ourDisc"], rec["minDisc"]
    parsed = parse_source(rec["source"])
    if not parsed:
        return {"t": t, "r": r, "status": "unparseable_source"}
    top, w = parsed
    bases = small_bases(top, target_r, n_pool=n_bases)
    if not bases:
        return {"t": t, "r": r, "top": top, "status": "no_bases"}
    winners = []
    our_dig = len(str(our_disc))
    for coeffs, base_disc in bases:
        try:
            primes = gp.split_primes(coeffs, 12, k=n_primes, hi=hi)
        except Exception:
            primes = []
        if not primes:
            continue
        cands = [c for c in sweep_base(coeffs, w, primes) if c[1] == target_r]
        cands.sort(key=lambda c: c[0])  # smallest split prime first (usually smallest disc)
        for q, rr, poly in cands[:4]:  # nfdisc only on the few smallest-prime r-matches
            try:
                fd = gp.scoreable_disc(poly)
            except Exception:
                fd = None
            if fd is None:
                continue
            fda = abs(int(fd))
            if fda < our_disc:
                winners.append({"base_disc": base_disc, "q": q, "field_disc": fda,
                                "field_dig": len(str(fda)), "coeffs": poly,
                                "beats_min": fda <= min_disc})
                break  # one winner per base is enough
        if len(winners) >= per_pair:
            break
    winners.sort(key=lambda wn: wn["field_disc"])
    return {"t": t, "r": r, "top": top, "our_dig": our_dig,
            "min_dig": len(str(min_disc)), "loss": rec["loss"], "k": rec["k"],
            "winners": winners[:per_pair],
            "status": "improved" if winners else "no_smaller_model"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enqueue", action="store_true", help="enqueue improved models as ready polys")
    ap.add_argument("--limit", type=int, default=400, help="max behind gen12 pairs to attempt")
    ap.add_argument("--min-weight", type=float, default=0.06, help="skip pairs with weight below")
    ap.add_argument("--kmax", type=int, default=5, help="only k<=this (k>=8 is worthless)")
    ap.add_argument("--per-pair", type=int, default=2, help="max models to enqueue per pair")
    ap.add_argument("--only", type=str, default="", help="comma t.r list -- validate specific pairs")
    args = ap.parse_args()

    data = defend_held.load()
    behind = [d for d in data if not d["we_hold_min"]]
    # gen12 family, k in {2..kmax}, weight >= min-weight, ranked by recoverable loss
    cand = [d for d in behind
            if defend_held.family(d["source"]) == "gen12"
            and 2 <= d["k"] <= args.kmax and d["weight"] >= args.min_weight]
    cand.sort(key=lambda d: -d["loss"])
    if args.only:
        want = set(args.only.split(","))
        cand = [d for d in cand if f"{d['t']}.{d['r']}" in want]
    cand = cand[:args.limit]

    print(f"=== DEFEND gen12: {len(cand)} behind pairs (k<= {args.kmax}, weight>= "
          f"{args.min_weight}), enqueue={args.enqueue} ===", flush=True)

    if args.enqueue:
        store.init()
    t0 = time.time()
    improved = enqueued = 0
    loss_full = 0.0      # sum of the pairs' FULL recoverable loss weight*(1-ratio) (task metric)
    recovered = 0.0      # actual score recovered = weight*(new_ratio - old_ratio)
    dig_reduced = 0
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    ck = open(CKPT, "a")
    for i, rec in enumerate(cand):
        res = defend_pair(rec, per_pair=args.per_pair)
        if res["status"] == "improved":
            improved += 1
            best = res["winners"][0]
            loss_full += rec["loss"]
            new_ratio = _new_ratio(best["field_disc"], rec["minDisc"])
            recovered += rec["weight"] * max(0.0, new_ratio - rec["ratio"])
            dig_reduced += res["our_dig"] - best["field_dig"]
            tag_flag = "<=MIN" if best["beats_min"] else "<ours"
            print(f"  [{i+1}/{len(cand)}] 24T{rec['t']} r{rec['r']} k={rec['k']} top={res['top']}"
                  f" disc {res['our_dig']}d->{best['field_dig']}d ({tag_flag}) "
                  f"nwin={len(res['winners'])}", flush=True)
            for wn in res["winners"]:
                rowlog = {"t": rec["t"], "r": rec["r"], "top": res["top"],
                          "our_disc": rec["ourDisc"], "min_disc": rec["minDisc"],
                          "field_disc": wn["field_disc"], "base_disc": wn["base_disc"],
                          "q": wn["q"], "coeffs": wn["coeffs"]}
                ck.write(json.dumps(rowlog) + "\n")
                ck.flush()
                if args.enqueue:
                    tag = f"defend:{rec['t']}.{rec['r']}:d24:b{wn['base_disc']}"
                    if store.enqueue("ready", {"coeffs": wn["coeffs"]}, target=tag):
                        enqueued += 1
        else:
            if (i + 1) % 20 == 0:
                print(f"  [{i+1}/{len(cand)}] ... {improved} improved so far "
                      f"({time.time()-t0:.0f}s)", flush=True)
    ck.close()
    if args.enqueue and enqueued:
        store.set_priority_prefix("defend:", 150.0)

    print(f"\n=== SUMMARY ===")
    print(f"  attempted:        {len(cand)} behind gen12 pairs")
    print(f"  improved:         {improved} got a strictly-smaller-disc model")
    print(f"  total disc digits reduced (sum over best models): {dig_reduced}")
    print(f"  recoverable loss of improved pairs (sum weight*(1-ratio)): {loss_full:.1f}")
    print(f"  ACTUAL score recovered (sum weight*(new_ratio-old_ratio)): {recovered:.1f}")
    print(f"  enqueued:         {enqueued} defend: ready polys (priority 150)")
    print(f"  winners logged:   {CKPT}")
    print(f"  elapsed:          {time.time()-t0:.0f}s")


def _new_ratio(new_disc: int, min_disc: int) -> float:
    import math
    d = max(new_disc, min_disc)  # can't score better than the global-min field disc
    return math.log(min_disc) / math.log(d) if d > 1 else 1.0


if __name__ == "__main__":
    main()
