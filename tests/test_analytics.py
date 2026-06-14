from datetime import date

import pandas as pd

from ama_ucf.analytics import (
    analytics_tab,
    cross_segment_evaluation,
    event_density,
    event_type_mix,
)

# mock data pass into the test functions below
def make_analytics_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "semester": "Fall '26",
                "event_date": date(2026, 9, 1),
                "Event": "Kickoff",
                "Type": "Social",
            },
            {
                "semester": "Fall '26",
                "event_date": date(2026, 9, 8),
                "Event": "Workshop 1",
                "Type": "Workshop",
            },
            {
                "semester": "Fall '26",
                "event_date": date(2026, 9, 22),
                "Event": "Workshop 2",
                "Type": "Workshop",
            },
            {
                "semester": "Spring '27",
                "event_date": date(2027, 1, 15),
                "Event": "Speaker Night",
                "Type": "Speaker",
            },
        ]
    )


def test_event_density_counts_events_by_week():
    result = event_density(make_analytics_df())

    assert list(result.columns) == ["event_date", "event_count"]
    assert result["event_count"].sum() == 4


def test_cross_segment_evaluation_groups_by_semester_and_type():
    result = cross_segment_evaluation(make_analytics_df())

    workshop = result[(result["semester"] == "Fall '26") & (result["Type"] == "Workshop")].iloc[0]

    assert workshop["event_count"] == 2
    assert workshop["first_event_date"] == pd.Timestamp("2026-09-08")
    assert workshop["last_event_date"] == pd.Timestamp("2026-09-22")
    assert workshop["largest_gap_days"] == 14


def test_event_type_mix_calculates_share_and_cumulative_share():
    result = event_type_mix(make_analytics_df())

    workshop = result[result["Type"] == "Workshop"].iloc[0]

    assert list(result.columns) == [
        "Type",
        "event_count",
        "share_of_events",
        "cumulative_share",
    ]
    assert workshop["event_count"] == 2
    assert workshop["share_of_events"] == 0.5
    assert result["cumulative_share"].iloc[-1] == 1.0


def test_analytics_tab_returns_enabled_analytics_without_google_write(monkeypatch):
    written = {}

    def fake_write_to_sheet(gc, results):
        written["gc"] = gc
        written["results"] = results
        return {"success": True, "error": None, "data": "analytics written"}

    monkeypatch.setattr("ama_ucf.analytics.write_to_sheet", fake_write_to_sheet)

    result = analytics_tab(gc={"data": object()}, all_worksheets=make_analytics_df())

    assert result["success"] is True
    assert result["error"] is None
    assert set(result["data"]) == {
        "event_density",
        "cross_segment_evaluation",
        "event_type_mix",
    }
    assert written["results"] == result["data"]
