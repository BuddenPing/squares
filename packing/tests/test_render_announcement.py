"""The intake announcement says no more than the record holds, and credits by evidence.

`devtools.render_announcement` turns an intake pass's new results into lines the owner
can post (think-ghbx). These hold its numbers to the direction that keeps a printed bound
true, its "new best known" to the bounds on record, its handles to the evidence that
names them, and the command to the register as it stands.
"""

from __future__ import annotations

import textwrap
from collections.abc import Mapping
from datetime import date
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from devtools import render_announcement as ra
from devtools.check_standing import LOWER, UPPER, Stated
from devtools.render_recent_results import Records, load_records

SAMPLE = [f"T-{n}" for n in range(128, 147)]


@pytest.fixture(scope="module")
def records() -> Records:
    return load_records()


def exact(value: str | Fraction) -> ra.Span:
    number = Fraction(value)
    return ra.Span(number, number)


# --- Numbers ------------------------------------------------------------------------


def test_an_upper_bound_is_rounded_up_and_a_lower_bound_down() -> None:
    assert ra.shown(exact("13.812856253277056"), UPPER) == "13.81285626"
    assert ra.shown(exact(Fraction(1340000, 199529)), LOWER) == "6.71581574"
    # Where the value ends within the places, it is printed exactly, without zeros.
    assert ra.shown(exact(Fraction(291, 50)), LOWER) == "5.82"
    assert ra.shown(exact(Fraction(2297, 400)), LOWER) == "5.7425"
    for value in (Fraction(22, 7), Fraction(10**12 + 1, 10**11), Fraction(7, 3)):
        assert Fraction(ra.shown(exact(value), UPPER)) >= value
        assert Fraction(ra.shown(exact(value), LOWER)) <= value


def test_cut_decimals_are_rounded_up_from_the_top_of_what_they_stand_for() -> None:
    stated = Stated(Fraction("11.987099332245063"), Fraction(1, 10**15))
    bound = ra.Span.of_stated(stated)
    assert bound.open_high
    assert ra.shown(bound, UPPER) == "11.98709934"
    assert Fraction(ra.shown(bound, UPPER)) >= bound.high


def test_a_bound_is_printed_to_as_many_places_as_keep_it_better_than_the_previous() -> None:
    new, previous = exact("10.904821012320356"), exact("10.904821012324")
    printed = Fraction(ra.shown(new, UPPER, previous))
    assert new.high <= printed < previous.low
    low, earlier = exact("6.7158157460820"), exact("6.71581574608")
    printed = Fraction(ra.shown(low, LOWER, earlier))
    assert earlier.high < printed <= low.low


def test_a_margin_is_cut_to_two_significant_figures_never_rounded_up() -> None:
    assert ra.margin_text(Fraction("0.0006598949723517562")) == "6.5e-4"
    assert ra.margin_text(Fraction("0.0102")) == "1.0e-2"
    assert ra.margin_text(Fraction("0.00999999")) == "9.9e-3"
    assert ra.margin_text(Fraction(3)) == "3.0e0"
    assert ra.margin_text(Fraction(1, 10**17) * Fraction(22, 10)) == "2.2e-17"


def test_posted_length_counts_a_link_as_23_and_a_relation_sign_twice() -> None:
    assert ra.posted_length("s(5) ≤ 2 https://jlevy.github.io/squares/results.html#t-001") == (
        len("s(5) ≤ 2 ") + 1 + ra.URL_LENGTH
    )
    # The en dash and the typographic apostrophe are in X's light ranges.
    light = "n = 122\u2013126 \u2019"
    assert ra.posted_length(light) == len(light)


# --- Standing at a count ------------------------------------------------------------


def test_a_better_bound_on_record_takes_new_best_known_away() -> None:
    bound = exact("10.5")
    count = ra.assess(105, UPPER, bound, [ra.Rival("T-200", exact("10.4"), earlier=False)])
    assert not count.best
    assert count.bettered_by == ("T-200",)


def test_an_equal_bound_registered_first_takes_it_away_and_a_later_one_does_not() -> None:
    bound = exact("10.5")
    assert not ra.assess(1, UPPER, bound, [ra.Rival("T-1", exact("10.5"), earlier=True)]).best
    assert ra.assess(1, UPPER, bound, [ra.Rival("T-9", exact("10.5"), earlier=False)]).best


def test_the_previous_best_is_the_best_bound_on_record_before_the_entry() -> None:
    rivals = [
        ra.Rival("the n = 7 case record", exact("10.9"), earlier=True),
        ra.Rival("T-100", exact("10.8"), earlier=True),
        ra.Rival("T-300", exact("10.6"), earlier=False),
    ]
    count = ra.assess(7, UPPER, exact("10.5"), rivals)
    assert count.best
    assert count.previous == exact("10.8")
    assert count.margin == Fraction("0.3")
    lower = ra.assess(7, LOWER, exact("6"), [ra.Rival("T-1", exact("5.9"), earlier=True)])
    assert lower.best
    assert lower.margin == Fraction("0.1")


def test_cut_decimals_better_a_bound_only_where_every_number_they_stand_for_does() -> None:
    cut = ra.Span.of_stated(Stated(Fraction("10.5"), Fraction(1, 10)))
    # `10.5…` to one place stands for [10.5, 10.6).
    assert ra.better(cut, exact("10.6"), UPPER)
    assert not ra.better(cut, exact("10.59"), UPPER)
    assert ra.better(exact("10.6"), cut, LOWER)
    assert not ra.better(exact("10.59"), cut, LOWER)
    assert not ra.better(exact("10.5"), cut, UPPER)


# --- Credit and handles -------------------------------------------------------------


def handle(name: str, at: str) -> ra.Handle:
    return ra.Handle(name, at, "test")


def test_credit_names_keep_the_register_order_and_drop_the_separators() -> None:
    assert ra.credit_names("Ahmed et al. after Levy, Daniel") == ["Ahmed", "Levy", "Daniel"]
    assert ra.credit_names("wand125 after Tokoharu and Levy") == ["wand125", "Tokoharu", "Levy"]
    assert ra.credit_names("Couzo; Daniel after Couzo, Levy") == ["Couzo", "Daniel", "Levy"]
    assert ra.primary_names("Couzo after Xu; Daniel after Couzo") == ["Couzo", "Daniel"]
    assert ra.primary_names("Wang, Li after Kleddamag, Levy") == ["Wang", "Li"]


def test_a_handle_replaces_only_its_own_name_and_keeps_the_line_whole() -> None:
    handles = {"Levy": handle("Levy", "ojoshe"), "Ahmed": handle("Ahmed", "ManassehA06")}
    assert (
        ra.with_handles("wand125 after Tokoharu and Levy", handles)
        == "wand125 after Tokoharu and @ojoshe"
    )
    assert (
        ra.with_handles("Ahmed et al. after Levy, Daniel", handles)
        == "@ManassehA06 et al. after @ojoshe, Daniel"
    )
    assert ra.with_handles("Levyson after Xu", handles) == "Levyson after Xu"


PROFILE = """\
---
softschema:
  contract: packing.squares:Contributor/v1
  schema: contributor.schema.yaml
  envelope: contributor
  status: enforced
contributor:
  id: {id}
  display_name: '{display}'
  aliases: [{aliases}]
  links:
{links}
  sources:
    - id: primary-byline
      archive_path: LICENSE
      locator: 'test'
  provenance:
    - field: /display_name
      sources: [primary-byline]
---
"""


def write_profile(
    directory: Path, person: str, display: str, aliases: str, links: list[tuple[str, str, str]]
) -> None:
    lines = "\n".join(
        f"    - kind: {kind}\n      url: {url}\n      handle: {at}" for kind, url, at in links
    )
    directory.mkdir(exist_ok=True)
    (directory / f"{person}.md").write_text(
        PROFILE.format(id=person, display=display, aliases=aliases, links=lines),
        encoding="utf-8",
    )


def test_a_contributor_profile_gives_its_twitter_link_and_its_github_login(
    tmp_path: Path,
) -> None:
    write_profile(
        tmp_path,
        "joshua-levy",
        "Joshua Levy",
        "Levy, jlevy",
        [
            ("github", "https://github.com/jlevy", "jlevy"),
            ("twitter", "https://x.com/ojoshe", "ojoshe"),
        ],
    )
    write_profile(
        tmp_path,
        "evan-daniel",
        "Evan Daniel",
        "Daniel, evand",
        [("github", "https://github.com/evand", "evand")],
    )
    profiles = ra.load_profiles(tmp_path)
    assert {p.id for p in profiles} == {"joshua-levy", "evan-daniel"}
    handles, warnings = ra.resolve_handles(["Levy", "Daniel", "Xu"], profiles, None, {})
    assert warnings == []
    assert handles["Levy"].handle == "ojoshe"
    assert "joshua-levy.md" in handles["Levy"].source
    assert set(handles) == {"Levy"}
    assert ra.load_profiles(tmp_path / "absent") == []


def fake_github(
    users: Mapping[str, Mapping[str, Any]],
    *,
    issues: list[dict[str, Any]] | None = None,
    credited: Mapping[str, str] | None = None,
    primaries: Mapping[str, list[str]] | None = None,
) -> tuple[ra.GitHub, list[str]]:
    fetched: list[str] = []

    def fetch(login: str) -> Mapping[str, Any] | None:
        fetched.append(login)
        return users.get(login)

    github = ra.GitHub(
        owner="jlevy",
        issues=issues or [],
        credited_names=credited or {},
        primaries=primaries or {},
        fetch=fetch,
    )
    return github, fetched


def issue(number: int, author: str, *ids: str) -> dict[str, Any]:
    return {"number": number, "author": author, "results": [{"register": list(ids)}]}


def test_github_ties_a_login_to_a_credited_name_only_by_evidence() -> None:
    users = {
        "jlevy": {"name": "Joshua Levy", "twitter_username": "ojoshe"},
        "ry-xu": {"name": "Ryan Xu", "twitter_username": "small_LM"},
        "franciscouzo": {"name": "Francisco Couzo", "twitter_username": "fc_x"},
        "itsnaka": {"name": "natcha", "twitter_username": "naka_x"},
        "lollipoll": {"name": None, "twitter_username": "rehwaldt_x"},
        "evand": {"name": "Evan Daniel", "twitter_username": None},
    }
    github, _ = fake_github(
        users,
        issues=[
            issue(432, "ry-xu", "T-125"),
            issue(451, "franciscouzo", "T-128"),
            issue(481, "itsnaka", "T-136"),
            issue(425, "lollipoll", "T-117", "T-118"),
            issue(465, "evand", "T-131", "T-128"),
        ],
        credited={
            "Francisco Couzo": "Couzo",
            "Nate Chaoweeraprasit (itsnaka)": "Chaoweeraprasit",
            "Evan Daniel": "Daniel",
        },
        primaries={
            "T-125": ["ry-xu"],
            "T-128": ["Couzo"],
            "T-131": ["Daniel"],
            "T-136": ["Chaoweeraprasit"],
            "T-117": ["Rehwaldt"],
            "T-118": ["Rehwaldt"],
        },
    )
    names = ["Levy", "ry-xu", "Xu", "Couzo", "Chaoweeraprasit", "Rehwaldt", "Daniel"]
    handles, warnings = ra.resolve_handles(names, [], github, {})
    assert warnings == []
    assert {name: h.handle for name, h in handles.items()} == {
        "Levy": "ojoshe",
        "ry-xu": "small_LM",
        "Couzo": "fc_x",
        "Chaoweeraprasit": "naka_x",
        "Rehwaldt": "rehwaldt_x",
    }
    assert "PROJECT_AUTHOR" in handles["Levy"].source
    assert "credited_names" in handles["Chaoweeraprasit"].source
    assert "#425" in handles["Rehwaldt"].source
    # Xu is credited by surname and nothing in the record ties it to ry-xu's login; Daniel's
    # account declares no handle. Neither gets one.
    assert "Xu" not in handles
    assert "Daniel" not in handles


def test_an_issue_never_ties_the_owner_or_an_issue_that_credits_two_people() -> None:
    users = {"jlevy": {"twitter_username": "ojoshe"}, "evand": {"twitter_username": "ev"}}
    github, _ = fake_github(
        users,
        issues=[issue(1, "jlevy", "T-001"), issue(465, "evand", "T-131", "T-128")],
        primaries={"T-001": ["Bentz"], "T-131": ["Daniel"], "T-128": ["Couzo"]},
    )
    handles, _ = ra.resolve_handles(["Bentz", "Daniel", "Couzo"], [], github, {})
    assert handles == {}


def test_two_handles_for_one_name_give_none() -> None:
    users = {
        "alpha": {"name": "Ada Smith", "twitter_username": "one"},
        "beta": {"name": "Ada Smith", "twitter_username": "two"},
    }
    github, _ = fake_github(
        users,
        issues=[issue(1, "alpha"), issue(2, "beta")],
        credited={"Ada Smith": "Smith"},
    )
    handles, warnings = ra.resolve_handles(["Smith"], [], github, {})
    assert handles == {}
    assert len(warnings) == 1
    assert "Smith" in warnings[0]


def test_a_malformed_login_is_never_fetched() -> None:
    github, fetched = fake_github({}, issues=[issue(1, "../../orgs/x")])
    ra.resolve_handles(["Somebody"], [], github, {})
    assert "../../orgs/x" not in fetched


def test_a_profile_wins_over_github_and_github_over_the_record(tmp_path: Path) -> None:
    write_profile(
        tmp_path,
        "queuingtheorydotcom",
        "Queuingtheorydotcom",
        "Ahmed, ManassehA06",
        [("twitter", "https://x.com/ManassehA06", "ManassehA06")],
    )
    stated = {"Ahmed": handle("Ahmed", "from_record"), "Levy": handle("Levy", "from_record")}
    github, _ = fake_github({"jlevy": {"twitter_username": "ojoshe"}})
    handles, _ = ra.resolve_handles(
        ["Ahmed", "Levy"], ra.load_profiles(tmp_path), github, stated
    )
    assert handles["Ahmed"].handle == "ManassehA06"
    assert handles["Levy"].handle == "ojoshe"
    handles, _ = ra.resolve_handles(["Levy"], [], None, stated)
    assert handles["Levy"].handle == "from_record"


def test_every_handle_the_record_states_is_still_stated_there() -> None:
    found = ra.record_handles()
    assert found["Ahmed"].handle == "ManassehA06"
    assert "packing/frontier/n-011.md" in found["Ahmed"].source


def test_a_record_handle_whose_words_are_gone_fails_loudly(tmp_path: Path) -> None:
    (tmp_path / "case.md").write_text("Ahmed wrote a proof.\n", encoding="utf-8")
    table = (
        ra.RecordHandle("Ahmed", "ManassehA06", "case.md", "posts on X as [@ManassehA06]"),
    )
    with pytest.raises(SystemExit, match="no longer says"):
        ra.record_handles(table, tmp_path)


# --- The register as it stands ------------------------------------------------------


def test_every_printed_bound_is_true_and_beats_the_previous_best_where_it_is_new(
    records: Records,
) -> None:
    """Over the whole register: a printed upper bound is at least every number the entry
    states and a printed lower bound at most; where a count is the best known, the printed
    number is still strictly better than the previous best."""
    index = ra.rival_bounds(records)
    checked = 0
    for record in records.register.results:
        if record["kind"] not in ra.BOUND_KINDS:
            continue
        for count in ra.counts(record, records, index):
            printed = Fraction(ra.shown(count.bound, count.direction, count.previous))
            if count.direction == UPPER:
                assert printed >= count.bound.high, (record["id"], count.n)
            else:
                assert printed <= count.bound.low, (record["id"], count.n)
            if count.best and count.previous is not None:
                assert ra.better(exact(printed), count.previous, count.direction)
            checked += 1
    assert checked > 100


def test_since_selects_by_the_date_the_register_received_a_result(records: Records) -> None:
    chosen, skipped = ra.select(records, since="2026-10-10", min_significance=3)
    assert chosen
    assert all(str(r["registered"]) >= "2026-10-10" for r in chosen)
    assert all(int(r["significance"]["score"]) >= 3 for r in chosen)
    assert all("significance" in line.left_out for line in skipped)
    with pytest.raises(SystemExit, match="not in the register"):
        ra.select(records, ids=["T-999"])


def run(
    capsys: pytest.CaptureFixture[str], argv: list[str], **kwargs: Any
) -> tuple[list[str], str]:
    assert ra.main(argv, **kwargs) == 0
    captured = capsys.readouterr()
    return captured.out.splitlines(), captured.err


def test_the_announcement_of_the_sample_states_no_more_than_its_rungs(
    records: Records, capsys: pytest.CaptureFixture[str]
) -> None:
    lines, err = run(capsys, ["--ids", *SAMPLE, "--date", "2026-10-11"])
    head, body = lines[0], lines[1:]
    assert head == f"11 October 2026: {len(body)} new results"
    assert body
    for line in body:
        entry = line.rsplit("#", 1)[-1].upper()
        record = records.results[entry]
        assert line.endswith(ra.result_link(entry))
        if int(str(record["verification"])[1:]) < ra.VERIFIED_FROM:
            assert "not yet verified" in line
            assert "New best known" not in line
            assert "verified V" not in line
        assert "#" not in line.rsplit(" ", 1)[0], "no hashtags"
    # T-129 is scored 1; every result left out is said to be, with why.
    assert "left out T-129: significance 1, below 3" in err
    left = {
        line.split(":")[0].removeprefix("left out ")
        for line in err.splitlines()
        if line.startswith("left out")
    }
    printed = {line.rsplit("#", 1)[-1].upper() for line in body}
    assert left | printed == set(SAMPLE)
    assert not left & printed


def test_github_handles_reach_the_lines_and_their_sources_reach_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fetch(login: str) -> Mapping[str, Any] | None:
        return {"jlevy": {"name": "Joshua Levy", "twitter_username": "ojoshe"}}.get(login)

    lines, err = run(
        capsys, ["--ids", "T-128", "--date", "2026-10-11", "--github"], fetch=fetch
    )
    assert len(lines) == 2
    assert "@ojoshe" in lines[1]
    assert " Levy" not in lines[1]
    assert "@ojoshe for Levy: GitHub profile of jlevy" in err


def test_all_keeps_a_bettered_result_and_says_what_betters_it(
    capsys: pytest.CaptureFixture[str], records: Records
) -> None:
    index = ra.rival_bounds(records)
    bettered = next(
        record
        for record in records.register.results
        if record["kind"] in ra.BOUND_KINDS
        and (found := ra.counts(record, records, index))
        and not any(count.best for count in found)
        and int(record["significance"]["score"]) >= ra.MIN_SIGNIFICANCE
    )
    entry = str(bettered["id"])
    lines, err = run(capsys, ["--ids", entry, "--date", "2026-10-11"])
    assert lines == ["11 October 2026: 0 new results"]
    assert f"left out {entry}: the best known at no count" in err
    lines, _ = run(capsys, ["--ids", entry, "--date", "2026-10-11", "--all"])
    assert "; since " in lines[1]
    assert "New best known" not in lines[1]


def test_the_frontmatter_reader_reads_only_the_opening_block() -> None:
    text = textwrap.dedent(
        """\
        ---
        a: 1
        ---
        body
        ---
        b: 2
        """
    )
    assert ra.frontmatter(text) == "a: 1"
    assert ra.frontmatter("no front matter\n") == ""


def test_the_header_names_the_day_and_the_count() -> None:
    assert ra.header(date(2026, 10, 11), 1) == "11 October 2026: 1 new result"
    assert ra.header(date(2026, 1, 2), 12) == "2 January 2026: 12 new results"
