# Review: Verification Gaps in the Drawn Packings and the Upper-Bound Register

**Date:** 13 October 2026. **Verdict: five standing gaps, each to be filled; no bound in
the register is wrong.** Every count’s verified upper bound rests on an exact
certificate. What falls short of the owner’s standard is what the project *draws* and
what it *reports*. Of the 324 drawings on the site’s atlas, 58 at the stack top (77 on
`main`) show a packing that is only numerically checked.
15 on each tree show an exactly verified packing at a side above the verified upper
bound. The case pages and the composites draw all 92 numerically checked witnesses on
both trees. At the exact 36-digit reading the project’s own regularizer makes, 79 of
those 92 are not packings at their printed sides, and all five read here at full
precision fail. 63 case records report a side that no exact certificate reaches.

The owner set the standard on 13 October 2026: “Every packing, even after
regularization, should be exactly verified”, where “valid means a valid packing with
equal or smaller side, with exact verification”, and asked that any verification gap
older than the regularization stack be documented “as a serious gap that should be
filled later.” This review measures both trees against that standard and records each
gap, with its counts, how it was measured and what filling it would take.

This review was written by an AI agent for the project’s coordinator.
Its relation to the results is `project`. It moves no rung, writes no record and changes
no drawing. It writes this file and its entry in the document map.

**The two trees.** `main` is `ea227e62d`. The *stack top* is `408e4c42f`, the head of
the regularization stack (pull request 559), read with `git show` and never checked out.
Witness files are identical on the two trees.
The stack changes 59 case records, the results register and the regularized layer.

**Evidential status.** Each finding is marked **measured** (computed here by the command
in [How This Was Measured](#how-this-was-measured)), **read** (taken from the record or
the code without recomputation) or **inferred**.

## The Standard Applied

A packing is **exactly verified** when an exact decision procedure — exact sign over the
rationals or over a number field, as `sqpack.witness.exact_verify` and the independent
checker `devtools.check_rational_witness_independent` decide — accepts every wall and
pair constraint at a stated side.
An interval-certified enclosure is rigorous but is not exact in this sense, and a
numerical check at any tolerance is neither.

Below, R is the case record’s reported upper bound and U its verified upper bound, the
best side the record verifies exactly.
A drawn packing is **valid** when it is exactly verified at a side no larger than U.
That is how the stack’s regularization policy records the owner’s answer (section 9,
question 13): a view is valid when both maintained exact routes accept it and its side
is at most U, the best side the record verifies, since the owner asked for a packing
“optimal as best as known”.
R cannot be the line.
It is a printed decimal that often truncates the optimum, and no exact packing may reach
it. Where R lies below U, that is its own gap (Gap 4).

## Summary of the Gaps

Counts out of 324.

| Gap | `main` | Stack top | Status |
| --- | ---: | ---: | --- |
| 1a. Site atlas draws a numerically checked witness | 77 | 58 | measured |
| 1b. Case pages, composites and survey thumbnails draw one | 92 | 92 | measured |
| 2a. Numerically checked witness, all known-best | 92 | 92 | measured |
| 2b. Of those, the axis tool’s exact 36-digit reading is no packing at the printed side | 79 (71 overlap, 8 too large) | 79 | read from the index |
| 2c. Of those, read exactly at full precision and found infeasible | 5 of 5 sampled | same files | measured |
| 3. Drawn exact view sits above U | 15 | 15 | measured |
| 4a. R below U: the reported side is not exactly certified | 63 | 63 | measured |
| 4b. U rests on an interval certificate, not an exact one | 1 (n = 29) | 0 | measured |
| 5a. Label stronger than the evidence | 0 | 0 | measured |
| 5b. Exact view labelled “numerically checked” | 15 | 34 | measured |

Site atlas validity against U, on `main`: 232 valid (176 exact witnesses, 56 views), 15
exactly verified above U, 77 not exactly verified.
At the stack top: 251 valid (176 exact witnesses, 75 views), 15 exactly verified above
U, 58 not exactly verified.
On the case pages and composites, both trees: 232 valid and 92 not exactly verified.
**Measured.**

No drawn exact packing anywhere has a side below U, and R is never above U.
**Measured.**

## What Each Surface Draws

**Read** from the renderers, and **measured** against the regularized index of each
tree.

| Surface | What it draws | Source |
| --- | --- | --- |
| Repository atlas drawings `packing/atlas/known-best/rendering/n-NNN.svg`, the composites `known-best-1-100` and `known-best-1-324`, the case pages, the frontier survey’s thumbnails | The known-best witness, at every count | [`build_known_best_atlas.py`](../../../packing/devtools/build_known_best_atlas.py), [`render_case_pages.py`](../../../packing/devtools/render_case_pages.py) through `render_frontier_page.packing_svg` |
| The site’s atlas grid, on the homepage and the atlas page | The regularized view where the index marks a count `regularized`; the witness everywhere else | [`overview_sections.atlas_regularized`](../../../packing/devtools/overview_sections.py) |

The known-best witnesses, `packing/witnesses/known-best/n-NNN.yaml`, are the same on the
two trees. **Measured.**

- **232 exact witnesses.** 231 carry rational coordinates (`exact-rational-sat`), and
  `n = 51` carries coordinates in a number field (`exact-number-field-sat`). Each side
  equals R exactly.
- **92 numerically checked witnesses.** All carry decimal centres and angles under
  `numerical-multiprecision` at 120 digits.
  78 come from Kingbird’s derived numerical facts and were checked at a tolerance of
  `1e-8`. The other 14 come from Francisco Couzo’s published files and were checked at
  `1e-12`. (An earlier summary gave `1e-12` for all 92; the files say otherwise.)
  None has a side equal to R.

The regularized index, `packing/atlas/known-best/regularized/index.json`, lists these
views. **Measured.**

| Tree | Views drawn | From a rational witness | From a decimal witness | `unchanged` | `refused` |
| --- | ---: | ---: | ---: | ---: | ---: |
| `main` | 71 | 56 | 15 (axis tool) | 181 | 72 |
| Stack top | 90 | 56 | 34 (26 Daniel’s regularizer, 6 grid slack, 2 axis tool) | 181 | 53 |

Every drawn view is recorded as decided exactly on two routes: the repository’s exact
verifier and the independent rational checker.
The deferred `regularized-views` job decides each one again
(`regularize_axis_components --verify-atlas`). **Read.**

## Gap 1. Drawn Packings That Are Not Exactly Verified

**Measured.** At these counts the drawing is a decimal witness that has passed a
numerical check, and no exact decision covers the pose that is drawn.

- **Site atlas, stack top, 58 counts:** 5, 10, 11, 17, 19, 27, 28, 38, 39, 40, 52, 53,
  55, 65, 67, 69, 82, 89, 101, 104, 109, 122, 124, 125, 128, 145, 147, 148, 149, 150,
  151, 170, 173, 174, 197, 200, 201, 202, 203, 204, 205, 226, 229, 231, 233, 235, 257,
  260, 262, 264, 265, 290, 291, 294, 296, 298, 299, 300. The coordinator measured the
  same list independently from the stack’s census.
- **Site atlas, `main`, 77 counts:** the 58 above plus 18, 29, 37, 41, 50, 54, 66, 71,
  83, 85, 87, 107, 171, 178, 198, 227, 230, 234, 293. The stack draws an exact view at
  these 19.
- **Case pages, composites and survey thumbnails, both trees, 92 counts:** every decimal
  witness, listed in the [appendix](#appendix-the-92-decimal-witnesses).
  These surfaces never draw a regularized view.

At every one of these counts the record holds a certificate at U, exact everywhere but
`n = 29` on `main` (Gap 4). The gap is that the drawing is not that certificate.
The appendix names the certificate for each count.
**Read.**

## Gap 2. Most Decimal Witnesses Fail an Exact Reading at Their Printed Sides

A numerically checked witness passes when no constraint is violated by more than the
tolerance.
The figures below show that this check hides real violations, and that most of
the 92 printed poses fail when their decimals are read exactly.

**The receipts understate the violations.** **Read** from the code, **measured** on five
witnesses. Each numerical receipt records `minimum_containment_clearance` and
`minimum_best_pair_gap`. `sqpack.witness._margin_summary` computes both with the
tolerance-aware sign the check uses, so a value replaces the running minimum only when
it is lower by more than the tolerance.
The recorded figures are therefore some value within `1e-8` (or `1e-12`) of the true
minimum, not the minimum itself.
At `n = 10` the receipt records 0 for both, while the exact reading below finds four
overlaps of `6.9e-30`. Six receipts record a negative figure:

| n | Source, tolerance | Receipt’s figure | Exact reading at the printed side |
| ---: | --- | --- | --- |
| 5 | Kingbird, `1e-8` | pair gap `−2.6e-100` | **4 overlaps**, pair gap `−6.86e-30` |
| 10 | Kingbird, `1e-8` | 0 and 0 | **4 overlaps**, pair gap `−6.86e-30` |
| 71 | Kingbird, `1e-8` | pair gap `−3.2e-100` | not read here; the axis tool’s reading overlaps |
| 106 | Couzo, `1e-12` | containment `−3.10e-16` | **34 wall violations**, clearance `−8.28e-16`; pairs separated by at least `1.98e-13` |
| 172 | Couzo, `1e-12` | containment `−3.15e-18` | **22 wall violations**, clearance `−5.09e-17`; pairs separated by at least `2.01e-13` |
| 257 | Kingbird, `1e-8` | pair gap `−1.5e-120` | not read here; the axis tool’s reading overlaps |
| 301 | Couzo, `1e-12` | containment `−3.24e-17` | **27 wall violations**, clearance `−5.14e-16`; pairs separated by at least `1.99e-13` |

The `n = 10` row records no negative figure and is included as the counterexample.

**Exact readings at the printed side.** **Measured.** Each sampled witness was read as
the exact rationals its decimal centres and side denote.
Each printed angle became the exact rotation built from its half-angle tangent rounded
to 60 digits, so that cos² + sin² = 1 exactly.
The resulting rational witness was decided with `sqpack.witness.exact_verify`. That
rounding moves a corner by less than `1e-59`, far below every margin found.
At `n = 5` a 150-digit tangent gives the same result.
All five sampled witnesses are refused.
The Kingbird pair overlaps at `5` and `10` are at the level of the 30-digit truncation
of `√2/2` in their printed sides.
The Couzo witnesses are pairwise disjoint but cross a wall by up to `8.3e-16`.

**The axis tool’s exact reading.** **Read** from the index on both trees.
For each decimal witness, `devtools.regularize_axis_components` builds the 36-digit
rational pose at centre dilation 1 and decides it exactly before regularizing.

- **71 overlap.** The tool refuses these with `promotion-overlap`, with between 1 and
  158 overlapping pairs each.
- **8 are packings only at a larger side.** Their extent exceeds the printed side by
  `9e-17` to `1.1e-15`: 106, 110, 152, 177, 206, 210, 241, 301.
- **13 are packings at the printed side**, after the tool’s translation to the
  lower-left corner: 26, 40, 65, 82, 101, 122, 145, 172, 182, 240, 268, 273, 297.

An overlap is independent of the side.
But 68 of the 71 refused witnesses print 100-digit centres, which the 36-digit reading
rounds. So the refusal decides the 36-digit pose, not the printed one, and the
full-precision sample above is what ties the two together.

**Two counts are infeasible by theorem.** **Inferred** from the record.
At `n = 5` and `n = 10` the case records hold s(n) proved, and the witness’s printed
side lies `4.8e-30` below the proved optimum.
No packing exists at that side, whatever the reading.

**Printed sides against R and U.** **Measured.**

- 33 decimal witnesses print a side below R, by `2.5e-50` to `2.0e-29`: a truncated
  closed form.
- 59 print a side above R. 30 of these are above by at least `1e-16`: the 16 counts
  whose R is Kingbird’s 14-decimal print, and the 14 Couzo witnesses at `3e-12` to
  `3.6e-11`.
- Against U, on `main`: 70 below, 21 above, 1 equal.
  At the stack top: 55 below, 21 above, 16 equal.
  There, the register result `T-154` moved U to the printed sides of witnesses whose
  exact views it registered.

**Inferred:** no witness side below R or U is a better packing.
Each is a rounded decimal of the packing whose exact certificate gives U; the
coordinator reached the same reading independently.

**The 14 Couzo counts are not the reported packing.** **Measured.** At 106, 110, 152,
172, 177, 182, 206, 210, 240, 241, 268, 273, 297 and 301, R = U is the side of Evan
Daniel’s exact optimum (`E-evand-exact-optima-2026-10-05-exact-replay`). The witness is
Couzo’s earlier decimal pose, `3e-12` to `3.6e-11` larger.

## Gap 3. Exact Drawings Above the Verified Bound

**Measured.** These site-atlas drawings are exactly verified, but at a side above U, so
they are not valid by the standard above.
All are views of decimal witnesses, and at every one R = U.

- **`main`, 15 counts:** 26, `5.5e-30` above a closed-form U, and the 14 Couzo counts
  106, 110, 152, 172, 177, 182, 206, 210, 240, 241, 268, 273, 297 and 301, `2.8e-12` to
  `3.6e-11` above U. All 15 are the axis tool’s views.
  At each, the record holds an exact certificate at U that the drawing is not.
- **Stack top, 15 counts:**
  - 18, 26, 66 and 85, `3.7e-31` to `5.5e-30` above a closed-form U. These are the
    status quo of the stack policy’s section 9, item 4 (“irrational optima”).
  - 87, `4.3e-16` above U.
  - The ten Couzo counts 106, 110, 152, 172, 182, 206, 241, 268, 297 and 301, each drawn
    at the witness’s side, `2.8e-12` to `3.6e-11` above U. Of these, 110 and 301 are the
    axis tool’s views.

At 177, 210, 240 and 273 the stack draws Daniel’s view at exactly U = R. Those drawings
are valid.

At 15 counts the stack draws an exact view at exactly U where R is below U: 29, 37, 41,
50, 54, 71, 83, 107, 171, 178, 198, 227, 230, 234 and 293. Those drawings are valid
under this standard.
What falls short there is the reported side, which belongs to Gap 4.

At 110 and 301 on both trees, and at 106, 152, 177, 206, 210 and 241 on `main`, the axis
tool’s view is exactly verified only at a side above the witness’s own printed side
(`fits_reported_side: false` in the index).
**Read.**

## Gap 4. Reported Sides the Register Does Not Exactly Certify

**Measured** over every case record’s `reported_upper_bound` and `verified_upper_bound`,
on both trees. Each closed form was evaluated to 100 digits with
`sqpack.kingbird_catalogue.evaluate_exact_form`.

- **Every count has an exact U.** All 324 verified upper bounds carry an exact form.
  - On `main`, 323 rest on `exact-algebraic` evidence.
    The other, `n = 29`, rests on `E-n029-interval-certified-upper`, a rigorous interval
    certificate that is not exact.
  - At the stack top all 324 rest on `exact-algebraic` evidence.
  - 175 counts rest on the exact grid replay (`E-basic-grid-upper`), with R equal to the
    grid side. These are not gaps.
- **R is below U at 63 counts, the same 63 on both trees:**
  - **47 with a closed-form R:** 50, 53, 54, 101, 104, 107, 109, 122, 124, 125, 145,
    147, 148, 149, 150, 151, 170, 171, 173, 174, 178, 197, 198, 200, 201, 202, 203, 204,
    226, 227, 229, 230, 231, 233, 234, 257, 260, 262, 264, 265, 290, 291, 293, 294, 296,
    298, 299. On `main`, U exceeds R by `2.2e-16` to `9.8e-15`. At the stack top `T-154`
    narrowed this to `1.4e-36` to `7.2e-15`. An exact certificate at R would need
    number-field arithmetic.
  - **16 whose R is a decimal only:** 11, 17, 28, 29, 37, 39, 41, 55, 69, 71, 83, 87,
    128, 205, 235, 300. Here R is Kingbird’s print truncated at 14 decimals, below the
    packing’s true side.
    The gap is `9.5e-16` to `1.0e-14` on `main` and `1.2e-16` to `9.3e-15` at the stack
    top. **Inferred:** no exact certificate of the catalogue’s packing can reach a
    truncated print, so the truncation, not the packing, is what falls short.
  - All 63 have a numerically checked witness.
    R exceeds U nowhere.
- **The record already says so, count by count.** Thirteen of the 16 decimal-only
  records say “The printed side itself is not certified here”, and all 47 closed-form
  records say that U is the certificate’s side rounded up at fourteen decimals (for
  example, [`n-028.md`](../../../packing/frontier/n-028.md)). The rule comes from
  [`catalogue_upper_bounds.py`](../../../packing/devtools/catalogue_upper_bounds.py):
  the verified value is the larger of the printed side and the certified side rounded up
  at the printed precision, and the record compares the two to one unit of the printed
  last place. Under that convention the 63 counts are agreements.
  Under the owner’s standard they are gaps.

## Gap 5. Labels

**Measured** against the rendering code: `build_known_best_atlas.frame_from_witness` and
`render_regularized_atlas.regularized_frame`.

- **No drawing is labelled more strongly than its evidence.** “(certified upper bound)”
  appears only where the drawn packing is exactly verified at the side the label states:
  an exact witness, or a view of one.
- **Views of decimal witnesses are labelled more weakly than their evidence:** 15 on
  `main`, 34 at the stack top.
  Each carries its source witness’s “(numerically checked)” although the view itself is
  exactly verified. The renderer does this on purpose.
  It carries the record’s tier so that a drawing never promotes one, and the stack’s
  regularization policy repeats the rule.
  The cost is that a reader cannot tell which drawings are exact.
- **Decimal witnesses keep a label that is literally true but misleading.**
  “(numerically checked)” on a witness whose exact reading overlaps — 71 at the 36-digit
  reading, and every one sampled at full precision — does not tell a reader that the
  drawn pose is not a packing.
  The tier vocabulary has no word for that finding.

## What the Record’s Own Tools Enforce

**Read** from each module’s docstring and code.

| Tool | What it enforces | What it does not |
| --- | --- | --- |
| `packing-witness check` (`sqpack.witness.numerical_check`) | Each decimal witness passes at its recorded precision and tolerance | Exact feasibility; true minima (Gap 2) |
| `packing-witness verify` (`exact_verify`) | Exact feasibility of rational and number-field witnesses at their sides | It refuses decimal geometry by design (`formal-certificate-missing`) |
| `devtools.check_rational_witness_independent` | An independent exact decision of rational-corner witnesses | Applies to promotions and views, never to the decimal houses |
| `devtools.regularize_axis_components --check-atlas` / `--verify-atlas` | The index against witnesses and views by digest (records tier); exact re-derivation and re-decision of every view (deferred `regularized-views` job) | Nothing about counts drawn from a witness |
| `devtools.render_regularized_atlas --check` | Drawings match views; a view whose recorded exact decision failed is refused | The side relation to R |
| `devtools.select_houses --check` | Fails where a reviewed register certificate at `C3` or above lies below a case’s U (passes on `main`: no house moves) | A house that is decimal while an exact certificate at U exists |
| `devtools.check_basic_bounds` | The exact grid replay behind `E-basic-grid-upper` | Anything tighter than the grid |
| `devtools.catalogue_upper_bounds` | Rational promotion of the Kingbird witnesses at 69, 83 and 87 | Other counts |
| `devtools.check_results` | The results register’s rungs, references and reviews | The relation of R, U and the drawn side |
| `devtools.render_certificate_reach` | Lower-bound fractional certificates’ reach | Upper bounds; not applicable here |

No check compares the drawn packing’s exact side with R, or fails when a drawing is a
decimal pose.

## Already Documented

**Read.** The new findings here are the drawn-packing gaps (1 and 3), the
tolerance-blurred receipts and full-precision infeasibility (2), and the totals.

- The per-count statements in the case records and the reviews of single imports cover
  the 63 uncertified reported sides one count at a time:
  [review of issue 227](review-2026-09-29-issue-227-upper-bound-packings.md),
  [review of Couzo 6042c56](review-2026-10-05-couzo-6042c56.md) and
  [the Kingbird intake at 69, 83 and 87](review-2026-10-05-kingbird-intake-n69-n83-n87.md).
- The rule that a drawing carries the record’s tier is in
  [`render_regularized_atlas.py`](../../../packing/devtools/render_regularized_atlas.py)
  and in section 1 of the stack’s `docs/project/policies/regularization-policy.md`.
  Section 9, item 4 of that policy (“irrational optima: the status quo”) covers 18, 26,
  66 and 85.
- [The upper-bound certification plan](../specs/active/plan-2026-09-22-upper-bound-certification-blocks.md)
  plans the certification of reported bounds.
- Beads: `think-75ll` (bridge numerical witnesses to exact certificates; P1, paused),
  `think-2716` (certify the reported upper bounds; P2, open), `think-tow1` (slackened
  rational promotion; P1, open) and `think-omqv` (register exact packings at the printed
  sides; carried out as `T-154` on the stack).
- `packing/defects.yaml` records no defect for any of these gaps.

## Filling the Gaps

Each gap is serious under the owner’s standard and is to be filled later.
In order of what it buys:

1. **Make every house exact** (Gaps 1b and 2). Replace each of the 92 decimal witnesses
   with an exact witness built from the certificate the record already holds at U.
   - 14 Couzo counts: Daniel’s rational optima, which the converter in
     [`evand_exact_certificates.py`](../../../packing/devtools/evand_exact_certificates.py)
     already turns into rational witnesses.
   - 60 counts on `main`: Daniel’s ceiling certificates.
     At the stack top, 58 of these rest on `T-154`’s registered exact packings instead,
     and 2 (150, 290) still on Daniel’s ceilings.
   - 18 counts: the exact constructions the record cites, written as
     `algebraic-number-field` witnesses, the form `n = 51` already uses.
     These are 5, 10, 11, 18, 19, 26, 27, 38, 40, 52, 65, 66, 67, 82, 85 and 89, from
     the modules under `packing/cases/`; 17, from the audited endpoint certificate of
     experiment 238; and 29, whose certificate on `main` is an interval enclosure and at
     the stack top a `T-154` packing.
     Of these, 11 lies in a field of degree 8.

   [`upper_bound_houses.py`](../../../packing/devtools/upper_bound_houses.py) and
   [`adopt_houses.py`](../../../packing/devtools/adopt_houses.py) are the existing
   machinery. A house change re-triggers review of any regularized view derived from the
   old witness.

2. **Draw exactly verified views at U** (Gaps 1a and 3). The regularization stack’s next
   layer, in progress on branch `claude/upbeat-ptolemy-1lxxx8`, draws views at U at the
   Couzo counts where the solve reaches it.
   Number-field views settle 18, 26, 66 and 85.

3. **Decide what R means where no exact certificate reaches it** (Gap 4).
   - For the 16 decimal-only counts, the reported side should become the exact side of
     the certified packing, with the catalogue’s print kept as the citation.
   - For the 47 closed-form counts, R can be certified only over the number field its
     closed form names, which needs the number-field views the stack defers
     (`think-yk2h`).

4. **Fix the receipts** (Gap 2). Make `_margin_summary` report true minima at the
   working precision, regenerate the 92 receipts, and record each witness’s
   full-precision exact-reading outcome beside its numerical one.
   The full exact reading of all 92 costs about 32 CPU-minutes, scaled from `n = 301`’s
   59 seconds.

5. **Gate it.** Build one tool that reproduces this review’s tables, as `OR-1` requires.
   It should fail when a drawing on any surface is not exactly verified at a side no
   larger than U, against an allowlist that only shrinks.
   It should report R below U separately.
   This review’s measurements ran as one-off scripts over the repository functions named
   below, and that tool replaces them.

6. **Decide the label** (Gap 5). Either let a view of a decimal witness state its own
   exact tier, or keep the record’s tier and add a mark that the drawn view is exact.
   This is an owner decision, because the current rule is deliberate.

## How This Was Measured

Everything ran in a worktree of `main` at `ea227e62d`, with the project interpreter
(CPython 3.14.7). The stack top was read with `git show` and `git archive` from
`origin/claude/busy-pascal-vgiccb-518` at `408e4c42f`.

- **Witness census:** each `packing/witnesses/known-best/n-NNN.yaml` was loaded for its
  `claim` (provenance, method, precision, tolerance), its `scalar.kind`, its `side` and
  its `certificate.result`. Witness files are byte-identical on the two trees: the
  stack’s diff touches no file under `packing/witnesses/`.
- **Register census:** the front matter of each `packing/frontier/n-NNN.md` was loaded,
  and R (its exact form where present, else its value) and U (its exact form) were
  evaluated to 100 digits with `sqpack.kingbird_catalogue.evaluate_exact_form`. The one
  named root, `n = 11`’s `root(P_trump11, …)`, was read at its printed enclosure.
  Two values are treated as equal when they agree to `1e-90`. Evidence methods come from
  `packing/frontier/evidence.yaml`.
- **Drawn packings:** each tree’s `regularized/index.json` names the drawn view; each
  view’s exact side was read from its gzip YAML. A view is exact when its entry’s
  `exact_verification.passed` holds; a witness is exact when its provenance is
  `verified`.
- **Exact readings:** for `n = 5, 10, 106, 172, 301`, as Gap 2 describes, decided with
  `sqpack.witness.exact_verify`; for `n = 5` also with a 150-digit tangent.
  They took between under a second and 59 seconds each.
- **House check:** `python -m devtools.select_houses --check` on `main` reported “0 of
  57 counts move”.

The scripts were scratch files and are not retained; item 5 of
[Filling the Gaps](#filling-the-gaps) replaces them with a tool.

## Appendix: The 92 Decimal Witnesses

Source: K is Kingbird’s derived numerical facts, C is Couzo’s files.
*Printed − R* is the witness’s printed side minus the reported side.
*Axis reading* is the axis tool’s 36-digit exact reading at dilation 1: “overlaps (k)”
with k failing pairs, “fits”, or the side excess it needs.
*Site draws* gives the witness, or a view and its side relative to U. *Exact certificate
at U* names the evidence behind U on each tree, which is the certificate an exact house
would be built from.

| n | Source | Tol. | Printed − R | Axis reading | Site draws, `main` | Site draws, stack | Exact certificate at U, `main` | Exact certificate at U, stack |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | K | 1e-8 | −4.8e-30 | overlaps (3) | witness | witness | Göbel n=5 | Göbel n=5 |
| 10 | K | 1e-8 | −4.8e-30 | overlaps (2) | witness | witness | Göbel n=10 | Göbel n=10 |
| 11 | K | 1e-8 | +4.2e-15 | overlaps (6) | witness | witness | Trump n=11 | Trump n=11 |
| 17 | K | 1e-8 | +9.5e-16 | overlaps (7) | witness | witness | n=17 endpoint | n=17 endpoint |
| 18 | K | 1e-8 | +3.7e-31 | overlaps (10) | witness | view, U +3.7e-31 | lifted Q(√7) | lifted Q(√7) |
| 19 | K | 1e-8 | −2.9e-30 | overlaps (2) | witness | witness | lifted Q(√2) | lifted Q(√2) |
| 26 | K | 1e-8 | +5.5e-30 | fits | view, U +5.5e-30 | view, U +5.5e-30 | Göbel off-centre | Göbel off-centre |
| 27 | K | 1e-8 | −4.8e-30 | overlaps (4) | witness | witness | Göbel strip | Göbel strip |
| 28 | K | 1e-8 | +9.3e-15 | overlaps (16) | witness | witness | Daniel ceiling | T-154 view |
| 29 | K | 1e-8 | +9.2e-15 | overlaps (17) | witness | view, at U | interval n=29 | T-154 view |
| 37 | K | 1e-8 | +1.2e-16 | overlaps (20) | witness | view, at U | Daniel ceiling | T-154 view |
| 38 | K | 1e-8 | −4.8e-30 | overlaps (6) | witness | witness | Göbel strip | Göbel strip |
| 39 | K | 1e-8 | +8.9e-15 | overlaps (20) | witness | witness | Daniel ceiling | T-154 view |
| 40 | K | 1e-8 | +6.0e-31 | fits | witness | witness | Göbel n=40 | Göbel n=40 |
| 41 | K | 1e-8 | +2.2e-15 | overlaps (15) | witness | view, at U | Daniel ceiling | T-154 view |
| 50 | K | 1e-8 | −4.3e-40 | overlaps (27) | witness | view, at U | Daniel ceiling | T-154 view |
| 52 | K | 1e-8 | −4.8e-30 | overlaps (6) | witness | witness | Göbel strip | Göbel strip |
| 53 | K | 1e-8 | −2.5e-50 | overlaps (17) | witness | witness | Daniel ceiling | T-154 view |
| 54 | K | 1e-8 | +1.7e-30 | overlaps (16) | witness | view, at U | Daniel ceiling | T-154 view |
| 55 | K | 1e-8 | +3.0e-15 | overlaps (26) | witness | witness | Daniel ceiling | T-154 view |
| 65 | K | 1e-8 | +4.8e-33 | fits | witness | witness | Göbel family | Göbel family |
| 66 | K | 1e-8 | +1.2e-30 | overlaps (3) | witness | view, U +1.2e-30 | lifted Q(√2) | lifted Q(√2) |
| 67 | K | 1e-8 | −4.8e-30 | overlaps (7) | witness | witness | Göbel strip | Göbel strip |
| 69 | K | 1e-8 | +8.9e-15 | overlaps (29) | witness | witness | Daniel ceiling | T-154 view |
| 71 | K | 1e-8 | +5.5e-15 | overlaps (25) | witness | view, at U | Daniel ceiling | T-154 view |
| 82 | K | 1e-8 | +4.8e-33 | fits | witness | witness | Göbel L | Göbel L |
| 83 | K | 1e-8 | +2.0e-15 | overlaps (30) | witness | view, at U | Daniel ceiling | T-154 view |
| 85 | K | 1e-8 | +9.1e-31 | overlaps (14) | witness | view, U +9.1e-31 | Göbel off-centre | Göbel off-centre |
| 87 | K | 1e-8 | +2.3e-15 | overlaps (36) | witness | view, U +4.3e-16 | Daniel ceiling | T-154 view |
| 89 | K | 1e-8 | −3.3e-33 | overlaps (36) | witness | witness | Göbel family | Göbel family |
| 101 | K | 1e-8 | +4.8e-33 | fits | witness | witness | Daniel ceiling | T-154 view |
| 104 | K | 1e-8 | −4.8e-30 | overlaps (10) | witness | witness | Daniel ceiling | T-154 view |
| 106 | C | 1e-12 | +9.1e-12 | side +3.5e-16 | view, U +9.1e-12 | view, U +9.1e-12 | Daniel optimum | Daniel optimum |
| 107 | K | 1e-8 | +1.1e-36 | overlaps (42) | witness | view, at U | Daniel ceiling | T-154 view |
| 109 | K | 1e-8 | −3.3e-33 | overlaps (37) | witness | witness | Daniel ceiling | T-154 view |
| 110 | C | 1e-12 | +2.8e-12 | side +8.9e-17 | view, U +2.8e-12 | view, U +2.8e-12 | Daniel optimum | Daniel optimum |
| 122 | K | 1e-8 | +4.8e-33 | fits | witness | witness | Daniel ceiling | T-154 view |
| 124 | K | 1e-8 | +1.2e-30 | overlaps (18) | witness | witness | Daniel ceiling | T-154 view |
| 125 | K | 1e-8 | −4.8e-30 | overlaps (10) | witness | witness | Daniel ceiling | T-154 view |
| 128 | K | 1e-8 | +7.0e-15 | overlaps (42) | witness | witness | Daniel ceiling | T-154 view |
| 145 | K | 1e-8 | +4.8e-33 | fits | witness | witness | Daniel ceiling | T-154 view |
| 147 | K | 1e-8 | +1.2e-30 | overlaps (18) | witness | witness | Daniel ceiling | T-154 view |
| 148 | K | 1e-8 | +1.2e-30 | overlaps (18) | witness | witness | Daniel ceiling | T-154 view |
| 149 | K | 1e-8 | −4.8e-30 | overlaps (14) | witness | witness | Daniel ceiling | T-154 view |
| 150 | K | 1e-8 | −1.3e-37 | overlaps (73) | witness | witness | Daniel ceiling | Daniel ceiling |
| 151 | K | 1e-8 | +1.4e-37 | overlaps (56) | witness | witness | Daniel ceiling | T-154 view |
| 152 | C | 1e-12 | +5.6e-12 | side +1.8e-16 | view, U +5.6e-12 | view, U +5.6e-12 | Daniel optimum | Daniel optimum |
| 170 | K | 1e-8 | −2.5e-31 | overlaps (45) | witness | witness | Daniel ceiling | T-154 view |
| 171 | K | 1e-8 | −4.3e-40 | overlaps (61) | witness | view, at U | Daniel ceiling | T-154 view |
| 172 | C | 1e-12 | +3.6e-11 | fits | view, U +3.6e-11 | view, U +3.6e-11 | Daniel optimum | Daniel optimum |
| 173 | K | 1e-8 | +1.2e-30 | overlaps (18) | witness | witness | Daniel ceiling | T-154 view |
| 174 | K | 1e-8 | −4.8e-30 | overlaps (18) | witness | witness | Daniel ceiling | T-154 view |
| 177 | C | 1e-12 | +1.4e-11 | side +5.5e-16 | view, U +1.4e-11 | view, at U | Daniel optimum | Daniel optimum |
| 178 | K | 1e-8 | +1.7e-30 | overlaps (33) | witness | view, at U | Daniel ceiling | T-154 view |
| 182 | C | 1e-12 | +3.4e-12 | fits | view, U +3.4e-12 | view, U +3.4e-12 | Daniel optimum | Daniel optimum |
| 197 | K | 1e-8 | +4.8e-33 | overlaps (1) | witness | witness | Daniel ceiling | T-154 view |
| 198 | K | 1e-8 | −4.3e-40 | overlaps (63) | witness | view, at U | Daniel ceiling | T-154 view |
| 200 | K | 1e-8 | +1.2e-30 | overlaps (61) | witness | witness | Daniel ceiling | T-154 view |
| 201 | K | 1e-8 | −4.8e-30 | overlaps (20) | witness | witness | Daniel ceiling | T-154 view |
| 202 | K | 1e-8 | −2.8e-31 | overlaps (6) | witness | witness | Daniel ceiling | T-154 view |
| 203 | K | 1e-8 | −3.3e-30 | overlaps (138) | witness | witness | Daniel ceiling | T-154 view |
| 204 | K | 1e-8 | −2.0e-29 | overlaps (55) | witness | witness | Daniel ceiling | T-154 view |
| 205 | K | 1e-8 | +8.2e-15 | overlaps (51) | witness | witness | Daniel ceiling | T-154 view |
| 206 | C | 1e-12 | +4.0e-12 | side +1.1e-15 | view, U +4.0e-12 | view, U +4.0e-12 | Daniel optimum | Daniel optimum |
| 210 | C | 1e-12 | +3.8e-12 | side +1.8e-16 | view, U +3.8e-12 | view, at U | Daniel optimum | Daniel optimum |
| 226 | K | 1e-8 | +4.8e-33 | overlaps (1) | witness | witness | Daniel ceiling | T-154 view |
| 227 | K | 1e-8 | +1.5e-37 | overlaps (92) | witness | view, at U | Daniel ceiling | T-154 view |
| 229 | K | 1e-8 | +1.2e-30 | overlaps (30) | witness | witness | Daniel ceiling | T-154 view |
| 230 | K | 1e-8 | +1.7e-37 | overlaps (147) | witness | view, at U | Daniel ceiling | T-154 view |
| 231 | K | 1e-8 | −4.8e-30 | overlaps (20) | witness | witness | Daniel ceiling | T-154 view |
| 233 | K | 1e-8 | −3.3e-30 | overlaps (154) | witness | witness | Daniel ceiling | T-154 view |
| 234 | K | 1e-8 | +1.4e-37 | overlaps (64) | witness | view, at U | Daniel ceiling | T-154 view |
| 235 | K | 1e-8 | +8.1e-15 | overlaps (43) | witness | witness | Daniel ceiling | T-154 view |
| 240 | C | 1e-12 | +6.1e-12 | fits | view, U +6.1e-12 | view, at U | Daniel optimum | Daniel optimum |
| 241 | C | 1e-12 | +1.3e-11 | side +7.8e-17 | view, U +1.3e-11 | view, U +1.3e-11 | Daniel optimum | Daniel optimum |
| 257 | K | 1e-8 | −2.5e-31 | overlaps (124) | witness | witness | Daniel ceiling | T-154 view |
| 260 | K | 1e-8 | +1.2e-30 | overlaps (101) | witness | witness | Daniel ceiling | T-154 view |
| 262 | K | 1e-8 | −4.8e-30 | overlaps (24) | witness | witness | Daniel ceiling | T-154 view |
| 264 | K | 1e-8 | −3.3e-30 | overlaps (158) | witness | witness | Daniel ceiling | T-154 view |
| 265 | K | 1e-8 | −3.3e-30 | overlaps (158) | witness | witness | Daniel ceiling | T-154 view |
| 268 | C | 1e-12 | +1.2e-11 | fits | view, U +1.2e-11 | view, U +1.2e-11 | Daniel optimum | Daniel optimum |
| 273 | C | 1e-12 | +1.0e-11 | fits | view, U +1.0e-11 | view, at U | Daniel optimum | Daniel optimum |
| 290 | K | 1e-8 | +4.8e-33 | overlaps (58) | witness | witness | Daniel ceiling | Daniel ceiling |
| 291 | K | 1e-8 | +4.8e-33 | overlaps (58) | witness | witness | Daniel ceiling | T-154 view |
| 293 | K | 1e-8 | −3.4e-37 | overlaps (90) | witness | view, at U | Daniel ceiling | T-154 view |
| 294 | K | 1e-8 | +1.2e-30 | overlaps (100) | witness | witness | Daniel ceiling | T-154 view |
| 296 | K | 1e-8 | −4.8e-30 | overlaps (26) | witness | witness | Daniel ceiling | T-154 view |
| 297 | C | 1e-12 | +4.5e-12 | fits | view, U +4.5e-12 | view, U +4.5e-12 | Daniel optimum | Daniel optimum |
| 298 | K | 1e-8 | −3.3e-30 | overlaps (158) | witness | witness | Daniel ceiling | T-154 view |
| 299 | K | 1e-8 | −2.0e-29 | overlaps (66) | witness | witness | Daniel ceiling | T-154 view |
| 300 | K | 1e-8 | +3.5e-15 | overlaps (59) | witness | witness | Daniel ceiling | T-154 view |
| 301 | C | 1e-12 | +4.6e-12 | side +5.6e-16 | view, U +4.6e-12 | view, U +4.6e-12 | Daniel optimum | Daniel optimum |

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
