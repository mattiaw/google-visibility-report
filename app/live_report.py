from __future__ import annotations

import argparse
from datetime import date
from datetime import datetime
from pathlib import Path
import traceback

from app.reporting import build_visibility_report, render_text_report, save_text_report
from app.search_console import GoogleSearchConsoleClient


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _plain_english_error(error: Exception) -> tuple[str, str]:
    raw = f"{type(error).__name__}: {error}"
    lowered = raw.lower()

    if "access_denied" in lowered or "developer-approved testers" in lowered:
        return (
            "Google blocked the OAuth login because this app is still in Testing mode.",
            "In Google Cloud Auth Platform, add your Gmail address under Audience > Test users, then run the command again.",
        )
    if "api has not been used" in lowered or "service_disabled" in lowered or "disabled" in lowered:
        return (
            "The Google Search Console API appears to be disabled for this Google Cloud project.",
            "Open Google Cloud API Library for the selected project and enable the Google Search Console API.",
        )
    if "permission" in lowered or "forbidden" in lowered or "403" in lowered:
        return (
            "Google rejected the request because this login may not have access to that Search Console property.",
            "Run again with --list-sites and use one of the exact property names Google returns.",
        )
    if "winerror 10013" in lowered or "socket" in lowered:
        return (
            "Windows or the current sandbox blocked the outbound Google API connection.",
            "Run the same command from your normal PowerShell window outside the Codex sandbox.",
        )
    return (
        "The live Google Search Console request failed before a report could be generated.",
        "Read the technical details below, fix the Google/API setup issue, and run the command again.",
    )


def _write_failure_note(error: Exception, site_url: str, output_path: Path | None = None) -> Path:
    now = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    destination = output_path or Path("reports") / f"search-console-error_{now}.txt"
    destination.parent.mkdir(parents=True, exist_ok=True)

    summary, next_action = _plain_english_error(error)
    details = "".join(traceback.format_exception_only(type(error), error)).strip()
    destination.write_text(
        "\n".join(
            [
                "Search Console Visibility Report Failed",
                f"Site: {site_url}",
                f"Time: {datetime.now().isoformat(timespec='seconds')}",
                "",
                summary,
                "",
                f"Next: {next_action}",
                "",
                "Technical details",
                details,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return destination


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

    try:
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
    except Exception as error:
        summary, next_action = _plain_english_error(error)
        saved_path = _write_failure_note(error, args.site_url, output_path=args.output)
        print(summary)
        print(f"Next: {next_action}")
        print(f"Saved failure note to {saved_path}")
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
