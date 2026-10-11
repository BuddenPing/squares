"""Audit Guzhou0806's new-support bound, s(40) > 3359/500, and price its replay.

The comment of 2026-10-11 on jlevy/squares#485 claims ``s(40) > 3359/500 = 6.718`` from a
new rational density: 685 positive D4 rectangle orbits, 522 drawn from wand125's
``rect_n40_L67`` pool and 163 outside it, all with new weights, of mass ``3999/100``. The
continuous-pose and axis kernels of T-145's release decide it unchanged, byte for byte, at
new parameters: side ``B = 3350/3359``, threshold ``4999/5000``, the same 43 slabs of the
half-angle tangent, and the near-axis patch at ``A = 249329659/250000000``. The source is
retained in ``resources/web/guzhou-n40-new-supports-2026-10-11/``; T-145's review
(``docs/project/reviews/review-2026-10-10-guzhou-n40-continuous-pose-bound.md``) read
both kernels line by line and states the input formats this tool regenerates.

Four subcommands:

- ``derive`` writes the two kernel inputs, regenerated here from the retained density
  (`pose_input`, and `axis_input` of `devtools.audit_continuous_pose`), and the crate's
  near-axis input, and prints their SHA-256. Both release receipts name the kernel
  inputs by digest (`POSE_SHA256`, `AXIS_SHA256`), which is what binds them to the
  density.
- ``check`` decides the claim's finite steps in exact rationals (`check_report`): the
  density's orbit facts (`support_facts`: the 522 inherited boxes are rows of the
  original pool, the 163 generated ones are D4-equivalent to none of its 2,526
  rectangles, the 685 orbits are distinct, every box lies in ``K``, every weight is
  positive and they sum to ``M``), the D4 expansion, both inputs' identity and the
  enclosure of every number, the dominated measure, the scalar chain, and every value
  of both release receipts; it refuses the finite controls (`FINITE_CONTROLS`) and
  prices the continuous-pose replay from the receipts and T-145's replay here
  (`price`).
- ``run-axis`` builds the release's axis kernel from the retained source with the
  release's flags in a scratch tree, runs it on the derived input and at two thresholds
  either side of its minimum, and, given a crate binary of reviewed source, decides the
  near-axis statement a second way with ``sqverify-fast``'s exact axis sweep. These are
  the quick parts of the replay; the 43 slabs are not run here.
- ``check-axis`` judges those receipts.

**What its author read** (its independence record, for the finite steps). Written on
2026-10-11 by an AI agent (Claude, lane E of the 2026-10-11 intake pass, ``think-tln9``)
from the release's ``README.md``, ``SOURCES.md``, ``VERIFICATION.md``,
``REPRODUCIBILITY.md``, ``OBSTRUCTION.md``, ``PROOF.md`` (for the density's definition and
the parameters), ``certificate/parameters.json``, the diff of ``verifier/run.py`` and the
workflow against T-145's pin (for the commands; the axis kernel is now built with the
pose kernel's flags), and the receipts and both densities as data; and from
`devtools.audit_continuous_pose`, whose input builders it reuses. It did not open
``verifier/exact.py``, ``verifier/audit.py``, ``obstruction/check.py``,
``obstruction/check.cpp``, ``obstruction/run.py`` or the release's tests. It shares with
``exact.py`` the definition of the density (weight ``w`` puts ``w / (8 |R|)`` on each of
the eight images), its D4 expansion, the kernels' input order, the enclosure rule and the
inward rounding, and no code.

Nothing here decides the continuous cover; the release's kernel does, over the 43 slabs,
and that replay waits for an owner budget (``price`` says what it costs).

Usage, from ``packing/``, each after ``uv run --frozen --all-extras --group dev``::

    python -m devtools.audit_n40_new_supports derive --out DIR
    python -m devtools.audit_n40_new_supports check [--output OUT.json]
    python -m devtools.audit_n40_new_supports run-axis --out DIR \\
        [--crate-binary sqverify_fast/target/release/sqverify-fast]
    python -m devtools.audit_n40_new_supports check-axis [--receipts DIR] [--output OUT]
"""

from __future__ import annotations

import argparse
import gzip
import heapq
import itertools
import json
import math
import shutil
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools.audit_clipped_corner_transfer import (
    Density,
    Rect,
    area,
    d4_maps,
    image,
    invariant,
    merge,
    rational,
    sha256,
    text,
)
from devtools.audit_continuous_pose import CLAIM as T145_CLAIM
from devtools.audit_continuous_pose import (
    CRATE_SCALE,
    FLAGS,
    GRID,
    KERNEL_SOURCES,
    RELEASE_STAGES,
    SQRT2_UP,
    TIMING,
    Check,
    Claim,
    axis_block,
    axis_capture,
    axis_input,
    axis_rows,
    ceil_div,
    coverage_block,
    crate_input,
    dominated,
    extent,
    grid_nodes,
    hex_pair,
    kernel_threshold,
    least_bound,
    maps_terms,
    pose_terms,
    quarter_terms,
    read_receipt,
    read_slabs,
    scalar_block,
    slab_output,
    spawn,
    term_capture,
    without,
    write_json,
)
from devtools.check_sqverify_fast import crate_source_sha256
from devtools.retained_data import read_retained_bytes
from devtools.sqverify_fast_census import REVIEWED_SOURCES

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "packing/resources/web"
PACKET = WEB / "guzhou-n40-new-supports-2026-10-11"
SOURCE = PACKET / "source"
CANDIDATE = SOURCE / "certificate/certified_candidate.json"
#: The original pool, which the 2026-10-01 rectangle packet retains and this packet pins.
ORIGINAL = (
    WEB / "wand125-rectangle-certificates-2026-10-01/wand125-rectangles/certificates"
    "/rect_n40_L67/certified_candidate.json"
)
PARAMETERS = SOURCE / "certificate/parameters.json"
MANIFEST = PACKET / "acquisition/upstream-subtree.sha256"
#: The release's two receipts: the producer's local run in the tree at the pin, and the
#: GitHub Actions run 38120568498 that the release ZIP carries instead.
RECEIPTS = {"local": SOURCE / "results", "ci": PACKET / "release-ci/results"}
RECEIPT_DIR = PACKET / "receipts"
#: T-145's packet: its kernels, its receipts and its replay here, the price's calibration.
T145 = WEB / "guzhou-n40-continuous-pose-2026-10-10"

PIN = "6a65957e6c5c51cdf267917d882dab7f5b4928dd"
CANDIDATE_SHA256 = "984fcd3acc605fe3c50a84912eed77e0192ca5b7253b19b6aa31a4e28e1bf5c2"
ORIGINAL_SHA256 = "71011d0356dd179c6e7e6e02c9a064ff30f6f13844016ce3b97463bf7ef53dc0"
POSE_SHA256 = "6c64a2d21207e7b65ea011dc7ca7a655418840defbf017340ce44ab7fc7b94fb"
AXIS_SHA256 = "10dd46b06f14144619bf9de03151c43215e43e34f7e60df440f4e27d6a594396"
CI_COMPILER = "g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0"
#: The CI run's binaries. The pose binary is T-145's CI binary; the axis binary is new,
#: since ``run.py`` now builds the unchanged axis source with the pose kernel's flags.
CI_BINARIES = {
    "axis": "19288b2f9bcb1cfa86a0bde9db1e1fbb79d43dc8044bc7243af8f6ad405899af",
    "pose": "69bc9e6485102d3636db5377884ba6304f749be94d6ca913d82d80108f1ed4ab",
}
#: Files this release keeps byte for byte from T-145's, whose review read them.
SHARED_WITH_T145 = (
    "verifier/continuous_pose.cpp",
    "verifier/axis_integer_grid.cpp",
    "tests/kernel_harness.cpp",
    "tests/rounding_harness.cpp",
    "tests/oracle.py",
)

#: The claim's parameters, as ``parameters.json`` names them: T-145's but for the side,
#: the bound and the axis side.
CLAIM = replace(
    T145_CLAIM,
    B=Fraction(3350, 3359),
    X=Fraction(3359, 500),
    A=Fraction(249329659, 250000000),
)
#: T-145's bound, which this claim raises by `RAISE`.
EARLIER = Fraction(1340000, 199529)
RAISE = Fraction(217911, 99764500)
#: What PROOF.md section 6 states for ``B - A W(eps)``.
NEAR_AXIS_MARGIN = Fraction(424025836324581, 839750000000839750000000)
SCHEMA = "n40-expanded-rectangles/v1"
COUNTS = {"sites": 685, "inherited": 522, "generated": 163, "terms": 5480, "pool": 2526}


# --------------------------------------------------------------------------- the density


@dataclass(frozen=True)
class Site:
    """One orbit of the new density, as the release lists it."""

    box: Rect
    weight: Fraction
    kind: str
    source_index: int | None


def as_rect(values: Sequence[object]) -> Rect:
    """Four JSON numbers or strings as an exact rectangle ``(x0, y0, x1, y1)``."""
    x0, y0, x1, y1 = (rational(v) for v in values)
    return (x0, y0, x1, y1)


def read_sites(raw: bytes) -> tuple[dict[str, Any], tuple[Site, ...]]:
    """The candidate's header and its sites, every number exact."""
    data = json.loads(raw, parse_float=Fraction)
    sites = tuple(
        Site(
            box=as_rect(item["box"]),
            weight=rational(item["weight"]),
            kind=str(item["kind"]),
            source_index=int(item["source_index"]) if "source_index" in item else None,
        )
        for item in data["sites"]
    )
    header = {key: value for key, value in data.items() if key != "sites"}
    return header, sites


def site_density(raw: bytes) -> Density:
    """The candidate as a density: weight ``w`` on box ``R`` puts ``w / (8 |R|)`` on each
    of its eight images, in site order, as PROOF.md section 1 defines it."""
    header, sites = read_sites(raw)
    side = rational(header["L"])
    rows = tuple((site.box, site.weight) for site in sites if site.weight > 0)
    maps = d4_maps(side)
    terms = [(image(rect, f), w / (8 * area(rect))) for rect, w in rows for f in maps]
    return Density(
        sha256=sha256(raw),
        side=side,
        core=rational(header["B"]),
        n=int(header["n"]),
        listed=len(sites),
        rows=rows,
        terms=len(terms),
        merged=merge(terms),
    )


def read_pool(raw: bytes) -> tuple[list[Rect], list[Fraction]]:
    """The original candidate's 2,526 rectangles and their weights, zero weights kept."""
    data = json.loads(raw, parse_float=Fraction)
    rects = [as_rect(r) for r in data["rectangles"]]
    return rects, [rational(w) for w in data["weights"]]


def canonical(rect: Rect, side: Fraction) -> Rect:
    """The least of a rectangle's eight images: one name per D4 orbit."""
    return min(image(rect, f) for f in d4_maps(side))


@dataclass(frozen=True)
class SupportFacts:
    """What the release says of its 685 orbits, decided on the retained bytes."""

    header: dict[str, Any]
    sites: int
    kinds: dict[str, int]
    positive: int
    in_k: int
    inherited_exact: int
    inherited_distinct: bool
    inherited_positive_before: int
    generated_outside_pool: int
    orbits: int
    mass: Fraction


def support_facts(raw: bytes, pool_raw: bytes) -> SupportFacts:
    header, sites = read_sites(raw)
    side = rational(header["L"])
    pool, weights = read_pool(pool_raw)
    pool_orbits = {canonical(rect, side) for rect in pool}
    inherited = [s for s in sites if s.kind == "inherited"]
    generated = [s for s in sites if s.kind == "generated"]
    indices = [s.source_index for s in inherited]
    return SupportFacts(
        header=header,
        sites=len(sites),
        kinds=dict(Counter(s.kind for s in sites)),
        positive=sum(s.weight > 0 for s in sites),
        in_k=sum(
            0 <= s.box[0] < s.box[2] <= side and 0 <= s.box[1] < s.box[3] <= side for s in sites
        ),
        inherited_exact=sum(
            s.source_index is not None
            and 0 <= s.source_index < len(pool)
            and pool[s.source_index] == s.box
            for s in inherited
        ),
        inherited_distinct=len(set(indices)) == len(indices),
        inherited_positive_before=sum(
            s.source_index is not None and weights[s.source_index] > 0 for s in inherited
        ),
        generated_outside_pool=sum(
            canonical(s.box, side) not in pool_orbits for s in generated
        ),
        orbits=len({canonical(s.box, side) for s in sites}),
        mass=sum((s.weight for s in sites), Fraction(0)),
    )


def load_candidate() -> bytes:
    return read_retained_bytes(CANDIDATE)


def load_pool() -> bytes:
    return read_retained_bytes(ORIGINAL)


# --------------------------------------------------------------------------- the facts


@dataclass(frozen=True)
class InputFacts:
    """What the density and the derived inputs give at the claim."""

    distinct: int
    invariant: bool
    integral: Fraction
    pose_sha256: str
    pose_is_expansion: bool
    enclosures: tuple[int, int]
    axis_sha256: str
    axis_rows: int
    axis_dropped: int
    axis_is_expansion: bool
    axis_dominated: bool
    axis_quarter_invariant: bool
    dominated_mass: Fraction
    axis_weights: int
    evaluation_bound: int
    nodes: tuple[int, int]
    minimiser: tuple[int, int]
    minimum: int
    minimiser_capture: int
    minimiser_capture_g: Fraction


def pose_input(density: Density, claim: Claim = CLAIM) -> bytes:
    """The pose kernel's ``certificate_input.txt`` as this release writes it: T-145's
    format (`devtools.audit_continuous_pose.pose_input`) but for ``B``, which is now a
    hexadecimal pair like every other number, since ``3350/3359`` has no finite decimal.
    The kernel reads each pair with ``stod``, which takes either form."""
    terms = pose_terms(density)
    lines = [hex_pair(claim.L), hex_pair(claim.B), str(len(terms))]
    lines += [" ".join(hex_pair(v) for v in term) for term in terms]
    return ("\n".join(lines) + "\n").encode()


def pose_enclosures(data: bytes, density: Density, claim: Claim = CLAIM) -> tuple[int, int]:
    """How many of the pose input's numbers there are, and how many lie in a finite
    binary64 pair that brackets their rational."""
    lines = data.decode().splitlines()
    values = [claim.L, claim.B]
    pairs = [lines[0].split(), lines[1].split()]
    terms = pose_terms(density)
    if int(lines[2]) != len(terms) or len(lines) != len(terms) + 3:
        return 0, 1
    for term, line in zip(terms, lines[3:], strict=True):
        numbers = line.split()
        values += list(term)
        pairs += [numbers[2 * k : 2 * k + 2] for k in range(len(term))]
    held = 0
    for x, pair in zip(values, pairs, strict=True):
        lo, hi = float.fromhex(pair[0]), float.fromhex(pair[1])
        held += math.isfinite(lo) and math.isfinite(hi) and Fraction(lo) <= x <= Fraction(hi)
    return held, len(values)


def input_facts(density: Density, claim: Claim = CLAIM) -> InputFacts:
    expansion = Counter(maps_terms(density))
    pose = pose_input(density, claim)
    quarter = quarter_terms(density)
    rows = axis_rows(density)
    length, side = int(claim.L * GRID), int(claim.A * GRID)
    dominated_ok = all(
        Fraction(row[0], GRID) >= t[0]
        and Fraction(row[1], GRID) >= t[1]
        and Fraction(row[2], GRID) <= t[2]
        and Fraction(row[3], GRID) <= t[3]
        and 0 <= Fraction(row[4], GRID) <= t[4]
        for row, t in zip(map(dominated, quarter), quarter, strict=True)
    )
    turned = Counter((length - e, a, length - b, d, w) for a, b, d, e, w in rows)
    weights = sum(row[4] for row in rows)
    axis = json.loads(str(read_receipt(RECEIPTS["ci"], "axis.json")["stdout"]))
    x, y = int(axis["minimizer_x_integer"]), int(axis["minimizer_y_integer"])
    return InputFacts(
        distinct=len(density.merged),
        invariant=invariant(density),
        integral=sum((area(r) * v for r, v in density.merged.items()), Fraction(0)),
        pose_sha256=sha256(pose),
        pose_is_expansion=Counter(pose_terms(density)) == expansion,
        enclosures=pose_enclosures(pose, density, claim),
        axis_sha256=sha256(axis_input(rows, claim)),
        axis_rows=len(rows),
        axis_dropped=len(quarter) - len(rows),
        axis_is_expansion=Counter(quarter) == expansion,
        axis_dominated=dominated_ok,
        axis_quarter_invariant=turned == Counter(rows),
        dominated_mass=sum(
            (Fraction(w * (d - a) * (e - b), GRID**3) for a, b, d, e, w in rows), Fraction(0)
        ),
        axis_weights=weights,
        evaluation_bound=16 * weights * (length + length + side // 2) ** 2,
        nodes=(
            len(grid_nodes(rows, length, side, 0)),
            len(grid_nodes(rows, length, side, 1)),
        ),
        minimiser=(x, y),
        minimum=int(axis["minimum_numerator"]),
        minimiser_capture=axis_capture(rows, x, y, side),
        minimiser_capture_g=term_capture(
            maps_terms(density), Fraction(x, GRID), Fraction(y, GRID), claim.A
        ),
    )


# --------------------------------------------------------------------------- the checks


def support_checks(s: SupportFacts, density: Density, claim: Claim = CLAIM) -> list[Check]:
    """The density's orbit facts, against what the release states of them."""
    h = s.header
    expected_header = {
        "B": text(claim.B),
        "L": text(claim.L),
        "X": text(claim.X),
        "axis_side": text(claim.A),
        "epsilon": text(claim.eps),
        "mass": text(claim.mass),
        "threshold": text(claim.tau),
    }
    return [
        Check("density: the release's candidate", density.sha256 == CANDIDATE_SHA256, ""),
        Check(
            "density: its header is the claim's",
            h.get("schema") == SCHEMA
            and h.get("n") == claim.n
            and {k: str(h.get(k)) for k in expected_header} == expected_header
            and h.get("source_sha256") == ORIGINAL_SHA256,
            f"{h.get('schema')}, built on {str(h.get('source_sha256'))[:8]}...",
        ),
        Check(
            "density: 685 positive orbits, 522 inherited and 163 generated",
            (s.sites, s.positive) == (COUNTS["sites"], COUNTS["sites"])
            and s.kinds == {"inherited": COUNTS["inherited"], "generated": COUNTS["generated"]},
            f"{s.positive} of {s.sites} positive; {s.kinds}",
        ),
        Check(
            "density: every box is a proper rectangle in K",
            s.in_k == s.sites,
            f"{s.in_k} of {s.sites}",
        ),
        Check(
            "density: each inherited box is its pool row exactly, no row twice",
            s.inherited_exact == COUNTS["inherited"] and s.inherited_distinct,
            f"{s.inherited_exact} of {COUNTS['inherited']}; "
            f"{s.inherited_positive_before} of them positive in rect_n40_L67",
        ),
        Check(
            "density: no generated box is D4-equivalent to any of the 2526 pool rectangles",
            s.generated_outside_pool == COUNTS["generated"],
            f"{s.generated_outside_pool} of {COUNTS['generated']}",
        ),
        Check(
            "density: the 685 orbits are distinct",
            s.orbits == COUNTS["sites"],
            f"{s.orbits} canonical forms",
        ),
        Check("density: the weights sum to M", s.mass == claim.mass, text(s.mass)),
    ]


def density_checks(f: InputFacts, density: Density, claim: Claim = CLAIM) -> list[Check]:
    """The D4 expansion and both derived inputs, at the claim."""
    held, total = f.enclosures
    length = int(claim.L * GRID)
    terms = COUNTS["terms"]
    return [
        Check(
            "density: D4 expansion",
            density.terms == terms,
            f"{density.terms} terms, {f.distinct} distinct rectangles",
        ),
        Check("density: D4-invariant", f.invariant, "under each of the eight maps"),
        Check("density: integral of g is M", f.integral == claim.mass, text(f.integral)),
        Check("pose input: the receipts' input", f.pose_sha256 == POSE_SHA256, f.pose_sha256),
        Check(
            "pose input: its terms are the D4 expansion",
            f.pose_is_expansion,
            "the same multiset as the eight maps give",
        ),
        Check(
            "pose input: every number brackets its rational",
            held == total == 2 + 5 * terms,
            f"{held} of {total}",
        ),
        Check("axis input: the receipts' input", f.axis_sha256 == AXIS_SHA256, f.axis_sha256),
        Check(
            "axis input: its terms are the D4 expansion",
            f.axis_is_expansion,
            "quarter-turn order, the same multiset as the eight maps give",
        ),
        Check(
            "axis input: every term kept",
            (f.axis_rows, f.axis_dropped) == (terms, 0),
            f"{f.axis_rows} rows, {f.axis_dropped} dropped",
        ),
        Check(
            "axis input: dominated by g",
            f.axis_dominated,
            "supports rounded inward to 1e-9, densities down to 1e-9",
        ),
        Check(
            "axis input: quarter-turn invariant",
            f.axis_quarter_invariant,
            "the integer rows map onto themselves under (x, y) -> (L - y, x)",
        ),
        Check(
            "axis input: the dominated mass is below M",
            0 < claim.mass - f.dominated_mass < Fraction(1, 10**4),
            f"M - mass = {float(claim.mass - f.dominated_mass):.6g}",
        ),
        Check(
            "axis input: the int128 guards",
            f.axis_weights < 10**15 and f.evaluation_bound < 2**125,
            f"16 sum w (l + l + A/2)^2 = {f.evaluation_bound}",
        ),
        Check(
            "axis input: the grid of breakpoints",
            f.nodes == (3293, 3293) and f.nodes[0] * f.nodes[1] <= 15_000_000,
            f"{f.nodes[0]} x {f.nodes[1]} = {f.nodes[0] * f.nodes[1]} vertices",
        ),
        Check(
            "axis: the minimiser is a vertex of the quadrant",
            length // 2 <= f.minimiser[0] <= length - int(claim.A * GRID) // 2
            and length // 2 <= f.minimiser[1] <= length - int(claim.A * GRID) // 2,
            f"({f.minimiser[0]}, {f.minimiser[1]}) / 1e9",
        ),
        Check(
            "axis: the capture at the minimiser, evaluated here",
            f.minimiser_capture == f.minimum,
            f"{f.minimiser_capture} / 1e27",
        ),
        Check(
            "axis: g captures at least as much there",
            f.minimiser_capture_g * GRID**3 >= f.minimiser_capture,
            f"{float(f.minimiser_capture_g):.12f}",
        ),
    ]


def chain_checks(claim: Claim, f: InputFacts, least: Fraction) -> list[Check]:
    """The scalar chain at the claim's parameters, with the receipts' kernel outputs."""
    tip = claim.T * claim.T + 2 * claim.T - 1
    near = claim.eps * claim.eps + 2 * claim.eps - 1
    margin = claim.B - claim.A * extent(claim.eps)
    ends = claim.endpoints
    first, last = (ends[0], ends[-1]) if ends else (0, 0)
    threshold = kernel_threshold(claim.tau)
    required = ceil_div(GRID**3 * claim.tau.numerator, claim.tau.denominator)
    return [
        Check("claim: X = L / B", claim.X == claim.L / claim.B, text(claim.L / claim.B)),
        Check(
            "claim: X raises T-145's bound",
            claim.X - EARLIER == RAISE,
            text(claim.X - EARLIER),
        ),
        Check(
            "counting: n tau - M > 0",
            claim.n * claim.tau - claim.mass > 0,
            text(claim.n * claim.tau - claim.mass),
        ),
        Check(
            "domain: E > 0 at every angle",
            SQRT2_UP * SQRT2_UP > 2 and claim.L > claim.B * SQRT2_UP,
            f"L - B sqrt2_up = {text(claim.L - claim.B * SQRT2_UP)}",
        ),
        Check(
            "slabs: T passes pi/4",
            tip > 0 and Fraction(1, 2) >= claim.T,
            f"T^2 + 2T - 1 = {text(tip)}",
        ),
        Check(
            "slabs: the endpoints partition [eps, T]",
            len(ends) >= 2
            and all(p < q for p, q in itertools.pairwise(ends))
            and Fraction(first, claim.den) == claim.eps
            and Fraction(last, claim.den) == claim.T
            and first > 0
            and 2 * last <= claim.den <= 10**7,
            f"{len(ends) - 1} slabs from {first} to {last} over {claim.den}",
        ),
        Check(
            "slabs: the kernel's threshold is at least tau",
            Fraction(threshold) >= claim.tau,
            f"up(fl(tau)) - tau = {float(Fraction(threshold) - claim.tau):.3g}",
        ),
        Check(
            "slabs: the receipts' least leaf bound is at least the threshold",
            least >= Fraction(threshold),
            f"{text(least)}, above tau by {float(least - claim.tau):.3g}",
        ),
        Check(
            "near-axis: W increases on [0, eps] and A <= B",
            near < 0 and extent(claim.eps) >= 1 and claim.A <= claim.B,
            f"eps^2 + 2 eps - 1 = {float(near):.6g}",
        ),
        Check(
            "near-axis: A W(eps) <= B, by PROOF.md's margin",
            margin >= 0 and (claim != CLAIM or margin == NEAR_AXIS_MARGIN),
            f"B - A W(eps) = {text(margin)}",
        ),
        Check(
            "axis: the receipts' minimum is at least tau",
            f.minimum >= required,
            f"{f.minimum} against ceil(1e27 tau) = {required}",
        ),
    ]


def manifest(path: Path = MANIFEST) -> dict[str, str]:
    """A packet's subtree manifest: upstream path to SHA-256."""
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        out[name.removeprefix("./")] = digest
    return out


def admission_block(s: SupportFacts, f: InputFacts, density: Density) -> dict[str, object]:
    return {
        "axis_evaluation_bound": str(f.evaluation_bound),
        "axis_input_sha256": f.axis_sha256,
        "generated_representatives": s.kinds.get("generated", 0),
        "inherited_representatives": s.kinds.get("inherited", 0),
        "mass": text(s.mass),
        "original_sha256": str(s.header.get("source_sha256")),
        "pose_input_sha256": f.pose_sha256,
        "positive_representatives": s.positive,
        "source_sha256": density.sha256,
        "terms": density.terms,
    }


def slab_row_checks(name: str, rows: Sequence[dict[str, Any]], pose_binary: str) -> Check:
    """Every slab row of one release receipt: the contract's arguments, exit 0, the
    identities, and a verified kernel output whose counts close the cover."""
    digests = manifest()
    good = 0
    for index, ((lo, hi), row) in enumerate(zip(CLAIM.slabs(), rows, strict=False)):
        out = slab_output(row)
        args = [str(lo), str(hi), str(CLAIM.den), "4999", "5000", str(CLAIM.budget)]
        good += (
            row.get("index") == index
            and row.get("arguments") == args
            and row.get("exit_code") == 0
            and row.get("timed_out") is False
            and row.get("input_sha256") == POSE_SHA256
            and row.get("source_sha256") == digests[KERNEL_SOURCES["pose"]]
            and row.get("binary_sha256") == pose_binary
            and out.get("status") == "verified"
            and (out.get("pl"), out.get("ph"), out.get("den")) == (lo, hi, CLAIM.den)
            and int(out["nodes"]) == 2 * int(out["leaves"]) - 1
            and Fraction(out["lower_bound"]) >= Fraction(kernel_threshold(CLAIM.tau))
        )
    return Check(
        f"{name} receipt: every slab verified as the contract runs it",
        good == len(rows) == len(CLAIM.slabs()),
        f"{good} of {len(rows)}",
    )


def receipt_checks(
    name: str, folder: Path, s: SupportFacts, f: InputFacts, density: Density
) -> list[Check]:
    """One release receipt against this tool's values."""
    receipt = read_receipt(folder)
    slabs = read_slabs(folder)
    axis = read_receipt(folder, "axis.json")
    stdout = json.loads(str(axis["stdout"]))
    binaries = receipt.get("binaries") or {}
    digests = manifest()
    sources = receipt.get("source_sha256") or {}
    stages = {stage["stage"]: stage["exit_code"] for stage in receipt.get("stages", [])}
    return [
        Check(
            f"{name} receipt: parameters", receipt.get("parameters") == CLAIM.parameters(), ""
        ),
        Check(
            f"{name} receipt: scalar block",
            receipt.get("scalar") == scalar_block(CLAIM),
            str((receipt.get("scalar") or {}).get("axis_containment_margin")),
        ),
        Check(
            f"{name} receipt: admission block",
            receipt.get("admission") == admission_block(s, f, density),
            "the derived inputs' digests and the orbit counts",
        ),
        Check(
            f"{name} receipt: coverage block is the slabs' totals",
            receipt.get("coverage") == coverage_block(slabs),
            json.dumps(coverage_block(slabs), sort_keys=True),
        ),
        Check(
            f"{name} receipt: axis block is the axis output's",
            receipt.get("axis") == axis_block(stdout, CLAIM),
            json.dumps(axis_block(stdout, CLAIM), sort_keys=True),
        ),
        Check(
            f"{name} receipt: slab and axis records by digest",
            receipt.get("slabs_sha256") == sha256((folder / "slabs.jsonl").read_bytes())
            and receipt.get("axis_sha256") == sha256((folder / "axis.json").read_bytes()),
            "",
        ),
        Check(
            f"{name} receipt: the source it ran is the retained tree",
            len(sources) == 30 and all(digests.get(p) == d for p, d in sources.items()),
            f"{sum(digests.get(p) == d for p, d in sources.items())} of {len(sources)} files",
        ),
        Check(
            f"{name} receipt: status and flags",
            receipt.get("status") == "REPLAYED_SAME_KERNEL"
            and receipt.get("author_claim_status") == "CERTIFIED"
            and receipt.get("claim") == f"s({CLAIM.n}) > {text(CLAIM.X)}"
            and receipt.get("compile_flags") == list(FLAGS)
            and receipt.get("workers") == 4,
            f"{receipt.get('status')}, four workers",
        ),
        Check(
            f"{name} receipt: the axis run",
            axis.get("exit_code") == 0
            and axis.get("input_sha256") == AXIS_SHA256
            and axis.get("source_sha256") == digests[KERNEL_SOURCES["axis"]]
            and axis.get("binary_sha256") == binaries.get("axis")
            and stdout.get("status") == "AXIS_COVERAGE_PROVED"
            and (stdout.get("x_nodes"), stdout.get("y_nodes")) == f.nodes
            and stdout.get("scale") == str(GRID**3)
            and stdout.get("direct_sum_matches") is True
            and stdout.get("evaluation_abs_bound") == str(f.evaluation_bound)
            and int(stdout["minimum_numerator"]) == f.minimum,
            str(stdout.get("status")),
        ),
        slab_row_checks(name, slabs, str(binaries.get("pose"))),
        Check(
            f"{name} receipt: the fourteen stages exited as expected",
            stages == RELEASE_STAGES,
            ", ".join(f"{k} {v}" for k, v in stages.items()),
        ),
    ]


def identity_checks() -> list[Check]:
    """What tells the two receipts apart, what they share, and what the release keeps
    from T-145's."""
    local, ci = read_receipt(RECEIPTS["local"]), read_receipt(RECEIPTS["ci"])
    slabs = {name: read_slabs(folder) for name, folder in RECEIPTS.items()}
    axes = {name: read_receipt(folder, "axis.json") for name, folder in RECEIPTS.items()}
    same = sum(
        without(slab_output(a), TIMING) == without(slab_output(b), TIMING)
        and without(a, {"seconds", "stdout", "binary_sha256"})
        == without(b, {"seconds", "stdout", "binary_sha256"})
        for a, b in zip(slabs["local"], slabs["ci"], strict=True)
    )
    ci_sums = set((PACKET / "release-ci/SHA256SUMS").read_text(encoding="utf-8").splitlines())
    tree_sums = set((SOURCE / "SHA256SUMS").read_text(encoding="utf-8").splitlines())
    result_lines = {
        f"{sha256((RECEIPTS['ci'] / name).read_bytes())}  results/{name}"
        for name in ("axis.json", "obstruction.json", "slabs.jsonl", "verification.json")
    }
    ours, theirs = manifest(), manifest(T145 / "acquisition/upstream-subtree.sha256")
    kept = [path for path in SHARED_WITH_T145 if ours.get(path) == theirs.get(path)]
    return [
        Check(
            "local receipt: the producer's run, not CI",
            local.get("source_commit") is None and "15.2.0" in str(local.get("compiler")),
            f"{local.get('compiler')}, Python {local.get('python')}",
        ),
        Check(
            "ci receipt: run 38120568498 on the pin",
            ci.get("source_commit") == PIN
            and ci.get("compiler") == CI_COMPILER
            and ci.get("binaries") == CI_BINARIES,
            f"{ci.get('compiler')}, Python {ci.get('python')}",
        ),
        Check(
            "receipts: every slab identical apart from timing and the binary",
            same == len(slabs["local"]) == len(slabs["ci"]) == len(CLAIM.slabs()),
            f"{same} of {len(slabs['ci'])}",
        ),
        Check(
            "receipts: the axis outputs identical",
            json.loads(str(axes["local"]["stdout"])) == json.loads(str(axes["ci"]["stdout"])),
            "every field",
        ),
        Check(
            "release-ci SHA256SUMS: the tree's but for the four results lines",
            len(ci_sums) == len(tree_sums) == 34
            and result_lines <= ci_sums
            and len(ci_sums - tree_sums) == 4
            and len(tree_sums - ci_sums) == 4,
            "the CI receipts' digests",
        ),
        Check(
            "kernels: byte for byte T-145's, which its review read",
            kept == list(SHARED_WITH_T145),
            f"{len(kept)} of {len(SHARED_WITH_T145)}: {', '.join(kept)}",
        ),
    ]


# --------------------------------------------------------------------------- controls


@dataclass(frozen=True)
class FiniteControl:
    name: str
    change: str
    claim: Claim
    #: The checks of `chain_checks` that must fail on it.
    expect: tuple[str, ...]


NEAR_AXIS = "near-axis: A W(eps) <= B, by PROOF.md's margin"
FINITE_CONTROLS = (
    FiniteControl(
        "G",
        "A one step of 1/250000000 larger, 249329660/250000000",
        replace(CLAIM, A=Fraction(249329660, 250000000)),
        (NEAR_AXIS,),
    ),
    FiniteControl(
        "G2",
        "tau replaced by 3999/4000, where 40 tau = M",
        replace(CLAIM, tau=Fraction(3999, 4000)),
        ("counting: n tau - M > 0",),
    ),
    FiniteControl(
        "G3",
        "T replaced by 41/100, short of pi/4",
        replace(CLAIM, T=Fraction(41, 100)),
        ("slabs: T passes pi/4", "slabs: the endpoints partition [eps, T]"),
    ),
    FiniteControl(
        "G4",
        "eps replaced by 1/10^5",
        replace(CLAIM, eps=Fraction(1, 10**5)),
        (NEAR_AXIS, "slabs: the endpoints partition [eps, T]"),
    ),
)


def finite_controls(f: InputFacts, least: Fraction) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for control in FINITE_CONTROLS:
        failed = [c.name for c in chain_checks(control.claim, f, least) if not c.held]
        out.append(
            {
                "control": control.name,
                "change": control.change,
                "expect_failed": list(control.expect),
                "failed": failed,
                "refused": all(name in failed for name in control.expect),
            }
        )
    return out


def density_controls(raw: bytes, pool_raw: bytes) -> list[dict[str, object]]:
    """Two altered densities, each refused by `support_checks`: one generated site moved
    onto a pool rectangle's D4 image, and one weight scaled by 99/100."""
    data = json.loads(raw)
    pool = json.loads(pool_raw)["rectangles"]
    first = next(i for i, site in enumerate(data["sites"]) if site["kind"] == "generated")
    side = Fraction(67, 10)
    x0, y0, x1, y1 = (Fraction(str(v)) for v in pool[0])
    mirrored = (side - x1, y0, side - x0, y1)
    moved = json.loads(raw)
    moved["sites"][first]["box"] = [text(v) for v in mirrored]
    scaled = json.loads(raw)
    weight = Fraction(scaled["sites"][0]["weight"]) * Fraction(99, 100)
    scaled["sites"][0]["weight"] = text(weight)
    out: list[dict[str, object]] = []
    for name, change, value, expect in (
        (
            "D1",
            f"generated site {first} moved onto pool rectangle 0 reflected in x",
            moved,
            "density: no generated box is D4-equivalent to any of the 2526 pool rectangles",
        ),
        ("D2", "site 0's weight scaled by 99/100", scaled, "density: the weights sum to M"),
    ):
        mutant = json.dumps(value).encode()
        checks = support_checks(support_facts(mutant, pool_raw), site_density(mutant))
        failed = [c.name for c in checks if not c.held]
        out.append(
            {
                "control": name,
                "change": change,
                "expect_failed": [expect],
                "failed": failed,
                "refused": expect in failed,
            }
        )
    return out


# --------------------------------------------------------------------------- the price


def lpt_makespan(times: Sequence[float], workers: int) -> float:
    """The wall time of the longest-first schedule on ``workers`` processes, as the
    release's runner and `devtools.audit_continuous_pose` hand out slabs."""
    loads = [0.0] * workers
    for t in sorted(times, reverse=True):
        heapq.heapreplace(loads, loads[0] + t)
    return max(loads)


def t145_calibration() -> dict[str, float]:
    """T-145's slabs as its two receipts timed them, and as its replay here did, on the
    host this record's replays run on (the packet's receipts)."""
    with gzip.open(T145 / "receipts/slabs.jsonl.gz", "rt", encoding="utf-8") as handle:
        here = sum(float(json.loads(line)["cpu_seconds"]) for line in handle if line.strip())
    local = sum(float(row["seconds"]) for row in read_slabs(T145 / "source/results"))
    ci = sum(float(row["seconds"]) for row in read_slabs(T145 / "release-ci/results"))
    return {
        "replay_cpu_seconds_here": round(here, 1),
        "local_receipt_slab_seconds": round(local, 1),
        "ci_receipt_slab_seconds": round(ci, 1),
        "here_over_local": round(here / local, 4),
        "here_over_ci": round(here / ci, 4),
    }


def price() -> dict[str, Any]:
    """What the continuous-pose replay costs here, from the two receipts' slab times
    scaled by T-145's measured ratio, and what the rest of the entry point costs."""
    calibration = t145_calibration()
    times = {name: [float(r["seconds"]) for r in read_slabs(f)] for name, f in RECEIPTS.items()}
    ratio = {"local": calibration["here_over_local"], "ci": calibration["here_over_ci"]}
    predicted = {name: [t * ratio[name] for t in ts] for name, ts in times.items()}
    central = [max(a, b) for a, b in zip(predicted["local"], predicted["ci"], strict=True)]
    receipts = {name: read_receipt(folder) for name, folder in RECEIPTS.items()}
    duals = {
        name: round(
            sum(
                float(stage["seconds"])
                for stage in read_receipt(folder, "obstruction.json").get("stages", [])
            ),
            1,
        )
        for name, folder in RECEIPTS.items()
    }
    return {
        "basis": (
            "each slab's time in both release receipts, scaled by T-145's replay here "
            "over the same receipt's time; the larger of the two predictions per slab"
        ),
        "receipt_slab_seconds": {name: round(sum(ts), 1) for name, ts in times.items()},
        "receipt_longest_slab_seconds": {name: round(max(ts), 1) for name, ts in times.items()},
        "t145_calibration": calibration,
        "predicted_slab_cpu_seconds_here": {
            name: round(sum(ts), 1) for name, ts in predicted.items()
        },
        "predicted_slab_cpu_hours_here": round(sum(central) / 3600, 2),
        "predicted_longest_slab_seconds_here": round(max(central), 1),
        "predicted_wall_seconds_here": {
            str(w): round(lpt_makespan(central, w), 1) for w in (1, 2, 4)
        },
        "receipt_full_entry": {
            name: {
                "seconds": round(float(r.get("full_entry_seconds", 0)), 1),
                "workers": r.get("workers"),
                "worker_seconds": round(float(r.get("full_entry_seconds", 0)) * 4, 1),
            }
            for name, r in receipts.items()
        },
        "receipt_dual_seconds": duals,
    }


# --------------------------------------------------------------------------- the report


def check_report() -> dict[str, Any]:
    raw, pool_raw = load_candidate(), load_pool()
    density = site_density(raw)
    s = support_facts(raw, pool_raw)
    f = input_facts(density)
    least, at = least_bound(read_slabs(RECEIPTS["ci"]))
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    checks = [
        Check(
            "density: the pool is rect_n40_L67, as the release pins it",
            sha256(pool_raw) == ORIGINAL_SHA256,
            "the 2026-10-01 packet's copy",
        ),
        *support_checks(s, density),
        *density_checks(f, density),
        *chain_checks(CLAIM, f, least),
        Check(
            "retained parameters.json is the claim",
            parameters == CLAIM.parameters(),
            "all keys",
        ),
    ]
    for name, folder in RECEIPTS.items():
        checks += receipt_checks(name, folder, s, f, density)
    checks += identity_checks()
    controls = finite_controls(f, least) + density_controls(raw, pool_raw)
    held = all(c.held for c in checks) and all(item["refused"] for item in controls)
    margin = CLAIM.B - CLAIM.A * extent(CLAIM.eps)
    minimum = Fraction(f.minimum, GRID**3)
    return {
        "kind": "n40-new-supports-finite-audit/v1",
        "claim": f"s(40) > {text(CLAIM.X)}",
        "candidate": str(CANDIDATE.relative_to(REPO)),
        "values": {
            "raise_over_T145": text(RAISE),
            "counting_margin": text(CLAIM.n * CLAIM.tau - CLAIM.mass),
            "near_axis_margin": text(margin),
            "near_axis_margin_decimal": f"{float(margin):.6g}",
            "kernel_threshold": float.hex(kernel_threshold(CLAIM.tau)),
            "least_leaf_bound": text(least),
            "least_leaf_bound_slab": at,
            "least_leaf_bound_minus_tau": f"{float(least - CLAIM.tau):.6g}",
            "axis_minimum": text(minimum),
            "axis_margin_decimal": f"{float(minimum - CLAIM.tau):.6g}",
            "axis_minimiser": [f.minimiser[0], f.minimiser[1]],
            "g_capture_at_axis_minimiser": f"{float(f.minimiser_capture_g):.15g}",
            "dominated_mass_deficit": f"{float(CLAIM.mass - f.dominated_mass):.6g}",
            "evaluation_bound": str(f.evaluation_bound),
            "distinct_rectangles": f.distinct,
            "inherited_positive_in_rect_n40_L67": s.inherited_positive_before,
            "pose_input_sha256": f.pose_sha256,
            "axis_input_sha256": f.axis_sha256,
        },
        "checks": [c.as_json() for c in checks],
        "controls": controls,
        "price": price(),
        "status": "FINITE_STEPS_HOLD" if held else "FINITE_AUDIT_FAILED",
    }


# --------------------------------------------------------------------------- the axis run


AXIS_SOURCE = KERNEL_SOURCES["axis"]
#: The thresholds either side of the reported minimum 1.0014864314...: the kernel must
#: refuse the first (exit 2) and prove the second, as T-145's control H did. The kernel
#: admits a threshold's numerator and denominator up to 10^6 each, so the one above is
#: 1.001488 = 62593/62500 (1001487/10^6 stops at its input bounds, exit 3).
AXIS_CONTROLS = (
    ("H-above", Fraction(1001488, 10**6), 2, "AXIS_TEST_REFUSED"),
    ("H-below", Fraction(1001486, 10**6), 0, "AXIS_COVERAGE_PROVED"),
)


def crate_axis_input(density: Density) -> bytes:
    """``sqverify-fast``'s near-axis input: the 685 rows with weights scaled by
    `CRATE_SCALE`, side ``A`` on the standard net, threshold one."""
    return crate_input(density, CLAIM.A, Fraction(83, 40000), 201)


def run_axis(out: Path, crate: Path | None) -> dict[str, Any]:
    """Build the axis kernel from the retained source in ``out`` as ``run.py`` does,
    run it on the derived input and at the two control thresholds, and run the crate."""
    density = site_density(load_candidate())
    tree, build, logs = out / "tree", out / "build", out / "logs"
    for folder in (tree / "verifier", build, logs):
        folder.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE / AXIS_SOURCE, tree / AXIS_SOURCE)
    binary = build / "axis"
    argv = ["g++", *FLAGS, AXIS_SOURCE, "-o", str(binary)]
    compiler = subprocess.run(
        ["g++", "--version"], capture_output=True, text=True, check=True
    ).stdout.splitlines()[0]
    built = spawn(argv, tree, logs / "build-axis")
    record: dict[str, Any] = {
        "kind": "n40-new-supports-axis-stage/v1",
        "compiler": compiler,
        "build": {
            "argv": [*argv[:-1], "axis"],
            "source_sha256": sha256((tree / AXIS_SOURCE).read_bytes()),
            "binary_sha256": sha256(binary.read_bytes()) if binary.exists() else None,
            **built,
        },
    }
    rows = axis_rows(density)
    runs: dict[str, Any] = {}
    for name, tau in (("axis", CLAIM.tau), *((n, t) for n, t, _, _ in AXIS_CONTROLS)):
        data = axis_input(rows, CLAIM, tau)
        (out / f"{name}-input.txt").write_bytes(data)
        result = spawn([str(binary), f"{name}-input.txt"], out, logs / name)
        runs[name] = {"tau": text(tau), "input_sha256": sha256(data), **result}
        print(f"{name}: exit {result['exit_code']}, {result['wall_seconds']} s", flush=True)
    record["runs"] = runs
    if crate is not None:
        source = crate_source_sha256()
        reviewed = REVIEWED_SOURCES.get(source)
        if reviewed is None or not reviewed.declared_nets:
            raise SystemExit(f"{source} is not reviewed source for a declared net")
        data = crate_axis_input(density)
        (out / "axis-A.json").write_bytes(data)
        argv = [str(crate), "--candidate", "axis-A.json", "--n", "40", "--side", "67/10"]
        argv += ["--directions", "0", "--threshold", "1", "--threads", "1", "--confirm"]
        result = spawn(argv, out, logs / "crate-axis-A")
        print(f"crate-axis-A: exit {result['exit_code']}, {result['wall_seconds']} s")
        record["crate"] = {
            "argv": ["sqverify-fast", *argv[1:]],
            "binary_sha256": sha256(crate.read_bytes()),
            "crate_source_sha256": source,
            "reviewed_source": {"commit": reviewed.commit, "review": reviewed.review},
            "input_sha256": sha256(data),
            **result,
        }
    receipts = out / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    write_json(receipts / "axis-stage.json", record)
    return record


def axis_stage_checks(record: dict[str, Any]) -> list[Check]:
    """The axis stage's receipts against both release receipts."""
    build, runs = record["build"], record["runs"]
    release = [
        json.loads(str(read_receipt(folder, "axis.json")["stdout"]))
        for folder in RECEIPTS.values()
    ]
    axis = runs["axis"]
    output = json.loads(axis["stdout"]) if axis["exit_code"] == 0 else {}
    ci_compiler = record["compiler"] == CI_COMPILER
    checks = [
        Check(
            "axis build: the retained source, the release's flags",
            build["exit_code"] == 0 and build["argv"][1:5] == list(FLAGS),
            f"{record['compiler']}, binary {str(build['binary_sha256'])[:12]}...",
        ),
        Check(
            "axis build: with the CI run's compiler, the CI run's binary",
            not ci_compiler or build["binary_sha256"] == CI_BINARIES["axis"],
            "compared" if ci_compiler else "another compiler; not compared",
        ),
        Check(
            "axis run: the derived input, every output field both receipts'",
            axis["exit_code"] == 0
            and axis["input_sha256"] == AXIS_SHA256
            and all(output == r for r in release),
            f"{output.get('status')}, minimum {output.get('minimum_numerator')}, "
            f"{axis['wall_seconds']} s",
        ),
    ]
    for name, tau, code, status in AXIS_CONTROLS:
        run = runs[name]
        seen = json.loads(run["stdout"]).get("status") if run["stdout"].strip() else None
        checks.append(
            Check(
                f"axis control {name}: tau = {text(tau)} gives {status}",
                run["exit_code"] == code and seen == status and run["tau"] == text(tau),
                f"exit {run['exit_code']}, {seen}",
            )
        )
    if "crate" in record:
        crate = record["crate"]
        lines = [json.loads(line) for line in crate["stdout"].splitlines() if line]
        row = next((x for x in lines if "r" in x), {})
        summary = next((x for x in lines if x.get("kind")), {})
        premises = summary.get("premises") or {}
        reviewed = REVIEWED_SOURCES.get(str((summary.get("build") or {}).get("source_sha256")))
        checks += [
            Check(
                "crate: reviewed source for a declared net, the binary embeds it",
                reviewed is not None and reviewed.declared_nets,
                str((summary.get("build") or {}).get("source_sha256")),
            ),
            Check(
                "crate: the near-axis statement at side A by the exact vertex sweep",
                crate["exit_code"] == 0
                and premises.get("format") == "T"
                and premises.get("source_rectangles") == COUNTS["sites"]
                and premises.get("mass_exact") == text(CLAIM.mass * CRATE_SCALE)
                and premises.get("B") == text(CLAIM.A)
                and summary.get("threshold") == "1"
                and row.get("verdict") == "verified"
                and row.get("method") == "axis-vertex-sweep"
                and float(row.get("min_certified_lower_bound", 0)) >= 1,
                f"{row.get('verdict')}, {row.get('vertices')} vertices, least "
                f"{row.get('min_certified_lower_bound')!r} at {row.get('argmin')}, "
                f"{crate['wall_seconds']} s",
            ),
        ]
    return checks


def axis_report(folder: Path) -> dict[str, Any]:
    record = json.loads((folder / "axis-stage.json").read_text(encoding="utf-8"))
    checks = axis_stage_checks(record)
    held = all(c.held for c in checks)
    return {
        "kind": "n40-new-supports-axis-check/v1",
        "checks": [c.as_json() for c in checks],
        "status": "AXIS_STAGE_HOLDS" if held else "AXIS_STAGE_FAILED",
    }


# --------------------------------------------------------------------------- the CLI


def emit(report: dict[str, Any], output: Path | None) -> int:
    if output is not None:
        write_json(output, report)
    for item in report.get("checks", []):
        print(f"{'ok  ' if item['held'] else 'FAIL'} {item['name']}: {item['detail']}")
    for item in report.get("controls", []):
        mark = "refused " if item["refused"] else "ADMITTED"
        print(f"{mark} control {item['control']} ({item['change']}): failed {item['failed']}")
    if "price" in report:
        print(json.dumps(report["price"], indent=2, sort_keys=True))
    print(report["status"])
    return 0 if report["status"] in {"FINITE_STEPS_HOLD", "AXIS_STAGE_HOLDS"} else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)
    derive = commands.add_parser("derive", help="write the kernel and crate inputs")
    derive.add_argument("--out", type=Path, required=True)
    check = commands.add_parser("check", help="the finite audit, its controls and the price")
    check.add_argument("--output", type=Path)
    run = commands.add_parser("run-axis", help="build and run the axis kernel and the crate")
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--crate-binary", type=Path)
    judge = commands.add_parser("check-axis", help="judge the axis stage's receipts")
    judge.add_argument("--receipts", type=Path, default=RECEIPT_DIR)
    judge.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "derive":
        density = site_density(load_candidate())
        args.out.mkdir(parents=True, exist_ok=True)
        files = {
            "certificate_input.txt": pose_input(density, CLAIM),
            "axis-input.txt": axis_input(axis_rows(density), CLAIM),
            "axis-A.json": crate_axis_input(density),
        }
        for name, data in files.items():
            (args.out / name).write_bytes(data)
            print(f"{sha256(data)}  {name}")
        return 0
    if args.command == "check":
        return emit(check_report(), args.output)
    if args.command == "run-axis":
        crate = args.crate_binary.resolve() if args.crate_binary else None
        run_axis(args.out.resolve(), crate)
        return emit(axis_report(args.out.resolve() / "receipts"), None)
    return emit(axis_report(args.receipts), args.output)


if __name__ == "__main__":
    sys.exit(main())
