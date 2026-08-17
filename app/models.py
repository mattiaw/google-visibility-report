from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class QueryMetric:
    query: str
    clicks: int
    impressions: int
    ctr: float
    position: float


@dataclass(frozen=True)
class PageMetric:
    url: str
    clicks: int
    impressions: int
    ctr: float
    position: float
    indexed: bool | None = None
    indexing_status: str | None = None


@dataclass(frozen=True)
class SitemapMetric:
    url: str
    discovered_pages: int
    status: str
    last_read: str | None = None


@dataclass(frozen=True)
class SiteMetrics:
    site_url: str
    period_start: date
    period_end: date
    total_clicks: int
    total_impressions: int
    average_ctr: float
    average_position: float
    pages: list[PageMetric] = field(default_factory=list)
    queries: list[QueryMetric] = field(default_factory=list)
    sitemaps: list[SitemapMetric] = field(default_factory=list)
    indexed_homepage: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Recommendation:
    priority: str
    title: str
    explanation: str
    next_action: str


@dataclass(frozen=True)
class VisibilityReport:
    site_url: str
    period_label: str
    headline: str
    summary: str
    stats: list[tuple[str, str]]
    recommendations: list[Recommendation]
    top_queries: list[QueryMetric]
    top_pages: list[PageMetric]

