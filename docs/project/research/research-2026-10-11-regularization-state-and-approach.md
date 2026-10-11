# Research: Regularizing Every Known-Best Packing for Display

**Date:** 2026-10-11 (last updated 2026-10-11)

**Author:** Joshua Levy, with Claude (session_017JNnKDwL74rnktr9s8BdjP)

**Status:** In Progress

**Bead:** think-pwmi (epic think-cdud).

## Overview

The atlas draws each known-best packing of $n$ unit squares, $n = 1..324$, with the
house renderer: a square’s hue is its angle class and its shade is how many of its four
sides it shares whole with a wall or a same-angle neighbour.
Under those two conventions a packing’s regular structure (rows, blocks, strips,
symmetric tilted bands) should read at a glance as a few uniform hue families in dark,
even shades. It often does not, because the witnesses the record holds carry slack and
noise the drawing makes visible: a row a few hundredths off its wall renders light, a
square tilted a few hundredths of a degree off the axis leaves the axis hue altogether,
and a tilted band whose angles differ by more than a microradian splits into several
hues.

**Regularization** redraws a packing the record already holds so that it reads cleanly,
without changing its side, its evidence tier or its credit.
This document collects what the project has done about it so far, what each approach
fixed and could not fix, what the spikes of 11 October 2026 showed on fifteen counts,
and the standard approach recommended for regularizing every result: an automated pass
under the [regularization policy](../policies/regularization-policy.md), with judgment
reserved for the cases the automation cannot decide.

The owner’s request (11 October 2026): regularize all current results “using something
similar to what Evan Daniel has done”, with a standard policy and automation wherever
possible and judgment on the trickier cases, so that the results look right in the
diagrams’ colour conventions.

## Questions to Answer

1. What makes a known-best drawing look irregular in the house conventions, and how much
   of it is the packing and how much the witness’s representation?
2. What has the project tried, what did each approach fix, and what did each leave?
3. What does Evan Daniel’s process add, and what does it cost in the record’s terms
   (side, identity, credit)?
4. On the pilot counts, what changes, and does the result look cleaner by the house
   measures: fewer hue classes, more full-side contacts, no square lighter than before?
5. What is the standard procedure for all 324 counts: which counts it can settle
   automatically, which need review, and which need a different route (an algebraic
   field, or a register result first)?

## Scope

**In scope:** the display layer for the known-best atlas and case pages; the two
generators (`regularize_axis_components/2` and Evan Daniel’s vendored regularizer); the
side, identity, shading and labelling rules; the spikes run on 11 October 2026; the plan
for a full run.

**Out of scope:** new upper bounds as such (a certificate below the verified bound is a
register result and goes through the import runbook, not this document); proofs of local
optimality; the renderer’s palette.

## Findings

### How the House Conventions Read a Packing

Two renderers draw packings, and they decide hue and shade differently.

|  | House renderer (atlas, website, case pages) | Stage rule (workbench) |
| --- | --- | --- |
| Code | `packing/src/sqpack/render/color.py` | `packages/workbench/src/core/geometry.ts` `contactFacts` |
| Hue | Angle classes seeded at $10^{-6}$ rad and merged where full-side contacts link them; right angles pinned to hue 0 (green), 45 degrees to hue 1, the rest by class size | Half-degree angle classes |
| Shade | 4 minus the number of sides shared whole with a wall or a same-class neighbour, both ends within $2 \times 10^{-6}$ | Centres a side apart within 0.01, angles within half a degree |
| What it exposes | Any slack above $2 \times 10^{-6}$, and any tilt above a microradian | Slack above a hundredth; tilts above half a degree |

So the house drawing is strict: it shows the witness exactly as retained.
A row 0.03 off its wall is light; an “axis” square tilted 0.01 degrees is not green; two
squares of one tilted band that differ by $10^{-5}$ rad are two hues.
Nothing in the drawing distinguishes a real gap from representation noise, which is why
the layer exists.

### Why Drawings Look Irregular

The census of 2 October 2026 (X-049, “Why Grid Squares Render Light”) settled the first
question: light shading is not inexact arithmetic.
Of 45,468 green (axis-aligned) squares in the atlas, 7,725 rendered light:

- **5,272 structural:** they border a tilted square, a hole or a staggered row, and
  should stay light.
- **2,419 slack:** they sit beside a real gap or sideways shift of $2 \times 10^{-5}$ to
  0.5 in the retained coordinates.
  Almost all are in records that came from optimizer packets (Couzo, de Winter): at
  $n = 102$ every one of 69 green squares was light, with the top row 0.0298 from the
  wall.
- **34 in the precision band**, missing contact by less than ten times the renderer’s
  tolerance.

Where squares do touch, the arithmetic is fine (median contact residual 0, largest
$2 \times 10^{-6}$). The slack is in the packings as retained: optimizers stop when the
side stops improving, and a square that carries no load is left wherever it was.

Three other sources of irregularity matter for hue rather than shade:

- **Near-axis tilts.** Float optimizers almost never return an exactly zero angle: at
  $n = 301$, 131 squares sit between $10^{-6}$ rad and 0.68 degrees.
  Each leaves the green class; 265 squares atlas-wide are not green for this reason
  alone.
- **Angle noise inside tilted bands.** Evan Daniel’s exact solve groups angles by exact
  equality and finds 2,400 distinct rotation groups over the 324 records, 1,172 after
  merging; $n = 66$ goes from 31 groups to 2. Not every split is noise: $n = 175$ has a
  true 0.801-degree column, and whether $n = 71$’s two-class split is load-bearing is
  open (H-050).
- **Decimal witnesses.** 106 of the 324 witnesses are decimal (most from the Kingbird
  catalogue). Rounded to 36-digit rationals, 73 of them overlap by a sliver, so no exact
  frame exists at the record’s side without changing it.

### What Has Been Tried

**`regularize_axis_components/2`** (this project, 2 October 2026, X-049 “Exact
Regularization”). Straighten every square within $10^{-4}$ rad of the axis, slide each
axis square one axis at a time toward its lattice slot until it meets an exact contact,
hold any move that lowers a house or stage count (its own or a neighbour’s), and verify
the result twice over $\mathbb{Q}$ at the witness’s side.
It is sound at the same side by construction, and it is the only generator that measures
non-regression. Today it changes 68 records, leaves 182 unchanged and refuses 74; on the
68 it changes, light green squares fall from 4,666 to 2,609 with no regression, and 149
squares are held. It cannot touch tilted structure, impose symmetry, merge hue classes,
or frame a decimal witness that overlaps at dilation 1.

**Dilation** (`--smallest-dilation`, measured 2 October 2026). Scaling the decimal
witnesses’ rational poses by $1 + 10^{-p}$ until they verify frames all 89 then refused,
but changes the side, and changed only two squares’ shading.
The atlas README’s ruling of that day refused it: a dilated view certifies a side the
register does not hold, which is a tier promotion under a drawing’s name.

**Evan Daniel’s regularizer** (`search/regularize`, 9 and 10 October 2026, vendored here
at `675a5ea`). Re-solve the packing to an 80-digit KKT point of minimizing the side;
hold the angles and side fixed and move the centres by a translation LP, so every LP
point is a packing; impose the largest container symmetry; choose coincident faces with
a MILP; merge free squares’ angles into existing groups, and undetermined groups too
(`conservative` path-tests each merge; `fewest` also merges determined groups within 5
degrees); refine and verify at 80 digits; write a rational certificate dilated by
$1 + 10^{-20}$. It reaches tilted structure, symmetry and the decimal records, and its
lists change 147 records (the project’s tool, 68). Its cost in the record’s terms: its
side is never the witness’s; its “same packing” is a sampled numerical path test; and at
three of T-146’s fifteen counts no symmetry pairs its squares one to one with the
credited packing.

**T-146** (10 October 2026). Fifteen of Evan Daniel’s regularized certificates were
below the register’s bound and became register results, the first to carry a typed
`regularizations` credit.
The review accepted them for finite feasibility only and measured 10 to 239 squares
moved beyond $10^{-3}$.

**Same-side exact re-solve** (planned in the assessment’s slice 3, built in this
session). Take the regularized view’s angles in the witness’s own exact rotation frame,
find the contacts tight at the generator’s point, and solve them over $\mathbb{Q}$ at
the witness’s own side.
Where every rotation is rational in the witness’s frame this turns Evan Daniel’s view
into a `same`-side view; it is the step that lets “clean” and “no side changed” hold
together.

**Proposed, not built:** exact compaction of the remaining slack squares inside a fixed
tilted structure (think-qun0), releasing the 149 held squares by joint moves
(think-mkyx), and views over $\mathbb{Q}(\sqrt{2})$ and other fields for the refused
decimal records (think-yk2h). A renderer-side fix, loosening the house tolerance, would
reach only the precision band (34 squares then, 65 now), so it was never pursued.

### Rules Already Decided

- **A regularized drawing changes no side, frontier value, evidence tier or credit**,
  and never replaces the witness (epic think-los0, 2 October 2026; the index’s policy
  line; the regularization policy, section 1).
- **Non-regression:** no square’s house or stage count may fall (X-049; policy
  obligation 4).
- **No dilated frames** (atlas README, 2 October 2026; policy decision-table row 4).
- **A certificate below the verified bound is a register result first** (policy section
  1, row 3).
- **Identity is measured, not asserted:** the record says “the same packing” in its own
  voice only with a `measured` basis (results schema; policy section 2).
- **Credit:** the packing stays its finder’s; the regularization is credited by
  `regularizations` items; Evan Daniel’s method is credited whenever his code made the
  view (policy section 7; the vendored README).
- **The website shows regularized drawings only, with no badges**, and its legend keeps
  only tilt colours and contact shades (owner, 5 and 9 October 2026).

### The Spikes of 11 October 2026

**The pipeline.** `devtools.regularize_evand` drives the vendored code at `675a5ea`: the
witness written at full precision as upstream’s input, the exact solve, the regularizer
(`conservative`, `coincide`, source orientation), the certificate imported and decided
on three exact routes, `devtools.regularize_same_side` to bring the view to the
witness’s own side over $\mathbb{Q}$, identity by `arrangement_gap`, the house and stage
contact histograms, and the policy’s decision table.
`devtools.regularize_gallery` draws each count’s source, regularized view and current
layer view with the house renderer.
Run outputs stay outside the repository; nothing in the record changed.

**Pilot 1: the policy’s edge cases.** Fifteen counts: the epic’s pilot set (10, 26, 70,
101, 129, 146, 200, 324), the refused-kind controls (5, 10, 11, 17, 37, 51), the T-146
counts whose identity failed one to one (129, 292), and the generator’s known failure
(261). “Light” below means squares that share at most one whole side, as the house
renderer counts them.

| $n$ | Witness | Outcome (policy row) | Angle classes | Light squares | Four-side squares | What moved |
| --- | --- | --- | --- | --- | --- | --- |
| 5, 10 | decimal, Göbel family | refused (4): same side impossible | 2 | unchanged | unchanged | nothing visible |
| 11 | decimal | admit (10) | 2 → 2 | 6 → 6 | 1 → 1 | nothing visible |
| 17 | decimal | candidate (3), side $10^{-22}$ below the bound | 3 → 3 | unchanged | unchanged | nothing visible |
| 26 | decimal | admit (10) | 2 → 2 | 1 → 0 | 7 → 8 | one rattler, 0.31, onto the grid |
| 37 | decimal | candidate (3), $9.9 \times 10^{-15}$ below | 4 → 4 | unchanged | unchanged | 7 squares, up to 0.16 |
| 51 | $\mathbb{Q}(\sqrt{2})$ | refused (4): no rational frame | 2 | unchanged | unchanged | nothing visible |
| 70 | rational (Xu) | candidate (3), solved view $1.5 \times 10^{-10}$ below | 6 → 4 | 21 → 16 | 33 → 35 | 10 moved, 6 turned |
| 101, 200 | decimal | candidate (3), about $10^{-14}$ below | 2 → 2 | unchanged | unchanged | nothing |
| 129 | rational | candidate (3), solved $1.3 \times 10^{-10}$ below | 8 → 6 | 27 → 19 | 79 → 79 | 20 moved (up to 0.87), 2 turned |
| 146 | rational | candidate (3), solved $9.8 \times 10^{-11}$ below | 3 → 3 | 38 → 35 | 80 → 80 | 24 moved |
| 261 | rational (Xu) | refused (1): the exact solve finds it not jammed | 2 | unchanged | unchanged | nothing |
| 292 | rational (Rehwaldt after Couzo) | **admit (10)** | **24 → 9** | **132 → 54** | **84 → 198** | 102 moved (up to 0.42), 17 turned |
| 324 | grid | unchanged (5) | 1 | 0 | 324 | nothing |

Identity was one to one at every count that produced a view.
The run cost 857 CPU-seconds and 670 seconds of wall time at two workers.
At $n = 292$ the stages took 240 s (exact solve), 49 s (regularizer), 22 to 32 s (each
exact route), 170 to 206 s (same-side re-solve) and 72 s (`arrangement_gap`).

**What the pilot shows.**

- **Where the packing has a tilted band assembled by an optimizer, the change is large
  and exactly what the colour conventions need.** At $n = 292$ the band’s 24 hue classes
  become 9, the light squares fall from 132 to 54, and squares with all four sides
  shared rise from 84 to 198, at the record’s exact side.
  The current layer reaches 124 there.
- **Where the packing is a Göbel-style 45-degree family or a clean grid, there is little
  to do.** At 5, 10, 11, 17, 51, 101, 200 and 324 nothing visible moves.
  Those drawings already read cleanly, and their refusals cost nothing visually.
- **Re-solving finds a lower packing nearby.** At 70, 129 and 146 the exact solve lowers
  the side by about $10^{-10}$ and turns a tilted band by up to 0.0115 degrees.
  No exact rotation of the witness matches the turned band, so the same-side re-solve
  refuses, and the regularized view is a `solved` certificate below the case record’s
  bound. Those three sides equal T-146’s registered certificates, which the case records
  have not yet adopted as their bound.
  Starting the regularizer from the witness’s own pose instead (`--frame witness`) did
  not help: upstream’s 80-digit verification finds overlaps of about $10^{-10}$ there.
- **Row 3 is mostly rounding.** At 17, 37, 101 and 200 the same-side view is exact at
  the witness’s printed side, which lies $10^{-22}$ to $10^{-14}$ below a verified bound
  that is an exact certificate’s side rounded up at fourteen decimals.
  Each is technically a new verified bound, so the policy holds the drawing until it is
  registered.

<!-- PILOT-2 -->

## Key Insights

1. **The record’s side is the binding constraint, and it sorts the 324 counts into four
   kinds.** A rational witness (217) can be regularized at its own side over
   $\mathbb{Q}$. A decimal witness whose printed side is at or above its optimum can be
   regularized at its printed side.
   A Göbel-family decimal witness, whose printed side truncates an irrational optimum,
   has no rational packing at that side at all.
   The algebraic witness at $n = 51$ needs its own field.
   The same-side re-solve’s survey of $n = 1..80$ shows this split exactly: every
   rational witness reaches `same`, 15 of 25 decimal witnesses do, and the 10 that do
   not are the Göbel family.
2. **The house renderer is strict, so regularization must be exact.** It counts a shared
   side only when both ends match within $2 \times 10^{-6}$ and merges angle classes
   only within $10^{-6}$ rad.
   A float snap would leave squares one rounding away from contact.
   An exact re-solve over $\mathbb{Q}$ closes contacts with residual zero and makes
   equal angles literally equal, which is what the renderer rewards.
3. **Most of the visible gain is in optimizer-packet records**, the same ones X-049
   found slack in. The Kingbird and Göbel-family drawings are already regular.
4. **Some “candidates” are the register’s own results seen again.** A regularization run
   rediscovers registered-but-unadopted refinements (T-146) and the rounding gap between
   a printed side and its verified bound.
   Both should be settled in the record before a full run, so the run’s candidate list
   means something.
5. **Two generators are complementary.** Evan Daniel’s reaches tilted structure,
   symmetry and angle merges; the project’s tool measures non-regression square by
   square. At $n = 292$ Evan Daniel’s view has fewer light squares than the project’s
   current view (54 against 87) and more four-side squares (198 against 124); at 70 and
   129 the project’s current view changes nothing visible.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
