"""The regularization policy's improvement rule: its one statement, and the judgement it
states.

The owner, 13 October 2026: "tie is fine on exactness or regularity as long as it is
making some improvement wrt our regularity or heuristic goals", and "that should be
codified in our regularization standards doc". So the rule is written once, in section 11
of the regularization policy (`POLICY`), between the two markers below, and everything
that applies it reads it from there: question 14 of the policy points to it,
`devtools.regularize_select` prints it in its `RULE`, and `devtools.default_drawings`
prints it with its check. Nothing else restates it.

What the statement says, `judge` decides. Its goals are

- **regularity**, the seven measures (`MEASURES`): five from the house renderer's
  colouring of a drawing (`census_drawing_regularity.regularity`), fewer being better --
  light, uneven and near-axis squares, distinct angle classes and hues -- and the house
  and stage totals of full shared sides (`regularize_evand.contact_partners`), more being
  better. `compare` reads them, as the selection always has;
- **the side**: a smaller exact side is better and a larger one worse;
- **exactness**: an exactly verified view is better than a numerically checked witness.
  Every view the layer draws is exactly verified, so exactness is never worse.

A view improves on a drawing when it is worse on none of these and better on at least one;
ties on the others are fine, and a tie on every one is no improvement. `GOAL_WORDS` names
the words the statement uses for each goal, so a goal added here and not to the policy,
or taken out of the policy and not here, fails `problems`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
POLICY_DOCUMENT = "docs/project/policies/regularization-policy.md"
POLICY = REPO / POLICY_DOCUMENT
#: Where the statement stands, as a link from the repository's root.
SECTION = f"{POLICY_DOCUMENT}#11-the-improvement-rule"
BEGIN = "<!-- BEGIN RULE: improvement (devtools.improvement_rule) -->"
END = "<!-- END RULE: improvement -->"

#: The house renderer's colouring of a drawing, fewer being better.
DRAWING_MEASURES = ("light_axis", "uneven_axis", "near_axis", "classes", "hues")
#: Full shared sides under the house and stage rules, more being better.
CONTACT_MEASURES = ("house_total", "stage_total")
MEASURES = DRAWING_MEASURES + CONTACT_MEASURES
FEWER_IS_BETTER = frozenset(DRAWING_MEASURES)
#: The two goals beside the measures.
SIDE = "side"
EXACTNESS = "exactness"
GOALS = (*MEASURES, SIDE, EXACTNESS)
#: The words the statement uses for each goal.
GOAL_WORDS = {
    "light_axis": "light",
    "uneven_axis": "uneven",
    "near_axis": "near-axis",
    "classes": "angle classes",
    "hues": "hues",
    "house_total": "house",
    "stage_total": "stage",
    SIDE: "smaller exact side",
    EXACTNESS: "exactly verified",
}


@cache
def statement(policy: Path = POLICY) -> str:
    """The rule as the policy states it, on one line: the text between the markers."""
    text = policy.read_text(encoding="utf-8")
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError(f"{POLICY_DOCUMENT} must state the improvement rule once, marked")
    start, end = text.index(BEGIN) + len(BEGIN), text.index(END)
    if end < start:
        raise ValueError(f"{POLICY_DOCUMENT} closes the improvement rule before opening it")
    words = " ".join(text[start:end].split())
    if not words:
        raise ValueError(f"{POLICY_DOCUMENT} marks an empty improvement rule")
    return words


def problems(policy: Path = POLICY) -> list[str]:
    """What keeps the statement from being the rule `judge` applies."""
    try:
        words = statement(policy)
    except (OSError, ValueError) as error:
        return [str(error)]
    return [
        f"the improvement rule in {POLICY_DOCUMENT} does not name the goal {goal} ({phrase!r})"
        for goal, phrase in GOAL_WORDS.items()
        if phrase not in words
    ]


def compare(
    view: Mapping[str, int | None], drawing: Mapping[str, int | None]
) -> tuple[list[str], list[str]]:
    """The measures on which a view is better and worse than a drawing; a measure either
    side lacks is not compared."""
    gains: list[str] = []
    worse: list[str] = []
    for key in MEASURES:
        mine, theirs = view.get(key), drawing.get(key)
        if mine is None or theirs is None or mine == theirs:
            continue
        better = mine < theirs if key in FEWER_IS_BETTER else mine > theirs
        (gains if better else worse).append(key)
    return gains, worse


@dataclass(frozen=True)
class Judgement:
    """A view against a drawing, goal by goal."""

    better: tuple[str, ...]
    worse: tuple[str, ...]

    @property
    def improves(self) -> bool:
        """The rule: worse on no goal and better on one."""
        return bool(self.better) and not self.worse

    @property
    def reason(self) -> str:
        """Why it is no improvement, in words; empty when it is one."""
        if self.worse:
            return f"worse on {', '.join(self.worse)}"
        return "" if self.better else "no gain"


def judge(
    gains: Sequence[str],
    worse: Sequence[str],
    *,
    smaller: bool,
    larger: bool,
    exact_gain: bool,
) -> Judgement:
    """The rule over every goal, from the measures' comparison (`compare`), whether the
    view's exact side is smaller or larger than the drawing's, and whether it replaces a
    numerically checked witness with an exactly verified view."""
    unknown = sorted((set(gains) | set(worse)) - set(MEASURES))
    if unknown:
        raise ValueError(f"not measures of the rule: {unknown}")
    return Judgement(
        better=(*gains, *((SIDE,) if smaller else ()), *((EXACTNESS,) if exact_gain else ())),
        worse=(*worse, *((SIDE,) if larger else ())),
    )
