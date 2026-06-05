# AMA UCF Google Sheets to Google Calendar Pipeline

This project syncs AMA UCF event data from Google Sheets into Google Calendar. It is being shaped as an automated Python data pipeline that runs on GitHub Actions instead of a Flask web application.

The goal is to keep the club calendar up to date from a semester-based planning sheet while also producing lightweight analytics and audit logs that make each sync run observable.

## Current Stack

- Python 3.12
- Google Sheets API through `gspread`
- Google Calendar API through `google-api-python-client`
- Google authentication through `google-auth`
- GitHub Actions for scheduled and manual pipeline runs
- Environment variables and repository secrets for credentials and IDs

This project does not use Flask. Runtime automation should happen through GitHub Actions workflows.

## What the Pipeline Does

- Reads event rows from a semester tab in Google Sheets.
- Normalizes Google Sheets serial dates and fractional times into Python date/time values.
- Builds Google Calendar event payloads with title, description, location, type, start time, and end time.
- Pushes future events into the configured Google Calendar.
- Supports snapshot-style syncs and a watch-style polling mode during local development.

## Planned Production Pipeline Features

### 1. Write Analytics Back to Google Sheets

Use `gspread` and NumPy to calculate analytics from the event sheet and write the results back to an `Analytics` tab.

Analytics should include:

- Event-type frequency
- Semester-over-semester event totals
- Summary tables that can be reviewed directly inside Google Sheets

### 2. Add a Sync Audit Trail

Each sync run should write a timestamped audit entry to either `sync_log.csv` or a small SQLite database.

The audit trail should capture:

- Run timestamp
- Semester or sheet processed
- Events found
- Events created
- Events skipped
- Errors or warnings

This makes the project behave more like a production data pipeline with basic observability.

### 3. Add Pytest Coverage

Add tests for the core normalization helpers:

- `normalizingEvents()`
- `serialToDate()`

The tests should cover valid rows, missing dates, past events, Google Sheets serial date conversion, and malformed input.

### 4. Add Pandas DataFrame Support

Add `gspread-dataframe` and use `get_as_dataframe()` instead of relying only on `get_all_records()`.

This will allow the pipeline to:

- Clean column types more intentionally
- Handle empty cells and null values properly
- Normalize date, time, and event-type fields before calendar sync
- Treat the sync as a real tabular data pipeline rather than a simple row script

Expected additions:

- `pandas`
- `numpy`
- `gspread-dataframe`

### 5. Parameterize Multiple Semesters and Sheets

Add a `--semester` CLI argument so the same code can sync different semester tabs.

Example:

```bash
python main.py --semester "Fall '26"
```

The GitHub Actions workflow should also be able to pass the target semester as an input for manual runs.

## Project Structure and Target Architecture

```text
.
├── .github/
│   └── workflows/
│       └── sync.yml             # Planned GitHub Actions schedule/manual workflow
├── main.py                      # Pipeline entry point; planned home for --semester CLI support
├── pyproject.toml               # Python version and package dependencies
├── src/
│   ├── analytics.py             # Planned NumPy analytics writer for the Analytics sheet tab
│   ├── audit.py                 # Planned sync_log.csv or SQLite audit trail writer
│   ├── calendar.py              # Google Calendar authentication and event creation
│   ├── config.py                # Environment-based configuration
│   ├── dataframe.py             # Planned gspread-dataframe ingestion and dtype cleanup
│   └── sheets.py                # Google Sheets access and event normalization
├── tests/
│   └── test_sheets.py           # Planned pytest coverage for normalizingEvents() and serialToDate()
├── private/                     # Local-only credentials; ignored by Git
│   ├── token.json               # Private OAuth token generated after Google auth
│   └── google_api_key.json      # Private Google API credential/client JSON
├── sync_log.csv                 # Planned generated audit log, or sync_log.db for SQLite
├── README.md
└── uv.lock
```

Architecture flow:

```text
GitHub Actions
    -> main.py --semester "<sheet tab>"
    -> src.sheets / src.dataframe
    -> src.calendar
    -> Google Calendar
    -> src.analytics
    -> Google Sheets Analytics tab
    -> src.audit
    -> sync_log.csv or SQLite
```

## Configuration

The pipeline expects configuration to come from environment variables locally and from GitHub Actions secrets in automation.

Important values include:

- `SPREADSHEET_ID`: Google Sheet ID containing event tabs
- `CALENDAR_ID`: Target Google Calendar ID
- `GOOGLE_CREDENTIALS_FILE`: Path to the private Google API credential/client JSON file, such as `private/google_api_key.json`
- `GOOGLE_TOKEN_FILE`: Path to the private OAuth token file, such as `private/token.json`
- `SERVICE_ACCT_KEY`: Path or serialized service account credential, if the pipeline uses a service account runtime
- `CALENDAR_TIMEZONE`: Calendar timezone, defaults to `America/New_York`
- `CALENDAR_NAME`: Calendar name used when creating or resolving calendars
- `POLL_INTERVAL_SECONDS`: Polling interval for watch mode

GitHub Actions should store sensitive values as repository secrets instead of committing credential files.

### Private Google OAuth Files

The Google OAuth flow depends on two private JSON files:

- `private/token.json`: Generated after a successful OAuth login and used to refresh access without logging in every run.
- `private/google_api_key.json`: The credential/client file created in the Google Cloud Console for this project.

Both files must stay private and should be ignored by Git. For GitHub Actions, store their contents as encrypted repository secrets and recreate them during the workflow run, or use a service account setup if the final pipeline moves away from local OAuth.

Recommended local secret layout:

```text
private/
├── token.json
└── google_api_key.json
```

Recommended `.gitignore` entry:

```gitignore
private/
```

This keeps all local-only Google credential material in one obvious place, makes Git protection simple, and prevents secret files from being scattered through the project root.

## Local Development

Install dependencies:

```bash
uv sync
```

Run a one-time sync:

```bash
uv run python main.py
```

Run watch mode locally:

```bash
uv run python main.py watch
```

## GitHub Actions Runtime

The production version should run through GitHub Actions on a schedule and through manual dispatch.

Recommended workflow triggers:

- Scheduled sync, such as daily or weekly
- Manual `workflow_dispatch` for ad hoc syncs
- Optional semester input for reusable runs

Example workflow intent:

```yaml
on:
  schedule:
    - cron: "0 13 * * 1"
  workflow_dispatch:
    inputs:
      semester:
        description: "Google Sheet tab to sync"
        required: false
```

## Google Cloud Requirements

Enable these APIs in the Google Cloud project:

- Google Sheets API
- Google Calendar API
- Google Drive API

Use least-privilege credentials where possible, and share the target Sheet and Calendar with the service account used by the pipeline.

## Roadmap

- Replace row-dictionary reads with Pandas DataFrame ingestion through `gspread-dataframe`.
- Add NumPy-backed analytics and write them to an `Analytics` sheet tab.
- Add `sync_log.csv` or SQLite run logging.
- Add `pytest` tests for date conversion and event normalization.
- Add a `--semester` argument for reusable semester-based runs.
- Add a GitHub Actions workflow for scheduled and manual syncs.

Created by Humberto Bohorquez. Built with Python, Google APIs, and GitHub Actions.
