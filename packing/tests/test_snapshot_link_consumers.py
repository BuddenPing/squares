"""Historical browser output needs a worker consumer before link rescue copies it."""

import re
import subprocess
from pathlib import Path

import pytest

from devtools import run_negative_controls as controls
from tests.test_negative_controls import index_fixture_source

#: How `sqpack.campaign.ledger.dead_links` reads a campaign link: everything up to the
#: closing parenthesis, resolved by its path before any `#`.
LEDGER_LINK = re.compile(r"\]\(([^)#][^)]*)\)")


def test_fragment_links_rescue_their_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`[proof](review.md#section)` needs `review.md` as much as a bare link does."""
    repo = tmp_path / "source"
    packing = repo / "packing"
    archive = packing / "resources"
    review = archive / "original_review/review.md"
    review.parent.mkdir(parents=True)
    review.write_text("# Seven rows close the support\n")
    bundle = archive / "bundle"
    bundle.mkdir()
    (bundle / "certificate.json").write_bytes(b"deciding scientific input")
    campaign = packing / "campaign/X-001-cover.md"
    campaign.parent.mkdir()
    campaign.write_text(
        "[support proof](../resources/original_review/review.md#seven-rows-close-the-support)\n"
        "[bundle](../resources/bundle#readme)\n"
        "[this document](#cover)\n"
    )
    register = packing / "frontier/results.yaml"
    register.parent.mkdir()
    register.write_text("results: []\n")
    monkeypatch.setattr(controls, "REPO", repo)
    monkeypatch.setattr(controls, "ROOT", packing)
    monkeypatch.setattr(controls, "HERE", Path("packing"))
    monkeypatch.setattr(controls, "PRUNE", frozenset({archive}))
    monkeypatch.setattr(controls, "DESCEND", frozenset())
    monkeypatch.setattr(controls, "LINKED_PRUNE_ROOTS", (archive,))
    monkeypatch.setattr(controls, "ROOT_DOCUMENTS", ())
    monkeypatch.setattr(controls, "COPY_SEPARATELY", ())
    monkeypatch.setattr(controls, "LINK_BACK", ())
    monkeypatch.setattr(controls, "root_files", lambda: ())

    assert controls.INLINE_LINK.findall(campaign.read_text()) == [
        "../resources/original_review/review.md",
        "../resources/bundle",
    ]
    assert controls.snapshot_pruned_targets() == [review]
    assert controls.linked_pruned_directories() == [bundle]
    index_fixture_source(repo)
    tree = tmp_path / "worker"
    controls.clone_tree(tree)
    assert (tree / review.relative_to(repo)).read_bytes() == review.read_bytes()
    assert (tree / bundle.relative_to(repo)).is_dir()


def test_every_pruned_target_the_ledger_resolves_reaches_a_worker() -> None:
    """The copier reads campaign links the way `ledger check` does (think-wzmf).

    The ledger stats every relative link's path before its `#`. A target under a pruned
    root that the copier misses is a dead link in every worker, and the 35 controls that
    drive `ledger check` would report it in place of the refusal each one rehearses. The
    original n11 review was that case, linked from campaign Markdown only with fragments.
    """
    roots = frozenset(controls.LINKED_PRUNE_ROOTS)
    files = set(controls.snapshot_pruned_targets())
    directories = set(controls.linked_pruned_directories())
    missing = []
    for document in sorted((controls.ROOT / "campaign").rglob("*.md")):
        for target in LEDGER_LINK.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (document.parent / target.split("#")[0]).resolve()
            if not resolved.exists() or not controls.in_pruned_roots(resolved, roots):
                continue
            if resolved not in (files if resolved.is_file() else directories):
                missing.append(f"{document.relative_to(controls.REPO)} -> {target}")
    assert not missing


def test_operational_links_preserve_checked_consumers_and_scientific_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "source"
    packing = repo / "packing"
    runs = packing / "benchmarks/math-startup/runs"
    output = runs / "historical/reference.pdf"
    output.parent.mkdir(parents=True)
    output.write_bytes(b"retained browser observation")
    archive = packing / "resources"
    scientific_input = archive / "certificate.json"
    archive.mkdir()
    scientific_input.write_bytes(b"deciding scientific input")
    review = repo / "docs/review.md"
    review.parent.mkdir()
    review.write_text(
        "[observation](../packing/benchmarks/math-startup/runs/historical/reference.pdf)\n"
        "[scientific input](../packing/resources/certificate.json)\n"
    )
    readme, synopsis = repo / "README.md", repo / "SYNOPSIS.md"
    readme.write_text("[review](docs/review.md)\n")
    synopsis.write_text("Synopsis\n")
    campaign = packing / "campaign/record.md"
    campaign.parent.mkdir()
    campaign.write_text("Campaign\n")
    register = packing / "frontier/results.yaml"
    register.parent.mkdir()
    register.write_text("results: []\n")
    monkeypatch.setattr(controls, "REPO", repo)
    monkeypatch.setattr(controls, "ROOT", packing)
    monkeypatch.setattr(controls, "HERE", Path("packing"))
    monkeypatch.setattr(controls, "PRUNE", frozenset({runs, archive}))
    monkeypatch.setattr(
        controls,
        "DESCEND",
        frozenset({packing / "benchmarks", packing / "benchmarks/math-startup"}),
    )
    monkeypatch.setattr(controls, "LINKED_PRUNE_ROOTS", (runs, archive))
    monkeypatch.setattr(controls, "ROOT_DOCUMENTS", (readme, synopsis, review.parent))
    monkeypatch.setattr(controls, "COPY_SEPARATELY", ())
    monkeypatch.setattr(controls, "LINK_BACK", ())

    # A checked link to the review checks that document, not its outgoing links.
    assert controls.snapshot_pruned_targets() == [scientific_input]
    index_fixture_source(repo)
    tree = tmp_path / "worker"
    controls.clone_tree(tree)
    assert not (tree / output.relative_to(repo)).exists()
    copied_input = tree / scientific_input.relative_to(repo)
    assert copied_input.read_bytes() == scientific_input.read_bytes()
    git_tree = subprocess.run(
        ["git", "-C", str(repo), "write-tree"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    assert controls.snapshot_git_source_bytes(git_tree) == controls.snapshot_source_bytes()

    for document, relative in (
        (readme, "packing/benchmarks/math-startup/runs/historical/reference.pdf"),
        (synopsis, "packing/benchmarks/math-startup/runs/historical/reference.pdf"),
        (campaign, "../benchmarks/math-startup/runs/historical/reference.pdf"),
    ):
        original = document.read_text()
        document.write_text(original + f"[observed input]({relative})\n")
        assert controls.snapshot_pruned_targets() == [output, scientific_input]
        document.write_text(original)

    # Structural result registration and explicit custody remain independent of prose.
    for field in ("artifacts", "controls", "reviews"):
        declaration = (
            "reviews: [{path: packing/benchmarks/math-startup/runs/historical/reference.pdf}]"
            if field == "reviews"
            else f"{field}: [packing/benchmarks/math-startup/runs/historical/reference.pdf]"
        )
        register.write_text(f"results:\n- {declaration}\n")
        assert controls.snapshot_pruned_targets() == [output, scientific_input]
    register.write_text("results: []\n")
    monkeypatch.setattr(controls, "COPY_SEPARATELY", (output,))
    assert output in controls.snapshot_copy_targets()

    # Rescued evidence remains a private mutable copy, never a link into custody.
    readme.write_text(
        "[observed input](packing/benchmarks/math-startup/runs/historical/reference.pdf)\n"
    )
    index_fixture_source(repo)
    rescued_tree = tmp_path / "rescued-worker"
    controls.clone_tree(rescued_tree)
    copied = rescued_tree / output.relative_to(repo)
    assert not copied.is_symlink()
    assert copied.read_bytes() == output.read_bytes()
    copied.write_bytes(b"corrupted observation")
    assert output.read_bytes() == b"retained browser observation"


def test_linked_directories_follow_the_same_checked_consumer_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A linked pruned directory is recreated empty only for a link a worker checks."""
    repo = tmp_path / "source"
    packing = repo / "packing"
    runs = packing / "benchmarks/math-startup/runs"
    observations = runs / "historical"
    observations.mkdir(parents=True)
    (observations / "reference.pdf").write_bytes(b"retained browser observation")
    archive = packing / "resources"
    bundle = archive / "bundle"
    bundle.mkdir(parents=True)
    (bundle / "certificate.json").write_bytes(b"deciding scientific input")
    review = repo / "docs/review.md"
    review.parent.mkdir()
    review.write_text(
        "[observations](../packing/benchmarks/math-startup/runs/historical)\n"
        "[bundle](../packing/resources/bundle)\n"
    )
    readme, synopsis = repo / "README.md", repo / "SYNOPSIS.md"
    readme.write_text("[review](docs/review.md)\n")
    synopsis.write_text("Synopsis\n")
    campaign = packing / "campaign/record.md"
    campaign.parent.mkdir()
    campaign.write_text("Campaign\n")
    register = packing / "frontier/results.yaml"
    register.parent.mkdir()
    register.write_text("results: []\n")
    monkeypatch.setattr(controls, "REPO", repo)
    monkeypatch.setattr(controls, "ROOT", packing)
    monkeypatch.setattr(controls, "HERE", Path("packing"))
    monkeypatch.setattr(controls, "PRUNE", frozenset({runs, archive}))
    monkeypatch.setattr(
        controls,
        "DESCEND",
        frozenset({packing / "benchmarks", packing / "benchmarks/math-startup"}),
    )
    monkeypatch.setattr(controls, "LINKED_PRUNE_ROOTS", (runs, archive))
    monkeypatch.setattr(controls, "ROOT_DOCUMENTS", (readme, synopsis, review.parent))
    monkeypatch.setattr(controls, "COPY_SEPARATELY", ())
    monkeypatch.setattr(controls, "LINK_BACK", ())

    # The review's directory link to browser output is not followed in a worker; its
    # link to the archive keeps the custody the file rule keeps.
    assert controls.linked_pruned_directories() == [bundle]
    index_fixture_source(repo)
    tree = tmp_path / "worker"
    controls.clone_tree(tree)
    assert not (tree / observations.relative_to(repo)).exists()
    landed = tree / bundle.relative_to(repo)
    assert landed.is_dir()
    assert not any(landed.iterdir())

    for document, relative in (
        (readme, "packing/benchmarks/math-startup/runs/historical"),
        (synopsis, "packing/benchmarks/math-startup/runs/historical"),
        (campaign, "../benchmarks/math-startup/runs/historical"),
    ):
        original = document.read_text()
        document.write_text(original + f"[observations]({relative})\n")
        assert controls.linked_pruned_directories() == [observations, bundle]
        document.write_text(original)
