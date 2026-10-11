"""The driver of Evan Daniel's vendored regularizer, on counts small enough to run here.

The input writer is held to exact digits (a rational witness's centres to fifty
significant digits of its exact values, a decimal witness's strings verbatim, the
algebraic witness's field values) and to upstream's own batch inputs where the witness
has not changed since upstream solved it. The replica builder is held to its boundary:
it copies the seven modules the pipeline runs byte for byte and writes nothing under
`vendor/`. The decision table is run as a pure function over synthetic measurements, one
for each of its ten rows and one that no row matches. One count, n = 26, runs end to end
through the real solver and regularizer.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import mpmath
import pytest
from jsonschema import Draft202012Validator

from devtools import regularize_evand as drive
from devtools.regularize_evand import Decision, Measured, Options, classify
from sqpack.witness import load_witness, materialize_exact_witness
from sqpack.yamlio import load_yaml

ALL_ROUTES = {"exact_verify": True, "independent": True, "half_angle": True}


def witness(n: int) -> dict:
    return load_witness(drive.witness_path(n), fallback_schema=drive.WITNESS_SCHEMA)


def vendor_listing() -> list[tuple[str, int]]:
    """Every file under `vendor/evand-regularize` with its size, for a before-and-after."""
    found: list[tuple[str, int]] = []
    for directory, _subdirectories, files in os.walk(drive.VENDOR):
        for name in files:
            path = Path(directory) / name
            found.append((str(path.relative_to(drive.VENDOR)), path.stat().st_size))
    return sorted(found)


# --------------------------------------------------------------------------------------
# Stage 1: the input
# --------------------------------------------------------------------------------------


def test_decimal_input_carries_the_witness_strings_verbatim() -> None:
    source = witness(26)
    n, side, rows = drive.read_input(drive.input_text(source))
    assert n == 26
    assert side == source["side"]
    expected = [(*square["center"], square["angle"]) for square in source["squares"]]
    assert rows == expected


def test_rational_input_is_its_exact_values_to_fifty_digits() -> None:
    source = witness(70)
    assert source["scalar"]["kind"] == "rational"
    _n, side, rows = drive.read_input(drive.input_text(source))
    squares, exact_side = materialize_exact_witness(source)
    bound = Fraction(1, 10**47)
    assert abs(Fraction(side) - Fraction(exact_side)) < bound
    mpmath.mp.dps = 60
    for (x, y, degrees), corners in zip(rows, squares, strict=True):
        xs = [Fraction(cx) for cx, _ in corners]
        ys = [Fraction(cy) for _, cy in corners]
        assert abs(Fraction(x) - sum(xs, Fraction(0)) / 4) < bound
        assert abs(Fraction(y) - sum(ys, Fraction(0)) / 4) < bound
        c, s = xs[1] - xs[0], ys[1] - ys[0]
        turn = mpmath.mpf(degrees) * mpmath.pi / 180
        assert abs(mpmath.cos(turn) - mpmath.mpf(c.numerator) / c.denominator) < 1e-45
        assert abs(mpmath.sin(turn) - mpmath.mpf(s.numerator) / s.denominator) < 1e-45


def test_algebraic_input_is_the_field_values_at_sixty_digits() -> None:
    source = witness(51)
    assert source["scalar"]["kind"] == "algebraic-number-field"
    n, side, rows = drive.read_input(drive.input_text(source))
    assert n == 51
    assert len(rows) == 51
    mpmath.mp.dps = 60
    exact = (16 + 5 * mpmath.sqrt(2)) / 3
    assert abs(mpmath.mpf(side) - exact) < mpmath.mpf(10) ** -48


@pytest.mark.parametrize("n", [5, 10, 13, 26])
def test_input_agrees_with_upstreams_batch_input(n: int) -> None:
    """Same squares in the same order, agreeing to binary64, angles modulo 90 degrees."""
    mine = drive.read_input(drive.input_text(witness(n)))
    theirs = drive.read_input((drive.UPSTREAM_INPUTS / f"n-{n}.txt").read_text())
    assert mine[0] == theirs[0]
    assert float(mine[1]) == float(theirs[1])
    for (x, y, angle), (u, v, other) in zip(mine[2], theirs[2], strict=True):
        assert math.isclose(float(x), float(u), rel_tol=1e-15, abs_tol=1e-15)
        assert math.isclose(float(y), float(v), rel_tol=1e-15, abs_tol=1e-15)
        turn = abs(float(angle) % 90 - float(other) % 90)
        assert min(turn, 90 - turn) < 1e-12


def test_witness_frame_is_the_exact_pose_at_s_w_to_eighty_digits() -> None:
    """`--frame witness` hands the regularizer the policy's frame: here n = 70's exact pose."""
    source = witness(70)
    frame = drive.source_frame(source)
    assert frame.side is not None
    n, side, rows = drive.read_input(drive.frame_text(source, frame))
    assert n == 70
    assert abs(Fraction(side) - frame.side) < Fraction(1, 10**78)
    for (x, y, _degrees), (cx, cy, _c, _s) in zip(rows, frame.placements, strict=True):
        assert abs(Fraction(x) - cx) < Fraction(1, 10**78)
        assert abs(Fraction(y) - cy) < Fraction(1, 10**78)


# --------------------------------------------------------------------------------------
# Stage 2: the replica
# --------------------------------------------------------------------------------------


def test_replica_copies_the_pipeline_and_writes_nothing_under_vendor(tmp_path: Path) -> None:
    before = vendor_listing()
    rows = [drive.batch_row(n, drive.case_facts(n), witness(n)) for n in (5, 26)]
    replica = drive.build_replica(tmp_path / "run", rows)
    assert vendor_listing() == before
    for directory, names in drive.REPLICA_FILES.items():
        for name in names:
            copied = replica / directory / name
            assert copied.read_bytes() == (drive.VENDOR / directory / name).read_bytes()
    results = json.loads((replica / drive.BATCH / "results.json").read_text())
    assert [row["n"] for row in results] == [5, 26]
    assert all(row["from_"] == "witness" for row in results)
    link = replica / drive.BATCH / "work/n-26"
    assert link.is_symlink()
    assert link.resolve() == (tmp_path / "run/n-026/solve").resolve()


def test_run_directory_inside_the_checkout_is_refused() -> None:
    with pytest.raises(drive.EvandRunError, match="inside the checkout"):
        drive.outside_checkout(drive.VENDOR / "runs")


def test_counts_parse_as_integers_and_ranges() -> None:
    assert drive.parse_counts(["5", "9-11", "10"]) == [5, 9, 10, 11]


# --------------------------------------------------------------------------------------
# Stage 8: the decision table, one synthetic measurement per row
# --------------------------------------------------------------------------------------

SW = Fraction(562, 100)
SAME = Measured(
    "same",
    produced=True,
    routes=ALL_ROUTES,
    relation="same",
    side=SW,
    upper=SW - Fraction(1, 10**20),
    level=2,
    max_move=Fraction(3, 10),
)

ROWS = {
    1: (Measured("solved", produced=False, status="solve timeout"), "generator-failed"),
    2: (
        Measured(
            "solved",
            produced=True,
            routes={**ALL_ROUTES, "half_angle": False},
            relation="solved",
            side=SW,
        ),
        "invalid",
    ),
    3: (
        Measured(
            "solved",
            produced=True,
            routes=ALL_ROUTES,
            relation="solved",
            side=SW,
            upper=SW + Fraction(1, 10**10),
        ),
        None,
    ),
    4: (
        Measured(
            "solved", produced=True, routes=ALL_ROUTES, relation="solved", side=SW, upper=SW
        ),
        "dilated-side",
    ),
    5: (replace(SAME, pose_equals_witness=True), None),
    6: (replace(SAME, one_to_one=False), "not-one-to-one"),
    7: (replace(SAME, regressions=2), "regression"),
    8: (replace(SAME, level=3), None),
    9: (replace(SAME, max_move=Fraction(6, 10)), None),
    10: (SAME, None),
}
EXPECTED = {
    1: ("no-view", None),
    2: ("refuse", "refused"),
    3: ("held", None),
    4: ("held", None),
    5: ("no-change", "unchanged"),
    6: ("refuse", "refused"),
    7: ("refuse", "refused"),
    8: ("alternate", None),
    9: ("review", None),
    10: ("admit", "regularized"),
}


@pytest.mark.parametrize("row", sorted(ROWS))
def test_each_row_of_the_decision_table(row: int) -> None:
    measured, refusal = ROWS[row]
    decided = classify(measured)
    assert decided.row == row
    assert (decided.decision, decided.index_record) == EXPECTED[row]
    assert decided.refusal == refusal


def test_the_first_matching_row_decides() -> None:
    """A view failing a route and below U is invalid (row 2) before it is a candidate."""
    both = Measured(
        "same",
        produced=True,
        routes={"exact_verify": False, "independent": True},
        relation="same",
        side=SW,
        upper=SW + 1,
    )
    assert classify(both).row == 2
    turned = replace(SAME, unnamed_turns=(3,), regressions=1)
    assert classify(turned) == Decision(
        6,
        "refuse",
        "refused",
        "unnamed-turn",
        "squares [3] turned without a recorded angle change",
    )


def test_a_fewest_merge_is_an_alternate_and_fewest_alone_is_not_admitted() -> None:
    merged = replace(SAME, variant="fewest", determined_merge=True)
    assert classify(merged).row == 8
    plain = replace(SAME, variant="fewest")
    assert classify(plain).row is None
    assert classify(plain).decision == "review"


@pytest.mark.parametrize("row", [3, 4, 7])
def test_a_view_that_draws_the_same_picture_is_no_change_whatever_its_row(row: int) -> None:
    """Owner, 11 October 2026: nothing is refused or held where nothing would change."""
    measured, _refusal = ROWS[row]
    decided = classify(replace(measured, visible_change=False))
    assert decided.row == row
    assert (decided.decision, decided.index_record, decided.refusal) == (
        "no-change",
        "unchanged",
        None,
    )
    assert decided.reason.startswith("nothing visible changes (")


@pytest.mark.parametrize("row", [1, 2])
def test_no_view_and_an_invalid_view_are_reported_as_they_are(row: int) -> None:
    measured, _refusal = ROWS[row]
    decided = classify(replace(measured, visible_change=False))
    assert (decided.decision, decided.index_record) == EXPECTED[row]


def test_visible_change_reads_moves_turns_pairing_and_house_counts() -> None:
    still = {"moved": 0, "turned": [], "one_to_one": True}
    same_counts = {"house": {"before": [0, 1, 2, 3, 4], "after": [0, 1, 2, 3, 4]}}
    assert not drive.visible_change(still, same_counts)
    assert drive.visible_change({**still, "moved": 1}, same_counts)
    assert drive.visible_change({**still, "turned": [3]}, same_counts)
    assert drive.visible_change({**still, "one_to_one": False}, same_counts)
    changed = {"house": {"before": [0, 1, 2, 3, 4], "after": [0, 0, 3, 3, 4]}}
    assert drive.visible_change(still, changed)


def test_a_solved_view_with_no_upper_bound_is_held_and_says_so() -> None:
    measured = Measured("solved", produced=True, routes=ALL_ROUTES, relation="solved", side=SW)
    decided = classify(measured)
    assert decided.row == 4
    assert "U unknown" in decided.reason
    at_bound = classify(replace(measured, upper=SW))
    assert at_bound.decision == "held"
    assert "exactly the verified upper bound" in at_bound.reason


def _register_item_validator() -> Draft202012Validator:
    schema = load_yaml((drive.ROOT / "frontier/results.schema.yaml").read_text())
    return Draft202012Validator(
        schema["$defs"]["result"]["properties"]["regularizations"]["items"]
    )


REPORT = {
    "n": 26,
    "source": {
        "path": "packing/witnesses/known-best/n-026.yaml",
        "provenance": {"source_key": "[kingbird]", "found_by": ["Göbel"], "improved_by": []},
    },
    "generator": {
        "pin": "675a5ea",
        "patches": [],
        "variant": "conservative",
        "style": "coincide",
    },
    "regularize": {
        "merged": [[8, -0.0057, 0.0], [23, -44.994, 45.0], [4, 12.0, 30.5]],
        "angle_changes": [["determined-merge", 30.0, 30.7, 2]],
    },
    "outputs": {"same": {"relation": "same"}, "solved": {"relation": "solved"}},
    "identity": {"one_to_one": True, "moved": 1, "max_move": "3.1e-1", "max_turn_deg": "0"},
}


def test_the_regularization_record_is_the_registers_item_once_of_is_resolved() -> None:
    """Owner, 11 October 2026: our regularizations are tracked with the packing's
    provenance, in the register's terms, so admission copies the record unchanged."""
    record = drive.regularization_record(REPORT)
    assert record is not None
    assert record["of_witness"] == "W-known-best-n026"
    assert record["provenance"]["source_key"] == "[kingbird]"
    assert record["by"] == "project"
    assert "evand/square-packing@675a5ea" in record["method"]
    assert record["side"] == "same"
    assert record["changes"] == {
        "merged_rotation_groups_deg": 0.7,
        # Square 8 onto the axis; 23 onto 45 degrees and 4 onto 30.5 are re-angled.
        "straightened": 1,
        "re_angled": 2,
    }
    assert record["identity"]["basis"] == "measured"
    as_item = {
        key: value for key, value in record.items() if key not in {"of_witness", "provenance"}
    }
    errors = list(_register_item_validator().iter_errors({**as_item, "of": "T-001"}))
    assert errors == []


def test_no_view_has_no_regularization_record() -> None:
    assert drive.regularization_record({**REPORT, "outputs": {}}) is None
    assert drive.regularization_record({**REPORT, "identity": None}) is None


# --------------------------------------------------------------------------------------
# One count, end to end
# --------------------------------------------------------------------------------------


def test_n26_runs_end_to_end(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    receipt = drive.run([26], Options(run_dir=run_dir), workers=1)
    report = json.loads((run_dir / "n-026/report.json").read_text())
    assert report["status"] == "ok"
    assert report["source"]["path"] == "packing/witnesses/known-best/n-026.yaml"
    assert report["solve"]["status"] == "KKT local min"
    assert report["solve"]["free"] == [8, 19, 23]
    assert report["regularize"]["level"] == 1
    solved = report["outputs"]["solved"]
    assert solved["relation"] == "solved"
    assert solved["routes"] == ALL_ROUTES
    assert Fraction(solved["side_exact"]) > Fraction(report["source"]["s_W_exact"])
    loaded = load_witness(
        run_dir / "n-026/view-solved.yaml", fallback_schema=drive.WITNESS_SCHEMA
    )
    assert loaded["id"] == "W-known-best-n026-regularized"
    assert loaded["certificate"]["derived_from"]["sha256"] == report["source"]["sha256"]
    assert report["identity"]["one_to_one"] is True
    assert sum(report["shades"]["house"]["before"]) == 26
    if report["outputs"]["same"] is None:
        assert report["outputs"]["same_refusal"].startswith("same-side")
        assert report["decision"]["row"] == 4
    else:
        same = report["outputs"]["same"]
        assert same["relation"] == "same"
        assert same["side_exact"] == report["source"]["s_W_exact"]
        assert report["identity"]["of"] == "same"
    row = receipt["counts"][0]
    assert row["n"] == 26
    assert receipt["generator"]["pin"] == "675a5ea"
    assert receipt["generator"]["patches"] == []
    assert receipt["cost"]["cpu_seconds"] > 0
    assert "26" in receipt["solve_outputs"]
    assert "26" in drive.report_table(receipt).splitlines()[1]
    # Deciding again from the written report reproduces the decision and keeps the cost.
    decided = report["decision"]
    again = drive.reclassify(run_dir)
    redone = json.loads((run_dir / "n-026/report.json").read_text())
    assert redone["decision"] == decided
    assert again["cost"] == receipt["cost"]
    assert again["reclassified"]["counts"] == [26]
