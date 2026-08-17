# Google Visibility Report

A weekly Google visibility report for small businesses, written in human language.

This project is a simple layer over Google Search Console data. It answers the questions a small business owner actually asks:

- Can Google find my website?
- Did more or fewer people see me this week?
- Which pages got noticed?
- Which pages should I fix first?
- What should I do next?

The first version works with sample or imported Search Console-shaped data. Google OAuth and live API access are the next layer.

## Product Shape

The product should stay intentionally small:

1. Connect Google Search Console.
2. Choose a site property.
3. Pull weekly search and indexing data.
4. Generate a plain-English report.
5. Email it every week.

## Architecture

- `app/reporting.py`: turns metrics into human-language findings.
- `app/main.py`: tiny FastAPI app with report endpoints.
- `app/search_console.py`: Search Console client boundary. It includes a fixture client now and is ready for a live Google client later.
- `app/mailer.py`: SMTP email sender for scheduled reports.
- `sample_data/`: example input data for development and demos.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/report/sample
```

Generate a text report from sample data:

```powershell
.\.venv\Scripts\python.exe -m app.cli sample_data/childslot_week.json
```

## Environment Variables

For email delivery:

```text
GVR_SMTP_HOST=smtp.resend.com
GVR_SMTP_PORT=587
GVR_SMTP_USERNAME=resend
GVR_SMTP_PASSWORD=<api key>
GVR_SMTP_FROM_EMAIL=reports@example.com
GVR_SMTP_FROM_NAME=Google Visibility Report
```

For a future live Google Search Console integration:

```text
GOOGLE_CLIENT_ID=<oauth client id>
GOOGLE_CLIENT_SECRET=<oauth client secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/oauth/callback
```

## First Case Studies

- ChildSlot: `https://childslot.com/`
- EqualDrive: `https://equaldrive.app/`

