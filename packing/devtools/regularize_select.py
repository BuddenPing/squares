#!/usr/bin/env python3
"""Choose the regularized view to draw at each count from finished generator runs.

Usage, from `packing/`, after
`uv run --frozen --all-extras --group dev python -m devtools.regularize_select`:

    [--evand-run DIR ...] [--grid-run DIR ...] [--tree DIR] [--repo-root TREE]
        [--workers K] [--output FILE.json] [--markdown FILE.md]

The selection step of the regularization process
(`docs/project/guides/regularization-process.md`), under the owner's rules of 13 October
2026 (`docs/project/policies/regularization-policy.md`, section 9, questions 13 to 15).
It reads finished runs of both generators, `devtools.regularize_evand run` and
`devtools.regularize_grid_slack` at any straightening threshold, and the drawing a tree's
atlas shows today (`--tree`, this checkout by default: the tree's view where its layer's
index says `regularized`, else its known-best witness). Every view each run holds is
decided on four counts:

1. **Exact.** Both maintained routes decide the view over Q
   (`register_regularized_bounds.decide_view`: `sqpack.witness.exact_verify` and the
   independent checker).
2. **Side.** Its exact side against `U`, the case record's `verified_upper_bound` as
   `regularize_evand.upper_bound` reads it (a ceiling the side is held to, never s(n)),
   and against the side today's drawing is drawn at. A view below `U` is a register
   candidate (policy row 3): listed apart, registered through the import runbook first,
   never admitted here.
3. **Table.** The decision table as it stands. An Evan Daniel report is decided again on
   a copy as `regularize_evand reclassify --refresh-bounds` would decide it (`U` read
   again from the case record, a same-side view above it set aside); a grid-slack report
   by `regularize_grid_slack.decided`. Only row 10 (`admit`) is adoptable; rows 7 and 8
   go to the owner.
4. **Drawing.** Seven measures against today's drawing. Five come from the house
   renderer's colouring (`census_drawing_regularity.regularity`), fewer being better: light,
   uneven and near-axis squares, distinct angle classes and hues; a square turned a hair
   off its group adds a class and a hue though the other measures tie (n = 236, two
   squares 0.000537 degrees off). Two are the house and stage totals of full shared sides,
   more being better: the view's from its report's histograms, today's from
   `regularize_evand.contact_partners` on the tree's drawing.

A view is **adoptable** when both routes accept it, its side is at most `U` and at most
today's drawn side, row 10 admits it, it is the view its run draws, it is worse than
today's drawing on no measure, and it is better on one or drawn at a smaller side. A
change that improves no measure at the same side is not made, except where it replaces a
drawing that is not exactly verified (a numerically checked witness) with an exactly
verified view. At each count the first adoptable view in preference order (Evan Daniel's,
then grid-slack by rising threshold, then the order the runs were given) that no other
adoptable view dominates (better on some measure, worse on none) is chosen.

The output is every candidate with its verdicts and the reasons it was not adopted, a
Markdown table of the choices and the register candidates, and the `regularize_evand
layer` commands that admit the chosen views: the Evan Daniel runs in one invocation, the
counts they would admit but were not chosen from them excluded, after a `reclassify` of
any run whose stored decisions are stale; one invocation per grid-slack run, with an empty
`--run-dir`. Nothing is written but the files named. Case records and witnesses are this
checkout's; only today's drawing comes from `--tree`, and a report measured against
another drawing than the tree's is noted.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
import shlex
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Literal

from strif import atomic_output_file

from devtools import census_drawing_regularity as census
from devtools import regularize_evand as driver
from devtools import regularize_grid_slack as grid
from devtools.register_regularized_bounds import decide_view
from sqpack.yamlio import load_yaml

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
FORMAT = "regularized-view-selection-v1"
GENERATOR = "python -m devtools.regularize_select"
#: The house renderer's colouring of a drawing, fewer being better.
DRAWING_MEASURES = ("light_axis", "uneven_axis", "near_axis", "classes", "hues")
#: Full shared sides under the house and stage rules, more being better.
CONTACT_MEASURES = ("house_total", "stage_total")
MEASURES = DRAWING_MEASURES + CONTACT_MEASURES
FEWER_IS_BETTER = frozenset(DRAWING_MEASURES)
#: An Evan Daniel report's outputs, in the order a count's candidates are listed. A
#: same-side view above the bound is `same_above_bound` once `yield_to_bound` sets it aside.
EVAND_OUTPUTS = ("same", "solved", "same_above_bound")
VIEW_FILES = {
    "same": "view-same.yaml",
    "solved": "view-solved.yaml",
    "same_above_bound": "view-same.yaml",
}
RULE = (
    "adoptable: both exact routes accept the view, its side is at most U and at most "
    "today's drawn side, row 10 admits it, it is the view its run draws, it is worse than "
    "today's drawing on no measure, and better on one or at a smaller side, or replaces a "
    "drawing that is not exactly verified; chosen: the "
    "first adoptable view (Evan Daniel's, then grid-slack by rising threshold) that no "
    "other adoptable view dominates"
)


@dataclass(frozen=True)
class Job:
    """One count of one finished run."""

    kind: Literal["evand", "grid"]
    run: Path
    n: int
    rank: int
    """The run's position among the runs given, for the preference order."""


# --------------------------------------------------------------------------------------
# Deciding a view (worker processes)
# --------------------------------------------------------------------------------------


def total(histogram: Sequence[int] | None) -> int | None:
    """Full sides shared, over a histogram of squares with 0 to 4 of them."""
    return None if histogram is None else driver.total_contacts(histogram)


def _literal(value: Fraction | None) -> str | None:
    return None if value is None else driver.literal(value)


def _record(job: Job, output: str | None) -> dict[str, Any]:
    run = job.run.name
    source = f"evand:{run}:{output}" if job.kind == "evand" else f"grid:{run}"
    return {
        "n": job.n,
        "source": source,
        "kind": job.kind,
        "run": str(job.run),
        "rank": job.rank,
        "output": output,
        "threshold": None,
        "view": False,
        "why": None,
    }


def decided_view(
    record: dict[str, Any],
    view: Mapping[str, Any],
    decision: driver.Decision,
    ident: Mapping[str, Any] | None,
    shaded: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """One view decided on both exact routes and measured, beside its table row."""
    n = int(record["n"])
    exact = decide_view(view)
    drawing = census.regularity(view)
    measured = ident is not None and shaded is not None
    current = (shaded or {}).get("against_current") or {}
    histograms = current.get("histograms")
    witness = grid.load_source(n)
    return {
        **record,
        "view": True,
        "routes": {
            "exact_verify": bool(exact["exact_verify"]["passed"]),
            "independent": bool(exact["independent"]["passed"]),
        },
        "side": exact["side"],
        "upper": _literal(driver.upper_bound(driver.case_facts(n))),
        "s_W": _literal(driver.source_frame(witness).side),
        "row": decision.row,
        "decision": decision.decision,
        "reason": decision.reason,
        "measured": measured,
        "measures": {
            **{key: int(drawing[key]) for key in DRAWING_MEASURES},
            "house_total": total((shaded or {}).get("house", {}).get("after"))
            if measured
            else None,
            "stage_total": total((shaded or {}).get("stage", {}).get("after"))
            if measured
            else None,
        },
        "measured_against": None
        if not measured
        else {
            "house": (histograms or {}).get("house"),
            "stage": (histograms or {}).get("stage"),
        },
        "pose": {
            "one_to_one": bool((ident or {}).get("one_to_one")),
            "unnamed_turns": len((ident or {}).get("unnamed_turns") or []),
            "max_move": float((ident or {}).get("max_move") or 0),
            "max_turn_deg": float((ident or {}).get("max_turn_deg") or 0),
        },
    }


def _set_aside(report: Mapping[str, Any]) -> driver.Measured:
    """The table's reading of a same-side view `yield_to_bound` set aside, as if alone."""
    block = report["outputs"]["same_above_bound"]
    alone = {
        **report,
        "outputs": {"same": block, "solved": None},
        "identity": block.get("identity"),
        "shades": block.get("shades"),
    }
    return driver.measured_from_report(alone, "same")


def evand_candidates(job: Job) -> list[dict[str, Any]]:
    """Every view of one count of a driver run, decided as `reclassify --refresh-bounds`
    would decide the run now, on a copy of its report."""
    directory = driver.count_dir(job.run, job.n)
    stored = driver.read_json(directory / "report.json")
    report = copy.deepcopy(stored)
    refreshed = driver.refresh_bound(report, job.n) is not None
    driver.yield_to_bound(report)
    outputs = report.get("outputs") or {}
    solved = driver.measured_from_report(report, "solved")
    same = driver.measured_from_report(report, "same") if outputs.get("same") else None
    governing = "same" if same is not None else "solved"
    decision = driver.classify(same or solved)
    was = stored.get("decision") or {}
    stale = refreshed or (was.get("row"), was.get("decision")) != (
        decision.row,
        decision.decision,
    )
    common = {
        "governing_output": governing,
        "governing_decision": decision.decision,
        "stored_decision": was.get("decision"),
        "stale": stale,
    }
    rows: list[dict[str, Any]] = []
    for name in EVAND_OUTPUTS:
        block = outputs.get(name)
        if not isinstance(block, dict):
            continue
        record = {**_record(job, name), **common, "governing": name == governing}
        # The governing view's measurements are the report's own; another view's, where
        # it was measured, are its block's.
        ident, shaded = block.get("identity"), block.get("shades")
        if name == "same_above_bound":
            measured = _set_aside(report)
        elif name == governing:
            measured = same if same is not None else solved
            ident, shaded = report.get("identity"), report.get("shades")
        else:
            measured = solved
        path = directory / VIEW_FILES[name]
        if not path.is_file():
            rows.append({**record, "why": f"{path.name} is missing"})
            continue
        view = load_yaml(path.read_text(encoding="utf-8"))["witness"]
        rows.append(decided_view(record, view, driver.classify(measured), ident, shaded))
    if not rows:
        rows.append({**_record(job, None), **common, "why": decision.reason})
    return rows


def grid_candidates(job: Job) -> list[dict[str, Any]]:
    """One count of a grid-slack run, decided by `regularize_grid_slack.decided`."""
    directory = job.run / f"n-{job.n:03d}"
    report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
    settings = report.get("settings") or {}
    record = {
        **_record(job, "grid"),
        "threshold": float(settings.get("near_axis_degrees", grid.NEAR_AXIS_DEGREES)),
        "governing": True,
    }
    if report.get("generator") != grid.GENERATOR:
        return [{**record, "why": f"a view of {report.get('generator')}, not {grid.GENERATOR}"}]
    path = directory / "view.yaml.gz"
    if "measured" not in report or not path.is_file():
        return [{**record, "why": str(report.get("refusal") or "no view written")}]
    decision = grid.decided(report, grid.load_source(job.n))
    view = load_yaml(gzip.decompress(path.read_bytes()).decode("utf-8"))["witness"]
    measured = report["measured"]
    return [decided_view(record, view, decision, measured["identity"], measured["shades"])]


def candidates_of(job: Job) -> list[dict[str, Any]]:
    return evand_candidates(job) if job.kind == "evand" else grid_candidates(job)


def today(unit: tuple[Path, int, Mapping[int, Mapping[str, Any]]]) -> dict[str, Any]:
    """The drawing a tree's atlas shows for one count, measured as candidates are."""
    tree, n, entries = unit
    drawing, body = census.drawing_for(tree, n, entries)
    shape = census.regularity(body)
    partners = driver.contact_partners(body)
    house, stage = (driver.histogram(partners[rule]) for rule in driver.RULE_NAMES)
    # Every view the layer draws is exactly verified; a witness is where its claim says
    # so. A numerically checked (decimal) witness is not exactly verified at its printed
    # side, so there is no exact side to hold a view to, and only `U` decides.
    provenance = (body.get("claim") or {}).get("coordinate_provenance")
    verified = drawing.kind == "regularized-view" or provenance == "verified"
    try:
        side = driver.literal(Fraction(str(body["side"]))) if verified else None
    except TypeError, ValueError:
        side = None  # an exact side over a number field, which no rational view meets
    return {
        "n": n,
        "drawing": {"kind": drawing.kind, "path": drawing.path, "generator": drawing.generator},
        "verified": verified,
        "side": side,
        "printed_side": None if side is not None else str(body.get("side")),
        **{key: int(shape[key]) for key in DRAWING_MEASURES},
        "house_total": driver.total_contacts(house),
        "stage_total": driver.total_contacts(stage),
        "house": house,
        "stage": stage,
    }


# --------------------------------------------------------------------------------------
# The owner's rule (pure, on decided rows)
# --------------------------------------------------------------------------------------


def compare(
    view: Mapping[str, int | None], now: Mapping[str, int | None]
) -> tuple[list[str], list[str]]:
    """The measures on which a view is better and worse than today's drawing; a measure
    either side lacks is not compared."""
    gains: list[str] = []
    worse: list[str] = []
    for key in MEASURES:
        mine, theirs = view.get(key), now.get(key)
        if mine is None or theirs is None or mine == theirs:
            continue
        better = mine < theirs if key in FEWER_IS_BETTER else mine > theirs
        (gains if better else worse).append(key)
    return gains, worse


def dominates(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    """Whether view `a` is better than view `b` on some measure and worse on none."""
    better, worse = compare(a["measures"], b["measures"])
    return bool(better) and not worse


def refusals(row: Mapping[str, Any]) -> list[str]:
    """Why a judged candidate is not adoptable, in the order the rule reads; empty when
    it is."""
    if not row["view"]:
        return [f"no view: {row['why']}"]
    reasons: list[str] = []
    refused = sorted(name for name, passed in row["routes"].items() if not passed)
    if refused:
        reasons.append(f"refused by {', '.join(refused)}")
    if row["upper"] is None:
        reasons.append("U is unknown")
    elif not row["at_most_U"]:
        reasons.append(f"its side is {row['minus_U']:+.2e} above U")
    elif row["below_U"]:
        reasons.append(f"its side is {row['minus_U']:+.2e} below U: register it first (row 3)")
    if row["above_drawn"]:
        reasons.append(f"its side is {row['minus_drawn']:+.2e} above today's drawing's")
    if row["decision"] != "admit":
        reasons.append(f"row {row['row']} {row['decision']}: {row['reason']}")
    if not row.get("governing", True):
        reasons.append("not the view its run draws, the only one `layer` admits")
    if not row["measured"]:
        reasons.append("its contacts were not measured")
    if row["worse"]:
        reasons.append(f"worse than today's drawing on {', '.join(row['worse'])}")
    if not row["gains"] and not row["smaller"] and not row["replaces_unverified"]:
        reasons.append("neither better on a measure nor at a smaller side")
    return reasons


def _difference(a: Fraction, b: Fraction | None) -> float | None:
    return None if b is None else float(a - b)


def _fraction(text: str | None) -> Fraction | None:
    return None if text is None else Fraction(text)


def judge(row: Mapping[str, Any], now: Mapping[str, Any]) -> dict[str, Any]:
    """A decided candidate against today's drawing: sides, measures, notes and reasons."""
    judged = dict(row)
    if not judged["view"]:
        judged.update(gains=[], worse=[], notes=[])
    else:
        side = Fraction(judged["side"])
        upper, drawn = _fraction(judged["upper"]), _fraction(now.get("side"))
        judged.update(
            minus_U=_difference(side, upper),
            minus_s_W=_difference(side, _fraction(judged["s_W"])),
            minus_drawn=_difference(side, drawn),
            at_most_U=upper is not None and side <= upper,
            below_U=upper is not None and side < upper,
            above_drawn=drawn is not None and side > drawn,
            smaller=drawn is not None and side < drawn,
            replaces_unverified=not now.get("verified", True),
            now={key: now.get(key) for key in MEASURES},
        )
        gains, worse = compare(judged["measures"], judged["now"])
        judged.update(gains=gains, worse=worse, notes=notes(judged, now))
    judged["refusals"] = refusals(judged)
    judged["adoptable"] = not judged["refusals"]
    return judged


def notes(row: Mapping[str, Any], now: Mapping[str, Any]) -> list[str]:
    """What a reader should know that decides nothing."""
    found: list[str] = []
    against = row.get("measured_against") or {}
    if against.get("house") is not None and (
        against.get("house") != now.get("house") or against.get("stage") != now.get("stage")
    ):
        found.append("the run measured it against another drawing than the tree's")
    elif (
        row.get("measured")
        and against.get("house") is None
        and now.get("drawing", {}).get("kind") == "regularized-view"
    ):
        found.append("the run measured it against no view; the tree draws one")
    if not now.get("verified", True):
        found.append(
            "today's drawing is a numerically checked witness: an exactly verified view at "
            "most U may replace it with no measure better"
        )
    elif now.get("side") is None:
        found.append("today's drawing has no rational side: only U holds the side")
    if row.get("stale"):
        found.append("the run's stored decision is stale: reclassify it before `layer`")
    return found


def preference(row: Mapping[str, Any]) -> tuple[int, float, int, int]:
    """Evan Daniel's views first, then grid-slack by rising threshold, then run order."""
    if row["kind"] == "evand":
        return (0, 0.0, int(row["rank"]), EVAND_OUTPUTS.index(row["output"]))
    return (1, float(row["threshold"] or 0.0), int(row["rank"]), 0)


def choose(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """The first adoptable view in preference order that no other adoptable view
    dominates, or None."""
    adoptable = sorted((row for row in rows if row["adoptable"]), key=preference)
    return next(
        (
            row
            for row in adoptable
            if not any(dominates(other, row) for other in adoptable if other is not row)
        ),
        None,
    )


# --------------------------------------------------------------------------------------
# The plan: the commands that admit the chosen views
# --------------------------------------------------------------------------------------


def layer_admits(rows: Sequence[Mapping[str, Any]]) -> dict[str, set[int]]:
    """The counts `regularize_evand layer` would admit from each Evan Daniel run: those
    whose run draws an admitted view, as stored or as decided now."""
    found: dict[str, set[int]] = {}
    for row in rows:
        if row["kind"] != "evand":
            continue
        admitted = "admit" in {row.get("governing_decision"), row.get("stored_decision")}
        if admitted:
            found.setdefault(row["run"], set()).add(int(row["n"]))
    return found


def _counts(counts: Sequence[int] | set[int]) -> str:
    return " ".join(str(n) for n in sorted(counts))


def layer_commands(
    chosen: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    *,
    repo_root: str = "..",
) -> list[str]:
    """The commands, from `packing/`, that admit exactly the chosen views.

    `layer` reads its driver runs in order and lets a later run's report of a count
    replace an earlier one's, admitted or not, so the driver runs share one invocation
    only where no chosen count appears in another of them; otherwise each run is admitted
    on its own, excluding what it would admit and was not chosen from it.
    """
    prefix = "python -m devtools.regularize_evand"
    root = shlex.quote(repo_root)
    evand_runs: dict[str, set[int]] = {}
    grid_runs: dict[str, set[int]] = {}

    def order(row: Mapping[str, Any]) -> tuple[float, int, int]:
        return (float(row.get("threshold") or 0.0), int(row.get("rank") or 0), int(row["n"]))

    for row in sorted(chosen, key=order):
        target = evand_runs if row["kind"] == "evand" else grid_runs
        target.setdefault(row["run"], set()).add(int(row["n"]))
    present: dict[str, set[int]] = {}
    for row in rows:
        if row["kind"] == "evand":
            present.setdefault(row["run"], set()).add(int(row["n"]))
    stale = sorted(
        {row["run"] for row in rows if row["kind"] == "evand" and row.get("stale")}
        & set(evand_runs)
    )
    commands = [
        f"{prefix} reclassify --run-dir {shlex.quote(run)} --refresh-bounds" for run in stale
    ]
    admits = layer_admits(rows)
    runs = list(evand_runs)
    shared = any(
        n in present.get(other, set())
        for run in runs
        for n in evand_runs[run]
        for other in runs
        if other != run
    )
    for group in [[run] for run in runs] if shared else [runs] if runs else []:
        admitted = set().union(*(admits.get(run, set()) for run in group))
        wanted = set().union(*(evand_runs[run] for run in group))
        command = f"{prefix} layer --run-dir {' '.join(shlex.quote(run) for run in group)} "
        command += f"--repo-root {root}"
        if admitted - wanted:
            command += f" --exclude {_counts(admitted - wanted)}"
        commands.append(command)
    commands.extend(
        f'{prefix} layer --run-dir "$(mktemp -d)" --repo-root {root} '
        f"--grid-run {shlex.quote(run)} --grid-counts {_counts(counts)}"
        for run, counts in grid_runs.items()
    )
    return commands


# --------------------------------------------------------------------------------------
# The selection and its report
# --------------------------------------------------------------------------------------


def jobs_for(evand_runs: Sequence[Path], grid_runs: Sequence[Path]) -> list[Job]:
    jobs: list[Job] = []
    kinds: tuple[tuple[Literal["evand", "grid"], Sequence[Path]], ...] = (
        ("evand", evand_runs),
        ("grid", grid_runs),
    )
    for kind, runs in kinds:
        for rank, run in enumerate(runs):
            resolved = run.resolve()
            jobs.extend(
                Job(kind, resolved, int(path.parent.name.removeprefix("n-")), rank)
                for path in sorted(resolved.glob("n-*/report.json"))
            )
    return jobs


def _map[T, R](function: Callable[[T], R], items: Sequence[T], workers: int) -> list[R]:
    if workers > 1 and len(items) > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(function, items))
    return [function(item) for item in items]


def register_candidates(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Every exactly verified view below `U` (policy row 3): a register result first,
    through the import runbook, and never admitted by this selection."""
    return [
        {key: row[key] for key in ("n", "source", "side", "minus_U", "row", "decision")}
        for row in rows
        if row["view"] and all(row["routes"].values()) and row["below_U"]
    ]


def select(
    evand_runs: Sequence[Path],
    grid_runs: Sequence[Path],
    tree: Path,
    *,
    workers: int = 1,
    repo_root: str = "..",
) -> dict[str, Any]:
    """Decide every view of the runs, judge it against the tree's drawing, and choose."""
    jobs = jobs_for(evand_runs, grid_runs)
    # The largest counts first, so the longest exact decisions do not start last.
    ordered = sorted(jobs, key=lambda job: -job.n)
    decided = [row for rows in _map(candidates_of, ordered, workers) for row in rows]
    entries = census.read_index(tree)
    counts = sorted({job.n for job in jobs})
    drawn = {
        row["n"]: row for row in _map(today, [(tree, n, entries) for n in counts], workers)
    }
    judged = sorted(
        (judge(row, drawn[row["n"]]) for row in decided),
        key=lambda row: (row["n"], preference(row)),
    )
    by_count: dict[int, list[dict[str, Any]]] = {}
    for row in judged:
        by_count.setdefault(int(row["n"]), []).append(row)
    chosen: list[Mapping[str, Any]] = []
    summary: dict[str, Any] = {}
    for n, rows in by_count.items():
        pick = choose(rows)
        if pick is not None:
            chosen.append(pick)
        summary[str(n)] = {
            "today": drawn[n],
            "chosen": None if pick is None else pick["source"],
            "candidates": rows,
        }
    register = register_candidates(judged)
    return {
        "format": FORMAT,
        "generated_by": GENERATOR,
        "policy": driver.POLICY,
        "rule": RULE,
        "tree": str(tree),
        "runs": {
            "evand": [str(run.resolve()) for run in evand_runs],
            "grid": [str(run.resolve()) for run in grid_runs],
        },
        "chosen": [
            {key: row[key] for key in ("n", "source", "run", "output", "gains", "minus_drawn")}
            for row in chosen
        ],
        "register_candidates": register,
        "commands": layer_commands(chosen, judged, repo_root=repo_root),
        "counts": summary,
    }


def _scientific(value: float | None) -> str:
    if value is None:
        return "-"
    return "0" if value == 0 else f"{value:+.2e}"


def _measures(values: Mapping[str, Any]) -> tuple[str, str]:
    return (
        " / ".join(str(values[key]) for key in DRAWING_MEASURES),
        " / ".join(str(values[key]) for key in CONTACT_MEASURES),
    )


def markdown(selection: Mapping[str, Any]) -> str:
    """The choices, the register candidates and the commands, as Markdown."""
    lines = [
        (
            "| n | view | side - U | side - drawn "
            "| light / uneven / near-axis / classes / hues | house / stage sides | better on |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    counts = selection["counts"]
    for n, entry in counts.items():
        pick = next(
            (row for row in entry["candidates"] if row["source"] == entry["chosen"]), None
        )
        if pick is None:
            continue
        before_shape, before_sides = _measures(pick["now"])
        after_shape, after_sides = _measures(pick["measures"])
        lines.append(
            f"| {n} | {pick['source']} | {_scientific(pick['minus_U'])} "
            f"| {_scientific(pick['minus_drawn'])} | {before_shape} -> {after_shape} "
            f"| {before_sides} -> {after_sides} | {', '.join(pick['gains']) or '-'} |"
        )
    unchosen = [n for n, entry in counts.items() if entry["chosen"] is None]
    lines.append("")
    lines.append(
        f"{len(selection['chosen'])} counts chosen; {len(unchosen)} with no adoptable "
        "view (the JSON report gives each candidate's reasons)."
    )
    if selection["register_candidates"]:
        lines += [
            "",
            "Register candidates (policy row 3; registered first, never admitted here):",
            "",
            "| n | view | side - U |",
            "| --- | --- | --- |",
        ]
        lines.extend(
            f"| {row['n']} | {row['source']} | {_scientific(row['minus_U'])} |"
            for row in selection["register_candidates"]
        )
    lines += ["", "```bash", *selection["commands"], "```"]
    return "\n".join(lines) + "\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with atomic_output_file(path) as temporary:
        temporary.write_text(text, encoding="utf-8")


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    command.add_argument(
        "--evand-run", type=Path, nargs="+", default=[], help="finished driver runs"
    )
    command.add_argument(
        "--grid-run", type=Path, nargs="+", default=[], help="finished grid-slack runs"
    )
    command.add_argument(
        "--tree", type=Path, default=REPO, help="the checkout whose drawing is today's"
    )
    command.add_argument(
        "--repo-root", default="..", help="the tree the printed `layer` commands write into"
    )
    command.add_argument("--workers", type=int, default=1, help="processes (default 1)")
    command.add_argument("--output", type=Path, help="write the JSON report here")
    command.add_argument("--markdown", type=Path, help="write the Markdown table here")
    return command


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not args.evand_run and not args.grid_run:
        parser().error("give at least one --evand-run or --grid-run")
    selection = select(
        args.evand_run,
        args.grid_run,
        args.tree.resolve(),
        workers=max(1, args.workers),
        repo_root=args.repo_root,
    )
    table = markdown(selection)
    if args.output:
        _write(args.output, json.dumps(selection, indent=1) + "\n")
    if args.markdown:
        _write(args.markdown, table)
    print(table, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
