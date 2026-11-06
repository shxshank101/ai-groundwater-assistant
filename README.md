# 💧 AI Groundwater Information Assistant

**Project ID:** P16 · **Team:** OJ16

| # | Member | Registration No. |
|---|--------|------------------|
| 1 | Shashank Singh | 12517817 |
| 2 | Hemant Kaushik | 12515559 |
| 3 | Surender Kumar | 12516464 |

A Streamlit web app that answers groundwater questions from **official government reports**
using Retrieval-Augmented Generation (RAG), and shows analytics from **real monitoring data**.

> **Read this first - about the data.** This project ships with **no groundwater measurements and no
> reports**. The workspace it was built in could not reach cgwb.gov.in / indiawris.gov.in, and the
> project rule is *never invent data*. You add the real files yourself (10 minutes, see
> [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md)). Until you do, the dashboard says "no data" instead of showing numbers.

## Features
- 💬 Chatbot with history, follow-up questions, report name + page citations, honest "not enough evidence" replies
- 📄 RAG pipeline: PyMuPDF → cleaning → LangChain chunks (1000 / 150 overlap) → Sentence Transformers → ChromaDB (saved on disk)
- 📈 Analytics: state / district views, yearly trends, quarterly and year-vs-year comparison, map, filters, source + period panel
- 📚 Document Library: upload, status, duplicate detection, keyword search, delete
- 🔎 Explore Reports: semantic search with page numbers
- 🗂️ Data Sources: official links, CSV upload with metadata, validation report
- ⬇️ Download chat, suggested questions, clear conversation, loading spinners, error messages

## Install
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit .env (see "LLM setup")
```
The first run downloads the embedding model (~90 MB) from Hugging Face. Internet is needed once.

## Run
```bash
streamlit run app.py
```

## Add real data (summary)
1. Download PDFs (e.g. *National Compilation on Dynamic Ground Water Resources of India*) from
   https://cgwb.gov.in/cgwbpnm/ → upload in **Document Library**.
2. Download groundwater-level CSV(s) from India-WRIS → upload in **Data Sources** (fill in the metadata form).

## LLM setup (optional but recommended)
Without an LLM the chatbot still works in **retrieval-only mode**: it shows the best matching report
passages with page numbers. For written answers, set three values in `.env`:
`LLM_API_URL`, `LLM_API_KEY`, `LLM_MODEL` (any OpenAI-compatible API, e.g. Groq, OpenRouter, a local
Ollama server). Free tiers exist but have rate limits and can change; **check the provider's current terms.**
Never commit `.env`.

## Tests
```bash
python -m pytest -v
```
Latest recorded run: [docs/TEST_RESULTS.md](docs/TEST_RESULTS.md).

## Troubleshooting
| Problem | Fix |
|---|---|
| "no extractable text" for a PDF | It is a scanned image. Download a text version or add OCR. |
| Embedding model download fails | The app falls back to an offline hashing embedder (lower quality). Dashboard shows which is active. Fix internet / proxy and delete `vector_store/`, then re-index. |
| "LLM could not be reached" | Check the three `.env` values and your network; the app falls back to report passages. |
| 401 / 429 from the API | Bad key / rate limit - wait and retry. |
| Dataset rejected | Read the message: it lists missing columns (needs `date, state_name, district_name, station_name, currentlevel`). |
| Changed embedding model | Vectors from different models are not mixed (separate collections); re-upload PDFs. |
| `ModuleNotFoundError` | Activate the venv and re-run `pip install -r requirements.txt`. |

## Folder structure
```
groundwater_assistant/
├── app.py  config.py  ui.py  download_official_data.py
├── requirements.txt  .env.example  .gitignore  README.md
├── modules/   document_processor  embeddings  vector_store  rag_pipeline  chatbot
│              data_ingestion  data_validation  groundwater_analytics  source_citations
├── pages/     dashboard  chatbot  analytics  reports  documents  sources  about
├── tests/     conftest  test_data  test_rag  test_analytics
├── data/      raw  processed  pdfs  metadata        vector_store/   assets/
└── docs/      PROJECT_REPORT  DATA_GUIDE  DEPLOYMENT  VIVA_QA  TEST_RESULTS
```
