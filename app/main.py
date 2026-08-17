from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.reporting import build_visibility_report, render_text_report
from app.search_console import FixtureSearchConsoleClient

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"
SAMPLE_DATA = BASE_DIR / "sample_data" / "childslot_week.json"

templates = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

app = FastAPI(title="Google Visibility Report")


@app.get("/")
def home() -> dict[str, str]:
    return {
        "name": "Google Visibility Report",
        "purpose": "Plain-English weekly Search Console reports for small businesses.",
        "sample_report": "/report/sample",
        "sample_text_report": "/report/sample.txt",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/report/sample.txt", response_class=PlainTextResponse)
def sample_text_report() -> str:
    client = FixtureSearchConsoleClient(SAMPLE_DATA)
    metrics = client.weekly_metrics("https://childslot.com/")
    return render_text_report(build_visibility_report(metrics))


@app.get("/report/sample", response_class=HTMLResponse)
def sample_html_report() -> str:
    client = FixtureSearchConsoleClient(SAMPLE_DATA)
    metrics = client.weekly_metrics("https://childslot.com/")
    report = build_visibility_report(metrics)
    template = templates.get_template("report.html")
    return template.render(report=report)

