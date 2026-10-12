"""The regularized views registered as verified upper bounds (T-147).

`devtools.register_regularized_bounds` retains each view whose exact side lies below its
case's verified upper bound, decides it on both maintained exact routes, makes three
controls of it, and writes the case records' verified upper lane. These tests hold the
committed receipts, the retained views and the case records to each other, the layer to
its own output, and the controls' construction to the outcomes it promises.
"""

from __future__ import annotations

import json
from decimal import Decimal
from fractions import Fraction

import pytest

from devtools import apply_exact_ceilings, render_case_verifiers
from devtools import register_regularized_bounds as registered
from devtools.apply_upper_bound_packets import normalized
from sqpack.assurance import bounds_agree_at_declared_precision


def test_the_receipts_the_views_and_the_records_agree() -> None:
    assert registered.problems() == []


def test_no_held_or_rehoused_count_is_registered() -> None:
    selection = json.loads(registered.SELECTION.read_text(encoding="utf-8"))
    assert 17 not in registered.committed()
    assert not set(registered.committed()) & registered.EXCLUDED
    assert set(selection["registered"]) == set(selection["candidates"]) - registered.EXCLUDED
    assert len(registered.REHOUSED) == 42


def test_each_side_lies_below_the_bound_it_replaced_and_at_or_below_t101s_side() -> None:
    """The registered side is below the ceiling the record held, never above the side of
    the earlier exact certificate of the same packing, and above the catalogue's closed
    form wherever it prints one: a ceiling of the same packing, not a smaller one."""
    for n, row in registered.committed().items():
        side = Fraction(row["side"])
        earlier = apply_exact_ceilings.bound_value(row["earlier_verified"])
        assert side < earlier, n
        if row["t101_side"] is not None:
            assert side <= Fraction(row["t101_side"]), n
        if row["printed_exact_form"]:
            assert row["above_exact_side_by"] > 0, n
        assert Fraction(Decimal(row["value"])) >= side, n


def test_the_display_is_exact_where_the_side_ends_and_a_ceiling_where_it_does_not() -> None:
    assert registered.display(Fraction(11, 2)) == "5.5"
    assert registered.display(Fraction(1, 3)) == "0." + "3" * 35 + "4"
    assert registered.display(Fraction(1, 2**40)) == format(
        registered.ceiling_decimal(Fraction(1, 2**40), registered.DISPLAY_PLACES), "f"
    )


@pytest.mark.parametrize("n", [28, 29, 37, 50, 204, 300])
def test_the_records_are_the_layer_applied_to_themselves(n: int) -> None:
    path = registered.FRONTIER / f"n-{n:03d}.md"
    text = path.read_text(encoding="utf-8")
    rendered = render_case_verifiers.refresh(registered.apply_case(n, text))
    assert normalized(rendered) == normalized(text)


@pytest.mark.parametrize("n", [28, 50, 69, 300])
def test_the_t101_layer_leaves_a_record_this_layer_owns(n: int) -> None:
    path = registered.FRONTIER / f"n-{n:03d}.md"
    text = path.read_text(encoding="utf-8")
    assert apply_exact_ceilings.apply_case(n, text) == text


def test_each_record_says_whether_its_bound_agrees_with_the_report() -> None:
    """A bound that disagrees with the report at the declared precision carries the
    ceiling section and a `mathematics` blocker; one that agrees carries neither."""
    for n, row in registered.committed().items():
        case = registered.case_front(n)
        agrees = bounds_agree_at_declared_precision(
            case["reported_upper_bound"], case["verified_upper_bound"]
        )
        assert agrees == row["agrees_with_report"], n
        body = (registered.FRONTIER / f"n-{n:03d}.md").read_text(encoding="utf-8")
        assert (registered.CEILING_HEADING in body) != agrees, n
        assert registered.SECTION in body, n
        assert registered.DATED in body, n


def test_every_control_reached_its_outcome_on_both_routes() -> None:
    receipt = json.loads(registered.CONTROLS.read_text(encoding="utf-8"))
    assert receipt["all_as_expected"]
    by_count: dict[int, set[str]] = {}
    for row in receipt["rows"]:
        by_count.setdefault(row["n"], set()).add(row["control"])
        if row["expect"] == "refused":
            assert not row["exact_verify"], row
            assert not row["independent"], row
    assert set(by_count) == set(registered.committed())
    assert all(len(kinds) == 3 for kinds in by_count.values())


def _two_squares(side: Fraction) -> dict[str, object]:
    """Two touching axis-parallel unit squares on the floor of a box of `side`."""
    return {
        "id": "W-control-pair",
        "n": 2,
        "side": registered.literal(side),
        "square_size": "1",
        "representation": "center-basis",
        "scalar": {"kind": "rational"},
        "coordinates": {
            "origin": "lower-left",
            "axes": "x-right-y-up",
            "angle_unit": "not-applicable",
        },
        "squares": [
            {"id": 1, "center": ["1/2", "1/2"], "basis": ["1", "0"]},
            {"id": 2, "center": ["3/2", "1/2"], "basis": ["1", "0"]},
        ],
        "claim": {
            "coordinate_provenance": "verified",
            "method": "exact-algebraic",
            "limitations": "A test fixture.",
        },
    }


def test_the_controls_refuse_an_overlap_and_a_shrink_and_accept_one_unit() -> None:
    view = _two_squares(Fraction(23, 10))
    assert registered.decide_view(view)["exact_verify"]["passed"]
    from sqpack.witness import exact_verify  # noqa: PLC0415

    outcomes = []
    for mutant, row in registered.control_views(view):
        first, _report = exact_verify(mutant)
        side, corners = registered.corners_of(mutant)
        second = registered.independent.check_squares(corners, side)
        outcomes.append(
            (
                row["control"],
                row["expect"],
                first["verification_passed"],
                second["verification_passed"],
            )
        )
    assert outcomes == [
        ("tightest-pair-overlapped", "refused", False, False),
        ("side-shrunk-past-clearance", "refused", False, False),
        ("side-shrunk-one-unit", "accepted", True, True),
    ]


def test_a_trailing_blocker_names_the_gap_and_what_would_close_it() -> None:
    row = {
        "value": "5.824444616674059297016873205016",
        "printed_side": "5.82444461667405",
        "printed_exact_form": None,
        "printed_exact_form_degree": None,
        "above_exact_side_by": None,
    }
    blocker = registered.trailing_blocker(row, ["E-kingbird-upper-register"])
    assert blocker["kind"] == "mathematics"
    assert "9.297016873205016e-15" in blocker["detail"]
    assert blocker["evidence"] == ["E-kingbird-upper-register"]
