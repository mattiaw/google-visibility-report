from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Protocol

from app.models import PageMetric, QueryMetric, SitemapMetric, SiteMetrics

SEARCH_CONSOLE_READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"


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


def default_report_dates(today: date | None = None) -> tuple[date, date]:
    """Return the last seven complete days."""

    today = today or date.today()
    end = today - timedelta(days=1)
    start = end - timedelta(days=6)
    return start, end


class GoogleSearchConsoleClient:
    def __init__(self, credentials, cache_discovery: bool = False):
        self.credentials = credentials
        self.cache_discovery = cache_discovery

    @classmethod
    def from_oauth_files(
        cls,
        client_secrets_path: str | Path,
        token_path: str | Path,
    ) -> "GoogleSearchConsoleClient":
        credentials = load_oauth_credentials(client_secrets_path, token_path)
        return cls(credentials)

    def _service(self):
        from googleapiclient.discovery import build

        return build(
            "searchconsole",
            "v1",
            credentials=self.credentials,
            cache_discovery=self.cache_discovery,
        )

    def list_sites(self) -> list[dict]:
        response = self._service().sites().list().execute()
        return response.get("siteEntry", [])

    def weekly_metrics(
        self,
        site_url: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> SiteMetrics:
        start_date, end_date = _normalize_dates(start_date, end_date)
        service = self._service()

        totals = _query_search_analytics(service, site_url, start_date, end_date, [])
        page_rows = _query_search_analytics(service, site_url, start_date, end_date, ["page"])
        query_rows = _query_search_analytics(service, site_url, start_date, end_date, ["query"])

        pages = [
            PageMetric(
                url=row["keys"][0],
                clicks=int(row.get("clicks", 0)),
                impressions=int(row.get("impressions", 0)),
                ctr=float(row.get("ctr", 0.0)),
                position=float(row.get("position", 0.0)),
            )
            for row in page_rows
        ]
        queries = [
            QueryMetric(
                query=row["keys"][0],
                clicks=int(row.get("clicks", 0)),
                impressions=int(row.get("impressions", 0)),
                ctr=float(row.get("ctr", 0.0)),
                position=float(row.get("position", 0.0)),
            )
            for row in query_rows
        ]

        total_row = totals[0] if totals else _aggregate_rows(page_rows)
        sitemaps = _list_sitemaps(service, site_url)

        return SiteMetrics(
            site_url=site_url,
            period_start=start_date,
            period_end=end_date,
            total_clicks=int(total_row.get("clicks", 0)),
            total_impressions=int(total_row.get("impressions", 0)),
            average_ctr=float(total_row.get("ctr", 0.0)),
            average_position=float(total_row.get("position", 0.0)),
            pages=pages,
            queries=queries,
            sitemaps=sitemaps,
            indexed_homepage=None,
            raw={
                "totals": totals,
                "pages": page_rows,
                "queries": query_rows,
            },
        )


def load_oauth_credentials(client_secrets_path: str | Path, token_path: str | Path):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_secrets_path = Path(client_secrets_path)
    token_path = Path(token_path)
    scopes = [SEARCH_CONSOLE_READONLY_SCOPE]

    credentials = None
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), scopes)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), scopes)
        credentials = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def _normalize_dates(start_date: date | None, end_date: date | None) -> tuple[date, date]:
    if start_date and end_date:
        return start_date, end_date
    if start_date or end_date:
        raise ValueError("Pass both start_date and end_date, or neither.")
    return default_report_dates()


def _query_search_analytics(
    service,
    site_url: str,
    start_date: date,
    end_date: date,
    dimensions: list[str],
    row_limit: int = 25,
) -> list[dict]:
    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": dimensions,
        "rowLimit": row_limit,
    }
    response = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    return response.get("rows", [])


def _aggregate_rows(rows: list[dict]) -> dict:
    clicks = sum(float(row.get("clicks", 0)) for row in rows)
    impressions = sum(float(row.get("impressions", 0)) for row in rows)
    weighted_position = sum(
        float(row.get("position", 0)) * float(row.get("impressions", 0)) for row in rows
    )
    return {
        "clicks": clicks,
        "impressions": impressions,
        "ctr": clicks / impressions if impressions else 0.0,
        "position": weighted_position / impressions if impressions else 0.0,
    }


def _list_sitemaps(service, site_url: str) -> list[SitemapMetric]:
    try:
        response = service.sitemaps().list(siteUrl=site_url).execute()
    except Exception:
        return []

    sitemaps: list[SitemapMetric] = []
    for row in response.get("sitemap", []):
        errors = int(row.get("errors", 0))
        warnings = int(row.get("warnings", 0))
        is_pending = bool(row.get("isPending", False))
        status = "pending" if is_pending else "success" if errors == 0 else "error"
        if warnings and status == "success":
            status = "warning"
        discovered_pages = 0
        for content in row.get("contents", []):
            discovered_pages += int(content.get("submitted", 0) or content.get("indexed", 0) or 0)
        sitemaps.append(
            SitemapMetric(
                url=row.get("path", ""),
                discovered_pages=discovered_pages,
                status=status,
                last_read=row.get("lastDownloaded"),
            )
        )
    return sitemaps

