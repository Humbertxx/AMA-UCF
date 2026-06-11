from datetime import date, timedelta

import pandas as pd

from src.sheets import normalize_calendar


def make_event_row(**overrides):
    row = {
        "event_date": date.today() + timedelta(days=7),
        "time": 0.5,
        "Event": "Super marketing Workshop",
        "Description": "Hollywood Stars and Celebrities: What Do They Know? Do They Know Things?? Let's Find Out!",
        "Location": "BA1 135",
        "Type": "Workshop",
    }
    row.update(overrides)
    return row


def test_normalize_calendar_builds_timed_future_event_payload():
    df = pd.DataFrame([make_event_row()])

    result = normalize_calendar({"data": df})

    assert result == {
        "success": True,
        "error": None,
        "data": [
            {
                "summary": "Marketing Workshop",
                "description": "Learn campaign planning basics.",
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

    result = normalize_calendar({"data": df})

    assert result["success"] is True
    assert result["error"] is None
    assert len(result["data"]) == 1
    event = result["data"][0]
    assert event["start"] == {"date": event_date.isoformat()}
    assert event["end"] == {"date": event_date.isoformat()}
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

    result = normalize_calendar({"data": df})

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

    result = normalize_calendar({"data": df})

    assert result["success"] is False
    assert result["error"]
    assert result["data"] is None
