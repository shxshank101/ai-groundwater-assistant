"""
groundwater_analytics.py - calculations and Plotly charts for the dashboard.

All numbers come from the loaded (real) dataset. Anything we compute ourselves
(averages, trend slopes) is labelled "derived" in the UI. Depth is in metres
below ground level (m bgl): a LARGER number means the water table is DEEPER.
"""
from typing import Dict, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TEAL, BLUE = "#0e9aa7", "#1565c0"


def filter_data(df: pd.DataFrame, states=None, districts=None, year_range=None) -> pd.DataFrame:
    out = df
    if states:
        out = out[out["state_name"].isin(states)]
    if districts:
        out = out[out["district_name"].isin(districts)]
    if year_range:
        out = out[(out["date"].dt.year >= year_range[0]) & (out["date"].dt.year <= year_range[1])]
    return out


def coverage_summary(df: pd.DataFrame) -> Dict:
    """Real coverage + freshness numbers for the home page."""
    if df.empty:
        return {"rows": 0}
    return {"rows": int(len(df)), "stations": int(df["station_name"].nunique()),
            "districts": int(df["district_name"].nunique()), "states": int(df["state_name"].nunique()),
            "first_date": df["date"].min().date(), "latest_date": df["date"].max().date()}


def add_period_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["year"] = out["date"].dt.year
    out["quarter"] = out["date"].dt.quarter
    out["month"] = out["date"].dt.month
    return out


def state_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Mean/min/max depth and number of readings per state (derived from the data)."""
    g = df.groupby("state_name")["currentlevel"]
    out = g.agg(mean_depth="mean", min_depth="min", max_depth="max", readings="count").reset_index()
    out["mean_depth"] = out["mean_depth"].round(2)
    return out.sort_values("mean_depth", ascending=False).reset_index(drop=True)


def yearly_trend(df: pd.DataFrame, by: Optional[str] = None) -> pd.DataFrame:
    d = add_period_columns(df)
    keys = ["year"] if by is None else [by, "year"]
    return d.groupby(keys)["currentlevel"].agg(mean_depth="mean", readings="count").reset_index()


def quarterly_comparison(df: pd.DataFrame) -> pd.DataFrame:
    d = add_period_columns(df)
    return (d.groupby(["year", "quarter"])["currentlevel"].mean().reset_index(name="mean_depth"))


def linear_trend(yearly: pd.DataFrame) -> Optional[Dict]:
    """Straight-line fit of mean depth vs year. DERIVED value, not an official statistic.

    Positive slope = water table getting deeper over the period.
    Needs at least 3 distinct years, otherwise returns None (we do not extrapolate).
    """
    d = yearly.dropna(subset=["mean_depth"])
    if d["year"].nunique() < 3:
        return None
    slope, intercept = np.polyfit(d["year"].astype(float), d["mean_depth"].astype(float), 1)
    return {"slope_m_per_year": round(float(slope), 4), "years": int(d["year"].nunique()),
            "direction": "deeper" if slope > 0 else "shallower" if slope < 0 else "no change"}


def compare_years(df: pd.DataFrame, year_a: int, year_b: int, level: str = "state_name") -> pd.DataFrame:
    """Mean depth per state/district in two years and the change (b - a)."""
    d = add_period_columns(df)
    pa = d[d["year"] == year_a].groupby(level)["currentlevel"].mean()
    pb = d[d["year"] == year_b].groupby(level)["currentlevel"].mean()
    out = pd.concat([pa.rename(f"mean_{year_a}"), pb.rename(f"mean_{year_b}")], axis=1).dropna()
    out["change_m"] = (out[f"mean_{year_b}"] - out[f"mean_{year_a}"]).round(2)
    return out.round(2).reset_index().sort_values("change_m", ascending=False)


# --------------------------------------------------------------------------- charts
def _style(fig, title):
    fig.update_layout(title=title, template="plotly_white", font=dict(family="Inter, sans-serif"),
                      margin=dict(l=10, r=10, t=50, b=10))
    return fig


def chart_state_depth(summary: pd.DataFrame, top: int = 20):
    s = summary.head(top)
    fig = px.bar(s, x="mean_depth", y="state_name", orientation="h", color="mean_depth",
                 color_continuous_scale=["#b2ebf2", TEAL, BLUE],
                 labels={"mean_depth": "Mean depth (m bgl)", "state_name": ""})
    fig.update_yaxes(autorange="reversed")
    return _style(fig, "Mean depth to water level by state (deeper = larger value)")


def chart_yearly_trend(yearly: pd.DataFrame, by: Optional[str] = None):
    fig = px.line(yearly, x="year", y="mean_depth", color=by, markers=True,
                  labels={"mean_depth": "Mean depth (m bgl)", "year": "Year"},
                  color_discrete_sequence=[TEAL, BLUE, "#7e57c2", "#ef6c00", "#2e7d32"])
    fig.update_yaxes(autorange="reversed", title="Mean depth (m bgl) - axis reversed, down = deeper")
    return _style(fig, "Historical depth to water level")


def chart_quarterly(q: pd.DataFrame):
    q = q.copy()
    q["quarter"] = "Q" + q["quarter"].astype(str)
    fig = px.bar(q, x="year", y="mean_depth", color="quarter", barmode="group",
                 labels={"mean_depth": "Mean depth (m bgl)"},
                 color_discrete_sequence=["#b2ebf2", TEAL, BLUE, "#0d3b66"])
    return _style(fig, "Quarterly comparison of mean depth")


def chart_distribution(df: pd.DataFrame):
    fig = px.histogram(df, x="currentlevel", nbins=40, color_discrete_sequence=[TEAL],
                       labels={"currentlevel": "Depth to water level (m bgl)"})
    return _style(fig, "Distribution of recorded depths")


def chart_map(df: pd.DataFrame, max_points: int = 5000):
    if not {"latitude", "longitude"} <= set(df.columns):
        return None
    d = df.dropna(subset=["latitude", "longitude"])
    if d.empty:
        return None
    d = d.sample(min(len(d), max_points), random_state=0) if len(d) > max_points else d
    fig = px.scatter_map(d, lat="latitude", lon="longitude", color="currentlevel",
                         hover_name="station_name", zoom=3.5, height=520,
                         color_continuous_scale=["#b2ebf2", TEAL, BLUE, "#0d3b66"],
                         labels={"currentlevel": "Depth (m bgl)"})
    fig.update_layout(map_style="carto-positron", margin=dict(l=0, r=0, t=40, b=0),
                      title="Monitoring stations (colour = depth)")
    return fig
