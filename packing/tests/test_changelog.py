"""Changelog reader, publication boundaries, and merged-PR authoring behavior."""

from __future__ import annotations

import copy
import html
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote, urlsplit

import pytest
import yaml
from kpress.format.markdown import parse_markdown

from devtools import import_changelog, render_changelog
from devtools.repo_links import repo_url


def document() -> dict:
    return {
        "softschema": {
            "contract": "packing.squares:SiteChangelog/v1",
            "schema": "site-changelog.schema.yaml",
            "status": "enforced",
        },
        "repository": "https://github.com/jlevy/squares",
        "deliveries": [
            {
                "number": number,
                "title": f"Contribution {number}",
                "merged_at": day + "T12:00:00Z",
                "base_ref": "main",
                "merge_commit": "a" * 40,
                **({"stack_id": 498} if number != 553 else {}),
            }
            for number, day in [
                (553, "2026-10-12"),
                (497, "2026-10-12"),
                (509, "2026-10-13"),
                (549, "2026-10-14"),
            ]
        ],
        "stacks": [
            {
                "id": 498,
                "pull_requests": [497, 509, 549],
                "evidence": "https://github.com/jlevy/squares/pull/498",
            }
        ],
        "coverage": {"pull_requests": [497, 509, 549, 553], "omissions": []},
        "entries": [
            {
                "id": "admission",
                "date": "2026-10-12",
                "title": "Replayed certificates",
                "pull_requests": [553],
                "summary": "Admitted **verified** bounds for $n = 304$.",
                "references": [
                    {"label": "Evidence", "target": "packing/frontier/results.yaml"}
                ],
            },
            {
                "id": "foundations",
                "date": "2026-10-13",
                "title": "Regularization & tooling",
                "pull_requests": [497, 509],
                "stack_id": 498,
                "summary": "Retained the [policy]"
                "(docs/project/policies/regularization-policy.md).",
                "details": "- Comparison tool\n- Provenance\n  - Pinned source",
            },
            {
                "id": "later-delivery",
                "date": "2026-10-14",
                "title": "Driver",
                "pull_requests": [549],
                "stack_id": 498,
                "summary": "Added the driver.",
            },
        ],
        "frozen_entries": [
            {"id": "foundations", "date": "2026-10-13", "pull_requests": [497, 509]}
        ],
    }


def test_shared_renderer_orders_links_math_and_anchors() -> None:
    data = document()
    render_changelog.validate(data)
    github = render_changelog.render_markdown(data)
    site = render_changelog.render_markdown(data, destination="site")
    for text in (github, site):
        assert text.index("2026-10-14") < text.index("2026-10-13") < text.index("2026-10-12")
        assert 'id="foundations"' in text
        assert "https://github.com/jlevy/squares/pull/497" in text
        assert "$n = 304$" in text
        assert "  - Pinned source" in text
    assert "[Evidence](packing/frontier/results.yaml)" in github
    assert (
        "[Evidence](https://github.com/jlevy/squares/blob/main/packing/frontier/results.yaml)"
        in site
    )
    assert (
        "https://github.com/jlevy/squares/blob/main/docs/project/policies/regularization-policy.md"
        in site
    )
    assert "Regularization &amp; tooling" in github


def test_semantic_negative_boundaries() -> None:
    mutations = [
        (lambda d: d["entries"][0].update(date="2026-02-30"), "calendar date"),
        (lambda d: d["entries"][0].update(date="2026-10-11"), "latest merge date"),
        (lambda d: d["entries"][2].update(pull_requests=[553]), "PR #553"),
        (lambda d: d["entries"][0].update(id="foundations"), "duplicate entry"),
        (lambda d: d["deliveries"][0].update(base_ref="feature"), "main"),
        (lambda d: d["deliveries"][0].update(merged_at=None), "merged_at"),
        (lambda d: d["entries"][1].update(stack_id=999), "stack"),
        (
            lambda d: d["entries"][1].update(pull_requests=[509]),
            "frozen",
        ),
        (lambda d: d["entries"][0].update(summary=" "), "blank"),
        (lambda d: d.update(unknown=True), "Additional properties"),
    ]
    for mutate, message in mutations:
        data = document()
        mutate(data)
        with pytest.raises(ValueError, match=message):
            render_changelog.validate(data)
    data = document()
    data["entries"][1].pop("stack_id")
    with pytest.raises(ValueError, match="grouped PRs"):
        render_changelog.validate(data)


def test_markdown_rejects_html_and_unsafe_links_preserves_code() -> None:
    for prose in (
        "<script>forbidden</script>",
        "[bad](javascript:alert%281%29)",
        "[bad](data:text/html,hello)",
        "[bad](//evil.example/x)",
        "[bad](../../escape.md)",
        "[bad][x]\n\n[x]: javascript:alert(1)",
        '[bad](https://example.com){onclick="alert(1)"}',
        "{#unexpected}\n\nA paragraph.",
    ):
        data = document()
        data["entries"][0]["summary"] = prose
        with pytest.raises(ValueError, match=r"raw HTML|unsafe|repository-relative|attributes"):
            render_changelog.validate(data)
    data = document()
    data["entries"][0]["summary"] = "`<b>` and `[policy](README.md)` are code."
    render_changelog.validate(data)
    assert "`[policy](README.md)`" in render_changelog.render_markdown(data, destination="site")


def test_kpress_preserves_math_and_unique_stable_ids() -> None:
    data = document()
    data["entries"][1]["title"] = "Foundations"
    site = render_changelog.render_markdown(data, destination="site")
    tree = parse_markdown(site, title="Changelog", math="auto")
    ids = re.findall(r'\bid="([^"]+)"', tree.html)
    assert len(ids) == len(set(ids))
    assert ids.count("changelog") == 1
    assert ids.count("foundations") == 1
    assert "<math" in tree.html
    assert "<ul>" in tree.html
    assert '<h4 id="foundations">Foundations</h4>' in tree.html


def test_structured_links_reject_decoded_markup_and_unsafe_authorities() -> None:
    attacks = [
        "https://example.com/)<script>forbidden</script>",
        "https://example.com/%3Cscript%3Ealert%281%29%3C/script%3E",
        "https://example.com/&lt;script&gt;alert(1)&lt;/script&gt;",
        "https://example.com/%26lt%3Bscript%26gt%3B",
        "https://example.com/%253Cscript%253E",
        "https://example.com/%0A<script>forbidden</script>",
        "https://example.com\\evil/path",
        "https://user@example.com/path",
        "https://@example.com/path",
        "https://example.com:invalid/path",
        "https://exam ple.com/path",
        "javascript:alert(1)",
    ]
    for attack in attacks:
        for field in ("reference", "publication", "dated_publication", "artifact"):
            data = document()
            entry = data["entries"][0]
            if field == "reference":
                entry["references"] = [{"label": "Evidence", "target": attack}]
            elif field == "artifact":
                entry["artifacts"] = [
                    {"kind": "result", "label": "Current result", "target": attack}
                ]
                entry["publication"] = {"evidence": "https://example.com/audit"}
            else:
                entry["publication"] = {"evidence": attack}
                if field == "dated_publication":
                    entry["publication"]["date"] = "2026-10-12"
            with pytest.raises(ValueError, match=r"unsafe|does not match|registered public"):
                render_changelog.render_markdown(data, destination="site")


def test_structured_link_markdown_delimiters_cannot_create_html_links() -> None:
    injection = ")[Injected](https://evil.example/x)"
    target = "https://example.com/audit" + injection
    artifact_target = "https://jlevy.github.io/squares/result/t-151.html#" + injection
    for dated in (False, True):
        data = document()
        entry = data["entries"][0]
        entry["references"] = [{"label": "Evidence", "target": target}]
        entry["publication"] = {"evidence": target}
        entry["artifacts"] = [
            {"kind": "result", "label": "Current result", "target": artifact_target}
        ]
        if dated:
            entry["publication"]["date"] = "2026-10-12"
        tree = parse_markdown(
            render_changelog.render_markdown(data, destination="site"), title="Changelog"
        )
        links = re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', tree.html, re.DOTALL)
        assert not any(label == "Injected" for _href, label in links)
        assert "<script" not in tree.html
        destinations = [html.unescape(href) for href, _label in links]
        assert quote(target, safe=":/?#@!$&*+,;=%-._~") in destinations
        assert quote(artifact_target, safe=":/?#@!$&*+,;=%-._~") in destinations
        assert "https://github.com/jlevy/squares/pull/553" in destinations


def test_real_structured_links_preserve_exact_canonical_destinations() -> None:
    data = render_changelog.load()
    tree = parse_markdown(
        render_changelog.render_markdown(data, destination="site"), title="Changelog"
    )
    destinations = {
        html.unescape(href) for href in re.findall(r'<a\b[^>]*href="([^"]+)"', tree.html)
    }
    for entry in data["entries"]:
        for number in entry["pull_requests"]:
            assert f"{data['repository']}/pull/{number}" in destinations
        for artifact in entry.get("artifacts", []):
            assert artifact["target"] in destinations
        for reference in entry.get("references", []):
            parts = urlsplit(reference["target"])
            fragment = (f"?{parts.query}" if parts.query else "") + (
                f"#{parts.fragment}" if parts.fragment else ""
            )
            target = reference["target"] if parts.scheme else repo_url(parts.path, fragment)
            assert target in destinations
        if "publication" in entry:
            assert entry["publication"]["evidence"] in destinations


def test_previous_local_main_is_independent_of_editable_frozen_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous = document()
    current = copy.deepcopy(previous)
    current.pop("frozen_entries")
    current["entries"].pop()
    current["coverage"]["omissions"] = [{"pull_request": 549, "reason": "Administrative"}]
    render_changelog.validate(current)
    calls: list[list[str]] = []

    def git(args: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(args)
        stdout = {
            "rev-parse": "a" * 40,
            "ls-tree": "100644 blob metadata site-changelog.yaml",
            "show": yaml.safe_dump(previous, sort_keys=False),
        }[args[1]]
        return subprocess.CompletedProcess(args, 0, stdout=stdout)

    monkeypatch.setattr(render_changelog.subprocess, "run", git)
    with pytest.raises(ValueError, match="frozen entry later-delivery"):
        render_changelog.validate_previous_ref(current, "origin/main")
    assert [call[1] for call in calls] == ["rev-parse", "ls-tree", "show"]


def test_candidate_main_delivery_refusal_does_not_create_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {
            "number": 600,
            "title": "Pending main",
            "mergedAt": "2026-10-15T00:01:00Z",
            "baseRefName": "main",
            "mergeCommit": {"oid": "b" * 40},
            "state": "MERGED",
        }
    ]
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps(rows), encoding="utf-8")
    monkeypatch.setattr(
        import_changelog.subprocess,
        "run",
        lambda args, **_kwargs: subprocess.CompletedProcess(args, 1, stdout="", stderr=""),
    )
    output = tmp_path / "candidate.yaml"
    assert (
        import_changelog.main(
            [
                "--metadata",
                str(metadata),
                "--baseline",
                str(tmp_path / "absent.yaml"),
                "--output",
                str(output),
            ]
        )
        == 1
    )
    assert not output.exists()


def test_coverage_omissions_and_frozen_baseline() -> None:
    data = document()
    old = copy.deepcopy(data)
    data["entries"].pop()
    with pytest.raises(ValueError, match="coverage"):
        render_changelog.validate(data)
    data["coverage"]["omissions"] = [{"pull_request": 549, "reason": "Administrative closeout"}]
    render_changelog.validate(data)
    data["entries"][1]["pull_requests"] = [509]
    with pytest.raises(ValueError, match="frozen"):
        render_changelog.validate_frozen(data, old)


def test_publication_artifacts_and_historical_releases() -> None:
    data = document()
    data["entries"][0].update(
        artifacts=[
            {
                "kind": "result",
                "label": "Current result",
                "target": "https://jlevy.github.io/squares/result/t-151.html",
            }
        ],
        publication={"evidence": "https://github.com/jlevy/squares/actions/runs/123"},
        releases=[{"component": "site", "version": "v0.4.1"}],
    )
    render_changelog.validate(data)
    assert "First public" not in render_changelog.render_markdown(data)
    data["entries"][0]["releases"][0]["version"] = "v9.9.9"
    with pytest.raises(ValueError, match="retained history"):
        render_changelog.validate(data)
    data["entries"][0].pop("releases")
    data["entries"][0]["artifacts"][0]["target"] = "https://evil.example/result.html"
    with pytest.raises(ValueError, match="registered public"):
        render_changelog.validate(data)
    data["entries"][0]["artifacts"][0]["target"] = (
        "https://jlevy.github.io/squares/result/t-151.html"
    )
    data["entries"][0].pop("publication")
    with pytest.raises(ValueError, match="publication evidence"):
        render_changelog.validate(data)


def test_freshness_check_and_soft_wrapping(tmp_path: Path) -> None:
    source, output = tmp_path / "history.yaml", tmp_path / "CHANGELOG.md"
    source.write_text(yaml.safe_dump(document(), sort_keys=False), encoding="utf-8")
    assert render_changelog.main(["--source", str(source), "--output", str(output)]) == 0
    assert (
        render_changelog.main(["--source", str(source), "--output", str(output), "--check"])
        == 0
    )
    current = output.read_text(encoding="utf-8")
    output.write_text(
        current.replace("Admitted **verified** bounds", "Admitted\n**verified** bounds"),
        encoding="utf-8",
    )
    assert (
        render_changelog.main(["--source", str(source), "--output", str(output), "--check"])
        == 0
    )
    output.write_text(current.replace("Admitted", "Claimed"), encoding="utf-8")
    assert (
        render_changelog.main(["--source", str(source), "--output", str(output), "--check"])
        == 1
    )


def test_candidate_import_requires_actual_merged_main_and_preserves_old_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = document()
    rows = [
        {
            "number": 600,
            "title": "New tooling",
            "body": "Needs editorial review",
            "mergedAt": "2026-10-15T00:01:00Z",
            "baseRefName": "main",
            "mergeCommit": {"oid": "b" * 40},
            "state": "MERGED",
        }
    ]
    candidate = import_changelog.draft(rows, baseline)
    assert candidate["entries"][:-1] == baseline["entries"]
    assert candidate["entries"][-1]["date"] == "2026-10-15"
    assert "artifacts" not in candidate["entries"][-1]
    render_changelog.validate(candidate)
    for key, value in [("mergedAt", None), ("baseRefName", "feature"), ("state", "OPEN")]:
        bad = copy.deepcopy(rows)
        bad[0][key] = value
        with pytest.raises(ValueError, match="merged main metadata"):
            import_changelog.draft(bad, baseline)
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps(rows), encoding="utf-8")
    output = tmp_path / "candidate.yaml"
    checked = []
    monkeypatch.setattr(
        import_changelog,
        "verify_main_delivery",
        lambda delivery, main_ref: checked.append((delivery["number"], main_ref)),
    )
    assert (
        import_changelog.main(
            [
                "--metadata",
                str(metadata),
                "--baseline",
                str(tmp_path / "absent.yaml"),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert checked == [(600, "origin/main")]
    assert "editorial review" in output.read_text(encoding="utf-8").lower()
