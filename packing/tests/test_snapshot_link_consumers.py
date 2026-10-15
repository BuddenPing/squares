"""A pruned file returns to a worker only for a reader a registered control runs there.

The copy-back follows the links a registered control resolves inside a worker -- the
campaign record's, `README.md`'s and `SYNOPSIS.md`'s -- and the paths the record declares
structurally: the results register's evidence and each defect's `recorded_in`. Every
other document's links are prose for a reader outside the worker (think-b6ir).
"""

import re
import subprocess
from pathlib import Path

import pytest

from cases.kingbird29 import layout as kingbird_layout
from devtools import check_gate_budgets, check_readme, check_synopsis
from devtools import run_negative_controls as controls
from devtools.check_pr_wall import load_walls
from sqpack.campaign import ledger
from sqpack.yamlio import safe_load
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


def test_the_link_checked_documents_are_the_ones_registered_controls_check() -> None:
    """The rule's documents are the checkers' own, and registered controls run them."""
    checked = {
        (controls.REPO / document).resolve() for document in controls.LINK_CHECKED_DOCUMENTS
    }
    assert checked == {check_readme.README.resolve(), check_synopsis.SYNOPSIS.resolve()}
    assert ledger.ROOT.resolve() == (controls.ROOT / "campaign").resolve()
    spec = safe_load((controls.ROOT / "devtools/controls.yaml").read_text(encoding="utf-8"))
    commands = {control["run"] for control in spec["controls"]}
    for checker in (
        "devtools.check_readme",
        "devtools.check_synopsis",
        "campaign.ledger check",
    ):
        assert any(checker in command for command in commands), checker


def test_the_wall_workflows_are_declared_worker_inputs() -> None:
    """`check_gate_budgets` reads each wall's workflow; no review's link brings it now."""
    read = {
        check_gate_budgets.PULL_REQUEST_WORKFLOW,
        *(
            controls.REPO / wall.file
            for wall in load_walls(check_gate_budgets.REGISTER).workflows
        ),
    }
    assert read <= set(controls.COPY_SEPARATELY)
    assert set(controls.wall_workflows()) == read


#: The verifier-registry paths a review's link used to bring into every worker: the ones
#: `validate_schemas` found missing there once the copy-back stopped following reviews.
REVIEW_LINKED_VERIFIER_PATHS = (
    "packing/resources/web/n11-optimality-2026-09-29/source/VERIFY.py",
    (
        "packing/resources/web/queuingtheorydotcom-n11-lean-2026-10-06/receipts/lean/"
        "AuditN11Statement.lean"
    ),
    "packing/resources/web/wand125-closed-form-2026-10-14/review/README.md",
)


def test_the_readers_the_baselines_found_are_declared_worker_inputs() -> None:
    """Each explicit input names a reader that still reads it, or the entry is stale."""
    carried = set(controls.COPY_SEPARATELY)
    assert controls.ROOT / kingbird_layout.DEFAULT_SOURCE in carried
    registry = safe_load(
        (controls.ROOT / "frontier/verifiers.yaml").read_text(encoding="utf-8")
    )
    # The fields `verifier_registry.problems` requires to exist.
    named = {
        path
        for record in registry["verifiers"]
        for path in (
            *record.get("source", []),
            *(version["path"] for version in record.get("versions", []) if "path" in version),
            *([record["independence_record"]] if "independence_record" in record else []),
        )
    }
    for path in REVIEW_LINKED_VERIFIER_PATHS:
        assert path in named, path
        assert controls.REPO / path in carried, path


def test_only_the_links_a_control_checks_are_rescued(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A review's or a guide's links leave the worker; checked links and declarations stay."""
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
    paper = archive / "paper.md"
    paper.write_text("# A paper\n")
    review = repo / "docs/review.md"
    review.parent.mkdir()
    review.write_text(
        "[observation](../packing/benchmarks/math-startup/runs/historical/reference.pdf)\n"
        "[scientific input](../packing/resources/certificate.json)\n"
    )
    guide = repo / "development.md"
    guide.write_text("[paper](packing/resources/paper.md#a-paper)\n")
    readme, synopsis = repo / "README.md", repo / "SYNOPSIS.md"
    readme.write_text("[review](docs/review.md)\n")
    synopsis.write_text("Synopsis\n")
    campaign = packing / "campaign/record.md"
    campaign.parent.mkdir()
    campaign.write_text("Campaign\n")
    register = packing / "frontier/results.yaml"
    register.parent.mkdir()
    register.write_text("results: []\n")
    defects = packing / "defects.yaml"
    defects.write_text("defects: []\n")
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
    monkeypatch.setattr(controls, "ROOT_DOCUMENTS", (readme, synopsis, guide, review.parent))
    monkeypatch.setattr(controls, "COPY_SEPARATELY", ())
    monkeypatch.setattr(controls, "LINK_BACK", ())

    # A checked link to the review checks that document, not its outgoing links, and no
    # control link-checks the guide: both documents reach the worker, their targets not.
    assert controls.snapshot_pruned_targets() == []
    index_fixture_source(repo)
    tree = tmp_path / "worker"
    controls.clone_tree(tree)
    assert (tree / review.relative_to(repo)).read_bytes() == review.read_bytes()
    assert (tree / guide.relative_to(repo)).read_bytes() == guide.read_bytes()
    for omitted in (output, scientific_input, paper):
        assert not (tree / omitted.relative_to(repo)).exists()
    git_tree = subprocess.run(
        ["git", "-C", str(repo), "write-tree"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    assert controls.snapshot_git_source_bytes(git_tree) == controls.snapshot_source_bytes()

    # The same targets linked from a document a control checks return, fragment or not.
    for document, relative in (
        (readme, "packing/resources/certificate.json"),
        (synopsis, "packing/resources/certificate.json#digest"),
        (campaign, "../resources/certificate.json#digest"),
    ):
        original = document.read_text()
        document.write_text(original + f"[deciding input]({relative})\n")
        assert controls.snapshot_pruned_targets() == [scientific_input]
        document.write_text(original)

    # Structural declarations are independent of prose: the results register's evidence
    # and the defect log's `recorded_in`, which `validate_schemas` requires to exist.
    for declaration in (
        "artifacts: [packing/resources/certificate.json]",
        "controls: [packing/resources/certificate.json]",
        "reviews: [{path: packing/resources/certificate.json}]",
    ):
        register.write_text(f"results:\n- {declaration}\n")
        assert controls.snapshot_pruned_targets() == [scientific_input]
    register.write_text("results: []\n")
    defects.write_text("defects:\n- recorded_in: packing/resources/paper.md\n")
    assert controls.snapshot_pruned_targets() == [paper]
    index_fixture_source(repo)
    git_tree = subprocess.run(
        ["git", "-C", str(repo), "write-tree"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()
    assert controls.snapshot_git_source_bytes(git_tree) == controls.snapshot_source_bytes()
    defects.write_text("defects: []\n")
    monkeypatch.setattr(controls, "COPY_SEPARATELY", (output,))
    assert output in controls.snapshot_copy_targets()
    monkeypatch.setattr(controls, "COPY_SEPARATELY", ())

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

    # Neither of the review's directory links is followed in a worker.
    assert controls.linked_pruned_directories() == []
    index_fixture_source(repo)
    tree = tmp_path / "worker"
    controls.clone_tree(tree)
    assert not (tree / observations.relative_to(repo)).exists()
    assert not (tree / bundle.relative_to(repo)).exists()

    for document, prefix in ((readme, "packing/"), (synopsis, "packing/"), (campaign, "../")):
        original = document.read_text()
        document.write_text(
            original
            + f"[observations]({prefix}benchmarks/math-startup/runs/historical)\n"
            + f"[bundle]({prefix}resources/bundle#certificate)\n"
        )
        assert controls.linked_pruned_directories() == [observations, bundle]
        document.write_text(original)
    readme.write_text("[bundle](packing/resources/bundle)\n")
    index_fixture_source(repo)
    linked_tree = tmp_path / "linked-worker"
    controls.clone_tree(linked_tree)
    landed = linked_tree / bundle.relative_to(repo)
    assert landed.is_dir()
    assert not any(landed.iterdir())
