"""The homepage's newest three S5 results, from the existing result register."""

from __future__ import annotations

from devtools import overview_sections, render_changelog
from devtools.overview_data import Overview, Result, prose_html, tex_bounds

LIMIT = 3


def highlights(overview: Overview) -> tuple[Result, ...]:
    """Keep the register's displayed-date and ID order, without an age cutoff."""
    return tuple(
        result
        for result in overview_sections.recent_results(overview)
        if overview_sections.significance(result) == 5
    )[:LIMIT]


def _article(result: Result) -> str:
    claim = prose_html(result.record["claim"], between="</p><p>")
    rationale = prose_html(result.record["significance"]["rationale"], between="</p><p>")
    kind = result.record["kind"]
    topic = "optimality" if kind in {"formalization", "simplification"} else kind
    qualifier = (
        '<p class="site-result-meta">Reported result: this project has not verified '
        "the complete claim.</p>"
        if result.record["verification"] == "V0"
        else ""
    )
    return (
        f'<article class="site-news-item" data-news-entry="{result.id}">'
        f"{render_changelog.news_topics([topic])}"
        f"<h3>{tex_bounds(result.summary)}</h3>"
        f'<p class="site-result-status">{overview_sections.status_chips(result)}</p>'
        f'<p class="site-result-meta">{overview_sections.date_cell(result)} · '
        f"{overview_sections.credit_cell(result.credit)}</p>"
        f"{qualifier}<p>{claim}</p><p>{rationale}</p>"
        f'<p><a href="result/{result.id.lower()}.html">Full result '
        f"{result.id}</a></p></article>"
    )


def render(overview: Overview) -> str:
    """Give each selected result its own card, keeping every headline in the preview."""
    cards = (
        render_changelog.news_card(
            f"news-result-{result.id.lower()}",
            overview_sections.first_day(result.dated[1]),
            _article(result),
        )
        for result in highlights(overview)
    )
    return '<div class="site-news sans-text" data-news>' + "\n".join(cards) + "</div>"
