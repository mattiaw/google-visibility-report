from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.reporting import build_visibility_report, render_text_report
from app.search_console import metrics_from_dict


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a plain-English Google visibility report.")
    parser.add_argument("metrics_json", type=Path, help="Path to Search Console-shaped metrics JSON.")
    args = parser.parse_args()

    payload = json.loads(args.metrics_json.read_text(encoding="utf-8"))
    report = build_visibility_report(metrics_from_dict(payload))
    print(render_text_report(report))


if __name__ == "__main__":
    main()

