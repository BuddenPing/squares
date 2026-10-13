#!/usr/bin/env python3
"""Record the regularized drawings in the register, generated from the layer's index.

Usage, from `packing/`, after `uv run --frozen --all-extras --group dev python -m
devtools.regularized_drawings`:

    [--check]

The atlas's regularized layer (`atlas/known-best/regularized/index.json`) draws a view of
a count's credited packing that this project regularized: by `regularize_axis_components/2`,
by Evan Daniel's regularizer through `devtools.regularize_evand`, or by the grid-slack
generator (`docs/project/policies/regularization-policy.md`). Each entry that draws a view
carries its regularization in the register's terms, `results.schema.yaml`'s
`regularizations` item, with `of_witness`, the source witness, standing in for `of`. The
owner asked that the regularizations the project makes be tracked with the provenance of
the packings they redraw (11 October 2026), and that every regularized version be captured
in the frontier records (12 October 2026). So `results.yaml` carries them too, as its
`regularized_drawings`: one item a drawn count, the layer's record with `of` resolved to the
registered result that holds the packing, and the view it is drawn from.

**Which result holds the packing.** A view at the witness's own side (`same`) redraws the
packing the witness retains: `of` is the registered result whose `attribution` names the
witness's source and whose scope holds the count. A view at the verified upper bound
(`bound`, written `solved` in the register's terms) redraws the packing solved to that
bound: `of` is the result the case's verified upper bound rests on
(`build_bound_citations.results_carrying` on the bound's own evidence). A `same` view whose
side is also exactly the verified upper bound, where no registered result attributes the
witness's source, redraws the packing at that bound in the same way: the result the bound
rests on holds it (T-154 certified 26 witnesses' own sides exactly from views that are
drawn here). Where the bound rests on several results, the one whose `regularizations`
registered a view of the count at that bound answers: at 33 counts T-154's view lies
exactly at the side of Evan Daniel's earlier certificate, and the case cites both (T-101,
T-154). Exactly one result must answer; where none does, or more than one, the count
is listed under `unregistered`
with the reason, and its record stays in the layer's index alone. The register holds a
result by others only when the record acts on it (`epistemics.md`, Results by Others), so a
packing from before this project began that no replay here ever registered has no result to
name, and inventing one is not this tool's to do.

**What is not a result.** A drawing changes no side, frontier value, evidence tier or
credit (the policy, section 1), so these items are not a register result and carry no rung:
they are this project's regularizations of results the register already holds. A view
whose side lies below the verified upper bound is a result first (row 3) and is registered
by its own entry's `regularizations`.

**Whose regularization, and whether it was modified.** The owner asked on 13 October 2026
that the frontier records say which counts have been regularized and whether the
regularization is this project's, that a pure regularization never count as a result
while staying a credited part of the record, and that where this project's own
modifications to Evan Daniel's regularizer were used, the record say so as well. So each
item names its `modifications` where his regularizer or the grid-slack port of his
placement made the view, read from the index entry alone (`project_modifications`): the
retry rungs the kept solve climbed (`run.rungs`, or before the retry ladder
`run.retried_with`), the replica patches its `method` names, the same-side exact re-solve a
view at the witness's side was brought to it by, and for a grid-slack view the port
itself, which is this project's code and not his. An empty list says his regularizer ran
unmodified; a view of this project's axis tool has no such field.

**The case records.** Each case record whose count the layer draws, or whose house is
itself a regularization its source published (a register result's `regularizations`
item whose `by` is the bibliography key of the source the witness names, as `T-146`'s
are), carries a generated `regularization` field in its front matter: a one-paragraph
`note` the site's case page prints, then its `items`, the source's regularization first
in the register's own terms and this project's after it, with the generator, the credit
line, the modifications, the side relation (`same` or `bound`), the registered result
that holds the packing (`of`, or null where none does) and the view's path. A record the
layer does not draw and whose house no source regularized carries no such field.

The register's list is a block at the end of `results.yaml`, from `MARKER` on, which this
tool writes whole, and each case record's field is written in place, at the end of its
front matter; `--check` compares both with what the index gives and writes nothing.
`devtools.check_results` holds the same comparison (`problems`), so neither the register
nor a case record can drift from the layer.
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from functools import cache
from pathlib import Path
from typing import Any

import yaml
from strif import atomic_output_file

from devtools.build_bound_citations import (
    in_scope,
    load_case,
    load_register,
    own_evidence,
    results_carrying,
)
from sqpack.yamlio import load_yaml, safe_load

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
RESULTS = ROOT / "frontier/results.yaml"
INDEX = ROOT / "atlas/known-best/regularized/index.json"
FRONTIER = ROOT / "frontier"
VENDORED = REPO / "vendor/evand-regularize/vendored.yaml"
KEY = "regularized_drawings"
#: The case record's front-matter field this tool writes.
CASE_FIELD = "regularization"
MARKER = (
    "# Generated by python -m devtools.regularized_drawings from the regularized layer's\n"
    "# index (packing/atlas/known-best/regularized/index.json); do not edit by hand.\n"
)
GENERATOR = "python -m devtools.regularized_drawings"
#: A regularization's `by` for this project's own runs (`results.schema.yaml`).
PROJECT_REGULARIZER = "project"
#: The fields of a layer record the register's item keeps, in its order.
ITEM_FIELDS = ("n", "of", "by", "method", "modifications", "side", "changes", "identity")
#: The layer's generators, as its index names them.
AXIS_GENERATOR = "regularize_axis_components/2"
EVAND_GENERATOR = "evand-regularize"
#: Whose code made each generator's view: this project's axis tool (`axis`), Evan Daniel's
#: regularizer through the vendored driver (`evand`), or the grid-slack port of his
#: placement (`grid`). A generator not named here is refused, not credited by a guess.
GENERATOR_KINDS = {
    AXIS_GENERATOR: "axis",
    EVAND_GENERATOR: "evand",
    "regularize_grid_slack/0": "grid",
    "regularize_grid_slack/1": "grid",
}
#: The credit line of a view this project's axis tool made (policy section 7); the other
#: generators' lines are their index blocks' `credit`.
AXIS_CREDIT = (
    "Regularized by the Squares Project with its own axis tool (regularize_axis_components/2)"
)
#: The kind of result whose exact side a registered regularization proves, which the
#: notes say it is.
UPPER_BOUND = "upper-bound"
#: How an item names each of this project's modifications to Evan Daniel's regularizer.
SAME_SIDE_RESOLVE = "same-side exact re-solve (devtools.regularize_same_side)"
BOUND_RESOLVE = "exact re-solve at the verified upper bound (devtools.regularize_same_side)"
#: The retry rungs, by the name the driver records (`devtools.regularize_evand`). The
#: stall-stop rung's one change is its replica patch, which the view's `method` names, so
#: it has no words of its own (`SILENT_RUNGS`); any other rung is refused.
RUNG_WORDS = {
    "dps-100": "retry rung dps-100",
    "force-kkt": "retry rung force-kkt",
    "first-pass": "retry rung first-pass (devtools.regularize_evand_first_pass)",
}
SILENT_RUNGS = frozenset({"stall-stop"})
#: The patches a vendored view's `method` names after the pin, `@675a5ea+name`.
_METHOD_PATCHES = re.compile(r"evand/square-packing@[0-9a-f]+((?:\+[^,+\s]+)*)")
#: How a note reads a project item's side relation and a source item's.
SIDE_WORDS = {
    "same": "at the witness's own side",
    "bound": "at the verified upper bound",
    "solved": "solved to its side",
}
IDENTITY_FIELDS = ("basis", "measured_in", "one_to_one", "moved", "max_move", "max_turn_deg")


class RegularizedDrawingsError(ValueError):
    """The index or the register names something this tool has no words for: a generator,
    a retry rung or retry argument, or a registering result that is not an upper bound."""


def generator_kind(generator: str) -> str:
    """Whose code made a generator's view (`GENERATOR_KINDS`); refused where unknown."""
    try:
        return GENERATOR_KINDS[generator]
    except KeyError:
        raise RegularizedDrawingsError(
            f"generator {generator!r} is not one this tool knows; name it in GENERATOR_KINDS"
        ) from None


def generator_credit(generator: str, generators: Mapping[str, Any]) -> str:
    """A generator's credit line: the axis tool's own, or its index block's `credit`."""
    if generator_kind(generator) == "axis":
        return AXIS_CREDIT
    credit = (generators.get(generator) or {}).get("credit")
    if not credit:
        raise RegularizedDrawingsError(f"the index's {generator} block names no credit")
    return str(credit)


def upper_bound_result(result: Mapping[str, Any]) -> str:
    """A registering result's id, refused unless it is an upper bound, which is what the
    notes say its regularization's exact side proves."""
    if result.get("kind") != UPPER_BOUND:
        raise RegularizedDrawingsError(
            f"{result['id']} registers a regularization but is a {result.get('kind')} result, "
            f"not an {UPPER_BOUND}"
        )
    return str(result["id"])


@dataclass(frozen=True)
class Resolved:
    """Which registered result holds a drawn count's packing, or why none answers."""

    of: str | None
    reason: str


def relation(entry: Mapping[str, Any]) -> str:
    """A drawn entry's side relation: an axis view is always at the witness's side."""
    side = entry.get("side") or {}
    return str(side.get("relation") or "same")


def bound_side(bound: Mapping[str, Any]) -> Fraction | None:
    """A verified upper bound as a rational where it is one: its exact form, or its decimal
    where it states none; `None` for a closed form, which no rational side equals."""
    exact = bound.get("exact_form")
    text = str(exact if exact is not None else bound.get("value") or "")
    try:
        return Fraction(text)
    except ValueError:
        return None


def at_bound(entry: Mapping[str, Any], bound: Mapping[str, Any]) -> bool:
    """Whether a drawn entry's exact side is the case's verified upper bound."""
    view = (entry.get("side") or {}).get("view")
    upper = bound_side(bound)
    return view is not None and upper is not None and Fraction(str(view)) == upper


def witness_source_key(entry: Mapping[str, Any], repo: Path = REPO) -> str | None:
    """The bibliography key the drawn entry's source witness names."""
    document = load_yaml((repo / entry["source"]["witness"]).read_text(encoding="utf-8"))
    return (document["witness"].get("source") or {}).get("key")


def registering_holders(
    n: int, holders: Sequence[str], results: Sequence[Mapping[str, Any]], *, side: str
) -> list[str]:
    """The results a verified upper bound rests on, narrowed, where several prove it, to
    those that registered a regularized view of `n` at that bound (a `regularizations` item
    for `n` on `side`). At 33 counts the side of Evan Daniel's certificate (T-101) is also
    the side of a registered regularized view (T-154), and the case cites both: the view
    drawn there is the registering result's. Where none or several register one, the
    holders stand as they were, and the count is listed unregistered."""
    if len(holders) < 2:
        return list(holders)
    registering = [
        str(result["id"])
        for result in results
        if str(result["id"]) in holders
        and any(
            int(item["n"]) == n and item.get("side") == side
            for item in result.get("regularizations") or []
        )
    ]
    return registering if len(registering) == 1 else list(holders)


def packing_result(
    entry: Mapping[str, Any],
    results: Sequence[Mapping[str, Any]],
    *,
    source_key: str | None,
    bound_holders: Sequence[str],
    side_at_bound: bool = False,
) -> Resolved:
    """The registered result whose packing the drawn entry redraws (see the module).
    `side_at_bound` says a `same` view's side is also exactly the verified upper bound."""
    n = int(entry["n"])
    if relation(entry) == "bound":
        bound_holders = registering_holders(n, bound_holders, results, side="solved")
        if len(bound_holders) == 1:
            return Resolved(bound_holders[0], "holds the verified upper bound the view is at")
        return Resolved(None, f"the verified upper bound rests on {list(bound_holders)}")
    if side_at_bound:
        bound_holders = registering_holders(n, bound_holders, results, side="same")
    holders = [
        str(result["id"])
        for result in results
        if in_scope(result["scope"], n)
        and source_key in ((result.get("attribution") or {}).get("source_keys") or [])
    ]
    if len(holders) == 1:
        return Resolved(holders[0], "attributes the witness's source")
    if not holders and side_at_bound and len(bound_holders) == 1:
        return Resolved(
            bound_holders[0], "holds the verified upper bound the witness's side is exactly"
        )
    if not holders:
        return Resolved(
            None, f"no registered result attributes the witness's source {source_key}"
        )
    return Resolved(None, f"several results attribute the witness's source: {holders}")


def rungs(entry: Mapping[str, Any]) -> list[str]:
    """The retry rungs a drawn view's solve climbed, as its index entry records them:
    `run.rungs`, or before the retry ladder the one retry's arguments, `retried_with`
    (`--dps N` and `--force-kkt`; any other argument is refused)."""
    run = entry.get("run") or {}
    if "rungs" in run:
        return [str(rung) for rung in run["rungs"]]
    arguments = [str(argument) for argument in run.get("retried_with") or []]
    found = []
    at = 0
    while at < len(arguments):
        if arguments[at] == "--dps" and at + 1 < len(arguments):
            found.append(f"dps-{arguments[at + 1]}")
            at += 2
        elif arguments[at] == "--force-kkt":
            found.append("force-kkt")
            at += 1
        else:
            raise RegularizedDrawingsError(
                f"n={entry.get('n')}: retry argument {arguments[at]!r} is not one this tool "
                "knows"
            )
    return found


def rung_words(found: Sequence[str], n: object = None) -> list[str]:
    """How an item names each rung a solve climbed (`RUNG_WORDS`), the stall-stop rung
    by its patch alone; a rung with no words is refused rather than dropped."""
    words = []
    for rung in found:
        if rung in SILENT_RUNGS:
            continue
        if rung not in RUNG_WORDS:
            raise RegularizedDrawingsError(
                f"n={n}: retry rung {rung!r} is not one this tool knows; name it in RUNG_WORDS"
            )
        words.append(RUNG_WORDS[rung])
    return words


@cache
def patch_kinds(path: Path = VENDORED) -> dict[str, str]:
    """The vendored copy's recorded local changes by the name a `method` gives them: a
    replica patch by its patch file's stem, any other change by its path. Read only where
    a view's `method` names one, so a tree without `vendor/` (a negative control's
    snapshot) reads none."""
    document = load_yaml(path.read_text(encoding="utf-8")) or {}
    kinds: dict[str, str] = {}
    for change in document.get("local_changes") or []:
        name = Path(str(change["patch"])).stem if change.get("patch") else str(change["path"])
        kinds[name] = str(change.get("kind") or "modified")
    return kinds


def project_modifications(
    entry: Mapping[str, Any], kinds: Mapping[str, str] | None = None
) -> list[str] | None:
    """This project's modifications to Evan Daniel's regularizer that made a drawn view,
    read from its index entry: the retry rungs its solve climbed, the vendored copy's
    patches its `method` names, and the exact re-solve that brought it to the witness's
    side; for a grid-slack view, the port of his placement, which is this project's code,
    and its re-solve. An empty list: his regularizer ran unmodified. None: the view is
    this project's axis tool's, which is not his regularizer."""
    generator = str(entry.get("generator"))
    kind = generator_kind(generator)
    resolve = SAME_SIDE_RESOLVE if relation(entry) == "same" else BOUND_RESOLVE
    if kind == "grid":
        return [
            f"port of his coincidence placement ({generator}) rather than his code",
            resolve,
        ]
    if kind == "axis":
        return None
    found = rung_words(rungs(entry), entry.get("n"))
    method = str((entry.get("regularization") or {}).get("method") or "")
    match = _METHOD_PATCHES.search(method)
    named = [name for name in (match.group(1) if match else "").split("+") if name]
    if kinds is None:
        kinds = patch_kinds() if named else {}
    found.extend(
        f"replica patch {name}" if kinds.get(name) == "replica" else f"local change {name}"
        for name in named
    )
    if relation(entry) == "same":
        found.append(SAME_SIDE_RESOLVE)
    return found


def item(
    entry: Mapping[str, Any], of: str, modifications: Sequence[str] | None = None
) -> dict[str, Any]:
    """The register's item for a drawn entry: its regularization with `of` resolved, and
    this project's modifications to Evan Daniel's regularizer where his method made it."""
    record = entry["regularization"]
    found = {**record, "of": of}
    if modifications is not None:
        found["modifications"] = list(modifications)
    kept = {key: found[key] for key in ITEM_FIELDS if key in found}
    kept["identity"] = {
        key: record["identity"][key] for key in IDENTITY_FIELDS if key in record["identity"]
    }
    kept["view"] = entry["view"]["path"]
    return kept


@dataclass(frozen=True)
class Drawn:
    """A count the layer draws, the result that holds its packing, and the modifications
    to Evan Daniel's regularizer that made it."""

    entry: Mapping[str, Any]
    resolved: Resolved
    modifications: list[str] | None


def drawn_counts(index: Mapping[str, Any], repo: Path = REPO) -> list[Drawn]:
    """Every count the layer draws regularized, with `of` resolved (see the module)."""
    register = load_register()
    results = register.results
    found: list[Drawn] = []
    for entry in sorted(index["entries"], key=lambda record: int(record["n"])):
        if entry.get("status") != "regularized":
            continue
        n = int(entry["n"])
        holders: list[str] = []
        exact = False
        if relation(entry) in {"bound", "same"}:
            bound = load_case(n).get("verified_upper_bound") or {}
            exact = relation(entry) == "same" and at_bound(entry, bound)
            if relation(entry) == "bound" or exact:
                own = own_evidence(bound.get("evidence") or [], register)
                holders = results_carrying(n, own, results)
        resolved = packing_result(
            entry,
            results,
            source_key=witness_source_key(entry, repo),
            bound_holders=holders,
            side_at_bound=exact,
        )
        found.append(Drawn(entry, resolved, project_modifications(entry)))
    return found


def expected(
    index: Mapping[str, Any], repo: Path = REPO, drawn: Sequence[Drawn] | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """What the register's `regularized_drawings` should hold for this index: the items
    whose packing a registered result holds, and the drawn counts with none, each with
    its reason."""
    items: list[dict[str, Any]] = []
    unregistered: list[dict[str, Any]] = []
    for count in drawn_counts(index, repo) if drawn is None else drawn:
        if count.resolved.of is None:
            unregistered.append({"n": int(count.entry["n"]), "reason": count.resolved.reason})
        else:
            items.append(item(count.entry, count.resolved.of, count.modifications))
    return items, unregistered


# ---------------------------------------------------------------- the case records


def source_regularizations(
    results: Sequence[Mapping[str, Any]],
    sources: Mapping[str, Any],
    repo: Path = REPO,
) -> dict[int, dict[str, Any]]:
    """The counts whose house is itself a regularization its source published: a
    register result's `regularizations` item by a source (`by` a bibliography key) whose
    key the count's known-best witness names, in the register's own terms, with the
    result that registered it (`registered_in`) and the source's credit line."""
    found: dict[int, dict[str, Any]] = {}
    for result in results:
        for record in result.get("regularizations") or []:
            by = str(record["by"])
            n = int(record["n"])
            if by == PROJECT_REGULARIZER:
                continue
            witness = {"source": {"witness": f"packing/witnesses/known-best/n-{n:03d}.yaml"}}
            if witness_source_key(witness, repo) != by:
                continue
            source = sources.get(by)
            credit = getattr(source, "credit", None) or ", ".join(
                getattr(source, "authors", ()) or (by,)
            )
            found[n] = {
                "by": by,
                "credit": credit,
                "of": str(record["of"]),
                "registered_in": upper_bound_result(result),
                "method": str(record["method"]),
                "side": str(record["side"]),
            }
    return found


def project_case_item(count: Drawn, generators: Mapping[str, Any]) -> dict[str, Any]:
    """This project's regularization of a drawn count, as its case record keeps it."""
    entry = count.entry
    generator = str(entry["generator"])
    found: dict[str, Any] = {
        "by": PROJECT_REGULARIZER,
        "credit": generator_credit(generator, generators),
        "generator": generator,
    }
    if count.modifications is not None:
        found["modifications"] = list(count.modifications)
    found["side"] = relation(entry)
    found["of"] = count.resolved.of
    found["view"] = str(entry["view"]["path"])
    return found


def case_note(items: Sequence[Mapping[str, Any]]) -> str:
    """The record's one paragraph: who regularized the drawing, with which modifications,
    and that it is a drawing, not a result; then who regularized the house, where its
    source did."""
    sentences: list[str] = []
    for found in items:
        if found["by"] != PROJECT_REGULARIZER:
            continue
        modifications = found.get("modifications")
        head = str(found["credit"])
        if modifications:
            head += f", with the project's modifications: {', '.join(modifications)}"
        elif modifications is not None:
            head += ", unmodified"
        sentences.append(head + ".")
        where = SIDE_WORDS[str(found["side"])]
        if found.get("of"):
            sentences.append(f"A drawing of {found['of']}'s packing {where}, not a result.")
        else:
            sentences.append(
                f"A drawing {where}, not a result; no registered result holds the packing."
            )
    for found in items:
        if found["by"] == PROJECT_REGULARIZER:
            continue
        sentences.append(
            f"The house is itself its source's regularization of {found['of']}'s packing "
            f"({found['credit']}), registered as {found['registered_in']} for the upper "
            "bound its exact side proves."
        )
    return " ".join(sentences)


def case_fields(
    index: Mapping[str, Any], repo: Path = REPO, drawn: Sequence[Drawn] | None = None
) -> dict[int, dict[str, Any]]:
    """Each case record's `regularization` field, by count, for the records that carry
    one: the source's regularization of the house first, then this project's drawing."""
    register = load_register()
    by_source = source_regularizations(register.results, register.sources, repo)
    generators = index.get("generators") or {}
    projects = {
        int(count.entry["n"]): project_case_item(count, generators)
        for count in (drawn_counts(index, repo) if drawn is None else drawn)
    }
    fields: dict[int, dict[str, Any]] = {}
    for n in sorted(set(by_source) | set(projects)):
        items = [found for found in (by_source.get(n), projects.get(n)) if found]
        fields[n] = {"note": case_note(items), "items": items}
    return fields


def case_block(field: Mapping[str, Any]) -> str:
    """The field as the front matter writes it, under `packing:`."""
    dumped = yaml.safe_dump(
        {CASE_FIELD: dict(field)}, sort_keys=False, allow_unicode=True, width=96
    )
    return "".join(f"  {line}\n" for line in dumped.splitlines())


_CASE_BLOCK = re.compile(rf"^  {CASE_FIELD}:.*\n(?:    .*\n)*", re.MULTILINE)


def with_case_field(text: str, field: Mapping[str, Any] | None) -> str:
    """A case record's text with its `regularization` field set to `field`, at the end
    of its front matter, or removed where `field` is None; the rest left as it was."""
    if not text.startswith("---\n"):
        raise ValueError("a case record opens with its front matter")
    end = text.index("\n---\n", 4) + 1
    front, rest = text[:end], text[end:]
    block = case_block(field) if field is not None else ""
    if _CASE_BLOCK.search(front):
        front = _CASE_BLOCK.sub(lambda _match: block, front, count=1)
    else:
        front += block
    return front + rest


def case_problems(
    index: Mapping[str, Any], fields: Mapping[int, Mapping[str, Any]] | None = None
) -> list[str]:
    """The case records whose `regularization` field differs from what the index gives."""
    wanted = case_fields(index) if fields is None else fields
    problems = []
    for path in sorted(FRONTIER.glob("n-[0-9][0-9][0-9].md")):
        n = int(path.stem.split("-")[1])
        text = path.read_text(encoding="utf-8")
        if with_case_field(text, wanted.get(n)) != text:
            problems.append(
                f"{path.name}'s {CASE_FIELD} differs from the regularized layer's index; "
                f"run {GENERATOR}"
            )
    return problems


def update_cases(fields: Mapping[int, Mapping[str, Any]]) -> int:
    """Write each case record's `regularization` field; return how many records changed."""
    changed = 0
    for path in sorted(FRONTIER.glob("n-[0-9][0-9][0-9].md")):
        n = int(path.stem.split("-")[1])
        text = path.read_text(encoding="utf-8")
        updated = with_case_field(text, fields.get(n))
        if updated != text:
            with atomic_output_file(path) as temporary:
                temporary.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


_PLAIN = re.compile(r"^[A-Za-z0-9_./-]+$")
_NUMERIC = re.compile(r"^[0-9.eE+-]+$")
#: Plain words YAML would read as something other than a string.
_WORDS = frozenset({"null", "true", "false", "yes", "no", "on", "off", "y", "n"})


def scalar(value: Any) -> str:
    """One scalar as the block writes it: JSON's double-quoted string where YAML would read
    the plain text differently, which YAML reads back as the same string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        # YAML 1.1, which the register's loader reads, takes `1e-15` for a string: its
        # float needs a point in the mantissa, so JSON's exponent form gains one.
        text = json.dumps(value)
        mantissa, exponent, power = text.partition("e")
        return f"{mantissa}.0e{power}" if exponent and "." not in mantissa else text
    if isinstance(value, int):
        return json.dumps(value)
    text = str(value)
    if _PLAIN.match(text) and not _NUMERIC.match(text) and text.lower() not in _WORDS:
        return text
    return json.dumps(text, ensure_ascii=False)


def block_text(
    items: Sequence[Mapping[str, Any]], unregistered: Sequence[Mapping[str, Any]]
) -> str:
    """The generated block: `MARKER`, then `regularized_drawings` in the register's style."""
    lines = [
        MARKER.rstrip("\n"),
        f"{KEY}:",
        "  index: packing/atlas/known-best/regularized/index.json",
    ]
    if unregistered:
        lines.append("  unregistered:")
        for row in unregistered:
            lines.append(f"    - n: {row['n']}")
            lines.append(f"      reason: {scalar(row['reason'])}")
    else:
        lines.append("  unregistered: []")
    lines.append("  items:" if items else "  items: []")
    for row in items:
        lines.append(f"    - n: {row['n']}")
        for key in ITEM_FIELDS[1:]:
            if key not in row:
                continue
            value = row[key]
            if key == "changes":
                inner = ", ".join(f"{name}: {scalar(number)}" for name, number in value.items())
                lines.append(f"      changes: {{{inner}}}")
            elif key == "modifications":
                inner = ", ".join(json.dumps(str(found), ensure_ascii=False) for found in value)
                lines.append(f"      modifications: [{inner}]")
            elif key == "identity":
                lines.append("      identity:")
                lines.extend(
                    f"        {name}: {scalar(found)}" for name, found in value.items()
                )
            else:
                lines.append(f"      {key}: {scalar(value)}")
        lines.append(f"      view: {scalar(row['view'])}")
    return "\n".join(lines) + "\n"


def split(text: str) -> tuple[str, str]:
    """`results.yaml` as the hand-written register and the generated block after it."""
    at = text.find(MARKER)
    if at < 0:
        return text, ""
    return text[:at], text[at:]


def index_document(path: Path = INDEX) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def problems(
    register_text: str | None = None, index: Mapping[str, Any] | None = None
) -> list[str]:
    """Where `results.yaml`'s generated block, or a case record's `regularization` field,
    differs from what the layer's index gives."""
    text = RESULTS.read_text(encoding="utf-8") if register_text is None else register_text
    _head, block = split(text)
    document = index_document() if index is None else index
    drawn = drawn_counts(document)
    items, unregistered = expected(document, drawn=drawn)
    wanted = block_text(items, unregistered)
    found_problems = case_problems(document, case_fields(document, drawn=drawn))
    if block == wanted:
        return found_problems
    found = (safe_load(block) or {}).get(KEY) or {} if block else {}
    named = {row["n"] for row in found.get("items") or []}
    owed = {row["n"] for row in items}
    detail = []
    if named != owed:
        detail.append(f"items for {sorted(owed - named)} missing, {sorted(named - owed)} extra")
    return [
        f"results.yaml's {KEY} differs from the regularized layer's index"
        + (f" ({'; '.join(detail)})" if detail else "")
        + f"; run {GENERATOR}",
        *found_problems,
    ]


def update() -> tuple[int, int, int]:
    """Write the generated block and the case records' fields; return the items, the
    unregistered counts and the case records changed."""
    text = RESULTS.read_text(encoding="utf-8")
    head, _block = split(text)
    document = index_document()
    drawn = drawn_counts(document)
    items, unregistered = expected(document, drawn=drawn)
    with atomic_output_file(RESULTS) as temporary:
        temporary.write_text(
            head.rstrip("\n") + "\n\n" + block_text(items, unregistered), "utf-8"
        )
    changed = update_cases(case_fields(document, drawn=drawn))
    return len(items), len(unregistered), changed


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--check", action="store_true", help="compare, writing nothing")
    args = parser.parse_args(argv)
    if args.check:
        found = problems()
        for problem in found:
            print(problem)
        if found:
            return 1
        print(
            f"{KEY} in results.yaml and the case records' {CASE_FIELD} agree with the "
            "regularized layer's index"
        )
        return 0
    recorded, missing, changed = update()
    print(
        f"{KEY}: {recorded} items, {missing} drawn counts no registered result holds; "
        f"{changed} case records changed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
