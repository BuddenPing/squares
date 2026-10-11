"""The 11 October 2026 house adoption: derivation, drawing custody and the case records."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from devtools import adopt_houses as adopt
from devtools import select_houses as select
from devtools import upper_bound_houses as houses
from sqpack.yamlio import safe_load


@pytest.fixture(scope="module")
def selections() -> dict[int, select.Selection]:
    return select.select()


def test_no_confirmed_reviewed_side_is_left_below_its_case(
    selections: dict[int, select.Selection],
) -> None:
    """After the adoption the derivation moves nothing: every case is at its house."""
    assert [n for n, selection in selections.items() if selection.moves] == []


def test_every_adopted_case_holds_the_derived_smallest_side(
    selections: dict[int, select.Selection],
) -> None:
    for n, result in houses.ADOPTED.items():
        best = selections[n].candidates[0]
        assert best.result == result
        assert selections[n].case.verified == best.side == houses.side(n)


def test_regularizations_leave_the_packing_with_its_finder(
    selections: dict[int, select.Selection],
) -> None:
    assert selections[153].candidates[0].regularizes == "T-136"
    assert selections[103].candidates[0].regularizes == "T-138"
    assert selections[70].candidates[0].regularizes == "T-125"
    assert adopt.CREDITS[153].found_by == (adopt.SQUISH,)
    assert adopt.CREDITS[70].found_by == (adopt.XU,)
    assert adopt.CREDITS[103].improved_by == ("Mishapolk", adopt.DANIEL)


def _candidate(result: str, side: Fraction, published: str) -> select.Candidate:
    return select.Candidate(
        result=result,
        n=7,
        side=side,
        source_key=f"[{result}]",
        published=published,
        report_evidence=(),
        confirming_evidence=(f"E-{result.lower()}",),
        regularizes=None,
    )


def test_ties_go_to_the_earlier_finder_then_the_earlier_entry() -> None:
    later = _candidate("T-200", Fraction(5, 2), "2026-10-10")
    earlier = _candidate("T-300", Fraction(5, 2), "2026-10-09")
    smaller = _candidate("T-400", Fraction(9, 4), "2026-10-11")
    assert min([later, earlier], key=select.precedence) is earlier
    assert min([later, earlier, smaller], key=select.precedence) is smaller
    first = _candidate("T-100", Fraction(5, 2), "2026-10-10")
    assert min([later, first], key=select.precedence) is first


def test_a_case_keeps_its_own_house_where_nothing_is_below(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry: dict[str, Any] = {
        "id": "T-900",
        "kind": "upper-bound",
        "verification": "V3",
        "confirmation": "C3",
        "scope": {"n_values": [7]},
        "attribution": {"source_keys": ["[test]"], "published": "2026-10-10"},
        "evidence": ["E-test-replay"],
        "reviews": [{"verdict": "accepted", "covers": ["T-900"]}],
    }
    evidence = {
        "E-test-replay": {
            "claim": "upper-bound",
            "assurance": "verified",
            "origin": "replayed-here",
            "replay_status": "passed",
        }
    }
    monkeypatch.setitem(select.reports.HOUSES, "[test]", lambda _n: Fraction(3))
    monkeypatch.setattr(select, "_side", lambda _key, _n: Fraction(3))
    case = select.Case(
        n=7, verified=Fraction(3), reported=Fraction(3), source_key="", evidence=()
    )
    held = select.select([entry], evidence, cases={7: case})[7]
    assert held.house is None
    assert not held.moves
    lower = select.Case(
        n=7, verified=Fraction(4), reported=Fraction(4), source_key="", evidence=()
    )
    moved = select.select([entry], evidence, cases={7: lower})[7]
    assert moved.house is not None
    assert moved.margin == 1
    unreviewed = {**entry, "reviews": [{"verdict": "defect-open", "covers": ["T-900"]}]}
    assert select.select([unreviewed], evidence, cases={7: lower}) == {}


def test_the_ceiling_rounds_up_and_the_display_ends_where_the_side_does() -> None:
    assert select.ceiling(Fraction(1, 3), 4) == "0.3334"
    assert select.ceiling(Fraction(18)) == "18.0000000000000000"
    assert adopt.display(Fraction(11986956226066, 10**12)) == "11.986956226066"
    assert adopt.display(Fraction(1, 3)) == "0.3333333333333334"


def test_every_adopted_house_rebuilds_from_its_private_inputs() -> None:
    houses.check_houses()


def test_the_house_inputs_are_ordinary_private_copies_of_every_worker() -> None:
    from devtools import run_negative_controls as controls  # noqa: PLC0415

    inputs = houses.private_input_paths()
    assert set(inputs) <= set(controls.COPY_SEPARATELY)
    assert all(path.is_file() and not path.is_symlink() for path in inputs)
    leaves = {path.relative_to(controls.ROOT) for path in houses.snapshot_house_links()}
    assert leaves <= controls.HOUSE_LINK_LEAVES


def test_a_late_verdict_in_a_receipt_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = houses.receipt_cases(houses.receipt_of(70), "evand-regularized-exact-replay-v1")
    forged = [
        {**row, "exact_verify": {**row["exact_verify"], "verification_passed": True}}
        if row["n"] == 70 and row["control"] == houses.kernel.JOBS[2]
        else row
        for row in rows
    ]
    monkeypatch.setattr(houses, "receipt_cases", lambda _path, _form: tuple(forged))
    with pytest.raises(houses.kernel.ReportError):
        houses.expected_house(70)


def test_the_adopted_case_records_and_coverage_are_at_their_houses(
    selections: dict[int, select.Selection],
) -> None:
    assert adopt.check() == []
    assert adopt.plan(selections) == []


def test_the_receipt_of_the_custody_run_names_every_input_and_house() -> None:

    receipt = safe_load(houses.CUSTODY_RECEIPT.read_text(encoding="utf-8"))
    assert receipt["format"] == houses.CUSTODY_FORMAT
    assert receipt["outcome"] == "PASS"
    assert receipt["houses"] == {str(n): result for n, result in houses.ADOPTED.items()}
    recorded = {row["path"] for row in receipt["inputs"]}
    assert recorded == {
        path.relative_to(houses.REPO).as_posix() for path in houses.private_input_paths()
    }
    assert len(receipt["mutations_refused_and_restored"]) == 2 * len(houses.source_keys())
    assert receipt["fresh_geometric_deciders"] is False


def test_the_prior_state_keeps_every_moved_record_as_it_stood_before() -> None:
    """Each record was retained before the move: at another source, above its house."""
    history = adopt.read_history()
    assert sorted(history) == list(houses.NUMBERS)
    for n, text in history.items():
        packing = safe_load(text.split("---\n", 2)[1])["packing"]
        assert packing["n"] == n
        assert packing["reported_upper_bound"]["source_key"] != houses.source_for(n).key
        assert Fraction(packing["verified_upper_bound"]["exact_form"]) > houses.side(n)
    adopt.retain_history({70: "a later text is not the prior state"})
    assert adopt.read_history()[70] == history[70]


def test_a_redraft_keeps_the_house_and_takes_the_drafted_lower_lanes() -> None:
    """The generator's redraft of an adopted case changes only what the draft owns."""
    record = select.case_path(70).read_text(encoding="utf-8")
    assert adopt.holds(70, record)
    assert adopt.adopt_case(70, record, record) == record
    lower = {"value": "1", "exact_form": "1", "evidence": ["E-area-lower"]}
    drafted = adopt.with_lane(record, "verified_lower_bound", lower)
    redrafted = adopt.adopt_case(70, record, drafted)
    packing = safe_load(redrafted.split("---\n", 2)[1])["packing"]
    assert packing["verified_lower_bound"] == lower
    assert redrafted == drafted
    # A record whose upper lane left the house is refused, and one at another source is
    # the draft's entirely.
    forged = adopt.with_lane(
        record,
        "verified_upper_bound",
        {"value": "9", "exact_form": "9", "evidence": ["E-basic-grid-upper"]},
    )
    with pytest.raises(adopt.AdoptionError, match="exact side"):
        adopt.adopt_case(70, forged, record)
    earlier = adopt.read_history()[70]
    assert not adopt.holds(70, earlier)
    assert adopt.adopt_case(70, earlier, record) == record
