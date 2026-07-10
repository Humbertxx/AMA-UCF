from datetime import date

import pandas as pd

from ama_ucf.analytics import (
    analytics_tab,
    cross_segment_evaluation,
    event_density,
    event_type_mix,
    write_to_sheet,
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
    data = event_density(make_analytics_df())

    assert list(data.columns) == ["event_date", "event_count"]
    assert data["event_count"].sum() == 4


def test_cross_segment_evaluation_groups_by_semester_and_type():
    data = cross_segment_evaluation(make_analytics_df())

    workshop = data[(data["semester"] == "Fall '26") & (data["Type"] == "Workshop")].iloc[0]

    assert workshop["event_count"] == 2
    assert workshop["first_event_date"] == pd.Timestamp("2026-09-08")
    assert workshop["last_event_date"] == pd.Timestamp("2026-09-22")
    assert workshop["largest_gap_days"] == 14


def test_event_type_mix_calculates_share_and_cumulative_share():
    data = event_type_mix(make_analytics_df())

    workshop = data[data["Type"] == "Workshop"].iloc[0]

    assert list(data.columns) == [
        "Type",
        "event_count",
        "share_of_events",
        "cumulative_share",
    ]
    assert workshop["event_count"] == 2
    assert workshop["share_of_events"] == 0.5
    assert data["cumulative_share"].iloc[-1] == 1.0


def test_analytics_tab_returns_enabled_analytics_without_google_write(monkeypatch):
    written = {}

    def fake_write_to_sheet(sh, results):
        written["sh"] = sh
        written["results"] = results
        return "analytics written"

    monkeypatch.setattr("ama_ucf.analytics.write_to_sheet", fake_write_to_sheet)

    fake_sh = [object()]
    result = analytics_tab(fake_sh, all_worksheets=make_analytics_df())

    assert result == "analytics written"
    assert written["sh"] is fake_sh
    assert set(written["results"]) == {
        "event_density",
        "cross_segment_evaluation",
        "event_type_mix",
    }


def test_write_to_sheet_creates_missing_analytics_anchor(monkeypatch):
    writes = []

    class FakeCell:
        def __init__(self, row, col):
            self.row = row
            self.col = col

    class FakeWorksheet:
        def __init__(self):
            self.title_cell = None

        def find(self, value):
            return self.title_cell if value == "Insightful Analytics" else None

        def update_cell(self, row, col, value):
            self.title_cell = FakeCell(row, col)

    class FakeSpreadsheet:
        def __init__(self):
            self.ws = FakeWorksheet()

        def worksheet(self, title):
            assert title == "Analytics"
            return self.ws

    def fake_set_with_dataframe(ws, df, row, col):
        writes.append((row, col, list(df.columns)))

    monkeypatch.setattr("ama_ucf.analytics.set_with_dataframe", fake_set_with_dataframe)

    results = {
        "event_density": pd.DataFrame({"event_date": [pd.Timestamp("2026-09-01")], "event_count": [1]}),
        "cross_segment_evaluation": pd.DataFrame(
            {
                "semester": ["Fall '26"],
                "Type": ["Workshop"],
                "event_count": [1],
                "first_event_date": [pd.Timestamp("2026-09-01")],
                "last_event_date": [pd.Timestamp("2026-09-01")],
                "largest_gap_days": [None],
            }
        ),
        "event_type_mix": pd.DataFrame(
            {
                "Type": ["Workshop"],
                "event_count": [1],
                "share_of_events": [1.0],
                "cumulative_share": [1.0],
            }
        ),
    }

    result = write_to_sheet([FakeSpreadsheet()], results)

    assert result == "analytics written"
    assert writes == [
        (11, 13, ["event_date", "event_count"]),
        (
            11,
            17,
            [
                "semester",
                "Type",
                "event_count",
                "first_event_date",
                "last_event_date",
                "largest_gap_days",
            ],
        ),
        (11, 23, ["Type", "event_count", "share_of_events", "cumulative_share"]),
    ]
