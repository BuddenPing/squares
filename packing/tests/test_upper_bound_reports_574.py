"""PR #574: PingYou Ltd's certificate refinements, whose geometry is in release assets.

The pull request's pinned commit adds HostedData manifests that bind four release assets of
BuddenPing/square-packing-certificates by size and SHA-256, and the certificates are members
of those zip assets. These tests hold the importer's release-asset custody on a synthetic
upstream, the centre-basis adapter, the PR #574 packet's rational declaration and its
algebraic one (`devtools.algebraic_witness_reports`). Only the synthetic upstream needs
Git; nothing needs the network.
"""

from __future__ import annotations

import functools
import hashlib
import io
import json
import os
import shutil
import subprocess
import zipfile
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
import yaml
from test_upper_bound_reports import CENTRED, DATE, DELEEUW

from devtools import algebraic_witness_reports as algebraic
from devtools import check_standing
from devtools import evand_arrangement_reports as kernel
from devtools import evand_exact_certificates as legacy
from devtools import upper_bound_reports as reports
from sqpack.witness import witness_envelope

PR574 = "pingyou-pr574-certificates-2026-10-13"
SYNTHETIC = "synthetic-assets-2026-10-10"
MANIFEST = "packing/hosted/synthetic.yaml"
MEMBER = "bundle/certificate.json"
ASSET = "synthetic.zip"
TAG = "data/synthetic-v1"
REPOSITORY = "example/synthetic"


def _git(directory: Path, *arguments: str) -> str:
    environment = {**os.environ, "GIT_AUTHOR_DATE": DATE, "GIT_COMMITTER_DATE": DATE}
    identity = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid"]
    completed = subprocess.run(
        ["git", *identity, "-C", str(directory), *arguments],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    )
    return completed.stdout.strip()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _readme(packet: Path, rows: list[Any]) -> None:
    table = "\n".join(row.markdown() for row in rows)
    (packet / "README.md").write_text(
        "# Synthetic\n\n## Compressed Files\n\n"
        "| Stored File | Origin | Git Blob of Original | SHA-256 of Original |\n"
        f"| --- | --- | --- | --- |\n{table}\n"
    )


@pytest.fixture
def private(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[str], Path]:
    """Copy a packet into a private repository root and point the importer at it."""
    repo = tmp_path / "private"
    web = repo / reports.WEB.relative_to(reports.REPO)
    monkeypatch.setattr(reports, "REPO", repo)
    monkeypatch.setattr(reports, "WEB", web)
    monkeypatch.setattr(kernel, "REPO", repo)

    def copy(name: str) -> Path:
        target = web / name
        shutil.copytree(reports.ROOT / "resources/web" / name, target)
        return target

    return copy


def _zip(members: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, data in members.items():
            archive.writestr(zipfile.ZipInfo(name, date_time=(2026, 10, 10, 0, 0, 0)), data)
    return stream.getvalue()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


CERTIFICATE = (json.dumps(CENTRED, indent=2) + "\n").encode()


def _spec(**changes: str) -> dict[str, str]:
    return {
        "manifest": MANIFEST,
        "repository": REPOSITORY,
        "tag": TAG,
        "asset": ASSET,
        "member": MEMBER,
        "sha256": _sha256(CERTIFICATE),
        **changes,
    }


@pytest.fixture
def archived(private: Callable[[str], Path], tmp_path: Path) -> tuple[Path, Path, Path]:
    """A derived-only packet whose certificate is a member of a manifest-pinned asset."""
    asset = _zip({MEMBER: CERTIFICATE})
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / ASSET).write_bytes(asset)
    upstream = tmp_path / "upstream"
    (upstream / "packing/hosted").mkdir(parents=True)
    _git(upstream, "init", "--quiet")
    manifest = {
        "repository": REPOSITORY,
        "tag": TAG,
        "objects": [
            {
                "path": f"attic/{ASSET}",
                "asset": ASSET,
                "size": len(asset),
                "sha256": _sha256(asset),
            }
        ],
    }
    (upstream / MANIFEST).write_text(yaml.safe_dump(manifest, sort_keys=False))
    _git(upstream, "add", MANIFEST)
    _git(upstream, "commit", "--quiet", "-m", "manifest")
    packet = reports.WEB / SYNTHETIC
    (packet / "acquisition").mkdir(parents=True)
    _write_json(
        packet / "acquisition/declaration.json",
        {
            "format": "external-source-declaration-v1",
            "id": "synthetic",
            "source_url": "https://example.invalid/synthetic",
            "source_ref": "main",
            "source_commit": _git(upstream, "rev-parse", "HEAD"),
            "retrieved_at_utc": "2026-10-10T00:00Z",
            "git_scope": "The manifest of a synthetic one-commit repository.",
            "archived_dir": "source",
            "license": "None stated: derived-only custody.",
            "claims": ["s(2) <= 3, a synthetic centred certificate in a release asset."],
            "scope": [MANIFEST],
            "pinned_only": [{"match": MANIFEST, "reason": "Derived-only custody."}],
        },
    )
    reports.acquire_source.acquire(packet, upstream, reports.REPO)
    declaration = _json(private(DELEEUW) / reports.DECLARATION)
    declaration.update(
        {
            "issue": "https://example.invalid/pull",
            "certificates": [
                {
                    "n": 2,
                    "path": MEMBER,
                    "format": "centred-json",
                    "offered": "3.0",
                    "first_committed": DATE,
                    "fact": "facts/n-002.yaml",
                    "archive": _spec(),
                }
            ],
            "requested": [2],
            "replayed": [2],
            "houses": [
                {
                    "n": 2,
                    "reader": "grid",
                    "source_key": "[Kingbird]",
                    "holders": "the grid",
                    "reported_value": "2",
                    "verified_value": "2",
                    "evidence": ["E-basic-grid-upper"],
                }
            ],
            "pending": [],
        }
    )
    _write_json(packet / reports.DECLARATION, declaration)
    _readme(packet, [])
    _readme(packet, reports.derive(packet, upstream, assets=assets))
    return packet, upstream, assets


# --------------------------------------------------------------------------- custody


def test_a_fact_from_a_release_asset_reads_offline_and_names_the_members_digest(
    archived: tuple[Path, Path, Path],
) -> None:
    packet, upstream, assets = archived
    expected = reports.parse_certificate(CERTIFICATE, 2, "centred-json")
    assert reports.read_facts(packet) == {2: expected}
    rows = reports.derive(packet, upstream, check=True, assets=assets)
    assert [row.stored for row in rows] == ["facts/n-002.yaml.gz"]
    witness = reports.fact_witness(
        packet,
        reports.load_declaration(packet),
        reports.load_declaration(packet)["certificates"][0],
        expected,
    )
    assert witness["source"]["revision_sha256"] == _sha256(CERTIFICATE)
    assert witness["source"]["url"] == (
        f"https://github.com/{REPOSITORY}/releases/download/{TAG}/{ASSET}#{MEMBER}"
    )


def test_an_asset_that_is_not_the_one_the_manifest_pins_is_refused(
    archived: tuple[Path, Path, Path],
) -> None:
    packet, upstream, assets = archived
    (assets / ASSET).write_bytes(_zip({MEMBER: CERTIFICATE.replace(b'"3"', b'"4"')}))
    with pytest.raises(reports.ReportError, match=r"not the asset the manifest pins|bytes"):
        reports.derive(packet, upstream, check=True, assets=assets)
    with pytest.raises(reports.ReportError, match="needs --assets"):
        reports.derive(packet, upstream, check=True)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"sha256": "0" * 64}, "not the bytes the declaration names"),
        ({"tag": "data/other-v1"}, "does not name"),
        ({"asset": "other.zip"}, "does not list other.zip once"),
    ],
)
def test_a_member_the_manifest_or_the_digest_does_not_bear_out_is_refused(
    archived: tuple[Path, Path, Path], change: dict[str, str], message: str
) -> None:
    packet, upstream, assets = archived
    declaration = _json(packet / reports.DECLARATION)
    declaration["certificates"][0]["archive"].update(change)
    _write_json(packet / reports.DECLARATION, declaration)
    with pytest.raises(reports.ReportError, match=message):
        reports.derive(packet, upstream, check=True, assets=assets)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"path": "bundle/other.json"}, "not its asset member"),
        (
            {"path": "../escape.json", "archive": {**_spec(), "member": "../escape.json"}},
            "names its manifest",
        ),
        ({"fact": None}, "release-asset certificate is a fact"),
    ],
)
def test_the_declaration_refuses_an_asset_member_it_cannot_bind(
    archived: tuple[Path, Path, Path], change: dict[str, Any], message: str
) -> None:
    packet, _upstream, _assets = archived
    declaration = _json(packet / reports.DECLARATION)
    row = declaration["certificates"][0]
    for key, value in change.items():
        if value is None:
            row.pop(key)
        else:
            row[key] = value
    _write_json(packet / reports.DECLARATION, declaration)
    with pytest.raises(reports.ReportError, match=message):
        reports.load_declaration(packet)


def test_the_centre_basis_adapter_reads_a_witness_back_to_its_poses() -> None:
    certificate = reports.parse_certificate(CERTIFICATE, 2, "centred-json")
    witness = kernel.to_witness(certificate)
    raw = json.dumps(witness_envelope(witness, schema="../elsewhere.yaml")).encode()
    assert reports.parse_certificate(raw, 2, "witness-center-basis") == certificate
    witness["squares"][1]["basis"] = ["1", "1/3"]
    raw = json.dumps(witness_envelope(witness)).encode()
    with pytest.raises(reports.ReportError, match="no rotation"):
        reports.parse_certificate(raw, 2, "witness-center-basis")


def test_the_pingyou_adapter_reads_the_574_construction_records_and_no_other_field() -> None:
    base = {"n": 2, "s_exact": "3", "squares": [["1", "1", "0"], ["2", "2", "1/3"]]}
    records = {"construction": "a motif", "rules": [[1, 2]], "boundary_word": {"a": [0]}}
    raw = json.dumps({**base, **records}).encode()
    assert reports.parse_certificate(raw, 2, "pingyou-json").side == 3
    with pytest.raises(reports.ReportError, match="mistyped"):
        reports.parse_certificate(
            json.dumps({**base, "rules": "x"}).encode(), 2, "pingyou-json"
        )
    with pytest.raises(reports.ReportError, match="unknown"):
        reports.parse_certificate(json.dumps({**base, "other": 1}).encode(), 2, "pingyou-json")


# --------------------------------------------------------------------------- the packet


@functools.cache
def _claims() -> dict[int, dict[str, Any]]:
    return {
        row["n"]: row for row in reports.check_claims(reports.packet_path(PR574))["results"]
    }


def test_every_574_certificate_is_admitted_at_its_printed_side() -> None:
    packet = reports.packet_path(PR574)
    declaration = reports.load_declaration(packet)
    certificates = reports.read_facts(packet)
    assert list(certificates) == [row["n"] for row in declaration["certificates"]]
    assert len(certificates) == 85
    for row in declaration["certificates"]:
        side = certificates[row["n"]].side
        if "/" in row["offered"]:
            assert side == Fraction(row["offered"])
        else:
            assert legacy.ceiling_decimal(side, 40) == row["offered"]


def test_each_574_side_is_below_its_case_and_smallest_by_print_only_at_258_and_261() -> None:
    rows = _claims()
    assert all(row["case"]["relation"] == "below" for row in rows.values())
    assert sorted(n for n, row in rows.items() if row["smallest"] == reports.THIS) == [258, 261]
    # Where another report's printed side is decidably smaller: #575, #583 and #593.
    above = {
        n for n, row in rows.items() if any(p["relation"] == "above" for p in row["pending"])
    }
    assert above == {211, 237, 241, 304}


def test_the_574_register_plan_states_each_bound_as_check_standing_reads_it() -> None:
    plan = reports.register_plan(reports.packet_path(PR574))
    result = plan["results.yaml"]
    scope = result["scope"]["n_values"]
    assert scope == sorted(_claims())
    stated = check_standing.statements(" ".join(result["claim"].split()), scope)
    assert {n: bound.value for (n, _), bound in stated.items()} == {
        n: Fraction(_claims()[n]["exact_side"]) for n in scope
    }
    assert result["attribution"]["published"] == "2026-10-13"


def test_the_574_receipts_admit_every_roster_job_on_both_routes() -> None:
    packet = reports.packet_path(PR574)
    positives = reports.check_certification(packet)
    assert list(positives) == reports.load_declaration(packet)["replayed"]
    for margins in reports.margins(positives).values():
        for field in ("containment_clearance", "best_pair_gap"):
            assert margins[f"exact_verify_{field}"] == margins[f"independent_{field}"]
            assert Fraction(margins[f"exact_verify_{field}"]) >= 0


# --------------------------------------------------------------------------- algebraic


@functools.cache
def _algebraic() -> dict[int, dict[str, Any]]:
    record = algebraic.check_claims(reports.packet_path(PR574))
    return {row["n"]: row for row in record["results"]}


def test_the_574_algebraic_witnesses_are_admitted_in_their_declared_fields() -> None:
    packet = reports.packet_path(PR574)
    declaration = algebraic.load_declaration(packet)
    witnesses = algebraic.read_facts(packet)
    assert len(witnesses) == 60
    for row in declaration["witnesses"]:
        polynomial = witnesses[row["n"]]["scalar"]["minimal_polynomial"]
        assert len(polynomial) == row["degree"] + 1


def test_the_574_algebraic_sides_against_the_case_records() -> None:
    rows = _algebraic()
    equal = sorted(n for n, row in rows.items() if row["case"]["verified_relation"] == "equal")
    assert equal == [5, 10, 18, 19, 26, 27, 38, 40, 51, 52, 65, 66, 67, 82, 85, 89]
    assert all(row["case"]["verified_relation"] in {"equal", "below"} for row in rows.values())
    assert sorted(n for n, row in rows.items() if row["below_every_other"]) == [207]
    assert rows[302]["pending"]
    assert any(
        item["report"] == "#583" and item["relation"] == "above"
        for item in rows[302]["pending"]
    )


def test_a_field_witness_passes_the_route_and_both_controls_are_refused() -> None:
    witness = algebraic.read_facts(reports.packet_path(PR574), {5})[5]
    for control in algebraic.JOBS:
        row = algebraic.decide(witness, control)
        algebraic.validate_job(row, witness, control)
    flipped = {**algebraic.decide(witness, "positive"), "control": "duplicate-square-overlap"}
    with pytest.raises(algebraic.ReportError, match="not refused"):
        algebraic.validate_job(flipped, witness, "duplicate-square-overlap")


def test_the_574_algebraic_receipts_admit_every_roster_job() -> None:
    packet = reports.packet_path(PR574)
    positives = algebraic.check(packet)
    assert list(positives) == algebraic.load_declaration(packet)["replayed"]
    assert all(row["verification_passed"] for row in positives.values())
