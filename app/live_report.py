from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from app.reporting import build_visibility_report, render_text_report, save_text_report
from app.search_console import GoogleSearchConsoleClient


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a live Search Console visibility report.")
    parser.add_argument(
        "--site-url",
        required=True,
        help="Search Console property, e.g. sc-domain:childslot.com or https://childslot.com/",
    )
    parser.add_argument(
        "--client-secrets",
        default="client_secret.json",
        help="OAuth client secrets JSON downloaded from Google Cloud.",
    )
    parser.add_argument(
        "--token",
        default=".gvr/token.json",
        help="Local OAuth token cache path. Do not commit this file.",
    )
    parser.add_argument("--start-date", help="Optional YYYY-MM-DD report start date.")
    parser.add_argument("--end-date", help="Optional YYYY-MM-DD report end date.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional text report path. Defaults to reports/<site>_<period>.txt.",
    )
    parser.add_argument(
        "--list-sites",
        action="store_true",
        help="List Search Console properties visible to this Google login, then exit.",
    )
    args = parser.parse_args()

    client = GoogleSearchConsoleClient.from_oauth_files(
        client_secrets_path=Path(args.client_secrets),
        token_path=Path(args.token),
    )

    if args.list_sites:
        for site in client.list_sites():
            permission = site.get("permissionLevel", "unknown")
            print(f"{site.get('siteUrl')} ({permission})")
        return

    metrics = client.weekly_metrics(
        site_url=args.site_url,
        start_date=_parse_date(args.start_date),
        end_date=_parse_date(args.end_date),
    )
    report = build_visibility_report(metrics)
    text = render_text_report(report)
    saved_path = save_text_report(report, output_path=args.output)
    print(text)
    print(f"Saved report to {saved_path}")


if __name__ == "__main__":
    main()
