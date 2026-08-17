from __future__ import annotations

from app.search_console import FixtureSearchConsoleClient


def test_fixture_client_loads_metrics_for_requested_site() -> None:
    client = FixtureSearchConsoleClient("sample_data/childslot_week.json")
    metrics = client.weekly_metrics("https://example.com/")

    assert metrics.site_url == "https://example.com/"
    assert metrics.total_impressions == 42
    assert metrics.sitemaps[0].status == "success"

