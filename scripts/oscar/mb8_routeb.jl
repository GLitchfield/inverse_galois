# minblk=8 cluster-B Route-B relative-Kummer + Galois-module CFT engine  (test 0052).
#
# Target: 24T19280 = (C2)^9:(C3 x L3(2)), kernel (C2)^9 = 3(+)6 = V (x) F2[C3]  (V = natural
# 3-dim F2[L3(2)]-module).  Generalizes to 20408 (S3 top) + cluster A (14051/16060).
#
# This is the OSCAR carry of the test-0050 PARI-BLOCKED spec.  It runs the feasibility LADDER,
# prints the verdict, and is structured to EMIT 25-coeff models (as `MODEL:<t> <r> <25 asc ints>`
# lines, parsed by scripts/mb8_routeb_oscar.py) the moment step (i) module-selection is unblocked.
#
# VERDICT (data/processed/oscar_routeb_probe.json): OSCAR does the tractable abelian arithmetic
# over the degree-21 non-Galois frame model M0 = S7.k (class_group, ray_class_group, induced
# C3-action) -- realizing spec-step (ii) totally-positive control -- but WALLS at spec-step (i)
# module-selection: the F2[C3xL3(2)]-module decomposition needs the L3(2)-action, which lives on
# the degree-168 L3(2)-closure.  normal_closure(S7) to degree 168 does NOT return in 900s, and
# automorphism_group(M0)=C3 only (L3(2) invisible on the non-Galois M0).  So steps (iii) torsor
# assembly and (iv) extraction are moot.  Same essential MODULE wall as PARI; not turnkey in Hecke.
#
# Run (ladder, ~5min; skips the 15-min normal_closure hang unless MB8_CLOSURE=1):
#   ~/.juliaup/bin/julia scripts/oscar/mb8_routeb.jl
#   MB8_CLOSURE=1 ~/.juliaup/bin/julia scripts/oscar/mb8_routeb.jl   # also attempt the deg-168 build

using Oscar

Qx, x = polynomial_ring(QQ, "x")

# --- seeds (test 0052) ---
# genuine 7T5 = L3(2) septic (OSCAR galois_group => order 168, id (7,5)); r1=3 (not totally real).
# ALL six (19280,r) sigs are open tc=0 so r=24 is not required to score; swap in a totally-real
# (r1=7) 7T5 septic here for the r=24 slice.
const S7  = x^7 - 7*x + 3
const KC  = x^3 - x^2 - 2*x + 1                 # C3 cubic, disc 49
const O8  = x^8 - 2*x^7 - 17*x^6 + 15*x^5 + 53*x^4 - x^3 - 37*x^2 - 15*x - 1  # 8T48 seed (diagonal V)
# Track-F seed-radical disc primes (the DIAGONAL twist; the F4-twist conductor is unknown).
const SEED_PRIMES = ZZ(2) * ZZ(21557) * ZZ(640663)

ck(k, v) = (println("[CKPT] $k = $v"); flush(stdout))

function build_frame()
    NS, _ = number_field([S7, KC])
    M0, _ = Hecke.simple_extension(NS)
    ck("M0_degree", degree(M0))
    return M0
end

# spec-step (ii): the tractable abelian arithmetic Hecke DOES over the deg-21 frame model.
function abelian_arithmetic(M0)
    local Cl, au, R, mR, Rs, act
    t = @elapsed begin; Cl, _ = class_group(maximal_order(M0)); end
    ck("class_group(M0 deg21)  [$(round(t,digits=1))s]", Cl)
    t = @elapsed begin; au = automorphism_group(M0); end
    ck("automorphism_group(M0/Q)  [$(round(t,digits=1))s]  (C3 only => L3(2) invisible)", order(au[1]))
    OM = maximal_order(M0); rlp = real_places(M0)
    t = @elapsed begin; R, mR = ray_class_group(SEED_PRIMES * OM, rlp; n_quo = 2); end
    Rs, _ = snf(R)
    ck("ray_class_group(M0, seed-modulus, mod 2)  [$(round(t,digits=1))s]  (rank $(ngens(Rs)))", Rs)
    # induce the C3-action = the ONLY part of the F2[Q]-module Hecke can see over M0
    sig = first(x for x in automorphism_list(M0) if x != id_hom(M0))
    t = @elapsed begin; act = Hecke.induce_action(mR, [sig]); end
    ck("induce_action(C3 on ray class group)  [$(round(t,digits=1))s]  (C3-part ONLY)", "ok")
    return R, mR, act
end

# spec-step (i): THE WALL.  Selecting the F4-twisted 6-dim F2[C3xL3(2)]-submodule needs the
# L3(2)-action = the degree-168 L3(2)-closure of the septic.  This is where OSCAR stops.
function module_selection_wall()
    if get(ENV, "MB8_CLOSURE", "0") == "1"
        println("[WALL] attempting normal_closure(S7) -> degree 168 (expected: no return in 900s) ...")
        flush(stdout)
        S7f, _ = number_field(S7)
        t = @elapsed (N0 = normal_closure(S7f))
        ck("normal_closure(S7)  [$(round(t,digits=1))s]", degree(N0))
    else
        println("[WALL] step (i) module-selection: needs the L3(2)-action on Cl/ray-class of the")
        println("[WALL]   degree-168 L3(2)-closure.  normal_closure(S7)->deg168 does NOT return in")
        println("[WALL]   900s (set MB8_CLOSURE=1 to reproduce the hang).  Aut(M0)=C3 exposes only")
        println("[WALL]   the C3-isotypic split, NOT which V within it => the 3(+)6 twist is")
        println("[WALL]   unresolvable in Hecke.  => 0 models emitted.  (Magma AbelianExtension")
        println("[WALL]   carrying the module is the candidate fallback; see the probe JSON.)")
        flush(stdout)
    end
    return Vector{Any}()   # models: empty until (i) is unblocked
end

# --- driver ---
println("=== mb8 Route-B OSCAR engine (test 0052) : 24T19280 = (C2)^9:(C3xL3(2)) ===")
flush(stdout)
M0 = build_frame()
abelian_arithmetic(M0)
models = module_selection_wall()
for m in models
    # m = (t, r, coeffs::Vector{Int} ascending) ; consumed by mb8_routeb_oscar.py
    println("MODEL:$(m[1]) $(m[2]) " * join(m[3], ","))
end
println("=== engine done : $(length(models)) model(s) emitted ===")
flush(stdout)
