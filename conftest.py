"""
Shared test helpers.

IMPORTANT: everything created here is a TEST FIXTURE used only to check that the
code works (tiny PDFs, a handful of invented rows). Fixtures live in temporary
folders and are never loaded by the app or shown on any page.
"""
import sys
from pathlib import Path

import pandas as pd
import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modules.embeddings import HashingEmbedder  # noqa: E402
from modules.rag_pipeline import RAGPipeline  # noqa: E402
from modules.vector_store import VectorStore  # noqa: E402


def make_pdf(path: Path, pages):
    """Write a small PDF with one text string per page (a list of strings)."""
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_textbox(pymupdf.Rect(50, 50, 550, 780), text, fontsize=11)
    doc.save(path)
    doc.close()
    return path


PAGES = [
    "FIXTURE REPORT. Groundwater is water stored beneath the earth surface in aquifers, "
    "in the pores and cracks of soil and rock. It is a major source of drinking water.",
    "Groundwater depletion happens when extraction exceeds recharge. Over-pumping for irrigation "
    "lowers the water table and causes wells to dry up in affected regions.",
    "Artificial recharge methods include check dams, percolation tanks and rooftop rainwater "
    "harvesting. These structures let rainwater percolate into aquifers.",
]


@pytest.fixture
def pdf_path(tmp_path):
    return make_pdf(tmp_path / "fixture_report.pdf", PAGES)


@pytest.fixture
def pipeline(tmp_path):
    store = VectorStore(path=tmp_path / "vs", embedder=HashingEmbedder())
    return RAGPipeline(store, registry_path=tmp_path / "documents.json")


@pytest.fixture
def indexed(pipeline, pdf_path):
    rec = pipeline.ingest_pdf(pdf_path)
    assert rec["status"] == "ok"
    return pipeline


@pytest.fixture
def sample_df():
    """Invented rows used ONLY to test calculations (values chosen so means are easy to check)."""
    rows = [
        ("2019-01-15", "State A", "D1", "S1", 10.0), ("2019-04-15", "State A", "D1", "S1", 12.0),
        ("2020-01-15", "State A", "D1", "S1", 14.0), ("2021-01-15", "State A", "D1", "S1", 16.0),
        ("2019-01-15", "State B", "D2", "S2", 5.0), ("2021-01-15", "State B", "D2", "S2", 3.0),
    ]
    df = pd.DataFrame(rows, columns=["date", "state_name", "district_name", "station_name", "currentlevel"])
    df["date"] = pd.to_datetime(df["date"])
    return df
