# Hecke.fields driver for IGP24 (Sircana/Fieker constructive-Shafarevich enumerator).
#
# Builds degree-`n` fields realizing the SOLVABLE transitive group nTt, by enumerating the
# Galois-closure tower (Hecke.fields on the SmallGroup id) and extracting the degree-n non-normal
# subfields. For a REGULAR action (|G| == n, e.g. |G|=24 Galois groups) the degree-n field IS its
# own closure -> use fields() directly. signature() gives the real-root count r. The group label is
# guaranteed by CONSTRUCTION (constructive Shafarevich), not a search; the Python gate still
# density-checks each field against the target 24Tt.
#
# NOTE (2026-07-07): Hecke VN62X's own `fields_transitive_group`/`_find_discriminant_bound` is
# BUGGY here (line 63 `ind = i` indexes the subgroup-class list by the transitive number -> out of
# range; and the Frobenius branch's exact `root(disc^k, n-1)` errors on non-perfect powers). We
# therefore bypass it: the enumeration bound is the CLOSURE disc bound directly (passed by the
# caller / grown by the disc-min loop), and we extract the subfield for the class whose coset
# action has TransitiveIdentification == t, filtering emitted fields by their own disc <= field_cap.
#
# Usage:  julia hecke_fields.jl <n> <t> <enum_cap> <only_real:0|1> <unram-csv-or-""> \
#             [enum_seed] [field_cap]
#   enum_cap/enum_seed : bound on the Hecke.fields enumeration (= field disc for |G|=n, else the
#                        Galois-CLOSURE disc). With enum_seed -> disc-MIN loop (x4 until non-empty).
#   field_cap          : cap on the emitted degree-n field disc (default = enum_cap). For |G|>n set
#                        this to D_base-1 to demand a strictly-sub-baseline (winnable) field.
# Emits one JSON per field: {"coeffs":[c0..cn],"r":<r1>,"disc":"<abs>"}; final
# {"done":true,"count":k,"bound":"<last enum bound>"}. Coeffs ascending, NOT yet polredabs'd.

using Hecke, GAP

const EXT = Base.get_extension(Hecke, :GAPExt)
@assert EXT !== nothing "GAPExt not loaded (need GAP.jl)"

# Select the conjugacy class of core-free index-n subgroups whose coset action realizes 24Tt,
# then extract the corresponding fixed field from each closure tower. Bypasses to_non_normal
# (which picks the FIRST core-free index-n class, possibly a different transitive type).
function extract_subfields(lf, G1, n::Int, t::Int)
  lC = GAP.Globals.ConjugacyClassesSubgroups(G1)
  ind = 0
  for k in 1:Int(GAP.Globals.Length(lC))
    H = GAP.Globals.Representative(lC[k])
    Int(GAP.Globals.Index(G1, H)) == n || continue
    Int(GAP.Globals.Size(GAP.Globals.Core(G1, H))) == 1 || continue
    mp = GAP.Globals.FactorCosetAction(G1, H)
    Int(GAP.Globals.TransitiveIdentification(GAP.Globals.Image(mp))) == t || continue
    ind = k
    break
  end
  ind == 0 && error("no core-free index-$n subgroup with transitive id $t")
  rep = GAP.Globals.Representative(lC[ind])
  out = AbsSimpleNumField[]
  for x in lf
    Hecke.assure_automorphisms(x)
    EXT.assure_isomorphism(x, G1)
    push!(out, EXT.fixed_field(x, rep))
  end
  return out
end

function enum_at(n::Int, t::Int, bound::ZZRingElem, field_cap::ZZRingElem, gord::Int, id, G1;
                 only_real::Bool=false, unram::Vector{ZZRingElem}=ZZRingElem[])
  local ln
  if gord == n
    lf = Hecke.fields(id[1], id[2], bound; only_real=only_real, unramified_outside=unram)
    ln = [ft.field for ft in lf]
  else
    lf = Hecke.fields(id[1], id[2], bound; only_real=only_real, unramified_outside=unram)
    ln = extract_subfields(lf, G1, n, t)
  end
  out = Vector{Any}()
  seen = Set{Vector{BigInt}}()
  for K in ln
    OK = maximal_order(K)
    d = abs(discriminant(OK))
    d <= field_cap || continue
    f = defining_polynomial(K)
    cs = [BigInt(ZZ(coeff(f, j))) for j in 0:degree(f)]
    cs in seen && continue
    push!(seen, cs)
    r1, _ = signature(K)
    push!(out, (cs, r1, BigInt(d)))
  end
  return out
end

function main()
  n = parse(Int, ARGS[1])
  t = parse(Int, ARGS[2])
  enum_cap = ZZRingElem(parse(BigInt, ARGS[3]))
  only_real = ARGS[4] == "1"
  unram = ZZRingElem[]
  if length(ARGS) >= 5 && !isempty(ARGS[5])
    unram = ZZRingElem[ZZRingElem(parse(Int, s)) for s in split(ARGS[5], ",")]
  end
  seed = length(ARGS) >= 6 && !isempty(ARGS[6]) ? ZZRingElem(parse(BigInt, ARGS[6])) : nothing
  field_cap = length(ARGS) >= 7 && !isempty(ARGS[7]) ? ZZRingElem(parse(BigInt, ARGS[7])) : enum_cap

  Gt = GAP.Globals.TransitiveGroup(n, t)
  @assert Bool(GAP.Globals.IsSolvable(Gt)) "nTt not solvable"
  id = GAP.Globals.IdGroup(Gt)
  G1 = GAP.Globals.SmallGroup(id)
  gord = Int(id[1])

  res = Vector{Any}()
  lastbound = enum_cap
  if seed === nothing
    res = enum_at(n, t, enum_cap, field_cap, gord, id, G1; only_real=only_real, unram=unram)
  else
    b = seed
    while b <= enum_cap
      println(stderr, "[minloop] trying bound=$(string(b))"); flush(stderr)
      res = enum_at(n, t, b, field_cap, gord, id, G1; only_real=only_real, unram=unram)
      lastbound = b
      isempty(res) || break
      b = b * 4
    end
  end

  for (cs, r, d) in res
    coeffstr = "[" * join(string.(cs), ",") * "]"
    println("{\"coeffs\":$coeffstr,\"r\":$r,\"disc\":\"$(string(d))\"}")
  end
  println("{\"done\":true,\"count\":$(length(res)),\"bound\":\"$(string(lastbound))\"}")
  flush(stdout)
end

main()
