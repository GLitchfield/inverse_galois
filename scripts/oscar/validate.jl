# De-novo Galois-group identification of degree-24 polynomials via OSCAR (Fieker-Klüners),
# checked against our SAIR-Magma `24Tt` labels. Tests both coefficient orderings, so it also
# pins our realized.csv convention (ascending). See scripts/oscar/README.md + docs/tests/0026.
#
# Run under a 16GB physical-RAM cap:
#   systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=8G \
#     julia --heap-size-hint=14G scripts/oscar/validate.jl

using Oscar

include(joinpath(@__DIR__, "test_polys.jl"))   # const POLYS = [(label, coeffs_ascending), ...]

Qx, x = polynomial_ring(QQ, "x")

function tlabel(G)
    try
        id = transitive_group_identification(G)   # (n, i)
        return "$(id[1])T$(id[2])"
    catch
        return "$(degree(G))T$(transitive_identification(G))"
    end
end

println("known\tfound\torder\tmatch\tsecs")
flush(stdout)
nok = 0
for (label, coeffs) in POLYS
    found = "?"; ok = false; secs = 0.0; order = "-"
    try
        secs = @elapsed begin
            la = tlabel(galois_group(Qx(coeffs))[1])
            if la == label
                found = la; ok = true; order = "asc"
            else
                ld = tlabel(galois_group(Qx(reverse(coeffs)))[1])
                if ld == label
                    found = ld; ok = true; order = "desc"
                else
                    found = "asc=$la,desc=$ld"; order = "?"
                end
            end
        end
    catch e
        found = "ERR:" * first(sprint(showerror, e), 80)
    end
    global nok += ok ? 1 : 0
    println("$label\t$found\t$order\t$(ok ? "OK" : "X")\t$(round(secs, digits=1))")
    flush(stdout)
end
println("=== matched $nok / $(length(POLYS)) ===")
flush(stdout)
