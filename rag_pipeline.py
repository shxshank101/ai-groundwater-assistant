"""
rag_pipeline.py - the Retrieval-Augmented Generation (RAG) pipeline.

RAG in one sentence: instead of letting the AI answer from memory, we first
FIND the relevant report passages and then ask the AI to answer ONLY from them.

  ingest_pdf()  : PDF -> text -> chunks -> embeddings -> ChromaDB (+ registry entry)
  answer()      : question -> retrieve chunks -> LLM (or extractive fallback) -> answer + sources
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

import config
from modules.document_processor import PDFProcessingError, process_pdf, file_hash
from modules.source_citations import build_context, make_citations
from modules.vector_store import VectorStore

NOT_ENOUGH_EVIDENCE = ("I could not find enough information about this in the uploaded reports, "
                       "so I will not guess. Try rephrasing the question, or add the relevant "
                       "government report in the Document Library.")

SYSTEM_PROMPT = (
    "You are a groundwater information assistant for students and farmers in India. "
    "Answer ONLY using the numbered context passages provided. If the passages do not contain "
    "the answer, say you do not have enough information. Never invent numbers, districts or "
    "report names. Use simple language, quote units exactly as written, and cite sources "
    "like [1] or [2] after the statements they support.")


# ------------------------------------------------------------------ document registry
def load_registry(path: Path = config.DOCUMENT_REGISTRY) -> Dict[str, Dict]:
    if Path(path).exists():
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_registry(registry: Dict[str, Dict], path: Path = config.DOCUMENT_REGISTRY) -> None:
    Path(path).write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")


class RAGPipeline:
    def __init__(self, store: Optional[VectorStore] = None,
                 registry_path: Path = config.DOCUMENT_REGISTRY):
        self.store = store or VectorStore()
        self.registry_path = Path(registry_path)

    # ------------------------------------------------------------------ ingestion
    def ingest_pdf(self, pdf_path: Path, source_url: str = "", organization: str = "",
                   publication_year: str = "") -> Dict:
        """Process one PDF and store it. Returns its registry record (status ok/failed)."""
        pdf_path = Path(pdf_path)
        registry = load_registry(self.registry_path)
        record = {"document": pdf_path.name, "status": "failed", "error": "",
                  "source_url": source_url, "organization": organization,
                  "publication_year": publication_year,
                  "processed_on": datetime.now().isoformat(timespec="seconds"),
                  "total_pages": 0, "pages_with_text": 0, "chunks": 0, "doc_hash": ""}
        try:
            record["doc_hash"] = file_hash(pdf_path)
            # Skip exact duplicates (same content, any file name).
            for name, rec in registry.items():
                if rec.get("doc_hash") == record["doc_hash"] and rec.get("status") == "ok" \
                        and name != pdf_path.name:
                    record.update(status="duplicate", error=f"Same content as '{name}'.")
                    return record
            result = process_pdf(pdf_path)
            self.store.delete_document(pdf_path.name)       # replace older version if any
            record["chunks"] = self.store.add_chunks(result["chunks"])
            record.update(status="ok", total_pages=result["total_pages"],
                          pages_with_text=result["pages_with_text"])
        except PDFProcessingError as exc:
            record["error"] = str(exc)
        except Exception as exc:  # keep the app alive on any unexpected problem
            record["error"] = f"Unexpected error: {exc}"
        if record["status"] != "duplicate":
            registry[pdf_path.name] = record
            save_registry(registry, self.registry_path)
        return record

    def remove_document(self, document: str) -> None:
        self.store.delete_document(document)
        registry = load_registry(self.registry_path)
        registry.pop(document, None)
        save_registry(registry, self.registry_path)

    # ------------------------------------------------------------------ answering
    def condense_question(self, question: str, history: List[Dict]) -> str:
        """Make a follow-up question stand alone ("and in 2022?" -> full question).

        With an LLM we ask it to rewrite. Without one we use a simple rule: a short
        question that has no topic words gets the previous user question appended.
        """
        user_turns = [h["content"] for h in history if h["role"] == "user"]
        if not user_turns:
            return question
        if config.llm_configured():
            try:
                convo = "\n".join(f"{h['role']}: {h['content']}" for h in
                                  history[-2 * config.HISTORY_TURNS:])
                rewritten = self._chat([
                    {"role": "system", "content": "Rewrite the last user question so it is fully "
                     "self-contained, using the conversation. Output only the question."},
                    {"role": "user", "content": f"{convo}\nuser: {question}"}])
                if rewritten.strip():
                    return rewritten.strip()
            except Exception:
                pass
        words = re.findall(r"[A-Za-z]+", question)
        follow_up = len(words) <= 6 or re.search(r"\b(it|they|that|this|those|there|its|more)\b",
                                                 question.lower())
        return f"{user_turns[-1]} {question}" if follow_up else question

    def retrieve(self, question: str, top_k: int = config.TOP_K) -> List[Dict]:
        hits = self.store.search(question, top_k=top_k)
        return [h for h in hits if h["score"] >= config.MIN_RELEVANCE]

    def answer(self, question: str, history: Optional[List[Dict]] = None) -> Dict:
        """Return {'answer','citations','hits','mode','standalone_question'}."""
        history = history or []
        if not question or not question.strip():
            raise ValueError("Please type a question.")
        standalone = self.condense_question(question.strip(), history)
        hits = self.retrieve(standalone)
        if not hits:
            return {"answer": NOT_ENOUGH_EVIDENCE, "citations": [], "hits": [],
                    "mode": "no-evidence", "standalone_question": standalone}
        citations = make_citations(hits)
        if config.llm_configured():
            try:
                text = self._generate(question, hits, history)
                return {"answer": text, "citations": citations, "hits": hits,
                        "mode": "llm", "standalone_question": standalone}
            except Exception as exc:
                note = f"(The language model could not be reached: {exc}. Showing report passages instead.)\n\n"
        else:
            note = ("(No LLM is configured, so this is a retrieval-only answer: the most relevant "
                    "report passages are shown below. See README to enable AI answers.)\n\n")
        return {"answer": note + self._extractive(hits), "citations": citations, "hits": hits,
                "mode": "extractive", "standalone_question": standalone}

    # -------------------------------------------------------------------- helpers
    @staticmethod
    def _extractive(hits: List[Dict]) -> str:
        return "\n\n".join(f"**[{i}] {h['document']}, p. {h['page']}**\n{h['text']}"
                           for i, h in enumerate(hits[:3], 1))

    def _generate(self, question: str, hits: List[Dict], history: List[Dict]) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [{"role": h["role"], "content": h["content"]}
                     for h in history[-2 * config.HISTORY_TURNS:]]
        messages.append({"role": "user", "content":
                         f"Context passages:\n{build_context(hits)}\n\nQuestion: {question}"})
        return self._chat(messages)

    @staticmethod
    def _chat(messages: List[Dict]) -> str:
        """Call an OpenAI-compatible /chat/completions endpoint."""
        url = config.LLM_API_URL.rstrip("/") + "/chat/completions"
        resp = requests.post(url, timeout=config.LLM_TIMEOUT,
                             headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
                             json={"model": config.LLM_MODEL, "messages": messages,
                                   "temperature": 0.1})
        if resp.status_code == 401:
            raise RuntimeError("API key rejected (401). Check LLM_API_KEY.")
        if resp.status_code == 429:
            raise RuntimeError("Rate limit reached (429). Wait a moment and retry.")
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
