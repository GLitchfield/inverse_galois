"""search_ctl — manage the search daemon (searchd).

Subcommands:
  refresh                fetch the live leaderboard -> data/processed/progress.json
  tick                   hands-off maintenance (for cron): ensure daemon, refresh, produce, status
  produce                enqueue UNDISCOVERED targets from the exact-labeling Galois families
  produce-spec           enqueue speculative constructions over the non-Galois base library
  status                 queue counts + daemon's last status + sole realizers so far
  health                 per-producer feed health -- flags a SILENT/CRASHING producer (gen12 guard)
  failures               SAIR per-poly rejection reasons, tallied by producer (why polys fail)
  harvest                list verified targets (label, scoreable)
  pause | resume | stop  set the daemon control flags
  set KEY VALUE          set a kv knob (interval, build_batch, max_pending, max_posts_day)

Run: uv run python scripts/search_ctl.py <cmd> [args]
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from itertools import combinations
from pathlib import Path

from igp import db, gap, gp, rank, sair
from igp import kernelsolve as ks
from igp import searchstore as store

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "data" / "processed" / "searchd.log"

PROG = Path(__file__).resolve().parents[1] / "data" / "processed" / "progress.json"

# Non-Galois degree-12 bases (coeffs ascending, h=1, completely-split prime). The daemon's
# construct->submit->Magma flow labels these without needing a-priori alignment, so diverse
# bases => diverse (less-popular) tops => higher undiscovered yield. Extend this library.
NONGALOIS_LIB = [
    ([-2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 601),       # x^12 - 2        (12T28)
    ([-1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1], 541),      # x^12 - x^6 - 1
    ([-1, 0, 0, 0, 0, 0, -2, 0, 0, 0, 0, 0, 1], 337),      # x^12 - 2x^6 - 1
]


def refresh():
    # archive the outgoing snapshot first: day-over-day teamCount diffs reveal WHERE rivals'
    # mass-claims landed (the vein-diagnosis lever, 2026-07-04)
    try:
        if PROG.exists():
            arch = PROG.parent / "progress_archive"
            arch.mkdir(exist_ok=True)
            stamp = time.strftime("%Y%m%d_%H%M", time.localtime(PROG.stat().st_mtime))
            (arch / f"progress_{stamp}.json").write_bytes(PROG.read_bytes())
    except Exception:
        pass
    prog = {}
    n = 0
    for lab in sair.labels_progress():
        for sig in lab.get("signatures", []):
            prog[f"{lab['t']},{sig['r']}"] = {
                "teamCount": sig.get("teamCount", 0),
                "minDisc": sig.get("minimumDiscAbs"),
            }
        n += 1
    PROG.parent.mkdir(parents=True, exist_ok=True)
    PROG.write_text(json.dumps(prog))
    print(f"refreshed: {n} labels, {len(prog)} signatures -> {PROG.name}")


def _galois_families():
    fa = "polredbest(nfsplitting(x^4+8*x+12))"
    fd = "polredbest(polcompositum(nfsplitting(x^3-2), x^2-5)[1])"
    a4 = [int(x) for x in gp.script(f"print(Vec({fa}));").strip("[]").split(",")][::-1]
    d6 = [int(x) for x in gp.script(f"print(Vec({fd}));").strip("[]").split(",")][::-1]
    return [
        ("C12", gp.cyclotomic_top_perms(13),
         lambda w: ("cyclotomic_c2", {"w": w, "n": 13, "q": 53})),
        ("C2xC6", gp.cyclotomic_top_perms(21),
         lambda w: ("cyclotomic_c2", {"w": w, "n": 21, "q": 43})),
        ("D6", gp.galois_action_perms(d6),
         lambda w: ("galois_c2", {"base": d6, "w": w, "q": 31})),
        ("A4", gp.galois_action_perms(a4),
         lambda w: ("galois_c2", {"base": a4, "w": w, "q": 71})),
    ]


def produce():
    if not PROG.exists():
        print("no progress.json; run `refresh` first")
        return
    prog = json.loads(PROG.read_text())
    def undisc(t):
        return prog.get(f"{t},0", {}).get("teamCount", 1) == 0

    store.init()
    added = 0
    for name, perms, mk in _galois_families():
        reps = {}
        for pc in range(1, 5):
            for idx in combinations(range(12), pc):
                w = [1 if k in idx else 0 for k in range(12)]
                reps.setdefault(ks.module_basis(sum(1 << k for k in idx), perms), w)
        ws = list(reps.values())
        labels = gap.kernel_labels_for_top(perms, ws)
        for w in ws:
            lab = labels.get(tuple(w))
            if lab and undisc(lab[3:]):
                kind, payload = mk(w)
                if store.enqueue(kind, payload, target=lab):
                    added += 1
                    print(f"  + {lab} ({name})")
    print(f"enqueued {added} undiscovered targets; queue={store.counts()}")


def produce_spec(per_base: int = 12):
    """Speculative producer: enqueue C_2-kernel constructions over the non-Galois base library.

    No a-priori target (Magma labels post-construction); the daemon submits and we harvest
    whatever lands undiscovered. Low-popcount kernel patterns per base.
    """
    store.init()
    pats = []
    for i in range(12):
        pats.append([1 if k == i else 0 for k in range(12)])
    for i, j in combinations(range(12), 2):
        pats.append([1 if k in (i, j) else 0 for k in range(12)])
    added = 0
    for bi, (base, q0) in enumerate(NONGALOIS_LIB):
        qs = _split_primes(base, 12, k=6) or [q0]   # sweep primes -> sweep r (test 0036)
        for q in qs:
            for w in pats[:per_base]:
                if store.enqueue("general_c2", {"base": base, "w": w, "q": q},
                                 target=f"spec:b{bi}:q{q}:{''.join(map(str, w))}"):
                    added += 1
    print(f"enqueued {added} speculative constructions; queue={store.counts()}")


CUBICS = ["x^3-2", "x^3-3", "x^3-x-1", "x^3+x-1", "x^3-x^2-2*x-1"]   # S_3 and C_3
QUARTICS = ["x^4-2", "x^4+1", "x^4-x-1", "x^4+x+1", "x^4-2*x^2-2", "x^4+8*x+12"]  # varied


def _compositum_base(c: str, qu: str, hi: int = 3000):
    """Degree-12 compositum of two polys -> (ascending coeffs, split prime) or None."""
    out = gp.script(
        f"C=polcompositum(({c}),({qu}));F=0;for(i=1,#C,if(poldegree(C[i])==12,F=C[i]));"
        "if(F==0,print(\"SKIP\"),Fr=polredbest(F);bnf=bnfinit(Fr);sq=0;"
        f"for(q=2,{hi},if(isprime(q)&&#idealprimedec(bnf,q)==12,sq=q;break));"
        "print(if(sq==0,\"NOSPLIT\",Vec(Fr)));print(sq))",
        timeout=300,
    )
    lines = [ln for ln in out.splitlines() if ln.strip()]
    if not lines or not lines[0].startswith("["):
        return None
    coeffs = [int(x) for x in lines[0].strip("[]").split(",")][::-1]
    return coeffs, int(lines[1])


def produce_compositum(per_base: int = 10):
    """Enqueue C_2-kernels over degree-12 compositum bases (diverse/obscure tops)."""
    store.init()
    pats = [[1 if k == i else 0 for k in range(12)] for i in range(12)]
    pats += [[1 if k in (0, i) else 0 for k in range(12)] for i in range(1, 12)]
    added = bases = 0
    for c in CUBICS:
        for qu in QUARTICS:
            try:
                res = _compositum_base(c, qu)
            except Exception:
                res = None
            if not res:
                continue
            base, q = res
            bases += 1
            tag = f"comp:{c}|{qu}"
            qs = _split_primes(base, 12, k=6) or [q]   # sweep primes -> sweep r (test 0036)
            for q in qs:
                for w in pats[:per_base]:
                    if store.enqueue("general_c2", {"base": base, "w": w, "q": q},
                                     target=f"{tag}:q{q}:{''.join(map(str, w))}"):
                        added += 1
    print(f"compositum producer: {bases} feasible bases, enqueued {added}; queue={store.counts()}")


# Malle-Matzat M24/Q(t) family (arXiv 1204.1328, s=0): F = (t - A0)^2 + (X^2+1)*B0^2 has Galois
# group M24 over Q(t). M24 is PRIMITIVE + non-solvable -> unreachable by tower constructions (which
# need a completely-split prime, density 1/|H|, infeasible for primitive |H|); an explicit family is
# the only route. Sum-of-squares => all specializations totally complex => signature (M24, r=0).
_M24_A0 = ("4194304*X^12-72351744*X^10+1572864*X^9+154443776*X^8-34062336*X^7+46684160*X^6"
           "+16098816*X^5-156060348*X^4+30667728*X^3-5330757*X^2-3462498*X+9958791")
_M24_B0 = ("-25165824*X^10-1572864*X^9+145227776*X^8-16515072*X^7-164757504*X^6+48453120*X^5"
           "-56207872*X^4-6865152*X^3+71415384*X^2-8906760*X+224829")


def produce_m24(t_lo: int = -60, t_hi: int = 60):
    """Specialize the Malle-Matzat M24/Q(t) family F = (t-A0)^2 + (X^2+1)*B0^2 (arXiv 1204.1328) ->
    degree-24 polynomials with Galois group M24 (primitive). polredbest -> monic; sum-of-squares =>
    all totally complex => (M24, r=0).

    LOW VALUE -- DO NOT auto-run or prioritize. M24 (24T24680, r=0) is the textbook primitive group
    everyone realizes via this same published family: teamCount=11 => 2^(1-11) ~ 0.001, and we
    already hold it (worse disc than the leaderboard min). Lesson (the hard way): a FAMOUS group
    a published family is CONTESTED, not a sole-realizer 1.0. The teamCount==0 1.0s live in OBSCURE
    groups reached by the targeted gate, not in named primitives. Kept only to document the family.
    """
    store.init()
    added = 0
    for t in range(t_lo, t_hi + 1):
        tgt = f"m24:s0:t{t}"
        if store.has_target(tgt):
            continue
        try:
            out = gp.script(
                f"F=(({t})-({_M24_A0}))^2+(X^2+1)*({_M24_B0})^2;print(Vec(polredbest(F)))",
                timeout=150)
            co = [int(x) for x in out.strip("[]").split(",")][::-1]
        except Exception:
            continue
        if co and len(co) == 25 and co[-1] == 1 \
                and store.enqueue("ready", {"coeffs": co}, target=tgt):
            added += 1
    print(f"m24 producer: enqueued {added} M24 specializations; queue={store.counts()}")


# Verified explicit degree-24 polynomials from the literature (constant-first / ascending coeffs,
# monic). Each was locally confirmed: irreducible, deg 24, real-root count = the target r, and the
# stated smooth field disc (2026-06-30 dive; docs/auto_log.md). Label confirmed by SAIR/Magma on
# submission. Only the ones that ADD value vs our coverage are listed (fresh group or disc-min win).
_LITERATURE = [
    # Roberts f_C2(53/22,x), S.M12.A paper (personal.morris.umn.edu/~roberts/research/m12.pdf).
    # -> M12.2 = 24T18441, r=0, field disc 2^12*3^24*11^22. We hold 0 rows for 18441 => FRESH GROUP
    # (its disc equals the current leaderboard min; teamCount=2 so shared, not sole -- value is the
    # distinct-group headline, not a disc beat).
    ("lit:roberts_m12.2_fC2", "24T18441 r0 M12.2 (Roberts m12.pdf)",
     [81, 2673, 15552, -104841, 278586, -520641, 733491, -753291, 623997, -483318, 351252,
      -237699, 154308, -89067, 42768, -17710, 6512, -2255, 1012, -594, 330, -154, 53, -11, 1]),
    # Bosman P_16,23, level-1 modular forms (arXiv:0710.1237, Table 1). -> PGL(2,23) = 24T10255,
    # r=2, field disc -23^37 (ramified only at 23). 10.5x smaller than the leaderboard min at
    # (10255,2) => disc-min win (baseline pair, caps at 0.5).
    ("lit:bosman_pgl2_23_P16", "24T10255 r2 PGL(2,23) (Bosman arXiv:0710.1237)",
     [55431347, 252536071, 484510019, 438371490, 41851168, -357303183, -397878081, -158103380,
      60172945, 106722024, 52203054, 2669403, -10740931, -6156732, -1208328, 308798, 255599,
      59639, 1058, -1886, -138, 115, 46, 9, 1]),
    # LMFDB degree-24 field (public database row), disc-min pull: strict D_base beat at (201, 0).
    ("lit:t201_r0_discmin", "24T201 r0 disc-min pull (strict D_base beat, tc=3)",
     [19102691171, -73544667498, 160857935018, -233830339250, 245051163350, -194950475952,
      123937218667, -66031129034, 30646649329, -12732271020, 4831154654, -1697566468,
      550577979, -163896444, 45288146, -11566776, 2702251, -591434, 116903, -19862, 3339,
      -508, 55, -8, 1]),
]
# Our own engine-built polynomials (2026-07-03..07-05: Roberts-lift twists, spin covers,
# block-product words) were enqueued through this same producer. They are solution data and are not
# published; a local copy lives in data/processed/literature_own.json (gitignored) and is appended
# if present.
_OWN_LITERATURE = ROOT / "data" / "processed" / "literature_own.json"
if _OWN_LITERATURE.exists():
    _LITERATURE += [(e["tag"], e["desc"], e["coeffs"])
                    for e in json.loads(_OWN_LITERATURE.read_text())]


def produce_literature():
    """Enqueue the verified explicit literature polynomials (_LITERATURE) as ready-to-submit tasks.

    One-shot + idempotent (has_target dedup); not on the refill timer. Provenance = the lit: target
    tag. See docs/auto_log.md (2026-06-30 primitive/2-transitive dive) for verification + citations.
    """
    store.init()
    added = 0
    for tag, _desc, co in _LITERATURE:
        if len(co) != 25 or co[-1] != 1:
            raise ValueError(f"{tag}: expected 25 ascending monic coeffs, got {len(co)}")
        if not store.has_target(tag) and store.enqueue("ready", {"coeffs": co}, target=tag):
            added += 1
    print(f"literature producer: enqueued {added}/{len(_LITERATURE)}; queue={store.counts()}")


def _queue_full() -> bool:
    """True if the queue already holds a deep buffer -- the cursor producers self-pace on this so
    they keep the daemon fed (never idle) without ballooning the queue to millions (they can emit
    ~600k/day, we verify ~tens of k/day). Cap kv-tunable."""
    return store.counts().get("queued", 0) > store.get_kv("queue_cap", 30000)


def _gen12_pats():
    """Diverse C_2-kernel patterns spanning popcount 1..4 -- enough to cover each deg-12 top's
    distinct kernel submodules (~5-9 groups/top; one singleton suffices since all singletons give
    the same full-kernel group). The pattern->group map is alignment-dependent over non-Galois
    bases (test 0038), so we harvest a diverse set and let Magma label."""
    idxs = ([(0,)]
            + list(combinations(range(12), 2))[:14]
            + list(combinations(range(8), 3))[:10]
            + list(combinations(range(6), 4))[:5])
    return [[1 if k in idx else 0 for k in range(12)] for idx in idxs]


def produce_general12(per_run: int = 500, hi: int = 60000, n_primes: int = 2):
    """general_c2 (2x12 C_2-kernel) over NON-Galois deg-12 bases -- a CURSOR over the FULL LMFDB
    mirror (303,209 deg-12 fields total, 2026-07-10 re-audit -- the mirror grew ~4.4x from the stale
    68,777 figure; we walk a per_run slice and advance an offset that AUTO-WRAPS at end-of-supply,
    so the daemon never starves -- we had been re-pulling only the smallest-disc ~480). NB: ~1% of
    the mirror has NULL class_number; int(None) on those pages had silently crashed this producer
    (fixed in lmfdb.fields 2026-07-10) -- the crash fired BEFORE the empty-list wrap, so a stuck
    past-window cursor took gen12 fully offline. Novel-base runway is ~303k; once the
    offset passes it the cursor re-walks and the atlas dry-gate skips already-sampled shapes, so the
    marginal open-1.0 then comes from the split-prime-q dial + new shapes, not virgin bases. Each
    (base, kernel) is a 2-block
    24T group (Magma labels); ~45/50 open targets are 2-block, so this is the main feed. As the
    cursor walks into rarer (larger-disc) fields it covers more of the ~301 deg-12 tops -- incl.
    LARGE / NON-SOLVABLE ones. general_c2 handles any class number (non-principal patterns -> []).
    """
    from igp import lmfdb
    store.init()
    if _queue_full():
        print("general12: queue full (>cap); skipping this tick")
        return
    per_run = max(50, int(per_run * float(store.get_kv("prod_scale", 1.0))))
    n_primes = int(store.get_kv("gen12_nprimes", n_primes))  # split-prime dial: more OPEN r/base
    # Band-bound the cursor to the PRODUCTIVE disc window (2026-07-10): the smallest-disc head is
    # mined out (dry), yield lives in the mid-disc band. gen12_hi=0 => walk the whole mirror.
    lo = int(store.get_kv("gen12_lo", 0))
    hi_off = int(store.get_kv("gen12_hi", 0))
    off = store.get_kv("gen12_offset", 0)
    if hi_off and off >= hi_off:  # past the band -> jump to its start, skipping the dry head
        off = lo
    try:
        bases = lmfdb.fields(12, class_number=None, per_group=2, limit=per_run, offset=off)
        if not bases:  # off the end of the mirror -> restart at the band start (lo; default 0)
            off = lo
            bases = lmfdb.fields(12, class_number=None, per_group=2, limit=per_run, offset=off)
    except Exception as e:
        print(f"LMFDB unavailable ({str(e)[:80]}); skipping general12")
        return
    pats = _gen12_pats()
    try:  # atlas gate (review item G, 2026-07-04): gen12's dry majority was 97% of the claim mix
        from igp import atlas, db
        prog = json.loads(PROG.read_text())
        held = {(int(r["t"]), int(r["r"])) for r in db.load_realized()
                if r.get("label", "").startswith("24T")}
        amap = atlas.classify(prog, held, prefix="gen12:")
    except Exception as e:
        print(f"  atlas unavailable ({str(e)[:60]}); gen12 runs untargeted")
        amap = {}
    explore_budget = 150
    added = used = skipped_dry = 0
    for coeffs, label, disc, _h in bases:
        try:
            qs = gp.split_primes(coeffs, 12, k=n_primes, hi=hi)
        except Exception:
            qs = []
        if not qs:
            continue  # no completely-split prime within hi (|H| too large) -> skip
        used += 1
        for q in qs:
            for w in pats:
                wtag = "".join(map(str, w))
                info = amap.get(f"gen12:{label}:{wtag}")
                if info is not None:
                    builds = sum(info["labels"].values())
                    rate = info["open_pairs"] / builds if builds else 1.0
                    # gen12 is high-variance (one shape -> many groups), so binary open_pairs==0
                    # barely fires; skip well-sampled shapes with negligible value-per-build too
                    if info["open_pairs"] == 0 or (builds >= 20 and rate < 0.02):
                        skipped_dry += 1
                        continue
                if info is None:
                    if explore_budget <= 0:
                        continue
                    explore_budget -= 1
                tgt = f"gen12:{label}:d{disc}:q{q}:{wtag}"
                if store.enqueue("general_c2", {"base": coeffs, "w": w, "q": q}, target=tgt):
                    added += 1
    store.set_kv("gen12_offset", off + per_run)
    print(f"general12 cursor[{off}:{off + per_run}]: {len(bases)} fields, {used} usable, "
          f"enqueued {added} (skipped {skipped_dry} dry); queue={store.counts()}")


def produce_mb2(tops_per_run: int = 8, bases_per_top: int = 3, n_primes: int = 2,
                hi: int = 60000):
    """Targeted-base general_c2 at the unrealized minblk=2 solvable groups (census 2026-07-05).

    1,139 unrealized-open groups (every pair tc=0, ~multi-pair sole claim each) are single-
    quadratic extensions over a deg-12 SOLVABLE top (kernel rank 1-11 = exactly the C2^12
    submodule general_c2's w-pattern selects). gen12 never hit them because it walks LMFDB by
    smallest disc and never TARGETS these tops. This arm walks data/targets/mb2_strike_list.csv
    (value-ranked: supplied tops, open pairs desc), pulls totally-real bases per top (r=24 and
    the twist family), sweeps the gen12 w-patterns + split primes. Tags mb2:12Tj:d..., so the
    atlas learns which (top, w) reaches which 24Tt and the dry-gate prunes.
    """
    import csv as _csv

    from igp import lmfdb
    store.init()
    if _queue_full():
        print("mb2: queue full (>cap); skipping this tick")
        return
    strike = ROOT / "data" / "targets" / "mb2_strike_list.csv"
    if not strike.exists():
        print("mb2: no strike list (scripts/mb2_strike_list.py); skipping")
        return
    rows = [r for r in _csv.DictReader(strike.open()) if int(r.get("tr_bases") or 0) > 0]
    tops: list[str] = []
    for r in rows:  # preserve value ranking; dedupe tops
        if r["top12j"] not in tops:
            tops.append(r["top12j"])
    if not tops:
        print("mb2: strike list has no supplied tops")
        return
    tops_per_run = max(1, int(tops_per_run * float(store.get_kv("prod_scale", 1.0))))
    off = int(store.get_kv("mb2_top_off", 0)) % len(tops)
    batch = [tops[(off + i) % len(tops)] for i in range(min(tops_per_run, len(tops)))]
    pats = _gen12_pats()
    try:
        from igp import atlas, db
        prog = json.loads(PROG.read_text())
        held = {(int(r["t"]), int(r["r"])) for r in db.load_realized()
                if r.get("label", "").startswith("24T")}
        amap = atlas.classify(prog, held, prefix="mb2:")
    except Exception as e:
        print(f"  atlas unavailable ({str(e)[:60]}); mb2 runs untargeted")
        amap = {}
    added = used = skipped_dry = 0
    for j in batch:
        lab = f"12T{j}"
        try:
            bases = lmfdb.fields(12, galois_label=lab, max_r2=0, class_number=None,
                                 limit=bases_per_top)
            if not bases:  # no totally-real supply -> any signature still covers low r
                bases = lmfdb.fields(12, galois_label=lab, class_number=None,
                                     limit=bases_per_top)
        except Exception as e:
            print(f"  LMFDB unavailable for {lab} ({str(e)[:60]}); skipping top")
            continue
        for coeffs, label, disc, _h in bases:
            try:
                qs = gp.split_primes(coeffs, 12, k=n_primes, hi=hi)
            except Exception:
                qs = []
            if not qs:
                continue
            used += 1
            for q in qs:
                for w in pats:
                    wtag = "".join(map(str, w))
                    info = amap.get(f"mb2:{label}:{wtag}")
                    if info is not None:
                        builds = sum(info["labels"].values())
                        if info["open_pairs"] == 0 or (builds >= 20
                                                       and info["open_pairs"] / builds < 0.02):
                            skipped_dry += 1
                            continue
                    tgt = f"mb2:{label}:d{disc}:q{q}:{wtag}"
                    if store.enqueue("general_c2", {"base": coeffs, "w": w, "q": q}, target=tgt):
                        added += 1
    store.set_kv("mb2_top_off", (off + len(batch)) % len(tops))
    print(f"mb2 tops[{off}:+{len(batch)}]/{len(tops)}: {used} bases usable, enqueued {added} "
          f"(skipped {skipped_dry} dry); queue={store.counts()}")


def produce_rfill(groups_per_run: int = 40, primes_per_group: int = 12):
    """Signature-fill: cover OPEN r-values of groups we ALREADY REACH (9,262 pairs, 2026-07-06).

    The split prime dials the real-root count r (test 0036), so a group held at r0 via base B +
    kernel w, at other split primes, lands OTHER r-values -- most of them the
    group's unfilled open signatures. This is the cheapest harvest lever left: no new base, no new
    math, just re-dialing r on our provenance. Cursor over held groups (kv rfill_off); per group,
    re-pull its exact base from LMFDB (galois_label + disc from the provenance tag) and sweep many
    split primes with the held w. Tags rfill:t:... so the atlas learns prime -> r and the
    dry-gate prunes groups whose menu is filled.
    """
    from igp import baseline, db, lmfdb
    store.init()
    if _queue_full():
        print("rfill: queue full; skipping")
        return
    prog = json.loads(PROG.read_text())
    rows = db.load_realized()
    held_pairs = {(r["t"], r["r"]) for r in rows if str(r.get("scoreable")).lower() == "true"}
    # one representative gen12/mb2 provenance per held group (base disc, label, w)
    prov: dict[str, tuple[str, str, list[int]]] = {}
    for r in rows:
        src = r.get("source") or ""
        if r["t"] in prov or not (src.startswith("daemon:gen12:")
                                  or src.startswith("daemon:mb2:")):
            continue
        try:
            parts = src.split(":")
            prov[r["t"]] = (parts[2], parts[3].lstrip("d"), [int(c) for c in parts[5]])
        except (IndexError, ValueError):
            continue
    valid: dict[int, list[int]] = {}
    for a, b in baseline.valid_pairs():
        valid.setdefault(int(a), []).append(int(b))
    # held groups that still have unfilled OPEN r-values
    targets = []
    for t, (label, disc, w) in prov.items():
        openr = [r for r in valid.get(int(t), [])
                 if (prog.get(f"{t},{r}") or {}).get("teamCount", 0) == 0
                 and (t, str(r)) not in held_pairs]
        if openr:
            targets.append((t, label, disc, w, len(openr)))
    targets.sort(key=lambda x: -x[4])  # most open signatures first
    if not targets:
        print("rfill: no held group has unfilled open signatures")
        return
    groups_per_run = max(10, int(groups_per_run * float(store.get_kv("prod_scale", 1.0))))
    off = int(store.get_kv("rfill_off", 0)) % len(targets)
    batch = [targets[(off + i) % len(targets)] for i in range(min(groups_per_run, len(targets)))]
    added = used = 0
    for t, label, disc, w, _n in batch:
        try:
            cand = [c for (c, _g, dd, _h)
                    in lmfdb.fields(12, galois_label=label, class_number=None, limit=12)
                    if str(dd) == disc]
        except Exception:
            continue
        if not cand:
            continue
        base = cand[0]
        qs = _split_primes(base, 12, k=primes_per_group) or []
        if qs:
            used += 1
        for q in qs:
            tgt = f"rfill:{t}:q{q}"
            if store.enqueue("general_c2", {"base": base, "w": w, "q": q}, target=tgt):
                added += 1
    store.set_kv("rfill_off", (off + len(batch)) % len(targets))
    print(f"rfill groups[{off}:+{len(batch)}]/{len(targets)}: {used} bases, enqueued {added} "
          f"(9262-pair inventory); queue={store.counts()}")


def produce_basemin(bases_per_sole: int = 2, primes_per_base: int = 4):
    """Undercut defense along the UNEXPLORED disc axis: rebuild each sole on SMALLER-DISC bases.

    produce_harden exhausted the split-prime dial (every sole already rebuilt at every prime
    below its original -- 2026-07-06, enqueued 0). But our bases were whatever the gen12 cursor
    happened to feed, not the minimal-disc field of that top, and base disc drives cover disc.
    For each gen12-provenance sole, pull the SMALLEST-disc LMFDB fields of the SAME 12Tj label
    strictly below the original base disc and rebuild with the same w-pattern across a split-
    prime sweep (r-menu coverage; some primes re-hit the sole's r at a smaller disc).
    """
    from igp import db, lmfdb
    store.init()
    prog = json.loads(PROG.read_text())
    rows = db.load_realized()
    soles = [r for r in rows if str(r.get("scoreable")).lower() == "true"
             and (prog.get(f"{r['t']},{r['r']}") or {}).get("teamCount", 9) <= 1
             and (r.get("source") or "").startswith("daemon:gen12:")]
    seen_pair: set[tuple[str, str]] = set()
    added = probed = 0
    for r in soles:
        key = (r["t"], r["r"])
        if key in seen_pair:
            continue
        seen_pair.add(key)
        try:
            _d, _tag, label, dstr, _q, wtag = r["source"].split(":")
            old_disc = int(dstr.lstrip("d"))
            w = [int(c) for c in wtag]
        except ValueError:
            continue
        try:
            cands = [(c, g, dd, h) for (c, g, dd, h)
                     in lmfdb.fields(12, galois_label=label, class_number=None, limit=8)
                     if int(dd) < old_disc][:bases_per_sole]
        except Exception:
            continue
        probed += 1
        for coeffs, _g, dd, _h in cands:
            qs = _split_primes(coeffs, 12, k=primes_per_base) or []
            for q in qs:
                tgt = f"basemin:{r['t']}.{r['r']}:{label}:d{dd}:q{q}"
                if store.enqueue("general_c2", {"base": coeffs, "w": w, "q": q}, target=tgt):
                    added += 1
    print(f"basemin: {len(seen_pair)} sole pairs, {probed} with provenance, enqueued {added}; "
          f"queue={store.counts()}")


def produce_size4(per_base: int = 12):
    """Enqueue size-4 (V_4-block, 6x4) biquadratic constructions over Galois degree-6 bases.

    12x2 groups are saturated; 6x4 is the dominant frontier shape and far less commonly built.
    Bases: C_6 = Q(zeta_7) (q=29) and S_3 = splitting field of x^3-2 (split prime found).
    """
    store.init()
    f6 = [int(x) for x in gp.script("print(Vec(polcyclo(7)));").strip("[]").split(",")][::-1]
    s3 = [int(x) for x in gp.script("print(Vec(polredbest(nfsplitting(x^3-2))));")
          .strip("[]").split(",")][::-1]
    def split_prime(cs):
        out = gp.script(f"f=Pol({cs[::-1]},'y);bnf=bnfinit(f);"
                        "for(q=2,4000,if(isprime(q)&&#idealprimedec(bnf,q)==6,print(q);break));")
        return int(out.strip())
    bases = [("C6", f6, 29), ("S3", s3, split_prime(s3))]
    # varied (w1, w2) pairs over 6 coords (independent square-classes)
    pairs = [([1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0]), ([1, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0]),
             ([1, 0, 1, 0, 0, 0], [0, 1, 0, 1, 0, 0]), ([1, 1, 1, 0, 0, 0], [0, 0, 1, 1, 0, 0]),
             ([1, 0, 0, 1, 0, 0], [0, 1, 1, 0, 0, 0]), ([1, 1, 0, 1, 0, 0], [0, 0, 1, 1, 1, 0])]
    added = 0
    for name, base, q in bases:
        for w1, w2 in pairs[:per_base]:
            tgt = f"size4:{name}:{''.join(map(str, w1))}/{''.join(map(str, w2))}"
            if store.enqueue("biquadratic", {"base": base, "w1": w1, "w2": w2, "q": q}, target=tgt):
                added += 1
    print(f"size-4 producer: enqueued {added}; queue={store.counts()}")


def _diverse_deg6_bases(max_order: int = 48):
    """Locally generate degree-6 bases with DIVERSE tops (one small-disc field per Galois
    order <= max_order, h=1, completely-split prime). polgalois (deg<=11) labels them — no
    external DB needed. Returns [(coeffs, order, split_prime)]."""
    # gp function with early returns (avoids the multi-statement comma-if parse bug);
    # one line "order|splitprime|coeffs" per matching base.
    out = gp.script(
        "chk(a,b,c)=my(f=x^6+a*x^3+b*x+c,o,bnf,sq);"
        "if(!polisirreducible(f),return(0));o=polgalois(f)[1];"
        f"if(o>{max_order},return(0));bnf=bnfinit(f);if(bnf.no!=1,return(0));"
        "sq=0;for(q=2,2000,if(isprime(q)&&#idealprimedec(bnf,q)==6,sq=q;break));"
        "if(sq==0,return(0));[o,sq,Vec(polredbest(f))];\n"
        "for(a=-3,3,for(b=-3,3,for(c=-3,3,r=chk(a,b,c);"
        "if(r!=0,print(r[1],\"|\",r[2],\"|\",r[3])))));",
        timeout=500,
    )
    by_order = {}
    for ln in out.splitlines():
        if "|" not in ln:
            continue
        o_s, sq_s, cs_s = ln.split("|")
        o = int(o_s)
        if o in by_order:
            continue  # keep first (smallest |coeffs|) per order
        coeffs = [int(x) for x in cs_s.strip("[]").split(",")][::-1]
        by_order[o] = (coeffs, o, int(sq_s))
    return list(by_order.values())


def produce_size4_general(per_base: int = 8):
    """Enqueue general (non-Galois) size-4 (6x4) constructions over diverse degree-6 bases.

    The diversity 12x2 lacks: each degree-6 base's top (6Tj, various orders) gives a distinct
    6x4 family. Labels via Magma (daemon). This is the local 'base library' (LMFDB is captcha
    -walled; polgalois generates labeled bases directly)."""
    store.init()
    bases = _diverse_deg6_bases()
    pairs = _BIQ_PAIRS
    added = 0
    for coeffs, order, _q in bases:
        qs = _split_primes(coeffs, 6, k=3) or [_q]   # sweep primes -> sweep r (test 0036)
        for q in qs:
            for w1, w2 in pairs[:per_base]:
                tgt = (f"g6x4:o{order}:d{coeffs[0]}:q{q}:"
                       f"{''.join(map(str, w1))}/{''.join(map(str, w2))}")
                if store.enqueue("general_biquadratic",
                                 {"base": coeffs, "w1": w1, "w2": w2, "q": q}, target=tgt):
                    added += 1
    orders = sorted({o for _, o, _ in bases})
    print(f"size-4-general: {len(bases)} diverse deg-6 bases (orders {orders}), "
          f"enqueued {added}; queue={store.counts()}")


# Independent (w1,w2) square-class pairs over 6 coords. Different pairs for the SAME group give
# DIFFERENT field discs, so a wider sweep => more disc samples per (t,r) => the builder keeps a
# smaller min (alignment-free disc-min: Magma labels, build_submission picks min). Test 0038.
_BIQ_PAIRS = [
    ([1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0]), ([1, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0]),
    ([1, 0, 1, 0, 0, 0], [0, 1, 0, 1, 0, 0]), ([1, 1, 1, 0, 0, 0], [0, 0, 1, 1, 0, 0]),
    ([1, 0, 0, 1, 0, 0], [0, 1, 1, 0, 0, 0]), ([1, 1, 0, 1, 0, 0], [0, 0, 1, 1, 1, 0]),
    ([1, 0, 0, 0, 1, 0], [0, 1, 0, 0, 0, 1]), ([1, 1, 1, 1, 0, 0], [0, 0, 1, 1, 1, 1]),
]


def _produce_shortblock(shape: str, degree: int, kind: str, per_run: int, n_primes: int,
                        hi: int, force: bool):
    """Shared cursor producer for the NON-ABELIAN short-block shapes (test 0041 GAP screen):
    the open minblk in {3,4} pool needs S3-cubic / S4-quartic kernels almost exclusively —
    zero V4/C4/D4 — so these walk the full LMFDB deg-8/deg-6 mirror with the new radical/
    generic kernels. Self-paces on queue depth unless force (first wave)."""
    from igp import lmfdb
    store.init()
    if not force and _queue_full():
        print(f"{shape}: queue full (>cap); skipping this tick")
        return
    per_run = max(20, int(per_run * float(store.get_kv("prod_scale", 1.0))))
    key = f"{shape}_offset"
    off = store.get_kv(key, 0)
    try:
        bases = lmfdb.fields(degree, class_number=None, per_group=3, limit=per_run, offset=off)
        if not bases:  # walked off the end -> restart the cursor
            off, bases = 0, lmfdb.fields(degree, class_number=None, per_group=3, limit=per_run)
    except Exception as e:
        print(f"LMFDB unavailable ({str(e)[:80]}); skipping {shape}")
        return
    pats = [[1] + [0] * (degree - 1), [0, 1, 1] + [0] * (degree - 3),
            [1, 0, 1] + [0] * (degree - 3)]
    try:
        from igp import atlas, db
        prog = json.loads(PROG.read_text())
        held = {(int(r["t"]), int(r["r"])) for r in db.load_realized()
                if r.get("label", "").startswith("24T")}
        amap = atlas.classify(prog, held, prefix=shape + ":")
    except Exception:
        amap = {}
    explore_budget = 60
    added = used = skipped_dry = 0
    for coeffs, label, disc, _h in bases:
        try:
            qs = gp.split_primes(coeffs, degree, k=n_primes, hi=hi)
        except Exception:
            qs = []
        if not qs:
            continue
        used += 1
        for q in qs:
            for i, w in enumerate(pats):
                info = amap.get(f"{shape}:{label}:p{i}")
                if info is not None and info["open_pairs"] == 0:
                    skipped_dry += 1
                    continue
                if info is None:
                    if explore_budget <= 0:
                        continue
                    explore_budget -= 1
                tgt = f"{shape}:{label}:d{disc}:q{q}:p{i}"
                if store.enqueue(kind, {"base": coeffs, "w": w, "q": q}, target=tgt):
                    added += 1
    store.set_kv(key, off + len(bases))
    print(f"{shape}: {used}/{len(bases)} bases usable (cursor {off}->{off + len(bases)}), "
          f"enqueued {added} (skipped {skipped_dry} dry); queue={store.counts()}")


_COMPOSE_OUTERS = {
    # ascending coeffs per outer degree a (blocks = a, block size = 24/a). Varying the constant
    # sweeps both the field disc and the real-root count of the composition (an r dial).
    2: [[-c, 0, 1] for c in (2, 3, 5, 6, 7, 10, -2, -3, -5)] + [[-c, -1, 1] for c in (1, 3, 5)],
    3: [[-c, 0, 0, 1] for c in (2, 3, 5, 6, 7, -2, -3)] + [[-c, -1, 0, 1] for c in (1, 3)],
    4: [[-c, 0, 0, 0, 1] for c in (2, 3, 5, 6, -2, -3)] + [[-c, -1, 0, 0, 1] for c in (1, 3)],
}


def produce_compose(per_run: int = 150, force: bool = False):
    """f(g(x)) composition producer — the wreath shapes 2x12 / 3x8 / 4x6 (research-log G2 find,
    2026-06-24, validated then never built). Gal(h) <= Gal(g) wr Gal(f): the only cheap route to
    the minblk in {6,8,12} strata (~965 open/steal sigs), incl. the near-S24 titans = quadratic
    outer over a generic S12/A12 inner (S12 wr C2 order 2.29e17 = 24T24996/97). Cursored over
    the LMFDB deg-12/8/6 mirrors; first wave seeds the titan shot with explicit S12/A12 inners."""
    from igp import lmfdb
    store.init()
    if not force and _queue_full():
        print("compose: queue full (>cap); skipping this tick")
        return
    # Atlas targeting (2026-07-04): skip (inner-label, outer) shapes whose observed groups carry
    # zero open/steal value; explore unseen shapes at a capped rate; concentrate on open-bearing.
    try:
        from igp import atlas, db
        prog = json.loads(PROG.read_text())
        held = {(int(r["t"]), int(r["r"])) for r in db.load_realized()
                if r.get("label", "").startswith("24T")}
        amap = atlas.classify(prog, held, prefix="compose:")
    except Exception as e:
        print(f"  atlas unavailable ({str(e)[:60]}); compose runs untargeted")
        amap = {}
    explore_budget = 40
    added = skipped_dry = 0
    for a, inner_deg in ((2, 12), (3, 8), (4, 6)):
        key = f"compose{a}_offset"
        off = store.get_kv(key, 0)
        try:
            inners = lmfdb.fields(inner_deg, class_number=None, per_group=2,
                                  limit=per_run, offset=off)
            if not inners:
                off, inners = 0, lmfdb.fields(inner_deg, class_number=None, per_group=2,
                                              limit=per_run)
            if a == 2 and off == 0:  # titan shot: generic S12/A12 inners, quadratic outer
                for lab in ("12T301", "12T300"):
                    inners += lmfdb.fields(12, galois_label=lab, class_number=None, limit=6)
        except Exception as e:
            print(f"LMFDB unavailable ({str(e)[:80]}); skipping compose{a}")
            continue
        for coeffs, label, disc, _h in inners:
            for j, outer in enumerate(_COMPOSE_OUTERS[a]):
                info = amap.get(f"compose:{a}x{inner_deg}:{label}:o{j}")
                if info is not None and info["open_pairs"] == 0:
                    skipped_dry += 1
                    continue          # known shape, saturated groups -> don't rebuild it
                if info is None:
                    if explore_budget <= 0:
                        continue      # unseen shape: explore, but capped per tick
                    explore_budget -= 1
                tgt = f"compose:{a}x{inner_deg}:{label}:d{disc}:o{j}"
                if store.enqueue("compose", {"inner": coeffs, "outer": outer}, target=tgt):
                    added += 1
        store.set_kv(key, off + per_run)
    print(f"compose: enqueued {added} (skipped {skipped_dry} dry shapes); queue={store.counts()}")



_LIFT_SELS = [[1], [2], [3], [4], [5], [1, 2], [1, 3], [2, 3]]
# top-value 12T labels first (lift-map dive: upper-bound pts | supply)
_LIFT_HOT = ["12T274", "12T292", "12T294", "12T261", "12T264", "12T188", "12T105"]


def produce_lift(per_run: int = 120, force: bool = False):
    """Orbit-sign lift producer (task #17; 2026-07-02 dive arc). K24 = K12(sqrt delta) over LMFDB
    deg-12 bases: closure-preserving quadratic lifts reaching 491 24Tt (~384 unheld) -- a contested
    breadth/points play (~30-80 pts realistic), zero open 1.0s (verified census). First wave seeds
    the dive's top-value labels; then a cursor walks all deg-12 labels. v2 refinement (queued): the
    Hecke-parity conductor predictor for rank-then-build."""
    from igp import lmfdb
    store.init()
    if not force and _queue_full():
        print("lift: queue full (>cap); skipping this tick")
        return
    per_run = max(20, int(per_run * float(store.get_kv("prod_scale", 1.0))))
    added = 0
    off = store.get_kv("lift_offset", 0)
    try:
        bases = []
        if force and off == 0:
            for lab in _LIFT_HOT:
                bases += lmfdb.fields(12, galois_label=lab, class_number=None, limit=4)
        bases += lmfdb.fields(12, class_number=None, per_group=2, limit=per_run, offset=off)
    except Exception as e:
        print(f"LMFDB unavailable ({str(e)[:80]}); skipping lift")
        return
    try:
        from igp import atlas, db
        prog = json.loads(PROG.read_text())
        held = {(int(r["t"]), int(r["r"])) for r in db.load_realized()
                if r.get("label", "").startswith("24T")}
        amap = atlas.classify(prog, held, prefix="lift:")
    except Exception:
        amap = {}
    explore_budget = 60
    import sqlite3 as _sq
    bad_sels: dict = {}
    with _sq.connect(store.DB) as _c:   # sels that repeatedly build empty for a label: the factor
        q = ("SELECT target, COUNT(*) FROM queue WHERE status='failed' AND detail='empty' "
             "AND target LIKE 'lift:%' GROUP BY target")   # structure is per-label, so learnable
        for tgt, n in _c.execute(q):
            if n >= 2:
                parts = tgt.split(":")
                bad_sels.setdefault(parts[1], set()).add(parts[-1])
    for coeffs, label, disc, _h in bases:
        for sel in _LIFT_SELS:
            stag = f"s{''.join(map(str, sel))}"
            if stag in bad_sels.get(label, ()):
                continue
            skey = f"lift:{label}:{stag}"
            info = amap.get(skey)
            if info is not None and info["open_pairs"] == 0:
                continue
            if info is None:
                if explore_budget <= 0:
                    continue
                explore_budget -= 1
            tgt = f"lift:{label}:d{disc}:s{''.join(map(str, sel))}"
            if store.enqueue("lift", {"base": coeffs, "sel": sel}, target=tgt):
                added += 1
    store.set_kv("lift_offset", off + per_run)
    print(f"lift: enqueued {added}; queue={store.counts()}")





def produce_tr6(per_run: int = 60, force: bool = False):
    """Totally-real sextic base factory via PARI nflist (task #18 v1, 2026-07-05). The S4-quartic
    kernel screen's TOP-demand stratum sits over 6T3=D6 tops (75 open groups), and r=24-capable
    candidates need totally-real bases -- which LMFDB stocks thinly (2-11/label) but nflist
    GENERATES on the fly with signature control. Walks a disc-window cursor; enqueues
    general_quartic tasks tagged g6x4s4:* so the atlas/bandit/quota treat them as one family."""
    from igp import atlas, db
    store.init()
    if not force and _queue_full():
        print("tr6: queue full (>cap); skipping this tick")
        return
    lo = int(store.get_kv("tr6_lo", 1))
    hi = lo * 8
    try:
        prog = json.loads(PROG.read_text())
        held = {(int(r["t"]), int(r["r"])) for r in db.load_realized()
                if r.get("label", "").startswith("24T")}
        amap = atlas.classify(prog, held, prefix="g6x4s4:")
    except Exception:
        amap = {}
    pats = [[1, 0, 0, 0, 0, 0], [0, 1, 1, 0, 0, 0], [1, 0, 1, 0, 0, 0]]
    added = 0
    for gname, label in (("D6", "6T3"), ("C6", "6T1")):
        try:
            out = gp.script(
                f'v=nflist("{gname}",[{lo},{hi}],0);'
                f'for(i=1,min(#v,{per_run}),print(Vec(polredbest(v[i])),"|",poldisc(v[i])))',
                timeout=300)
        except Exception as e:
            print(f"  nflist {gname} failed: {str(e)[:60]}")
            continue
        for ln in out.splitlines():
            if "|" not in ln:
                continue
            vec, disc = ln.split("|")
            coeffs = [int(x) for x in vec.strip("[]").split(",")][::-1]
            try:
                qs = gp.split_primes(coeffs, 6, k=2, hi=20000)
            except Exception:
                continue
            for q in qs:
                for i, w in enumerate(pats):
                    info = amap.get(f"g6x4s4:{label}:p{i}")
                    if info is not None and info["open_pairs"] == 0:
                        continue
                    tgt = f"g6x4s4:{label}:d{disc.strip()}:q{q}:p{i}"
                    if store.enqueue("general_quartic", {"base": coeffs, "w": w, "q": q},
                                     target=tgt):
                        added += 1
    store.set_kv("tr6_lo", hi)
    print(f"tr6: window [{lo},{hi}], enqueued {added}; queue={store.counts()}")


def produce_harden(per_pair_primes: int = 8, force: bool = False):
    """Disc-harden our own sole 1.0s (2026-07-05 defensibility audit): 99% were built with lazy
    split primes (q>50), leaving ~98 bits of disc an attacker can undercut. Rebuild each sole's
    construction with the SMALLEST split primes so our min-disc becomes the floor. Caveat: the
    prime is also the r-dial (test 0036), so we rebuild at the 3 smallest primes per sole to
    re-hit the exact (t,r); Magma arbitrates. v1 covers payload-recoverable rows (general_c2 &
    general_biquadratic); ready/manual soles need the atlas-shape route (v2)."""
    import sqlite3 as _sq

    from igp import baseline, db
    store.init()
    if not force and _queue_full():
        print("harden: queue full (>cap); skipping this tick")
        return
    prog = json.loads(PROG.read_text())
    sole_lines: dict = {}
    for r in db.load_realized():
        if (str(r.get("scoreable")).lower() == "true" and r.get("label", "").startswith("24T")
                and not baseline.is_baseline(r["t"], r["r"])
                and (prog.get(r["t"] + "," + r["r"]) or {}).get("teamCount", 9) <= 1):
            sole_lines[r["coeffs"]] = (r["t"], r["r"])
    recov: dict = {}
    with _sq.connect(store.DB) as c:
        c.row_factory = _sq.Row
        q = ("SELECT kind, payload, line FROM queue WHERE status='verified' AND line IS NOT NULL "
             "AND kind IN ('general_c2','general_biquadratic','galois_c2')")
        for row in c.execute(q):
            if row["line"] in sole_lines:
                recov[row["line"]] = (row["kind"], json.loads(row["payload"]))
    added = probed = 0
    for line, (kind, payload) in recov.items():
        t, rr = sole_lines[line]
        base = payload.get("base")
        if not base:
            continue
        deg = len(base) - 1
        old_q = int(payload.get("q") or 10 ** 9)
        try:
            qs = [q for q in gp.split_primes(base, deg, k=per_pair_primes, hi=20000) if q < old_q]
        except Exception:
            continue
        probed += 1
        for q in qs:
            np = dict(payload)
            np["q"] = q
            tgt = f"harden:{t}.{rr}:d{deg}:q{q}"
            if store.enqueue(kind, np, target=tgt):
                added += 1
    print(f"harden: {len(sole_lines)} soles, {len(recov)} recoverable, {probed} probed, "
          f"enqueued {added}; queue={store.counts()}")


def produce_selfcomp(max_groups: int = 60, per_shape: int = 5, force: bool = False):
    """Self-competition disc-min (2026-07-04): re-attack OUR OWN weak results. Finds held
    scoreable pairs where our disc is far off the leaderboard min (ratio < 0.85), ranks groups by
    recoverable value 2^(1-k)*(1-ratio), asks the atlas which shape families hit each group, and
    enqueues fresh-base candidates of those shapes (deeper LMFDB pages each run). The builder
    keeps the min disc per pair, so every better draw directly recovers points."""
    import math

    from igp import atlas, db, lmfdb
    store.init()
    if not force and _queue_full():
        print("selfcomp: queue full (>cap); skipping this tick")
        return
    prog = json.loads(PROG.read_text())
    best: dict = {}
    for r in db.load_realized():
        fd = r.get("field_disc") or ""
        if str(r.get("scoreable")).lower() == "true" and fd.lstrip("-").isdigit():
            k = (int(r["t"]), int(r["r"]))
            d = abs(int(fd))
            best[k] = min(best.get(k, d), d)
    recover: dict = {}
    for (t, rr), d in best.items():
        e = prog.get(f"{t},{rr}") or {}
        md = e.get("minDisc")
        k = max(e.get("teamCount", 1), 1)
        if md and str(md).isdigit() and d > 1 and int(md) > 1:
            ratio = math.log(int(md)) / math.log(d)
            if ratio < 0.85:
                recover[t] = recover.get(t, 0.0) + (2 ** (1 - k)) * (1 - ratio)
    top = set(sorted(recover, key=lambda t: -recover[t])[:max_groups])
    if not top:
        print("selfcomp: no weak-disc groups above threshold")
        return
    fams: dict = {}
    for key, labs in atlas.observed().items():
        fam = key.split(":")[0]
        if fam not in ("compose", "lift", "g8x3s3", "g6x4s4"):
            continue
        for t in labs:
            if t in top:
                fams.setdefault(t, set()).add(key)
    off = store.get_kv("selfc_offset", 3)
    pats = {8: [[1] + [0] * 7, [0, 1, 1] + [0] * 5, [1, 0, 1] + [0] * 5],
            6: [[1] + [0] * 5, [0, 1, 1] + [0] * 3, [1, 0, 1] + [0] * 3]}
    added = 0
    for t in top:
        for key in sorted(fams.get(t, []))[:3]:
            parts = key.split(":")
            fam = parts[0]
            try:
                if fam == "compose" and len(parts) >= 4:
                    shape, lbl, oj = parts[1], parts[2], int(parts[3][1:])
                    a, b = (int(x) for x in shape.split("x"))
                    for coeffs, label, disc, _h in lmfdb.fields(
                            b, galois_label=lbl, class_number=None, limit=per_shape, offset=off):
                        tgt = f"selfc:{t}:comp{shape}:{label}:d{disc}:o{oj}"
                        outer = _COMPOSE_OUTERS[a][oj % len(_COMPOSE_OUTERS[a])]
                        if store.enqueue("compose", {"inner": coeffs, "outer": outer}, target=tgt):
                            added += 1
                elif fam == "lift":
                    lbl = parts[1]
                    for coeffs, label, disc, _h in lmfdb.fields(
                            12, galois_label=lbl, class_number=None, limit=per_shape, offset=off):
                        for sel in _LIFT_SELS[:4]:
                            stag = "s" + "".join(map(str, sel))
                            tgt = f"selfc:{t}:lift:{label}:d{disc}:{stag}"
                            if store.enqueue("lift", {"base": coeffs, "sel": sel}, target=tgt):
                                added += 1
                elif fam in ("g8x3s3", "g6x4s4"):
                    lbl = parts[1]
                    deg = 8 if fam == "g8x3s3" else 6
                    kind = "general_cubic" if fam == "g8x3s3" else "general_quartic"
                    for coeffs, label, disc, _h in lmfdb.fields(
                            deg, galois_label=lbl, class_number=None, limit=per_shape, offset=off):
                        qs = gp.split_primes(coeffs, deg, k=1, hi=60000)
                        if not qs:
                            continue
                        for i, w in enumerate(pats[deg]):
                            tgt = f"selfc:{t}:{fam}:{label}:d{disc}:q{qs[0]}:p{i}"
                            if store.enqueue(kind, {"base": coeffs, "w": w, "q": qs[0]},
                                             target=tgt):
                                added += 1
            except Exception:
                continue
    store.set_kv("selfc_offset", off + per_shape)
    print(f"selfcomp: {len(top)} weak-disc groups (recoverable ~"
          f"{sum(recover[t] for t in top):.1f} pts), enqueued {added}; queue={store.counts()}")


def produce_g8x3(per_run: int = 250, n_primes: int = 3, force: bool = False):
    """8x3 S3-cubic kernels (general_cubic) over the deg-8 LMFDB mirror -> the 606 open
    minblk=3 groups (2,728 open sigs) the cyclic zeta-Kummer 8x3 cannot reach (test 0041)."""
    _produce_shortblock("g8x3s3", 8, "general_cubic", per_run, n_primes, 60000, force)


def produce_g6x4(per_run: int = 250, n_primes: int = 3, force: bool = False):
    """6x4 S4-quartic kernels (general_quartic) over the deg-6 LMFDB mirror -> the 541 open
    minblk=4 groups (3,706 open sigs); the V4/biquadratic kernel hits NONE of them (test 0041)."""
    _produce_shortblock("g6x4s4", 6, "general_quartic", per_run, n_primes, 60000, force)


def produce_lmfdb(degree: int = 6, per_group: int = 12, hi: int = 20000, n_primes: int = 3):
    """6x4 biquadratic over the SMALLEST-disc LMFDB degree-6 bases. NOT cursored: degree 6 has only
    16 transitive groups (6T1..16), so 6x4 = (6Tj) x V_4-kernel is saturated at ~16 tops -- walking
    into larger-disc fields adds no new groups and only worsens disc. Instead pull the smallest-disc
    fields (best for disc-min on the saturated tops) with diversity across tops; sweep several split
    primes (r, test 0036) and (w1,w2) patterns (disc-min, test 0038). Magma labels.
    """
    from igp import lmfdb
    store.init()
    try:
        bases = lmfdb.fields(degree, class_number=1, per_group=per_group, limit=800)
    except Exception as e:
        print(f"LMFDB unavailable ({str(e)[:80]}); skipping")
        return
    pairs = _BIQ_PAIRS
    added = used = 0
    for coeffs, label, disc, _h in bases:
        qs = _split_primes(coeffs, degree, k=n_primes, hi=hi)
        if not qs:
            continue  # no small completely-split prime (|H| too big)
        used += 1
        for q in qs:
            for w1, w2 in pairs:
                tgt = (f"lmfdb6x4:{label}:d{disc}:q{q}:"
                       f"{''.join(map(str, w1))}/{''.join(map(str, w2))}")
                if store.enqueue("general_biquadratic",
                                 {"base": coeffs, "w1": w1, "w2": w2, "q": q}, target=tgt):
                    added += 1
    print(f"LMFDB 6x4: {len(bases)} smallest-disc deg-6 fields, {used} usable, enqueued {added}; "
          f"queue={store.counts()}")


def produce_discmin(per_top: int = 60):
    """#4: re-realize the exact-labeling families over LMFDB MINIMAL-disc bases.

    For each order-12 Galois top (12T1=C_12, 12T2=C_2xC_6, 12T3=D_6, 12T4=A_4), pull LMFDB's
    smallest-disc field of that label, route every cyclic kernel over it (galois_c2), and
    enqueue. The engine keeps the min disc per (t,r), so these minimal-base realizations
    improve our beatable signatures (PoC: 24T2595 37->34 digits). Smaller prime/pattern is the
    further GA knob.
    """
    from itertools import combinations

    from igp import lmfdb
    store.init()
    added = 0
    for top in ("12T1", "12T2", "12T3", "12T4"):
        try:
            fs = lmfdb.fields(12, galois_label=top, class_number=1, limit=1)
        except Exception as e:
            print(f"  LMFDB unavailable ({str(e)[:60]}); skipping disc-min")
            return
        if not fs:
            continue
        base = fs[0][0]
        q = gp.script(f"f=Pol({base[::-1]},'y);bnf=bnfinit(f);"
                      f"for(q=2,3000,if(isprime(q)&&#idealprimedec(bnf,q)==12,print(q);break));").strip()
        if not q:
            continue
        perms = gp.galois_action_perms(base)
        reps = {}
        for pc in range(1, 4):
            for idx in combinations(range(12), pc):
                w = [1 if k in idx else 0 for k in range(12)]
                reps.setdefault(ks.module_basis(sum(1 << k for k in idx), perms), w)
        ws = list(reps.values())[:per_top]
        labels = gap.kernel_labels_for_top(perms, ws)
        for w in ws:
            lab = labels.get(tuple(w))
            if not lab:
                continue
            tgt = f"discmin:{top}:{lab}"
            if store.enqueue("galois_c2", {"base": base, "w": w, "q": int(q)}, target=tgt):
                added += 1
        print(f"  {top}: LMFDB base + routed kernels enqueued")
    print(f"disc-min producer: enqueued {added}; queue={store.counts()}")


def produce_discmin2(alphas=("-1", "2", "-2", "3", "-3", "5", "-5", "6", "-6", "7", "-7",
                             "10", "-10", "11", "-11", "13", "-13", "14", "-14", "15", "-15",
                             "10", "-10", "13", "-13", "15", "-15")):
    """Disc-min via MINIMAL-RAMIFICATION radicals: F(sqrt(alpha)) for small squarefree alpha over
    LMFDB minimal-disc degree-12 bases. A small fixed radical ramifies far less than a split-prime
    radical, so the field disc is smaller -- aimed at the behind-on-disc C_2-kernel sigs (test 0029
    showed even our `discmin` family is being beaten). `ready` polys; the engine keeps the min disc
    per (t,r), so any that match a held sig with smaller disc upgrades our score."""
    from igp import lmfdb
    store.init()
    added = 0
    for top in ("12T1", "12T2", "12T3", "12T4"):
        try:
            fs = lmfdb.fields(12, galois_label=top, class_number=1, limit=1)
        except Exception as e:
            print(f"  LMFDB unavailable ({str(e)[:50]}); skipping disc-min2")
            return
        if not fs:
            continue
        base = fs[0][0]
        for alpha in alphas:
            tgt = f"discmin2:{top}:a{alpha}"
            if store.has_target(tgt):
                continue
            try:
                co = gp.quadratic_ext(base, alpha)
            except Exception:
                continue
            if co and len(co) == 25 and co[-1] == 1:
                store.enqueue("ready", {"coeffs": co}, target=tgt)
                added += 1
    print(f"disc-min2 (small-radical) producer: enqueued {added}; queue={store.counts()}")


def produce_sigfill(n_bases: int = 16, per_base: int = 24):
    """Signature fill: realize varied real-root counts `r` via totally-real deg-12 bases.

    Most of our towers use small-disc (complex) bases, so a group lands at a single `r`. A rational
    radical gives r in {0,24}; a radical that's an EXPRESSION in the base generator has mixed
    embedding signs -> INTERMEDIATE r. So F(sqrt(alpha)) over totally-real bases (r2=0), swept over
    alpha expressions, fills the under-covered intermediate-r region (test 0029: 241/319 groups have
    only one observed r). `ready` degree-24 polys; Magma labels (t, r). See review / test 0031.
    """
    from igp import lmfdb
    store.init()
    if _queue_full():
        return
    # alpha=const>0 -> r=24; const<0 -> r=0; y-expressions -> intermediate r (embedding-sign mix).
    alphas = ["2", "-1", "3", "-2", "y", "y-1", "y+1", "2-y", "3-y", "y-2",
              "y^2-2", "y^2-y-1", "y^3-y-1", "y^2-3", "y^2+y-1", "y^3-2*y-1"]
    # CURSOR the full totally-real pool (was a FIXED 16 h=1 bases -> swept once -> silent; the open
    # sig-fill pairs are 65% high-r, 2026-07-10, which needs a much wider totally-real base supply).
    # per_group=None, NOT per_group=1 (audit 2026-07-13): per_group=1 collapses the pool to one
    # representative field per 12Tj (<=227), which the cursor swept long ago -- every offset then
    # returned 100%-already-enqueued bases and the producer sat at added=0 for 29h. The real supply
    # is 5472 totally-real deg-12 fields; distinct discs give distinct target keys.
    n_bases = max(8, int(n_bases * float(store.get_kv("prod_scale", 1.0))))
    off = int(store.get_kv("sigfill_offset", 0))
    try:
        bases = lmfdb.fields(12, class_number=None, max_r2=0, per_group=None,
                             limit=n_bases, offset=off)
        if not bases:
            off = 0
            bases = lmfdb.fields(12, class_number=None, max_r2=0, per_group=None, limit=n_bases)
    except Exception as e:
        print(f"LMFDB unavailable ({str(e)[:60]}); skipping sigfill")
        return
    added = 0
    for coeffs, label, disc, _h in bases:
        for alpha in alphas[:per_base]:
            tgt = f"sigfill:{label}:d{disc}:{alpha}"
            if store.has_target(tgt):
                continue
            try:
                co = gp.quadratic_ext(coeffs, alpha)
            except Exception:
                continue
            if co and len(co) == 25 and co[-1] == 1:
                store.enqueue("ready", {"coeffs": co}, target=tgt)
                added += 1
    store.set_kv("sigfill_offset", off + n_bases)
    print(f"sigfill cursor[{off}:{off + n_bases}]: {len(bases)} totally-real bases x alpha sweep, "
          f"enqueued {added}; queue={store.counts()}")


def _bits(w) -> int:
    return sum(1 << k for k, x in enumerate(w) if x)


def _split_primes(coeffs, ndeg: int, k: int = 1, hi: int = 20000) -> list[int]:
    """First ``k`` primes that split completely in the deg-``ndeg`` field (idealprimedec==ndeg)."""
    out = gp.script(
        f"f=Pol({coeffs[::-1]},'y);bnf=bnfinit(f);n=0;"
        f"for(q=2,{hi},if(isprime(q)&&#idealprimedec(bnf,q)=={ndeg},print(q);n++;"
        f"if(n>={k},break)));",
        timeout=150)
    return [int(x) for x in out.split()]


def _r_if_valid(K) -> str | None:
    """Real-root count (as a string) of a real degree-24 monic K, else None (degenerate/short)."""
    return str(gp.real_roots(K)) if (K and len(K) == 25 and K[-1] == 1) else None


# Sweep sizes. A given (base, kernel) fixes the GROUP t but the split prime sets alpha's embedding
# signs -> the real-root count r (verified: one 12T3 kernel reaches r in {8,12,16} across primes).
# So sweeping primes harvests multiple OPEN (t,r) per reachable group; `covered` stops once a t's
# open r are all claimed, bounding wasted construction. More bases add further r/disc diversity.
_TSIG_NBASES = 3
_TSIG_NPRIMES = 5


def _tsig_c2(open_by_t, per_base, enq, n_bases: int = _TSIG_NBASES, n_primes: int = _TSIG_NPRIMES):
    """C_2-kernel (2x12): single quadratic generator over deg-12 Galois totally-real bases, primes
    swept per kernel to span the open real-root counts of each reachable group."""
    from igp import lmfdb
    added = scanned = 0
    covered: dict = {}   # t -> {r already enqueued this run} (dedup across bases/primes)
    for top in ("12T1", "12T2", "12T3", "12T4", "12T5"):  # the order-12 (Galois) tops
        for coeffs, _lab, _disc, _h in lmfdb.fields(12, galois_label=top, class_number=1,
                                                     max_r2=0, limit=n_bases):
            qs = _split_primes(coeffs, 12, k=n_primes)
            if not qs:
                continue
            perms = gp.galois_action_perms(coeffs)
            reps: dict = {}
            for pc in range(1, 4):
                for idx in combinations(range(12), pc):
                    w = [1 if k in idx else 0 for k in range(12)]
                    reps.setdefault(ks.module_basis(_bits(w), perms), w)
            ws = list(reps.values())[:per_base]
            labels = gap.kernel_labels_for_top(perms, ws)
            for w in ws:
                lab = labels.get(tuple(w))
                if not lab or lab[3:] not in open_by_t:
                    continue
                t = lab[3:]
                need = set(open_by_t[t]) - covered.get(t, set())  # open r not yet claimed for t
                for q in qs:
                    if not need:
                        break
                    scanned += 1
                    try:
                        K = gp.galois_c2(coeffs, w, q)
                    except Exception:
                        continue
                    r = _r_if_valid(K)
                    if r in need:               # obtained this open r (new or already queued)
                        if enq(f"tsig:c2:{lab}:r{r}", K):
                            added += 1
                        need.discard(r)         # discard regardless, so the early-break can fire
                        covered.setdefault(t, set()).add(r)
    return added, scanned


def _tsig_c2multi(open_by_t, per_base, enq, n_bases: int = 2, n_pairs: int = 3):
    """Multi-generator C_2-kernel (2x12): NON-cyclic kernels over deg-12 Galois totally-real bases,
    reaching groups whose kernel needs >=2 generators (invisible to the single-generator c2 family).
    Sweeps several prime PAIRS per kernel for open-r diversity."""
    from igp import lmfdb
    added = scanned = 0
    covered: dict = {}
    for top in ("12T1", "12T2", "12T3", "12T4", "12T5"):
        for coeffs, _lab, _disc, _h in lmfdb.fields(12, galois_label=top, class_number=1,
                                                     max_r2=0, limit=n_bases):
            qs = _split_primes(coeffs, 12, k=2 * n_pairs)
            if len(qs) < 2:
                continue
            qpairs = [(qs[2 * i], qs[2 * i + 1]) for i in range(len(qs) // 2)]
            perms = gp.galois_action_perms(coeffs)
            singles = [[1 if k in idx else 0 for k in range(12)]
                       for pc in (1, 2) for idx in combinations(range(12), pc)]
            seen: set = set()
            kernels = []
            for w1, w2 in combinations(singles, 2):
                span = ks.rref(ks.orbit(_bits(w1), perms) | ks.orbit(_bits(w2), perms))
                if span in seen or ks.module_basis(_bits(w1), perms) == span \
                        or ks.module_basis(_bits(w2), perms) == span:
                    continue  # seen, or cyclic (c2's job) — keep only genuinely 2-generator kernels
                seen.add(span)
                kernels.append([w1, w2])
                if len(kernels) >= per_base:
                    break
            if not kernels:
                continue
            labels = gap.kernel_labels_multigen(perms, kernels)
            for gens, lab in zip(kernels, labels, strict=False):
                if not lab or lab[3:] not in open_by_t:
                    continue
                t = lab[3:]
                need = set(open_by_t[t]) - covered.get(t, set())
                for qa, qb in qpairs:
                    if not need:
                        break
                    scanned += 1
                    try:
                        K = gp.galois_c2_multi(coeffs, [(qa, gens[0]), (qb, gens[1])])
                    except Exception:
                        continue
                    r = _r_if_valid(K)
                    if r in need:
                        if enq(f"tsig:c2m:{lab}:r{r}", K):
                            added += 1
                        need.discard(r)
                        covered.setdefault(t, set()).add(r)
    return added, scanned


def _tsig_biq(open_by_t, per_base, enq, n_bases: int = 3, n_primes: int = 2):
    """Biquadratic V_4-block (4x6): K=F(sqrt b1, sqrt b2) over deg-6 Galois totally-real bases —
    the size-4-block swath of 24T groups, disjoint from the size-2-block (2x12) families.
    """
    from igp import lmfdb
    added = scanned = 0
    covered: dict = {}
    for top in ("6T1", "6T2"):  # the order-6 (Galois) deg-6 groups
        for coeffs, _lab, _disc, _h in lmfdb.fields(6, galois_label=top, class_number=1,
                                                     max_r2=0, limit=n_bases):
            qs = _split_primes(coeffs, 6, k=n_primes)
            if not qs:
                continue
            perms = gp.galois_action_perms(coeffs)
            reps: dict = {}
            for pc in range(1, 4):
                for idx in combinations(range(6), pc):
                    w = [1 if k in idx else 0 for k in range(6)]
                    reps.setdefault(ks.module_basis(_bits(w), perms), w)
            pats = list(reps.values())
            pairs = list(combinations(pats, 2))[:per_base]
            if not pairs:
                continue
            labels = gap.biquadratic_labels_batch(perms, pairs)
            for w1, w2 in pairs:
                lab = labels.get((tuple(w1), tuple(w2)))
                if not lab or lab[3:] not in open_by_t:
                    continue
                t = lab[3:]
                need = set(open_by_t[t]) - covered.get(t, set())
                for q in qs:
                    if not need:
                        break
                    scanned += 1
                    try:
                        K = gp.biquadratic_c2(coeffs, w1, w2, q)
                    except Exception:
                        continue
                    r = _r_if_valid(K)
                    if r in need:
                        if enq(f"tsig:bq:{lab}:r{r}", K):
                            added += 1
                        need.discard(r)
                        covered.setdefault(t, set()).add(r)
    return added, scanned


_TSIG_FAMILIES = {"c2": _tsig_c2, "c2multi": _tsig_c2multi, "biq": _tsig_biq}


def produce_sigfill_targeted(force: bool = False, per_base: int = 300,
                             families: tuple = ("c2", "c2multi", "biq")):
    """Targeted discovery — enqueue tower constructions that hit a HIGH-VALUE signature: (t,r)
    valid, non-baseline, unheld by us, and teamCount<=1 — tc==0 = open (first ~= 1.0); tc==1 =
    another team's SOLE pair (~0.5 to us + halves their 1.0). Each family PREDICTS the group
    locally (kernel/biquadratic label over a Galois base) and we compute r LOCALLY (gp.real_roots);
    over TOTALLY-REAL bases the kernel spans intermediate r. We construct + enqueue ONLY candidates
    whose (predicted t, local r) is an open target. Families: `c2` (2x12 single), `c2multi` (2x12
    non-cyclic), `biq` (4x6 V_4). Self-throttled to ~6h; `force` overrides for a manual run.
    """
    from igp import baseline
    store.init()
    # cadence loosened 6h->2h (2026-07-11): producer_value shows tsig at ~32 pts/1k builds (starved
    # at 76 rows) -- one of the most efficient producers; run it more. kv-tunable.
    cadence = int(store.get_kv("tsig_cadence_s", 2 * 3600))
    if not force and time.time() - (store.get_kv("tsig_last", 0) or 0) < cadence:
        print(f"targeted sigfill: ran <{cadence // 3600}h ago, skipping (force=True to override)")
        return
    prog = json.loads((ROOT / "data" / "processed" / "progress.json").read_text())
    # Two tiers (2026-07-02): tc==0 = OPEN (first ~= 1.0), and tc==1 pairs SOMEONE ELSE holds solo
    # (37k pairs) — joining one is worth ~0.5 to us AND halves the holder's 1.0 (a ~1.0 relative
    # swing; competitors have been doing exactly this to our sole pairs). Same build cost either
    # way, so both tiers are targets. Pairs WE hold must be excluded HERE: tc==1 can be US, and
    # the families' `covered` is only a per-run dedup, not a held-pairs check.
    ours = {(r["t"], r["r"]) for r in db.load_realized() if r.get("label", "").startswith("24T")}
    open_by_t: dict = {}
    for (t, r) in baseline.valid_pairs():
        if baseline.is_baseline(t, r) or (t, r) in ours:
            continue
        e = prog.get(f"{t},{r}")
        if e is not None and e.get("teamCount", 9) <= 1:
            open_by_t.setdefault(t, set()).add(r)

    def enq(tgt, coeffs):
        return store.enqueue("ready", {"coeffs": coeffs}, target=tgt)

    added = scanned = 0
    per: dict = {}
    for fam in families:
        try:
            a, s = _TSIG_FAMILIES[fam](open_by_t, per_base, enq)
        except Exception as e:
            print(f"  tsig family {fam} failed: {str(e)[:80]}")
            a = s = 0
        per[fam] = a
        added += a
        scanned += s
    store.set_kv("tsig_last", time.time())
    n_open = sum(len(v) for v in open_by_t.values())
    by = ", ".join(f"{k}={v}" for k, v in per.items())
    print(f"targeted sigfill: {n_open} open 1.0 targets ({len(open_by_t)} groups); scanned "
          f"{scanned} on-target, enqueued {added} 1.0 candidates ({by}); queue={store.counts()}")


def produce_trinomials(cap: int = 200):
    """#6: enqueue irreducible degree-24 trinomials x^24 + a*x^k + b as 'ready' polys.

    Our empirical sole-realizer ENGINE: the broad trinomial sweep produced 9 of our first
    attributed sole realizers (rare groups the targeted towers don't reach). Cheap fan-out —
    Magma labels whatever results. Widened k and |a|,|b| ranges; the bandit's sole-share term
    (rank.py) keeps these prioritised despite their lower scoreable rate.
    """
    import sympy
    store.init()
    x = sympy.symbols("x")
    added = 0
    ks = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
    rng = (-5, -4, -3, -2, -1, 1, 2, 3, 4, 5)
    for k in ks:
        for a in rng:
            for b in rng:
                if added >= cap:
                    break
                f = x**24 + a * x**k + b
                if not sympy.Poly(f, x).is_irreducible:
                    continue
                asc = [0] * 25
                asc[0], asc[k], asc[24] = b, a, 1
                tgt = f"tri:24_{k}_{a}_{b}"
                if store.enqueue("ready", {"coeffs": asc}, target=tgt):
                    added += 1
    print(f"trinomial producer: enqueued {added} irreducible degree-24 trinomials; "
          f"queue={store.counts()}")


def _quad_stream():
    """Infinite stream of (i, j, a, b, c) for x^24 + a*x^i + b*x^j + c, small-coeff-first, genuine
    quadrinomials (a,b,c != 0; 1<=i<j<=23). Deterministic, so a kv cursor makes successive runs
    produce NEW candidates -> an inexhaustible, non-repeating generator."""
    from itertools import count
    for m in count(1):  # shell of max |coeff| = m (small discriminants first)
        for a in range(-m, m + 1):
            for b in range(-m, m + 1):
                for c in range(-m, m + 1):
                    if a == 0 or b == 0 or c == 0 or max(abs(a), abs(b), abs(c)) != m:
                        continue
                    for i in range(1, 24):
                        for j in range(i + 1, 24):
                            yield (i, j, a, b, c)


def produce_quadrinomials(target: int | None = None, max_add: int | None = None):
    """Continuous-supply fix: top the queue up toward `target` with irreducible degree-24
    quadrinomials (ready polys; Magma labels). A kv cursor over the deterministic small-coeff-first
    stream makes each run yield NEW candidates -> inexhaustible. Runs last in the tick so the
    targeted (high-yield) producers fill first and this absorbs the remaining verifier capacity.

    `target` (buffer depth) and `max_add` (per-run cap) default to kv knobs so the buffer can be
    tuned live as we learn the verifier's true rate -- bigger buffer => higher duty cycle between
    (infrequent) ticks."""
    import sympy
    store.init()
    target = target if target is not None else store.get_kv("quad_target", 2500)
    max_add = max_add if max_add is not None else store.get_kv("quad_max_add", 1500)
    queued = store.counts().get("queued", 0)
    need = min(max_add, max(0, target - queued))
    if need <= 0:
        print(f"quadrinomial producer: queue {queued} >= target {target}, no top-up")
        return
    x = sympy.symbols("x")
    cursor = store.get_kv("quad_cursor", 0)
    stream = _quad_stream()
    for _ in range(cursor):
        next(stream)
    added = scanned = 0
    scan_cap = need * 40  # bound work if irreducibles are sparse in a shell
    for (i, j, a, b, c) in stream:
        scanned += 1
        if sympy.Poly(x**24 + a * x**i + b * x**j + c, x).is_irreducible:
            asc = [0] * 25
            asc[0], asc[i], asc[j], asc[24] = c, a, b, 1
            if store.enqueue("ready", {"coeffs": asc}, target=f"quad:24_{i}_{j}_{a}_{b}_{c}"):
                added += 1
        if added >= need or scanned >= scan_cap:
            break
    store.set_kv("quad_cursor", cursor + scanned)
    print(f"quadrinomial producer: +{added} (cursor {cursor}->{cursor + scanned}, "
          f"queue->{store.counts().get('queued', 0)})")


def _pent_stream():
    """Infinite small-coeff-first stream of (i,j,k,a,b,c,d) for x^24 + a*x^i + b*x^j + c*x^k + d
    (genuine pentanomials; 1<=i<j<k<=23, coeffs != 0). Denser than quadrinomials => more distinct
    Galois groups (the S_24 majority is dropped by the daemon filter)."""
    from itertools import count
    for m in count(1):
        for a in range(-m, m + 1):
            for b in range(-m, m + 1):
                for c in range(-m, m + 1):
                    for d in range(-m, m + 1):
                        if 0 in (a, b, c, d) or max(abs(a), abs(b), abs(c), abs(d)) != m:
                            continue
                        for i in range(1, 24):
                            for j in range(i + 1, 24):
                                for k in range(j + 1, 24):
                                    yield (i, j, k, a, b, c, d)


def produce_pentanomials(cap: int = 400):
    """Second inexhaustible family (raw breadth): up to `cap` NEW irreducible degree-24
    pentanomials per run via a kv cursor. Runs each tick alongside the quad buffer for diversity."""
    import sympy
    store.init()
    x = sympy.symbols("x")
    cursor = store.get_kv("pent_cursor", 0)
    stream = _pent_stream()
    for _ in range(cursor):
        next(stream)
    added = scanned = 0
    for (i, j, k, a, b, c, d) in stream:
        scanned += 1
        if sympy.Poly(x**24 + a * x**i + b * x**j + c * x**k + d, x).is_irreducible:
            asc = [0] * 25
            asc[0], asc[i], asc[j], asc[k], asc[24] = d, a, b, c, 1
            tgt = f"pent:24_{i}_{j}_{k}_{a}_{b}_{c}_{d}"
            if store.enqueue("ready", {"coeffs": asc}, target=tgt):
                added += 1
        if added >= cap or scanned >= cap * 40:
            break
    store.set_kv("pent_cursor", cursor + scanned)
    print(f"pentanomial producer: +{added} (cursor {cursor}->{cursor + scanned}, "
          f"queue->{store.counts().get('queued', 0)})")


def _size3_patterns():
    """Length-8 Kummer exponent vectors (values 0..2): singletons + value-(1,1)/(1,2) pairs.
    Singletons of value 2 are omitted (same field as value 1); pairs vary the field."""
    pats = [[1 if k == i else 0 for k in range(8)] for i in range(8)]  # 8 singletons
    for i in range(8):
        for j in range(i + 1, 8):
            pats.append([1 if k in (i, j) else 0 for k in range(8)])  # (1,1) pairs
    for i in range(8):
        for j in range(8):
            if i != j:
                p = [0] * 8
                p[i], p[j] = 1, 2
                pats.append(p)  # (1,2) pairs
    return pats


def produce_size3(per_base: int = 24):
    """Enqueue size-3 (C_3-block, 8x3) cyclotomic-Kummer constructions over diverse zeta_n bases.

    n in {15,24,30} all have phi(n)=8 and 3|n (so zeta_3 in Q(zeta_n) => clean cyclic C_3 Kummer);
    each gives a distinct abelian degree-8 top. 8x3 is the bandit's top-yield shape; this widens it
    from one base/12 patterns to three bases x richer exponent patterns.
    """
    store.init()
    pats = _size3_patterns()
    added = 0
    for n, q in ((15, 31), (24, 73), (30, 31)):
        for w in pats[:per_base]:
            tgt = f"size3:z{n}:{''.join(map(str, w))}"
            if store.enqueue("cyclotomic_kummer", {"w": w, "n": n, "q": q, "k": 3}, target=tgt):
                added += 1
    print(f"size-3 producer: 3 bases (z15,z24,z30), enqueued {added}; queue={store.counts()}")


def _diverse_deg8_bases(cap: int = 24):
    """Diverse irreducible degree-8 fields for the compositum 8x3 (no local Galois label needed —
    Magma labels the degree-24 result). Wide form/coeff sweep, deduped by polredbest canonical
    form, so the degree-8 tops vary (=> varied 8x3 groups)."""
    out = gp.script(
        "p(f)=if(polisirreducible(f),print(Vec(polredbest(f))));\n"
        "for(a=-2,2,for(b=-2,2,for(c=-2,2,"
        "p(x^8+a*x^3+b*x+c);p(x^8+a*x^4+b*x^2+c);p(x^8+a*x^5+b*x+c))));",
        timeout=600,
    )
    seen, bases = set(), []
    for ln in out.splitlines():
        ln = ln.strip()
        if not ln.startswith("[") or ln in seen:
            continue
        seen.add(ln)
        bases.append([int(x) for x in ln.strip("[]").split(",")][::-1])
        if len(bases) >= cap:
            break
    return bases


_C8X3_CUBICS = [[-1, -2, 1, 1], [1, 0, -3, 1]]  # cyclic C_3 cubics (conductors 7, 9)


def produce_size3_compositum(per_run: int = 150):
    """8x3 = compositum of a degree-8 field with a cyclic cubic (group = deg-8 top x C_3), a CURSOR
    over the FULL LMFDB degree-8 mirror (100k+ fields) -- 8x3 is where sole realizers reportedly
    live, yet this had been ~24 locally-generated bases. Walks a per_run slice + advances an offset;
    enqueues a `compositum` build-task so the daemon's parallel pool builds the deg-24 field (Magma
    labels). Two cyclic cubics for signature variety.
    """
    from igp import lmfdb
    store.init()
    if _queue_full():
        print("size3 compositum: queue full (>cap); skipping this tick")
        return
    off = store.get_kv("c8x3_offset", 0)
    try:
        bases = lmfdb.fields(8, class_number=None, per_group=3, limit=per_run, offset=off)
        if not bases:
            off, bases = 0, lmfdb.fields(8, class_number=None, per_group=3, limit=per_run)
    except Exception as e:
        print(f"LMFDB unavailable ({str(e)[:80]}); skipping size3 compositum")
        return
    added = 0
    for coeffs, label, disc, _h in bases:
        for ci, cubic in enumerate(_C8X3_CUBICS):
            tgt = f"c8x3:{label}:d{disc}:c{ci}"
            if store.enqueue("compositum", {"base": coeffs, "cubic": cubic}, target=tgt):
                added += 1
    store.set_kv("c8x3_offset", off + per_run)
    print(f"size-3 compositum cursor[{off}:{off + per_run}]: {len(bases)} deg-8 fields, "
          f"enqueued {added}; queue={store.counts()}")


def clear(prefix: str):
    """Skip queued rows whose target starts with ``prefix`` (deprioritize saturated work)."""
    import sqlite3
    with sqlite3.connect(store.DB) as c:
        n = c.execute("UPDATE queue SET status='skipped' WHERE status='queued' AND target LIKE ?",
                      (prefix + "%",)).rowcount
    print(f"cleared {n} queued rows matching {prefix!r}; queue={store.counts()}")


def daemon_running() -> bool:
    out = subprocess.run(["pgrep", "-f", "scripts/searchd.py"], capture_output=True, text=True)
    return bool(out.stdout.strip())


def ensure_daemon():
    if daemon_running():
        return False
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a") as fh:
        subprocess.Popen(
            ["uv", "run", "python", "scripts/searchd.py"],
            cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, start_new_session=True,
        )
    return True


def rank_queue():
    """Set queue priorities via the producer bandit + per-row surrogate (igp.rank)."""
    progress = json.loads(PROG.read_text()) if PROG.exists() else {}
    summary = rank.apply_ranking(progress)
    print("ranking:", json.dumps(summary))


def autotune():
    """Bounded self-tuning (2026-07-04): every incident this week ended with a human adjusting a
    constant after the fact. Small steps, hard bounds; all changes land in the config journal.
    - prod_scale: producers multiply per_run by this; keeps queue depth in a healthy band.
    - max_pending: widens when the daemon reports pending-gate blocks (SAIR verify slowdowns)."""
    counts = store.counts()
    queued = counts.get("queued", 0)
    scale = float(store.get_kv("prod_scale", 1.0))
    cap = float(store.get_kv("prod_scale_cap", 8.0))  # throughput lever A (2026-07-10): was 4.0
    if queued < 8000:
        scale = min(scale * 1.3, cap)
    elif queued > 35000:
        scale = max(scale * 0.75, 0.5)
    if scale != float(store.get_kv("prod_scale", 1.0)):
        store.set_kv("prod_scale", round(scale, 2))
        print(f"autotune: prod_scale -> {scale:.2f} (queued={queued})")
    st = store.get_kv("status", {}) or {}
    hits = int(store.get_kv("gate_hits", 0)) + (1 if st.get("gated") else -1)
    hits = max(hits, 0)
    if hits >= 3:
        mp = min(int(store.get_kv("max_pending", 4000)) + 500, 8000)
        store.set_kv("max_pending", mp)
        print(f"autotune: max_pending -> {mp} (gate pressure)")
        hits = 0
    store.set_kv("gate_hits", hits)


def _qmax() -> int | None:
    """MAX(rowid) of the queue -- monotone in rows INSERTED (enqueues), robust to pruning (which
    deletes old, low rowids and never lowers MAX). Delta around a producer call == that producer's
    enqueue count (only producers insert queue rows, and the tick runs them sequentially)."""
    import sqlite3
    try:
        with sqlite3.connect(store.DB) as c:
            return c.execute("SELECT MAX(rowid) FROM queue").fetchone()[0] or 0
    except Exception:
        return None


def _record_producer_runs(producers) -> None:
    """Run each producer AND persist per-producer health to kv, so a SILENT or CRASHING producer
    can't hide. This is the gen12 blind spot (2026-07-10): gen12 swallowed its own int(None) crash,
    returned 0, and stayed dead for days while the daemon showed 'up' and the score bled. Health
    recording is fully fail-soft -- it never blocks production."""
    try:
        health = store.get_kv("producer_health", {}) or {}
    except Exception:
        health = {}
    now = int(time.time())
    for producer in producers:
        name = producer.__name__
        r0 = _qmax()
        err = None
        try:
            producer()
        except Exception as e:
            err = str(e)[:150]
            print(f"  producer {name} failed: {err}")
        try:
            r1 = _qmax()
            enq = max(0, r1 - r0) if (r0 is not None and r1 is not None) else 0
            rec = health.get(name, {})
            rec.update(last_ts=now, last_enq=enq, last_error=err,
                       err_streak=(rec.get("err_streak", 0) + 1) if err else 0,
                       zero_streak=0 if enq > 0 else rec.get("zero_streak", 0) + 1,
                       max_enq=max(rec.get("max_enq", 0), enq),
                       total_enq=rec.get("total_enq", 0) + enq)
            if enq > 0:
                rec["last_enq_ts"] = now
            health[name] = rec
        except Exception as e:
            print(f"  health-record {name} failed: {str(e)[:60]}")
    try:
        store.set_kv("producer_health", health)
    except Exception:
        pass


def producer_health(zero_alert: int = 12, err_alert: int = 3) -> list[str]:
    """Alerts for producers that look BROKEN (not merely exhausted): a producer that PROVED capacity
    (peak enqueue >= 50/run) but has errored err_alert+ runs in a row, or gone silent zero_alert+
    consecutive ticks. A SILENT alert on a genuinely-exhausted producer is still useful signal (add
    runway). Returns human-readable alert strings (empty = all healthy)."""
    health = store.get_kv("producer_health", {}) or {}
    now = int(time.time())
    out = []
    for name, rec in sorted(health.items()):
        es, zs = rec.get("err_streak", 0), rec.get("zero_streak", 0)
        if es >= err_alert:
            emsg = (rec.get("last_error") or "")[:55]
            out.append(f"{name}: ERRORING x{es} -- {emsg}")
        elif rec.get("max_enq", 0) >= 50 and zs >= zero_alert:
            le = rec.get("last_enq_ts")
            hrs = f"{(now - le) // 3600}h" if le else "?"
            out.append(f"{name}: SILENT {zs} ticks (~{hrs}); peak {rec['max_enq']}/run, "
                       f"total {rec.get('total_enq', 0)} -- exhausted or broken?")
    return out


def produce_gen12_treal(per_run: int = 300, hi: int = 60000, n_primes: int = 8):
    """TOTALLY-REAL-base C2 kernel -- the minblk=2 HIGH-R lever (2026-07-10). r(K) = 2*#{real places
    of the deg-12 base F where alpha>0} <= 2*r1(F), so ONLY totally-real bases (max_r2=0) can reach
    the high-r open pairs. Within the ~41k open minblk=2 pairs, r>=16 holds 23,817 (r=24 alone
    10,411), yet gen12's complex-base cursor SATURATED r=0 (439k held / 3k open) and structurally
    can't reach them. Same general_c2 machinery, restricted to max_r2=0 bases + a WIDE split-prime
    sweep (each prime = a different alpha sign = a different r), atlas-open-gated. Validated: these
    totally-real bases build 47% at r>=16, 33% at r=24 (vs 0.03% of held). Shares gen12's atlas."""
    from igp import lmfdb
    store.init()
    if _queue_full():
        return
    per_run = max(50, int(per_run * float(store.get_kv("prod_scale", 1.0))))
    n_primes = int(store.get_kv("gen12treal_nprimes", n_primes))
    off = int(store.get_kv("gen12treal_offset", 0))
    try:
        bases = lmfdb.fields(12, max_r2=0, class_number=None, per_group=2,
                             limit=per_run, offset=off)
        if not bases:
            off = 0
            bases = lmfdb.fields(12, max_r2=0, class_number=None, per_group=2, limit=per_run)
    except Exception as e:
        print(f"LMFDB unavailable ({str(e)[:60]}); skipping gen12_treal")
        return
    pats = _gen12_pats()
    try:
        from igp import atlas, db
        prog = json.loads(PROG.read_text())
        held = {(int(r["t"]), int(r["r"])) for r in db.load_realized()
                if r.get("label", "").startswith("24T")}
        amap = atlas.classify(prog, held, prefix="gen12:")
    except Exception:
        amap = {}
    explore_budget = 150
    added = used = skipped_dry = 0
    for coeffs, label, disc, _h in bases:
        try:
            qs = gp.split_primes(coeffs, 12, k=n_primes, hi=hi)
        except Exception:
            qs = []
        if not qs:
            continue
        used += 1
        for q in qs:
            for w in pats:
                wtag = "".join(map(str, w))
                info = amap.get(f"gen12:{label}:{wtag}")
                if info is not None:
                    builds = sum(info["labels"].values())
                    rate = info["open_pairs"] / builds if builds else 1.0
                    if info["open_pairs"] == 0 or (builds >= 20 and rate < 0.02):
                        skipped_dry += 1
                        continue
                if info is None:
                    if explore_budget <= 0:
                        continue
                    explore_budget -= 1
                tgt = f"gen12treal:{label}:d{disc}:q{q}:{wtag}"
                if store.enqueue("general_c2", {"base": coeffs, "w": w, "q": q}, target=tgt):
                    added += 1
    store.set_kv("gen12treal_offset", off + per_run)
    store.set_priority_prefix("gen12treal", 128.0)  # high-r open buckets are the richest slice left
    print(f"gen12_treal cursor[{off}:{off + per_run}]: {len(bases)} totally-real bases, {used} "
          f"usable, enqueued {added} (skipped {skipped_dry} dry); queue={store.counts()}")


# nflist DIRECT-PRODUCT families (tasks #14 + #18, 2026-07-10): the compositum of an nflist deg-4
# field and a coprime deg-6 field is a deg-24 field of the PRODUCT-ACTION group -- a family the
# producers can't reach, with TINY SMOOTH discs (strong score ratio + always scoreable, no grader
# blank). The 24Tt is fixed per (G4,G6) pair (verified once via GAP product action); r is read off
# polsturm and open-gated. nflist name -> GAP transitive ID: C4=4T1,V4=4T2,A4=4T4,C6=6T1,D6=6T3.
NFLIST_DP = [("C4", "C6", 2), ("V4", "C6", 3), ("A4", "C6", 71),
             ("C4", "D6", 27), ("V4", "D6", 30), ("A4", "D6", 250)]


def produce_nflist(per_recipe: int = 5, window: int = 10**7, max_attempts: int = 12):
    """Enqueue deg-24 direct-product fields from nflist small-field compositums (good polys: tiny
    smooth disc). Group per (G4,G6) is GAP-fixed; each candidate is gated OPEN (teamCount==0) or
    disc-defensible (held-by-others -> the tiny disc wins disc-min)."""
    store.init()
    if _queue_full():
        return
    try:
        prog = json.loads(PROG.read_text())
    except Exception:
        prog = {}
    added = attempts = 0
    # ROTATE 2 recipes per call with a hard attempt budget: each compositum24 is a deg-24
    # polredabs+nfdisc (~2s), so an unbounded sweep blows the 5-min feed window. 2 recipes/call
    # covers all 6 over 3 calls; max_attempts bounds the wall time.
    ri = int(store.get_kv("nflist_recipe_i", 0)) % len(NFLIST_DP)
    recipes = (NFLIST_DP[ri:] + NFLIST_DP[:ri])[:2]
    store.set_kv("nflist_recipe_i", (ri + 2) % len(NFLIST_DP))
    for g4, g6, t in recipes:
        if attempts >= max_attempts:
            break
        ts = str(t)
        off = int(store.get_kv(f"nflist_{g4}{g6}_off", 0))
        try:
            f4s = gp.nflist_fields(g4, off * window + 1, (off + 1) * window, limit=14)
            f6s = gp.nflist_fields(g6, 1, window, limit=8)
        except Exception:
            continue
        if not f4s or not f6s:
            store.set_kv(f"nflist_{g4}{g6}_off", 0)  # window empty -> restart the cursor
            continue
        n = 0
        for f4, d4 in f4s:
            if n >= per_recipe or attempts >= max_attempts:
                break
            for f6, d6 in f6s:
                if attempts >= max_attempts:
                    break
                if math.gcd(d4, d6) != 1:
                    continue  # shared subfield -> compositum collapses to a fiber product (wrong t)
                attempts += 1
                try:
                    res = gp.compositum24(f4, f6)
                except Exception:
                    res = None
                if not res:
                    continue  # not linearly disjoint / rough disc -> next f6
                co, r = res
                tc = prog.get(f"{ts},{r}", {}).get("teamCount")
                if tc is None:
                    break  # (t,r) not achievable -> next base
                tier = "new" if tc == 0 else "alt"  # open 1.0 vs tiny-disc defense
                tag = f"nflist:{g4}{g6}{tier}:{ts}.{r}:w{off}i{n}"
                if store.enqueue("ready", {"coeffs": co}, target=tag):
                    added += 1
                    n += 1
                break  # one model per base (disc diversity comes from the next f4)
        store.set_kv(f"nflist_{g4}{g6}_off", off + 1)
    store.set_priority_prefix("nflist:", 125.0)
    print(f"nflist direct-product: {added} enqueued / {attempts} attempts; queue={store.counts()}")


# ABELIAN-KERNEL families (task #3, 2026-07-12): a C_n cyclic RAY CLASS FIELD over a deg-(24/n)
# base (gp.abelian_kernel) -- the class-field-theory generalization of general_c2's n=2 radical to
# arbitrary abelian kernels, reaching the SOLVABLE minblk=3 (C3/deg8) and minblk=4 (C4/deg6) strata
# the C2-tower structurally can't. The 24Tt is DETERMINISTIC per base Galois label (pilot: 6T5->
# 24T65, 6T11->24T397, 6T13->24T643; 8T17->24T113, 8T47->24T7221), and the base signature is a clean
# r dial: totally-real base (max_r2=0) -> r=24, mixed -> r=8, complex -> r=0. Pilot 5/7 scoreable.
ABELIAN_RECIPES = [(6, 4), (8, 3)]  # (base degree, kernel degree C_n); n = 24/deg


def _abelian_gate():
    """Open-gate state for produce_abelian. The group 24Tt is deterministic per (recipe, base_label)
    (up to an occasional adjacent sibling), and the cursor walks the disc-ORDERED mirror, so a
    recurring label's deeper fields carry only LARGER discs and re-produce the SAME (t,r) we already
    hold -- pure waste. Returns per-key {(recipe, base_label): {"pairs": set((t,r)), "builds": int}}
    (the r-distribution actually observed for that key) plus the set of (t,r) we hold scoreable. The
    loop skips a key only once it is WELL-SAMPLED (builds>=3) and every observed pair is held --
    sound: a thinly-seen or partially-open label still builds."""
    from collections import defaultdict

    from igp import db
    keys: dict = defaultdict(lambda: {"pairs": set(), "builds": 0})
    held: set = set()
    for r in db.load_realized():
        if not r.get("label", "").startswith("24T"):
            continue
        pair = (r.get("t"), r.get("r"))
        if str(r.get("scoreable")).lower() == "true":
            held.add(pair)
        src = r.get("source", "")
        if src.startswith("daemon:abelian:"):
            parts = src.split(":")
            if len(parts) >= 4:
                base_label = parts[3].split(".")[0]  # strip any ".r8" provenance suffix
                k = keys[(parts[2], base_label)]
                k["pairs"].add(pair)
                k["builds"] += 1
    return keys, held


def produce_abelian(per_recipe: int = 24, treal: bool | None = None):
    """Enqueue C_n ray-class-field deg-24 specs (daemon's pool does the heavy bnfinit+scan+polredabs
    build). Cursored over deg-6 (C4, minblk=4) and deg-8 (C3, minblk=3) bases; alternates totally-
    real bases (r=24, the rich high-r slice) and general bases (r in {0,8}) each call. Deterministic
    per base, so the cursor advancing over fresh bases is what avoids rework (a repeat dedups by
    poly). LOCAL-GATED inside gp.abelian_kernel (deg24 + irreducible + nfdisc-smooth)."""
    from igp import lmfdb
    store.init()
    if _queue_full():
        return
    if treal is None:  # alternate treal/general across calls so both r-regimes stay fed
        treal = not bool(store.get_kv("abelian_treal_last", False))
    store.set_kv("abelian_treal_last", treal)
    per_recipe = max(8, int(per_recipe * float(store.get_kv("prod_scale", 1.0))))
    keys, held = _abelian_gate()
    added = skipped_dry = 0
    for deg, n in ABELIAN_RECIPES:
        ckey = f"abelian_{deg}_{n}_off" + ("_tr" if treal else "")
        off = int(store.get_kv(ckey, 0))
        try:
            bases = lmfdb.fields(deg, class_number=None, per_group=2, limit=per_recipe,
                                 offset=off, max_r2=0 if treal else None)
            if not bases:
                off = 0
                bases = lmfdb.fields(deg, class_number=None, per_group=2, limit=per_recipe,
                                     max_r2=0 if treal else None)
        except Exception as e:
            print(f"LMFDB unavailable ({str(e)[:60]}); skipping abelian d{deg}c{n}")
            continue
        recipe = f"d{deg}c{n}{'tr' if treal else 'g'}"
        for i, (coeffs, label, disc, _h) in enumerate(bases):
            k = keys.get((recipe, label))
            # skip a WELL-SAMPLED, fully-held label: deeper same-label fields (larger disc) re-
            # produce the same held (t,r), so building them is pure waste (sound: thin/partly-open
            # labels still build, and every unseen label explores)
            if k and k["builds"] >= 3 and k["pairs"] and k["pairs"] <= held:
                skipped_dry += 1
                continue
            tag = f"abelian:{recipe}:{label}:d{disc}:off{off}i{i}"
            if store.enqueue("abelian_kernel", {"base": coeffs, "n": n}, target=tag):
                added += 1
        store.set_kv(ckey, off + per_recipe)
    # MEASURED low value (test 0065, 2026-07-12): reaches minblk=3/4 but those strata are heavily
    # contested (k>=10 => 2^(1-k)~0); 38 wins earned only 0.25 pts, ~all from ONE low-k hit
    # (24T265,24 k=3). Builds are EXPENSIVE (10-20s vs <1s), so keep priority LOW so they don't
    # starve gen12_treal (the real lever); retained as cheap exploration for the rare low-k pair.
    store.set_priority_prefix("abelian:", 30.0)
    print(f"abelian (treal={treal}): enqueued {added} (skipped {skipped_dry} dry); "
          f"queue={store.counts()}")


# The full producer set, shared by tick() (every 15 min, with refresh) and feed() (every ~5 min,
# producers only) -- so the daemon's queue stays topped up between full ticks instead of idling.
TICK_PRODUCERS = (produce, produce_spec, produce_compositum, produce_general12, produce_gen12_treal,
                  produce_size4,
                  produce_size4_general, produce_lmfdb, produce_discmin, produce_discmin2,
                  produce_sigfill, produce_sigfill_targeted, produce_size3,
                  produce_size3_compositum, produce_g8x3, produce_g6x4, produce_compose,
                  produce_lift, produce_selfcomp,
                  produce_harden, produce_tr6, produce_mb2, produce_basemin, produce_rfill,
                  produce_nflist, produce_abelian)


def feed():
    """Lightweight produce-only cycle for a FAST timer (~5 min): run the producers + rank + record
    per-producer health, but SKIP the tick's slow, rate-flaky leaderboard refresh. This decouples
    production cadence from the 15-min full tick so the daemon never drains to 0 and idles
    (throughput lever B, 2026-07-10). The atlas dry-gate + bandit still front every producer, so
    more volume stays quality-directed, not a random flood."""
    if store.get_kv("control", {}).get("stop"):
        print("feed: daemon stopped; skipping")
        return
    try:
        autotune()
    except Exception as e:
        print(f"  autotune failed: {str(e)[:60]}")
    _record_producer_runs(TICK_PRODUCERS)
    for a in producer_health():
        print(f"  !!producer-health {a}")
    try:
        rank_queue()
    except Exception as e:
        print(f"  ranking failed: {str(e)[:60]}")
    print("feed queue:", store.counts())


def tick():
    """One hands-off maintenance cycle (for cron): ensure daemon, refresh, produce, rank, status."""
    relaunched = ensure_daemon()
    print(f"daemon {'RELAUNCHED' if relaunched else 'already running'}")
    try:
        autotune()
    except Exception as e:
        print(f"  autotune failed: {str(e)[:60]}")
    if not PROG.exists() or (time.time() - PROG.stat().st_mtime) > 2 * 3600:
        refresh()
    try:  # official standings snapshot (rank/score truth vs our estimate; fail-soft)
        lb = ROOT / "data" / "processed" / "leaderboard.json"
        lb.write_text(json.dumps({"t": int(time.time()), "items": sair.leaderboard()}))
    except Exception as e:
        print(f"  leaderboard fetch failed: {str(e)[:60]}")
    # Un-stale local scoreable flags from SAIR's ASYNC disc scoring (a poly labels immediately but
    # scores later; engine.collect records the pending=false and never re-fetches). Left unchecked
    # this UNDERCOUNTS local coverage/score and mis-aims defense/disc-min -- a one-off resync
    # recovered 10,399 rows (2026-07-12). Gated to ~3h (fetches up to 400 submissions). Fail-soft.
    try:
        if time.time() - float(store.get_kv("resync_last", 0)) > 3 * 3600:
            try:  # sibling script: bare when run as `python scripts/search_ctl.py`, dotted when
                import resync_scoreable as _rs  # imported as scripts.search_ctl (tests)
            except ModuleNotFoundError:
                import scripts.resync_scoreable as _rs
            s = _rs.resync()
            store.set_kv("resync_last", time.time())
            if s["upgraded"]:
                print(f"  resync: upgraded {s['upgraded']} stale-scoreable rows "
                      f"({s['downloaded']} subs)")
    except Exception as e:
        print(f"  resync failed: {str(e)[:60]}")
    # quad/pent/tri (inexhaustible random enumerators) are intentionally OMITTED from auto-prod
    # -- they've plateaued (quad: 9343 attempts -> 108 sigs) and the daemon won't submit them anyway
    # (searchd no_submit). Still available on demand via produce-quad/pent/trinomials.
    _record_producer_runs(TICK_PRODUCERS)
    for a in producer_health():  # surface a dead/silent feed in the tick log (the gen12 blind spot)
        print(f"  !!producer-health {a}")
    try:
        rank_queue()
    except Exception as e:
        print(f"  ranking failed: {str(e)[:60]}")
    status()


def status():
    print("queue:", store.counts())
    st = store.get_kv("status")
    if st:
        print("daemon last:", json.dumps(st))
    print("control:", store.get_kv("control", {}))
    sole = [r for r in db.load_realized() if r.get("source", "").startswith("daemon:")]
    print(f"daemon-realized rows: {len(sole)}")


def harvest():
    import sqlite3
    with sqlite3.connect(store.DB) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute("SELECT target,label,status FROM queue WHERE status='verified'").fetchall()
    for r in rows:
        ok = r["target"] == r["label"]
        print(f"  {r['target']} -> {r['label']} {'OK' if ok else 'MISMATCH'}")
    print(f"verified: {len(rows)}")


def main():
    store.init()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "refresh":
        refresh()
    elif cmd == "produce":
        produce()
    elif cmd == "produce-spec":
        produce_spec()
    elif cmd == "produce-comp":
        produce_compositum()
    elif cmd == "produce-size4":
        produce_size4()
    elif cmd == "produce-size3":
        produce_size3()
    elif cmd == "produce-size3c":
        produce_size3_compositum()
    elif cmd == "produce-gen12":
        produce_general12()
    elif cmd == "produce-gen12treal":
        produce_gen12_treal()
    elif cmd == "produce-nflist":
        produce_nflist()
    elif cmd == "produce-m24":
        produce_m24()
    elif cmd == "produce-rfill":
        produce_rfill()
    elif cmd == "produce-basemin":
        produce_basemin()
    elif cmd == "produce-mb2":
        produce_mb2()
    elif cmd == "produce-lit":
        produce_literature()
    elif cmd == "produce-g8x3":
        produce_g8x3(force=True)
    elif cmd == "produce-g6x4":
        produce_g6x4(force=True)
    elif cmd == "produce-compose":
        produce_compose(force=True)
    elif cmd == "produce-lift":
        produce_lift(force=True)
    elif cmd == "produce-selfcomp":
        produce_selfcomp(force=True)
    elif cmd == "produce-harden":
        produce_harden(force=True)
    elif cmd == "produce-tr6":
        produce_tr6(force=True)
    elif cmd == "produce-size4g":
        produce_size4_general()
    elif cmd == "produce-lmfdb":
        produce_lmfdb()
    elif cmd == "produce-trinomials":
        produce_trinomials()
    elif cmd == "produce-quad":
        produce_quadrinomials()
    elif cmd == "produce-pent":
        produce_pentanomials()
    elif cmd == "produce-discmin":
        produce_discmin()
    elif cmd == "produce-discmin2":
        produce_discmin2()
    elif cmd == "produce-sigfill":
        produce_sigfill()
    elif cmd == "produce-tsig":
        produce_sigfill_targeted(force=True)
    elif cmd == "clear":
        clear(sys.argv[2])
    elif cmd == "tick":
        tick()
    elif cmd == "feed":
        feed()
    elif cmd == "rank":
        rank_queue()
    elif cmd == "status":
        status()
    elif cmd == "health":
        alerts = producer_health()
        print("PRODUCER HEALTH:", "all producers OK" if not alerts else f"{len(alerts)} ALERT(S)")
        for a in alerts:
            print("  !!", a)
        ph = store.get_kv("producer_health", {}) or {}
        for name, rec in sorted(ph.items(), key=lambda kv: -kv[1].get("last_enq", 0)):
            print(f"    {name:26s} last_enq={rec.get('last_enq', 0):5d} "
                  f"zero={rec.get('zero_streak', 0):3d} err={rec.get('err_streak', 0)} "
                  f"peak={rec.get('max_enq', 0)}")
    elif cmd == "failures":
        fr = store.get_kv("failed_reasons", {}) or {}
        if not fr:
            print("no SAIR-rejected polynomials recorded yet")
        else:
            print(f"SAIR rejection reasons by producer ({sum(fr.values())} total):")
            for k, n in sorted(fr.items(), key=lambda x: -x[1])[:30]:
                fam, _, reason = k.partition("|")
                print(f"  {n:6d}  {fam:14s} {reason}")
    elif cmd == "harvest":
        harvest()
    elif cmd in ("pause", "resume", "stop"):
        ctrl = store.get_kv("control", {})
        ctrl["stop" if cmd == "stop" else "pause"] = (cmd != "resume")
        store.set_kv("control", ctrl)
        print(f"control = {ctrl}")
    elif cmd == "set":
        key, val = sys.argv[2], json.loads(sys.argv[3])
        store.set_kv(key, val)
        print(f"{key} = {val}")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
