#!/usr/bin/env python3
"""Hold the vendored copy of Evan Daniel's regularizer to its manifest.

`vendor/evand-regularize/` is a subset of evand/square-packing copied byte for byte at one
pinned commit: the exact solver and its two checkers under `search/exact/`, the
regularizer under `search/regularize/`, and the inputs and lists they read. It is the
generator behind the regularized drawing layer, and it decides nothing: every view it
produces is decided by this project's exact checkers. The directory's `README.md` says
what each file is for, how the credit is written and how the copy is forked or re-pinned;
`vendored.yaml` is the manifest this module reads.

**Why a digest here, against OR-16's default.** The rule reserves checksums for a real
trust boundary, and requires three answers beside one:

- *The boundary*: third-party code downloaded from another repository. Its bytes did not
  come from this project, and the point of vendoring it is that a reader can say exactly
  which upstream bytes ran.
- *The independently supplied expected value*: each file's SHA-256 as the upstream blob at
  the pinned commit, recorded when the copy was made and re-derivable by anyone from the
  upstream repository (`git show <pin>:<path> | sha256sum`), without trusting this one.
- *The failure it detects*: an in-place edit of the vendored code that is not recorded as
  a reviewed local change (a silent fork, after which the credit and the pin would both
  misdescribe what ran), a vendored file dropped, an unrecorded file added beside them,
  or a re-pin that left the manifest describing the old bytes.

Nothing else may refuse anything on these digests. No tool that runs the generator reads
them, and a mismatch here fails this check alone; it never blocks a regularization run or
invalidates a result, whose soundness rests on the exact checkers, not on the generator.

**What passes.** Every pinned file is present with its size and SHA-256, unless the
manifest's `local_changes` records it: `modified` (present, no longer the pinned bytes,
and for code a header comment naming `vendor/evand-regularize/README.md`), `removed`
(absent), `added` (a file upstream never had, present), or `replica` (a patch applied
only to a scratch replica of the copy, so the file here stays the pinned bytes, and the
patch, a unified diff at the repository-relative `patch` path, still applies to them
exactly). The README names each recorded change's path, and a replica patch's file name,
so the prose account and the manifest cannot drift apart. The licence file is never a
local change: the MIT grant requires its notice with every copy.
Nothing else is in the directory besides its `README.md` and `vendored.yaml`, the
project's own two files. What the directory holds is asked of git -- tracked
files and untracked files git would commit, so a stray run output is a finding before it
is staged and a gitignored `__pycache__` is not -- and walked from the filesystem only
where there is no index to ask.

**Re-pinning** is `--write`: from a clean upstream checkout at the new pin, after the
vendored files have been replaced with the new pin's bytes, it compares every vendored
file with the checkout's blob at that commit, byte for byte, and rewrites the manifest.
It refuses while local changes are recorded, because a re-pin must start from the
pristine copy (the README, "Re-pinning").

Usage, from `packing/`, each after `uv run --frozen --all-extras --group dev`:
    python -m devtools.check_vendored_evand
    python -m devtools.check_vendored_evand --write --checkout ../attic/evand-square-packing

It runs under the project interpreter (`except A, B:` parses on 3.14 only, `D-397`).
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqpack.yamlio import safe_load

REPO = Path(__file__).resolve().parents[2]
VENDORED = REPO / "vendor" / "evand-regularize"
MANIFEST_NAME = "vendored.yaml"
#: The provenance document: this project's, the directory's conventional readme.
DOCUMENT = "README.md"
#: This project's own files in the vendored directory. The manifest cannot list its own
#: digest, and the provenance document is ours to edit.
OWN_FILES = frozenset({DOCUMENT, MANIFEST_NAME})
#: What a patched or added script's header comment names, so a reader of the file finds
#: the record of the change.
HEADER_MARK = "vendor/evand-regularize/README.md"
FORMAT = "vendored-source-v1"
#: `replica` is a patch applied to a scratch replica only (`devtools.regularize_evand`), so
#: the vendored file stays the pinned bytes and the patch is checked to apply to them.
KINDS = ("modified", "added", "removed", "replica")
#: A patched or added file of these kinds carries a header comment pointing here.
COMMENTED_SUFFIXES = frozenset({".py", ".sh"})
HEADER_LINES = 20
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_HEX256 = re.compile(r"^[0-9a-f]{64}$")
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_BEAD = re.compile(r"^think-[a-z0-9]{4}$")
_HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")
#: Directories the fallback walk skips: interpreter caches, never content.
_SKIP = frozenset({"__pycache__", ".git"})

#: Written above the generated manifest, so `--write` reproduces the file it replaces.
HEADER = """\
# The manifest of vendor/evand-regularize: Evan Daniel's evand/square-packing, a subset
# copied byte for byte at one commit. README.md beside it is the prose: what each file
# is for, the credit, the licence, how a fork is recorded and how to re-pin.
#
# Checked by `python -m devtools.check_vendored_evand` from packing/ (edit tier), which
# also writes this file on a re-pin (`--write --checkout DIR`); edit `local_changes` by
# hand, never the pinned digests.
#
# Why SHA-256 here (OR-16): these bytes cross a real trust boundary -- they were
# downloaded from another party's repository. The expected value of each digest is the
# upstream blob at `source_commit`, which anyone can re-derive from the upstream
# repository without trusting this one. The failure it detects is an unrecorded edit,
# removal or addition in the vendored copy (a silent fork) or a manifest left stale by a
# re-pin. Nothing but that check reads these digests: no tool refuses to run the
# generator, and no result is invalidated, on a mismatch.
"""


class ManifestError(ValueError):
    """The manifest is not in the shape this check reads."""


class PatchError(ValueError):
    """A replica patch that does not apply exactly."""


@dataclass(frozen=True, slots=True)
class Pinned:
    """One upstream file at the pin."""

    path: str
    size: int
    sha256: str


@dataclass(frozen=True, slots=True)
class Change:
    """One reviewed local change to the vendored copy."""

    path: str
    kind: str
    day: str
    bead: str
    reason: str
    #: A `replica` change's unified diff, repository-relative; None for the other kinds.
    patch: str | None = None


@dataclass(frozen=True, slots=True)
class Manifest:
    source_url: str
    source_commit: str
    license_file: str
    files: dict[str, Pinned]
    changes: dict[str, Change]


# ---------------------------------------------------------------------------
# Reading the manifest
# ---------------------------------------------------------------------------


def _text(record: Mapping[str, Any], key: str, where: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        msg = f"{where}: `{key}` must be a non-empty string"
        raise ManifestError(msg)
    return value


def _relative(path: str, where: str) -> str:
    parts = path.split("/")
    if path.startswith("/") or "\\" in path or any(part in {"", ".", ".."} for part in parts):
        msg = f"{where}: `{path}` is not a plain relative POSIX path"
        raise ManifestError(msg)
    return path


def _pinned(entry: object, place: int) -> Pinned:
    where = f"files[{place}]"
    if not isinstance(entry, dict):
        msg = f"{where}: each file is a mapping"
        raise ManifestError(msg)
    record: dict[str, Any] = entry
    path = _relative(_text(record, "path", where), where)
    size = record.get("bytes")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        msg = f"{where} ({path}): `bytes` must be a non-negative integer"
        raise ManifestError(msg)
    sha256 = _text(record, "sha256", where)
    if not _HEX256.match(sha256):
        msg = f"{where} ({path}): `sha256` must be 64 lowercase hex digits"
        raise ManifestError(msg)
    if path in OWN_FILES:
        msg = f"{where}: {path} is this project's own file, not an upstream one"
        raise ManifestError(msg)
    return Pinned(path, size, sha256)


def _change(entry: object, place: int) -> Change:
    where = f"local_changes[{place}]"
    if not isinstance(entry, dict):
        msg = f"{where}: each local change is a mapping"
        raise ManifestError(msg)
    record: dict[str, Any] = entry
    path = _relative(_text(record, "path", where), where)
    kind = _text(record, "kind", where)
    if kind not in KINDS:
        msg = f"{where} ({path}): `kind` is one of {', '.join(KINDS)}, not {kind!r}"
        raise ManifestError(msg)
    day = str(record.get("date", ""))
    if not _DAY.match(day):
        msg = f"{where} ({path}): `date` must be YYYY-MM-DD"
        raise ManifestError(msg)
    bead = _text(record, "bead", where)
    if not _BEAD.match(bead):
        msg = f"{where} ({path}): `bead` must name the bead that tracks it (think-xxxx)"
        raise ManifestError(msg)
    patch = _relative(_text(record, "patch", where), where) if kind == "replica" else None
    return Change(path, kind, day, bead, _text(record, "reason", where), patch)


def parse_manifest(document: object) -> Manifest:
    """The manifest's fields, refused with a `ManifestError` naming what is wrong."""
    if not isinstance(document, dict):
        msg = "the manifest is a mapping"
        raise ManifestError(msg)
    record: dict[str, Any] = document
    if record.get("format") != FORMAT:
        msg = f"`format` must be {FORMAT!r}"
        raise ManifestError(msg)
    for key in ("source_url", "committed", "subject", "license", "copyright"):
        _text(record, key, "manifest")
    commit = _text(record, "source_commit", "manifest")
    if not _COMMIT.match(commit):
        msg = "`source_commit` must be the full 40-digit commit id"
        raise ManifestError(msg)
    if not _DAY.match(str(record.get("retrieved", ""))):
        msg = "`retrieved` must be YYYY-MM-DD"
        raise ManifestError(msg)
    entries = record.get("files")
    if not isinstance(entries, list) or not entries:
        msg = "`files` must be a non-empty list"
        raise ManifestError(msg)
    files: dict[str, Pinned] = {}
    for place, entry in enumerate(entries):
        pinned = _pinned(entry, place)
        if pinned.path in files:
            msg = f"files[{place}]: {pinned.path} is listed twice"
            raise ManifestError(msg)
        files[pinned.path] = pinned
    recorded = record.get("local_changes")
    if not isinstance(recorded, list):
        msg = "`local_changes` must be a list, `[]` when the copy is pristine"
        raise ManifestError(msg)
    changes: dict[str, Change] = {}
    for place, entry in enumerate(recorded):
        change = _change(entry, place)
        if change.path in changes:
            msg = f"local_changes[{place}]: {change.path} is recorded twice"
            raise ManifestError(msg)
        changes[change.path] = change
    license_file = _text(record, "license_file", "manifest")
    if license_file not in files:
        msg = f"`license_file` {license_file} is not among the pinned files"
        raise ManifestError(msg)
    return Manifest(
        _text(record, "source_url", "manifest"), commit, license_file, files, changes
    )


def load_manifest(path: Path) -> Manifest:
    return parse_manifest(safe_load(path.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# What the directory holds
# ---------------------------------------------------------------------------


def _git_listed(directory: Path) -> set[str] | None:
    """Tracked and untracked-but-unignored files under `directory`, or None with no index.

    Asked from the work tree's top so that a directory git ignores as a whole answers
    `None` (no index speaks for it) rather than an empty listing that would read as every
    file missing.
    """
    try:
        top = subprocess.run(
            ("git", "-C", str(directory), "rev-parse", "--show-toplevel"),
            check=True,
            capture_output=True,
        ).stdout
    except OSError, subprocess.CalledProcessError:
        return None
    root = Path(os.fsdecode(top).strip()).resolve()
    inside = directory.resolve().relative_to(root).as_posix()
    ignored = subprocess.run(
        ("git", "-C", str(root), "check-ignore", "-q", "--", inside),
        capture_output=True,
        check=False,
    )
    if inside != "." and ignored.returncode == 0:
        return None
    listed = subprocess.run(
        (
            "git",
            "-C",
            str(root),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            inside,
        ),
        check=True,
        capture_output=True,
    ).stdout
    prefix = "" if inside == "." else inside + "/"
    names = (os.fsdecode(name) for name in listed.split(b"\0") if name)
    return {name.removeprefix(prefix) for name in names if (root / name).is_file()}


def _walked(directory: Path) -> set[str]:
    found: set[str] = set()
    for here, names, files in os.walk(directory):
        names[:] = [name for name in names if name not in _SKIP]
        found.update(
            (Path(here) / name).relative_to(directory).as_posix()
            for name in files
            if not name.endswith(".pyc")
        )
    return found


def present_files(directory: Path) -> set[str]:
    """Every file `directory` holds, relative to it: git's answer, else a walk."""
    listed = _git_listed(directory)
    return _walked(directory) if listed is None else listed


# ---------------------------------------------------------------------------
# Replica patches
# ---------------------------------------------------------------------------


def _hunks(diff: str) -> list[tuple[str, str]]:
    """Each hunk of a unified diff as its text before and after; lines outside hunks are
    the diff's own prose and headers. A hunk is read by the line counts its header gives."""
    lines = diff.splitlines(keepends=True)
    hunks: list[tuple[str, str]] = []
    place = 0
    while place < len(lines):
        header = _HUNK.match(lines[place])
        place += 1
        if header is None:
            continue
        old, new = int(header.group(1) or 1), int(header.group(2) or 1)
        before: list[str] = []
        after: list[str] = []
        while len(before) < old or len(after) < new:
            if place == len(lines):
                msg = "a hunk ends before the line counts its header gives"
                raise PatchError(msg)
            line = lines[place]
            place += 1
            # An empty context line may have lost its leading space to an editor.
            tag, body = (" ", line) if line in {"\n", "\r\n"} else (line[:1], line[1:])
            if tag in {" ", "-"}:
                before.append(body)
            if tag in {" ", "+"}:
                after.append(body)
            if tag not in {" ", "-", "+", "\\"}:
                msg = f"a line in a hunk starts with neither ' ', '-' nor '+': {line!r}"
                raise PatchError(msg)
        hunks.append(("".join(before), "".join(after)))
    if not hunks:
        msg = "the patch has no hunk"
        raise PatchError(msg)
    return hunks


def apply_patch(text: str, diff: str) -> str:
    """`text` with each hunk of the unified `diff` applied by its exact text before.

    Line numbers are not trusted and nothing is fuzzed: each hunk's context and removed
    lines must occur exactly once in the text as the hunks before it left it, so a patch
    that no longer fits the bytes it was written against is refused, never half applied.
    """
    for before, after in _hunks(diff):
        found = text.count(before)
        if found != 1:
            where = "is not in the text" if found == 0 else f"occurs {found} times"
            first = before.splitlines()[0] if before else ""
            msg = f"the hunk beginning {first.strip()!r} {where}"
            raise PatchError(msg)
        text = text.replace(before, after)
    return text


def project_root(directory: Path) -> Path:
    """The repository that holds a vendored directory at `vendor/<name>`."""
    return directory.resolve().parents[1]


def _replica_problems(directory: Path, path: str, change: Change) -> list[str]:
    """A replica patch's file is there and still applies to the vendored file."""
    if change.patch is None:  # parse_manifest gives every replica change its patch
        return [f"{path}: a replica change names no patch"]
    patch = project_root(directory) / change.patch
    if not patch.is_file():
        return [f"{path}: its replica patch {change.patch} is missing"]
    try:
        apply_patch(
            (directory / path).read_text(encoding="utf-8"), patch.read_text(encoding="utf-8")
        )
    except PatchError as refusal:
        return [f"{path}: its replica patch {change.patch} does not apply: {refusal}"]
    return []


# ---------------------------------------------------------------------------
# The check
# ---------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _names_vendored(path: Path) -> bool:
    with path.open(encoding="utf-8", errors="replace") as stream:
        head = [stream.readline() for _ in range(HEADER_LINES)]
    return any(HEADER_MARK in line for line in head)


def _pinned_problems(directory: Path, manifest: Manifest, present: set[str]) -> list[str]:
    problems: list[str] = []
    for path, pinned in sorted(manifest.files.items()):
        change = manifest.changes.get(path)
        where = directory / path
        if change is not None and change.kind == "added":
            problems.append(f"{path}: recorded as added, but upstream has it at the pin")
        elif change is not None and change.kind == "removed":
            if path in present:
                problems.append(f"{path}: recorded as removed, but it is still here")
        elif path not in present:
            problems.append(f"{path}: pinned, but missing from the vendored copy")
        elif change is None or change.kind == "replica":
            # A replica patch changes only the scratch replica: the file here is pristine.
            if change is not None:
                problems += _replica_problems(directory, path, change)
            size = where.stat().st_size
            if size != pinned.size:
                problems.append(
                    f"{path}: {size} bytes, not the pinned {pinned.size}; an edit to vendored "
                    "code is a local change, recorded in vendored.yaml (README.md, Forking)"
                )
            elif _sha256(where) != pinned.sha256:
                problems.append(
                    f"{path}: not the pinned bytes; an edit to vendored code is a local "
                    "change, recorded in vendored.yaml (README.md, Forking)"
                )
        elif _sha256(where) == pinned.sha256:
            problems.append(f"{path}: recorded as modified, but it is still the pinned bytes")
        elif where.suffix in COMMENTED_SUFFIXES and not _names_vendored(where):
            problems.append(
                f"{path}: modified, but its first {HEADER_LINES} lines carry no comment "
                f"naming {HEADER_MARK}"
            )
    return problems


def check(directory: Path, manifest: Manifest, present: Iterable[str]) -> list[str]:
    """Every way the vendored copy at `directory` disagrees with `manifest`."""
    held = set(present)
    problems = [
        f"{name}: this project's file is missing from the vendored directory"
        for name in sorted(OWN_FILES - held)
    ]
    if manifest.license_file in manifest.changes:
        problems.append(
            f"{manifest.license_file}: the licence file is never a local change; the MIT "
            "grant requires its notice with every copy"
        )
    problems += _pinned_problems(directory, manifest, held)
    for path, change in sorted(manifest.changes.items()):
        if path in manifest.files:
            continue
        if change.kind != "added":
            problems.append(f"{path}: recorded as {change.kind}, but upstream has no such file")
        elif path not in held:
            problems.append(f"{path}: recorded as added, but it is not here")
        elif (directory / path).suffix in COMMENTED_SUFFIXES and not _names_vendored(
            directory / path
        ):
            problems.append(
                f"{path}: added, but its first {HEADER_LINES} lines carry no comment "
                f"naming {HEADER_MARK}"
            )
    document = directory / DOCUMENT
    prose = document.read_text(encoding="utf-8") if document.is_file() else ""
    problems += [
        f"{path}: recorded as a local change, but README.md's Local Changes does not name it"
        for path in sorted(manifest.changes)
        if path not in prose
    ]
    problems += [
        f"{path}: its replica patch {Path(change.patch).name} is not named in README.md"
        for path, change in sorted(manifest.changes.items())
        if change.patch is not None and Path(change.patch).name not in prose
    ]
    expected = set(manifest.files) | set(manifest.changes) | OWN_FILES
    problems += [
        f"{path}: not in the manifest; vendored code changes only by a recorded local "
        "change, and run outputs belong in a scratch directory, not here"
        for path in sorted(held - expected)
    ]
    return problems


# ---------------------------------------------------------------------------
# Re-pinning
# ---------------------------------------------------------------------------


def _git(checkout: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ("git", "-C", str(checkout), *arguments), check=True, capture_output=True
    ).stdout


def _quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def render_manifest(
    *, metadata: Mapping[str, str], files: Sequence[Pinned], retrieved: str
) -> str:
    """The manifest's text: `HEADER`, the pin, and one flow mapping per file."""
    lines = [
        HEADER.rstrip("\n"),
        "",
        f"format: {FORMAT}",
        f"source_url: {metadata['source_url']}",
        f"source_commit: {metadata['source_commit']}",
        f"git_tree: {metadata['git_tree']}",
        f"committed: {_quoted(metadata['committed'])}",
        f"subject: {_quoted(metadata['subject'])}",
        f"retrieved: {_quoted(retrieved)}",
        "license: MIT",
        "license_file: LICENSE",
        f"copyright: {_quoted(metadata['copyright'])}",
        "",
        "# Reviewed patches to the vendored copy, each {path, kind: modified | added |",
        "# removed | replica, date, bead, reason}, and a replica patch's `patch` file. A",
        "# modified file keeps its pinned entry below, so the pristine bytes stay",
        "# reconstructible from the upstream pin; a replica patch leaves them as they are.",
        "local_changes: []",
        "",
        f"# {len(files)} files, {sum(item.size for item in files)} bytes.",
        "files:",
    ]
    lines.extend(
        f"  - {{path: {item.path}, bytes: {item.size}, sha256: {item.sha256}}}"
        for item in files
    )
    return "\n".join(lines) + "\n"


def repin(directory: Path, checkout: Path, *, commit: str, retrieved: str) -> str:
    """The manifest for `directory` as a copy of `checkout` at `commit`, or a refusal.

    Each vendored file is compared byte for byte with the checkout's blob at the commit,
    read from the checkout's object store, so a modified working tree there is harmless.
    """
    manifest_path = directory / MANIFEST_NAME
    if manifest_path.is_file() and load_manifest(manifest_path).changes:
        msg = (
            "local changes are recorded; restore the pristine copy, re-pin, then re-apply "
            "each change and record it again (README.md, Re-pinning)"
        )
        raise ManifestError(msg)
    fields = (
        _git(checkout, "log", "-1", "--format=%H%n%T%n%cI%n%s", commit).decode().split("\n")
    )
    url = _git(checkout, "remote", "get-url", "origin").decode().strip().removesuffix(".git")
    licence = (directory / "LICENSE").read_text(encoding="utf-8")
    holder = next(line for line in licence.splitlines() if line.startswith("Copyright"))
    metadata = {
        "source_url": url,
        "source_commit": fields[0],
        "git_tree": fields[1],
        "committed": fields[2],
        "subject": fields[3],
        "copyright": holder,
    }
    pinned: list[Pinned] = []
    mismatched: list[str] = []
    for path in sorted(present_files(directory) - OWN_FILES):
        data = (directory / path).read_bytes()
        try:
            blob = _git(checkout, "cat-file", "blob", f"{fields[0]}:{path}")
        except subprocess.CalledProcessError:
            mismatched.append(f"{path}: upstream has no such file at {fields[0][:12]}")
            continue
        if blob != data:
            mismatched.append(f"{path}: not upstream's bytes at {fields[0][:12]}")
            continue
        pinned.append(Pinned(path, len(data), hashlib.sha256(data).hexdigest()))
    if mismatched:
        raise ManifestError("; ".join(mismatched))
    return render_manifest(metadata=metadata, files=pinned, retrieved=retrieved)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n", 1)[0])
    parser.add_argument("--directory", type=Path, default=VENDORED)
    parser.add_argument(
        "--write", action="store_true", help="rewrite the manifest from an upstream checkout"
    )
    parser.add_argument("--checkout", type=Path, help="upstream checkout, for --write")
    parser.add_argument("--commit", default="HEAD", help="the pin, for --write")
    parser.add_argument(
        "--retrieved",
        default=datetime.now(tz=UTC).date().isoformat(),
        help="retrieval date, for --write",
    )
    args = parser.parse_args(argv)
    directory: Path = args.directory
    try:
        if args.write:
            if args.checkout is None:
                parser.error("--write needs --checkout")
            text = repin(directory, args.checkout, commit=args.commit, retrieved=args.retrieved)
            (directory / MANIFEST_NAME).write_text(text, encoding="utf-8")
            written = load_manifest(directory / MANIFEST_NAME)
            print(
                f"wrote {MANIFEST_NAME}: {len(written.files)} files at {written.source_commit}"
            )
            return 0
        manifest = load_manifest(directory / MANIFEST_NAME)
    except ManifestError as refusal:
        print(f"check_vendored_evand: {refusal}", file=sys.stderr)
        return 1
    problems = check(directory, manifest, present_files(directory))
    for problem in problems:
        print(f"check_vendored_evand: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(
        f"vendored copy check passed: {len(manifest.files)} files match "
        f"{manifest.source_url}@{manifest.source_commit[:7]}, "
        f"{len(manifest.changes)} local change(s) recorded"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
