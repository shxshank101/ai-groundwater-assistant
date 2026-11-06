"""
ui.py - small helpers shared by all Streamlit pages: theme, cached objects, icons.
"""
import streamlit as st
import pandas as pd

import config
from modules import data_ingestion
from modules.chatbot import Chatbot
from modules.embeddings import get_embedder
from modules.rag_pipeline import RAGPipeline
from modules.vector_store import VectorStore

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.6rem; max-width: 1200px; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#0d3b66 0%,#0e6e8c 100%); }
section[data-testid="stSidebar"] * { color: #eaf8fb !important; }
.hero { background: linear-gradient(120deg,#0d3b66,#0e9aa7); color:#fff; padding:1.6rem 1.8rem;
        border-radius:18px; margin-bottom:1.2rem; }
.hero h1 { margin:0; font-size:1.9rem; color:#fff; } .hero p { margin:.3rem 0 0; opacity:.92; }
.card { background:#fff; border:1px solid #d6edf1; border-left:5px solid #0e9aa7; border-radius:14px;
        padding:1rem 1.2rem; box-shadow:0 2px 8px rgba(13,59,102,.06); margin-bottom:.8rem; }
.card .label { font-size:.78rem; color:#5b7c8d; text-transform:uppercase; letter-spacing:.05em; }
.card .value { font-size:1.6rem; font-weight:700; color:#0d3b66; }
.src { font-size:.85rem; color:#37606f; background:#eef9fb; border-radius:10px; padding:.4rem .7rem;
       margin:.2rem 0; }
.badge { display:inline-block; padding:.1rem .6rem; border-radius:999px; font-size:.75rem; font-weight:600; }
.ok { background:#d8f5e6; color:#14693a; } .bad { background:#fde0e0; color:#9b1c1c; }
.warn { background:#fff1d6; color:#8a5a00; }
</style>
"""


def setup_page(title: str, subtitle: str = ""):
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def metric_card(label: str, value: str):
    st.markdown(f"<div class='card'><div class='label'>{label}</div>"
                f"<div class='value'>{value}</div></div>", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading the embedding model and vector database...")
def get_pipeline() -> RAGPipeline:
    return RAGPipeline(VectorStore())


def get_chatbot() -> Chatbot:
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = Chatbot(get_pipeline())
    return st.session_state.chatbot


@st.cache_data(show_spinner="Reading and validating datasets...")
def load_datasets(files_signature: tuple):
    """Load every CSV in data/raw. files_signature (name, size, mtime) busts the cache on change."""
    frames, problems = [], []
    for path in data_ingestion.list_datasets():
        try:
            df = data_ingestion.load_dataset(path)["data"]
            df["dataset_file"] = path.name
            frames.append(df)
        except ValueError as exc:
            problems.append(str(exc))
    data = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return data, problems


def datasets():
    sig = tuple((p.name, p.stat().st_size, int(p.stat().st_mtime)) for p in data_ingestion.list_datasets())
    return load_datasets(sig)


def embedder_name() -> str:
    return get_embedder().name
