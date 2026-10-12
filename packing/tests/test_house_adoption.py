"""The 11 October 2026 house adoption: derivation, drawing custody and the case records."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
import yaml

from devtools import adopt_houses as adopt
from devtools import select_houses as select
from devtools import upper_bound_houses as houses
from sqpack.yamlio import safe_load


@pytest.fixture(scope="module")
def selections() -> dict[int, select.Selection]:
    return select.select()


@pytest.fixture(scope="module")
def prior() -> dict[int, str]:
    """Each moved record as it stood before the adoption, from the retained prior state."""
    return adopt.read_history()


@pytest.fixture(scope="module")
def replayed(
    selections: dict[int, select.Selection], prior: dict[int, str]
) -> list[adopt.Move]:
    """The adoption planned again from the retained prior state of every moved record."""
    cases = {
        n: select.parse_case(n, prior[n]) if n in prior else selection.case
        for n, selection in selections.items()
    }
    return adopt.plan(select.select(cases=cases), texts=prior)


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
    assert selections[236].candidates[0].regularizes == "T-136"
    assert selections[103].candidates[0].regularizes == "T-138"
    assert selections[70].candidates[0].regularizes == "T-125"
    assert adopt.CREDITS[236].found_by == (adopt.SQUISH,)
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


def _confirmed_entry() -> tuple[dict[str, Any], dict[str, Any]]:
    """A synthetic V3/C3 upper bound at n = 7 with an accepted review and a passing replay."""
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
    return entry, evidence


def test_a_case_keeps_its_own_house_where_nothing_is_below(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entry, evidence = _confirmed_entry()
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


def test_a_candidate_below_an_algebraic_ceilings_display_is_left_to_a_human(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A display rounded up at sixteen places cannot order a side just below it."""
    assert not select.load_case(51).exact  # (16 + 5 sqrt(2)) / 3
    assert select.load_case(70).exact
    entry, evidence = _confirmed_entry()
    display = Fraction(Decimal("7.6903559372884918"))
    algebraic = select.Case(
        n=7, verified=display, reported=display, source_key="", evidence=(), exact=False
    )
    within = display - Fraction(1, 10**17)
    monkeypatch.setitem(select.reports.HOUSES, "[test]", lambda _n: within)
    monkeypatch.setattr(select, "_side", lambda _key, _n: within)
    held = select.select([entry], evidence, cases={7: algebraic})[7]
    assert held.undecided
    assert held.house is None
    rational = dataclasses.replace(algebraic, exact=True)
    assert select.select([entry], evidence, cases={7: rational})[7].moves
    monkeypatch.setattr(select, "_side", lambda _key, _n: display)
    above = select.select([entry], evidence, cases={7: algebraic})[7]
    assert not above.undecided
    assert not above.moves
    assert "undecided" in select.table({7: held}, everything=False)


def test_no_unread_eligible_entry_is_pending_adoption() -> None:
    """An eligible entry with no exact reader is never a candidate, so `--check` reads its
    standing instead: one that states a side below its case would be an adoption the
    selector cannot see."""
    unread: list[str] = []
    select.candidates(select.load_results(), select.load_evidence(), unread=unread)
    assert select.unread_pending(unread) == {}


def test_check_lists_the_unread_and_fails_on_one_pending_adoption(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def selecting(*, since: str | None, unread: list[str]) -> dict[int, select.Selection]:
        assert since is None
        unread.append("T-901")
        return {}

    monkeypatch.setattr(select, "select", selecting)
    monkeypatch.setattr(select, "unread_pending", lambda _unread: {})
    assert select.main(["--check"]) == 0
    assert "unread, eligible but with no exact reader: T-901" in capsys.readouterr().out
    monkeypatch.setattr(select, "unread_pending", lambda unread: {unread[0]: [7]})
    assert select.main(["--check"]) == 1
    assert "T-901 has no exact reader and states a side below its case at n = [7]" in (
        capsys.readouterr().out
    )


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
    # Each input is still the file custody read: a changed one fails until custody runs
    # again (`python -m devtools.upper_bound_houses custody`).
    for row in receipt["inputs"]:
        raw = (houses.REPO / row["path"]).read_bytes()
        assert (row["bytes"], row["sha256"]) == (len(raw), hashlib.sha256(raw).hexdigest())
    assert len(receipt["mutations_refused_and_restored"]) == 2 * len(houses.source_keys())
    assert receipt["fresh_geometric_deciders"] is False


def test_the_prior_state_keeps_every_moved_record_as_it_stood_before(
    prior: dict[int, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each record was retained before the move: at another source, above its house."""
    assert sorted(prior) == list(houses.NUMBERS)
    for n, text in prior.items():
        packing = safe_load(text.split("---\n", 2)[1])["packing"]
        assert packing["n"] == n
        assert packing["reported_upper_bound"]["source_key"] != houses.source_for(n).key
        assert Fraction(packing["verified_upper_bound"]["exact_form"]) > houses.side(n)
    # Retaining again keeps the first text and writes only a count not yet retained; the
    # archive is never written here.
    saved: list[Any] = []
    monkeypatch.setattr(houses.kernel, "save_xz", lambda _path, value: saved.append(value))
    adopt.retain_history({70: "a later text is not the prior state"})
    assert saved == []
    adopt.retain_history({70: "a later text", 999: "a count not yet retained"})
    (record,) = saved
    rows = {row["n"]: row["frontier"] for row in record["cases"]}
    assert rows == {**prior, 999: "a count not yet retained"}


#: The front-matter keys `adopt_houses.front_matter` writes; every other key is the draft's
#: or another tool's.
OWNED = (
    "source_reviewed",
    "reported_upper_bound",
    "verified_upper_bound",
    "conjectured_optimum",
    "priority_notes",
    "evidence",
    "resources",
    "blockers",
)


def _front(text: str) -> dict[str, Any]:
    return dict(safe_load(text.split("---\n", 2)[1])["packing"])


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_the_writer_rebuilds_every_adopted_record_from_its_prior_state(
    replayed: list[adopt.Move],
) -> None:
    """Replaying `rewrite` on each retained prior record gives the committed record.

    What the writer owns is compared: its front-matter keys, and its opening paragraph and
    certificate section with whitespace collapsed, since flowmark rewraps the body. The
    verifier table and the rigidity scope are refreshed by their own tools.
    """
    assert [move.n for move in replayed] == sorted(houses.ADOPTED)
    for move in replayed:
        assert move.house.result == houses.ADOPTED[move.n]
        committed = select.case_path(move.n).read_text(encoding="utf-8")
        written = adopt.rewrite(move)
        held, wrote = _front(committed), _front(written)
        for key in OWNED:
            assert held.get(key) == wrote.get(key), f"n={move.n}: packing.{key}"
        body = _flat(committed.split("---\n", 2)[2])
        assert _flat(adopt.opening(move)) in body, f"n={move.n}: opening paragraph"
        assert _flat(adopt.section(move)) in body, f"n={move.n}: certificate section"


def test_a_conjecture_the_house_does_not_beat_stops_the_adoption(
    replayed: list[adopt.Move],
) -> None:
    move = next(move for move in replayed if move.n == 232)
    conjecture = adopt.conjectured(move.packing)
    assert conjecture == Fraction(Decimal("15.77817459305202")) > move.house.side
    assert "  conjectured_optimum: null\n" in adopt.rewrite(move)
    above = dataclasses.replace(move, house=dataclasses.replace(move.house, side=conjecture))
    with pytest.raises(adopt.AdoptionError, match="does not beat the conjectured optimum"):
        adopt.rewrite(above)
    grid = {"conjectured_optimum": "integer", "reported_upper_bound": {"value": "18"}}
    assert adopt.conjectured(grid) == 18
    assert adopt.conjectured({"conjectured_optimum": None}) is None


# ------------------------------------------------------------------- the coverage register


def _claims(directory: Path, name: str, sides: dict[int, str]) -> str:
    path = directory / f"{name}.json"
    rows = [{"n": n, "offered_side": side} for n, side in sides.items()]
    path.write_text(json.dumps({"results": rows}), encoding="utf-8")
    return path.as_posix()


def _register(directory: Path) -> str:
    """A coverage register at n = 7 before T-900 moves its house to 13/4."""
    claims = {
        "old": {7: "3.5"},
        "printed": {7: "3.3", 8: "9"},
        "below": {7: "3.2"},
        "equal": {7: "3.2500001"},
        "above": {7: "3.5000001"},
    }
    sources: list[dict[str, Any]] = [{"id": "new", "source_key": "[new]"}]
    sources += [
        {
            "id": name,
            "source_key": f"[{name}]",
            "claims_record": _claims(directory, name, sides),
        }
        for name, sides in claims.items()
    ]
    data = {
        "sources": sources,
        "selected_overrides": [
            {"n": 7, "source_id": "old", "value": "3.5", "evidence": "E-old", "reason": "Old."}
        ],
        "superseded_reports": [
            {
                "n": 7,
                "source_id": "older",
                "value": "3.75",
                "reason": (
                    "The house until 2026-10-01; its certificate stays retained and verified, "
                    "and T-800's exact side is smaller."
                ),
                "superseded_by": "old",
            },
            {
                "n": 7,
                "source_id": "grid",
                "value": "4",
                "reason": "Grid.",
                "superseded_by": "old",
            },
        ],
        "beyond_horizon_claims": [],
    }
    return yaml.safe_dump(data, sort_keys=False, width=adopt.WIDTH)


def _move(n: int = 7, side: Fraction = Fraction(13, 4)) -> adopt.Move:
    house = select.Candidate(
        result="T-900",
        n=n,
        side=side,
        source_key="[new]",
        published="2026-10-10",
        report_evidence=("E-new",),
        confirming_evidence=("E-new-replay",),
        regularizes=None,
    )
    earlier = Fraction(7, 2)
    case = select.Case(n=n, verified=earlier, reported=earlier, source_key="[old]", evidence=())
    selection = select.Selection(n=n, case=case, house=house, candidates=(house,))
    return adopt.Move(selection, house, {}, "")


def test_coverage_selects_the_new_house_and_points_every_row_at_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = _register(tmp_path)
    monkeypatch.setattr(adopt, "COVERAGE", tmp_path / "source-coverage.yaml")
    adopt.COVERAGE.write_text(text, encoding="utf-8")
    monkeypatch.setitem(select.reports.HOUSES, "[equal]", lambda _n: Fraction(13, 4))
    monkeypatch.setitem(select.reports.HOUSES, "[above]", lambda _n: Fraction(7, 2))
    once = adopt.coverage([_move()], text)
    data = safe_load(once)
    (override,) = data["selected_overrides"]
    assert override["source_id"] == "new"
    assert override["value"] == "3.2500000000000000"
    assert override["evidence"] == "E-new"
    assert "adopted on 2026-10-11 (T-900)" in override["reason"]
    rows = {row["source_id"]: row for row in data["superseded_reports"]}
    assert {row["superseded_by"] for row in rows.values()} == {"new"}
    # A row an earlier adoption wrote for the house it displaced now names this house, and
    # keeps its own day; another row keeps its reason.
    assert rows["older"]["reason"] == (
        "The house until 2026-10-01; its certificate stays retained and verified, and "
        "T-900's exact side is smaller."
    )
    assert rows["grid"]["reason"] == "Grid."
    assert rows["old"]["value"] == "3.5"
    assert rows["old"]["reason"].startswith("The house until 2026-10-11;")
    assert rows["old"]["reason"].endswith("and T-900's exact side is smaller.")
    # The release's other claims at the count: compared exactly where a reader rebuilds
    # them, by the print otherwise, and a print below the house is left for
    # `check_source_coverage` to refuse.
    assert "the side it prints is above the house" in rows["printed"]["reason"]
    assert "its exact side equals the house" in rows["equal"]["reason"]
    assert "T-900's registered certificate holds" in rows["equal"]["reason"]
    assert "its exact side is above the house" in rows["above"]["reason"]
    assert "below" not in rows
    assert [row["n"] for row in data["superseded_reports"]] == [7] * 6
    assert adopt.coverage([_move()], once) == once


def test_deferrals_drop_exactly_the_entries_a_case_record_cites() -> None:
    head = "# Deferred adoptions, each with its reason.\n"
    text = (
        head + "deferrals:\n"
        "  - evidence: E-a\n    results: [T-1]\n    bead: think-a\n"
        "  - evidence: E-b\n    results: [T-2]\n    bead: think-b\n"
    )
    assert adopt.deferrals(text, set()) == text
    kept = adopt.deferrals(text, {"E-a", "E-unrelated"})
    assert kept.startswith(head + "deferrals:\n  - evidence: E-b\n")
    assert safe_load(kept)["deferrals"] == [
        {"evidence": "E-b", "results": ["T-2"], "bead": "think-b"}
    ]
    assert adopt.deferrals(text, {"E-a", "E-b"}) == head + "deferrals: []\n"


# ------------------------------------------------------------------- an interrupted write


def _unadopted(text: str, counts: set[int]) -> str:
    """The coverage register with the adoption's selection at `counts` taken back."""
    data = safe_load(text)
    rows = data["superseded_reports"]
    for n in counts:
        displaced = next(
            row for row in rows if row["n"] == n and row["reason"].startswith("The house until")
        )
        rows.remove(displaced)
        override = next(row for row in data["selected_overrides"] if row["n"] == n)
        override.update(source_id=displaced["source_id"], value=displaced["value"])
    for key in ("selected_overrides", "superseded_reports"):
        start, end = adopt._section_span(text, key)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        dumped = yaml.safe_dump({key: data[key]}, sort_keys=False, width=adopt.WIDTH)
        text = text[:start] + dumped + text[end:]
    return text


def test_an_interrupted_write_is_finished_by_running_it_again(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selections: dict[int, select.Selection],
    prior: dict[int, str],
) -> None:
    """A write stopped before its last record leaves what a rerun finishes, to the byte."""
    moved = {84, 86}
    frontier = tmp_path / "frontier"
    frontier.mkdir()
    staged = {
        frontier / f"n-{n:03d}.md": prior[n]
        if n in moved
        else select.case_path(n).read_text(encoding="utf-8")
        for n in selections
    }
    staged[tmp_path / "source-coverage.yaml"] = _unadopted(
        adopt.COVERAGE.read_text(encoding="utf-8"), moved
    )
    staged[tmp_path / "deferrals.yaml"] = adopt.DEFERRALS.read_text(encoding="utf-8")
    monkeypatch.setattr(select, "FRONTIER", frontier)
    monkeypatch.setattr(adopt, "FRONTIER", frontier)
    monkeypatch.setattr(adopt, "COVERAGE", tmp_path / "source-coverage.yaml")
    monkeypatch.setattr(adopt, "DEFERRALS", tmp_path / "deferrals.yaml")
    retained: dict[int, str] = {}
    monkeypatch.setattr(adopt, "retain_history", retained.update)

    def stage() -> None:
        for path, text in staged.items():
            path.write_text(text, encoding="utf-8")

    def written() -> dict[Path, str]:
        return {path: path.read_text(encoding="utf-8") for path in staged}

    stage()
    moves = adopt.plan()
    assert [move.n for move in moves] == sorted(moved)
    assert adopt.write(moves) == sorted(moved)
    whole = written()
    assert retained == {n: prior[n] for n in moved}

    stage()
    real = adopt._write  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    calls: list[Path] = []

    def interrupted(path: Path, text: str) -> bool:
        calls.append(path)
        if len(calls) == 4:  # the coverage register, the deferrals, n = 84, then n = 86
            raise OSError("interrupted")
        return real(path, text)

    monkeypatch.setattr(adopt, "_write", interrupted)
    with pytest.raises(OSError, match="interrupted"):
        adopt.write(moves)
    monkeypatch.setattr(adopt, "_write", real)
    rest = adopt.plan()
    assert [move.n for move in rest] == [86]
    assert adopt.write(rest) == [86]
    assert written() == whole


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
