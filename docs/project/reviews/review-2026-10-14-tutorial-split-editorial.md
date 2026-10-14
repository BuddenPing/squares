# Editorial Review: The Basic and Advanced Square-Packing Tutorials

## Scope and Context

This is the author’s editorial and preservation record for
[TUTORIAL.md](../../../TUTORIAL.md) and
[TUTORIAL-ADVANCED.md](../../../TUTORIAL-ADVANCED.md), written by Codex, Astra strong
tier at xhigh, on 14 October 2026. It is not an independent mathematical review or a
publication approval.
The coordinator will arrange that review after the source is ready.

The owner asked for a much shorter beginner tutorial and an advanced companion, updated
for the latest results while preserving the original definitions and relevant
information. The writer read the original tutorial, the earlier pedagogy and soundness
reviews, current result and case records, the epistemic and regularization policies, and
the cited recent intake and formalization packets.
The
[plan and preservation map](../specs/active/plan-2026-10-14-basic-and-advanced-tutorials.md)
account for every original section and moved subsection.

Safe expression and formatting changes were applied directly.
The owner’s explicit revision brief also authorizes the structural split and factual
updates. Those substantive changes are recorded below with their evidence, rather than
silently changing the source’s meaning.
No result or policy was edited.

## Strengths Preserved

- The original gives complete mechanisms: the separation-cell LP, a finite weighted
  lower-bound proof, exact equality/sign decisions, and the local/global/capture proof
  composition. Those derivations remain in the advanced paper.
- Its distinctions prevent specific mistakes: a cell optimum is not a full local
  optimum; a numerical endpoint is not a certified terminal component; a contact graph
  is not a typed equation system; stationarity and rigidity do not prove global
  optimality. Each retains an explanation and relevant example.
- Its vocabulary and notation cards support readers returning to the technical paper.
  Every original row remains, with the changed definitions and new concepts noted below.
- Its provenance is unusually specific.
  Experiment identifiers, numerical baselines, scope limits, source links and figures
  are retained rather than replaced by general summaries.

## Weaknesses and Dispositions

| Group | Original issue | Applied change or remaining boundary |
| --- | --- | --- |
| Purpose, P1–P4 | The beginner introduction expanded into a long certificate proof before explaining the configuration model or LPs | Basic develops examples and evidence literacy; advanced teaches the LP and exact arithmetic before the certificate |
| Expression, E1–E3 | Repeated framing, absolute historical claims, several “what it bought” and “the trick” announcements, and present-tense old benchmark conclusions | Removed redundant framing; retained the measurements and scoped them to the experiments that produced them |
| Form, F1–F3 | A split would break old numbered-section links and move figures away from pinned source checks | Added explicit old-fragment landings and a full migration map; named the checks the coordinator must migrate |
| Reasoning, R1–R4 | The five-square family paragraph could be read as a claim about Göbel’s optimum; endpoint language conflated an implemented stopping condition with a mathematical local minimum | Named the worse family’s side; distinguished T-012/T-014; clarified the numerical-versus-mathematical terminal-set distinction |
| Grounding, G1–G3 | The paper omitted registered uniqueness and described proof-assistant formalization as unbuilt; recent regularization and independence rules were absent | Updated from T-112, the Lean packets, the regularization policy and the 14 October independence record |
| Judgment, J1–J3 | Old failures of one annealer could read as claims about every current proposer; numerical checks could obscure later exact certificates | Restricted search conclusions to their methods and seeds; separated the n=29 source transcription from subsequent certificates |

## Substantive Claim Changes

1. **The two five-square objects are different.** The retained exp-033/exp-034 face and
   sheet have side $1+5\sqrt2/4$, above the global optimum $2+\sqrt2/2$. The advanced
   refinement section retains the family lesson and its unresolved nonlinear scope.
   It also gives the separate current result: T-012 proves a second-order obstruction
   for Göbel’s optimum, and T-014 proves local isolation at fixed side, both `V3/C3`.
   Sources: the
   [synopsis’s exact-geometry inventory](../../../SYNOPSIS.md#what-is-built) and
   [X-012 proof](../../../packing/campaign/explorations/X-012-one-chart-four-hundred-inequalities-and-an-order-2m-contradiction.md).
   No classification of every five-square optimum is inferred.
2. **Eleven-square optimality and uniqueness have separate statuses.** T-060 remains
   `V3/C3`; T-112 records the equality-case uniqueness corollary at `V3/C2`. The old
   statement that T-060 alone does not assert uniqueness is preserved in substance by
   naming the distinct result, rather than implying the repository has no uniqueness
   result. Sources: [results register](../../../packing/frontier/RESULTS.md) and
   [uniqueness review](review-2026-10-06-n11-uniqueness-adversarial.md).
3. **Reported formalization is present, complete local replay is not.** The advanced
   arithmetic/tooling list no longer calls every proof-assistant formalization unbuilt.
   The
   [eleven-square packet](../../../packing/resources/web/queuingtheorydotcom-n11-lean-2026-10-06/README.md)
   distinguishes the reported full check from the statement-closure and upper-half build
   retained here. No rung is raised by this prose revision.
4. **Seventeen-square reports retain their scopes.** T-153 is Overbeck’s conditional
   candidate optimality proof; T-154 is Fitzharding’s separate Lean formalization, not a
   formalization of T-153. Both stay `V0/C1/S5`. The verified bracket uses the exact
   endpoints in the [case record](../../../packing/frontier/n-017.md), including the
   strict lower bound $18641771/4000000$. The full capture/tree replay and full Lean
   build remain outstanding.
5. **The n=29 picture is evidence about its source transcription.** Its retained
   multiprecision check remains numerical.
   The advanced caption now points to the separate later T-009 and T-155 certificates,
   so it does not imply no exact feasibility evidence exists.
   Source: [n=29 case](../../../packing/frontier/n-029.md).
6. **Nagamochi’s historical role needs the later correction.** The bibliography retains
   the 2005 paper and adds the counterexample and Karakuş replacement argument for the
   square-minus-one family, within the scopes of T-083 to T-085. It no longer presents
   the old general lower-bound source as an unqualified current authority.
7. **The pricing protocol has an administrative disposition.** Exp-134 was unrun and
   marked blocked after reprioritization.
   The manuscript says it supplies no scientific verdict, replacing the literal claim
   that it has “no verdict.”
   Source:
   [exp-134](../../../packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-134-paired-full-support-pricing.md).
8. **Exact arithmetic is not the only rigorous prover arithmetic.** The ownership
   induction uses exact rationals; the interval branch-and-bound route uses rigorous
   outward rounding. The original global-proof cost paragraph said every prover used
   exact rationals despite describing the interval route earlier.
   The revised paragraph preserves both mechanisms and their soundness requirements.
9. **Historical measurements stay historical.** LP timings, scalar costs, the kink
   comparison and five-seed annealer outcomes remain, with their original sources and
   limitations. The conclusions no longer imply a present benchmark of every solver.
   The original assertion about every upper bound ever obtained is narrowed to the
   constructive upper bounds being taught; the first-case priority wording about oblique
   tilt is replaced by Stromquist’s specific restricted-orientation comparison.
10. **Algebraic representation and termination are qualified.** The primitive-element
    theorem does not itself provide a useful field-degree estimate.
    The reconstruction target is an isolated solution of the declared rational
    polynomial system; a free family parameter may be transcendental.
    The glossary now distinguishes a numerical quench’s stopping condition from
    certified membership in the mathematical terminal set.
    These clarifications preserve the original semialgebraic and singular-rank caveats.
11. **Evidence independence and regularization are explained without changing policy.**
    The added advanced section follows [Epistemics](../../../epistemics.md) and the
    [regularization policy](../policies/regularization-policy.md).
    It keeps side relation, drawing identity, evidence grade, credit and result novelty
    separate. T-155’s 59 certificates and T-156’s monotonicity example come from the
    [registered package](../../../packing/cases/regularized_bounds/README.md); a new
    certificate is not automatically a new packing.
12. **Recent intake remains intake.** The 14 October ledger explicitly verifies no
    certificate; the new lower-bound reviews state their own coverage limits.
    The text links those records without adopting their claims as standing bounds.
    T-157 and T-158 are used as examples because they are already in the results
    register, with their actual claim types and confirmation routes.

## Suggested Checks for Independent Review and Integration

The independent reviewer should check the explanatory additions, the changed claim
scopes above, and the preservation map, especially the two five-square objects, T-112’s
separate confirmation, T-153/T-154, and T-155’s side/identity/novelty distinctions.
This is author-prepared source, not an independently accepted scientific revision.

The coordinator should render both papers, check that explicit legacy anchors survive
sanitization, and inspect the long advanced tables and the basic page on mobile.
The plan lists the exact source-input, title, figure, version-reference, layout and
page-link contracts that need integration.
The added root filename must be explicitly allowed by the document-layout convention.
A PDF route, if offered, should be tested through the repository’s publication workflow.

These are remaining integration and review tasks, not reasons to discard technical
content or weaken existing assertions to make tests pass.

## Edits Applied

- Rewrote the basic paper around a beginner’s questions, with small cases and worked
  distinctions before project-specific machinery.
- Reordered the advanced material by dependency; retained technical derivations,
  bibliography, figures, glossary and notation; added threshold/dilation exposition,
  current evidence independence and regularization.
- Applied separate expression, claim, reasoning and purpose passes under Practical
  Prose; recorded meaning-bearing changes above.
- Preserved old heading destinations with direct links and supplied the coordinator’s
  integration contract.
- Kept one common-doc footer per authored document and used the project’s Flowmark
  formatter.

## Validation and Limits

The source audit compares the original manuscript with both new manuscripts.
It checks word counts, original heading landings, glossary/notation row keys, figure and
source link preservation, local target existence, and manuscript-to-manuscript
fragments. The final formatted-source audit has the following results.
These are text checks; no test suite, mathematical replay, site build, PDF build or
rendered visual inspection ran in this lane.
The dedicated worktree’s vendor checkout is uninitialized, and no environment was
installed.

### Source Audit Receipt

The comparison baseline is the original `TUTORIAL.md` at this worktree’s starting
`HEAD`. `git show HEAD:TUTORIAL.md | wc -w` reports **20,269 words**;
`wc -w TUTORIAL.md TUTORIAL-ADVANCED.md` reports **2,941** and **21,735**, respectively.
The basic paper is about one seventh of the original’s length.
The advanced paper remains long because it retains the technical derivations and
reference cards while adding the current verification and regularization explanations.
Its short opening repeats the problem definition and elementary bounds so it can be read
independently; its evidence-status recap supports the later proof examples.
It does not repeat the beginner’s full walkthrough.

A read-only, in-memory Python audit used the repository’s pinned `GithubSlugger` from
`vendor/kpress/src/kpress/format/_github_slugger.py` in the primary checkout, with the
project’s Python 3.14 interpreter.
It compared original heading slugs, table keys, figure paths and external citation
targets against the two manuscripts, then checked local Markdown links across the four
authored documents.

| Check | Result |
| --- | --- |
| Original heading fragments still reachable in the basic paper | 50 of 50; 48 explicit relocation landings and two retained heading destinations |
| Duplicate basic-page IDs | 0 |
| Original glossary row keys retained in advanced vocabulary | 60 of 60 |
| Original notation row keys retained in advanced notation | 50 of 50 |
| Original figures retained across both papers | 5 of 5 |
| Original external citation targets missing | 0 |
| Local links checked | 300; no missing targets |
| Markdown fragment links checked | 172; no missing destinations |
| Required common-doc footers | Exactly one in each of the four authored files |

`flowmark --auto` formatted only the four authored documents, using the installed
`/Users/levy/.local/bin/flowmark`. `git diff --check` passed without output.
The author changed only the two manuscripts, this review and the preservation plan; no
shared rendering, registry, policy, release or test file changed in this lane.
These checks establish source continuity, not rendered-anchor behavior or independent
scientific verification.
Those remain explicit integration and review checks above.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
