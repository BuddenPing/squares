"""The register's record of the regularized drawings, on synthetic entries.

Which registered result holds a drawn count's packing: the one attributing the
witness's source for a view at the witness's side, the one the verified upper bound rests
on for a view at the bound or for a view at a witness's side that is exactly the bound
where no result attributes the source, and none where no result answers or several do.
The generated block reads back as the data it was written from, and the register's
checker holds each item to the register.
"""

from __future__ import annotations

from typing import Any

from devtools import regularized_drawings as drawings
from devtools.check_results import regularized_drawings_problems
from sqpack.yamlio import safe_load

RESULTS = [
    {"id": "T-001", "scope": {"n_values": [5, 6]}, "attribution": {"source_keys": ["[A]"]}},
    {"id": "T-002", "scope": {"n_min": 5, "n_max": 9}},
    {"id": "T-003", "scope": {"n_values": [6]}, "attribution": {"source_keys": ["[A]"]}},
]
INDEX = "packing/atlas/known-best/regularized/index.json"


def entry(n: int, relation: str | None = None) -> dict[str, Any]:
    found: dict[str, Any] = {
        "n": n,
        "status": "regularized",
        "view": {"path": f"packing/atlas/known-best/regularized/n-{n:03d}-regularized.yaml.gz"},
        "regularization": {
            "n": n,
            "of_witness": f"W-known-best-n{n:03d}",
            "provenance": {"source_key": "[A]", "found_by": ["A"], "improved_by": []},
            "by": "project",
            "method": "Evan Daniel's search/regularize, through devtools.regularize_evand",
            "side": "solved" if relation == "bound" else "same",
            "changes": {"re_angled": 2},
            "identity": {
                "basis": "measured",
                "measured_in": INDEX,
                "one_to_one": True,
                "moved": 3,
                "max_move": 0.4216289,
                "max_turn_deg": 2.35479,
            },
        },
    }
    if relation:
        found["side"] = {"relation": relation}
    return found


def test_the_packing_is_the_result_holding_it_at_the_side_drawn() -> None:
    def resolve(n: int, key: str | None, relation: str | None = None, holders=()) -> Any:
        return drawings.packing_result(
            entry(n, relation), RESULTS, source_key=key, bound_holders=list(holders)
        )

    assert resolve(5, "[A]").of == "T-001"
    assert resolve(7, "[A]").of is None
    assert "no registered result" in resolve(7, "[A]").reason
    assert resolve(6, "[A]").of is None
    assert "several" in resolve(6, "[A]").reason
    assert resolve(6, "[A]", "bound", ["T-002"]).of == "T-002"
    assert resolve(6, "[A]", "bound", []).of is None


def test_a_witness_side_exactly_at_the_bound_falls_back_to_the_bound_holder() -> None:
    """T-151 certified witnesses' own sides exactly: a `same` view there that no result
    attributes is held by the result the bound rests on, and only when the side is exact."""
    found = entry(7, "same")
    found["side"]["view"] = "33/5"

    def resolve(holders: list[str], *, at: bool = True) -> Any:
        return drawings.packing_result(
            found, RESULTS, source_key="[B]", bound_holders=holders, side_at_bound=at
        )

    assert resolve(["T-002"]).of == "T-002"
    assert resolve(["T-002"], at=False).of is None
    assert resolve(["T-002", "T-003"]).of is None
    # A source some result attributes keeps that result, at the bound or not.
    attributed = drawings.packing_result(
        entry(5, "same"), RESULTS, source_key="[A]", bound_holders=["T-002"], side_at_bound=True
    )
    assert attributed.of == "T-001"
    assert drawings.at_bound(found, {"value": "6.6", "exact_form": "33/5"})
    assert drawings.at_bound(found, {"value": "6.6"})
    assert not drawings.at_bound(
        found, {"value": "6.6000001", "exact_form": "330000001/50000000"}
    )
    assert not drawings.at_bound(found, {"value": "6.6", "exact_form": "4 + sqrt(2)"})
    assert not drawings.at_bound(entry(7, "same"), {"value": "6.6"})


def test_the_block_reads_back_as_the_items_it_was_written_from() -> None:
    item = drawings.item(entry(5), "T-001")
    assert "of_witness" not in item
    assert "provenance" not in item
    text = drawings.block_text([item], [{"n": 7, "reason": "no registered result: [B]"}])
    assert text.startswith(drawings.MARKER)
    document = safe_load(text)[drawings.KEY]
    assert document["items"] == [item]
    assert document["unregistered"] == [{"n": 7, "reason": "no registered result: [B]"}]
    head, block = drawings.split("results: []\n\n" + text)
    assert (head, block) == ("results: []\n\n", text)


def test_a_number_in_exponent_form_reads_back_as_a_number() -> None:
    # n = 84's identity measures a turn of 1e-15 degrees, which JSON prints without a
    # point and YAML 1.1 then reads as a string.
    for value in (1e-15, 2e-07, 7.516648e-20, 1.5e300, 0.0, 2.35479, 3):
        assert safe_load(f"x: {drawings.scalar(value)}\n")["x"] == value


def test_the_checker_holds_each_item_to_the_register() -> None:
    scopes = {"T-001": {5, 6}, "T-002": {5, 6, 7, 8, 9}}
    good = drawings.item(entry(5), "T-001")
    register = {"regularized_drawings": {"items": [good], "unregistered": []}}
    assert regularized_drawings_problems(register, scopes, drift=False) == []
    elsewhere = {**good, "n": 7, "of": "T-001"}
    stranger = {**good, "n": 8, "of": "T-099", "by": "[A]"}
    lost = {**good, "n": 9, "of": "T-002", "identity": {**good["identity"], "moved": 10}}
    register = {
        "regularized_drawings": {
            "items": [good, good, elsewhere, stranger, lost],
            "unregistered": [{"n": 5, "reason": "x"}],
        }
    }
    assert regularized_drawings_problems(register, scopes, drift=False) == [
        "regularized drawing at n = 5 is listed twice",
        "regularized drawing at n = 7 names T-001, whose scope does not hold n = 7",
        "regularized drawing at n = 8 names T-099, which is not registered",
        "regularized drawing at n = 8 is by [A], not `project`",
        "regularized drawing at n = 9: identity.moved, 10, is more squares than n = 9",
        "regularized drawing at n = 5 is both an item and unregistered",
    ]
