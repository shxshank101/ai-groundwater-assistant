"""
vector_store.py - stores chunk embeddings in ChromaDB (saved on disk, so the
index survives app restarts) and finds the chunks most similar to a question.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional

import chromadb

import config
from modules.document_processor import Chunk
from modules.embeddings import embed_texts, get_embedder


class VectorStore:
    def __init__(self, path: Path = config.VECTOR_DIR, collection: str = config.COLLECTION_NAME,
                 embedder=None):
        self.embedder = embedder or get_embedder()
        self.client = chromadb.PersistentClient(path=str(path))
        # The embedder name is part of the collection name: vectors from different
        # models are not comparable, so each model gets its own collection.
        safe = "".join(c if c.isalnum() else "_" for c in self.embedder.name)[-40:]
        self.collection = self.client.get_or_create_collection(
            name=f"{collection}_{safe}"[:60].strip("_") or "gw",
            metadata={"hnsw:space": "cosine"})

    # ---------------------------------------------------------------- write
    def add_chunks(self, chunks: List[Chunk], batch_size: int = 64) -> int:
        """Embed and store chunks. Re-adding the same chunk_id overwrites it."""
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start:start + batch_size]
            self.collection.upsert(
                ids=[c.chunk_id for c in batch],
                documents=[c.text for c in batch],
                embeddings=embed_texts([c.text for c in batch], self.embedder),
                metadatas=[c.metadata for c in batch])
        return len(chunks)

    def delete_document(self, document: str) -> None:
        self.collection.delete(where={"document": document})

    # ----------------------------------------------------------------- read
    def search(self, query: str, top_k: int = config.TOP_K,
               document: Optional[str] = None) -> List[Dict]:
        """Return the best chunks: [{'text','document','page','score'}], best first.

        score = cosine similarity (1.0 = identical direction, 0 = unrelated).
        """
        if not query.strip() or self.collection.count() == 0:
            return []
        n = min(top_k, self.collection.count())
        result = self.collection.query(
            query_embeddings=embed_texts([query], self.embedder), n_results=n,
            where={"document": document} if document else None)
        hits = []
        for text, meta, dist in zip(result["documents"][0], result["metadatas"][0],
                                    result["distances"][0]):
            hits.append({"text": text, "document": meta["document"], "page": int(meta["page"]),
                         "score": round(1.0 - float(dist), 4)})
        return hits

    def count(self) -> int:
        return self.collection.count()

    def documents(self) -> List[str]:
        data = self.collection.get(include=["metadatas"])
        return sorted({m["document"] for m in data["metadatas"]})

    def keyword_search(self, term: str, limit: int = 20) -> List[Dict]:
        """Plain text search inside stored chunks (used by the Document Library)."""
        needle = term.strip().lower()
        if not needle:
            return []
        # Chroma's own "contains" filter is case-sensitive, so we filter here instead.
        data = self.collection.get(include=["documents", "metadatas"])
        found = [{"text": t, "document": m["document"], "page": int(m["page"])}
                 for t, m in zip(data["documents"], data["metadatas"]) if needle in t.lower()]
        found.sort(key=lambda r: (r["document"], r["page"]))
        return found[:limit]
