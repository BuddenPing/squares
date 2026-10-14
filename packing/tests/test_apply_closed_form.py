"""The closed form's reported lanes are what `devtools.apply_closed_form` writes."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

from devtools import apply_closed_form as tool
from sqpack.yamlio import safe_load


def _case(n: int) -> dict:
    text = (tool.FRONTIER / f"n-{n:03d}.md").read_text(encoding="utf-8")
    return safe_load(text.split("---\n")[1])["packing"]


def test_every_record_is_written() -> None:
    assert tool.stale() == []


def test_the_lanes_it_raises_and_the_ones_it_leaves() -> None:
    plans = {plan.n: plan for plan in tool.plans()}
    raised = sorted(n for n, plan in plans.items() if plan.raise_reported)
    assert len(raised) == 154
    # A registered report pending adoption is stronger at 125 (T-144) and 148 (T-179).
    assert 125 not in raised
    assert 148 not in raised
    assert {126, 149} <= set(raised)
    assert len([plan for plan in plans.values() if not plan.raise_reported]) == 33


def test_a_raised_lane_rounds_down_and_cites_the_report() -> None:
    field = _case(149)["reported_lower_bound"]
    assert field["evidence"] == [tool.REPORT]
    assert field["source_key"] == tool.SOURCE_KEY
    value, exact = Decimal(field["value"]), Fraction(field["exact_form"])
    plan = next(plan for plan in tool.plans() if plan.n == 149)
    assert Fraction(value) <= exact <= Fraction(plan.a30)
    assert exact > Fraction(plan.a30) - Fraction(1, 10**30)


def test_a_stronger_pending_report_keeps_its_count() -> None:
    assert _case(125)["reported_lower_bound"]["source_key"] != tool.SOURCE_KEY
    assert _case(148)["reported_lower_bound"]["source_key"] != tool.SOURCE_KEY
    assert tool.stronger(148, Decimal("12.2277")) == "T-179"
    assert tool.stronger(149, Decimal("12.2804")) is None


def test_a_proved_count_cites_without_moving_a_bound() -> None:
    packing = _case(63)
    assert packing["reported_lower_bound"]["source_key"] != tool.SOURCE_KEY
    assert set(tool.EQUAL_EVIDENCE) <= set(packing["evidence"])
