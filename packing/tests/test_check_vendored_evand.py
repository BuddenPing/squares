"""The vendored regularizer is held to its manifest, and every way out of it is refused.

`devtools.check_vendored_evand` passes the real copy, then each rule is rehearsed on a
small copy built here: an unrecorded edit, a dropped file, a stray file, each kind of
local change done right and done wrong, the licence, and the re-pin writer.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import time
from pathlib import Path

import pytest

from devtools import check_vendored_evand as vendored
from sqpack.yamlio import safe_load

COMMIT = "0123456789abcdef0123456789abcdef01234567"
SCRATCH_GIT = (
    "-c",
    "user.name=vendored test",
    "-c",
    "user.email=vendored-test@example.invalid",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "core.hooksPath=/dev/null",
)
UPSTREAM = {
    "LICENSE": b"MIT License\n\nCopyright (c) 2026 Example Author\n",
    "CREDITS.md": b"# credits\n",
    "search/tool.py": b"import sys\nprint(sys.argv)\n",
    "search/data.json": b'{"n": 1}\n',
}
METADATA = {
    "source_url": "https://example.invalid/upstream",
    "source_commit": COMMIT,
    "git_tree": "f" * 40,
    "committed": "2026-10-11T10:34:02-06:00",
    "subject": "a subject: with a colon",
    "copyright": "Copyright (c) 2026 Example Author",
}


@pytest.fixture(autouse=True)
def _no_inherited_git(monkeypatch: pytest.MonkeyPatch) -> None:
    """An inherited `GIT_INDEX_FILE` must not aim the scratch repositories elsewhere."""
    for name in list(os.environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name)


def _git(directory: Path, *arguments: str) -> str:
    done = subprocess.run(
        ("git", "-C", str(directory), *SCRATCH_GIT, *arguments),
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def _copy(root: Path, local_changes: str = "[]") -> Path:
    """A vendored copy of `UPSTREAM` under `root`, with its manifest and provenance file."""
    directory = root / "vendor" / "upstream"
    for path, data in UPSTREAM.items():
        (directory / path).parent.mkdir(parents=True, exist_ok=True)
        (directory / path).write_bytes(data)
    files = [
        vendored.Pinned(path, len(data), hashlib.sha256(data).hexdigest())
        for path, data in sorted(UPSTREAM.items())
    ]
    text = vendored.render_manifest(metadata=METADATA, files=files, retrieved="2026-10-11")
    (directory / vendored.MANIFEST_NAME).write_text(
        text.replace("local_changes: []", f"local_changes: {local_changes}"), encoding="utf-8"
    )
    (directory / "README.md").write_text("# Vendored\n\n### Local Changes\n\nNone.\n")
    return directory


def _describe(directory: Path, entry: str) -> None:
    """The provenance file, with `entry` as its Local Changes section."""
    (directory / "README.md").write_text(f"# Vendored\n\n### Local Changes\n\n{entry}\n")


def _problems(directory: Path) -> list[str]:
    manifest = vendored.load_manifest(directory / vendored.MANIFEST_NAME)
    return vendored.check(directory, manifest, vendored.present_files(directory))


def _change(path: str, kind: str) -> str:
    return (
        f"[{{path: {path}, kind: {kind}, date: '2026-10-12', bead: think-abcd, reason: why}}]"
    )


def test_the_real_vendored_copy_matches_its_manifest(
    capsys: pytest.CaptureFixture[str],
) -> None:
    started = time.perf_counter()
    assert vendored.main([]) == 0
    assert time.perf_counter() - started < 5  # the step is priced at under a second
    output = capsys.readouterr().out
    assert "vendored copy check passed: 351 files match" in output
    assert "square-packing@675a5ea" in output


def test_the_real_manifest_pins_the_licence_and_the_commit() -> None:
    manifest = vendored.load_manifest(vendored.VENDORED / vendored.MANIFEST_NAME)
    assert manifest.source_commit == "675a5eaa8712542daac8b4515b0f69ad7044df44"
    assert manifest.license_file == "LICENSE"
    assert "README.md" not in manifest.files  # the project's own, never an upstream file
    assert "Copyright (c) 2026 Evan Daniel" in (vendored.VENDORED / "LICENSE").read_text()
    # A re-render of the parsed manifest is the file itself, so `--write` reproduces it.
    record = safe_load((vendored.VENDORED / vendored.MANIFEST_NAME).read_text())
    rendered = vendored.render_manifest(
        metadata={key: str(record[key]) for key in METADATA},
        files=list(manifest.files.values()),
        retrieved=str(record["retrieved"]),
    )
    assert rendered == (vendored.VENDORED / vendored.MANIFEST_NAME).read_text()


def test_a_pristine_copy_passes(tmp_path: Path) -> None:
    assert _problems(_copy(tmp_path)) == []


def test_an_unrecorded_edit_is_refused_whether_or_not_the_size_moved(tmp_path: Path) -> None:
    directory = _copy(tmp_path)
    (directory / "search/tool.py").write_bytes(b"import sys\nprint(sys.path)\n")
    (directory / "search/data.json").write_bytes(b'{"n": 2, "m": 3}\n')
    problems = _problems(directory)
    assert any("search/tool.py: not the pinned bytes" in line for line in problems)
    assert any("search/data.json: 17 bytes, not the pinned 9" in line for line in problems)


def test_a_dropped_file_and_a_stray_file_are_refused(tmp_path: Path) -> None:
    directory = _copy(tmp_path)
    (directory / "search/data.json").unlink()
    (directory / "runs").mkdir()
    (directory / "runs/out.json").write_text("{}")
    problems = _problems(directory)
    assert "search/data.json: pinned, but missing from the vendored copy" in problems
    assert any(line.startswith("runs/out.json: not in the manifest") for line in problems)


def test_the_walk_skips_interpreter_caches(tmp_path: Path) -> None:
    directory = _copy(tmp_path)
    (directory / "search/__pycache__").mkdir()
    (directory / "search/__pycache__/tool.cpython-314.pyc").write_bytes(b"\0")
    assert _problems(directory) == []


def test_git_answers_what_the_directory_holds(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    (tmp_path / ".gitignore").write_text("*.log\n")
    directory = _copy(tmp_path)
    _git(tmp_path, "add", ".")
    (directory / "search/run.log").write_text("ignored, so never content\n")
    assert _problems(directory) == []
    (directory / "search/new.py").write_text(
        "untracked and unignored, so it would be committed\n"
    )
    assert _problems(directory) == [
        (
            "search/new.py: not in the manifest; vendored code changes only by a recorded "
            "local change, and run outputs belong in a scratch directory, not here"
        )
    ]


def test_a_recorded_modification_passes_once_it_is_marked(tmp_path: Path) -> None:
    directory = _copy(tmp_path, _change("search/tool.py", "modified"))
    assert _problems(directory) == [
        "search/tool.py: recorded as modified, but it is still the pinned bytes",
        (
            "search/tool.py: recorded as a local change, but README.md's Local Changes "
            "does not name it"
        ),
    ]
    (directory / "search/tool.py").write_bytes(b"import sys\nprint(sys.path)\n")
    (directory / "README.md").write_text(
        "### Local Changes\n\n`search/tool.py` prints sys.path.\n"
    )
    assert _problems(directory) == [
        (
            "search/tool.py: modified, but its first 20 lines carry no comment naming "
            "vendor/evand-regularize/README.md"
        )
    ]
    (directory / "search/tool.py").write_bytes(
        b"# Locally modified (think-abcd); see vendor/evand-regularize/README.md.\n"
        b"import sys\nprint(sys.path)\n"
    )
    assert _problems(directory) == []


def test_a_modified_data_file_needs_no_header_comment(tmp_path: Path) -> None:
    directory = _copy(tmp_path, _change("search/data.json", "modified"))
    (directory / "search/data.json").write_bytes(b'{"n": 2}\n')
    _describe(directory, "`search/data.json` holds 2.")
    assert _problems(directory) == []


def test_a_removal_and_an_addition_are_held_to_what_they_say(tmp_path: Path) -> None:
    changes = (
        "[{path: search/data.json, kind: removed, date: '2026-10-12', bead: think-abcd, "
        "reason: unused}, {path: search/extra.py, kind: added, date: '2026-10-12', "
        "bead: think-abcd, reason: a driver}]"
    )
    directory = _copy(tmp_path, changes)
    _describe(directory, "`search/data.json` removed; `search/extra.py` added.")
    assert _problems(directory) == [
        "search/data.json: recorded as removed, but it is still here",
        "search/extra.py: recorded as added, but it is not here",
    ]
    (directory / "search/data.json").unlink()
    (directory / "search/extra.py").write_text(
        "# Added here (think-abcd); see vendor/evand-regularize/README.md.\n"
    )
    assert _problems(directory) == []


#: Each kind of local change, applied correctly: the path it records and the bytes it
#: leaves there (None for a removal).
APPLIED = {
    "modified": (
        "search/tool.py",
        (
            b"# Locally modified (think-abcd); see vendor/evand-regularize/README.md.\n"
            b"import sys\nprint(sys.path)\n"
        ),
    ),
    "added": (
        "search/extra.py",
        b"# Added here (think-abcd); see vendor/evand-regularize/README.md.\n",
    ),
    "removed": ("search/data.json", None),
}


@pytest.mark.parametrize("kind", sorted(APPLIED))
def test_only_the_local_changes_section_names_a_change(tmp_path: Path, kind: str) -> None:
    """A path the role table or a later section names is not thereby a described change."""
    path, data = APPLIED[kind]
    directory = _copy(tmp_path, _change(path, kind))
    if data is None:
        (directory / path).unlink()
    else:
        (directory / path).write_bytes(data)
    pristine = "None. Every file is byte-identical to the pin."
    readme = (
        f"# Vendored\n\n## What Each File Is For\n\n| `{path}` | its role |\n\n"
        f"### Local Changes\n\n{pristine}\n\n## Re-pinning\n\nRestore `{path}` first.\n"
    )
    (directory / "README.md").write_text(readme)
    assert _problems(directory) == [
        f"{path}: recorded as a local change, but README.md's Local Changes does not name it"
    ]
    (directory / "README.md").write_text(readme.replace(pristine, f"`{path}` is {kind}."))
    assert _problems(directory) == []


def test_the_local_changes_section_ends_at_the_next_heading_outside_code() -> None:
    readme = (
        "## Forking\n\nName `a.py` here.\n\n### Local Changes\n\n"
        "```sh\n# a comment, not a heading\n```\n\n`b.py` is patched.\n\n"
        "#### Detail\n\n`c.py`\n\n## Re-pinning\n"
    )
    section = vendored.local_changes_text(readme)
    assert "`b.py` is patched." in section
    assert "a.py" not in section
    assert "c.py" not in section
    assert vendored.local_changes_text("`b.py` is patched.\n") == ""


def test_the_licence_is_never_a_local_change(tmp_path: Path) -> None:
    directory = _copy(tmp_path, _change("LICENSE", "modified"))
    (directory / "LICENSE").write_text("All rights reserved.\n")
    _describe(directory, "`LICENSE` replaced.")
    assert (
        "LICENSE: the licence file is never a local change; the MIT grant requires its notice "
        "with every copy"
    ) in _problems(directory)


def test_the_project_files_must_be_there(tmp_path: Path) -> None:
    directory = _copy(tmp_path)
    (directory / "README.md").unlink()
    assert _problems(directory) == [
        "README.md: this project's file is missing from the vendored directory"
    ]


@pytest.mark.parametrize(
    ("edit", "complaint"),
    [
        (("source_commit: " + COMMIT, "source_commit: 0123abc"), "full 40-digit commit id"),
        (("format: vendored-source-v1", "format: other"), "`format` must be"),
        (("retrieved: '2026-10-11'", "retrieved: yesterday"), "`retrieved` must be"),
        (("license_file: LICENSE", "license_file: COPYING"), "not among the pinned files"),
        (("local_changes: []", "local_changes: none"), "`local_changes` must be a list"),
    ],
)
def test_a_malformed_manifest_is_refused(
    tmp_path: Path, edit: tuple[str, str], complaint: str
) -> None:
    directory = _copy(tmp_path)
    manifest = directory / vendored.MANIFEST_NAME
    manifest.write_text(manifest.read_text().replace(*edit), encoding="utf-8")
    with pytest.raises(vendored.ManifestError, match=complaint):
        vendored.load_manifest(manifest)


def test_a_change_without_a_bead_or_a_known_kind_is_refused(tmp_path: Path) -> None:
    manifest = _copy(tmp_path, _change("search/tool.py", "patched")) / vendored.MANIFEST_NAME
    with pytest.raises(vendored.ManifestError, match="`kind` is one of"):
        vendored.load_manifest(manifest)
    text = manifest.read_text().replace("kind: patched", "kind: modified")
    manifest.write_text(text.replace("bead: think-abcd", "bead: soon"), encoding="utf-8")
    with pytest.raises(vendored.ManifestError, match="`bead` must name the bead"):
        vendored.load_manifest(manifest)


def test_a_path_listed_twice_or_outside_the_copy_is_refused(tmp_path: Path) -> None:
    manifest = _copy(tmp_path) / vendored.MANIFEST_NAME
    text = manifest.read_text()
    line = next(row for row in text.splitlines() if "path: LICENSE" in row)
    manifest.write_text(text + line + "\n", encoding="utf-8")
    with pytest.raises(vendored.ManifestError, match="LICENSE is listed twice"):
        vendored.load_manifest(manifest)
    manifest.write_text(
        text.replace("path: search/tool.py", "path: ../tool.py"), encoding="utf-8"
    )
    with pytest.raises(vendored.ManifestError, match="not a plain relative POSIX path"):
        vendored.load_manifest(manifest)


def _upstream(tmp_path: Path) -> Path:
    checkout = tmp_path / "upstream"
    checkout.mkdir()
    _git(checkout, "init", "-q")
    for path, data in UPSTREAM.items():
        (checkout / path).parent.mkdir(parents=True, exist_ok=True)
        (checkout / path).write_bytes(data)
    _git(checkout, "add", ".")
    _git(checkout, "commit", "-q", "-m", "a subject: with a colon")
    _git(checkout, "remote", "add", "origin", "https://example.invalid/upstream.git")
    return checkout


def test_a_repin_binds_each_file_to_the_upstream_blob(tmp_path: Path) -> None:
    checkout = _upstream(tmp_path)
    directory = _copy(tmp_path / "project")
    commit = _git(checkout, "rev-parse", "HEAD")
    text = vendored.repin(directory, checkout, commit="HEAD", retrieved="2026-10-12")
    (directory / vendored.MANIFEST_NAME).write_text(text, encoding="utf-8")
    manifest = vendored.load_manifest(directory / vendored.MANIFEST_NAME)
    assert manifest.source_commit == commit
    assert manifest.source_url == "https://example.invalid/upstream"
    assert sorted(manifest.files) == sorted(UPSTREAM)
    assert _problems(directory) == []
    # A working-tree edit in the checkout is not the commit, and does not move the pin.
    (checkout / "search/tool.py").write_text("edited after the commit\n")
    assert vendored.repin(directory, checkout, commit="HEAD", retrieved="2026-10-12") == text


def test_a_repin_refuses_bytes_the_commit_does_not_hold(tmp_path: Path) -> None:
    checkout = _upstream(tmp_path)
    directory = _copy(tmp_path / "project")
    (directory / "search/tool.py").write_text("not upstream's\n")
    (directory / "search/local.py").write_text("upstream never had this\n")
    with pytest.raises(vendored.ManifestError) as refusal:
        vendored.repin(directory, checkout, commit="HEAD", retrieved="2026-10-12")
    assert "search/tool.py: not upstream's bytes at" in str(refusal.value)
    assert "search/local.py: upstream has no such file at" in str(refusal.value)


def test_a_repin_refuses_while_local_changes_are_recorded(tmp_path: Path) -> None:
    checkout = _upstream(tmp_path)
    directory = _copy(tmp_path / "project", _change("search/data.json", "modified"))
    with pytest.raises(vendored.ManifestError, match="restore the pristine copy"):
        vendored.repin(directory, checkout, commit="HEAD", retrieved="2026-10-12")


def test_the_command_reports_and_fails_on_a_finding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    directory = _copy(tmp_path)
    (directory / "stray.txt").write_text("x")
    assert vendored.main(["--directory", str(directory)]) == 1
    assert "stray.txt: not in the manifest" in capsys.readouterr().err
