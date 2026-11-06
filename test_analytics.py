"""Tests: dashboard calculations (checked against values worked out by hand)."""
import pandas as pd
import pytest

from modules import groundwater_analytics as ga


def test_coverage_summary(sample_df):
    c = ga.coverage_summary(sample_df)
    assert c["rows"] == 6 and c["states"] == 2 and c["stations"] == 2
    assert str(c["first_date"]) == "2019-01-15" and str(c["latest_date"]) == "2021-01-15"
    assert ga.coverage_summary(sample_df.iloc[0:0]) == {"rows": 0}


def test_state_summary_values(sample_df):
    s = ga.state_summary(sample_df).set_index("state_name")
    assert s.loc["State A", "mean_depth"] == 13.0          # (10+12+14+16)/4
    assert s.loc["State B", "mean_depth"] == 4.0           # (5+3)/2
    assert s.loc["State A", "readings"] == 4
    assert ga.state_summary(sample_df).iloc[0]["state_name"] == "State A"   # deepest first


def test_filters(sample_df):
    assert len(ga.filter_data(sample_df, states=["State B"])) == 2
    assert len(ga.filter_data(sample_df, year_range=(2020, 2021))) == 3
    assert len(ga.filter_data(sample_df, districts=["D1"], year_range=(2019, 2019))) == 2


def test_yearly_and_quarterly(sample_df):
    y = ga.yearly_trend(sample_df[sample_df.state_name == "State A"]).set_index("year")
    assert y.loc[2019, "mean_depth"] == 11.0 and y.loc[2021, "mean_depth"] == 16.0
    q = ga.quarterly_comparison(sample_df[sample_df.state_name == "State A"])
    assert set(q["quarter"]) == {1, 2}
    assert q[(q.year == 2019) & (q.quarter == 2)]["mean_depth"].iloc[0] == 12.0


def test_compare_years(sample_df):
    c = ga.compare_years(sample_df, 2019, 2021).set_index("state_name")
    assert c.loc["State A", "change_m"] == 16.0 - 11.0 == 5.0       # deeper
    assert c.loc["State B", "change_m"] == -2.0                      # shallower
    assert "State A" in ga.compare_years(sample_df, 2020, 2021)["state_name"].values
    assert "State B" not in ga.compare_years(sample_df, 2020, 2021)["state_name"].values  # no 2020 data


def test_linear_trend(sample_df):
    a = sample_df[sample_df.state_name == "State A"]
    t = ga.linear_trend(ga.yearly_trend(a))
    assert t["years"] == 3 and t["direction"] == "deeper" and t["slope_m_per_year"] > 0
    assert ga.linear_trend(ga.yearly_trend(sample_df[sample_df.state_name == "State B"])) is None  # only 2 years


def test_charts_build(sample_df):
    assert ga.chart_state_depth(ga.state_summary(sample_df)) is not None
    assert ga.chart_yearly_trend(ga.yearly_trend(sample_df, "state_name"), "state_name") is not None
    assert ga.chart_quarterly(ga.quarterly_comparison(sample_df)) is not None
    assert ga.chart_distribution(sample_df) is not None
    assert ga.chart_map(sample_df) is None                           # no lat/lon columns
    with_ll = sample_df.assign(latitude=30.0, longitude=75.0)
    assert ga.chart_map(with_ll) is not None
