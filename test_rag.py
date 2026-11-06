"""Tests: PDF extraction, page numbers, embeddings, vector store, RAG, citations, follow-ups."""
import numpy as np
import pytest

import config
from conftest import make_pdf, PAGES
from modules import document_processor as dp
from modules.chatbot import Chatbot
from modules.embeddings import HashingEmbedder, embed_texts
from modules.rag_pipeline import NOT_ENOUGH_EVIDENCE, RAGPipeline
from modules.source_citations import make_citations
from modules.vector_store import VectorStore


# ------------------------------------------------------------------ PDF processing
def test_extract_text_and_page_numbers(pdf_path):
    pages = dp.extract_pages(pdf_path)
    assert [p["page"] for p in pages] == [1, 2, 3]
    assert "aquifers" in pages[0]["text"] and "depletion" in pages[1]["text"]


def test_chunks_keep_document_and_page(pdf_path):
    result = dp.process_pdf(pdf_path)
    assert result["total_pages"] == 3 and result["chunks"]
    for c in result["chunks"]:
        assert c.document == "fixture_report.pdf" and c.page in (1, 2, 3)
        assert c.metadata["page"] == c.page
    depletion = [c for c in result["chunks"] if "depletion" in c.text]
    assert depletion and all(c.page == 2 for c in depletion)


def test_blank_pages_skipped_but_numbers_preserved(tmp_path):
    path = make_pdf(tmp_path / "gap.pdf", ["first page has real text content here", "", "third page text content here"])
    assert [p["page"] for p in dp.extract_pages(path)] == [1, 3]


def test_pdf_without_text_raises(tmp_path):
    with pytest.raises(dp.PDFProcessingError, match="no extractable text"):
        dp.extract_pages(make_pdf(tmp_path / "blank.pdf", ["", ""]))


def test_corrupt_and_missing_pdf(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"this is not a pdf")
    with pytest.raises(dp.PDFProcessingError):
        dp.extract_pages(bad)
    with pytest.raises(dp.PDFProcessingError):
        dp.extract_pages(tmp_path / "nope.pdf")


def test_clean_text():
    assert dp.clean_text("ground-\nwater   level\n\n\n\nnext") == "groundwater level\n\nnext"


def test_chunk_size_respected():
    pages = [{"page": 1, "text": "word " * 1000}]
    chunks = dp.split_pages(pages, "d.pdf", "h", chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 5 and max(len(c.text) for c in chunks) <= 300


# ---------------------------------------------------------------------- embeddings
def test_embeddings_shape_norm_determinism():
    e = HashingEmbedder()
    v1, v2 = embed_texts(["groundwater level", "groundwater level"], e)
    assert len(v1) == e.dim and v1 == v2
    assert abs(np.linalg.norm(v1) - 1.0) < 1e-5
    assert embed_texts([], e) == []


def test_similar_text_scores_higher():
    e = HashingEmbedder()
    q, near, far = embed_texts(["groundwater depletion causes", "causes of groundwater depletion",
                                "cricket match score today"], e)
    assert np.dot(q, near) > np.dot(q, far)


# ------------------------------------------------------------------- vector store
def test_retrieval_returns_correct_page(indexed):
    hits = indexed.store.search("rainwater harvesting recharge structures", top_k=3)
    assert hits[0]["page"] == 3 and hits[0]["document"] == "fixture_report.pdf"
    assert hits == sorted(hits, key=lambda h: -h["score"])


def test_vector_store_persists(tmp_path, pdf_path):
    path = tmp_path / "persist"
    s1 = VectorStore(path=path, embedder=HashingEmbedder())
    s1.add_chunks(dp.process_pdf(pdf_path)["chunks"])
    n = s1.count()
    s2 = VectorStore(path=path, embedder=HashingEmbedder())   # new object, same folder
    assert s2.count() == n > 0 and s2.documents() == ["fixture_report.pdf"]


def test_keyword_search_and_delete(indexed):
    assert any(r["page"] == 2 for r in indexed.store.keyword_search("over-pumping"))
    indexed.remove_document("fixture_report.pdf")
    assert indexed.store.count() == 0


def test_empty_store_search(pipeline):
    assert pipeline.store.search("anything") == []


# ------------------------------------------------------------------------ RAG + citations
def test_answer_without_llm_is_extractive_and_cited(indexed, monkeypatch):
    monkeypatch.setattr(config, "LLM_API_URL", "")
    res = indexed.answer("What causes groundwater depletion?")
    assert res["mode"] == "extractive"
    assert res["citations"][0]["document"] == "fixture_report.pdf" and res["citations"][0]["page"] == 2
    assert "retrieval-only" in res["answer"]


def test_citations_only_reference_real_pages(indexed):
    res = indexed.answer("How can groundwater be recharged with check dams?")
    pages_in_store = {1, 2, 3}
    assert res["citations"] and all(c["page"] in pages_in_store for c in res["citations"])
    assert all(c["document"] == "fixture_report.pdf" for c in res["citations"])


def test_make_citations_deduplicates():
    hits = [{"document": "a", "page": 1, "score": .5, "text": "x"},
            {"document": "a", "page": 1, "score": .9, "text": "y"}]
    cites = make_citations(hits)
    assert len(cites) == 1 and cites[0]["score"] == .9


def test_insufficient_evidence_is_honest(indexed):
    res = indexed.answer("quantum chromodynamics lattice gauge")
    assert res["mode"] == "no-evidence" and res["answer"] == NOT_ENOUGH_EVIDENCE and not res["citations"]


def test_empty_question_rejected(indexed):
    with pytest.raises(ValueError):
        indexed.answer("   ")


def test_llm_mode_uses_retrieved_context(indexed, monkeypatch):
    seen = {}

    def fake_chat(messages):
        seen["messages"] = messages
        return "Depletion happens when extraction exceeds recharge [1]."

    monkeypatch.setattr(config, "LLM_API_URL", "http://x")
    monkeypatch.setattr(config, "LLM_API_KEY", "k")
    monkeypatch.setattr(config, "LLM_MODEL", "m")
    monkeypatch.setattr(RAGPipeline, "_chat", staticmethod(fake_chat))
    res = indexed.answer("What is groundwater depletion?")
    assert res["mode"] == "llm" and "[1]" in res["answer"]
    assert "fixture_report.pdf, p. 2" in seen["messages"][-1]["content"]      # context really sent
    assert "Answer ONLY" in seen["messages"][0]["content"]


def test_llm_failure_falls_back_with_message(indexed, monkeypatch):
    def boom(messages):
        raise RuntimeError("API key rejected (401).")
    monkeypatch.setattr(config, "LLM_API_URL", "http://x")
    monkeypatch.setattr(config, "LLM_API_KEY", "k")
    monkeypatch.setattr(config, "LLM_MODEL", "m")
    monkeypatch.setattr(RAGPipeline, "_chat", staticmethod(boom))
    res = indexed.answer("What is groundwater?")
    assert res["mode"] == "extractive" and "could not be reached" in res["answer"]


def test_chat_http_errors(monkeypatch):
    class R:
        def __init__(self, code): self.status_code = code
        def raise_for_status(self): pass
    monkeypatch.setattr(config, "LLM_API_URL", "http://x")
    for code, text in ((401, "401"), (429, "429")):
        monkeypatch.setattr("modules.rag_pipeline.requests.post", lambda *a, _c=code, **k: R(_c))
        with pytest.raises(RuntimeError, match=text):
            RAGPipeline._chat([{"role": "user", "content": "hi"}])


# ----------------------------------------------------------------- ingestion edge cases
def test_ingest_failures_and_duplicates(pipeline, pdf_path, tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"junk")
    rec = pipeline.ingest_pdf(bad)
    assert rec["status"] == "failed" and rec["error"]
    assert pipeline.ingest_pdf(pdf_path)["status"] == "ok"
    copy = tmp_path / "copy.pdf"
    copy.write_bytes(pdf_path.read_bytes())
    assert pipeline.ingest_pdf(copy)["status"] == "duplicate"
    n = pipeline.store.count()
    assert pipeline.ingest_pdf(pdf_path)["status"] == "ok" and pipeline.store.count() == n  # re-ingest replaces


# -------------------------------------------------------------------- follow-ups + chat
def test_followup_is_condensed_and_retrieves(indexed, monkeypatch):
    monkeypatch.setattr(config, "LLM_API_URL", "")
    bot = Chatbot(indexed)
    bot.ask("What causes groundwater depletion?")
    res = bot.ask("and how to prevent it?")                       # no topic words of its own
    assert "depletion" in res["standalone_question"]
    assert len(bot.history) == 4


def test_standalone_question_not_changed(indexed):
    q = "What is the capital city of a country with many rivers?"
    assert indexed.condense_question(q, [{"role": "user", "content": "x"}]) == q


def test_clear_and_export(indexed):
    bot = Chatbot(indexed)
    bot.ask("What is groundwater?")
    text = bot.export_text()
    assert "You:" in text and "source: fixture_report.pdf, p." in text
    bot.clear()
    assert bot.history == []
