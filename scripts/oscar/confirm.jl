# Seeded Stauduhar descent ("confirm the predicted group" — IGP24 Phase-0 spike option C).
#
# We always KNOW the predicted 24Tt from the construction, hence the target group's ORDER.
# Inject `order(x) >= o_known` into the descent GroupFilter: DescentEnv applies the filter to
# prune maximal subgroups BEFORE building their (expensive, high-precision) resolvents, so every
# subgroup smaller than the answer — including the confirming resolvents at the answer level —
# is skipped. Replicates the galois_group prologue (find_prime -> GaloisCtx -> starting_group)
# verbatim except for that one extra filter, then calls the public `descent`.
#
# Finding (docs/tests/0026): correct on all cases; ~9-28% faster on the slow ones; the real win
# is MEMORY — it rescued 24T7871 (de-novo OOM'd at 16GB) to a clean 16-min run under the cap.
#
# Run under a 16GB physical-RAM cap (see README.md).

using Oscar

include(joinpath(@__DIR__, "test_polys.jl"))

# the slow / OOM de-novo cases (validate.jl) worth seeding; "" => all
const CONFIRM = Set(["24T577", "24T1627", "24T5338", "24T7871"])

const GG = Oscar.GaloisGrp
# descent internals aren't exported; resolve each from GaloisGrp -> Hecke -> Oscar
resolve(s) = isdefined(GG, s) ? getfield(GG, s) :
             (isdefined(Hecke, s) ? getfield(Hecke, s) : getfield(Oscar, s))
const find_prime       = resolve(:find_prime)
const starting_group   = resolve(:starting_group)
const descent          = resolve(:descent)
const order_from_shape = resolve(:order_from_shape)
const GaloisCtx        = resolve(:GaloisCtx)

Qx, x = polynomial_ring(QQ, "x")

const DENOVO = Dict("24T577"=>"22.5s", "24T1627"=>"4419.8s",
                    "24T5338"=>"2111.2s", "24T7871"=>"OOM@16G")

function confirm_via_order(label::String, coeffs::Vector{Int})
    t = parse(Int, split(label, "T")[2])
    o_known = order(transitive_group(24, t))
    K, _ = number_field(Qx(coeffs))
    p, ct = find_prime(K.pol, 2 * degree(K))
    GC = GaloisCtx(Hecke.Globals.Zx(numerator(K.pol)), p)
    roots(GC, 5)
    G, F, si = starting_group(GC, K; useSubfields = true)
    os = order_from_shape(ct, degree(K))
    push!(F, x -> order(x) % os == 0, "order lower bound")
    push!(F, x -> order(x) >= o_known, "seed: not below known order")
    Gg, _ = descent(GC, G, F, si)
    return transitive_group_identification(Gg)
end

println("label\tfound\tmatch\tC_secs\tdenovo")
flush(stdout)
for (label, coeffs) in POLYS
    (isempty(CONFIRM) || label in CONFIRM) || continue
    found = "?"; ok = false; secs = 0.0
    try
        secs = @elapsed begin
            id = confirm_via_order(label, coeffs)
            found = "$(id[1])T$(id[2])"
        end
        ok = (found == label)
    catch e
        found = "ERR:" * first(sprint(showerror, e), 140)
    end
    println("$label\t$found\t$(ok ? "OK" : "X")\t$(round(secs, digits=1))\t$(get(DENOVO, label, "?"))")
    flush(stdout)
end
println("=== confirm done ===")
flush(stdout)
