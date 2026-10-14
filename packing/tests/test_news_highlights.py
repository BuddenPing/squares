"""Homepage News selects existing S5 results without changing project history."""

from __future__ import annotations

import copy
import re
from dataclasses import replace

import pytest

from devtools import news_highlights, overview_data, overview_sections, render_changelog
from tests import site_renders


@pytest.fixture(scope="module")
def overview() -> overview_data.Overview:
    return site_renders.overview()


def _candidate(
    original: overview_data.Result, result_id: str, day: str, score: int = 5
) -> overview_data.Result:
    record = copy.deepcopy(original.record)
    record["id"] = result_id
    record["attribution"]["published"] = day
    record["significance"]["score"] = score
    return replace(original, record=record)


def test_selection_uses_only_s5_and_the_existing_date_and_id_order(
    overview: overview_data.Overview,
) -> None:
    original = next(result for result in overview.results if result.id == "T-154")
    candidates = [
        _candidate(original, "T-001", "2026-10-12"),
        _candidate(original, "T-999", "2026-10-13", 4),
        _candidate(original, "T-003", "2026-10-12"),
        _candidate(original, "T-004", "2026-09-29"),
        _candidate(original, "T-002", "2026-10-12"),
    ]
    example = replace(overview, results=candidates)
    assert [result.id for result in news_highlights.highlights(example)] == [
        "T-003",
        "T-002",
        "T-001",
    ]
    assert [
        result.id
        for result in news_highlights.highlights(
            replace(example, results=list(reversed(candidates)))
        )
    ] == ["T-003", "T-002", "T-001"]
    assert not news_highlights.highlights(replace(example, results=[candidates[1]]))


def test_current_news_has_three_results_including_the_older_s5_result(
    overview: overview_data.Overview,
) -> None:
    selected = news_highlights.highlights(overview)
    assert [result.id for result in selected] == ["T-154", "T-153", "T-060"]
    assert [result.dated for result in selected] == [
        ("published", "2026-10-12"),
        ("published", "2026-10-12"),
        ("published", "2026-09-29"),
    ]
    rendered = news_highlights.render(overview)
    assert re.findall(r'data-news-entry="([^"]+)"', rendered) == ["T-154", "T-153", "T-060"]
    assert rendered.count('class="site-news-day"') == 3
    assert rendered.count('data-news-topic="optimality"') == 3
    assert 'data-kind="formalization"' in rendered
    assert 'data-news-day="2026-10-12"' in rendered
    assert 'data-news-day="2026-09-29"' in rendered
    assert rendered.count('data-news-day="2026-10-12"') == 2
    assert re.findall(r'class="site-news-day" id="([^"]+)"', rendered) == [
        "news-result-t-154",
        "news-result-t-153",
        "news-result-t-060",
    ]
    assert re.findall(r'class="site-news-body" id="([^"]+)"', rendered) == [
        "news-result-t-154-body",
        "news-result-t-153-body",
        "news-result-t-060-body",
    ]
    assert 'id="t-154"' not in rendered


def test_news_keeps_the_registered_claims_credit_rungs_and_canonical_result_links(
    overview: overview_data.Overview,
) -> None:
    rendered = news_highlights.render(overview)
    for result in news_highlights.highlights(overview):
        match = re.search(
            rf'<article class="site-news-item" data-news-entry="{result.id}">(.*?)</article>',
            rendered,
            re.DOTALL,
        )
        assert match is not None
        article = match.group(1)
        assert f"<h3>{overview_data.tex_bounds(result.summary)}</h3>" in article
        assert overview_sections.credit_cell(result.credit) in article
        assert overview_sections.date_cell(result) in article
        assert overview_sections.status_chips(result) in article
        qualifier = "Reported result: this project has not verified the complete claim."
        if result.record["verification"] == "V0":
            assert article.index(qualifier) < article.index(
                overview_data.prose_html(result.record["claim"], between="</p><p>")
            )
        else:
            assert qualifier not in article
        assert overview_data.prose_html(result.record["claim"], between="</p><p>") in article
        assert (
            overview_data.prose_html(
                result.record["significance"]["rationale"], between="</p><p>"
            )
            in article
        )
        assert f'href="result/{result.id.lower()}.html"' in article
        assert f"Full result {result.id}" in article
    assert "Nothing here has repeated that build." in rendered
    assert "ten facts are a sample" in rendered
    assert "The complete capture recomputation and ten trees have not been run." in rendered
    assert "github.com/ofitzharding/sq17-lean/tree/" in rendered
    assert "github.com/Kleddamag/the-seventeenth-square-candidate/tree/" in rendered


def test_news_reads_no_launch_history_and_mutates_no_result_record(
    overview: overview_data.Overview, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = copy.deepcopy(overview)

    def no_history() -> render_changelog.Document:
        raise AssertionError("result News must not read or backfill launch history")

    monkeypatch.setattr(render_changelog, "load", no_history)
    assert news_highlights.render(overview)
    assert overview == before
