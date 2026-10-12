"""The grid-slack prototype on fixtures whose best drawing is known by hand.

Four unit squares scattered in a side-11/5 box can at best form a 2 x 2 block in a
corner, and the lower-left corner is the one nearest the start in L1: the view must put
them on exact halves there, at exactly the witness's side, decided on both exact routes,
with no house or stage total falling and every square paired one to one. A square turned
by `2 arctan(1/500)` (about 0.229 degrees) beside an axis square is straightened and
slid flush. A run directory under `witnesses/` is refused before anything is written.
When both ways of closing the tight set fail, the re-solve holds the unchanged squares at
their exact centres and tries again, and a literal past Python's integer-text limit moves
on to the next way rather than refusing the count.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from devtools import census_drawing_regularity as census
from devtools import regularize_grid_slack as slack
from devtools.regularize_evand import view_geometry

HALF = Fraction(1, 2)


def _basis_witness(
    rows: list[tuple[Fraction, Fraction, Fraction, Fraction]], side: str = "11/5"
) -> dict[str, Any]:
    """A rational centre-basis witness, in a side-11/5 box unless `side` says otherwise."""

    def text(value: Fraction) -> str:
        return str(value.numerator) if value.denominator == 1 else str(value)

    return {
        "id": "W-fixture",
        "n": len(rows),
        "side": side,
        "square_size": "1",
        "representation": "center-basis",
        "scalar": {"kind": "rational"},
        "coordinates": {
            "origin": "lower-left",
            "axes": "x-right-y-up",
            "angle_unit": "not-applicable",
        },
        "squares": [
            {"id": index, "center": [text(x), text(y)], "basis": [text(c), text(s)]}
            for index, (x, y, c, s) in enumerate(rows, start=1)
        ],
        "claim": {
            "coordinate_provenance": "verified",
            "method": "exact-algebraic",
            "limitations": "synthetic fixture",
        },
        "source": {"path": "tests/synthetic"},
    }


def scattered() -> dict[str, Any]:
    """Four axis squares, each a few hundredths to a seventh off a 2 x 2 corner block."""
    one, zero = Fraction(1), Fraction(0)
    return _basis_witness(
        [
            (HALF + Fraction(1, 20), HALF + Fraction(1, 20), one, zero),
            (Fraction(16, 10), HALF, one, zero),
            (HALF, Fraction(16, 10), one, zero),
            (Fraction(165, 100), Fraction(165, 100), one, zero),
        ]
    )


def tilted() -> dict[str, Any]:
    """An axis square on the floor and a square turned about 0.229 degrees beside it."""
    t = Fraction(1, 500)
    c, s = (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)
    one, zero = Fraction(1), Fraction(0)
    return _basis_witness([(HALF, HALF, one, zero), (Fraction(16, 10), Fraction(6, 10), c, s)])


def _centres(view: dict[str, Any]) -> list[tuple[Fraction, Fraction]]:
    _side, placements, _corners = view_geometry(view)
    return [(x, y) for x, y, _c, _s in placements]


def test_scattered_squares_close_into_the_nearest_corner_block() -> None:
    view, report = slack.regularize(scattered(), slack.Settings())
    assert view is not None
    assert report["relation"] == "same"
    (first,) = report["attempts"]
    assert first["placement"]["status"] == "placed"
    assert Fraction(view["side"]) == Fraction(11, 5)
    assert _centres(view) == [
        (HALF, HALF),
        (Fraction(3, 2), HALF),
        (HALF, Fraction(3, 2)),
        (Fraction(3, 2), Fraction(3, 2)),
    ]
    verdicts = first["exact"]["verdicts"]
    assert verdicts["exact_verify"]["passed"]
    assert verdicts["independent"]["passed"]
    drawn = census.regularity(view)
    assert drawn["axis_sides"] == [0, 0, 1, 2, 1]
    assert drawn["uneven_axis"] == 3
    measured = slack.measure(4, scattered(), view, [])
    assert measured["identity"]["one_to_one"] is True
    assert measured["totals_fall"] is False
    assert view["certificate"]["kind"] == "regularized-view"
    assert view["certificate"]["side_relation"] == "same"


def test_a_near_axis_square_is_straightened_and_slid_flush() -> None:
    view, report = slack.regularize(tilted(), slack.Settings())
    assert view is not None
    assert [row["square"] for row in report["straightened"]] == [2]
    assert report["straightened"][0]["degrees"] == pytest.approx(0.229183, abs=1e-6)
    assert view["squares"][1]["basis"] == ["1", "0"]
    assert _centres(view) == [(HALF, HALF), (Fraction(3, 2), HALF)]
    assert view["certificate"]["straightened"] == [2]
    drawn = census.regularity(view)
    assert drawn["near_axis"] == 0
    assert drawn["axis"] == 2
    measured = slack.measure(2, tilted(), view, [2])
    assert measured["identity"]["unnamed_turns"] == []


def test_nothing_is_straightened_past_the_threshold() -> None:
    view, report = slack.regularize(tilted(), slack.Settings(near_axis_degrees=0.1))
    assert view is not None
    assert report["straightened"] == []
    assert view["squares"][1]["basis"] != ["1", "0"]


def test_a_run_directory_in_the_record_is_refused() -> None:
    with pytest.raises(slack.GridSlackError):
        slack.run_one(1, slack.ROOT / "witnesses" / "scratch", slack.Settings())
    assert not (slack.ROOT / "witnesses" / "scratch").exists()


def test_a_run_writes_its_view_report_and_drawing(tmp_path: Path) -> None:
    report = slack.run_one(1, tmp_path, slack.Settings())
    directory = tmp_path / "n-001"
    assert (directory / "report.json").is_file()
    assert report["n"] == 1
    assert "measured" in report
    assert (directory / "view.yaml.gz").is_file()
    assert (directory / "drawing.svg").read_text(encoding="utf-8").startswith("<?xml")


def _row(coefficients: dict[int, int], rhs: Fraction, priority: tuple[int, ...]) -> Any:
    return slack.same.Row(
        "pair" if len(coefficients) > 1 else "wall",
        {column: Fraction(value) for column, value in coefficients.items()},
        rhs,
        1,
        {},
        priority,
    )


def test_only_the_witness_contacts_of_unchanged_squares_are_closed() -> None:
    frame = slack.same.exact_frame(scattered())
    # Squares 1 and 2 (columns 0 and 2) are 0.05 apart along x in the witness: a near
    # contact, not a contact. Square 2 sits on the floor (column 3): a contact.
    apart = _row({0: -1, 2: 1}, Fraction(1), (0, 0, 1))
    floor = _row({3: 1}, HALF, (1, 1, 1))
    kept, left = slack.closable([apart, floor], frame, changed=set())
    assert kept == [floor]
    assert left == [apart]
    kept, left = slack.closable([apart, floor], frame, changed={1})
    assert left == []


def test_a_left_open_row_the_solve_penetrates_is_closed_after_all() -> None:
    # x0 = 1/2 on the wall, x1 = x0 + 1 closed, x2 left open at 2.4 although x2 >= x1 + 1.
    wall = _row({0: 1}, HALF, (1, 0, 0))
    pair = _row({0: -1, 2: 1}, Fraction(1), (0, 0, 1))
    later = _row({2: -1, 4: 1}, Fraction(1), (0, 1, 2))
    generator = [(HALF, HALF), (Fraction(3, 2), HALF), (Fraction(12, 5), HALF)]
    solution, _promoted, _rounds, reopened = slack.settle_reopening(
        [pair, wall], [later], generator
    )
    assert reopened == 1
    assert solution.values[4] == Fraction(5, 2)


def test_no_bound_frame_below_the_witness_side() -> None:
    # n = 4's verified upper bound is 2, below the fixture's 11/5.
    assert slack.frame_for(scattered(), "bound") is None
    frame = slack.frame_for(scattered(), "same")
    assert frame is not None
    assert frame.side == Fraction(11, 5)


def beside_a_tilted_square() -> dict[str, Any]:
    """Two axis squares on the floor a tenth apart, and a square turned by
    `arctan(3/4)` (about 36.9 degrees) wedged into the opposite corner of a side-3 box:
    the placement slides the second axis square flush and leaves the tilted one alone."""
    one, zero = Fraction(1), Fraction(0)
    return _basis_witness(
        [
            (HALF, HALF, one, zero),
            (Fraction(16, 10), HALF, one, zero),
            (Fraction(23, 10), Fraction(23, 10), Fraction(4, 5), Fraction(3, 5)),
        ],
        side="3",
    )


def test_anchoring_substitutes_held_columns_and_keeps_every_gap() -> None:
    row = _row({0: -1, 2: 1}, Fraction(1), (0, 0, 1))
    values = {0: HALF, 2: Fraction(8, 5)}
    (held,) = slack.anchor([row], {0: HALF})
    assert held.coefficients == {2: Fraction(1)}
    assert held.gap({2: Fraction(8, 5)}) == row.gap(values) == Fraction(1, 10)
    (constant,) = slack.anchor([row], values)
    assert constant.coefficients == {}
    assert constant.gap({}) == Fraction(1, 10)
    generator = [(HALF, HALF), (Fraction(8, 5), HALF)]
    solution, _promoted, _rounds, _reopened = slack.settle_reopening(
        [row], [], generator, {0: HALF, 1: HALF}
    )
    assert solution.values[0] == HALF
    assert solution.values[2] == Fraction(3, 2)
    assert 0 not in solution.free_columns
    assert 1 not in solution.free_columns


def test_an_anchored_way_holds_the_unchanged_tilted_square_exactly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = slack.settle_variant

    def refusing(rows: str, **kwargs: Any) -> Any:
        settled = real(rows, **kwargs)
        if rows not in slack.ANCHORED:
            settled.refusal = settled.record["refusal"] = "penetrated: forced by the test"
        return settled

    monkeypatch.setattr(slack, "settle_variant", refusing)
    witness = beside_a_tilted_square()
    view, report = slack.regularize(witness, slack.Settings())
    assert view is not None
    settled = report["attempts"][0]["exact"]["settled"]
    assert [variant["rows"] for variant in settled] == [
        "witness-contacts",
        "all-tight",
        "anchored-tilted",
    ]
    assert settled[-1]["anchored"] == 1
    assert view["certificate"]["resolve"]["rows"] == "anchored-tilted"
    assert view["certificate"]["resolve"]["anchored_squares"] == 1
    assert _centres(view) == [
        (HALF, HALF),
        (Fraction(3, 2), HALF),
        (Fraction(23, 10), Fraction(23, 10)),
    ]
    verdicts = report["attempts"][0]["exact"]["verdicts"]
    assert verdicts["exact_verify"]["passed"]
    assert verdicts["independent"]["passed"]


def test_a_literal_past_the_digit_limit_tries_the_next_way(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = slack.same.same_side_witness
    calls: list[int] = []

    def too_long_once(*args: Any, **kwargs: Any) -> Any:
        calls.append(1)
        if len(calls) == 1:
            raise ValueError("Exceeds the limit (4300 digits) for integer string conversion")
        return real(*args, **kwargs)

    monkeypatch.setattr(slack.same, "same_side_witness", too_long_once)
    view, report = slack.regularize(scattered(), slack.Settings())
    assert view is not None
    settled = report["attempts"][0]["exact"]["settled"]
    assert settled[0]["refusal"].startswith("literal-too-long")
    assert settled[1]["refusal"] is None
    assert view["certificate"]["resolve"]["rows"] == settled[1]["rows"]
