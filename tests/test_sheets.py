from datetime import date, timedelta

import pandas as pd

from ama_ucf.sheets import get_all_worksheets, normalize_calendar, normalize_rows


def make_event_row(**overrides):
    row = {
        "event_date": date.today() + timedelta(days=7),
        "time": 0.5,
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

    assert result == {
        "success": True,
        "error": None,
        "data": [
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
        ],
    }


def test_normalize_calendar_builds_all_day_future_event_payload():
    event_date = date.today() + timedelta(days=14)
    df = pd.DataFrame([make_event_row(event_date=event_date, time=None)])

    result = normalize_calendar(df)

    assert result["success"] is True
    assert result["error"] is None
    assert len(result["data"]) == 1
    event = result["data"][0]
    assert event["start"] == {"date": event_date.isoformat()}
    assert event["end"] == {"date": (event_date + timedelta(days=1)).isoformat()}
    assert "dateTime" not in event["start"]
    assert "dateTime" not in event["end"]


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

    assert result["success"] is True
    assert [event["summary"] for event in result["data"]] == ["Future Event"]


def test_normalize_calendar_returns_error_for_missing_event_date():
    df = pd.DataFrame(
        [
            {
                "time": 0.5,
                "Event": "Malformed Event",
                "Description": "Missing required date column.",
                "Location": "BA1 135",
                "Type": "Workshop",
            }
        ]
    )

    result = normalize_calendar(df)

    assert result["success"] is False
    assert result["error"]
    assert result["data"] is None


def test_normalize_calendar_returns_error_for_invalid_time_fraction():
    df = pd.DataFrame([make_event_row(time=1.5)])

    result = normalize_calendar(df)

    assert result["success"] is False
    assert "Invalid time fraction" in result["error"]
    assert result["data"] is None


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

    assert result["success"] is True
    assert result["error"] is None
    data = result["data"]
    assert len(data) == 1
    assert data.iloc[0]["event_date"] == date(1899, 12, 31)


def test_get_all_worksheets_returns_wrapped_combined_dataframe(monkeypatch):
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

    assert result["success"] is True
    assert result["error"] is None
    data = result["data"]
    assert list(data["semester"]) == ["Fall '26", "Spring '27"]
    assert "Analytics" not in set(data["semester"])
