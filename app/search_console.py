from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Protocol

from app.models import PageMetric, QueryMetric, SitemapMetric, SiteMetrics


class SearchConsoleClient(Protocol):
    def weekly_metrics(self, site_url: str) -> SiteMetrics:
        """Return Search Console-shaped weekly metrics for a property."""


def metrics_from_dict(payload: dict) -> SiteMetrics:
    return SiteMetrics(
        site_url=payload["site_url"],
        period_start=date.fromisoformat(payload["period_start"]),
        period_end=date.fromisoformat(payload["period_end"]),
        total_clicks=int(payload.get("total_clicks", 0)),
        total_impressions=int(payload.get("total_impressions", 0)),
        average_ctr=float(payload.get("average_ctr", 0.0)),
        average_position=float(payload.get("average_position", 0.0)),
        indexed_homepage=payload.get("indexed_homepage"),
        pages=[
            PageMetric(
                url=row["url"],
                clicks=int(row.get("clicks", 0)),
                impressions=int(row.get("impressions", 0)),
                ctr=float(row.get("ctr", 0.0)),
                position=float(row.get("position", 0.0)),
                indexed=row.get("indexed"),
                indexing_status=row.get("indexing_status"),
            )
            for row in payload.get("pages", [])
        ],
        queries=[
            QueryMetric(
                query=row["query"],
                clicks=int(row.get("clicks", 0)),
                impressions=int(row.get("impressions", 0)),
                ctr=float(row.get("ctr", 0.0)),
                position=float(row.get("position", 0.0)),
            )
            for row in payload.get("queries", [])
        ],
        sitemaps=[
            SitemapMetric(
                url=row["url"],
                discovered_pages=int(row.get("discovered_pages", 0)),
                status=row.get("status", "unknown"),
                last_read=row.get("last_read"),
            )
            for row in payload.get("sitemaps", [])
        ],
        raw=payload,
    )


class FixtureSearchConsoleClient:
    def __init__(self, fixture_path: str | Path):
        self.fixture_path = Path(fixture_path)

    def weekly_metrics(self, site_url: str) -> SiteMetrics:
        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        payload["site_url"] = site_url
        return metrics_from_dict(payload)

