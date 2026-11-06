"""Tests: dataset loading, validation, duplicates, missing values, dates, units, metadata."""
import json

import pandas as pd
import pytest

from modules import data_ingestion
from modules.data_validation import clean_dataframe, validate_dataframe

COLS = ["date", "state_name", "district_name", "station_name", "currentlevel"]


def frame(rows):
    return pd.DataFrame(rows, columns=COLS)


def test_valid_frame_ok():
    rep = validate_dataframe(frame([("2020-01-01", "A", "B", "C", 5.0)]))
    assert rep["ok"] and rep["rows"] == 1 and rep["date_min"] == "2020-01-01"


def test_missing_required_column():
    rep = validate_dataframe(pd.DataFrame({"date": ["2020-01-01"]}))
    assert not rep["ok"] and "Missing required columns" in rep["errors"][0]


def test_empty_dataset():
    assert not validate_dataframe(frame([]))["ok"]


def test_duplicates_detected_and_removed():
    df = frame([("2020-01-01", "A", "B", "C", 5.0)] * 3 + [("2020-02-01", "A", "B", "C", 6.0)])
    assert validate_dataframe(df)["duplicate_rows"] == 2
    assert len(clean_dataframe(df)) == 2


def test_missing_values_reported_not_filled():
    df = frame([("2020-01-01", "A", "B", "C", None), ("2020-02-01", "A", "B", "C", 4.0)])
    rep = validate_dataframe(df)
    assert rep["missing_values"]["currentlevel"] == 1
    cleaned = clean_dataframe(df)
    assert len(cleaned) == 1 and cleaned["currentlevel"].iloc[0] == 4.0   # row dropped, nothing invented


def test_bad_dates_flagged():
    rep = validate_dataframe(frame([("not a date", "A", "B", "C", 5.0), ("2020-01-01", "A", "B", "C", 5.0)]))
    assert rep["bad_dates"] == 1


def test_out_of_range_flagged_but_kept():
    rep = validate_dataframe(frame([("2020-01-01", "A", "B", "C", 9999.0)]))
    assert rep["out_of_range"] == 1 and rep["ok"]


def test_unit_consistency():
    df = frame([("2020-01-01", "A", "B", "C", 5.0), ("2020-01-02", "A", "B", "C", 6.0)])
    df["unit"] = ["m bgl", "feet"]
    rep = validate_dataframe(df)
    assert not rep["ok"] and "units" in rep["errors"][0].lower()


def test_load_dataset_with_aliases_and_register(tmp_path):
    csv = tmp_path / "wl.csv"
    pd.DataFrame({"Date": ["2020-01-01", "2021-01-01"], "State": ["x", "y"], "District": ["d", "e"],
                  "Station": ["s", "t"], "currentlevel": [3.0, 4.0]}).to_csv(csv, index=False)
    loaded = data_ingestion.load_dataset(csv)
    assert list(loaded["data"]["state_name"]) == ["X", "Y"]
    reg = tmp_path / "datasets.json"
    rec = data_ingestion.register_dataset({"dataset_name": "t", "file": "wl.csv"}, path=reg)
    assert rec["source_url"] == "unknown" and rec["publication_date"] == "unknown"   # never guessed
    assert json.loads(reg.read_text())["wl.csv"]["dataset_name"] == "t"


def test_load_dataset_errors(tmp_path):
    with pytest.raises(ValueError):
        data_ingestion.load_dataset(tmp_path / "missing.csv")
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError):
        data_ingestion.load_dataset(bad)
