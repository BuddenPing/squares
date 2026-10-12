"""The finite steps of Guzhou0806's s(40) > 3359/500 (#485) hold, and refuse controls.

`devtools.audit_n40_new_supports` reads the retained new density and wand125's original
pool, decides the density's orbit facts and the claim's finite steps in exact rationals,
regenerates both kernel inputs, compares every value with both release receipts and
prices the continuous-pose replay. These tests read retained files only and run no
binary: the axis stage is the packet's receipt, judged as ``check-axis`` judges it.
"""

from __future__ import annotations

import dataclasses
import functools
import json
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools import audit_continuous_pose as t145
from devtools import audit_n40_new_supports as audit
from devtools.audit_n40_new_supports import CLAIM, RELEASE


@functools.cache
def raw() -> bytes:
    return audit.load_candidate()


@functools.cache
def pool() -> bytes:
    return audit.load_pool()


@functools.cache
def density() -> audit.Density:
    return audit.site_density(raw())


@functools.cache
def facts() -> audit.Facts:
    return audit.facts(density(), CLAIM, RELEASE)


@functools.cache
def report() -> dict[str, Any]:
    return audit.check_report()


def least() -> Fraction:
    return audit.least_bound(audit.read_slabs(audit.RECEIPTS["ci"]))[0]


def test_the_inputs_are_the_ones_the_receipts_decided() -> None:
    pose = audit.pose_input(density(), CLAIM, RELEASE)
    assert audit.sha256(pose) == audit.POSE_SHA256
    lines = pose.splitlines()
    assert lines[1] == b"0x1.fea0cf4cbf248p-1 0x1.fea0cf4cbf249p-1"
    assert lines[2] == b"5480"
    assert len(lines) == 5483
    axis = audit.axis_input(audit.axis_rows(density()), CLAIM)
    assert audit.sha256(axis) == audit.AXIS_SHA256
    assert axis.splitlines()[0] == b"6700000000 997318636 1000000000 1000000000 4999 5000 5480"


def test_the_orbits_are_what_the_release_says() -> None:
    s = audit.support_facts(raw(), pool())
    assert s.kinds == {"inherited": 522, "generated": 163}
    assert s.sites == s.positive == s.in_k == s.orbits == 685
    assert s.inherited_exact == 522
    assert s.inherited_distinct
    assert s.generated_outside_pool == 163
    assert s.inherited_positive_before == 427
    assert s.mass == Fraction(3999, 100)
    assert density().terms == 5480


def test_every_finite_check_holds_and_the_receipt_is_this_run() -> None:
    value = report()
    failed = [check["name"] for check in value["checks"] if not check["held"]]
    assert failed == []
    assert value["status"] == "FINITE_STEPS_HOLD"
    retained = (audit.RECEIPT_DIR / "finite-audit.json").read_text(encoding="utf-8")
    assert retained == json.dumps(value, indent=1, sort_keys=True) + "\n"


def test_the_scalars_are_the_releases() -> None:
    assert CLAIM.n * CLAIM.tau - CLAIM.mass == Fraction(1, 500)
    assert CLAIM.L / CLAIM.B == CLAIM.X == Fraction(3359, 500)
    assert Fraction(217911, 99764500) == CLAIM.X - audit.EARLIER
    assert CLAIM.B - CLAIM.A * audit.extent(CLAIM.eps) == audit.NEAR_AXIS_MARGIN
    assert least() == Fraction(9005397816695287, 2**53)
    assert len(CLAIM.slabs()) == 43


def test_the_axis_minimum_is_evaluated_again_at_its_minimiser() -> None:
    f = facts()
    assert f.minimiser == (3490012394, 6201340682)
    assert f.minimum == f.minimiser_capture == 1001486431423867090847280653
    assert f.minimiser_capture_g * 10**27 >= f.minimum
    assert f.nodes == (3293, 3293)
    assert f.evaluation_bound == 627444222088298915573283512797161984 < 2**125


def test_every_control_is_refused() -> None:
    controls = {str(item["control"]): item for item in report()["controls"]}
    assert sorted(controls) == ["D1", "D2", "D3", "G", "G2", "G3", "G4"]
    assert all(item["refused"] for item in controls.values())


def test_a_reweighting_that_keeps_the_orbit_facts_is_refused_by_the_input_digests() -> None:
    """D3 keeps every orbit fact and the mass, so only the binding of the density to
    the inputs both kernels decided can refuse it."""
    d3 = next(item for item in report()["controls"] if item["control"] == "D3")
    failed = set(d3["failed"])
    assert {"pose input: the receipts' input", "axis input: the receipts' input"} <= failed
    assert not any(
        name.startswith("density: ") and name != "density: the release's candidate"
        for name in failed
    )


def test_the_finite_checks_are_t145s_not_copies() -> None:
    for name in (
        "Facts",
        "facts",
        "input_checks",
        "chain_checks",
        "receipt_checks",
        "identity_checks",
        "finite_controls",
        "FiniteControl",
        "manifest",
        "pose_input",
    ):
        assert getattr(audit, name) is getattr(t145, name), name


def _copy_receipt(tmp_path: Path) -> Path:
    folder = tmp_path / "results"
    shutil.copytree(audit.RECEIPTS["ci"], folder)
    return folder


def _receipt_failures(folder: Path) -> list[str]:
    s = audit.support_facts(raw(), pool())
    checks = audit.receipt_checks(
        "ci",
        folder,
        CLAIM,
        facts(),
        release=RELEASE,
        admission=audit.release_admission(s, facts()),
    )
    return [c.name for c in checks if not c.held]


def test_a_slab_row_with_output_on_stderr_is_refused(tmp_path: Path) -> None:
    folder = _copy_receipt(tmp_path)
    rows = [json.loads(line) for line in (folder / "slabs.jsonl").read_text().splitlines()]
    rows[11]["stderr_sha256"] = audit.sha256(b"warning\n")
    (folder / "slabs.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
    failed = _receipt_failures(folder)
    assert "ci receipt: every slab verified as the contract runs it" in failed


def test_a_threshold_past_the_kernels_input_bounds_is_refused() -> None:
    wide = dataclasses.replace(CLAIM, tau=Fraction(10**8 - 1, 10**8))
    failed = [c.name for c in audit.chain_checks(wide, facts(), least(), RELEASE) if not c.held]
    assert "slabs: the kernel's threshold is at least tau" in failed


def test_a_minimiser_off_the_grid_is_not_a_vertex(tmp_path: Path) -> None:
    folder = tmp_path / "release-ci/results"
    folder.mkdir(parents=True)
    axis = json.loads((audit.RECEIPTS["ci"] / "axis.json").read_text())
    stdout = json.loads(axis["stdout"])
    stdout["minimizer_x_integer"] = str(int(stdout["minimizer_x_integer"]) + 1)
    axis["stdout"] = json.dumps(stdout)
    (folder / "axis.json").write_text(json.dumps(axis))
    moved = audit.facts(density(), CLAIM, dataclasses.replace(RELEASE, packet=tmp_path))
    assert not moved.minimiser_is_vertex
    failed = {c.name for c in audit.input_checks(moved, CLAIM, RELEASE) if not c.held}
    assert "axis: the minimiser is a vertex of the quadrant" in failed


def test_an_inherited_index_outside_the_pool_fails_a_check_rather_than_raising() -> None:
    data = json.loads(raw())
    inherited = [i for i, s in enumerate(data["sites"]) if s["kind"] == "inherited"]
    data["sites"][inherited[0]]["source_index"] = 10**6
    data["sites"][inherited[1]]["source_index"] = -1
    mutant = json.dumps(data).encode()
    s = audit.support_facts(mutant, pool())
    assert s.inherited_exact == 520
    assert s.inherited_positive_before <= 427
    failed = {c.name for c in audit.support_checks(s, audit.site_density(mutant)) if not c.held}
    assert "density: each inherited box is its pool row exactly, no row twice" in failed


def test_an_inherited_box_off_its_pool_row_is_refused() -> None:
    data = json.loads(raw())
    index = next(i for i, s in enumerate(data["sites"]) if s["kind"] == "inherited")
    data["sites"][index]["source_index"] += 1
    mutant = json.dumps(data).encode()
    checks = audit.support_checks(
        audit.support_facts(mutant, pool()), audit.site_density(mutant)
    )
    failed = {check.name for check in checks if not check.held}
    assert "density: each inherited box is its pool row exactly, no row twice" in failed


def test_a_changed_receipt_value_is_refused(tmp_path: Path) -> None:
    folder = _copy_receipt(tmp_path)
    receipt = json.loads((folder / "verification.json").read_text())
    receipt["admission"]["inherited_representatives"] = 523
    (folder / "verification.json").write_text(json.dumps(receipt))
    assert _receipt_failures(folder) == ["ci receipt: admission block"]


#: What the axis stage's judgement checks, the crate's two among them.
AXIS_STAGE_CHECKS = [
    "axis build: the retained source, the release's flags",
    "axis build: with the CI run's compiler, the CI run's binary",
    "axis run: the derived input, every output field both receipts'",
    "axis control H-above: tau = 62593/62500 gives AXIS_TEST_REFUSED",
    "axis control H-below: tau = 500743/500000 gives AXIS_COVERAGE_PROVED",
    "crate: reviewed source for a declared net, the binary embeds it",
    audit.CRATE_DECISION,
]


def test_the_axis_stage_receipt_is_this_run() -> None:
    value = audit.axis_report(audit.RECEIPT_DIR)
    assert [c["name"] for c in value["checks"]] == AXIS_STAGE_CHECKS
    assert all(c["held"] for c in value["checks"])
    retained = (audit.RECEIPT_DIR / "axis-check.json").read_text(encoding="utf-8")
    assert retained == json.dumps(value, indent=1, sort_keys=True) + "\n"


def test_an_axis_stage_without_the_crate_is_refused_unless_asked(tmp_path: Path) -> None:
    record = json.loads((audit.RECEIPT_DIR / "axis-stage.json").read_text())
    del record["crate"]
    (tmp_path / "axis-stage.json").write_text(json.dumps(record))
    value = audit.axis_report(tmp_path)
    assert [c["name"] for c in value["checks"] if not c["held"]] == [audit.CRATE_DECISION]
    assert value["status"] == "AXIS_STAGE_FAILED"
    partial = audit.axis_report(tmp_path, require_crate=False)
    assert [c["name"] for c in partial["checks"]] == AXIS_STAGE_CHECKS[:5]
    assert partial["status"] == "AXIS_STAGE_HOLDS"


def test_a_control_that_printed_no_json_fails_rather_than_raising(tmp_path: Path) -> None:
    record = json.loads((audit.RECEIPT_DIR / "axis-stage.json").read_text())
    record["runs"]["H-above"]["stdout"] = "terminate called after throwing\n"
    record["crate"]["stdout"] = "thread 'main' panicked\n"
    (tmp_path / "axis-stage.json").write_text(json.dumps(record))
    failed = {c["name"] for c in audit.axis_report(tmp_path)["checks"] if not c["held"]}
    assert failed == {
        "axis control H-above: tau = 62593/62500 gives AXIS_TEST_REFUSED",
        "crate: reviewed source for a declared net, the binary embeds it",
        audit.CRATE_DECISION,
    }


def test_the_axis_stage_receipt_holds_and_a_changed_one_does_not(tmp_path: Path) -> None:
    value = audit.axis_report(audit.RECEIPT_DIR)
    assert [c["name"] for c in value["checks"] if not c["held"]] == []
    assert value["status"] == "AXIS_STAGE_HOLDS"
    record = json.loads((audit.RECEIPT_DIR / "axis-stage.json").read_text())
    output = json.loads(record["runs"]["axis"]["stdout"])
    output["minimum_numerator"] = str(int(output["minimum_numerator"]) - 1)
    record["runs"]["axis"]["stdout"] = json.dumps(output)
    record["runs"]["H-above"]["exit_code"] = 0
    (tmp_path / "axis-stage.json").write_text(json.dumps(record))
    failed = {c["name"] for c in audit.axis_report(tmp_path)["checks"] if not c["held"]}
    assert failed == {
        "axis run: the derived input, every output field both receipts'",
        "axis control H-above: tau = 62593/62500 gives AXIS_TEST_REFUSED",
    }


def test_the_price_is_the_receipts_scaled_by_t145s_replay() -> None:
    assert audit.lpt_makespan([3.0, 3.0, 2.0, 2.0, 2.0], 2) == 7.0
    assert audit.lpt_makespan([5.0, 1.0], 4) == 5.0
    price = report()["price"]
    assert price["receipt_slab_seconds"] == {"local": 2655.3, "ci": 5229.5}
    assert 0.5 < price["predicted_slab_cpu_hours_here"] < 1.0
    walls = price["predicted_wall_seconds_here"]
    assert walls["4"] < walls["2"] < walls["1"] < 3600
