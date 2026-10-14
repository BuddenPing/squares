"""Evaluate every reported upper bound per count, in the order the reports arrived.

The owner's rule (2026-10-14): reports of ``s(n) <= v`` are taken per count ``n`` in the
order they reached this repository, and each one is recorded as a result while it is
stronger than the last; one that is not stronger than an earlier report is not recorded,
unless the owner names a key reason it should be. This module applies that rule to an
intake directory such as ``campaign/issue-intake/upper-bounds-20261014/``:

- **the start.** At ``n <= 324`` the standing side starts at the case record's reported
  upper bound on the tree (``packing/frontier/n-NNN.md``): its ``exact_form`` where that
  is a rational, else its ``value`` as a printed side within one unit of its last place.
  A register entry pending adoption that states a smaller upper bound
  (``check_standing.improvements``) lowers it. Above the horizon the start is the current
  beyond-horizon row of ``frontier/source-coverage.yaml``, else the grid ``ceil(sqrt n)``;
- **the walk.** The claims at ``n`` are sorted by ``reported_at`` (issue, comment or pull
  request creation; a claim added later by an edit or a commit carries its own time; a
  publication in a watched repository is dated by its first commit). A claim is
  *recorded* when every number it may be is below every number the standing side may be
  (`upper_bound_reports.below`), and it becomes the standing side; one equal to it (a
  tie) or above it is *not recorded*, and the verdict names what holds the count; one
  that print precision cannot order is *undecided*, never guessed, and stays beside the
  standing side until something decidably below both arrives;
- **exceptions** come only from the input's ``exceptions`` list, each with a count, a
  report and the owner's reason; such a claim is shown as recorded by exception and
  moves nothing;
- **owner decisions** the render lists without deciding: exact ties between different
  holders, a not-recorded claim whose certificate was first committed before the report
  that holds the count, every undecided comparison with what would decide it, claims
  whose time is unknown (kept out of the walk), and every count where a verdict changes
  when publications in watched repositories are not counted as reports.

Printed sides carry a rounding (`ROUNDINGS`), ``u`` being one unit in the last printed
place: ``up`` lies in ``(p - u, p]``; ``nearest`` and ``unstated`` within ``u`` of ``p``;
``binary64``, a double printed at more places than it determines, within one ulp of
``float(p)`` plus ``u``, as the lanes read #593's 16-place prints; ``cut`` (decimals
followed by an ellipsis) in ``[p, p + u)``; and ``exact`` is the number printed. A
claim's ``exact`` side, where a lane's frozen claim record or the certificate itself
states it, replaces the print in every comparison. ``restates`` says, for the README,
that a claim's certificate is another holder's packing; it changes no verdict. A
recorded claim is classified only where a source says what it is: ``refines`` (the same
configuration with a tighter certificate, naming the packing's finder and the entry that
holds it, which the register credits as a regularization) or ``new_packing`` (with
``continues`` where a continued search started from another arrangement); the render
lists every count where two or more refinements of one packing are each recorded.

The directory holds ``sources.yaml`` (what ``gather`` reads: the reports, their GitHub
coordinates, the lane claim records, and the printed sides transcribed from the reports),
``github-issues.json`` (the GitHub snapshot), ``ledger.yaml`` (the input of the rule) and
the rendered ``ledger.json`` and ``README.md``.

From ``packing/``, with the project interpreter::

    python -m devtools.intake_ledger gather [DIR] [--snapshot]
    python -m devtools.intake_ledger render [DIR] [--write | --check]
    python -m devtools.intake_ledger check [DIR]

``gather`` reads GitHub through ``gh`` (``--snapshot`` reuses ``github-issues.json``) and
the lanes' records with ``git show COMMIT:PATH``; it may need the network and runs in no
validation tier. ``render`` and ``check`` are offline; ``render --check`` fails when
either rendered file would change.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import re
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any, NotRequired, TypedDict, cast

import yaml
from strif import atomic_output_file

from devtools import check_source_coverage as coverage_check
from devtools import check_standing
from devtools import render_recent_results as view
from devtools.upper_bound_reports import Span, below, exact_span, grid_side, printed_span
from sqpack.yamlio import safe_load

MODULE = "devtools.intake_ledger"
ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
FRONTIER = ROOT / "frontier"
DEFAULT_DIRECTORY = ROOT / "campaign/issue-intake/upper-bounds-20261014"
SOURCES = "sources.yaml"
SNAPSHOT = "github-issues.json"
LEDGER = "ledger.yaml"
VERDICTS = "ledger.json"
README = "README.md"
LEDGER_FORMAT = "intake-ledger-v1"
SOURCES_FORMAT = "intake-ledger-sources-v1"
SNAPSHOT_FORMAT = "intake-ledger-github-v1"
VERDICTS_FORMAT = "intake-ledger-verdicts-v1"
GITHUB_REPOSITORY = "jlevy/squares"
#: The case corpus is ``n = 1..324``; above it the start is a beyond-horizon row or the grid.
HORIZON = 324
#: How a printed side was rounded; see the module docstring.
ROUNDINGS = ("up", "binary64", "nearest", "unstated", "cut", "exact")
KINDS = ("issue", "comment", "pull-request", "publication")
UNKNOWN = "unknown"
RECORDED = "recorded"
NOT_RECORDED = "not recorded"
UNDECIDED = "undecided"
BY_EXCEPTION = "recorded by exception"
#: What a recorded claim's certificate is, where a source says: a refinement of a standing
#: packing, a new packing, or neither stated (`Refines`, `NewPacking`).
REFINEMENT, NEW, UNCLASSIFIED = "refinement", "new packing", "unclassified"
BELOW, ABOVE, EQUAL = "below", "above", "equal"
SHOWN_PLACES = 12
#: The common-doc footer every durable document carries (`check_documentation`).
FOOTER = (
    "<!-- This document follows common-doc-guidelines.md.",
    "See github.com/jlevy/practical-prose and review guidelines before editing.",
    "-->",
)
_UTC = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
_DATE = re.compile(r"\d{4}-\d\d-\d\d")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?")
_FRACTION = re.compile(r"[0-9]+/[1-9][0-9]*")
_BEAD = re.compile(r"think-[a-z0-9]{4}")


class LedgerError(ValueError):
    """Refuse a malformed ledger, a claim outside its own print, or an unknown reference."""


def _require(condition: object, message: str) -> None:
    if not condition:
        raise LedgerError(message)


# --------------------------------------------------------------------------- the input


class RecordRelation(TypedDict):
    """A lane's exact comparison of an algebraic side with the case record it read.

    ``relation`` holds only while the record still prints ``value`` and ``exact_form``.
    """

    relation: str
    value: str
    exact_form: str
    read_from: str


class Refines(TypedDict):
    """Whose packing a claim's certificate tightens, as a source states it.

    A refinement is the same configuration with a tighter certificate: a padding
    reduction, an exact-contact refinement, an exact attainment. ``entry`` is the register
    entry or the report that holds the packing; ``source`` is where this is stated.
    """

    packing_of: str
    entry: str
    source: str


class NewPacking(TypedDict):
    """A claim its source states is a new packing, not a tighter certificate of one.

    ``continues`` names the arrangement a continued search started from, where the
    source says the packing continues one.
    """

    source: str
    continues: NotRequired[str]


class Claim(TypedDict):
    """One ``s(n) <= v`` a report states; see the module docstring for the fields."""

    n: int
    printed: str
    rounding: str
    exact: NotRequired[str]
    exact_from: NotRequired[str]
    first_committed: NotRequired[str]
    reported_at: NotRequired[str]
    record_relation: NotRequired[RecordRelation]
    restates: NotRequired[str]
    refines: NotRequired[Refines]
    new_packing: NotRequired[NewPacking]
    note: NotRequired[str]


class Lane(TypedDict):
    """A lane's branch and the commit whose frozen claim records the ledger read."""

    name: str
    branch: str
    commit: str
    note: NotRequired[str]


class Report(TypedDict):
    """One report: an issue, a comment, a pull request, or a watched-repository publication."""

    report: str
    url: str
    kind: str
    holders: str
    reported_at: str
    bead: str
    claims: list[Claim]
    note: NotRequired[str]


class OwnerException(TypedDict):
    """The owner's key reason to record a claim the rule does not record."""

    n: int
    report: str
    reason: str


class OtherItem(TypedDict):
    """An intake item that states no new upper bound, with its bead's disposition."""

    issue: str
    url: str
    holders: str
    kind: str
    bead: str
    disposition: str


class Ledger(TypedDict):
    format: str
    read_at_main: str
    read_on: str
    rule: str
    lanes: list[Lane]
    reports: list[Report]
    exceptions: list[OwnerException]
    other_items: list[OtherItem]


def number(text: str) -> Fraction:
    """A decimal, an integer or a fraction ``p/q``, exactly."""
    _require(_DECIMAL.fullmatch(text) or _FRACTION.fullmatch(text), f"not a number: {text!r}")
    return Fraction(text) if "/" in text else Fraction(Decimal(text))


def unit(printed: str) -> Fraction:
    """One unit in the last printed place."""
    return Fraction(1, 10 ** len(printed.partition(".")[2]))


def printed_side(printed: str, rounding: str) -> Span:
    """The numbers a printed side may be, by its rounding (`ROUNDINGS`)."""
    _require(rounding in ROUNDINGS, f"unknown rounding {rounding!r}")
    if rounding == "exact":
        return exact_span(number(printed))
    _require(_DECIMAL.fullmatch(printed) and "." in printed, f"not a decimal: {printed!r}")
    if rounding == "up":
        return printed_span(printed, "up")
    if rounding == "cut":
        value = number(printed)
        return Span(value, value + unit(printed), open_low=False, open_high=True)
    if rounding == "binary64":
        # The double nearest the side, rendered at more places than a double of that size
        # determines: the side lies within one ulp of the double plus one printed unit, as
        # the lanes read #593's 16-place prints (an exact side lies 1.2e-15 from them).
        value = number(printed)
        slack = Fraction(math.ulp(float(value))) + unit(printed)
        return Span(value - slack, value + slack, open_low=False, open_high=False)
    return printed_span(printed, "unstated")


def contains(span: Span, value: Fraction) -> bool:
    """Whether ``value`` is one of the numbers ``span`` may be."""
    above_low = value > span.low or (value == span.low and not span.open_low)
    below_high = value < span.high or (value == span.high and not span.open_high)
    return above_low and below_high


def claim_span(claim: Claim) -> Span:
    """The exact side where one is known, else the print."""
    if "exact" in claim:
        return exact_span(number(claim["exact"]))
    return printed_side(claim["printed"], claim["rounding"])


def load_yaml(path: Path) -> Any:
    return safe_load(path.read_text(encoding="utf-8"))


def _problems_of_claim(where: str, claim: Mapping[str, Any], reported_at: str) -> list[str]:
    problems: list[str] = []
    allowed = set(Claim.__annotations__)
    if set(claim) - allowed:
        problems.append(f"{where}: unknown fields {sorted(set(claim) - allowed)}")
    if not isinstance(claim.get("n"), int) or claim["n"] < 1:
        return [*problems, f"{where}: n is not a positive count"]
    try:
        span = printed_side(str(claim.get("printed")), str(claim.get("rounding")))
    except LedgerError as error:
        return [*problems, f"{where}: {error}"]
    if "exact" in claim:
        try:
            exact = number(str(claim["exact"]))
        except LedgerError as error:
            return [*problems, f"{where}: {error}"]
        if not contains(span, exact):
            problems.append(
                f"{where}: the exact side {claim['exact']} lies outside its own print "
                f"{claim['printed']} ({claim['rounding']})"
            )
    problems.extend(
        f"{where}: {key} is not a UTC time"
        for key in ("first_committed", "reported_at")
        if key in claim and not _UTC.fullmatch(str(claim[key]))
    )
    own = claim.get("reported_at")
    if own and reported_at != UNKNOWN and _UTC.fullmatch(str(own)) and own < reported_at:
        problems.append(f"{where}: a claim cannot arrive before its report")
    refines, new = claim.get("refines"), claim.get("new_packing")
    if refines is not None and new is not None:
        problems.append(f"{where}: a claim is a refinement or a new packing, not both")
    if refines is not None and not all(
        str(refines.get(key) or "").strip() for key in ("packing_of", "entry", "source")
    ):
        problems.append(f"{where}: refines names packing_of, entry and source")
    if new is not None and not str(new.get("source") or "").strip():
        problems.append(f"{where}: new_packing names its source")
    relation = claim.get("record_relation")
    if relation is not None and relation.get("relation") not in (BELOW, ABOVE, EQUAL):
        problems.append(f"{where}: record_relation is below, above or equal")
    return problems


def problems(ledger: Mapping[str, Any]) -> list[str]:
    """Every way the input breaks its contract; empty when it holds."""
    found: list[str] = []
    if ledger.get("format") != LEDGER_FORMAT:
        found.append(f"format is not {LEDGER_FORMAT}")
    if not _COMMIT.fullmatch(str(ledger.get("read_at_main"))):
        found.append("read_at_main is not a commit")
    if not _DATE.fullmatch(str(ledger.get("read_on"))):
        found.append("read_on is not a date")
    if not str(ledger.get("rule") or "").strip():
        found.append("the rule is not quoted")
    found.extend(
        f"lane {lane.get('name')}: a branch and a full commit"
        for lane in ledger.get("lanes") or []
        if not _COMMIT.fullmatch(str(lane.get("commit"))) or not lane.get("branch")
    )
    labels: set[str] = set()
    claimed: set[tuple[str, int]] = set()
    for report in ledger.get("reports") or []:
        label = str(report.get("report"))
        missing = {"report", "url", "kind", "holders", "reported_at", "bead", "claims"} - set(
            report
        )
        if missing:
            found.append(f"{label}: missing {sorted(missing)}")
            continue
        if label in labels:
            found.append(f"{label}: the report is listed twice")
        labels.add(label)
        if report["kind"] not in KINDS:
            found.append(f"{label}: unknown kind {report['kind']!r}")
        when = str(report["reported_at"])
        if when != UNKNOWN and not _UTC.fullmatch(when):
            found.append(f"{label}: reported_at is neither a UTC time nor {UNKNOWN}")
        if report["bead"] and not _BEAD.fullmatch(str(report["bead"])):
            found.append(f"{label}: bead is not a think-xxxx id")
        if not report["claims"]:
            found.append(f"{label}: no claims")
        for claim in report["claims"]:
            where = f"{label} n={claim.get('n')}"
            found.extend(_problems_of_claim(where, claim, when))
            key = (label, int(claim.get("n") or 0))
            if key in claimed:
                found.append(f"{where}: the claim is listed twice")
            claimed.add(key)
    for exception in ledger.get("exceptions") or []:
        key = (str(exception.get("report")), int(exception.get("n") or 0))
        if key not in claimed:
            found.append(f"exception {key}: names no claim of the ledger")
        if not str(exception.get("reason") or "").strip():
            found.append(f"exception {key}: states no reason")
    for item in ledger.get("other_items") or []:
        missing = set(OtherItem.__annotations__) - set(item)
        if missing:
            found.append(f"other item {item.get('issue')}: missing {sorted(missing)}")
    return found


def load_ledger(directory: Path) -> Ledger:
    value = load_yaml(directory / LEDGER)
    _require(isinstance(value, dict), f"{LEDGER} is not a mapping")
    found = problems(value)
    _require(not found, "; ".join(found))
    return cast("Ledger", value)


# --------------------------------------------------------------------------- the start


@dataclass(frozen=True)
class Side:
    """One side in the walk: the record on the tree, or one report's claim."""

    label: str
    holders: str
    span: Span
    shown: str
    value: Fraction
    kind: str
    reported_at: str = ""
    first_committed: str = ""
    exact: bool = False
    relation: RecordRelation | None = None
    record_print: tuple[str, str] | None = None
    decide: str = ""
    restates: str = ""
    refines: Refines | None = None
    new_packing: NewPacking | None = None


def shown(value: Fraction) -> str:
    """``value`` rounded up at `SHOWN_PLACES` places."""
    scaled = value * 10**SHOWN_PLACES
    whole = math.ceil(scaled)
    text = str(whole).rjust(SHOWN_PLACES + 1, "0")
    return f"{text[:-SHOWN_PLACES]}.{text[-SHOWN_PLACES:]}"


def scientific(value: Fraction) -> str:
    return f"{float(value):.2e}"


def _record_holders(bound: Mapping[str, Any]) -> str:
    found = [str(name) for name in bound.get("found_by") or []]
    improved = [str(name) for name in bound.get("improved_by") or []]
    text = ", ".join(found) or str(bound.get("source_key") or "")
    return f"{text}, improved by {', '.join(improved)}" if improved else text


_OPERATORS: Mapping[type[ast.operator], Callable[[Fraction, Fraction], Fraction]] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}


def _evaluate(node: ast.expr) -> Fraction:
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return Fraction(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_evaluate(node.operand)
    raise LedgerError("not a rational expression")


def rational_form(text: str) -> Fraction | None:
    """An exact form that is a rational, such as ``53/7`` or ``7 + (4/7)``; None for a
    closed form with a root, or anything else that is not integer arithmetic."""
    if not text or not re.fullmatch(r"[0-9+\-*/(). ]+", text):
        return None
    try:
        return _evaluate(ast.parse(text, mode="eval").body)
    except LedgerError, SyntaxError, ZeroDivisionError:
        return None


def record_side(n: int, bound: Mapping[str, Any], entries: Iterable[str]) -> Side:
    """The case record's reported upper bound: its rational exact form, else its print."""
    named = ", ".join(sorted(entries)) or str(bound.get("source_key") or "")
    label = f"record {named}"
    holders = _record_holders(bound)
    value = str(bound["value"])
    form = str(bound.get("exact_form") or "")
    rational = rational_form(form)
    if rational is not None:
        return Side(
            label,
            holders,
            exact_span(rational),
            shown(rational),
            rational,
            "record",
            exact=True,
        )
    if "." not in value:
        exact = number(value)
        return Side(label, holders, exact_span(exact), value, exact, "record", exact=True)
    decide = f"an exact comparison with the closed form {form}" if form else ""
    return Side(
        label,
        holders,
        printed_side(value, "nearest"),
        value,
        number(value),
        "record",
        record_print=(value, form),
        decide=decide or f"the exact side behind the record's print {value} at n = {n}",
    )


def pending_side(record: Mapping[str, Any], stated: check_standing.Stated) -> Side:
    """A register entry pending adoption, at the bound its words state."""
    if stated.slack:
        span = Span(stated.value, stated.value + stated.slack, open_low=False, open_high=True)
    else:
        span = exact_span(stated.value)
    entry = str(record["id"])
    keys = (record.get("attribution") or {}).get("source_keys") or []
    holders = ", ".join(str(key) for key in keys) or entry
    return Side(
        f"register {entry}, pending adoption",
        holders,
        span,
        shown(stated.value),
        stated.value,
        "register",
        exact=not stated.slack,
        decide=f"{entry}'s exact side" if stated.slack else "",
    )


def lowered(start: Side, pending: Sequence[Side]) -> Side:
    """The start, lowered by the smallest pending register bound decidably below it."""
    below_start = [side for side in pending if below(side.span, start.span)]
    smallest = [
        side
        for side in below_start
        if all(below(side.span, other.span) for other in below_start if other is not side)
    ]
    return smallest[0] if smallest else start


def beyond_side(n: int, rows: Mapping[int, Mapping[str, Any]]) -> Side:
    """Above the horizon: the current beyond-horizon row, else the grid."""
    row = rows.get(n)
    if row is None:
        grid = grid_side(n)
        return Side(
            "the grid", "ceil(sqrt n)", exact_span(grid), str(grid), grid, "record", exact=True
        )
    value = str(row["value"])
    return Side(
        f"beyond-horizon row {row['source_id']}",
        str(row["source_id"]),
        printed_side(value, "nearest"),
        value,
        number(value),
        "record",
        decide=f"the exact side of the beyond-horizon row {row['source_id']} at n = {n}",
    )


def tree_starts(counts: Iterable[int]) -> dict[int, Side]:
    """Each count's start, read from the records on the tree."""
    wanted = sorted(set(counts))
    starts: dict[int, Side] = {}
    inside = [n for n in wanted if n <= HORIZON]
    if inside:
        records = view.load_records()
        pending: dict[int, list[Side]] = {}
        for record in records.register.results:
            if view.standing(record, records) != view.PENDING_ADOPTION:
                continue
            for finding in check_standing.improvements(record, records):
                if finding.direction == check_standing.UPPER:
                    pending.setdefault(finding.n, []).append(
                        pending_side(record, finding.stated)
                    )
        for n in inside:
            bound = coverage_check.parse_case(FRONTIER / f"n-{n:03d}.md")[
                "reported_upper_bound"
            ]
            entries = view.lane_holders(n, records, "upper", ("reported",))
            starts[n] = lowered(record_side(n, bound, entries), pending.get(n, []))
    outside = [n for n in wanted if n > HORIZON]
    if outside:
        coverage = load_yaml(coverage_check.COVERAGE)
        rows = coverage_check.current_beyond_horizon(coverage)
        for n in outside:
            starts[n] = beyond_side(n, rows)
    return starts


# --------------------------------------------------------------------------- the walk


def entry_side(report: Report, claim: Claim) -> Side:
    span = claim_span(claim)
    exact = "exact" in claim or claim["rounding"] == "exact"
    value = number(claim.get("exact", claim["printed"]))
    decide = "" if exact else f"the exact side of {report['report']} at n = {claim['n']}"
    if exact:
        display = shown(value)
    elif len(claim["printed"].partition(".")[2]) > SHOWN_PLACES:
        display = shown(span.high)
    else:
        display = claim["printed"]
    return Side(
        report["report"],
        report["holders"],
        span,
        display,
        value,
        report["kind"],
        reported_at=claim.get("reported_at", report["reported_at"]),
        first_committed=claim.get("first_committed", ""),
        exact=exact,
        relation=claim.get("record_relation"),
        decide=decide,
        restates=claim.get("restates", ""),
        refines=claim.get("refines"),
        new_packing=claim.get("new_packing"),
    )


def compare(side: Side, other: Side) -> str:
    """Where ``side`` stands against ``other``: below, above, equal or undecided.

    An algebraic side's frozen relation to the case record replaces the spans while the
    record still prints what the lane read.
    """
    if side.relation is not None and other.record_print is not None:
        value, form = other.record_print
        if (side.relation["value"], side.relation["exact_form"]) == (value, form):
            return side.relation["relation"]
    if below(side.span, other.span):
        return BELOW
    if below(other.span, side.span):
        return ABOVE
    if side.exact and other.exact and side.span == other.span:
        return EQUAL
    return UNDECIDED


@dataclass
class Step:
    """One claim's verdict in the walk at one count."""

    side: Side
    verdict: str
    reason: str
    holders: list[Side]
    against: list[Side] = field(default_factory=list)
    exception: str = ""


@dataclass
class Walk:
    n: int
    start: Side
    steps: list[Step]
    standing: list[Side]


def decider(side: Side, others: Sequence[Side]) -> str:
    needed = [item.decide for item in (side, *others) if item.decide]
    return "; ".join(dict.fromkeys(needed)) or "an exact comparison of the two sides"


def walk(
    n: int,
    start: Side,
    entries: Sequence[Side],
    exceptions: Mapping[tuple[int, str], str] | None = None,
) -> Walk:
    """The owner's rule at one count: each claim in report order against the standing side.

    The standing side is a set: the record, then each recorded claim, together with any
    undecided claim nothing has since been decidably below. A claim is recorded only when
    it is below every member; it is not recorded when it is above or exactly equal to
    one; otherwise it is undecided and joins the set.
    """
    exceptions = exceptions or {}
    standing = [start]
    steps: list[Step] = []
    for side in sorted(entries, key=lambda item: (item.reported_at, item.label)):
        relations = [(member, compare(side, member)) for member in standing]
        above = [member for member, relation in relations if relation == ABOVE]
        equal = [member for member, relation in relations if relation == EQUAL]
        unsure = [member for member, relation in relations if relation == UNDECIDED]
        if all(relation == BELOW for _, relation in relations):
            step = Step(side, RECORDED, BELOW, [member for member, _ in relations])
            standing = [side]
        elif above or equal:
            reason = ABOVE if above else EQUAL
            step = Step(side, NOT_RECORDED, reason, above or equal)
        else:
            step = Step(side, UNDECIDED, UNDECIDED, unsure, against=unsure)
            standing = [member for member in standing if compare(member, side) != ABOVE]
            standing.append(side)
        reason = exceptions.get((n, side.label))
        if reason and step.verdict != RECORDED:
            step.verdict, step.exception = BY_EXCEPTION, reason
        steps.append(step)
    return Walk(n, start, steps, standing)


# --------------------------------------------------------------------------- the render


def _when(text: str) -> str:
    return text.replace("T", " ").removesuffix("Z") + "Z" if _UTC.fullmatch(text) else text


def held_by(step: Step) -> str:
    return ", ".join(member.label for member in step.holders)


def _difference(step: Step) -> str:
    """The claim against what it was decided by, as a distance and a direction."""
    if step.reason == EQUAL:
        return "equal"
    if step.reason == UNDECIDED or not step.holders:
        return ""
    gap = min(abs(member.value - step.side.value) for member in step.holders)
    word = "below" if step.reason == BELOW else "above"
    return f"{word} by {scientific(gap)}"


def step_record(step: Step) -> dict[str, Any]:
    side = step.side
    record: dict[str, Any] = {
        "report": side.label,
        "kind": side.kind,
        "reported_at": side.reported_at,
        "side": side.shown,
        "exact": side.exact,
        "verdict": step.verdict,
        "reason": step.reason,
        "decided_against": [member.label for member in step.holders],
        "difference": _difference(step),
    }
    if side.first_committed:
        record["first_committed"] = side.first_committed
    if UNDECIDED in (step.verdict, step.reason):
        record["decide_by"] = decider(side, step.against)
    if step.exception:
        record["exception"] = step.exception
    if side.restates:
        record["restates"] = side.restates
    if side.refines is not None:
        record["packing"] = {
            "kind": REFINEMENT,
            "packing_of": side.refines["packing_of"],
            "entry": side.refines["entry"],
        }
    elif side.new_packing is not None:
        record["packing"] = {
            "kind": NEW,
            **{key: value for key, value in side.new_packing.items() if key == "continues"},
        }
    return record


def side_record(side: Side) -> dict[str, Any]:
    return {
        "label": side.label,
        "holders": side.holders,
        "side": side.shown,
        "exact": side.exact,
    }


def _entries(ledger: Ledger, *, publications: bool) -> tuple[dict[int, list[Side]], list[Any]]:
    by_count: dict[int, list[Side]] = {}
    unknown: list[Any] = []
    for report in ledger["reports"]:
        if report["kind"] == "publication" and not publications:
            continue
        for claim in report["claims"]:
            side = entry_side(report, claim)
            if side.reported_at == UNKNOWN:
                unknown.append({"n": claim["n"], "report": report["report"]})
                continue
            by_count.setdefault(claim["n"], []).append(side)
    return by_count, unknown


def counts_of(ledger: Ledger) -> list[int]:
    return sorted({claim["n"] for report in ledger["reports"] for claim in report["claims"]})


def evaluate(ledger: Ledger, starts: Mapping[int, Side]) -> dict[str, Any]:
    """Every verdict, the owner decisions and the per-report summary, as ``ledger.json``."""
    exceptions = {
        (item["n"], item["report"]): item["reason"] for item in ledger.get("exceptions", [])
    }
    entries, unknown = _entries(ledger, publications=True)
    alternative_entries, _ = _entries(ledger, publications=False)
    walks = [walk(n, starts[n], entries.get(n, []), exceptions) for n in counts_of(ledger)]
    alternative = {
        n: walk(n, starts[n], alternative_entries.get(n, []), exceptions)
        for n in counts_of(ledger)
    }
    counts = []
    for result in walks:
        steps = [step_record(step) for step in result.steps]
        changed = publication_changes(result, alternative[result.n])
        counts.append(
            {
                "n": result.n,
                "start": side_record(result.start),
                "steps": steps,
                "best_now": [side_record(side) for side in result.standing],
                "publication_dependent": changed,
            }
        )
        if changed:
            counts[-1]["best_now_without_publications"] = [
                side_record(side) for side in alternative[result.n].standing
            ]
    return {
        "format": VERDICTS_FORMAT,
        "read_at_main": ledger["read_at_main"],
        "read_on": ledger["read_on"],
        "counts": counts,
        "summary": tally(walks),
        "reports": report_summaries(ledger, walks),
        "owner_decisions": {
            **owner_decisions(ledger, walks, unknown, counts),
            "refinement_chains": refinement_chains(walks),
        },
        "other_items": ledger.get("other_items", []),
    }


NOT_IN_WALK = "not in the walk"


def publication_changes(default: Walk, without: Walk) -> list[dict[str, Any]]:
    """The verdicts at one count that differ when publications are not counted as reports.

    A publication the default walk records or leaves undecided drops out of the other walk;
    any other report is listed where its verdict differs.
    """
    other = {step.side.label: step for step in without.steps}
    changed = []
    for step in default.steps:
        alternative = other.get(step.side.label)
        if alternative is None:
            if step.verdict == NOT_RECORDED:
                continue
            verdict, held = NOT_IN_WALK, ""
        elif alternative.verdict == step.verdict:
            continue
        else:
            verdict, held = alternative.verdict, held_by(alternative)
        changed.append(
            {
                "report": step.side.label,
                "with_publications": step.verdict,
                "held_by_with": held_by(step),
                "without_publications": verdict,
                "held_by_without": held,
            }
        )
    return changed


def kind_of(step: Step) -> str:
    """What a claim's certificate is, where its source says (`REFINEMENT`, `NEW`)."""
    if step.side.refines is not None:
        return REFINEMENT
    return NEW if step.side.new_packing is not None else UNCLASSIFIED


def _refined(step: Step) -> dict[str, str]:
    refines = step.side.refines
    return (
        {}
        if refines is None
        else {"packing_of": refines["packing_of"], "entry": refines["entry"]}
    )


def tally(walks: Sequence[Walk]) -> dict[str, int]:
    """The verdicts over every count, recorded claims split by what they are."""
    steps = [step for result in walks for step in result.steps]
    recorded = [step for step in steps if step.verdict == RECORDED]
    return {
        "counts": len(walks),
        "claims": len(steps),
        "recorded_new": sum(kind_of(step) == NEW for step in recorded),
        "recorded_new_continuing": sum(
            kind_of(step) == NEW and "continues" in (step.side.new_packing or {})
            for step in recorded
        ),
        "recorded_refinement": sum(kind_of(step) == REFINEMENT for step in recorded),
        "recorded_unclassified": sum(kind_of(step) == UNCLASSIFIED for step in recorded),
        "recorded_by_exception": sum(step.verdict == BY_EXCEPTION for step in steps),
        "not_recorded": sum(step.verdict == NOT_RECORDED for step in steps),
        "undecided": sum(step.verdict == UNDECIDED for step in steps),
    }


def _chain_root(
    step: Step, recorded: Mapping[str, Step], seen: frozenset[str] = frozenset()
) -> str:
    """The packing a recorded claim belongs to: itself, or what its refinement tightens."""
    refines = step.side.refines
    if refines is None:
        return step.side.label
    earlier = recorded.get(refines["entry"])
    if earlier is None or refines["entry"] in seen:
        return refines["entry"]
    return _chain_root(earlier, recorded, seen | {step.side.label})


def refinement_chains(walks: Sequence[Walk]) -> list[dict[str, Any]]:
    """Counts where two or more recorded refinements tighten one packing, with margins.

    A refinement's ``entry`` that names a report recorded at the same count is followed
    to that report's own packing, so a refinement of a refinement joins its chain.
    """
    chains = []
    for result in walks:
        recorded = {step.side.label: step for step in result.steps if step.verdict == RECORDED}

        groups: dict[str, list[Step]] = {}
        for step in recorded.values():
            if step.side.refines is not None:
                groups.setdefault(_chain_root(step, recorded), []).append(step)
        chains.extend(
            {
                "n": result.n,
                "packing": packing,
                "packing_of": group[0].side.refines["packing_of"]
                if group[0].side.refines
                else "",
                "refinements": [
                    {
                        "report": step.side.label,
                        "difference": _difference(step),
                        "decided_against": held_by(step),
                    }
                    for step in group
                ],
            }
            for packing, group in groups.items()
            if len(group) >= 2
        )
    return chains


def report_summaries(ledger: Ledger, walks: Sequence[Walk]) -> list[dict[str, Any]]:
    steps: dict[str, list[tuple[int, Step]]] = {}
    for result in walks:
        for step in result.steps:
            steps.setdefault(step.side.label, []).append((result.n, step))
    summaries = []
    for report in sorted(
        ledger["reports"], key=lambda item: (item["reported_at"], item["report"])
    ):
        own = steps.get(report["report"], [])
        summaries.append(
            {
                "report": report["report"],
                "url": report["url"],
                "kind": report["kind"],
                "holders": report["holders"],
                "reported_at": report["reported_at"],
                "bead": report["bead"],
                "counts": sorted(claim["n"] for claim in report["claims"]),
                "recorded": [n for n, step in own if step.verdict == RECORDED],
                "recorded_new": [
                    n for n, step in own if step.verdict == RECORDED and kind_of(step) == NEW
                ],
                "recorded_refinement": [
                    {"n": n, **_refined(step)}
                    for n, step in own
                    if step.verdict == RECORDED and kind_of(step) == REFINEMENT
                ],
                "recorded_unclassified": [
                    n
                    for n, step in own
                    if step.verdict == RECORDED and kind_of(step) == UNCLASSIFIED
                ],
                "recorded_by_exception": [n for n, step in own if step.verdict == BY_EXCEPTION],
                "not_recorded": [
                    {"n": n, "reason": step.reason, "held_by": held_by(step)}
                    for n, step in own
                    if step.verdict == NOT_RECORDED
                ],
                "undecided": [
                    {"n": n, "against": held_by(step)}
                    for n, step in own
                    if step.verdict == UNDECIDED
                ],
            }
        )
    return summaries


def _names(holders: str) -> set[str]:
    """The people or groups a credit names, without logins in parentheses."""
    plain = re.sub(r"\([^)]*\)", "", holders).replace("improved by", ",").replace(" and ", ",")
    return {name.strip().lower() for name in plain.split(",") if name.strip()}


def same_holder(first: str, second: str) -> bool:
    """Whether two credits share a holder: a tie between them is no owner decision."""
    return bool(_names(first) & _names(second))


def owner_decisions(
    ledger: Ledger, walks: Sequence[Walk], unknown: list[Any], counts: Sequence[Any]
) -> dict[str, Any]:
    holders = {report["report"]: report["holders"] for report in ledger["reports"]}
    ties: list[dict[str, Any]] = []
    early: list[dict[str, Any]] = []
    undecided: list[dict[str, Any]] = []
    for result in walks:
        for step in result.steps:
            side = step.side
            if step.reason == EQUAL:
                ties.extend(
                    {
                        "n": result.n,
                        "report": side.label,
                        "holders": side.holders,
                        "tied_with": member.label,
                        "tied_holders": member.holders,
                    }
                    for member in step.holders
                    if not same_holder(member.holders, side.holders)
                )
            if step.verdict == NOT_RECORDED and side.first_committed:
                early.extend(
                    {
                        "n": result.n,
                        "report": side.label,
                        "first_committed": side.first_committed,
                        "reported_at": side.reported_at,
                        "held_by": member.label,
                        "held_by_reported_at": member.reported_at,
                        "reason": step.reason,
                    }
                    for member in step.holders
                    if member.reported_at and side.first_committed < member.reported_at
                )
            if step.verdict == UNDECIDED:
                undecided.append(
                    {
                        "n": result.n,
                        "report": side.label,
                        "against": held_by(step),
                        "decide_by": decider(side, step.against),
                    }
                )
    dependent = [
        {
            "n": count["n"],
            **change,
            "best_now_without": " or ".join(
                f"{side['label']} {side['side']}"
                for side in count["best_now_without_publications"]
            ),
        }
        for count in counts
        for change in count["publication_dependent"]
    ]
    return {
        "exact_ties": ties,
        "first_commit_before_report": early,
        "undecided": undecided,
        "publication_dependent": dependent,
        "unknown_times": [{**item, "holders": holders[item["report"]]} for item in unknown],
    }


def _compress(counts: Iterable[int]) -> str:
    return check_standing.compress(sorted(counts)).replace(check_standing.EN_DASH, "-") or "-"


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _report_link(label: str, url: str) -> str:
    return f"[{_cell(label)}]({url})"


def readme(ledger: Ledger, verdicts: Mapping[str, Any]) -> str:
    """The human tables: the rule, per report, per count, owner decisions, other items."""
    lines = [
        "# Upper-Bound Reports, Count by Count, in Report Order",
        "",
        f"<!-- GENERATED by {MODULE} render from ledger.yaml. Do not edit. -->",
        "",
        (
            f"Read against `main` at `{ledger['read_at_main']}` on {ledger['read_on']}. "
            f"Rendered by `python -m {MODULE} render` from [ledger.yaml](ledger.yaml), which "
            f"`gather` writes from [sources.yaml](sources.yaml), "
            f"[github-issues.json](github-issues.json) and the lanes' frozen claim records; "
            f"the verdicts are also in [ledger.json](ledger.json)."
        ),
        "",
        "## The Rule",
        "",
        "The owner's rule: “" + " ".join(ledger["rule"].split()) + "”",
        "",
        (
            "At each count the standing side starts at the record on `main`. For n ≤ 324 that "
            "is the case record's reported upper bound (`packing/frontier/n-NNN.md`): its "
            "exact form where that is a rational, else its printed value within one unit of "
            "its last place, lowered by a register entry pending adoption that states a "
            "smaller bound. Above 324 it is the current beyond-horizon row of "
            "`frontier/source-coverage.yaml`, else the grid ⌈√n⌉. The claims are then taken in "
            "the order they reached this repository: issue, comment or pull-request creation, "
            "the update comment for a claim added to an issue later, the commit for a claim "
            "added to a pull request later, and the first commit for a publication in a "
            "watched repository that no issue reports. A claim is recorded when every number "
            "it may be is below every number the standing side may be, and it becomes the "
            "standing side. A claim equal to the standing side (a tie: the earlier holder "
            "keeps it) or above it is not recorded, and the table names what holds the count. "
            "A comparison the printed precision cannot decide is undecided; the undecided "
            "claim stays beside the standing side until a claim is decidably below both. Exact "
            "sides come from the lanes' frozen claim records or, where `ledger.yaml` says so, "
            "from the certificate at its pinned commit; this ledger compares sides and "
            "verifies no certificate. Sides are shown rounded up at 12 places where exact, as "
            "printed otherwise."
        ),
        "",
        "## Counts",
        "",
        *_count_lines(verdicts["summary"]),
        "",
        "## Lane Records Read",
        "",
        (
            "Exact sides marked as a lane's come from these commits' `acquisition/claims.json` "
            "(and `algebraic-claims.json`) files."
        ),
        "",
        "| Lane | Branch | Commit | Note |",
        "| --- | --- | --- | --- |",
        *[
            f"| {lane['name']} | `{lane['branch']}` | `{lane['commit']}` "
            f"| {lane.get('note', '')} |"
            for lane in ledger["lanes"]
        ],
        "",
        "## Per Report",
        "",
        (
            "| Report | Holder | Reported | Counts claimed | Recorded: new packing "
            "| Recorded: refinement (whose packing) | Recorded: unclassified "
            "| Not recorded (held by) | Undecided | Bead |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for summary in verdicts["reports"]:
        held: dict[str, list[int]] = {}
        for item in summary["not_recorded"]:
            held.setdefault(item["held_by"], []).append(item["n"])
        not_recorded = "; ".join(f"{_compress(ns)} ({who})" for who, ns in held.items()) or "-"
        undecided = _compress(item["n"] for item in summary["undecided"])
        whose: dict[str, list[int]] = {}
        for item in summary["recorded_refinement"]:
            whose.setdefault(f"{item['entry']}: {item['packing_of']}", []).append(item["n"])
        refined = "; ".join(f"{_compress(ns)} ({who})" for who, ns in whose.items()) or "-"
        unclassified = _compress(summary["recorded_unclassified"])
        if summary["recorded_by_exception"]:
            unclassified += f"; by exception {_compress(summary['recorded_by_exception'])}"
        lines.append(
            f"| {_report_link(summary['report'], summary['url'])} "
            f"| {_cell(summary['holders'])} | {_when(summary['reported_at'])} "
            f"| {_compress(summary['counts'])} | {_compress(summary['recorded_new'])} "
            f"| {_cell(refined)} | {unclassified} "
            f"| {_cell(not_recorded)} | {undecided} | {summary['bead'] or '-'} |"
        )
    lines += [
        "",
        "## Per Count",
        "",
        (
            "Each report at the count in report order, with its side and verdict; a verdict "
            "names what decided it and by how much."
        ),
        "",
        "| n | Record on main | Reports in order | Best now |",
        "| ---: | --- | --- | --- |",
    ]
    for count in verdicts["counts"]:
        start = count["start"]
        record = f"{start['side']} ({_cell(start['label'])}; {_cell(start['holders'])})"
        steps = []
        for step in count["steps"]:
            verdict = recorded_text(step)
            detail = step["difference"]
            if step["verdict"] != RECORDED and step["decided_against"]:
                detail = f"{detail} {', '.join(step['decided_against'])}".strip()
            if step.get("exception"):
                detail += f"; exception: {step['exception']}"
            if step.get("restates"):
                detail = f"{detail}; {step['restates']}".lstrip("; ")
            steps.append(
                f"{_cell(step['report'])} {step['side']}: {verdict}"
                + (f" ({_cell(detail)})" if detail else "")
            )
        best = " or ".join(
            f"{_cell(side['label'])} {side['side']}" for side in count["best_now"]
        )
        if len(count["best_now"]) > 1:
            best = f"undecided: {best}"
        lines.append(f"| {count['n']} | {record} | {'; '.join(steps)} | {best} |")
    lines += _decision_lines(verdicts["owner_decisions"])
    lines += _note_lines(ledger)
    lines += [
        "",
        "## Other Items (No New Upper Bound)",
        "",
        "| Issue | Holder | Kind | Bead | Disposition |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in verdicts["other_items"]:
        lines.append(
            f"| {_report_link(item['issue'], item['url'])} | {_cell(item['holders'])} "
            f"| {_cell(item['kind'])} | {item['bead']} | {_cell(item['disposition'])} |"
        )
    lines += ["", *FOOTER]
    return "\n".join(lines) + "\n"


def _decision_lines(decisions: Mapping[str, Any]) -> list[str]:
    lines = [
        "",
        "## Owner Decisions Needed",
        "",
        "Nothing here is decided by the rule; each list is what the owner may want to rule on.",
        "",
        "### Publication in a Watched Repository",
        "",
        (
            "By default a certificate published in a watched repository, with no issue, "
            "competes as a report from its first commit. These are the counts where a verdict "
            "changes if such publications are not counted: each publication drops out of the "
            "walk, and a later report may then be recorded in its place."
        ),
        "",
    ]
    if decisions["publication_dependent"]:
        lines += [
            (
                "| n | Report | Default verdict (decided against) | Without publications "
                "(decided against) | Best now without publications |"
            ),
            "| ---: | --- | --- | --- | --- |",
        ]
        for item in decisions["publication_dependent"]:
            against = f" ({_cell(item['held_by_without'])})" if item["held_by_without"] else ""
            lines.append(
                f"| {item['n']} | {_cell(item['report'])} | {item['with_publications']} "
                f"({_cell(item['held_by_with']) or '-'}) | {item['without_publications']}"
                f"{against} | {_cell(item['best_now_without'])} |"
            )
    else:
        lines.append("None.")
    lines += [
        "",
        "### Refinement Chains",
        "",
        (
            "Counts where two or more refinements of one packing are each recorded, in "
            "report order; the rule records each, and each margin is against the side it "
            "was decided against."
        ),
        "",
        *_chain_lines(decisions["refinement_chains"]),
        "",
        "### Exact Ties Between Different Holders",
        "",
        "Not recorded by the rule, since the earlier holder keeps a tie.",
        "",
    ]
    if decisions["exact_ties"]:
        lines += [
            "| Report (holder) | Tied with | Counts | Tied holders |",
            "| --- | --- | --- | --- |",
        ]
        groups: dict[tuple[str, str, str], list[Any]] = {}
        for item in decisions["exact_ties"]:
            key = (item["report"], item["holders"], item["tied_with"])
            groups.setdefault(key, []).append(item)
        for (report, holders, tied), items in groups.items():
            names = ", ".join(dict.fromkeys(item["tied_holders"] for item in items))
            lines.append(
                f"| {_cell(report)} ({_cell(holders)}) | {_cell(tied)} "
                f"| {_compress(item['n'] for item in items)} | {_cell(names)} |"
            )
    else:
        lines.append("None.")
    lines += [
        "",
        "### Certificate Committed Before the Report That Holds the Count",
        "",
        (
            "A claim not recorded whose certificate's first commit precedes the time the "
            "holding report reached this repository."
        ),
        "",
    ]
    if decisions["first_commit_before_report"]:
        lines += [
            (
                "| n | Report | First committed | Reported | Held by | Held by, reported "
                "| Reason |"
            ),
            "| ---: | --- | --- | --- | --- | --- | --- |",
        ]
        for item in decisions["first_commit_before_report"]:
            lines.append(
                f"| {item['n']} | {_cell(item['report'])} | {_when(item['first_committed'])} "
                f"| {_when(item['reported_at'])} | {_cell(item['held_by'])} "
                f"| {_when(item['held_by_reported_at'])} | {item['reason']} |"
            )
    else:
        lines.append("None.")
    lines += ["", "### Undecided Comparisons", ""]
    if decisions["undecided"]:
        lines += [
            "| n | Report | Against | What would decide it |",
            "| ---: | --- | --- | --- |",
        ]
        for item in decisions["undecided"]:
            lines.append(
                f"| {item['n']} | {_cell(item['report'])} | {_cell(item['against'])} "
                f"| {_cell(item['decide_by'])} |"
            )
    else:
        lines.append("None.")
    lines += ["", "### Claims of Unknown Time", "", "Kept out of the walk.", ""]
    if decisions["unknown_times"]:
        lines += ["| n | Report | Holder |", "| ---: | --- | --- |"]
        for item in decisions["unknown_times"]:
            lines.append(
                f"| {item['n']} | {_cell(item['report'])} | {_cell(item['holders'])} |"
            )
    else:
        lines.append("None.")
    return lines


def _chain_lines(chains: Sequence[Mapping[str, Any]]) -> list[str]:
    if not chains:
        return ["None."]
    lines = ["| n | Packing | Refinements in order |", "| ---: | --- | --- |"]
    for chain in chains:
        steps = "; ".join(
            f"{item['report']} {item['difference']} {item['decided_against']}".strip()
            for item in chain["refinements"]
        )
        packing = f"{chain['packing']} ({chain['packing_of']})" if chain["packing_of"] else ""
        lines.append(
            f"| {chain['n']} | {_cell(packing or chain['packing'])} | {_cell(steps)} |"
        )
    return lines


def _count_lines(summary: Mapping[str, int]) -> list[str]:
    continuing = summary["recorded_new_continuing"]
    return [
        (
            f"{summary['claims']} claims at {summary['counts']} counts. Recorded: "
            f"{summary['recorded_new']} new packings (of which {continuing} continue another "
            f"holder's or the reporter's own arrangement), {summary['recorded_refinement']} "
            f"refinements of a standing packing, {summary['recorded_unclassified']} that no "
            f"source classifies; {summary['recorded_by_exception']} recorded by exception; "
            f"{summary['not_recorded']} not recorded; {summary['undecided']} undecided."
        ),
        "",
        (
            "A refinement is the same configuration with a tighter certificate (a padding "
            "reduction, an exact-contact refinement, an exact attainment), as a source says; "
            "a new packing is one its source says is new, including one a continued search "
            "found from another arrangement. The rule records both; the register credits a "
            "refinement as a regularization of the packing it tightens."
        ),
    ]


def recorded_text(step: Mapping[str, Any]) -> str:
    """A recorded verdict, with what the certificate is where a source says."""
    packing = step.get("packing")
    if step["verdict"] != RECORDED or packing is None:
        return str(step["verdict"])
    if packing["kind"] == REFINEMENT:
        return (
            f"recorded, a refinement of {packing['packing_of']}'s packing ({packing['entry']})"
        )
    if "continues" in packing:
        return f"recorded (new packing, continuing {packing['continues']})"
    return "recorded (new packing)"


def _note_lines(ledger: Ledger) -> list[str]:
    """Each report's note and its claims' notes, one row per note."""
    lines = [
        "",
        "## Notes on Reports and Claims",
        "",
        "From `ledger.yaml`; a note that several claims share is one row.",
        "",
        "| Report | Counts | Note |",
        "| --- | --- | --- |",
    ]
    for report in ledger["reports"]:
        note = report.get("note")
        if note:
            lines.append(f"| {_cell(report['report'])} | all | {_cell(note)} |")
        notes: dict[str, list[int]] = {}
        for claim in report["claims"]:
            text = claim.get("note")
            if text:
                notes.setdefault(text, []).append(claim["n"])
        for note, ns in notes.items():
            lines.append(f"| {_cell(report['report'])} | {_compress(ns)} | {_cell(note)} |")
    return lines


def json_text(value: Any) -> str:
    return json.dumps(value, indent=1, ensure_ascii=False) + "\n"


def rendered(directory: Path) -> dict[str, str]:
    """The two rendered files' text, from the ledger and the records on the tree."""
    ledger = load_ledger(directory)
    verdicts = evaluate(ledger, tree_starts(counts_of(ledger)))
    return {VERDICTS: json_text(verdicts), README: readme(ledger, verdicts)}


def render(directory: Path, *, check: bool = False) -> list[str]:
    """Write the rendered files, or with ``check`` name those that would change."""
    changed = []
    for name, text in rendered(directory).items():
        path = directory / name
        if path.exists() and path.read_text(encoding="utf-8") == text:
            continue
        changed.append(name)
        if not check:
            with atomic_output_file(path) as temporary:
                Path(temporary).write_text(text, encoding="utf-8")
    return changed


# --------------------------------------------------------------------------- gather


Fetch = Callable[[str], Any]


def _gh_api(path: str) -> Any:
    shown_ = subprocess.run(("gh", "api", path), capture_output=True, text=True, check=True)
    return json.loads(shown_.stdout)


def github_item(source: Mapping[str, Any], api: Fetch) -> dict[str, Any]:
    """One report's GitHub coordinates: number, author, creation time, state, title.

    A comment carries its own author and time, and its issue's state and title.
    """
    base = f"repos/{GITHUB_REPOSITORY}"
    if "comment" in source:
        item = api(f"{base}/issues/comments/{source['comment']}")
        parent = api(f"{base}/issues/{source['issue']}")
        return {
            "report": source["report"],
            "kind": "comment",
            "number": int(source["issue"]),
            "comment_id": int(source["comment"]),
            "url": item["html_url"],
            "author": item["user"]["login"],
            "created_at": item["created_at"],
            "issue_state": parent["state"],
            "issue_closed_at": parent.get("closed_at"),
            "issue_title": parent["title"],
        }
    kind, path = ("pull-request", "pulls") if "pull" in source else ("issue", "issues")
    number_ = int(source.get("pull", source.get("issue", 0)))
    item = api(f"{base}/{path}/{number_}")
    return {
        "report": source["report"],
        "kind": kind,
        "number": number_,
        "url": item["html_url"],
        "author": item["user"]["login"],
        "created_at": item["created_at"],
        "state": item["state"],
        "closed_at": item.get("closed_at"),
        "title": item["title"],
    }


def git_show(commit: str, path: str) -> Any:
    try:
        shown_ = subprocess.run(
            ("git", "-C", str(REPO), "show", f"{commit}:{path}"),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        raise LedgerError(
            f"git show {commit[:12]}:{path} failed; fetch the lane's branch first: "
            f"{error.stderr.strip()[:200]}"
        ) from error
    return json.loads(shown_.stdout)


def _lane_claim(
    row: Mapping[str, Any], mapping: Mapping[str, Any], where: str, rounding: str, url: str
) -> Claim:
    if "side_decimal" in row:
        case = row.get("case") or {}
        claim: Claim = {
            "n": int(row["n"]),
            "printed": str(row["side_decimal"]),
            "rounding": "unstated",
            "first_committed": str(row["first_committed"]),
            "note": f"algebraic side of degree {row['degree']}; the print is the lane's",
        }
        if case.get("reported_relation") in (BELOW, ABOVE, EQUAL):
            claim["record_relation"] = {
                "relation": str(case["reported_relation"]),
                "value": str(case["reported_value"]),
                "exact_form": str(case.get("reported_exact_form") or ""),
                "read_from": where,
            }
        return claim
    offered = str(row["offered_side"])
    claim = {
        "n": int(row["n"]),
        "printed": offered,
        "rounding": "exact" if "/" in offered else rounding,
        "exact": str(row["exact_side"]),
        "exact_from": where,
        "first_committed": str(row["first_committed"]),
    }
    if mapping.get("printed_in_note") and row.get("printed_in") not in (None, "", url):
        claim["note"] = f"printed in {row['printed_in']}"
    return claim


def lane_claims(
    mapping: Mapping[str, Any], lanes: Mapping[str, Mapping[str, Any]], url: str, rounding: str
) -> list[Claim]:
    """The claims one lane record gives a report: its rows printed in it, or those named."""
    lane = lanes[mapping["lane"]]
    path = f"packing/resources/web/{mapping['packet']}/acquisition/{mapping['record']}"
    record = git_show(lane["commit"], path)
    where = f"{path} at {lane['branch']}@{lane['commit']}"
    wanted = {int(n) for n in mapping.get("counts") or []}
    rows = [row for row in record["results"] if _selected(row, mapping, wanted, url)]
    if wanted:
        found = {int(row["n"]) for row in rows}
        _require(found == wanted, f"{path}: no rows for {sorted(wanted - found)}")
    return [_lane_claim(row, mapping, where, rounding, url) for row in rows]


def _selected(
    row: Mapping[str, Any], mapping: Mapping[str, Any], wanted: set[int], url: str
) -> bool:
    """A lane row a report takes: every row, the counts named, or the rows printed in it."""
    if mapping.get("all"):
        return True
    if wanted:
        return int(row["n"]) in wanted
    return str(row.get("printed_in", "")) == url


def _merge(transcribed: Sequence[Claim], from_lanes: Sequence[Claim]) -> list[Claim]:
    """Transcribed fields win; a lane adds the exact side and the commit time."""
    merged: dict[int, Claim] = {claim["n"]: cast("Claim", dict(claim)) for claim in from_lanes}
    for claim in transcribed:
        lane = merged.get(claim["n"])
        if lane is None:
            merged[claim["n"]] = claim
            continue
        merged[claim["n"]] = cast("Claim", {**lane, **claim})
    return [merged[n] for n in sorted(merged)]


def _later(claim: Claim, reported_at: str) -> Claim:
    """A pull request's claim committed after it was opened arrived with that commit."""
    committed = claim.get("first_committed", "")
    if committed > reported_at and "reported_at" not in claim:
        claim = cast("Claim", {**claim, "reported_at": committed})
    return claim


def gather(directory: Path, *, snapshot: bool = False, api: Fetch = _gh_api) -> list[str]:
    """Write ``github-issues.json`` and ``ledger.yaml``; return the cross-check warnings."""
    sources = load_yaml(directory / SOURCES)
    _require(sources.get("format") == SOURCES_FORMAT, f"{SOURCES} format")
    lanes = {lane["name"]: lane for lane in sources["lanes"]}
    if snapshot:
        github = json.loads((directory / SNAPSHOT).read_text(encoding="utf-8"))["items"]
    else:
        github = [
            github_item(source, api)
            for source in sources["reports"]
            if "issue" in source or "pull" in source
        ]
    by_report = {item["report"]: item for item in github}
    reports: list[Report] = []
    for source in sources["reports"]:
        item = by_report.get(source["report"])
        if item is not None:
            kind, url, reported_at = item["kind"], item["url"], item["created_at"]
        else:
            kind, url, reported_at = "publication", source["url"], source["reported_at"]
        rounding = str(source.get("rounding", "up"))
        from_lanes = [
            claim
            for mapping in source.get("lanes", [])
            for claim in lane_claims(mapping, lanes, url, rounding)
        ]
        claims = _merge(source.get("claims", []), from_lanes)
        if kind == "pull-request":
            claims = [_later(claim, reported_at) for claim in claims]
        report: Report = {
            "report": source["report"],
            "url": url,
            "kind": kind,
            "holders": source["holders"],
            "reported_at": reported_at,
            "bead": source.get("bead", ""),
            "claims": claims,
        }
        if source.get("note"):
            report["note"] = source["note"]
        reports.append(report)
    ledger: Ledger = {
        "format": LEDGER_FORMAT,
        "read_at_main": sources["read_at_main"],
        "read_on": sources["read_on"],
        "rule": sources["rule"],
        "lanes": sources["lanes"],
        "reports": reports,
        "exceptions": sources.get("exceptions", []),
        "other_items": sources.get("other_items", []),
    }
    found = problems(ledger)
    _require(not found, "; ".join(found))
    snapshot_text = json_text({"format": SNAPSHOT_FORMAT, "items": github})
    ledger_text = yaml.safe_dump(ledger, sort_keys=False, allow_unicode=True, width=88)
    for name, text in ((SNAPSHOT, snapshot_text), (LEDGER, ledger_text)):
        with atomic_output_file(directory / name) as temporary:
            Path(temporary).write_text(text, encoding="utf-8")
    return cross_check(ledger, sources, lanes)


def _pending_owner(
    pending: Mapping[str, Any],
    n: int,
    claims: Mapping[tuple[str, int], Claim],
    reports: Sequence[Report],
) -> Report | None:
    """The ledger report a lane's ``pending`` row names at count ``n``, by its address.

    A register entry (``T-NNN``) is part of the record, not of the ledger, and names none.
    """
    url = str(pending.get("url", ""))
    label = str(pending.get("report", ""))
    if label.startswith("T-") or not url.startswith("https://github.com/"):
        return None
    for report in reports:
        if report["url"] == url and report["kind"] != "comment":
            return report
    for report in reports:
        commented = report["kind"] == "comment" and report["url"].split("#")[0] == url
        if commented and ("comment" in label or "refinement" in label):
            return report
    for report in reports:
        repository = report["url"].split("/tree/")[0] + "/"
        published = report["kind"] == "publication" and url.startswith(repository)
        if published and (report["report"], n) in claims:
            return report
    return None


def cross_check(
    ledger: Ledger, sources: Mapping[str, Any], lanes: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    """Where a lane read another report's side in a way this ledger's claim contradicts."""
    claims = {
        (report["report"], claim["n"]): claim
        for report in ledger["reports"]
        for claim in report["claims"]
    }
    warnings: list[str] = []
    seen: set[str] = set()
    for source in sources["reports"]:
        for mapping in source.get("lanes", []):
            key = f"{mapping['lane']}/{mapping['packet']}/{mapping['record']}"
            if key in seen:
                continue
            seen.add(key)
            lane = lanes[mapping["lane"]]
            path = f"packing/resources/web/{mapping['packet']}/acquisition/{mapping['record']}"
            for row in git_show(lane["commit"], path)["results"]:
                n = int(row["n"])
                for pending in row.get("pending", []):
                    owner = _pending_owner(pending, n, claims, ledger["reports"])
                    if owner is not None:
                        claim = claims.get((owner["report"], n))
                        warnings.extend(_disagreement(key, n, owner, claim, pending))
    return warnings


def _disagreement(
    key: str, n: int, owner: Report, claim: Claim | None, pending: Mapping[str, Any]
) -> list[str]:
    """A lane's reading of ``owner`` at ``n`` that the ledger's claim cannot both satisfy."""
    where = f"{key} n={n} reads {pending.get('report')}"
    if claim is None:
        return [f"{where}, which this ledger does not list at n = {n}"]
    ours = claim_span(claim)
    if "exact_side" in pending:
        theirs = exact_span(number(str(pending["exact_side"])))
        lane = f"exactly {pending['exact_side']}"
    else:
        theirs = printed_side(
            str(pending.get("printed")), _lane_rounding(str(pending.get("rounding")))
        )
        lane = f"{pending.get('printed')} ({pending.get('rounding')})"
    if below(ours, theirs) or below(theirs, ours):
        shown_ = claim.get("exact", claim["printed"])
        held = f"{shown_} ({claim['rounding']}) for {owner['report']}"
        return [f"{where} as {lane}; this ledger has {held}"]
    return []


def _lane_rounding(rounding: str) -> str:
    return rounding if rounding in ROUNDINGS else "unstated"


# --------------------------------------------------------------------------- command


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("gather", "render", "check"):
        command = sub.add_parser(name)
        command.add_argument("directory", type=Path, nargs="?", default=DEFAULT_DIRECTORY)
        if name == "gather":
            command.add_argument("--snapshot", action="store_true")
        if name == "render":
            mode = command.add_mutually_exclusive_group()
            mode.add_argument(
                "--check", action="store_true", help="fail if a file would change"
            )
            mode.add_argument("--write", action="store_true", help="write them (the default)")
    args = parser.parse_args(argv)
    directory = cast("Path", args.directory).resolve()
    if args.action == "gather":
        warnings = gather(directory, snapshot=args.snapshot)
        for warning in warnings:
            print(f"WARN  {warning}")
        print(f"wrote {SNAPSHOT} and {LEDGER}; {len(warnings)} cross-check warnings")
        return 0
    if args.action == "check":
        ledger = load_ledger(directory)
        claims = sum(len(report["claims"]) for report in ledger["reports"])
        print(f"OK: {len(ledger['reports'])} reports, {claims} claims")
        return 0
    changed = render(directory, check=args.check)
    if args.check and changed:
        print(f"FAIL  would change: {', '.join(changed)}", file=sys.stderr)
        return 1
    print("up to date" if not changed else f"wrote {', '.join(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
