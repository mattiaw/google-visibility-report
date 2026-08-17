from __future__ import annotations

import json
from pathlib import Path

from app.reporting import build_visibility_report, render_text_report
from app.search_console import metrics_from_dict


def load_sample():
    payload = json.loads(Path("sample_data/childslot_week.json").read_text(encoding="utf-8"))
    return metrics_from_dict(payload)


def test_report_uses_plain_english_headline_for_clicks() -> None:
    report = build_visibility_report(load_sample())

    assert report.headline == "Google sent visitors to the site this week."
    assert report.site_url == "https://childslot.com/"
    assert report.recommendations


def test_report_flags_impressions_without_clicks() -> None:
    report = build_visibility_report(load_sample())

    titles = [item.title for item in report.recommendations]
    assert "Google is showing a page, but people are not clicking it" in titles


def test_text_report_contains_small_business_language() -> None:
    text = render_text_report(build_visibility_report(load_sample()))

    assert "Weekly Google Visibility Report" in text
    assert "Top recommendations" in text
    assert "open play near massapequa" in text

