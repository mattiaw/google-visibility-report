from __future__ import annotations

from datetime import date
from pathlib import Path
import re

from app.models import PageMetric, QueryMetric, Recommendation, SiteMetrics, VisibilityReport


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _period_label(start: date, end: date) -> str:
    return f"{start.isoformat()} through {end.isoformat()}"


def _safe_file_stem(value: str) -> str:
    stem = value.replace("https://", "").replace("http://", "").strip("/").lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem)
    return stem.strip("-") or "site"


def default_text_report_path(report: VisibilityReport, reports_dir: Path = Path("reports")) -> Path:
    period = report.period_label.replace(" through ", "_to_")
    return reports_dir / f"{_safe_file_stem(report.site_url)}_{period}.txt"


def save_text_report(
    report: VisibilityReport,
    output_path: Path | None = None,
    reports_dir: Path = Path("reports"),
) -> Path:
    destination = output_path or default_text_report_path(report, reports_dir=reports_dir)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_text_report(report), encoding="utf-8")
    return destination


def _top_by_impressions(items: list[PageMetric | QueryMetric], limit: int = 5):
    return sorted(items, key=lambda item: (item.impressions, item.clicks), reverse=True)[:limit]


def build_visibility_report(metrics: SiteMetrics) -> VisibilityReport:
    recommendations: list[Recommendation] = []

    if metrics.indexed_homepage is False:
        recommendations.append(
            Recommendation(
                priority="High",
                title="Google may not be able to show your homepage yet",
                explanation=(
                    "The homepage is the front door. If it is not indexed, the rest of the site "
                    "has a weaker chance of being found."
                ),
                next_action="Inspect the homepage in Search Console and request indexing after fixes.",
            )
        )

    failed_sitemaps = [s for s in metrics.sitemaps if s.status.lower() not in {"success", "ok"}]
    if failed_sitemaps:
        recommendations.append(
            Recommendation(
                priority="High",
                title="Your sitemap needs attention",
                explanation=(
                    "A sitemap helps Google discover the pages you care about. One or more "
                    "submitted sitemaps did not report a clean status."
                ),
                next_action="Open the sitemap report in Search Console and fix fetch or parsing errors.",
            )
        )

    pages_with_impressions_no_clicks = [
        page for page in metrics.pages if page.impressions >= 10 and page.clicks == 0
    ]
    if pages_with_impressions_no_clicks:
        page = max(pages_with_impressions_no_clicks, key=lambda candidate: candidate.impressions)
        recommendations.append(
            Recommendation(
                priority="Medium",
                title="Google is showing a page, but people are not clicking it",
                explanation=(
                    f"{page.url} received {page.impressions} impressions with no clicks. "
                    "That usually means the page title or description is not compelling enough, "
                    "or the searcher expected something slightly different."
                ),
                next_action="Rewrite the page title and opening copy to match the search intent more clearly.",
            )
        )

    striking_distance_queries = [
        q for q in metrics.queries if q.impressions >= 10 and 8.0 <= q.position <= 20.0
    ]
    if striking_distance_queries:
        query = max(striking_distance_queries, key=lambda candidate: candidate.impressions)
        recommendations.append(
            Recommendation(
                priority="Medium",
                title="One search phrase is close enough to improve",
                explanation=(
                    f"'{query.query}' is averaging position {query.position:.1f}. "
                    "That is not page-one dominance, but it is close enough that better content "
                    "or internal links may help."
                ),
                next_action="Improve the best matching page and add one or two internal links to it.",
            )
        )

    if not recommendations:
        recommendations.append(
            Recommendation(
                priority="Low",
                title="Keep watching for enough data to make a confident move",
                explanation=(
                    "No urgent Google visibility issue stands out yet. That can be good news, "
                    "or it can simply mean the site is still too new to have much signal."
                ),
                next_action="Check again next week and focus on getting real local pages indexed.",
            )
        )

    if metrics.total_impressions == 0:
        headline = "Google is not showing this site in search results yet."
        summary = (
            "There were no recorded search impressions for this period. The first goal is simple: "
            "make sure Google can crawl the site, read the sitemap, and index the key pages."
        )
    elif metrics.total_clicks == 0:
        headline = "Google is seeing the site, but no one clicked this week."
        summary = (
            "The site received impressions but no clicks. That means Google is testing the site "
            "in results, and the best next move is to improve page titles, descriptions, and "
            "the match between pages and search intent."
        )
    else:
        headline = "Google sent visitors to the site this week."
        summary = (
            "The site earned both impressions and clicks. The next job is to understand which "
            "queries and pages are working, then improve the pages that are close but underperforming."
        )

    stats = [
        ("Clicks from Google", str(metrics.total_clicks)),
        ("Search impressions", str(metrics.total_impressions)),
        ("Average click-through rate", _pct(metrics.average_ctr)),
        ("Average position", f"{metrics.average_position:.1f}"),
        ("Homepage indexed", "Yes" if metrics.indexed_homepage else "No" if metrics.indexed_homepage is False else "Unknown"),
        ("Sitemaps submitted", str(len(metrics.sitemaps))),
    ]

    return VisibilityReport(
        site_url=metrics.site_url,
        period_label=_period_label(metrics.period_start, metrics.period_end),
        headline=headline,
        summary=summary,
        stats=stats,
        recommendations=recommendations[:3],
        top_queries=_top_by_impressions(metrics.queries),
        top_pages=_top_by_impressions(metrics.pages),
    )


def render_text_report(report: VisibilityReport) -> str:
    lines = [
        "Weekly Google Visibility Report",
        f"{report.site_url} | {report.period_label}",
        "",
        report.headline,
        "",
        report.summary,
        "",
        "This week's numbers",
    ]
    lines.extend(f"- {label}: {value}" for label, value in report.stats)
    lines.extend(["", "Top recommendations"])
    for index, recommendation in enumerate(report.recommendations, start=1):
        lines.extend(
            [
                f"{index}. [{recommendation.priority}] {recommendation.title}",
                f"   Why: {recommendation.explanation}",
                f"   Next: {recommendation.next_action}",
            ]
        )
    lines.extend(["", "Top search phrases"])
    if report.top_queries:
        lines.extend(
            f"- {query.query}: {query.impressions} impressions, {query.clicks} clicks, position {query.position:.1f}"
            for query in report.top_queries
        )
    else:
        lines.append("- No query data yet.")
    lines.extend(["", "Top pages"])
    if report.top_pages:
        lines.extend(
            f"- {page.url}: {page.impressions} impressions, {page.clicks} clicks, position {page.position:.1f}"
            for page in report.top_pages
        )
    else:
        lines.append("- No page data yet.")
    return "\n".join(lines) + "\n"

