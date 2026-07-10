from datetime import date, timedelta
import warnings

import pandas as pd
import pytest

from ama_ucf.sheets import get_all_worksheets, normalize_calendar, normalize_rows


def make_event_row(**overrides):
    row = {
        "event_date": date.today() + timedelta(days=7),
        "Time": 0.5,
        "Event": "Marketing Workshop",
        "Description": "Hollywood Stars and Celebrities: What Do They Know? Do They Know Things?? Let's Find Out!",
        "Location": "BA1 135",
        "Type": "Workshop",
    }
    row.update(overrides)
    return row

# mock data pass into the test functions below
def test_normalize_calendar_builds_timed_future_event_payload():
    df = pd.DataFrame([make_event_row()])

    result = normalize_calendar(df)

    assert result == [
        {
            "summary": "Marketing Workshop",
            "description": "Hollywood Stars and Celebrities: What Do They Know? Do They Know Things?? Let's Find Out!",
            "location": "BA1 135",
            "organizer": "Workshop",
            "start": {
                "dateTime": (
                    date.today() + timedelta(days=7)
                ).isoformat()
                + "T12:00:00"
            },
            "end": {
                "dateTime": (
                    date.today() + timedelta(days=7)
                ).isoformat()
                + "T13:00:00"
            },
        }
    ]


def test_normalize_calendar_builds_all_day_future_event_payload():
    event_date = date.today() + timedelta(days=14)
    df = pd.DataFrame([make_event_row(event_date=event_date, Time=None)])

    result = normalize_calendar(df)

    assert len(result) == 1
    event = result[0]
    assert event["start"] == {"date": event_date.isoformat()}
    assert event["end"] == {"date": (event_date + timedelta(days=1)).isoformat()}
    assert "dateTime" not in event["start"]
    assert "dateTime" not in event["end"]


def test_normalize_calendar_treats_nan_time_as_all_day_event():
    event_date = date.today() + timedelta(days=14)
    df = pd.DataFrame([make_event_row(event_date=event_date, Time=float("nan"))])

    result = normalize_calendar(df)

    event = result[0]
    assert event["start"] == {"date": event_date.isoformat()}
    assert event["end"] == {"date": (event_date + timedelta(days=1)).isoformat()}


def test_normalize_calendar_filters_past_events():
    past_event = make_event_row(
        event_date=date.today() - timedelta(days=1),
        Event="Past Event",
    )
    future_event = make_event_row(
        event_date=date.today() + timedelta(days=1),
        Event="Future Event",
    )
    df = pd.DataFrame([past_event, future_event])

    result = normalize_calendar(df)

    assert [event["summary"] for event in result] == ["Future Event"]


def test_normalize_calendar_returns_error_for_missing_event_date():
    df = pd.DataFrame(
        [
            {
                "Time": 0.5,
                "Event": "Malformed Event",
                "Description": "Missing required date column.",
                "Location": "BA1 135",
                "Type": "Workshop",
            }
        ]
    )

    with pytest.raises(KeyError):
        normalize_calendar(df)


def test_normalize_calendar_returns_error_for_invalid_time_fraction():
    df = pd.DataFrame([make_event_row(Time=1.5)])

    with pytest.raises(ValueError, match="Invalid time fraction"):
        normalize_calendar(df)


def test_normalize_rows_returns_response_with_event_date():
    df = pd.DataFrame(
        [
            {
                "Date": 1,
                "Event": "Launch Meeting",
                "Description": "Planning.",
                "Location": "BA1",
                "Type": "Workshop",
            },
            {
                "Date": None,
                "Event": None,
                "Description": "Dropped empty row.",
                "Location": None,
                "Type": None,
            },
        ]
    )

    result = normalize_rows(df)

    assert len(result) == 1
    assert result.iloc[0]["event_date"] == date(1899, 12, 31)


def test_normalize_rows_parses_text_dates_without_inference_warning():
    df = pd.DataFrame(
        [
            {
                "Date": "2026-09-01",
                "Event": "Launch Meeting",
                "Description": "Planning.",
                "Location": "BA1",
                "Type": "Workshop",
            },
            {
                "Date": "09/08/2026",
                "Event": "Follow-up",
                "Description": "Planning.",
                "Location": "BA1",
                "Type": "Workshop",
            },
        ]
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = normalize_rows(df)

    assert list(result["event_date"]) == [date(2026, 9, 1), date(2026, 9, 8)]
    assert not any("Could not infer format" in str(warning.message) for warning in caught)


def test_get_all_worksheets_returns_combined_dataframe(monkeypatch):
    class FakeWorksheet:
        def __init__(self, title):
            self.title = title

    class FakeSpreadsheet:
        def __init__(self, worksheets):
            self._worksheets = worksheets

        def worksheets(self):
            return self._worksheets

    def fake_get_as_dataframe(ws, evaluate_formulas=True, skiprows=2):
        return pd.DataFrame(
            [
                {
                    "Date": 1,
                    "Event": f"{ws.title} Event",
                    "Description": "Loaded from worksheet.",
                    "Location": "BA1",
                    "Type": "Social",
                }
            ]
        )

    monkeypatch.setattr("ama_ucf.sheets.get_as_dataframe", fake_get_as_dataframe)

    spreadsheets = [
        FakeSpreadsheet(
            [
                FakeWorksheet("Fall '26"),
                FakeWorksheet("Analytics"),
                FakeWorksheet("Spring '27"),
            ]
        )
    ]

    result = get_all_worksheets(spreadsheets)

    assert list(result["semester"]) == ["Fall '26", "Spring '27"]
    assert "Analytics" not in set(result["semester"])
