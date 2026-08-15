"""Embedders — one interface, three implementations (tech-stack.md §5.2).

  MiniLMEmbedder    all-MiniLM-L6-v2 in-process (best; needs sentence-transformers)
  GeminiEmbedder    gemini-embedding-001 at 384 dims (no torch, needs API key)
  LexicalEmbedder   deterministic hashed bag-of-words — offline dev/CI baseline

All produce 384-dim vectors so they share the pgvector column. The lexical
embedder is not a semantic model; it exists so ingestion, retrieval, eval and
CI run with zero dependencies and zero keys, upgrading transparently when a
real embedder is configured.
"""

import hashlib
import math
import re
from typing import Protocol

from app.core.config import get_settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "be",
    "do",
    "does",
    "if",
    "it",
    "this",
    "that",
}


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LexicalEmbedder:
    """Signed feature hashing over unigrams + bigrams, L2-normalized."""

    name = "lexical"

    def __init__(self, dim: int = 384) -> None:
        self._dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(text) for text in texts]

    def _one(self, text: str) -> list[float]:
        vector = [0.0] * self._dim
        tokens = tokenize(text)
        features = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:], strict=False)]
        for feature in features:
            digest = hashlib.sha1(feature.encode()).digest()
            bucket = int.from_bytes(digest[:4], "little") % self._dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class GeminiEmbedder:
    """google-genai embeddings, Matryoshka-truncated to the column dimension."""

    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def embed(self, texts: list[str]) -> list[list[float]]:
        from google.genai import types

        result = self._client.models.embed_content(
            model=self._model,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=get_settings().embedding_dim),
        )
        embeddings = result.embeddings or []
        return [[float(v) for v in e.values or []] for e in embeddings]


class MiniLMEmbedder:
    """sentence-transformers/all-MiniLM-L6-v2 — optional heavy dependency."""

    name = "minilm"

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return [[float(v) for v in vector] for vector in vectors]


_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    """Factory per Settings.embedder; resolves once per process."""
    global _embedder
    if _embedder is not None:
        return _embedder

    settings = get_settings()
    choice = settings.embedder
    if choice == "auto":
        try:
            _embedder = MiniLMEmbedder()
            return _embedder
        except ImportError:
            pass
        if settings.gemini_api_key:
            _embedder = GeminiEmbedder(settings.gemini_api_key, settings.gemini_embedding_model)
            return _embedder
        _embedder = LexicalEmbedder(settings.embedding_dim)
    elif choice == "minilm":
        _embedder = MiniLMEmbedder()
    elif choice == "gemini":
        _embedder = GeminiEmbedder(settings.gemini_api_key, settings.gemini_embedding_model)
    else:
        _embedder = LexicalEmbedder(settings.embedding_dim)
    return _embedder
