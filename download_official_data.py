"""
download_official_data.py - helper to fetch official files on YOUR computer.

Usage:
    python download_official_data.py                 # reads data/metadata/sources.json
    python download_official_data.py URL [URL ...]   # download specific direct links

sources.json is a list like:
  [{"url": "https://.../report.pdf", "type": "pdf", "organization": "CGWB",
    "publication_year": "2024", "name": "optional file name"}]
Use direct file links that you copied from the official sites (see docs/DATA_GUIDE.md).
PDFs are indexed automatically; CSVs are validated and registered.
If a download fails, the reason is printed - nothing is replaced with fake data.
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import config
from modules import data_ingestion
from modules.rag_pipeline import RAGPipeline


def main(argv):
    if argv:
        items = [{"url": u} for u in argv]
    else:
        src = config.METADATA_DIR / "sources.json"
        if not src.exists():
            print(f"Create {src} first (see docs/DATA_GUIDE.md).")
            return 1
        items = json.loads(src.read_text(encoding="utf-8"))

    pipeline = None
    for item in items:
        url = item["url"]
        name = item.get("name") or Path(urlparse(url).path).name or "download"
        is_pdf = item.get("type", "pdf" if name.lower().endswith(".pdf") else "csv") == "pdf"
        dest = (config.PDF_DIR if is_pdf else config.RAW_DIR) / name
        try:
            print(f"Downloading {url} ...")
            data_ingestion.download_file(url, dest)
        except Exception as exc:
            print(f"  FAILED: {exc}\n  Try another official source or download it in your browser.")
            continue
        if is_pdf:
            pipeline = pipeline or RAGPipeline()
            rec = pipeline.ingest_pdf(dest, url, item.get("organization", ""), item.get("publication_year", ""))
            print(f"  PDF status: {rec['status']} {rec['error']}")
        else:
            try:
                rec = data_ingestion.auto_register(dest, {"source_url": url, **{
                    k: item[k] for k in ("dataset_name", "source_organization", "publication_date") if k in item}})
                print(f"  CSV registered: {rec['measurement_period']}")
            except ValueError as exc:
                print(f"  CSV rejected: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
