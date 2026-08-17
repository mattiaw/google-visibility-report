from __future__ import annotations

from datetime import date

from app.search_console import default_report_dates


def test_default_report_dates_use_last_complete_week() -> None:
    start, end = default_report_dates(today=date(2026, 8, 17))

    assert start == date(2026, 8, 10)
    assert end == date(2026, 8, 16)
