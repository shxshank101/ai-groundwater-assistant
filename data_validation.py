"""
data_validation.py - checks a groundwater table BEFORE it is used.

Rule: we report problems, we never silently "fix" values or fill gaps.
The only automatic change is dropping exact duplicate rows (and we count them).
"""
from typing import Dict

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["date", "state_name", "district_name", "station_name", "currentlevel"]
# Depth to water level is measured in metres below ground level (m bgl).
# Values outside this range are FLAGGED (not deleted): they may be real or typos.
PLAUSIBLE_DEPTH_RANGE = (-5.0, 400.0)


def validate_dataframe(df: pd.DataFrame, expected_unit: str = "m bgl") -> Dict:
    """Return a report dictionary describing the quality of the data."""
    report: Dict = {"rows": int(len(df)), "errors": [], "warnings": [], "ok": True}
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        report["errors"].append(f"Missing required columns: {missing_cols}")
        report["ok"] = False
        return report
    if df.empty:
        report["errors"].append("Dataset has no rows.")
        report["ok"] = False
        return report

    # --- duplicates
    report["duplicate_rows"] = int(df.duplicated().sum())
    if report["duplicate_rows"]:
        report["warnings"].append(f"{report['duplicate_rows']} exact duplicate rows found.")

    # --- missing values per column
    missing = df[REQUIRED_COLUMNS].isna().sum()
    report["missing_values"] = {k: int(v) for k, v in missing.items() if v}
    for col, n in report["missing_values"].items():
        report["warnings"].append(f"{n} missing values in '{col}'.")

    # --- dates
    dates = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    bad_dates = int(dates.isna().sum() - df["date"].isna().sum())
    if bad_dates:
        report["warnings"].append(f"{bad_dates} values in 'date' could not be parsed.")
    report["bad_dates"] = bad_dates
    if dates.notna().any():
        report["date_min"] = str(dates.min().date())
        report["date_max"] = str(dates.max().date())
        if dates.max() > pd.Timestamp.now():
            report["warnings"].append("Some dates are in the future.")

    # --- numeric depth values + unit consistency
    levels = pd.to_numeric(df["currentlevel"], errors="coerce")
    non_numeric = int(levels.isna().sum() - df["currentlevel"].isna().sum())
    if non_numeric:
        report["warnings"].append(f"{non_numeric} non-numeric depth values.")
    lo, hi = PLAUSIBLE_DEPTH_RANGE
    out_of_range = int(((levels < lo) | (levels > hi)).sum())
    report["out_of_range"] = out_of_range
    if out_of_range:
        report["warnings"].append(f"{out_of_range} depth values outside {lo}..{hi} {expected_unit} (flagged, kept).")
    if "unit" in df.columns:
        units = set(df["unit"].dropna().astype(str).str.strip().str.lower())
        report["units_found"] = sorted(units)
        if len(units) > 1 or (units and expected_unit.lower() not in units):
            report["errors"].append(f"Inconsistent or unexpected units: {sorted(units)}")
            report["ok"] = False
    report["valid_depth_rows"] = int(levels.notna().sum())
    return report


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Parse types and drop exact duplicates. Missing values stay missing (NaN)."""
    out = df.drop_duplicates().copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["currentlevel"] = pd.to_numeric(out["currentlevel"], errors="coerce")
    if "level_diff" in out.columns:
        out["level_diff"] = pd.to_numeric(out["level_diff"], errors="coerce")
    for col in ("state_name", "district_name", "station_name"):
        out[col] = out[col].astype("string").str.strip().str.title()
    out = out.dropna(subset=["date", "currentlevel"])
    return out.reset_index(drop=True)
