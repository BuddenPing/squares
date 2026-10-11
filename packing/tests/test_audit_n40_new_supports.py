"""The finite steps of Guzhou0806's s(40) > 3359/500 (#485) hold, and refuse controls.

`devtools.audit_n40_new_supports` reads the retained new density and wand125's original
pool, decides the density's orbit facts and the claim's finite steps in exact rationals,
regenerates both kernel inputs, compares every value with both release receipts and
prices the continuous-pose replay. These tests read retained files only and run no
binary: the axis stage is the packet's receipt, judged as ``check-axis`` judges it.
"""

from __future__ import annotations

import functools
import json
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools import audit_n40_new_supports as audit
from devtools.audit_n40_new_supports import CLAIM


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
def facts() -> audit.InputFacts:
    return audit.input_facts(density())


@functools.cache
def report() -> dict[str, Any]:
    return audit.check_report()


def least() -> Fraction:
    return audit.least_bound(audit.read_slabs(audit.RECEIPTS["ci"]))[0]


def test_the_inputs_are_the_ones_the_receipts_decided() -> None:
    pose = audit.pose_input(density())
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
    assert sorted(controls) == ["D1", "D2", "G", "G2", "G3", "G4"]
    assert all(item["refused"] for item in controls.values())


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
    folder = tmp_path / "results"
    shutil.copytree(audit.RECEIPTS["ci"], folder)
    receipt = json.loads((folder / "verification.json").read_text())
    receipt["admission"]["inherited_representatives"] = 523
    (folder / "verification.json").write_text(json.dumps(receipt))
    s = audit.support_facts(raw(), pool())
    checks = audit.receipt_checks("ci", folder, s, facts(), density())
    assert [c.name for c in checks if not c.held] == ["ci receipt: admission block"]


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
