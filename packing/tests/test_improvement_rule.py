"""The improvement rule is stated once, in the regularization policy, and judged by one
function.

The owner, 13 October 2026: "tie is fine on exactness or regularity as long as it is
making some improvement wrt our regularity or heuristic goals", codified in the policy's
section 11. The selection's `RULE` and the default pictures' check read the statement from
the policy, and the statement names every goal `judge` decides, so neither can drift from
the other without a test or the check failing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from devtools import improvement_rule as rule
from devtools import regularize_select as select


def test_the_policy_states_the_rule_once_and_names_every_goal() -> None:
    words = rule.statement()
    assert words.startswith("A view improves on a drawing")
    assert rule.problems() == []
    assert set(rule.GOAL_WORDS) == set(rule.GOALS)


def test_the_selection_prints_the_policy_statement() -> None:
    assert rule.statement() in select.RULE
    assert rule.SECTION in select.RULE
    assert select.MEASURES == rule.MEASURES
    assert select.compare is rule.compare


def test_a_statement_that_drops_a_goal_fails(tmp_path: Path) -> None:
    policy = tmp_path / "policy.md"
    stated = rule.statement().replace("exactly verified", "verified")
    policy.write_text(f"intro\n\n{rule.BEGIN}\n\n{stated}\n\n{rule.END}\n", encoding="utf-8")
    assert rule.problems(policy) == [
        (
            f"the improvement rule in {rule.POLICY_DOCUMENT} does not name the goal "
            "exactness ('exactly verified')"
        )
    ]


@pytest.mark.parametrize(
    "text",
    [
        "no markers at all\n",
        f"{rule.END}\nthe rule\n{rule.BEGIN}\n",
        f"{rule.BEGIN}\none\n{rule.END}\n{rule.BEGIN}\ntwo\n{rule.END}\n",
        f"{rule.BEGIN}\n\n{rule.END}\n",
    ],
)
def test_a_statement_not_marked_once_is_refused(tmp_path: Path, text: str) -> None:
    policy = tmp_path / "policy.md"
    policy.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match="improvement rule"):
        rule.statement(policy)
    assert len(rule.problems(policy)) == 1


@pytest.mark.parametrize(
    ("gains", "worse", "flags", "reason"),
    [
        (["light_axis"], [], {}, ""),
        # Ties on the other goals are fine.
        (["house_total"], [], {"exact_gain": False}, ""),
        # Exactness is a goal: a numerically checked witness replaced, every measure tied.
        ([], [], {"exact_gain": True}, ""),
        # So is the side.
        ([], [], {"smaller": True}, ""),
        # A tie on every goal is no improvement.
        ([], [], {}, "no gain"),
        # Worse on any goal is no improvement, whatever it gains.
        (["light_axis"], ["hues"], {"exact_gain": True}, "worse on hues"),
        (["light_axis"], [], {"larger": True}, "worse on side"),
    ],
)
def test_worse_on_none_and_better_on_one(
    gains: list[str], worse: list[str], flags: dict[str, bool], reason: str
) -> None:
    """An empty reason is an improvement; any other names why it is not one."""
    judged = rule.judge(
        gains,
        worse,
        smaller=flags.get("smaller", False),
        larger=flags.get("larger", False),
        exact_gain=flags.get("exact_gain", False),
    )
    assert judged.improves is (not reason)
    assert judged.reason == reason


def test_only_the_rule_s_measures_are_judged() -> None:
    with pytest.raises(ValueError, match="not measures"):
        rule.judge(["symmetry"], [], smaller=False, larger=False, exact_gain=False)
