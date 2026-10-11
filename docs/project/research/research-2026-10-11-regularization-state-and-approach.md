# Research: Regularizing Every Known-Best Packing for Display

**Date:** 2026-10-11 (last updated 2026-10-11)

**Author:** Joshua Levy, with Claude (session_017JNnKDwL74rnktr9s8BdjP)

**Status:** Complete (spikes and recommendations; the full run is not started)

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
101, 129, 146, 200, 324), records the current layer has no view of (5, 10, 11, 17, 37,
51), the T-146 counts whose identity failed one to one (129, 292), and the generator’s
known failure (261). “Light” below means squares that share at most one whole side, as
the house renderer counts them.
Outcomes are reported in the words the owner asked for on 11 October 2026 (policy
section 4, “How a decision is reported”): **admitted**, **held** (a visible improvement
waiting on the record), **refused** (a visible change that fails a rule), **no change**
(the picture would not change, whatever row matched) and **no view** (the generator
produced nothing). The row that decided is given with each.

| $n$ | Witness | Outcome (policy row) | Angle classes | Light squares | Four-side squares | What moved |
| --- | --- | --- | --- | --- | --- | --- |
| 5, 10 | decimal, Göbel family | no change (row 4; same side impossible) | 2 | unchanged | unchanged | nothing visible |
| 11 | decimal | no change (row 10; $10^{-33}$ off the witness) | 2 → 2 | 6 → 6 | 1 → 1 | nothing visible |
| 17 | decimal | no change (row 3: a candidate $10^{-22}$ below the bound) | 3 → 3 | unchanged | unchanged | nothing visible |
| 26 | decimal | **admitted** (10) | 2 → 2 | 1 → 0 | 7 → 8 | one rattler, 0.31, onto the grid |
| 37 | decimal | held (3): register first, $9.9 \times 10^{-15}$ below | 4 → 4 | unchanged | unchanged | 7 squares, up to 0.16 |
| 51 | $\mathbb{Q}(\sqrt{2})$ | no change (row 4; no rational frame) | 2 | unchanged | unchanged | nothing visible |
| 70 | rational (Xu) | held (3): T-146’s side, $1.5 \times 10^{-10}$ below | 6 → 4 | 21 → 16 | 33 → 35 | 10 moved, 6 turned |
| 101, 200 | decimal | no change (row 3: candidates about $10^{-14}$ below) | 2 → 2 | unchanged | unchanged | nothing |
| 129 | rational | held (3): T-146’s side, $1.3 \times 10^{-10}$ below | 8 → 6 | 27 → 19 | 79 → 79 | 20 moved (up to 0.87), 2 turned |
| 146 | rational | held (3): T-146’s side, $9.8 \times 10^{-11}$ below | 3 → 3 | 38 → 35 | 80 → 80 | 24 moved |
| 261 | rational (Xu) | no view (1): the exact solve finds it not jammed | 2 | unchanged | unchanged | nothing |
| 292 | rational (Rehwaldt after Couzo) | **admitted (10)** | **24 → 9** | **132 → 54** | **84 → 198** | 102 moved (up to 0.42), 17 turned |
| 324 | grid | no change (5) | 1 | 0 | 324 | nothing |

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
  Those drawings already read cleanly, so leaving them as they are costs nothing
  visually.
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

**Pilot 2: where upstream merges most.** Ten counts chosen from upstream’s best-choice
list by how many rotation groups it merges, including three the current layer refuses
(66, 87, 260).

| $n$ | Witness | Outcome (policy row) | Angle classes | Light squares | Four-side squares | What moved |
| --- | --- | --- | --- | --- | --- | --- |
| 66 | decimal | **admitted** (10) | 2 → 2 | 0 → 0 | 33 → 33 | 24 squares by up to 0.025, into the packing’s symmetry |
| 86, 127 | rational | no view (1): the exact solve finds the newer witness not jammed | — | — | — | nothing |
| 87 | decimal | held (3): register first, about $10^{-14}$ below | 3 → 3 | 16 → 16 | 49 → 49 | 6 squares, up to 0.003 |
| 102 | rational | held (3): T-146’s side, $7.9 \times 10^{-11}$ below | 4 → 3 | 29 → 26 | 46 → 46 | 15 moved, 1 turned |
| 126 | rational | **admitted (10)** | **5 → 2** | **26 → 7** | **51 → 55** | 15 moved, 3 turned |
| 206 | decimal (Couzo) | held (4): its side is exactly the verified bound, not the witness’s | **44 → 4** | **135 → 26** | **32 → 144** | 96 moved, 40 turned |
| 260 | decimal | no change (row 3: a candidate about $10^{-14}$ below) | 2 → 2 | 0 → 0 | 188 → 188 | nothing |
| 267 | rational | held (3): register first, $2.5 \times 10^{-11}$ below | 9 → 5 | 41 → 37 | 196 → 196 | 31 moved, 10 turned |
| 295 | rational | refused (7): 22 per-square counts fall | 2 → 2 | **62 → 3** | **101 → 166** | 122 moved |

It cost 1,598 CPU-seconds and 933 seconds of wall time at three workers; the exact solve
at $n = 260$ alone took 801 s.

Three cases decide how the policy should read:

- **$n = 206$ is the clearest picture of what regularization is for.** Near-axis noise
  gives the source 44 angle classes, so the drawing scatters colour across a region that
  is a grid; the regularized view has 4 classes and a dark carpet.
  Its side is not the witness’s printed side, but it is **exactly the verified upper
  bound**: the certificate’s side and the case record’s bound are the same rational,
  $232189979115498488075628916091 / 15625000000000000000000000000$, because T-098 made
  that bound from Evan Daniel’s exact solve of this same packing.
  Row 4 holds it as a side other than the witness’s, but it certifies nothing the
  register does not already hold, and it passes every other check: no square’s count
  falls, the pairing is one to one, and the largest move is 0.37.
- **$n = 295$ improves on every histogram total** (light squares 62 to 3, four-side 101
  to 166) and is refused because 22 individual counts fall: one square loses a house
  contact and a row of squares loses a stage contact each.
  Strict per-square non-regression, written for the axis tool’s single slides, is too
  strict for a generator that moves a whole band; this is a case for review.
- **$n = 86$ and 127 fail in the exact solve** on the newer witnesses the record now
  holds, which upstream never solved.
  The current layer’s views stand there.

**The `fewest` variant** (owner question 1), run at 129 and 292 from the same solves:

| $n$ | Variant | Rotation groups | Identity | Four-side squares | Outcome |
| --- | --- | --- | --- | --- | --- |
| 129 | `conservative` | 10 → 6 | one to one | 79 → 79 | held (3) |
| 129 | `fewest` | 10 → 4 | **not one to one** | **79 → 53** | held (3) |
| 292 | `conservative` | 24 → 9 | one to one | 84 → 198 | admitted (10) |
| 292 | `fewest` | 24 → 7 | one to one | 84 → 198 | alternate (8) |

`fewest` merges two more groups at each count and, at 129, loses 26 four-side squares
and the one-to-one pairing T-146’s review also found missing.
It buys little for the colour conventions and costs identity.

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
6. **The decision table is right about soundness and too blunt about drawings.** Of 25
   pilot counts it admits 4 (26, 66, 126, 292). Eight are held: by T-146’s refinements
   rediscovered and by rounding below the bound (row 3), or by a view exactly at the
   verified bound (row 4, $n = 206$). One is refused for per-square regressions while
   every total improved (row 7, $n = 295$). None of those is a soundness problem.
   Nine change nothing visible, among them the Göbel family and $n = 51$, which would
   need a number field, and three give no view because the exact solve fails (86, 127,
   261).
7. **`conservative` is the right variant.** `fewest` adds a group merge or two and, at
   $n = 129$, costs a quarter of the four-side squares and the one-to-one identity.

## Comparison Matrix

| Criterion | Axis components (`regularize_axis_components/2`) | Evan Daniel’s certificate alone | Evan Daniel + same-side re-solve (recommended) | `fewest` variant | Number-field views |
| --- | --- | --- | --- | --- | --- |
| Side of the drawing | The witness’s, exactly | Dilated, $S^{\ast}(1 + 10^{-20})$ | The witness’s, exactly, where rotations stay rational | As either | The exact optimum |
| Near-axis tilts and slack | Straightens within $10^{-4}$ rad, slides one axis at a time | Fixed by the LP and merges | Fixed | Fixed | Fixed |
| Tilted bands and hue classes | Untouched | Merged | Merged, same side | Merged further | Merged |
| Symmetry | None imposed | Imposed where feasible | Kept from the view | Kept | Kept |
| Decimal witnesses | Refuses 73 | Reaches all | Reaches those whose printed side is not truncated | As left | Reaches the Göbel family |
| Non-regression | Measured per square | Not measured | Measured, by the driver | Measured | To be measured |
| Identity | Same squares by construction | Sampled path test upstream | Measured one to one | Fails at 129 | To be measured |
| Cost for 1..324 | About 800 CPU-s | 3 to 4 CPU-h | About 7 CPU-h (pilot fit) | Similar | Not built |
| Status | In the layer (68 views) | T-146’s fifteen | Built this session; pilot only | Measured | think-yk2h |

## Options Considered

### Option A: Keep the Axis Tool Only

**Description:** the status quo; regularize only straight squares and slack.

**Pros:** sound by construction; already gated; cheap.

**Cons:** leaves every tilted band’s hue noise, imposes no symmetry, and cannot touch
the 73 refused decimal records; at $n = 206$ it leaves 42 of 44 angle classes.

### Option B: Evan Daniel’s Regularizer Through the Same-Side Re-Solve

**Description:** the vendored generator (`conservative`, `coincide`, source orientation)
on the KKT point, each view re-solved over $\mathbb{Q}$ at the witness’s side, decided
on the maintained exact routes, measured, and classified; the axis tool kept as fallback
and as the non-regression reference.

**Pros:** reaches tilted structure and hue classes at the record’s exact side; every
view is exact and verified here; identity and shading are measured, not asserted.

**Cons:** about 7 CPU-hours for a full run; same side is impossible at Göbel-family
decimals; at counts where the witness is not at its optimum the re-solve moves the
packing and the view lands below the bound instead.

### Option C: Draw Evan Daniel’s Certificates As They Are

**Description:** admit the dilated certificates as drawings.

**Pros:** every count gets a view; no re-solve.

**Cons:** reverses the 2 October ruling; a dilated side certifies something the register
does not say, except where it equals the bound exactly.

### Eliminated Options

- **Loosening the renderer’s tolerance:** reaches only the precision band (65 squares
  atlas-wide) and makes the drawing lie about contacts.
- **Hand-editing coordinates:** the policy forbids it; every pose comes from a generator
  and an exact re-solve.
- **`fewest` as the default:** measured above; alternates only.

## Recommendations

Adopt Option B as the standard procedure for every result, with four amendments to the
policy and two changes to the record made first.
Everything below is a proposal for the owner; nothing in it has been applied.

**Settle the record before the full run.**

1. **Adopt registered refinements as the atlas witnesses** where the register already
   holds a lower exact side than the case record (T-146 at 15 counts, and any import in
   flight, such as #476 at 267). Then the run regularizes the credited packing at its
   own side instead of rediscovering it; at 70, 102, 129 and 146 the same-side re-solve
   should then succeed, which the next pilot must confirm.
2. **Register the exact packings at the printed sides in one batch.** Wherever the
   same-side view is exact at a witness’s printed side and that side is below the
   verified bound (37, 87, 101, 200 and 260 in the pilots; 17 waits on the $n = 17$
   intake hold, think-x4v4), one register result with a `regularizations` item per count
   closes the gap between reported and verified and lets the drawings in.
   This is owner question 3 in its current, much smaller form.

**Amend the decision table** (policy section 4):

3. **Row 4:** a view whose exact side equals the verified upper bound is admissible as a
   drawing (relation `bound`), since it certifies exactly what the register holds.
   This admits $n = 206$ and every T-098 or T-101 count where the regularizer reproduces
   the certified side.
4. **Row 7:** when per-square counts fall but neither rule’s totals fall (no fewer
   four-side squares, no more light squares), send the view to review instead of
   refusing it. Keep refusal when a total falls.
5. **Row 5:** a view within $10^{-9}$ of the witness with no square turned is
   `unchanged`, so a $10^{-33}$ difference ($n = 11$) does not create a file.
6. **Question 1:** `conservative` only, as the policy already defaults.

**Run it in three batches** (1–108, 109–216, 217–324), each with its receipt, its
gallery and a review record per decision, as the epic’s plan already says.
The automated pass admits row 10; the reviewer sees rows 7 to 9 and the gallery’s
flagged tie-breaks.
Where both generators admit a view, keep Evan Daniel’s and record the
axis tool’s beside it.

**Leave alone, deliberately:** the Göbel-family decimal records and $n = 51$, which are
already regular in the drawings and need a number field to be framed exactly
(think-yk2h); and the counts where the exact solve fails (86, 127, 261), where the axis
tool’s view or the witness stands.

**Effort.** About 7 CPU-hours for all 324 counts by a fit to the 25 pilot counts (cost
grows roughly as $n^{2.3}$; the exact solve dominates and has a heavy tail: 801 s at
$n = 260$), so 2 to 3 hours of wall time at three or four workers, mostly in the third
batch. Review: if a tenth to a fifth of counts reach the queue, 30 to 60 gallery entries
for the owner, a few minutes each.

## Next Steps

- [ ] Owner: answer the amendments and the two record changes above (think-pn0e).
- [ ] Adopt the register’s lower exact certificates as the atlas witnesses, T-146 at its
  15 counts first, and run the full pass only after the imports in flight at the same
  counts (#470, #476, #481, #483, #488, #489) land, since a changed witness lapses every
  review (think-cb34).
- [ ] Register the exact packings at printed sides in one batch (think-omqv).
- [ ] Amend the policy’s decision table, then teach `devtools.regularize_evand.classify`
  the amendments (think-up3h).
- [ ] The index contract for both generators (think-k35c), then batch 1 with its gallery
  and review records (think-ux1v).
- [ ] Give `arrangement_gap` a spatial index; it took 72 s of 553 at $n = 292$
  (think-fkmn).
- [ ] Record every regularization the project makes with the packing’s provenance, in
  the register’s `regularizations` terms (owner, 11 October 2026). The driver already
  writes the record per count; the index contract and admission carry it into the layer
  (think-k35c, now a blocker of the full run).
- [ ] After the full run: an explainer paper in the project’s own format, rendered by
  kpress like the $n = 11$ lower-bounds explainer, citing Evan Daniel’s work and
  summarizing this project’s changes with before/after figures (think-scua).

## Methodology

The record’s history comes from a read of the atlas README, X-049, the regularized
index, the reviews of T-098 and T-146, the assessment, the policy, Evan Daniel’s method
log and the beads of epics think-los0 and think-cdud, with every count checked against
the files. The spikes ran `devtools.regularize_evand` at the vendored pin on this host
(four cores, shared), outputs kept outside the repository; the gallery was rendered from
them with `devtools.regularize_gallery`. The cost fit is a least-squares line in log-log
over the 21 pilot counts with $n \ge 26$; it is an estimate, not a measurement of the
full run.

## References

- [Regularization policy](../policies/regularization-policy.md): the obligations and the
  decision table this document proposes to amend.
- [Assessment of Evan Daniel’s process](research-2026-10-11-evand-regularization-assessment.md):
  how upstream works, and the adaptation plan these tools carry out.
- [Atlas README, “The regularized views”](../../../packing/atlas/known-best/README.md#the-regularized-views):
  the layer and the 2 October ruling.
- [X-049](../../../packing/campaign/explorations/X-049-families-shading-and-the-large-n-limit.md):
  why grid squares render light, and the axis tool.
- [Review of T-146](../reviews/review-2026-10-10-evand-regularized-certificates.md): the
  first regularizations the register carries.
- [Evan Daniel’s `search/regularize`](https://github.com/evand/square-packing/tree/675a5eaa8712542daac8b4515b0f69ad7044df44/search/regularize)
  (MIT), vendored under `vendor/evand-regularize/`.
- The tools: `packing/devtools/regularize_evand.py`, `regularize_same_side.py`,
  `regularize_gallery.py`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
