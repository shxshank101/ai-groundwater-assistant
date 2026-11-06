# Viva Questions and Answers

**1. What is RAG?** Retrieval-Augmented Generation: first retrieve relevant passages from documents, then let the language model
write an answer using only those passages. It reduces made-up answers and allows citations.

**2. Why not just ask a normal chatbot?** It answers from memory, can invent numbers, and cannot cite the exact report page.

**3. What is an embedding?** A list of numbers representing the meaning of text. Similar meanings give vectors that point in
similar directions, so we can search by meaning.

**4. What is cosine similarity?** The angle-based closeness of two vectors (1 = same direction). ChromaDB returns a distance;
we show similarity = 1 − distance.

**5. Why chunk the text? Why 1000 / 150?** Models and search work better on small focused passages. Overlap stops a sentence
being cut in half at a boundary. These values are a common balance; they are in `config.py` and can be tuned.

**6. Why ChromaDB?** Free, runs locally, persists to disk, simple Python API.

**7. How do you keep page numbers?** We extract text page by page and store `document` and `page` in each chunk's metadata;
citations are built from that metadata of retrieved chunks.

**8. How do you stop hallucination?** Prompt says "answer only from context"; low-similarity results are discarded; if nothing
is relevant we return a fixed "not enough information" reply; citations come only from retrieved chunks.

**9. What happens without an LLM key?** Retrieval-only mode: the best passages are shown with pages, clearly labelled.

**10. How do follow-up questions work?** The new question is rewritten into a standalone one using recent history (by the LLM
if configured, otherwise by combining with the previous question for short/pronoun questions).

**11. Where does your data come from?** Official CGWB / India-WRIS files that the user downloads and loads. We never generate data.

**12. Why is the app empty when first started?** Because we refuse to show invented numbers; the pages explain how to add data.

**13. What does "m bgl" mean?** Metres below ground level: depth to the water level. Bigger = deeper water table = usually worse.

**14. How is the dataset validated?** Required columns, duplicates (removed and counted), missing values (reported, never filled),
unparseable dates, non-numeric depths, implausible values (flagged), mixed units (rejected).

**15. Is the trend a prediction?** No. It is a straight-line fit of yearly means over the selected years, labelled "derived".
It is not shown with fewer than 3 years.

**16. What is the fallback embedder and why does it exist?** If the Hugging Face model cannot be downloaded, a hashing/TF-IDF
style embedder keeps the app working offline. It matches words, not meaning, so quality is lower. The dashboard shows which is active.

**17. How did you test?** 42 pytest tests; PDFs and tables used in tests are tiny fixtures in temp folders. LLM calls are mocked.

**18. What are the limitations?** Scanned PDFs, table structure in PDFs, LLM can still err, free hosting loses stored files,
real-data behaviour must be verified with the official downloads.

**19. How are secrets protected?** API keys come from environment variables / `.env` (git-ignored) or Streamlit secrets.

**20. What would you improve?** OCR, table extraction, multilingual support, reranking, an evaluation set of questions.
