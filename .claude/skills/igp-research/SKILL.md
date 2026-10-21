---
name: igp-research
description: IGP24 hands-off DEEP research pass. Periodically (via cron, during the daemon's downtime) spawn EXACTLY ONE research subagent to dive deep on the next topic in a rotating agenda (constructive inverse Galois, degree-24 families, disc-min, DB mining), then record the synthesis into the research notes and surface actionable leads. Token-bounded: one subagent, NO fan-out. Use when invoked by the research cron or when the user asks for a deep-research dive.
---

# IGP24 deep-research playbook (one subagent, rotating, hands-off)

Goal: always be learning the problem space — methods, families, papers that may seed future
solutions — without burning the token budget. Hard rule from the user: **exactly ONE subagent per
run, NO multi-agent fan-out.** The single subagent may do many WebSearch/WebFetch calls itself (that's
thorough, not fan-out); it must not spawn further agents.

## 1. Pop the next topic from the LIVING agenda
The agenda is a dynamic, self-refilling queue in `docs/research_agenda.md` — step 3 pushes back the
follow-up questions each dive surfaces, so it grows with the research frontier instead of cycling.
Read that file, take the **top Pending** topic. If the user named a topic, use that and leave the
queue alone. If Pending is ever empty, make this a meta-dive: review `docs/related_work.md` + the
realized coverage, propose the next promising directions, and seed them into Pending.

(The queue was seeded from these starter topics:)
0. Explicit `Q(t)` / regular realizations of specific degree-24 groups beyond M24 (Malle–Matzat,
   Malle's multi-parameter tables, recent arXiv) — with the polynomials if available.
1. Rigidity / rationality criteria — which non-solvable degree-24 groups are rigid (hence
   constructible by the rigidity method), and how.
2. Solvable-group realizations via class field theory / Shafarevich — practical recipes for the
   solvable bulk (24,193 of 25,000) beyond our C_2/V_4/C_3 towers.
3. Specific 2-transitive / primitive families on 24 points: PSL(2,23), PGL(2,23), M24, M12-on-24,
   AGL/ASL — known explicit polynomials + their discriminants (check teamCount: famous = contested).
4. Discriminant minimization theory: small-disc number fields, conductor–discriminant, smooth-disc
   constructions, and how to engineer small/easily-factored discs (the verifier factors poly disc).
5. Imprimitive/block structure systematics: a clean map of which 24Tt are reachable by which tower
   shape (2×12, 3×8, 4×6, 6×4, 8×3, 12×2) and the kernel/submodule lattice per top.
6. Number-field / polynomial databases beyond LMFDB: Klüners–Malle "Database for Number Fields",
   the Jones–Roberts DB, Magma/PARI tables — anything with degree-24 or tower polynomials we can mine.
7. Belyi maps / dessins d'enfants and three-point covers for degree-24 group realizations.
8. The A_24 (and other square-discriminant) parametric-family problem — how to construct one.
9. Competition meta: the public discoveries page + Zulip — what shapes/groups are still open, what
   methods strong teams report, any rule/scoring nuances we've missed.

## 2. Spawn ONE subagent (Agent tool, subagent_type "general-purpose", run_in_background false)
Prompt template (fill {TOPIC}; give it our context so leads are actionable):
> Deep research for the SAIR IGP24 competition (realize transitive degree-24 groups `24Tt` as Galois
> groups of irreducible degree-24 integer polynomials, minimizing field discriminant; score per
> (t,r) signature = 2^(1-k)·log(D0)/log(D), k=#teams, so being the SOLE realizer of an OBSCURE
> (t,r) ≈ 1.0 while famous groups are heavily contested). We already do imprimitive tower
> constructions (C_2/V_4/C_3 kernels over LMFDB base fields, cursored over the full mirror) + the
> Malle–Matzat M24 family. RESEARCH TOPIC: {TOPIC}. Do a thorough web dive (multiple
> WebSearch/WebFetch; arXiv, Malle/Klüners pages, LMFDB, math.SE). Return a structured synthesis:
> (a) key findings with CITATIONS (URLs); (b) any EXPLICIT polynomials / parametric families / recipes
> (verbatim if short); (c) CONCRETE actionable leads for us — constructions we could implement, groups
> we could target — each tagged with feasibility + the famous-vs-obscure (contested-vs-open) caveat;
> (d) what's a dead end and why; **(e) 2-4 SPECIFIC follow-up research questions this dive opened up
> that each deserve their own future deep dive** (these refill our agenda — make them concrete and
> non-overlapping with the current topic, not generic). Do NOT spawn other agents. Be specific and
> honest; "no usable construction found, here's why" is a fine result.

## 3. Record + REFILL the agenda (always)
Keep it hands-off (no approval prompts unattended) — use the **Edit/Write tools, NOT shell `cat >>`**
(shell append isn't pre-approved; Edit/Write on the repo, `.venv/bin/python`, and `git
add/commit/push` ARE). Only THREE writes per run — log, agenda, tasks — NOT the curated docs:
- **Verify the subagent's open/contested claims against `progress.json`** first (teamCount semantics:
  OPEN = teamCount==0 and unheld; SOLE = held & teamCount<=1). Past dives had the subagent wrong on
  specific teamCounts — record the VERIFIED status, noting any corrections.
- **Append to `docs/auto_log.md`**: Edit it — old_string = the `<!-- AUTOLOG-MARKER ... -->` line,
  new_string = your full dated section (topic; condensed synthesis with citations; the VERIFIED
  actionable leads with feasibility + contested/open caveat; what's a dead end) + the marker. This
  single append-only log is the durable record; do NOT touch related_work/exploration_backlog/
  commentary (those are human-curated by promoting highlights from the log in interactive sessions).
- **Refill `docs/research_agenda.md`** (rewrite with the **Write** tool): move the topic just done from
  Pending to Done (newest first, one-line outcome), and push the **best 1-2 of the subagent's
  follow-up questions (e)** onto Pending — deduped vs Pending + Done. This keeps the agenda growing
  rather than cycling. Cap +2/dive so Pending doesn't balloon.
- For any clearly-buildable, **verified-OPEN** lead, `TaskCreate` it (the structured actionable output).
- `git add docs/auto_log.md docs/research_agenda.md && git commit && git push` (granular, clean).

## 4. Report (2-3 lines)
Topic covered; the single most useful finding; the best actionable lead (or "nothing buildable —
logged for the record"). Don't auto-implement constructions — research surfaces leads; building is a
deliberate next step (and must pass the famous≠open / check-teamCount gate first).
