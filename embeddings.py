"""
embeddings.py - converts text into numbers (vectors) so that similar meanings
end up close together.

Primary model : Sentence Transformers (all-MiniLM-L6-v2) from Hugging Face.
Fallback      : a TF-IDF-style hashing embedder. It is a real (lexical) embedding,
                works fully offline, and is used only if the Hugging Face model
                cannot be downloaded. The app always shows which one is active.
"""
import hashlib
import math
import re
from collections import Counter
from typing import List

import numpy as np

import config

_STOPWORDS = set("a an the of in on at to for and or is are was were be by with from as it this that "
                 "what which who how why when where does do did can could should would about into".split())


class HashingEmbedder:
    """Offline lexical embedder: hashes words (and word pairs) into a fixed-size vector."""
    name = "hashing-tfidf-fallback"
    dim = 768

    def _tokens(self, text: str) -> List[str]:
        words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOPWORDS]
        return words + [f"{a}_{b}" for a, b in zip(words, words[1:])]

    def _index(self, token: str) -> int:
        return int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dim

    def encode(self, texts: List[str]) -> List[List[float]]:
        out = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32)
            for token, count in Counter(self._tokens(text)).items():
                vec[self._index(token)] += 1.0 + math.log(count)   # sub-linear term frequency
            norm = np.linalg.norm(vec)
            out.append((vec / norm if norm else vec).tolist())
        return out


class SentenceTransformerEmbedder:
    """Wrapper around the sentence-transformers library (loaded lazily)."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        self.name = model_name

    def encode(self, texts: List[str]) -> List[List[float]]:
        return self._model.encode(texts, normalize_embeddings=True,
                                  show_progress_bar=False).tolist()


_embedder = None


def get_embedder(force_fallback: bool = False):
    """Return the shared embedder (tries Sentence Transformers first)."""
    global _embedder
    if force_fallback:
        return HashingEmbedder()
    if _embedder is None:
        try:
            _embedder = SentenceTransformerEmbedder(config.EMBEDDING_MODEL)
        except Exception:  # package missing or model download blocked
            _embedder = HashingEmbedder()
    return _embedder


def embed_texts(texts: List[str], embedder=None) -> List[List[float]]:
    """Embed a list of strings (empty list -> empty list)."""
    if not texts:
        return []
    return (embedder or get_embedder()).encode(texts)
