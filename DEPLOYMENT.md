# Deployment - Streamlit Community Cloud

1. **GitHub**: create a repository, then in the project folder
   ```bash
   git init && git add . && git commit -m "Groundwater assistant"
   git branch -M main
   git remote add origin https://github.com/<you>/<repo>.git && git push -u origin main
   ```
   `.gitignore` already excludes `.env` and `vector_store/`. Check `git status` shows no `.env`.
2. **requirements.txt** is already in the repo root. `sentence-transformers` pulls in PyTorch, which is large;
   if the free tier runs out of memory/disk, set `EMBEDDING_MODEL` to a smaller model or accept the offline fallback.
3. Go to https://share.streamlit.io → *New app* → pick the repo, branch `main`, main file `app.py`.
4. **Secrets**: *Advanced settings → Secrets*, paste:
   ```toml
   LLM_API_URL = "https://api.groq.com/openai/v1"
   LLM_API_KEY = "your_key"
   LLM_MODEL = "llama-3.1-8b-instant"
   ```
   Streamlit exposes top-level secrets as environment variables, which `config.py` reads. Never put keys in code.
5. **Deploy**. Then upload PDFs/CSVs through the app pages.

## Persistent storage limitation
Community Cloud storage is **not permanent**: uploaded PDFs, CSVs and the ChromaDB index can be lost when the app
restarts or sleeps. Options: (a) commit the (small, public) PDFs and CSVs into `data/` in the repo and re-index on start,
(b) use a host with a persistent disk (Render, Railway, a college server, Hugging Face Spaces with persistent storage),
(c) demo locally from your laptop - the safest choice for a viva.

Check each platform's current limits and pricing before relying on them.
