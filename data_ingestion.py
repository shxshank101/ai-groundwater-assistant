"""
data_ingestion.py - loads real groundwater CSV files and records their metadata.

IMPORTANT: this project ships WITHOUT groundwater measurements. You download the
official files (see docs/DATA_GUIDE.md or run download_official_data.py) and the
app loads them. Every dataset gets a metadata record (name, source URL,
organisation, period, publication date, coverage, units, download date, limits).
"""
import json
import re
from datetime import date
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import requests

import config
from modules.data_validation import clean_dataframe, validate_dataframe

# India-WRIS / India Data Portal files use slightly different column names.
COLUMN_ALIASES = {
    "state": "state_name", "statename": "state_name",
    "district": "district_name", "districtname": "district_name",
    "station": "station_name", "stationname": "station_name", "site_name": "station_name",
    "dataacquisitiontime": "date", "datetime": "date", "observation_date": "date",
    "level": "currentlevel", "depth_to_water_level": "currentlevel",
    "water_level": "currentlevel", "gwl": "currentlevel",
}

METADATA_FIELDS = ["dataset_name", "source_url", "source_organization", "measurement_period",
                   "publication_date", "geographic_coverage", "measurement_units",
                   "download_date", "limitations", "file"]


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """lower-case column names and map known aliases to our standard names."""
    cols = {}
    for c in df.columns:
        key = re.sub(r"[^a-z0-9_]+", "_", str(c).strip().lower()).strip("_")
        cols[c] = COLUMN_ALIASES.get(key, key)
    return df.rename(columns=cols)


def load_registry(path: Path = config.DATASET_REGISTRY) -> Dict[str, Dict]:
    if Path(path).exists():
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def register_dataset(meta: Dict, path: Path = config.DATASET_REGISTRY) -> Dict:
    """Save a dataset's metadata. Missing fields are stored as 'unknown' (never guessed)."""
    record = {k: meta.get(k) or "unknown" for k in METADATA_FIELDS}
    record["download_date"] = meta.get("download_date") or str(date.today())
    registry = load_registry(path)
    registry[record["file"]] = record
    Path(path).write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def load_dataset(csv_path: Path) -> Dict:
    """Read a CSV, validate it, clean it. Returns {'data','report'}.

    Raises ValueError for unreadable files or files that fail validation.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise ValueError(f"Dataset file not found: {csv_path.name}")
    try:
        raw = pd.read_csv(csv_path, low_memory=False)
    except Exception as exc:
        raise ValueError(f"Could not read '{csv_path.name}' as CSV: {exc}") from exc
    raw = normalise_columns(raw)
    report = validate_dataframe(raw)
    if not report["ok"]:
        raise ValueError(f"'{csv_path.name}' failed validation: {'; '.join(report['errors'])}")
    data = clean_dataframe(raw)
    report["rows_after_cleaning"] = int(len(data))
    return {"data": data, "report": report}


def list_datasets(raw_dir: Path = config.RAW_DIR) -> list:
    return sorted(p for p in Path(raw_dir).glob("*.csv"))


def auto_register(csv_path: Path, meta: Optional[Dict] = None) -> Dict:
    """Register a CSV using values measured from the data itself (period, coverage)."""
    loaded = load_dataset(csv_path)
    df, rep = loaded["data"], loaded["report"]
    base = {
        "dataset_name": csv_path.stem, "file": csv_path.name,
        "measurement_period": f"{rep.get('date_min', '?')} to {rep.get('date_max', '?')}",
        "geographic_coverage": f"{df['state_name'].nunique()} states/UTs, "
                               f"{df['district_name'].nunique()} districts, "
                               f"{df['station_name'].nunique()} stations",
        "measurement_units": "m bgl (metres below ground level) as published",
        "limitations": "; ".join(rep["warnings"]) or "none detected by automatic checks",
    }
    base.update(meta or {})
    return register_dataset(base)


def download_file(url: str, dest: Path, timeout: int = 60) -> Path:
    """Download a file (used by download_official_data.py). Raises on failure."""
    resp = requests.get(url, timeout=timeout, stream=True,
                        headers={"User-Agent": "GroundwaterAssistant-student-project"})
    resp.raise_for_status()
    with open(dest, "wb") as f:
        for block in resp.iter_content(1 << 16):
            f.write(block)
    return dest
