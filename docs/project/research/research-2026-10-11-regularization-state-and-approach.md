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
noise the drawing makes visible: a row a few hundredths off its wall renders light, and
a tilted band whose angles differ in the twelfth place splits into several hues.

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

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
