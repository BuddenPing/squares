"""The launch history reaches both reader surfaces and the publication scope."""

from __future__ import annotations

import copy
import re
from fnmatch import fnmatchcase

import pytest

from devtools import (
    check_published_site,
    pages_scope,
    render_changelog,
    render_overview,
    site_documents,
)
from devtools.pages_scope import REPO
from tests import site_renders


@pytest.fixture(scope="module")
def views() -> tuple[dict, str, str, str, str]:
    document = render_changelog.load()
    return (
        document,
        site_renders.html("news.html"),
        render_changelog.render(document),
        site_renders.html("about.html"),
        site_renders.html("index.html"),
    )


def test_news_contains_the_same_launch_history_as_github(
    views: tuple[dict, str, str, str, str],
) -> None:
    document, news, github, _about, _home = views
    history = news[news.index('id="changelog"') :]
    for entry in document["entries"]:
        anchor = render_changelog.entry_anchor(entry["id"])
        assert f'id="{anchor}"' in history
        assert f'id="{anchor}"' in github
        for number in entry["pull_requests"]:
            target = f"{document['repository']}/pull/{number}"
            assert target in history
            assert target in github
        for artifact in entry.get("artifacts", []):
            assert artifact["target"] in history
            assert artifact["target"] in github


def test_a_yaml_only_history_change_selects_and_deploys_news() -> None:
    workflow = pages_scope.load_workflow()
    changed = "packing/site-changelog.yaml"
    decisions = pages_scope.decide([changed], pages_scope.declared_inputs())
    assert any(item.half == "overview" and item.in_scope for item in decisions)
    push = workflow["on"]["push"]
    assert any(fnmatchcase(changed, pattern) for pattern in push["paths"])
    assert REPO / changed in render_overview.RENDER_INPUTS


def test_repository_changelog_links_land_on_news() -> None:
    assert site_documents.RECORD_PAGES["CHANGELOG.md"] == "news.html#changelog"


def test_publication_audit_refuses_a_missing_launch_link(
    views: tuple[dict, str, str, str, str],
) -> None:
    document, news, _github, _about, _home = views
    assert all(passed for passed, _line in check_published_site.changelog_checks(news))
    target = next(
        artifact["target"]
        for entry in document["entries"]
        for artifact in entry.get("artifacts", [])
    )
    damaged = news.replace(target, "https://example.com/missing")
    assert not all(passed for passed, _line in check_published_site.changelog_checks(damaged))


def test_publication_audit_accepts_the_renderers_encoded_artifact_destinations(
    views: tuple[dict, str, str, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    document = copy.deepcopy(views[0])
    artifact = next(
        artifact for entry in document["entries"] for artifact in entry.get("artifacts", [])
    )
    artifact["target"] += "#proof(1)"
    render_changelog.validate(document)
    monkeypatch.setattr(render_changelog, "load", lambda: document)
    news = render_overview.news_page().html
    assert "#proof%281%29" in news
    assert all(passed for passed, _line in check_published_site.changelog_checks(news))


def test_news_groups_days_and_home_previews_only_the_first_two_items(
    views: tuple[dict, str, str, str, str],
) -> None:
    document, news, _github, about, home = views
    ordered = render_changelog.ordered_entries(document)
    assert re.findall(r'data-news-entry="([^"]+)"', news) == [e["id"] for e in ordered]
    assert re.findall(r'data-news-day="([^"]+)"', news) == sorted(
        {e["date"] for e in ordered}, reverse=True
    )
    assert re.findall(r'data-news-entry="([^"]+)"', home) == [e["id"] for e in ordered[:2]]
    assert '<a class="site-action" href="news.html">All news' in home
    assert 'id="news" class="site-title">News' in news
    assert 'data-page="news" aria-current="page" href="news.html"' in news
    assert 'href="news.html"' in about
    assert "data-news-entry=" not in about
    assert 'class="site-news-day"' not in about
    for entry in ordered:
        anchor = render_changelog.entry_anchor(entry["id"])
        assert f'id="{anchor}" href="news.html#{anchor}" data-news-target' in about
        if entry in ordered[:2]:
            assert f'href="news.html#{anchor}"' in home


def test_news_preview_keeps_semantic_math_once_and_skips_hidden_subtrees() -> None:
    source = render_changelog._prose(
        "Verified **bound** $s(11) \\ge 381/100$.", destination="site"
    )
    preview = " ".join("".join(render_changelog._NewsPreviewText(source).parts).split())
    assert preview == "Verified bound s(11)≥381/100."
    nested = (
        '<p>Before <span aria-hidden="true">visual<annotation>nested<br/>'
        "<span>hidden</span></annotation><span>still hidden</span></span>"
        "<math><mrow><mi>x</mi><mo>≥</mo><mn>1</mn></mrow>"
        "<annotation>duplicate</annotation><annotation-xml>"
        "<span>duplicate again</span></annotation-xml></math><br/>after<br>end.</p>"
    )
    clean = " ".join("".join(render_changelog._NewsPreviewText(nested).parts).split())
    assert clean == "Before x≥1 after end."
