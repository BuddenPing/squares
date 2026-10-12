"""A project document's place and name say what kind of document it is (think-mv16)."""

from __future__ import annotations

import pytest

from devtools import check_documentation
from devtools.check_documentation import _layout_problems

LOOSE = "sits loose in docs/project/; put it in the directory for its kind"
CAPITALS = "has capitals in its name; use lowercase kebab-case"

# Exercise the rule directly; a whole document-map fixture would hide the case.
# pyright: reportPrivateUsage=false


@pytest.fixture(autouse=True)
def nothing_pending(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_documentation, "LAYOUT_PENDING", frozenset())


def test_documents_in_their_places_pass() -> None:
    assert (
        _layout_problems(
            {
                "README.md",
                "docs/project/README.md",
                "docs/project/guides/verification-tooling.md",
                "docs/project/handoffs/handoff-2026-09-04-block-close.md",
                "docs/project/reviews/review-2026-10-04-n11-optimality-paper-v0.1.4-changes.md",
                "docs/project/specs/active/spike-2026-08-25-n5-motion-lab.md",
                "packing/campaign/hypotheses/H-093-n11-scalar-61-16-certificate.md",
                "packing/campaign/explorations/X048-session-171-raw-row-support/d1-report.md",
            }
        )
        == []
    )


def test_a_loose_project_document_is_refused() -> None:
    """The case that prompted the rule: a new handoff beside the directories."""
    loose = "docs/project/handoff-2026-10-10-polynomial-pr-stack.md"
    assert _layout_problems({loose}) == [f"{loose}: {LOOSE}"]


def test_a_dated_directory_wants_its_kind_and_date() -> None:
    undated = "docs/project/reviews/stromquist-helper-arguments-math-review.md"
    misfiled = "docs/project/handoffs/review-2026-09-07-misfiled.md"
    plan = "docs/project/specs/active/plan-2026-10-11-documentation-organization.md"
    assert _layout_problems({undated, misfiled, plan}) == [
        f"{misfiled}: is not named handoff-YYYY-MM-DD-topic.md",
        f"{undated}: is not named review-YYYY-MM-DD-topic.md",
    ]


def test_capitals_need_a_convention_behind_them() -> None:
    playbook = "packing/atlas/known-best/FIGURE-PLAYBOOK.md"
    report = "packing/campaign/explorations/X048-session-171-raw-row-support/D1_REPORT.md"
    exploration = "packing/campaign/explorations/X-015-the-map-and-the-three-programs.md"
    assert _layout_problems({"AGENTS.md", playbook, exploration, report}) == [
        f"{playbook}: {CAPITALS}",
        f"{report}: {CAPITALS}",
    ]


def test_the_pending_list_only_shrinks(monkeypatch: pytest.MonkeyPatch) -> None:
    """An entry is excused while it breaks the rule, and refused once it no longer does."""
    monkeypatch.setattr(
        check_documentation, "LAYOUT_PENDING", frozenset({"SYNOPSIS.md", "TUTORIAL.md"})
    )
    assert _layout_problems({"SYNOPSIS.md", "TUTORIAL.md"}) == []
    assert _layout_problems({"SYNOPSIS.md", "docs/project/guides/tutorial.md"}) == [
        "layout allowlist entry no longer needed: TUTORIAL.md"
    ]
