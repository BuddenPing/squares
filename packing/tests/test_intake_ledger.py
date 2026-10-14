"""The owner's report-order rule, on synthetic counts, and the committed 2026-10-14 ledger."""

from __future__ import annotations

import copy
from fractions import Fraction
from typing import Any, cast

from devtools import check_standing
from devtools import intake_ledger as ledger
from devtools.upper_bound_reports import exact_span

GRID_10 = ledger.beyond_side(400, {})
CLAIM_TIME = "2026-10-12T00:00:00Z"


def record(value: str = "10.5", exact_form: str = "21/2") -> ledger.Side:
    bound = {"value": value, "exact_form": exact_form, "found_by": ["A. Holder"]}
    return ledger.record_side(100, bound, ["T-001"])


def side(
    label: str, printed: str, rounding: str = "exact", when: str = CLAIM_TIME, **more: Any
) -> ledger.Side:
    claim = cast("ledger.Claim", {"n": 100, "printed": printed, "rounding": rounding, **more})
    report: ledger.Report = {
        "report": label,
        "url": f"https://github.com/jlevy/squares/issues/{label.lstrip('#')}",
        "kind": "issue",
        "holders": f"holder of {label}",
        "reported_at": when,
        "bead": "",
        "claims": [claim],
    }
    return ledger.entry_side(report, claim)


def verdicts(walk: ledger.Walk) -> list[tuple[str, str, str]]:
    return [(step.side.label, step.verdict, ledger.held_by(step)) for step in walk.steps]


def test_later_and_stronger_is_recorded() -> None:
    first = side("#1", "10.4", when="2026-10-12T01:00:00Z")
    second = side("#2", "10.3", when="2026-10-12T02:00:00Z")
    walk = ledger.walk(100, record(), [second, first])
    assert verdicts(walk) == [("#1", "recorded", "record T-001"), ("#2", "recorded", "#1")]
    assert [item.label for item in walk.standing] == ["#2"]


def test_an_earlier_stronger_report_leaves_the_later_one_unrecorded() -> None:
    stronger = side("#1", "10.3", when="2026-10-12T01:00:00Z")
    weaker = side("#2", "10.4", when="2026-10-12T02:00:00Z")
    walk = ledger.walk(100, record(), [weaker, stronger])
    assert verdicts(walk) == [("#1", "recorded", "record T-001"), ("#2", "not recorded", "#1")]
    assert walk.steps[1].reason == ledger.ABOVE


def test_an_exact_tie_is_not_recorded_and_names_the_holder() -> None:
    first = side("#1", "103/10", when="2026-10-12T01:00:00Z")
    tie = side("#2", "10.3", when="2026-10-12T02:00:00Z")
    walk = ledger.walk(100, record(), [first, tie])
    assert verdicts(walk)[1] == ("#2", "not recorded", "#1")
    assert walk.steps[1].reason == ledger.EQUAL


def test_overlapping_prints_are_undecided_and_say_what_decides_them() -> None:
    first = side("#1", "10.40", "up", when="2026-10-12T01:00:00Z")
    second = side("#2", "10.395", "nearest", when="2026-10-12T02:00:00Z")
    walk = ledger.walk(100, record(), [first, second])
    assert verdicts(walk)[1] == ("#2", "undecided", "#1")
    assert {item.label for item in walk.standing} == {"#1", "#2"}
    assert "the exact side of #1" in ledger.decider(walk.steps[1].side, walk.steps[1].against)
    # A claim below both members of the undecided standing side is recorded.
    third = side("#3", "10.2", when="2026-10-12T03:00:00Z")
    later = ledger.walk(100, record(), [first, second, third])
    assert verdicts(later)[2] == ("#3", "recorded", "#1, #2")


def test_a_pending_adoption_bound_lowers_the_start() -> None:
    entry = {"id": "T-123", "attribution": {"source_keys": ["[Source 2026]"]}}
    stated = check_standing.Stated(Fraction("10.40"), Fraction(1, 100))
    pending = ledger.pending_side(entry, stated)
    start = ledger.lowered(record(), [pending])
    assert start.label == "register T-123, pending adoption"
    # A claim at 10.45 is below the record and above the pending bound: not recorded.
    walk = ledger.walk(100, start, [side("#1", "10.45")])
    assert verdicts(walk) == [("#1", "not recorded", "register T-123, pending adoption")]
    # A bound that is not below the record lowers nothing.
    higher = ledger.pending_side(entry, check_standing.Stated(Fraction("10.6"), Fraction(0)))
    assert ledger.lowered(record(), [higher]).label == "record T-001"


def test_the_start_beyond_the_horizon_is_the_row_or_the_grid() -> None:
    row = {"n": 400, "source_id": "row-2026-10-11", "value": "19.990000000000"}
    from_row = ledger.beyond_side(400, {400: row})
    assert from_row.label == "beyond-horizon row row-2026-10-11"
    assert ledger.walk(400, from_row, [side("#1", "19.99")]).steps[0].verdict == "undecided"
    assert GRID_10.label == "the grid"
    assert GRID_10.span == exact_span(Fraction(20))
    walk = ledger.walk(400, GRID_10, [side("#1", "19.99"), side("#2", "20")])
    assert [step.verdict for step in walk.steps] == ["recorded", "not recorded"]


def test_an_exception_is_applied_and_shown() -> None:
    stronger = side("#1", "10.3", when="2026-10-12T01:00:00Z")
    weaker = side("#2", "10.4", when="2026-10-12T02:00:00Z")
    walk = ledger.walk(100, record(), [stronger, weaker], {(100, "#2"): "first committed"})
    assert walk.steps[1].verdict == ledger.BY_EXCEPTION
    assert ledger.step_record(walk.steps[1])["exception"] == "first committed"
    # The exception moves nothing: the stronger report still holds the count.
    assert [item.label for item in walk.standing] == ["#1"]


def test_a_closed_form_of_integers_is_a_rational_record() -> None:
    assert ledger.rational_form("7 + (4/7)") == Fraction(53, 7)
    assert ledger.rational_form("2 + (1/2)sqrt(2)") is None
    assert ledger.record_side(
        50, {"value": "7.57142857142857", "exact_form": "7 + (4/7)"}, []
    ).exact


def test_a_relation_frozen_against_the_record_holds_only_while_the_record_reads_so() -> None:
    form = "2 + (1/2)sqrt(2)"
    start = ledger.record_side(5, {"value": "2.70710678118654", "exact_form": form}, ["T-005"])
    frozen: ledger.RecordRelation = {
        "relation": "equal",
        "value": "2.70710678118654",
        "exact_form": form,
        "read_from": "lane",
    }
    algebraic = side(
        "#1", "2.7071067811865475244008443621048490392848", "unstated", record_relation=frozen
    )
    assert ledger.compare(algebraic, start) == ledger.EQUAL
    moved = ledger.record_side(5, {"value": "2.707106781186547", "exact_form": form}, ["T-005"])
    assert ledger.compare(algebraic, moved) == ledger.UNDECIDED


def test_a_binary64_print_spans_one_ulp_and_a_cut_print_its_next_unit() -> None:
    span = ledger.printed_side("17.8702753825550609", "binary64")
    assert ledger.contains(span, Fraction("17.8702753825550621"))
    assert not ledger.contains(
        ledger.printed_side("17.8702753825550609", "nearest"), Fraction("17.8702753825550621")
    )
    cut = ledger.printed_side("12.95", "cut")
    assert ledger.contains(cut, Fraction("12.959"))
    assert not ledger.contains(cut, Fraction("12.96"))


def _minimal() -> dict[str, Any]:
    return {
        "format": ledger.LEDGER_FORMAT,
        "read_at_main": "f" * 40,
        "read_on": "2026-10-14",
        "rule": "the owner's rule",
        "lanes": [],
        "reports": [
            {
                "report": "#1",
                "url": "https://github.com/jlevy/squares/issues/1",
                "kind": "issue",
                "holders": "A",
                "reported_at": CLAIM_TIME,
                "bead": "think-abcd",
                "claims": [{"n": 100, "printed": "10.4", "rounding": "up", "exact": "52/5"}],
            }
        ],
        "exceptions": [],
        "other_items": [],
    }


def test_check_holds_the_schema_the_prints_and_the_times() -> None:
    assert ledger.problems(_minimal()) == []
    above_its_print = copy.deepcopy(_minimal())
    above_its_print["reports"][0]["claims"][0]["exact"] = "10401/1000"
    assert "outside its own print" in " ".join(ledger.problems(above_its_print))
    bad_time = copy.deepcopy(_minimal())
    bad_time["reports"][0]["reported_at"] = "12 October"
    assert "reported_at" in " ".join(ledger.problems(bad_time))
    duplicated = copy.deepcopy(_minimal())
    duplicated["reports"][0]["claims"].append(dict(duplicated["reports"][0]["claims"][0]))
    assert "listed twice" in " ".join(ledger.problems(duplicated))
    orphan = copy.deepcopy(_minimal())
    orphan["exceptions"] = [{"n": 7, "report": "#1", "reason": "why"}]
    assert "names no claim" in " ".join(ledger.problems(orphan))


def test_a_publication_dependent_verdict_is_listed_with_its_alternative() -> None:
    data = _minimal()
    data["reports"][0]["claims"] = [{"n": 400, "printed": "19.99", "rounding": "exact"}]
    data["reports"].append(
        {
            "report": "owner/repo@abc1234",
            "url": "https://github.com/owner/repo/tree/abc1234",
            "kind": "publication",
            "holders": "B",
            "reported_at": "2026-10-11T00:00:00Z",
            "bead": "",
            "claims": [{"n": 400, "printed": "19.98", "rounding": "exact"}],
        }
    )
    verdict = ledger.evaluate(cast("ledger.Ledger", data), {400: GRID_10})
    changes = {
        item["report"]: item for item in verdict["owner_decisions"]["publication_dependent"]
    }
    assert changes["#1"]["with_publications"] == "not recorded"
    assert changes["#1"]["without_publications"] == "recorded"
    assert changes["owner/repo@abc1234"]["without_publications"] == ledger.NOT_IN_WALK


def test_render_check_passes_on_the_committed_ledger() -> None:
    assert ledger.problems(ledger.load_yaml(ledger.DEFAULT_DIRECTORY / ledger.LEDGER)) == []
    assert ledger.render(ledger.DEFAULT_DIRECTORY, check=True) == []


def test_refinements_render_with_their_packing_and_form_a_chain() -> None:
    data = _minimal()
    original: dict[str, Any] = {
        "n": 100,
        "printed": "10.4",
        "rounding": "exact",
        "refines": {"packing_of": "A. Finder", "entry": "T-001", "source": "the issue"},
    }
    data["reports"][0]["claims"] = [original]
    data["reports"].append(
        {
            "report": "#2",
            "url": "https://github.com/jlevy/squares/issues/2",
            "kind": "issue",
            "holders": "B",
            "reported_at": "2026-10-12T05:00:00Z",
            "bead": "",
            "claims": [
                {
                    "n": 100,
                    "printed": "10.39",
                    "rounding": "exact",
                    "refines": {"packing_of": "A. Finder", "entry": "#1", "source": "lane"},
                }
            ],
        }
    )
    data["reports"].append(
        {
            "report": "#3",
            "url": "https://github.com/jlevy/squares/issues/3",
            "kind": "issue",
            "holders": "C",
            "reported_at": "2026-10-12T06:00:00Z",
            "bead": "",
            "claims": [
                {
                    "n": 100,
                    "printed": "10.2",
                    "rounding": "exact",
                    "new_packing": {"source": "the issue", "continues": "B's arrangement"},
                }
            ],
        }
    )
    assert ledger.problems(data) == []
    verdict = ledger.evaluate(cast("ledger.Ledger", data), {100: record()})
    steps = verdict["counts"][0]["steps"]
    assert ledger.recorded_text(steps[0]) == (
        "recorded, a refinement of A. Finder's packing (T-001)"
    )
    assert ledger.recorded_text(steps[2]) == (
        "recorded (new packing, continuing B's arrangement)"
    )
    chain = verdict["owner_decisions"]["refinement_chains"]
    assert [item["report"] for item in chain[0]["refinements"]] == ["#1", "#2"]
    assert chain[0]["packing"] == "T-001"
    summary = verdict["summary"]
    assert (summary["recorded_refinement"], summary["recorded_new"]) == (2, 1)
    row = verdict["reports"][0]
    assert row["recorded_refinement"] == [
        {"n": 100, "packing_of": "A. Finder", "entry": "T-001"}
    ]
    both = copy.deepcopy(data)
    both["reports"][0]["claims"][0]["new_packing"] = {"source": "x"}
    assert "not both" in " ".join(ledger.problems(both))
