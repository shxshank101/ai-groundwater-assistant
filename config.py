"""
config.py - central settings for the AI Groundwater Information Assistant.

Everything that might change (folders, chunk sizes, model names, API settings)
lives here, so the other modules never hard-code values.
Secrets (API keys) are read from environment variables / a .env file, never
written in the source code.
"""
import os
from pathlib import Path

try:  # python-dotenv is optional; it just loads the .env file if present
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass

# ----------------------------------------------------------------- project info
PROJECT_NAME = "AI Groundwater Information Assistant"
PROJECT_ID = "P16"
TEAM_NAME = "OJ16"
# Mandatory order: Shashank Singh must always be first.
TEAM_MEMBERS = [
    ("Shashank Singh", "12517817"),
    ("Hemant Kaushik", "12515559"),
    ("Surender Kumar", "12516464"),
]

# ----------------------------------------------------------------------- folders
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("GW_DATA_DIR", BASE_DIR / "data"))
RAW_DIR = DATA_DIR / "raw"            # datasets (CSV) exactly as downloaded
PROCESSED_DIR = DATA_DIR / "processed"  # cleaned datasets
PDF_DIR = DATA_DIR / "pdfs"           # government PDF reports
METADATA_DIR = DATA_DIR / "metadata"  # dataset + document registries (JSON)
VECTOR_DIR = Path(os.getenv("GW_VECTOR_DIR", BASE_DIR / "vector_store"))

for _d in (RAW_DIR, PROCESSED_DIR, PDF_DIR, METADATA_DIR, VECTOR_DIR):
    _d.mkdir(parents=True, exist_ok=True)

DATASET_REGISTRY = METADATA_DIR / "datasets.json"
DOCUMENT_REGISTRY = METADATA_DIR / "documents.json"

# -------------------------------------------------------------------- RAG settings
CHUNK_SIZE = 1000        # characters per chunk (about 150-200 words)
CHUNK_OVERLAP = 150      # characters shared between neighbouring chunks
TOP_K = 5                # how many chunks to retrieve per question
MIN_RELEVANCE = 0.15     # below this similarity we say "not enough evidence"
COLLECTION_NAME = "groundwater_reports"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# --------------------------------------------------------------------- LLM settings
# Any OpenAI-compatible chat endpoint works (Groq, OpenRouter, Hugging Face
# router, a local Ollama server ...). Many of them have a free tier.
LLM_API_URL = os.getenv("LLM_API_URL", "")      # e.g. https://api.groq.com/openai/v1
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")          # e.g. llama-3.1-8b-instant
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
HISTORY_TURNS = 4        # previous question/answer pairs sent to the LLM

# ----------------------------------------------------- official sources (for UI + docs)
OFFICIAL_SOURCES = [
    {"name": "Central Ground Water Board (CGWB)", "url": "https://cgwb.gov.in/",
     "organization": "CGWB, Ministry of Jal Shakti, Govt. of India"},
    {"name": "CGWB Groundwater Level Monitoring",
     "url": "https://cgwb.gov.in/hi/ground-water-level-monitoring",
     "organization": "CGWB"},
    {"name": "CGWB Publications", "url": "https://cgwb.gov.in/cgwbpnm/",
     "organization": "CGWB"},
    {"name": "National Water Data Portal", "url": "https://nwdp.nwic.gov.in/",
     "organization": "National Water Informatics Centre"},
    {"name": "India Water Resources Information System (India-WRIS)",
     "url": "https://indiawris.gov.in/", "organization": "Ministry of Jal Shakti / NRSC"},
]


def llm_configured() -> bool:
    """True when all three LLM settings are present."""
    return bool(LLM_API_URL and LLM_API_KEY and LLM_MODEL)
